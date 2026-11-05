# MIME: parsing, display and composition

RFC 5322 (message format), RFC 2045–2049 (MIME), RFC 2047 (encoded words), RFC 2231 (parameter
encoding), RFC 6532 (UTF-8 headers), RFC 2392 (cid:), RFC 3676 (format=flowed), RFC 5545/5546
(iCalendar/iTIP).

The **reference behavior** is `scripts/email/emaillib.py::summarize`, and the **answer key** is
`fixtures/email/manifest.json`. The app's MIME layer must produce the same results for every fixture.

## Robustness principle

Be lenient when parsing and strict when generating. Real mail is full of broken MIME, so degrade
gracefully, record the defect and keep going. Never throw on a message. Bound resource use: maximum
nesting depth (around 20), maximum parts (around 500), maximum decoded size per part, and decode
streams lazily.

## Headers

- **Unfold** (remove CRLF before WSP), then decode **RFC 2047** encoded-words
  (`=?charset?B|Q?...?=`). Whitespace *between two adjacent encoded words* is dropped; whitespace
  between an encoded word and plain text is kept (fixtures 002, 003).
- Tolerate encoded words in places the RFC forbids (inside quoted strings, Outlook-style filenames), and
  **raw UTF-8** (RFC 6532, fixture 017) as well as raw legacy 8-bit bytes. For the latter, try UTF-8,
  then the message's body charset, then windows-1256 or latin-1.
- Header names are case-insensitive (fixture 016). Headers that should appear once (Subject, From,
  Date) may appear twice; take the first.
- **Dates**: parse RFC 5322 with obsolete forms. Missing or unparseable → fall back to IMAP
  INTERNALDATE (fixture 016). Store UTC; display in the user's timezone (Africa/Cairo has DST since 2023).
- **Addresses**: groups (`undisclosed-recipients:;`), quoted display names, comments, IDN domains,
  and missing display names. Display name + address must both be shown when they disagree in
  suspicious ways (phishing).

## Structure and what to show

```
multipart/mixed                     ← attachments live here
├── multipart/related               ← HTML + the images it references by cid:
│   ├── multipart/alternative       ← same content, increasing fidelity
│   │   ├── text/plain
│   │   └── text/html               ← show this (last renderable alternative)
│   └── image/png (Content-ID)      ← INLINE, not an attachment
└── application/pdf (attachment)
```

- `multipart/alternative`: prefer the **last** part you can render (usually HTML). Keep text/plain
  for previews, search and "show as plain text".
- `multipart/related`: parts referenced via `cid:` from the HTML are **inline**, so render them in
  place and don't list them as attachments (fixtures 005, 007), even when they have a filename.
- An image with `Content-Disposition: inline` but no reference is shown below the body, or as an attachment.
- `message/rfc822`: an attached email (forward-as-attachment, fixture 018). Show it as an openable
  message, and don't merge its body into the outer body.
- `text/calendar; method=REQUEST|CANCEL|REPLY`: a meeting invite (fixture 013). Show the event
  summary, time in the user's timezone, location and organizer, plus actions later (R-18).
- `application/ms-tnef` (`winmail.dat`): Outlook-proprietary. Extract the attachments, or show it as a
  file with an explanation.
- A part with no headers defaults to `text/plain; charset=us-ascii`. A missing closing boundary still
  yields the parts seen so far, plus a defect (fixture 014).

## Charsets (Arabic matters)

The fallback chain for text parts is the declared charset, then UTF-8, then windows-1256, then latin-1
(which never fails), with a warning recorded.

- **windows-1256** (fixture 004) and **ISO-8859-6** are common for Arabic from older Outlook installs.
  Decoding them as latin-1 produces mojibake like `ÚÑÖ ÃÓÚÇÑ`.
- Aliases: `cp1256` and `x-cp1256`. Treat `iso-8859-1` labels as windows-1252 (as browsers do).
- Labels are sometimes wrong (UTF-8 bytes declared as windows-1256). Consider validating UTF-8 first
  when the declared charset is a single-byte one and decoding produces mostly control characters.
- Transfer encodings: 7bit, 8bit, binary, quoted-printable (soft line breaks `=\r\n`) and base64
  (ignore whitespace and tolerate missing padding).

## Attachments and filenames

- The filename comes from `Content-Disposition` `filename`, then `Content-Type` `name`. Decode RFC 2231
  (`filename*=UTF-8''...`, including continuations `filename*0*=`; fixture 006) and tolerate RFC 2047
  in quotes.
- **Neutralize before display and save** (fixture 019): strip or flag bidi controls (U+202E
  RIGHT-TO-LEFT OVERRIDE makes `invoice[U+202E]fdp.exe` look like `invoiceexe.pdf`), path separators and
  `..`, control characters, and Windows reserved names (`CON`, `PRN`, `AUX`, `NUL`, `COM1`–`9`,
  `LPT1`–`9`). Warn on executable extensions. Never trust the declared content type for safety
  decisions.

## Threading

1. Group by `References` chain and `In-Reply-To` (JWZ-style). A message with only `In-Reply-To`
   still joins its parent (fixture 010).
2. Fall back to the **normalized subject** within a time window, only when references are missing.
   Strip `Re:`, `RE:`, `Fwd:`, `FW:`, `AW:`, `SV:`, `TR:`, Arabic `رد:` and `إعادة توجيه:`, and list
   tags like `[sales]` (see `normalize_subject`).
3. Quoted text: `>` markers (plain text), `<blockquote type="cite">` (HTML), Outlook's
   `-----Original Message-----` / `From: … Sent: …` blocks (fixture 009) and Gmail's
   `<div class="gmail_quote">`. Collapse them behind "show quoted text".

## Composing

Generate UTF-8 `multipart/alternative` (plain plus HTML), or `multipart/related` when there are inline
images, inside `multipart/mixed` when there are attachments. Encode headers with RFC 2047, and use
RFC 2231 for non-ASCII filenames (never RFC 2047 in parameters). Keep lines ≤ 998 octets with CRLF.
Use `format=flowed` for plain text if we support it. Replies quote the original with an attribution
line in the user's language.
