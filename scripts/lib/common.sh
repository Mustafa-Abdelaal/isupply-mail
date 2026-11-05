#!/usr/bin/env bash
# shellcheck shell=bash
# Shared helpers for scripts/*. Source this file; do not execute it.
#
# Portability contract (developers use macOS, Linux and Windows/Git Bash):
#   - bash 3.2 compatible: no associative arrays, no mapfile/readarray, no ${var,,}, no `|&`
#   - POSIX tools only (no GNU-only flags such as `sed -i` without suffix, `readlink -f`, `timeout`)
#   - repo tooling is Python 3.9+ standard library only

set -o errexit -o nounset -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export REPO_ROOT

if [ -t 2 ] && [ -z "${NO_COLOR:-}" ]; then
  _c_red=$'\033[31m' _c_green=$'\033[32m' _c_yellow=$'\033[33m' _c_blue=$'\033[34m' _c_dim=$'\033[2m' _c_off=$'\033[0m'
else
  _c_red='' _c_green='' _c_yellow='' _c_blue='' _c_dim='' _c_off=''
fi

log() { printf '%s\n' "$*" >&2; }
log_step() { printf '%s==>%s %s\n' "$_c_blue" "$_c_off" "$*" >&2; }
log_ok() { printf '%s[ok]%s %s\n' "$_c_green" "$_c_off" "$*" >&2; }
log_warn() { printf '%s[warn]%s %s\n' "$_c_yellow" "$_c_off" "$*" >&2; }
log_err() { printf '%s[fail]%s %s\n' "$_c_red" "$_c_off" "$*" >&2; }
log_skip() { printf '%s[skip]%s %s\n' "$_c_dim" "$_c_off" "$*" >&2; }
die() {
  log_err "$*"
  exit 1
}
have() { command -v "$1" >/dev/null 2>&1; }

# Print the usage block at the top of the calling script (lines starting with "# " after the shebang).
usage() {
  sed -n '2,/^[^#]/{/^#/s/^# \{0,1\}//p;}' "$0" >&2
}

# Python 3.9+ interpreter for repo tooling. Windows installs often only provide `python`.
python_bin() {
  if [ -n "${PYTHON:-}" ]; then
    printf '%s' "$PYTHON"
    return 0
  fi
  local c
  for c in python3 python; do
    if have "$c" && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
      printf '%s' "$c"
      return 0
    fi
  done
  return 1
}

require_python() {
  PY="$(python_bin)" || die "Python 3.9+ is required for repo tooling. Run scripts/doctor for install hints."
  export PY
}

# --- Technology stack status (ADR-0002) -------------------------------------
STACK_ADR="$REPO_ROOT/docs/decisions/0002-technology-stack.md"

# Prints the ADR-0002 status word, e.g. "Proposed" or "Accepted".
stack_status() {
  if [ -f "$STACK_ADR" ]; then
    sed -n 's/^- \*\*Status:\*\* *\([A-Za-z]*\).*/\1/p' "$STACK_ADR" | head -n 1
  else
    printf 'Missing'
  fi
}

stack_ready() { [ "$(stack_status)" = "Accepted" ]; }

no_stack_note() {
  log_skip "$1 — no application stack wired yet (ADR-0002 is $(stack_status); /bootstrap-stack wires it)."
}

# --- Git helpers -------------------------------------------------------------

# Merge-base with origin/main (falls back to main, then HEAD) — the reference for "changed files".
base_ref() {
  local b
  for b in origin/main main; do
    if git -C "$REPO_ROOT" rev-parse --verify --quiet "$b" >/dev/null 2>&1; then
      if git -C "$REPO_ROOT" merge-base HEAD "$b" 2>/dev/null; then
        return 0
      fi
    fi
  done
  printf 'HEAD'
}

# Repo-relative files changed vs base: committed, staged, unstaged and untracked. One per line.
changed_files() {
  local base
  base="$(base_ref)"
  {
    git -C "$REPO_ROOT" diff --name-only --diff-filter=ACMR "$base" -- 2>/dev/null || true
    git -C "$REPO_ROOT" ls-files --others --exclude-standard 2>/dev/null || true
  } | sort -u
}

# --- Step runner ---------------------------------------------------------------
# Step functions run inside `if`, where bash disables errexit. A step must therefore
# collect its own status explicitly (rc=0; cmd || rc=1; return "$rc").
FAILED_STEPS=""

run_step() {
  local name="$1"
  shift
  log_step "$name"
  if "$@"; then
    log_ok "$name"
  else
    log_err "$name"
    FAILED_STEPS="${FAILED_STEPS}${FAILED_STEPS:+, }${name}"
  fi
}

finish_steps() {
  if [ -n "$FAILED_STEPS" ]; then
    log_err "Failed: $FAILED_STEPS"
    return 1
  fi
  log_ok "All steps passed"
}
