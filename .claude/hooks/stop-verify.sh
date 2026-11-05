#!/usr/bin/env bash
# Stop hook: before Claude ends a turn with uncommitted changes, run the fast quality gate
# (scripts/check --fast --changed). If it fails, block the stop once and hand Claude the
# failure output so it fixes the problem (or explains why it is unrelated).
#
# - Skipped when nothing changed, when the same tree already passed, or on the second
#   consecutive stop (stop_hook_active) to avoid loops.
# - Opt out for a session: ISUPPLY_SKIP_STOP_CHECK=1

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

[ "${ISUPPLY_SKIP_STOP_CHECK:-0}" = "1" ] && exit 0
[ "$(json_get .stop_hook_active)" = "true" ] && exit 0
cd "$PROJECT_DIR" 2>/dev/null || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
[ -x scripts/check ] || [ -f scripts/check ] || exit 0

status="$(git status --porcelain 2>/dev/null || true)"
[ -z "$status" ] && exit 0

# Skip if this exact working tree already passed.
git_dir="$(git rev-parse --git-dir 2>/dev/null || echo .git)"
stamp="$git_dir/isupply-stop-check.ok"
fingerprint="$( { printf '%s\n' "$status"; git diff HEAD 2>/dev/null || true; git ls-files --others --exclude-standard -z 2>/dev/null | xargs -0 cat 2>/dev/null || true; } | cksum | tr -d ' ')"
if [ -f "$stamp" ] && [ "$(cat "$stamp" 2>/dev/null)" = "$fingerprint" ]; then
  exit 0
fi

out="$(bash scripts/check --fast --changed 2>&1)"
rc=$?
if [ "$rc" -eq 0 ]; then
  printf '%s' "$fingerprint" >"$stamp" 2>/dev/null || true
  exit 0
fi

tail_out="$(printf '%s\n' "$out" | tail -n 60 | cut -c1-300)"
reason="The fast quality gate failed on your uncommitted changes (scripts/check --fast --changed). Fix the failures below before finishing — or, if they are pre-existing and unrelated to this task, say so explicitly to the user.

$tail_out"
printf '{"decision":"block","reason":%s}\n' "$(json_str "$reason")"
exit 0
