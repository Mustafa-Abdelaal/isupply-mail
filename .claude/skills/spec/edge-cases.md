# Email edge-case checklist for specs

Keep each item that applies, and say what the feature does in that situation.

## Data and scale

- [ ] Huge folders (100k+ messages) and long threads (200+ messages)
- [ ] Large messages and attachments (25 MB+), and server size limits on send (SMTP `SIZE`)
- [ ] Many accounts or shared mailboxes (sales@, support@)

## Network and server behavior

- [ ] Offline, flaky mobile network or captive portal: what is cached, what is queued, what the UI shows
- [ ] Servers without IDLE, CONDSTORE/QRESYNC, MOVE, SPECIAL-USE or UTF8=ACCEPT (common on cPanel hosting)
- [ ] Concurrent changes from another client (desktop Outlook moves or deletes the same message)
- [ ] UIDVALIDITY reset (folder recreated or restored by IT) and server-side expunge mid-sync
- [ ] Connection limits per account, throttling, temporary (4xx) vs permanent (5xx) SMTP errors
- [ ] Password changed or account disabled while the app is running

## Content

- [ ] Arabic/RTL subjects and bodies, mixed bidi text, Arabic folder names
- [ ] Legacy charsets (windows-1256, ISO-8859-6), wrong or missing charset labels
- [ ] Malformed MIME, missing boundaries, LF-only messages, very long header lines
- [ ] HTML with active content, remote images, tracking pixels, phishing links (see the security fixtures)
- [ ] Inline images (cid:), forwarded messages (message/rfc822), calendar invites, winmail.dat
- [ ] Hostile attachment names (RTL override, path traversal, reserved names, executables)

## People and time

- [ ] Time zones (Africa/Cairo, which has DST since 2023), dates in Arabic locales, 12/24h
- [ ] Contacts with Arabic names, duplicate display names, groups and undisclosed recipients
- [ ] Non-technical users: undo, confirmations, plain-language errors, accessibility

## Platforms

- [ ] Mobile background limits (iOS especially): what happens while the app is suspended
- [ ] Web without native sockets (gateway required), browser storage quotas, multiple tabs
- [ ] Desktop: OS keychain, notifications, `mailto:` handler, auto-update, multiple windows
