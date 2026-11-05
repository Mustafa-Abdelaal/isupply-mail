---
name: review-pr
description: Multi-agent review of the current branch or a PR — choose reviewers from the changed paths (code, security, email protocol, platform, UX/a11y), run them in parallel, verify every finding against the code, and report ranked, actionable results; --post publishes one consolidated PR comment. Use before opening a PR, when asked to review, and in CI.
argument-hint: "[PR number] [--post]"
---

# Review a change with specialist subagents

> **Cloud sessions:** GitHub GraphQL is blocked there, so the `gh issue`/`gh pr`/`gh label list` commands below need their REST forms. See [github-cli.md](../../../docs/agentic/github-cli.md).

Arguments: `$ARGUMENTS`. With no PR number, review the current branch against `origin/main`.

## 1. Collect the change

- **PR**: `gh pr view <n> --json title,body,headRefName,baseRefName,files,labels` and `gh pr diff <n>`.
- **Branch**: `git fetch origin main`, then `git diff --stat origin/main...HEAD`,
  `git diff origin/main...HEAD` and any uncommitted changes.
- Find the linked issue or spec (`Fixes #n` in the body or the branch name), and collect its acceptance
  criteria.

## 2. Pick reviewers from the changed paths

| Changed | Reviewer |
|---|---|
| anything | `code-reviewer` |
| protocol, sync, MIME, threading, outbox, fixtures | `email-protocol-expert` |
| rendering/sanitizer, auth/credentials, storage, attachments, network, `.github/`, `.claude/hooks/`, dependencies | `security-reviewer` |
| platform adapters, build/packaging, background/push, permissions/entitlements | `platform-reviewer` |
| UI, strings/l10n, specs with user-facing behavior | `ux-a11y-reviewer` |
| tests only, or coverage gaps suspected | `test-engineer` (in report-only mode) |

## 3. Run them in parallel, in ONE message

Give each subagent the file list, the diff command, the acceptance criteria, the relevant
`docs/domain/` or threat-model sections, and this output contract:

> Return findings as a list: `severity` (blocker|major|minor|nit), `file:line`, `problem`, `evidence`
> (quote code or describe a concrete failing scenario), `fix`, `confidence` (high|medium|low). Report
> nothing you can't substantiate. Say "no findings" if there are none.

## 4. Verify before reporting

For each finding, open the code and confirm it. Run a targeted test where you can
(`scripts/test -k …`). Drop anything you can't confirm, and merge duplicates across reviewers. Check
that the acceptance criteria are actually met, and that `scripts/check` passes (or report that it
doesn't).

## 5. Report

Use this format:

```
## Review: <branch or PR #n> — <verdict: ready | changes needed | blocked>
Gate: scripts/check <pass/fail> · Reviewers: <list>
### Blockers / Major / Minor (each: file:line — problem — fix)
### Acceptance criteria: AC-1 ✅ evidence … AC-2 ❌ why
### Nits (optional, collapsed)
```

- **With `--post`**: write the report to a temp file and run `gh pr comment <n> --body-file <file>`.
  Post one consolidated comment, never one comment per finding.
- **Without it**: show the report, and offer to fix the blockers now. Fixing them happens in the main
  session.
