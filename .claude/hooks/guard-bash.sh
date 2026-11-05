#!/usr/bin/env bash
# PreToolUse(Bash) guard. Denies (or escalates to a human) shell commands that are destructive,
# bypass the quality gate, rewrite protected history, or leak secrets. Reasons are written so
# Claude can choose a safe alternative.
#
# Covered: force pushes, pushes to protected branches, --no-verify, catastrophic rm,
# curl|sh, environment/secret dumping, unrestricted nested agents; "ask" for work-destroying git.
# Extend with care and add a case to scripts/tests/test_hooks.py for every new rule.

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

cmd="$(json_get .tool_input.command)"
[ -z "$cmd" ] && exit 0

PROTECTED='(main|master|production|release/[^ :]+)'

# 1) Drop heredoc bodies (commit messages etc. are data, not commands).
nodoc="$(printf '%s\n' "$cmd" | awk '
  in_doc { if ($0 ~ "^[ \t]*" delim "[ \t]*$") in_doc = 0; next }
  {
    line = $0
    if (match(line, /<<-?[ \t]*["'"'"']?[A-Za-z_][A-Za-z0-9_]*["'"'"']?/)) {
      d = substr(line, RSTART, RLENGTH); gsub(/<<-?[ \t]*|["'"'"']/, "", d); delim = d; in_doc = 1
    }
    print line
  }')"

# 2) Remove quoted strings for structural checks (flags inside messages must not trigger rules).
unquoted="$(printf '%s' "$nodoc" | sed -e "s/'[^']*'//g" -e 's/"[^"]*"//g' | tr '\n\t' '  ' | tr -s ' ')"

# 3) Split into simple commands on ; && || | and newlines.
segments="$(printf '%s\n' "$unquoted" | awk '{ gsub(/&&|\|\||;|\|/, "\n"); print }')"

matches() { printf '%s' "$1" | grep -Eq -- "$2"; }

current_branch() { git -C "$PROJECT_DIR" branch --show-current 2>/dev/null || true; }
remote_main_exists() { git -C "$PROJECT_DIR" rev-parse --verify --quiet refs/remotes/origin/main >/dev/null 2>&1; }

