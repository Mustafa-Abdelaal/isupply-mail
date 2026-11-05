---
paths:
  - "**/{test,tests,__tests__,integration_test,spec,e2e}/**"
  - "**/*{_test,.test,.spec,Test,Tests}.*"
  - "scripts/tests/**"
---

# Tests

- **Name the behavior.** Test names say what must happen ("drops cache when UIDVALIDITY changes"),
  not how the code does it.
- **One reason to fail.** Use arrange/act/assert, assert on outcomes rather than internals, and avoid
  sleeps (poll with a timeout).
- **Use the corpus.** Parsing and rendering tests read `fixtures/email/manifest.json` and assert its
  `expect` keys exactly as `scripts/tests/_support.py::conformance_errors` defines them. Don't
  duplicate expectations in code.
- **Integration**: protocol flows run against the dev server (`scripts/dev-mail`). They are skipped
  unless `ISUPPLY_INTEGRATION=1`, and test names contain `integration` so `scripts/test --integration`
  selects them.
- **Regression tests** reference the issue (`# regression: #123`) and must fail before the fix. Show
  the red run in the PR.
- **Never** weaken, skip or delete a failing test to make CI pass. If a test is wrong, fix it, and
  explain why in the commit.
- **Flaky tests**: quarantining one needs an issue link and an owner. Fix the root cause.
