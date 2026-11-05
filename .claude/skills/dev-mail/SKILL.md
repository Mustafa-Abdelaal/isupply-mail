---
name: dev-mail
description: Run and drive the local IMAP/SMTP test server (GreenMail in Docker) — start, seed the fixture corpus, bulk-load for performance, send test messages, reset, inspect folders — and write integration tests against it. Use when developing, debugging or testing anything that talks to a mail server.
argument-hint: "[up | seed | reset | send | status | down]"
allowed-tools: Bash(scripts/dev-mail:*), Bash(./scripts/dev-mail:*)
---

# Local mail server

Status: !`scripts/dev-mail status 2>/dev/null | head -15 || true`

Requested: `$ARGUMENTS`. With no argument, ensure the server is up and seeded.

## Commands

| Need | Run |
|---|---|
| Start (idempotent, waits until ready) | `scripts/dev-mail up` |
| Load fixtures into alice's folders (Archive, Reports, Junk, an Arabic folder…) | `scripts/dev-mail seed` |
| Performance data (N extra messages in `Bulk`) | `scripts/dev-mail seed --bulk 5000` |
| Clean slate | `scripts/dev-mail reset` |
| Trigger new-mail / IDLE paths | `scripts/dev-mail send --subject "Hello" [--from bob@isupply.test --to alice@isupply.test]` |
| Folder counts | `scripts/dev-mail status` |
| Logs / stop | `scripts/dev-mail logs` · `scripts/dev-mail down` |

**Accounts**: `alice@isupply.test` / `alice-dev-pw`, `bob@isupply.test` / `bob-dev-pw` and
`shared@isupply.test` / `shared-dev-pw`. These are throwaway credentials, and the server listens on
127.0.0.1 only.

**Ports**: IMAP 3143 (plain) and 3993 (TLS, self-signed); SMTP 3025 (plain) and 3465 (TLS); REST API
3080. You can override them via `DEV_MAIL_*` env vars (see `.env.example`).

## Know the server's limits

GreenMail supports IMAP4rev1, IDLE, MOVE, UIDPLUS, SORT, QUOTA and LITERAL+, and its hierarchy
delimiter is `.`. It does **not** support CONDSTORE, QRESYNC, SPECIAL-USE, NAMESPACE or COMPRESS, so
code must take its fallback paths here. That's useful, because many cPanel servers behave the same
way. To test the extension paths, add a Dovecot profile (see `infra/dev-mail/README.md`) rather than
mocking.

## Writing integration tests

- Put them in the integration tier. Names contain `integration`, and they're skipped unless
  `ISUPPLY_INTEGRATION=1` (`scripts/test --integration` sets it).
- Start each test from a known state: `scripts/dev-mail reset` in setup, or unique subjects per test.
- Create scenarios through real protocol operations: SMTP send, IMAP APPEND, flag STORE, EXPUNGE, and
  deleting and recreating a folder to force a UIDVALIDITY change.
- Poll with a timeout rather than sleeping. Delivery is asynchronous.
- See `scripts/tests/test_integration_devmail.py` for examples. CI runs this tier with `scripts/check --full`.