while IFS= read -r seg; do
  seg="$(printf '%s' "$seg" | sed -e 's/^ *//' -e 's/ *$//')"
  [ -z "$seg" ] && continue
  # strip leading env assignments and sudo
  core="$(printf '%s' "$seg" | sed -E 's/^(sudo +)?([A-Za-z_][A-Za-z0-9_]*=[^ ]* +)*//')"

  # --- git push ---------------------------------------------------------------
  if matches "$core" '^git( +-[Cc] +[^ ]+)* +push( |$)'; then
    if matches "$core" ' --no-verify( |$)'; then
      pretool_decision deny "Bypassing git hooks with --no-verify is not allowed. Fix the failing hook/check instead (run scripts/check)."
    fi
    if matches "$core" ' --mirror( |$)'; then
      pretool_decision deny "git push --mirror can overwrite every remote ref. Push a single feature branch instead."
    fi
    if matches "$core" ' (--force|-f)( |$)| -[a-zA-Z]*f[a-zA-Z]*( |$)| \+[^ ]+'; then
      pretool_decision deny "Plain force-push is blocked. If you rebased your OWN feature branch, use 'git push --force-with-lease origin <branch>'. Never rewrite main/master/release history."
    fi
    if matches "$core" "( |:)(refs/heads/)?${PROTECTED}( |$)"; then
      if remote_main_exists; then
        pretool_decision deny "Direct pushes to protected branches (main/master/production/release/*) are blocked. Push a feature branch and open a PR (/open-pr)."
      fi
    fi
    if matches "$core" ' --force-with-lease| --force-if-includes'; then
      if matches "$(current_branch)" "^${PROTECTED}$"; then
        pretool_decision deny "Force-pushing a protected branch is never allowed."
      fi
    fi
    # bare push / push HEAD while on a protected branch
    if matches "$core" '^git( +-[Cc] +[^ ]+)* +push( +-[a-zA-Z-]+)*( +[^ -][^ ]*)?( +HEAD)?$'; then
      if matches "$(current_branch)" "^${PROTECTED}$" && remote_main_exists; then
        pretool_decision deny "You are on a protected branch ($(current_branch)). Create a feature branch (git switch -c type/<issue>-<slug>) and push that instead."
      fi
    fi
    if matches "$core" ' --delete( |$)| -d( |$)| :[^ ]+$'; then
      pretool_decision ask "This deletes a remote branch or tag. Confirm it is yours and no longer needed."
    fi
  fi

  # --- git commit --no-verify ----------------------------------------------------
  if matches "$core" '^git( +-[Cc] +[^ ]+)* +commit( |$)' &&
    matches "$core" ' --no-verify( |$)| -[a-zA-Z]*n[a-zA-Z]*( |$)'; then
    pretool_decision deny "Bypassing git hooks (--no-verify / -n) is not allowed. Fix what the pre-commit hook reports."
  fi

  # --- work-destroying git: human confirms ----------------------------------------
  if matches "$core" '^git( +-[Cc] +[^ ]+)* +(reset +.*--hard|clean +.*-[a-zA-Z]*f|checkout +(--? +)?\.( |$)|restore +(--worktree +)?\.( |$)|stash +(drop|clear)|branch +.*-D|filter-branch|filter-repo|reflog +expire|update-ref +-d)'; then
    pretool_decision ask "This git command irreversibly discards work (uncommitted changes, stashes, branches or history). Confirm nothing valuable is lost — consider 'git stash' or a backup branch first."
  fi

  # --- GitHub: destructive or outward-facing -----------------------------------------
  if matches "$core" '^gh +repo +delete( |$)'; then
    pretool_decision deny "Deleting repositories is never done by agents."
  fi
  if matches "$core" '^gh +secret +'; then
    pretool_decision deny "Agents never read or write repository secrets. Ask the user to manage secrets in GitHub settings."
  fi
  if matches "$core" '^gh +api +.*(-X|--method) *(DELETE|PUT)( |$)'; then
    pretool_decision ask "This GitHub API call modifies or deletes repository state. Confirm it is intended."
  fi

  # --- environment dumps --------------------------------------------------------------
  if matches "$core" '^(printenv|env|export -p|set)$'; then
    pretool_decision deny "Dumping the whole environment can leak tokens (GH_TOKEN, API keys) into the transcript. Read the specific non-secret variable you need instead."
  fi
  if matches "$core" '^printenv +[A-Za-z0-9_]*(TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|APIKEY|PRIVATE_KEY|ACCESS_KEY)'; then
    pretool_decision deny "Printing a secret-bearing variable would leak it into the transcript. Check presence instead, e.g. [ -n \"\$VAR\" ] && echo set."
  fi

  # --- unrestricted nested agents -----------------------------------------------------
  if matches "$core" '^claude .*(--dangerously-skip-permissions|bypassPermissions)'; then
    pretool_decision deny "Starting a nested Claude with permissions bypassed is not allowed from inside a session."
  fi
done <<EOF
$segments
EOF

# --- catastrophic rm (quote characters removed but their contents kept: rm -rf "$HOME") ------
dequoted_segments="$(printf '%s\n' "$nodoc" | tr -d "\"'" | tr '\t' ' ' | awk '{ gsub(/&&|\|\||;|\|/, "\n"); print }')"
while IFS= read -r seg; do
  core="$(printf '%s' "$seg" | sed -E -e 's/^ +//' -e 's/^(sudo +)?([A-Za-z_][A-Za-z0-9_]*=[^ ]* +)*//')"
  if matches "$core" '^rm +(-[a-zA-Z-]+ +)*-[a-zA-Z]*[rR]' &&
    matches "$core" ' (/\*?|~/?|\$\{?HOME\}?/?|\.{1,2}/?|\*|\.git/?)( |$)'; then
    pretool_decision deny "Refusing recursive delete of a root, home, repository or .git path. Delete specific build/output directories by name instead."
  fi
done <<EOF
$dequoted_segments
EOF

# --- whole-command checks (need pipes / quotes intact) -------------------------------------
if matches "$nodoc" '(curl|wget)[^|]*\|[ ]*(sudo[ ]+)?(ba|z|da|k)?sh( |$)'; then
  pretool_decision deny "Piping a remote script into a shell is blocked (supply-chain risk). Download it, show the user what it does, and let them run it."
fi
if matches "$nodoc" '(echo|printf|print)[^;&|]*\$\{?[A-Za-z0-9_]*(TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|APIKEY|PRIVATE_KEY|ACCESS_KEY)[A-Za-z0-9_]*'; then
  pretool_decision deny "Printing a secret-bearing variable would leak it into the transcript. Check presence instead, e.g. [ -n \"\$VAR\" ] && echo set."
fi

exit 0
