#!/usr/bin/env bash
# PreToolUse(Edit|Write|NotebookEdit) guard: protects generated files, lockfiles, guardrails,
# accepted ADRs and existing email fixtures. Rules live in protected-paths.txt.

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

file="$(json_get .tool_input.file_path)"
[ -z "$file" ] && file="$(json_get .tool_input.notebook_path)"
[ -z "$file" ] && exit 0

rel="$(repo_relative "$file")"
[ -z "$rel" ] && exit 0 # outside the project: Claude Code's own permissions apply

# Accepted ADRs are immutable (supersede them with a new ADR).
case "$rel" in
  docs/decisions/[0-9][0-9][0-9][0-9]-*.md)
    if [ -f "$PROJECT_DIR/$rel" ] && grep -Eq '^- \*\*Status:\*\* *Accepted' "$PROJECT_DIR/$rel"; then
      pretool_decision ask "$rel is an Accepted ADR. Accepted ADRs are immutable: record a new ADR that supersedes it (/adr). Only the Status line may change (e.g. 'Superseded by ADR-0007')."
    fi
    ;;
esac

# Existing fixtures are conformance data; new fixtures are fine (use /email-fixture).
case "$rel" in
  fixtures/email/*.eml)
    if [ -f "$PROJECT_DIR/$rel" ]; then
      pretool_decision ask "$rel is an existing byte-exact email fixture referenced by fixtures/email/manifest.json. Prefer adding a NEW fixture (/email-fixture); editing this one changes the conformance suite for every implementation."
    fi
    ;;
esac

path_matches() { # path glob
  # shellcheck disable=SC2053 # intentional glob match
  [[ "$1" == $2 ]] && return 0
  case "$2" in
    '**/'*)
      # shellcheck disable=SC2053
      [[ "$1" == ${2#\*\*/} ]] && return 0
      ;;
  esac
  return 1
}

rules="$HOOKS_DIR/protected-paths.txt"
[ -f "$rules" ] || exit 0
while IFS='|' read -r decision pattern reason; do
  decision="$(printf '%s' "$decision" | tr -d ' \t')"
  case "$decision" in deny | ask) ;; *) continue ;; esac
  pattern="$(printf '%s' "$pattern" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  reason="$(printf '%s' "$reason" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  [ -z "$pattern" ] && continue
  if path_matches "$rel" "$pattern"; then
    pretool_decision "$decision" "$reason [$rel]"
  fi
done <"$rules"

exit 0
