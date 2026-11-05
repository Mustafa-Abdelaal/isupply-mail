---
name: open-pr
description: Ship the current branch as a pull request — confirm the gate is green and commits are clean, rebase on origin/main, push, and open a PR whose body follows the repo template (summary, linked issue, platforms, verification evidence, security and docs notes). Use when work is ready for review or the user asks to open or create a PR.
argument-hint: "[issue number] [--draft]"
---

# Open a pull request

> **Cloud sessions:** GitHub GraphQL is blocked there, so the `gh issue`/`gh pr`/`gh label list` commands below need their REST forms. See [github-cli.md](../../../docs/agentic/github-cli.md).

Branch: !`git branch --show-current 2>/dev/null || true`
Commits ahead of main:
!`git log --oneline origin/main..HEAD 2>/dev/null | head -30 || true`

## Preconditions

- You are not on `main`. If you are, create a branch first (`<type>/<issue>-<slug>`).
- The working tree is clean, or the leftovers are intentionally excluded and you've said so.
- `scripts/check` is green, plus `--full` for sync or protocol changes. Never open a non-draft PR with
  a red gate. Use `--draft` and explain instead.

## Steps

1. **Rebase**: `git fetch origin main && git rebase origin/main`. Resolve conflicts and re-run
   `scripts/check` if anything changed.
2. **Push**: `git push -u origin <branch>`. After a rebase of your *own* branch, use
   `git push --force-with-lease origin <branch>`. Plain `--force` is blocked by the guard hook.
3. **Write the body** to a temp file, following `.github/pull_request_template.md`:
   - **Summary**: what and why, in 2–5 bullets. Link the spec and ADR.
   - **Linked issue**: `Fixes #n` (or `Refs #n` for partial work).
   - **Platforms affected**: tick the boxes.
   - **How verified**: the exact commands and results, the AC → evidence mapping from the plan file,
     and screenshots for UI.
   - **Security and privacy**: what was considered, or "n/a" with a reason.
   - **Docs**: what was updated.
   - **Follow-ups**: issue links.
4. **Create**: `gh pr create --base main --head <branch> --title "<conventional title>" --body-file <file>`,
   adding `--draft` if requested or if the gate is red. Add labels that mirror the issue's.
5. **Report** the PR URL. Suggest `/review-pr <n>` if it hasn't been reviewed yet, and mention that
   `/address-review <n>` and `/fix-ci <n>` handle the next steps.
