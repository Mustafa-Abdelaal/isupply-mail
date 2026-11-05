---
name: tdd
description: Strict red-green-refactor loop for one behavior at a time — write a failing test, confirm it fails for the right reason, make it pass with minimal code, refactor while green. Use for parsers, sync logic, threading, state machines, or whenever the user asks for TDD.
argument-hint: "[behavior to implement]"
---

# Test-driven development loop

Target behavior: `$ARGUMENTS`

## The loop: one behavior per cycle

1. **List** the behaviors as test names first: the happy path, edge cases, failure paths. For email
   logic, mine the corpus: `jq -r '.fixtures[] | .file + "  " + (.tags | join(","))' fixtures/email/manifest.json`.
2. **Red.** Write ONE test for the next behavior, then run only that test (`scripts/test -k <name>`).
   It must fail **for the expected reason**: an assertion failure, not an import error or typo. If it
   passes already, the behavior exists, so delete or adjust the test.
3. **Green.** Write the smallest code that passes. Hard-coding is allowed if the next test will force
   the generalization.
4. **Refactor.** Remove duplication and clarify names while everything stays green. Run the area's
   tests after each change.
5. **Commit** at green when the step is meaningful (`/commit`).
6. Repeat until the behavior list is empty, then run `scripts/check`.

## Rules

- Never write production code without a failing test that demands it. Exception: pure wiring the
  stack's tooling can't test, which you must call out in the PR.
- Assert outcomes (returned values, emitted state, server-visible effects), not private calls.
- For parsing and rendering, assert against `manifest.json` expectations via the shared conformance
  checker instead of re-stating expected values in code.
- For time, randomness and network, inject clocks, seeds and transports, and use the dev mail server
  for protocol truth.
- Keep tests fast. Anything slower than a second belongs in the integration tier.
