# Testing strategy

Tests are how agents prove their work. Every tier runs through the stable scripts, so local and CI
behavior are identical.

## Tiers

| Tier | What | Where / tool | Runs in |
|---|---|---|---|
| **Unit** | Pure logic: parsing helpers, threading, state, outbox decisions | STACK test runner; repo tooling uses `unittest` | `scripts/test` (every commit; Stop hook with `--fast`) |
| **Fixture conformance** | Every message in `fixtures/email/manifest.json` interpreted exactly as expected | Reference: `scripts/tests/test_fixtures.py`; app: a conformance test wired by `/bootstrap-stack` | `scripts/test` |
| **Integration** | Real IMAP/SMTP behavior: sync, IDLE, send, folders, flags, UIDVALIDITY changes | `scripts/dev-mail` (GreenMail) + tests named `*integration*` | `scripts/test --integration`, `scripts/check --full`, CI `integration` job |
| **Platform/adapter contract** | Each platform adapter satisfies the same interface tests | STACK | CI platform jobs |
| **E2E / UI** | Critical flows: sign-in, read, compose and send, search, offline | STACK (Playwright for web; platform drivers) + `/verify-ui` screenshots | CI (after bootstrap), before release |
| **Security** | Hostile fixtures through the sanitizer, header-injection strings, limits | Unit + conformance | `scripts/test` |
| **Performance** | 100k-message folder, cold start, open message | `scripts/dev-mail seed --bulk N` + benchmarks | Before release, and on demand |

## Rules

- **Behavior changes come with tests, and bug fixes with a red-then-green regression test.** See
  `.claude/rules/tests.md`.
- **Parsing or rendering changes come with fixtures.** The corpus is the shared answer key, so add
  shapes with `/email-fixture`.
- **No mocks for the mail server** in integration tests. Use the dev server, and add a Dovecot profile
  when extension behavior (CONDSTORE/QRESYNC/SPECIAL-USE) needs coverage.
- **Deterministic**: injected clocks, seeded randomness, no sleeps, unique data per test.
- **Fast feedback**: `scripts/check --fast` should stay under about a minute. Slow suites go in the
  integration or E2E tiers.

## Coverage targets

The app core (sync, MIME, outbox, threading) gets ≥ 80% line coverage and 100% of the fixture corpus.
UI is covered by E2E on critical flows plus screenshot review. Coverage is a signal, not a goal: a
test that asserts nothing doesn't count.
