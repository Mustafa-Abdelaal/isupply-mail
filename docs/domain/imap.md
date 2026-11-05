# IMAP for client developers

The parts of IMAP (RFC 9051 IMAP4rev2, RFC 3501 IMAP4rev1, plus extensions) that a sync engine must get
right, and the ways real servers deviate. Check the **Server matrix** before relying on an extension.

## Identity: UID, UIDVALIDITY, sequence numbers

- **Sequence numbers** (1…N) renumber on every expunge. Never store them, and never use them across commands
  when another client may be active; use `UID FETCH/STORE/SEARCH/COPY/MOVE/EXPUNGE`.
- **UID** is unique within a mailbox *for a given UIDVALIDITY*. The key of a cached message is
  **(account, mailbox name, UIDVALIDITY, UID)**.
- **UIDVALIDITY change** (folder recreated, server migration, restore from backup) means every cached
  UID for that mailbox is invalid: drop the folder cache, keep local-only data (drafts in progress), and
  resync. Detect it on every `SELECT`/`EXAMINE`/`STATUS`.
- **UIDNEXT** is a hint: new messages have UID ≥ UIDNEXT, but UIDs can have gaps.
- **Message-ID** is not an identity: it can be missing, duplicated (the same message in several folders,
  or resent), or forged. Use it for threading and dedupe heuristics only.

## Sync strategy

1. **First sync of a folder**: newest first, windowed (for example the last 30 days or 500 messages),
   then backfill in the background. Fetch `UID FLAGS INTERNALDATE RFC822.SIZE BODYSTRUCTURE
   BODY.PEEK[HEADER.FIELDS (FROM TO CC SUBJECT DATE MESSAGE-ID IN-REPLY-TO REFERENCES ...)]` and,
   optionally, a short preview through a partial fetch of the first text part (`BODY.PEEK[1]<0.2048>`).
2. **Incremental, with CONDSTORE/QRESYNC** (RFC 7162): `ENABLE QRESYNC`, then
   `SELECT box (QRESYNC (uidvalidity modseq known-uids))`. The server sends changed flags and `VANISHED`
   UIDs. This is the efficient path; store `HIGHESTMODSEQ` per folder.
3. **Incremental, without them** (common on cPanel and GreenMail): fetch new messages with
   `UID FETCH <uidnext>:*`, refresh flags for a recent window (`UID FETCH 1:* (FLAGS)` is expensive on
   huge folders, so window it), and detect deletions by comparing `UID SEARCH ALL` (or ESEARCH) with the
   cache, in chunks.
4. **Bodies are lazy**: download on open, or prefetch for recent mail on Wi-Fi. Fetch attachments only
   on demand.
5. **Always `BODY.PEEK`**: plain `BODY[...]` sets `\Seen` as a side effect.

## Real-time updates

- **IDLE** (RFC 2177) watches one selected mailbox per connection. Re-issue it at least every **29
  minutes** (servers drop idle connections, often sooner behind NAT; 10–20 minutes is safer on mobile).
  Process untagged `EXISTS`, `EXPUNGE`, `FETCH (FLAGS)` and `VANISHED` responses.
- Watching several folders means one connection each, which runs into connection limits. Usually IDLE
  only on the Inbox and poll the rest with `STATUS` (or `NOTIFY`, RFC 5465, which is rarely supported).
- **Mobile background**: iOS and Android suspend the app and kill its sockets. Real push requires a
  server-side component that watches mailboxes (IDLE or a server plugin such as Dovecot
  `push_notification`) and sends APNs/FCM pushes. Design for this from day one.

## Folders (mailboxes)

- **Delimiter**: take it from the `LIST "" ""` response. It's `.` on many Dovecot/cPanel setups (and on
  GreenMail) and `/` elsewhere. Never assume one.
- **Names on the wire** are modified UTF-7 (RFC 3501 §5.1.3) unless `UTF8=ACCEPT` (RFC 6855) is enabled.
  Encode and decode at the protocol boundary (`scripts/email/emaillib.py` has a reference
  implementation, with tests), and quote names properly.
