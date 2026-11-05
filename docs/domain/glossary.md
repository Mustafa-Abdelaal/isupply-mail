# Glossary

| Term | Meaning |
|---|---|
| **ADR** | Architecture Decision Record (`docs/decisions/`) |
| **APPEND** | IMAP command that uploads a message into a mailbox (used for Sent copies, drafts, seeding) |
| **APNs / FCM** | Apple / Google push notification services; needed for new-mail alerts while the app is closed |
| **Autoconfig** | Thunderbird XML format describing a domain's mail servers |
| **Autodiscover** | Microsoft's server-discovery protocol (Exchange / Microsoft 365) |
| **Bidi** | Bidirectional text (Arabic RTL mixed with LTR numbers and Latin); controlled by Unicode bidi rules and `dir` |
| **BODYSTRUCTURE** | IMAP FETCH item describing a message's MIME tree without downloading it |
| **BODY.PEEK** | IMAP FETCH that does not set `\Seen` (always use it) |
| **cid:** | URL scheme referencing a MIME part by Content-ID (inline images, RFC 2392) |
| **CONDSTORE / QRESYNC** | IMAP extensions (RFC 7162) for efficient incremental sync via MODSEQ |
| **Conformance corpus** | `fixtures/email/` plus `manifest.json`: messages and the expected interpretation every implementation must match |
| **CTE** | Content-Transfer-Encoding: 7bit, 8bit, binary, quoted-printable, base64 |
| **DKIM / SPF / DMARC** | Domain authentication for outgoing mail (configured by IT on DNS/server) |
| **Encoded-word** | RFC 2047 header encoding `=?charset?B/Q?...?=` |
| **Envelope** | SMTP-level sender and recipients (`MAIL FROM`, `RCPT TO`), distinct from headers. Bcc lives only here |
| **Fixture** | A byte-exact test `.eml` in `fixtures/email/` |
| **Gateway** | Backend that speaks IMAP/SMTP for clients that can't (web) |
| **GreenMail** | Java test mail server used locally (`scripts/dev-mail`) |
| **IDLE** | IMAP extension (RFC 2177) for server-pushed updates on one selected mailbox |
| **INTERNALDATE** | Server-side arrival date of a message (fallback when `Date:` is missing) |
| **ISPDB** | Mozilla's database of provider autoconfig files |
| **JMAP** | JSON Meta Application Protocol (RFC 8620/8621), modern HTTP-based alternative to IMAP |
| **Message-ID** | Header identifying a message; used for threading, not unique identity |
| **MIME** | Multipurpose Internet Mail Extensions: multipart structure, types, encodings |
| **Modified UTF-7** | IMAP's encoding for non-ASCII mailbox names (RFC 3501 §5.1.3) |
| **MODSEQ** | Per-message modification sequence (CONDSTORE) |
| **Outbox** | Durable local queue of messages waiting to be sent |
| **Provisioning profile** | Centrally managed settings for `@isupply.com.eg` (servers, auth, signature, flags) |
| **RFC 2231** | Encoding for non-ASCII MIME parameter values (filenames), with continuations |
| **RTL** | Right-to-left layout (Arabic) |
| **Sanitizer** | Allowlist-based HTML cleaner run before rendering |
| **SMTPUTF8** | SMTP extension allowing UTF-8 in addresses/headers (RFC 6531) |
| **SPECIAL-USE** | IMAP mailbox attributes marking Sent/Drafts/Trash/Junk/Archive (RFC 6154) |
| **STARTTLS** | Upgrading a plaintext connection to TLS (must fail closed) |
| **Submission** | Client-to-server sending (port 465 implicit TLS or 587 STARTTLS) |
| **TNEF / winmail.dat** | Outlook-proprietary attachment container |
| **UID / UIDVALIDITY / UIDNEXT** | IMAP per-mailbox message id / its validity epoch / next UID hint |
| **Vertical slice** | An issue that delivers testable value end-to-end (see `/breakdown`) |
