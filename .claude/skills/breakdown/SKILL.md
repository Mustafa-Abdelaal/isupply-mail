---
name: breakdown
description: Split an approved spec or epic into small, independently shippable, agent-ready GitHub issues — vertical slices with acceptance criteria, platforms, verification commands, dependencies and labels — and create them with gh after the user confirms. Use after /spec and before /implement.
argument-hint: "[spec path | issue number]"
---

# Break a spec into issues

Input: `$ARGUMENTS`, a `docs/specs/…` path or an epic issue number. The spec must be `Approved`. If it
isn't, stop and suggest `/spec`.

## 1. Slice vertically

- Each issue delivers a testable capability end to end, like "read a plain-text message offline", not
  layer-by-layer work like "build the DB layer".
- Size: about one focused agent session, with a reviewable diff of about 400 lines or less. Split
  anything bigger.
- Put the walking skeleton first: the thinnest slice that touches every layer, then the slices that
  thicken it.
- Separate enabling work (fixtures, adapters, tooling) into its own issues when other issues depend on it.
- Note dependencies (`Blocked by #`) and mark which slices can run **in parallel** (separate agents or
  worktrees).

## 2. Draft each issue with the agent-task fields

Use the same fields as `.github/ISSUE_TEMPLATE/agent_task.yml`:

- **Context**: link to the spec and the AC IDs this slice satisfies, plus links to the ADR and domain docs.
- **Scope / Out of scope**: be explicit. Agents expand scope when it isn't written down.
- **Acceptance criteria**: copied or refined from the spec, each one testable.
- **Platforms**: the subset of web, windows, macos, linux, android, ios.
- **Likely files/areas**, and **Verification**: the exact commands, for example `scripts/test -k threading`,
  `scripts/check --full`, plus the fixtures to add or use and the screenshots required.
- **Labels**: `type:*`, `area:*`, `platform:*`, `priority:*`, and `agent:ready` only when nothing is
  ambiguous. Check that the labels exist: `gh label list --limit 200`.

## 3. Confirm, then create

1. Show the user a table (title, ACs, depends on, parallel?, labels) and wait for approval.
2. Write each body to a temp file and run
   `gh issue create --title "..." --body-file <file> --label "type:feature,area:sync,agent:ready"`.
3. If there are more than 3 issues, create an epic issue with a task list linking them all.
4. Add an "Implementation" section to the spec listing the issue links. Each issue can then be started
   with `/implement <n>`.
