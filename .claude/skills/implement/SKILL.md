---
name: implement
description: Golden path from a GitHub issue (or spec slice) to a tested, self-reviewed branch ready for a PR — understand, branch, plan with approval, build test-first in small commits, verify with scripts/check, review with subagents, hand off. Use when asked to build, implement, or work on an issue.
argument-hint: "[issue number]"
---

# Implement an issue end to end

> **Cloud sessions:** GitHub GraphQL is blocked there, so the `gh issue`/`gh pr`/`gh label list` commands below need their REST forms. See [github-cli.md](../../../docs/agentic/github-cli.md).

Branch: !`git branch --show-current 2>/dev/null || true`
Uncommitted: !`git status --short 2>/dev/null | head -20 || true`
Stack: !`grep -m1 -E '^- \*\*Status:\*\*' docs/decisions/0002-technology-stack.md 2>/dev/null || true`

## 0. Preconditions

- If the issue needs application code and ADR-0002 is not `Accepted`, **stop** and tell the user. Docs,
  tooling and fixtures can proceed without it.
- Start from a clean tree. If there are uncommitted changes, ask before stashing them.

## 1. Understand

- Run `gh issue view $ARGUMENTS --comments` and follow the links to the spec, ADRs and threat model.
- Read the `docs/domain/` page for the area. The `email-protocols` skill routes you to the right one.
- Find the existing code with the `Explore` subagent (broad searches) or Grep (targeted).
- Restate the goal, acceptance criteria, out-of-scope items and affected platforms in 5 lines. If
  anything is ambiguous, ask with AskUserQuestion **before** planning.

## 2. Branch and plan

- `git fetch origin main && git switch -c <type>/<issue>-<slug> origin/main` (type is one of feat,
  fix, refactor, docs, test, chore, perf, build, ci).
- Write `docs/plans/<issue padded to 4 digits>-<slug>.md` from [the template](../../../docs/plans/template.md):
  approach, alternatives rejected, files, step checkboxes, test plan, risks, rollback.
- If the work touches more than 3 files, a data model, a dependency or security, show the user the plan
  and **wait for approval**.

## 3. Build in small verified steps (repeat until done)

1. Write the next failing test first (`/tdd`). Email-shaped behavior gets a fixture (`/email-fixture`);
   protocol behavior gets an integration test against `scripts/dev-mail`.
2. Write the minimal code that makes it pass, then run `scripts/test -k <area>`.
3. Refactor while green, then tick the step in the plan file.
4. Commit (`/commit`) with a Conventional Commit message and `Refs #<issue>`.

Do one step at a time, and never leave the tree red between steps. If you discover more work, add it
to the plan's "Discovered" list rather than silently widening scope.

## 4. Verify like a reviewer would

- Run `scripts/check`. Run `scripts/check --full` too when sync, protocol or transport code changed.
- For UI changes, run `/verify-ui` (LTR + RTL, light + dark, phone + desktop widths).
- Map every acceptance criterion to evidence (test name, command output, screenshot) and put that
  mapping in the plan.

## 5. Self-review in parallel

Launch these in **one message**: `code-reviewer` always, plus by area `security-reviewer` (content,
credentials, network, storage), `email-protocol-expert` (IMAP/SMTP/MIME/sync), `platform-reviewer`
(adapters, background work, packaging) and `ux-a11y-reviewer` (UI). Running `/review-pr` does the same
thing. Verify each finding, fix the blockers, and list the deferred ones in the PR.

## 6. Hand off

- Set the plan status to `Ready for review` and update any docs you changed (`/sync-docs` if the
  structure moved).
- `/open-pr`. In your final message, say what changed, how it was verified (commands and results),
  and any follow-ups (filed as issues).
