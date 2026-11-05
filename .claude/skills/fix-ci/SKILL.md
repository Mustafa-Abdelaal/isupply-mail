---
name: fix-ci
description: Diagnose and fix failing CI for the current branch or a PR — pull failed job logs with gh, reproduce locally with the same scripts CI runs, fix the root cause (never skip, weaken or disable checks), push, and watch the rerun. Use when checks are red or the user says CI is failing.
argument-hint: "[PR number | run id]"
---

# Fix failing CI

## 1. Find the failure

```bash
gh pr checks <n>                         # or: gh run list --branch "$(git branch --show-current)" --limit 5
gh run view <run-id> --log-failed | tail -200
```

Identify the job, the step and the **first** error (later errors are often cascades).

## 2. Reproduce locally

CI only runs the stable scripts, so the same command reproduces the failure:

| CI job | Local command |
|---|---|
| `check` | `scripts/check` |
| `integration` | `scripts/check --full` (needs Docker) |
| `actionlint` | `actionlint` |
| platform build jobs (after bootstrap) | the job's `scripts/…` step |

If it only fails in CI, compare tool versions (`scripts/doctor`), OS (Windows path separators or
line endings, macOS bash 3.2) and environment (missing secrets in fork PRs, network). Look at
`.gitattributes` when a fixture or script breaks on Windows.

## 3. Fix the root cause

- **Never** fix CI by skipping tests, adding `continue-on-error`, loosening lint rules, deleting
  assertions or bumping timeouts blindly. If a check itself is wrong, fix the check in its own commit
  with a justification, and get the user to agree first.
- **Flaky test**: reproduce it with repetition (`for i in $(seq 20); do scripts/test -k name || break; done`),
  then fix the race. Don't just retry.
- **Dependency or action drift**: pin versions, and say so in the commit.

## 4. Push and watch

Commit with `fix(ci): …` or the real scope, push, then `gh run watch <new-run-id>` (or poll
`gh pr checks <n>`). Report the cause, the fix and the green run URL. If it's still red, loop back to
step 1. After three failed attempts, stop and summarize what you know for the user.
