#!/usr/bin/env bash
# SessionStart hook: give Claude a short, factual snapshot of where work stands, and prepare
# cloud sessions (git hooks, STACK dependencies). Plain stdout becomes session context.
# Keep the output small (< 2 KB) and factual — no instructions.

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

cd "$PROJECT_DIR" 2>/dev/null || exit 0
source_kind="$(json_get .source)"

lines=""
add() {
  lines="${lines}$1
"
}

# --- Cloud sessions: idempotent setup on fresh containers ----------------------------------
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ] && [ "$source_kind" = "startup" ] && [ -f scripts/setup ]; then
  log_file="${TMPDIR:-/tmp}/isupply-mail-setup.log"
  if bash scripts/setup --quiet >"$log_file" 2>&1; then
    add "- Cloud setup: scripts/setup completed (log: $log_file)."
  else
    add "- Cloud setup: scripts/setup reported problems (log: $log_file)."
  fi
fi

# --- Git position -----------------------------------------------------------------------
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch="$(git branch --show-current 2>/dev/null || true)"
  dirty="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  ahead_behind=""
  if git rev-parse --verify --quiet origin/main >/dev/null 2>&1 && [ -n "$branch" ]; then
    counts="$(git rev-list --left-right --count origin/main...HEAD 2>/dev/null || true)"
    [ -n "$counts" ] && ahead_behind=" | vs origin/main: $(printf '%s' "$counts" | awk '{print $2 " ahead, " $1 " behind"}')"
  fi
  add "- Branch: ${branch:-detached HEAD} | uncommitted files: ${dirty}${ahead_behind}"
  case "$branch" in
    main | master) add "- On the protected default branch: feature work happens on a branch named type/<issue>-<slug>." ;;
  esac

  # Active plan for the issue in the branch name (e.g. feat/12-thread-view -> docs/plans/0012-*.md)
  issue="$(printf '%s' "$branch" | sed -n -E 's#^[a-z]+/([0-9]+)-.*#\1#p')"
  if [ -n "$issue" ]; then
    padded="$(printf '%04d' "$issue" 2>/dev/null || printf '%s' "$issue")"
    plan="$(ls docs/plans/"${padded}"-*.md 2>/dev/null | head -n 1 || true)"
    if [ -n "$plan" ]; then
      plan_status="$(sed -n -E 's/^- \*\*Status:\*\* *(.*)$/\1/p' "$plan" | head -n 1)"
      add "- Issue #$issue plan: $plan (status: ${plan_status:-unknown}). Open items:"
      next="$(grep -E '^[[:space:]]*- \[ \]' "$plan" | head -n 8 || true)"
      [ -n "$next" ] && add "$next"
    else
      add "- Issue #$issue has no plan file yet (docs/plans/${padded}-<slug>.md)."
    fi
  fi
fi

# --- Stack status -----------------------------------------------------------------------
adr="docs/decisions/0002-technology-stack.md"
if [ -f "$adr" ]; then
  stack="$(sed -n 's/^- \*\*Status:\*\* *\([A-Za-z]*\).*/\1/p' "$adr" | head -n 1)"
  if [ "$stack" = "Accepted" ]; then
    decision="$(sed -n -E 's/^- \*\*Decision:\*\* *(.*)$/\1/p' "$adr" | head -n 1)"
    add "- Technology stack: Accepted — ${decision:-see $adr}."
    markers="$(grep -rl 'STACK:' scripts .claude/hooks 2>/dev/null | wc -l | tr -d ' ')"
    [ "$markers" != "0" ] && add "- ${markers} file(s) still contain STACK: placeholders (/bootstrap-stack wires them)."
  else
    add "- Technology stack: ${stack:-unknown} (ADR-0002). No application code exists yet; scripts/check runs repo-level checks (agent config, tooling, fixtures)."
  fi
fi

# --- Tooling warnings --------------------------------------------------------------------
command -v jq >/dev/null 2>&1 || add "- jq is not installed: hooks fall back to python (slower). scripts/doctor has install hints."
command -v gh >/dev/null 2>&1 || add "- gh (GitHub CLI) is not installed: issue/PR skills cannot reach GitHub."

printf 'iSupply Mail session context:\n%s' "$lines"
exit 0
