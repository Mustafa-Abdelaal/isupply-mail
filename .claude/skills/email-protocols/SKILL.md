---
name: email-protocols
description: Email domain knowledge for this client — IMAP sync (UID/UIDVALIDITY, IDLE, CONDSTORE/QRESYNC, folders, flags), SMTP submission and outbox, MIME parsing/composition and charsets, HTML email safety, autoconfig and auth, real-server quirks. Load before designing, writing or reviewing protocol, sync, parsing, rendering or account-setup code.
---

# Email protocol knowledge router

The canonical notes live in `docs/domain/`. Read the page(s) for your task **before** designing or
reviewing, and cite the section you relied on in your plan or PR.

| Working on | Read |
|---|---|
| Sync engine, folders, flags, IDLE/push, offline cache, search | [imap.md](../../../docs/domain/imap.md) |
| Sending, outbox, Sent copy, retries, bounces | [smtp.md](../../../docs/domain/smtp.md) |
| Parsing, display, attachments, compose, charsets, threading | [mime.md](../../../docs/domain/mime.md) |
| HTML rendering, sanitizer, remote content, links, dark mode | [html-email.md](../../../docs/domain/html-email.md) |
| Account setup, server discovery, OAuth/passwords, credential storage | [discovery-and-auth.md](../../../docs/domain/discovery-and-auth.md) |
| Vocabulary | [glossary.md](../../../docs/domain/glossary.md) |

## The rules agents most often get wrong

1. A message's identity is **(mailbox, UIDVALIDITY, UID)**. Sequence numbers shift on every expunge,
   and Message-ID is neither unique nor always present.
2. The folder delimiter comes from `LIST` (`.` on many cPanel/Dovecot servers, `/` elsewhere). Names on
   the wire are **modified UTF-7** unless UTF8=ACCEPT is enabled.
3. Special folders are found through **SPECIAL-USE** flags, falling back to localized names (Arabic
   Outlook folders are common). Never hard-code "Sent Items".
4. Always fetch with `BODY.PEEK[...]`, because plain `BODY[]` marks the message `\Seen`.
5. IDLE watches one mailbox per connection and must be re-issued within 29 minutes. Mobile OSes kill
   sockets in the background, so push needs a server-side component.
6. A browser cannot open IMAP/SMTP sockets, so **the web client needs a gateway**.
7. Bcc lives only in the SMTP envelope, never in the headers you send or store.
8. A timeout after `DATA` means the outcome is unknown. Never auto-resend without dedupe (Message-ID
   check in Sent).
9. Most servers don't save sent mail automatically, so APPEND it to Sent yourself unless the provider
   does (Gmail and Microsoft 365 do).
10. Text parts decode with the declared charset first, then the fallback chain. windows-1256 Arabic is
    common, and wrong labels happen.
11. `multipart/alternative` puts the **last** part you can render first in preference. Images in
    `multipart/related` that are referenced by `cid:` are inline, not attachments.
12. RFC 2047 encoded-words: drop the whitespace *between adjacent* encoded words. Encoded words inside
    quoted parameters (Outlook filenames) must be tolerated on input and never generated.
13. Treat HTML as hostile: allowlist sanitizer, scripts off, remote content off by default, and real
    link targets shown.
14. Attachment names can lie (RTL override `U+202E`, `../`, `CON.txt`). Neutralize before display or save.
15. Output is canonical: CRLF, lines ≤ 998 octets, UTF-8 with proper encoding, a Date with timezone,
    and a Message-ID on our domain.

## When the docs don't cover it

- Ask the `email-protocol-expert` subagent, or read the RFC (rfc-editor.org is pre-approved for WebFetch).
- Check the behavior against the dev server (`scripts/dev-mail`), and note which server and version you
  observed.
- Add what you learned to the `docs/domain/` page with its source (`/codify-lesson`).

## Tools

- `python3 scripts/email/inspect_eml.py FILE --json` prints the MIME tree, body choice, attachments and
  risky HTML.
- `python3 scripts/email/probe_server.py --imap HOST:993 --smtp HOST:465` reports capabilities, TLS and
  auth mechanisms.
- `python3 scripts/email/discover.py DOMAIN` finds candidate server settings.
- `scripts/dev-mail up|seed|send|status` runs the local IMAP/SMTP server with seeded fixtures.
