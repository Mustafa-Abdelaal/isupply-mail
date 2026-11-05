# ADR-0004: Server-side mail engine (sync, operation log, outbox, push)

- **Status:** Accepted (2026-11-05)
- **Date:** 2026-11-05
- **Deciders:** project owner (delegated), Claude (agent)
- **Related:** [ADR-0002](0002-technology-stack.md) · [imap.md](../domain/imap.md) · [smtp.md](../domain/smtp.md) · [threat model](../security/threat-model.md) · R-02, R-03, R-06, R-07, R-08, R-15, R-19, N-05, N-07

## Context

ADR-0002 puts IMAP and SMTP on the server. That server must keep a correct, fast copy of each mailbox,
apply user actions without losing them, send reliably, and tell clients and phones when mail arrives,
all within the mail host's connection limits. The host is not yet known (open questions 1–5): it may
lack CONDSTORE/QRESYNC (like GreenMail and many cPanel servers), so the fallback paths must be first-class.

## Decision drivers

| # | Driver | Weight (1–5) |
|---|---|---|
| D1 | Correctness: UID/UIDVALIDITY identity, never mark mail read by accident, never lose an action or a send | 5 |
| D2 | Works on the weakest likely server (no CONDSTORE/QRESYNC/SPECIAL-USE) | 5 |
| D3 | Few IMAP connections per account, and gentle on brute-force protection | 4 |
| D4 | Fast lists and search for 100k-message folders | 4 |
| D5 | Simple to operate on one VM | 3 |

## Options considered

- **A. Stateless gateway** (open IMAP per request, like classic webmail): no copy of mail, but slow
  lists, no server-side search across folders, no filters or push while users are away. Rejected on D4.
- **B. Sync into PostgreSQL with a durable operation log (chosen)**: the server mirrors folder and
  message metadata, caches opened bodies, and queues every mutation in an ordered table.
- **C. Put a JMAP server (for example Stalwart) in front of the mailbox**: elegant protocol, but adds a
  second mail server to operate and still needs our own push and filters. Revisit if we ever host mail.

## Decision

We choose **B**.

### Mirror

- Accounts, folders and messages live in PostgreSQL. A message is keyed by **(folder, UID)** under
  the folder's stored **UIDVALIDITY**; when UIDVALIDITY changes, the folder's messages are dropped and
  resynced (imap.md: Identity).
- Folders come from `LIST` with the server's delimiter, names decoded from modified UTF-7, and roles
  (inbox, sent, drafts, trash, junk, archive) from SPECIAL-USE, falling back to English and Arabic names.
- Message rows hold the envelope (from, to, cc, subject, dates, Message-ID, In-Reply-To, References),
  flags, size, an attachment hint, a preview snippet, a thread id and a search vector.
- **Bodies are lazy**: the first open fetches the full message with `BODY.PEEK[]`, parses it (the parser
  passes the fixture corpus), sanitizes the HTML and stores the result. The raw source is kept in a
  private, evictable cache so attachments and inline images can be served without refetching.

### Sync algorithm (per folder)

1. `STATUS (MESSAGES UIDNEXT UIDVALIDITY UNSEEN)`, plus `HIGHESTMODSEQ` when CONDSTORE is advertised.
   Unchanged values mean nothing to do (and with CONDSTORE, flags are known unchanged as well).
2. `EXAMINE` (read-only), then fetch new UIDs from the stored UIDNEXT in batches:
   `UID FLAGS INTERNALDATE RFC822.SIZE BODYSTRUCTURE BODY.PEEK[HEADER.FIELDS (...)]`.
3. First sync is windowed: the newest N messages (default 1,000) first, older ones backfilled in later
   jobs down to a configurable depth.
4. Flags: with CONDSTORE, `UID FETCH 1:* (FLAGS) (CHANGEDSINCE modseq)`; without it, re-read flags
   for a recent window (default the newest 500).
5. Deletions: when the message count disagrees, compare `UID SEARCH ALL` with the mirror in UID chunks.
6. Messages with pending operations keep their local state until the operation has been applied.

**Triggers**: the scheduler checks every account's Inbox each minute and other folders every ten
minutes; opening a folder in a client syncs it if it is older than 30 seconds; an IMAP IDLE watcher
(`mail:watch`, one process, one IDLE connection per active account on the Inbox) triggers a sync
within seconds of new mail.

### Operation log (mutations)

Every user action (flags, move, archive, delete, junk/not junk, draft save, send) writes the new state
to the mirror immediately (optimistic), and appends a row to `mail_operations`. One job per account
applies pending operations **in id order** under a per-account lock, using `UID STORE`, `UID MOVE`
(falling back to `UID COPY` + `\Deleted` + `UID EXPUNGE`, never plain `EXPUNGE`) and `APPEND`. A
temporary failure retries with backoff; a permanent one rolls the mirror back and tells the client.

### Outbox (sending)

A send is an operation with an **undo window** (default 10 seconds, per user). After it, the message
is built with Symfony Mime (UTF-8, multipart/alternative, RFC 2231 filenames, Bcc only in the envelope),
submitted over SMTP with verified TLS (implicit TLS on 465 preferred; STARTTLS on 587 fails closed),
appended to Sent unless the server saves sent mail itself, and the replied or forwarded message gets
`\Answered` or `$Forwarded`. **A timeout or disconnect after DATA marks the send "unknown"**: it is
never retried automatically, the user sees it, and the next Sent sync looks for its Message-ID.

### Filters and junk

New Inbox mail passes the user's rules (Thunderbird-style conditions and actions) and the junk check
(server spam headers, block and allow lists, and a per-account Bayesian classifier trained by "Junk"
and "Not junk") right after it is synced, so rules work even when every client is closed.

### Realtime and push

Mirror changes are broadcast on the user's private channel (Laravel Reverb), and clients refetch what
changed. New Inbox mail that survives filters and junk sends a **content-free** push ("2 new messages")
to the user's registered devices (FCM, APNs, Web Push); including sender and subject is an admin opt-in.

### Limits

At most two IMAP connections per account: one IDLE watcher and one worker (the per-account lock).
Authentication failures stop syncing for that account, mark it "needs password" and ask the user, so
the backend never hammers the mail host and trips cPHulk/fail2ban for the shared server IP.

## Consequences

- Positive: fast paged lists and cross-folder search from the database; durable, ordered actions;
  filters, junk handling and push that work around the clock; one place to fix sync bugs.
- Negative / trade-offs accepted: a database copy of mailbox metadata and opened bodies; sync delay of
  seconds (IDLE) to a minute (polling) on servers that the watcher cannot reach; the backfill depth
  bounds how far back offline search reaches until a server-side search fallback exists.
- Follow-ups: a Dovecot dev profile to exercise CONDSTORE/QRESYNC; QRESYNC `VANISHED` support; a
  server-side IMAP SEARCH fallback for mail older than the backfill window; an image proxy for
  remote content.
- Revisit if: the mail host offers push hooks (Dovecot `push_notification`) or JMAP, or per-IP
  connection caps prevent one IDLE connection per account.
