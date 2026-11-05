---
name: commit
description: Create well-scoped Conventional Commits from the current changes — review the diff, split unrelated changes, write type(scope) summary plus why-focused body and issue refs, let the git hooks run, commit. Use when asked to commit or at each green step of /implement.
argument-hint: "[optional message hint]"
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*), Bash(git log:*), Bash(git branch:*)
---

# Commit

Branch: !`git branch --show-current 2>/dev/null || true`
Status:
!`git status --short 2>/dev/null | head -40 || true`
Recent commits:
!`git log --oneline -8 2>/dev/null || true`

## Steps

1. **Read the full diff** (`git diff` and `git diff --staged`). Look for debug output, commented-out
   code, secrets, real email data and unrelated edits. Remove them or ask about them.
2. **Split** unrelated changes into separate commits (`git add <paths>` per group). Each commit should
   build and pass tests on its own.
3. **Write the message** in Conventional Commits form:

   ```
   <type>(<scope>): <imperative summary, ≤ 72 chars, no period>

   <why: the problem and the reasoning; what alternatives were rejected — wrap at 72>

   Refs #<issue>        (or Fixes #<issue> on the final commit of a fix)
   ```

   - **type**: feat, fix, refactor, perf, test, docs, build, ci, chore, revert. Breaking changes get
     `!` after the type/scope and a `BREAKING CHANGE:` footer.
   - **scope**: one of sync, imap, smtp, mime, render, compose, threading, search, auth, storage,
     notify, ui, l10n, web, desktop, mobile, server, fixtures, tooling, agent, ci, docs, deps.
   - Take the issue number from the branch name (`feat/12-…` gives `#12`).
   - If a session attribution trailer is required by your environment, append it after the refs.
4. **Commit** with `git commit -F <file>` or a heredoc. Never pass `--no-verify`. If the pre-commit hook
   fails (secret scan, gate), fix the cause and commit again.
5. **Confirm** with `git log --oneline -3` and report the commit(s). Don't push unless asked; that's
   `/open-pr`.
