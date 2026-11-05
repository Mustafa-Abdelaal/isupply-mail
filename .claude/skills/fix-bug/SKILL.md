---
name: fix-bug
description: Fix a bug the disciplined way — reproduce it first (anonymized .eml fixture, dev-mail scenario or failing test), find the root cause rather than the symptom, add a regression test that fails before the fix, fix, and check for the same bug elsewhere. Use for bug reports, crashes, wrong rendering, sync or sending problems.
argument-hint: "[issue number | bug description]"
---

# Fix a bug (reproduce → root cause → regression test → fix)

> **Cloud sessions:** GitHub GraphQL is blocked there, so the `gh issue`/`gh pr`/`gh label list` commands below need their REST forms. See [github-cli.md](../../../docs/agentic/github-cli.md).

Input: `$ARGUMENTS`. If it's an issue number, run `gh issue view <n> --comments`.

## 1. Reproduce before touching code

Pick the reproduction path that matches the symptom:

| Symptom | Reproduction |
|---|---|
| Email renders or parses wrong (garbled Arabic, missing attachment, broken layout) | Get the raw message: ask the user to export the `.eml` (*never* paste real mail into issues). Run `scripts/email/anonymize_eml.py`, then `inspect_eml.py --body`, then make a fixture with `/email-fixture` |
| Sync, flag, folder or new-mail problems | Script the server state with `scripts/dev-mail` (seed, `send`, IMAP APPEND/STORE/EXPUNGE, or delete and recreate a folder for a UIDVALIDITY reset) |
| Sending problems | Send against the dev server's SMTP. For provider-specific errors, `probe_server.py` the real server (needs user consent and credentials via env var) |
| Crash / logic error | Write a minimal unit test from the stack trace |

Write the reproduction as an **automated test** and watch it fail (`scripts/test -k <name>`). If you
can't reproduce, gather more info (app version, platform, server, exact steps) instead of guessing.

## 2. Find the root cause

- Ask "why" until you reach the decision that was wrong, not just the line that crashed.
- Check the domain docs: is this a known pitfall in `docs/domain/`? If it isn't, note it for step 5.
- Look for **siblings**: grep for the same pattern elsewhere (the same parser, the same assumption).

## 3. Fix

- Make the smallest change that fixes the root cause. Don't refactor or add features in the same commit.
- The regression test now passes, and `scripts/check` is green (add `--full` for sync or protocol code).
- Name the test after the behavior and mark it `regression: #<issue>`.

## 4. Verify the user's scenario

Re-run the original reproduction, plus `/verify-ui` for visible bugs. Confirm the sibling cases from
step 2 are fixed or filed as issues.

## 5. Prevent recurrence

If the bug came from a non-obvious fact (a server quirk, an RFC subtlety, a platform behavior), run
`/codify-lesson`: record it in `docs/domain/`, and add a lint, guard or test if the class of bug can be
caught mechanically.

## 6. Ship

Commit with `fix(<scope>): <what was wrong>` and `Fixes #<issue>`, then `/open-pr`. In the PR body,
describe the root cause, the fix, and the red-then-green evidence.
