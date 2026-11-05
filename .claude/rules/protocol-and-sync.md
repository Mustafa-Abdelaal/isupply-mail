---
paths:
  - "**/{imap,smtp,jmap,mime,mail,sync,transport,protocol,outbox,threading}/**"
  - "**/*{imap,Imap,IMAP,smtp,Smtp,SMTP,jmap,Jmap,mime,Mime,MIME}*"
---

# Protocol, sync and MIME code

Before changing this code, read the matching page in `docs/domain/` (imap.md, smtp.md, mime.md) and
cite the section you relied on in the plan or PR. When unsure, ask the `email-protocol-expert` subagent.

- **Identity**: messages are identified by (mailbox, UIDVALIDITY, UID). When UIDVALIDITY changes, drop
  the folder cache and resync. Never store sequence numbers. Message-ID is for threading only; it is
  not unique.
- **Folders**: use the delimiter from `LIST`, decode names as modified UTF-7 (or use UTF8=ACCEPT), and
  find Sent/Drafts/Trash/Junk/Archive via SPECIAL-USE, falling back to localized names (Arabic included).
- **Sync**: fetch with `BODY.PEEK` (never mark messages read by accident). Fetch `BODYSTRUCTURE` and
  headers first, bodies lazily. Use CONDSTORE/QRESYNC when advertised, with UID-range diff as the
  fallback. IDLE must re-issue within 29 minutes and survive dropped connections with backoff.
- **Connections**: hosting providers cap concurrent IMAP connections per account (often 10–20 per IP).
  Pool them, and never open one per folder unbounded.
- **Commands**: build them only through the protocol library's quoting/literal API. Never interpolate
  user input (search terms, folder names, addresses) into raw commands.
- **Sending**: Bcc goes in the envelope only. Use CRLF, keep lines ≤ 998 octets and encode headers with
  RFC 2047 or SMTPUTF8. Put every send through the durable outbox, and treat a timeout after DATA as
  "unknown" so it is never silently re-sent. APPEND to Sent unless the server auto-saves.
- **Parsing**: be lenient on input and strict on output. Unknown charsets fall back as `mime.md`
  describes, and malformed MIME degrades instead of throwing. Every new shape gets a fixture
  (`/email-fixture`).
- **Logging**: never log message bodies, full headers, credentials or tokens. Log mailbox and UID
  counts, timings and error classes.
- **Tests**: unit-test pure logic, run the fixture conformance suite for parsing, and test protocol
  flows against the dev server (`scripts/dev-mail up`, then `scripts/test --integration`).
