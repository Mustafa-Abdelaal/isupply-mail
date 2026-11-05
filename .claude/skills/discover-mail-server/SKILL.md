---
name: discover-mail-server
description: Work out and verify mail server settings for a domain (default isupply.com.eg) — autoconfig, Thunderbird ISPDB, DNS SRV/MX, provider fingerprint, then TLS/capability/auth probing — and record a server profile in docs/domain/server-profiles/. Use for zero-config provisioning work, provider questions, or when login/connection fails.
argument-hint: "[domain]"
---

# Discover and verify mail server settings

Domain: `$ARGUMENTS` (default `isupply.com.eg`). Background reading:
[discovery-and-auth.md](../../../docs/domain/discovery-and-auth.md).

## 1. Discover candidates

`python3 scripts/email/discover.py <domain>` (or `--json`) checks domain autoconfig, the ISPDB, SRV
records, MX fingerprints and guessed hostnames.

- If DNS lookups are unavailable (sandboxed environments block DNS-over-HTTPS), say so and ask the user
  to run the command on their machine, or to paste `dig MX <domain>` and `dig SRV _imaps._tcp.<domain>`.
- An MX fingerprint changes the plan:
  - **Google Workspace or Microsoft 365**: OAuth2 is mandatory. Microsoft 365 may be better served by
    Microsoft Graph than IMAP. Raise an ADR.
  - **cPanel/Plesk/shared hosting**: password auth over TLS. Expect certificate-name mismatches and
    connection limits.

## 2. Verify with a probe

`python3 scripts/email/probe_server.py --imap HOST:993 --smtp HOST:465 --json`. Without credentials it
collects pre-auth capabilities and TLS details.

For post-auth data (folders, SPECIAL-USE, quotas), the user provides a **test account**: they export
`MAIL_PASSWORD` themselves, then you add `--user test@domain --password-env MAIL_PASSWORD`. Never ask
for a password in chat, never put one in a command line or file, and never use a real staff mailbox
without explicit consent.

Record:

- TLS version, the certificate's names (do they match the hostname we'll configure?) and its expiry
- IMAP capabilities: IDLE, CONDSTORE/QRESYNC, MOVE, UIDPLUS, SPECIAL-USE, UTF8=ACCEPT, COMPRESS, QUOTA
- The folder delimiter, special-use folders and localized folder names
- SMTP: AUTH mechanisms, SIZE limit, SMTPUTF8, and 465 vs 587
- Connection limits, if the user's hosting panel exposes them

## 3. Write the profile

Create `docs/domain/server-profiles/<domain>.md` from the
[template](../../../docs/domain/server-profiles/README.md): the settings table, capabilities matrix,
auth method, quirks, the date probed, and who ran the probe. **No credentials, no usernames beyond the
pattern** (`%EMAILADDRESS%`).

## 4. Feed decisions

- Capabilities that matter for architecture (no CONDSTORE, OAuth-only, connection caps) get recorded
  in `docs/product/open-questions.md` and, once decided, in an ADR.
- The provisioning config the app ships for `@isupply.com.eg` must match this profile. Mention that in the
  PR that changes either one.