- **Special folders**: use SPECIAL-USE (RFC 6154: `\Sent \Drafts \Trash \Junk \Archive \All \Flagged`)
  from `LIST (SPECIAL-USE)` or `LIST-EXTENDED`. Fall back to known localized names, including Arabic
  Outlook names such as `العناصر المرسلة` (Sent Items) and `العناصر المحذوفة` (Deleted Items), and English
  variants (Sent, Sent Items, Sent Messages, INBOX.Sent). If the folder is still missing, create it and
  remember the mapping per account.
- `INBOX` is case-insensitive and special. Other names are case-sensitive on most servers.
- Some servers present every folder under an `INBOX.` prefix (personal namespace). Check `NAMESPACE`
  (RFC 2342).
- `\Noselect` / `\NonExistent` folders are containers only. Hide them, or show them as non-clickable.

## Flags and actions

- System flags: `\Seen \Answered \Flagged \Deleted \Draft`. Common keywords: `$Forwarded`, `$Junk`,
  `$NotJunk`, `$MDNSent`. Check `PERMANENTFLAGS` before storing custom keywords.
- **Move**: use `UID MOVE` (RFC 6851) when available. Otherwise `UID COPY`, then `UID STORE +FLAGS
  (\Deleted)`, then `UID EXPUNGE` (UIDPLUS, RFC 4315). Never use plain `EXPUNGE`, which deletes *every*
  `\Deleted` message, including other clients'.
- **Delete** moves the message to Trash. Permanent deletion happens only inside Trash, and only after
  user confirmation. Offer undo by delaying the server operation or moving it back.
- **Optimistic UI**: apply the change locally, queue the server operation, reconcile on response, and
  roll back with a visible message on failure.

## Connections, limits, robustness

- Hosting providers cap concurrent IMAP connections per account and/or per IP (often 10–20 on Dovecot,
  and per *IP*, which matters behind office NAT where many staff share one IP). Pool connections: one
  for IDLE and one or two for commands per account.
- Expect untagged responses at any time. Implement literals (`{n}`, plus `LITERAL+`/`LITERAL-`),
  timeouts per command, `NOOP` keepalive, and reconnect with exponential backoff and jitter.
- `COMPRESS=DEFLATE` (RFC 4978) saves a lot of mobile data. Enable it when it's offered.
- **Search**: `UID SEARCH CHARSET UTF-8 ...` for non-ASCII terms (Arabic). Some servers reject the
  charset, so fall back to local search. Never interpolate search terms into the command string; use
  the library's literal or quoting support.
- Send `ID` (RFC 2971) when supported (some servers log it, and Microsoft 365 may require it).

## Server matrix (fill in as we observe; cite version and date)

| Capability | GreenMail 2.1 (dev) | Dovecot (cPanel typical) | Microsoft 365 | Gmail |
|---|---|---|---|---|
| IDLE | ✅ | ✅ | ✅ | ✅ |
| CONDSTORE / QRESYNC | ❌ / ❌ | ✅ / ✅ | ✅ / ❌ | ✅ / ❌ |
| MOVE / UIDPLUS | ✅ / ✅ | ✅ / ✅ | ✅ / ✅ | ✅ / ✅ |
| SPECIAL-USE | ❌ | ✅ (if configured) | ✅ | ✅ (`[Gmail]/…`) |
| UTF8=ACCEPT | ❌ | ✅ (2.3+) | ❌ | ✅ |
| COMPRESS | ❌ | ✅ (if enabled) | ❌ | ✅ |
| Hierarchy delimiter | `.` | `.` or `/` | `/` | `/` |
| Auth | PLAIN/LOGIN | PLAIN/LOGIN | OAuth2 only | OAuth2 (or app password) |

The GreenMail column was verified in this repo (`scripts/email/probe_server.py` against `scripts/dev-mail`).
The other columns hold typical values; verify them against the actual `@isupply.com.eg` server with
`/discover-mail-server`.
