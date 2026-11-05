# Local dev mail server

[GreenMail](https://greenmail-mail-test.github.io/greenmail/) in Docker, giving every developer and
agent a real IMAP/SMTP server with seeded test mail. Driven by `scripts/dev-mail` (see `/dev-mail`).

```bash
scripts/dev-mail up        # start + wait until ready
scripts/dev-mail seed      # load fixtures/email/* into alice@isupply.test
scripts/dev-mail status    # folder counts
scripts/dev-mail send --subject "Hello"   # bob -> alice over SMTP
scripts/dev-mail reset     # purge all mail and reseed
scripts/dev-mail down
```

| Service | Host port | Notes |
|---|---|---|
| IMAP | 3143 | plain (dev only) |
| IMAPS | 3993 | TLS, self-signed (use `--insecure` with the probe tool) |
| SMTP | 3025 | plain, AUTH PLAIN/LOGIN optional |
| SMTPS | 3465 | TLS, self-signed |
| REST API | 3080 | `GET /api/service/readiness`, `POST /api/service/reset`, `POST /api/mail/purge`, `GET /api/user` |

Accounts: `alice@isupply.test` / `alice-dev-pw`, `bob@isupply.test` / `bob-dev-pw`, and
`shared@isupply.test` / `shared-dev-pw`. Ports bind to 127.0.0.1 only. Override them via `DEV_MAIL_*`
environment variables (`.env.example`).

## Known quirks (observed with GreenMail 2.1.3)

- An IMAP `DELETE` of a folder right after `POST /api/mail/purge` can drop the connection (socket EOF).
  That's why `scripts/dev-mail reset` uses `POST /api/service/reset`, which recreates the configured users
  with empty mailboxes, and then reseeds.
- The hierarchy delimiter is `.`, so the logical folder `Projects/2026` becomes `Projects.2026` on the wire.

## Fidelity and limits

GreenMail is fast and resettable, which makes it ideal for automated tests. Its capabilities are
IMAP4rev1, IDLE, MOVE, UIDPLUS, SORT, QUOTA and LITERAL+, with `.` as the hierarchy delimiter, and
SMTP AUTH PLAIN/LOGIN/XOAUTH2. It does **not** implement CONDSTORE, QRESYNC, SPECIAL-USE, NAMESPACE or
COMPRESS, so it exercises the fallback paths that many cPanel-hosted servers also need.

**Next step when sync work starts**: add a `dovecot` profile to `compose.yaml` (the official
`dovecot/dovecot` image) for CONDSTORE/QRESYNC/SPECIAL-USE coverage. Seed it through the same
`seed_mailbox.py --imap-port`, and run integration tests against both servers.
