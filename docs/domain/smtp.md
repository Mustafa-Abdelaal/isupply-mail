# SMTP submission for client developers

How a mail client sends: RFC 6409 (message submission), RFC 8314 (implicit TLS), RFC 5321 (SMTP),
RFC 4954 (AUTH) and RFC 6531 (SMTPUTF8).

## Connecting

- Prefer **port 465 with implicit TLS** (RFC 8314). Port **587 with STARTTLS** is the alternative, and
  it must **fail closed**: if `STARTTLS` isn't offered or fails, abort and never continue in plaintext
  (this prevents STARTTLS stripping). Port 25 is for server-to-server traffic, never clients.
- `EHLO` with a sensible name, then read the extensions: `SIZE <max>`, `AUTH <mechanisms>`, `8BITMIME`,
  `SMTPUTF8`, `PIPELINING`, `ENHANCEDSTATUSCODES`, `CHUNKING`, `DSN`.
- AUTH: `PLAIN` or `LOGIN` are acceptable only over TLS. OAuth2 uses `XOAUTH2` (Google, Microsoft) or
  `OAUTHBEARER` (RFC 7628).

## Building the message

- **Headers**: `From` (the authenticated user's address; servers may reject "send as" other
  addresses), `To`/`Cc`, `Subject`, a `Date` with timezone offset, a `Message-ID` on our domain
  (`<random@isupply.com>`), `MIME-Version`, and for replies `In-Reply-To` plus `References` (the
  parent's References followed by the parent's Message-ID).
- **Bcc goes in the envelope only.** Add the Bcc recipients to `RCPT TO` and strip the `Bcc:` header from
  the transmitted message. The copy saved to Sent may keep the Bcc header so the user can see it.
- **Encoding**: CRLF line endings, lines ≤ 998 octets (78 recommended), non-ASCII headers as RFC 2047
  encoded-words, or raw UTF-8 only if the server advertises `SMTPUTF8` *and* the recipient path
  supports it. Text bodies are UTF-8 with quoted-printable or base64. Send `multipart/alternative` with a
  plain-text part whenever there's HTML.
- **Header injection**: user-controlled values (subject, display names, addresses) must never contain
  raw CR or LF. Encode them, or reject them, before they reach the message builder.
- **Attachments**: check the size against `SIZE` *before* uploading. Base64 inflates size by about 33%.
  Offer to send big files another way rather than failing mid-transfer.

## Reliability: the outbox

1. Compose writes the message to the **durable outbox** (local storage) first, then attempts the send.
2. Classify the result:
   - `2xx`: success. APPEND a copy to Sent (unless the provider saves it automatically; Gmail and
     Microsoft 365 do), set `\Answered` or `$Forwarded` on the source message, then remove the outbox
     entry.
   - `4xx` (temporary): retry with backoff. Keep the item visible as "queued".
   - `5xx` (permanent): stop, show the error in plain language (bad recipient, too large, rejected as
     spam), and keep the draft so the user can fix and resend.
3. **Timeout or disconnect after `DATA`**: the server may have accepted the message. The outcome is
   **unknown**. Before any retry, check Sent and other recent mail for our `Message-ID`, or ask the
   user. Never silently resend (duplicate emails to customers are a real-world embarrassment).
4. Offline sends wait in the outbox and go out on reconnect, oldest first, one at a time per account.

## Drafts

- Autosave locally on every change (debounced) and sync to the server's Drafts folder via `APPEND` with
  the `\Draft` flag. Replace the previous version: APPEND the new one, then delete the old UID.
- Remember which server draft a local draft corresponds to (by UID plus UIDVALIDITY, or by a custom
  header such as `X-iSupply-Draft-Id`).

## Deliverability (company-level, not client code)

SPF, DKIM and DMARC for `isupply.com` are configured by IT on the DNS and mail server. The client must
send through the company's submission server with the user's own address in `From`, or messages will
fail DMARC at recipients. List them in the server profile (`docs/domain/server-profiles/`).
