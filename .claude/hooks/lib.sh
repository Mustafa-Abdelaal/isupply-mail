#!/usr/bin/env bash
# shellcheck shell=bash
# Shared helpers for Claude Code hooks (sourced, not executed).
#
# Hook design rules for this repo:
#   - Fast (< 1s for PreToolUse guards) and never interactive.
#   - Fail OPEN on internal errors: a broken hook must not block all work. Guards only
#     deny/ask on a positive match, with a reason Claude can act on.
#   - Portable: bash 3.2 (macOS), Git Bash (Windows), Linux. JSON via jq, else python.

HOOK_INPUT="$(cat 2>/dev/null || true)"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
# shellcheck disable=SC2034 # used by the hooks that source this file
HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

_py() {
  local c
  for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1; then
      printf '%s' "$c"
      return 0
    fi
  done
  return 1
}

# json_get .a.b — print a field from the hook input (strings raw, other values as JSON). Empty if absent.
json_get() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$HOOK_INPUT" | jq -r "$1 // empty" 2>/dev/null || true
    return 0
  fi
  local py
  py="$(_py)" || return 0
  printf '%s' "$HOOK_INPUT" | "$py" -c '
import json, sys
try:
    v = json.load(sys.stdin)
    for key in sys.argv[1].lstrip(".").split("."):
        v = v.get(key) if isinstance(v, dict) else None
    if v is not None:
        sys.stdout.write(v if isinstance(v, str) else json.dumps(v))
except Exception:
    pass
' "$1" 2>/dev/null || true
}

# json_str "text" — print a JSON string literal.
json_str() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$1" | jq -Rs .
    return 0
  fi
  local py
  if py="$(_py)"; then
    printf '%s' "$1" | "$py" -c 'import json, sys; sys.stdout.write(json.dumps(sys.stdin.read()))'
  else
    # Last resort: escape backslashes, quotes and newlines by hand.
    printf '"%s"' "$(printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | awk 'BEGIN{ORS="\\n"} {print}')"
  fi
}

# pretool_decision deny|ask|allow "reason" — emit a PreToolUse decision and exit.
pretool_decision() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"%s","permissionDecisionReason":%s}}\n' \
    "$1" "$(json_str "$2")"
  exit 0
}

# Repo-relative path for an absolute file path (Windows separators normalized). Empty if outside.
repo_relative() {
  local p
  p="$(printf '%s' "$1" | tr '\\' '/')"
  local root
  root="$(printf '%s' "$PROJECT_DIR" | tr '\\' '/')"
  case "$p" in
    "$root"/*) printf '%s' "${p#"$root"/}" ;;
    /* | [A-Za-z]:/*) printf '' ;;
    *) printf '%s' "$p" ;;
  esac
}
