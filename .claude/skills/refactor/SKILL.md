---
name: refactor
description: Behavior-preserving restructuring with a safety net — pin current behavior with characterization tests, change in small mechanical steps with scripts/check green after each, never mix in features or fixes. Use for cleanup, extraction, renames, splitting modules, or moving code behind platform adapters.
argument-hint: "[target code and goal]"
---

# Refactor safely

Goal: `$ARGUMENTS`

1. **Define done.** State the structural goal (for example "IMAP parsing is isolated from transport")
   and confirm that observable behavior must not change. If behavior *should* change, this is a
   feature or fix, so use `/implement` or `/fix-bug` instead.
2. **Pin the behavior.** Check coverage of the code you'll touch. Add characterization tests for
   uncovered paths, including the fixture conformance suite for parsing and rendering code. All of
   them must pass before you start.
3. **Plan the steps.** List small, mechanical steps (rename, extract function, move file, introduce an
   interface, swap the implementation). Each step leaves the code compiling and green. For more than
   ~5 files, write the steps into `docs/plans/` and get approval.
4. **Execute step by step**: one step, `scripts/test -k <area>`, commit
   (`refactor(<scope>): <step>`). Repeat. If a step goes red, revert it and take a smaller one.
5. **Don't change** public behavior, error messages, storage formats or wire formats. Change no tests
   except mechanical renames.
6. **Finish** with `scripts/check`, then ask the `code-reviewer` subagent to compare before and after
   for accidental behavior changes. Update the docs that describe the structure
   (`docs/architecture/overview.md`, the repo map in `AGENTS.md`).
