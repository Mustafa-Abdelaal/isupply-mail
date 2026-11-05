# Requirements (draft)

Status: **draft**, refined through `/spec`. The stack is decided ([ADR-0002](../decisions/0002-technology-stack.md)). IDs are stable;
specs and ADRs reference them. Priority: **M** = MVP, **N** = next, **L** = later.

## Functional

| ID | Requirement | Pri |
|---|---|---|
| R-01 | Sign in with only email address and password; server settings come from central provisioning (fallback: discovery) | M |
| R-02 | Folder list incl. special folders (Inbox, Sent, Drafts, Trash, Junk, Archive) and nested/Arabic-named folders | M |
| R-03 | Message list: sender, subject, preview, date, unread/flagged/attachment indicators; virtualized for 100k+ messages | M |
| R-04 | Read messages: safe HTML rendering, plain text, inline images, attachments (preview/save/share), calendar invites shown | M |
| R-05 | Compose, reply, reply-all, forward; rich text; attachments; recipients autocomplete; drafts autosave | M |
| R-06 | Send reliably via a durable outbox (offline queue, retry, failure visible); copy saved to Sent | M |
| R-07 | Flag, mark read/unread, move, archive, delete with undo; multi-select | M |
| R-08 | New-mail notifications on all platforms (incl. mobile push while the app is closed) | M |
| R-09 | Search: server-side across folders, local for cached mail; filters (from, has attachment, date) | M |
| R-10 | Conversation/thread view with quoted-text collapsing | M |
| R-11 | Company signature templates (central, per user/role), Arabic and English | M |
| R-12 | Remote images blocked by default; per-message/per-sender allow | M |
| R-13 | Phishing signals: external-sender banner, link target reveal, display-name spoofing warning | M |
| R-14 | Arabic/English UI, RTL layout, `dir=auto` content, Arabic search normalization | M |
| R-15 | Offline: read cached mail, compose and queue, sync on reconnect | M |
| R-16 | Shared mailboxes / multiple accounts | N |
| R-17 | Contacts: company directory (GAL) lookup and recent recipients | N |
| R-18 | Calendar invite responses (accept/decline) | N |
| R-19 | Message filters (Thunderbird-style rules: conditions on from/to/subject/body/size/attachments; move, mark, flag, junk, delete), run on arrival server-side and on demand | M |
| R-20 | Admin: revoke device/session, remote wipe of local cache, minimum app version | N |
| R-21 | `mailto:` handling and OS share-to-email integration | N |
| R-22 | S/MIME or PGP signed/encrypted mail | L |
| R-23 | Junk filtering: honor server spam headers, an adaptive classifier trained by Junk / Not junk, sender block and allow lists | M |
| R-24 | Vacation responder (if the server supports Sieve/managesieve) | L |

## Non-functional

| ID | Requirement | Target |
|---|---|---|
| N-01 | Security | Threat model controls in place; credentials only in OS secure storage; TLS verified |
| N-02 | Privacy | No message content, subjects or addresses in logs/analytics/crash reports |
| N-03 | Performance: cold start to cached inbox | < 1.5 s desktop, < 2 s mobile (mid-range Android) |
| N-04 | Performance: open a cached message | < 150 ms; uncached < 1 s on 4G |
| N-05 | Scale | 100k messages/folder, 50 folders, 5 years of mail without degradation |
| N-06 | Battery/data (mobile) | Push instead of polling; partial fetches; COMPRESS when available |
| N-07 | Reliability | No lost drafts or sends across crashes, kills, network loss |
| N-08 | Accessibility | WCAG 2.2 AA on all platforms |
| N-09 | Platforms | Web (evergreen browsers), Windows 10+, macOS 13+, Ubuntu LTS-class Linux, Android 9+, iOS 16+ (to confirm) |
| N-10 | Maintainability | One shared core; ≥ 80% coverage of core logic; fixture conformance suite passes on every platform |
| N-11 | Observability | Crash reporting + anonymous health metrics (sync latency, error classes) |
| N-12 | Distribution | Auto-update on desktop; store or MDM distribution on mobile (see open questions) |

## Constraints known today

- Browsers cannot open IMAP/SMTP sockets, so the **web client requires a server-side gateway**
  ([architecture](../architecture/overview.md)).
- Mobile OSes do not keep IMAP connections alive in the background, so **push notifications require a
  server component** that watches mailboxes or receives server events.
- The mail server and protocols available for `@isupply.com.eg` are not yet confirmed
  ([open questions](open-questions.md)). They decide much of the architecture.
