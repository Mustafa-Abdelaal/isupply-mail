# Server profiles

One file per mail domain we support: `<domain>.md`, created and updated with `/discover-mail-server`.
The app's provisioning config must match these profiles.

**Never include credentials or real usernames.** Use patterns like `%EMAILADDRESS%`.

## Template

```markdown
# <domain>

- Probed: YYYY-MM-DD by <who> with scripts/email/probe_server.py (+ discover.py)
- Provider: <cPanel/Dovecot | Microsoft 365 | Google Workspace | ...> (MX: ...)

| Role | Protocol | Host | Port | Security | Auth | Username |
|---|---|---|---|---|---|---|
| incoming | IMAP | mail.example.com | 993 | SSL/TLS | password (PLAIN) | %EMAILADDRESS% |
| outgoing | SMTP | mail.example.com | 465 | SSL/TLS | password (PLAIN) | %EMAILADDRESS% |

## TLS
Certificate CN/SAN: ... (matches host? yes/no) · issuer · expiry

## IMAP capabilities
IDLE ✅ · CONDSTORE ✅ · QRESYNC ✅ · MOVE ✅ · UIDPLUS ✅ · SPECIAL-USE ✅ · UTF8=ACCEPT ❌ · COMPRESS ❌ · QUOTA ✅
Delimiter: `.` · Namespace: `INBOX.` · Special folders: Sent=`INBOX.Sent` ...

## SMTP
AUTH: PLAIN LOGIN · SIZE: 52428800 · SMTPUTF8: ❌ · saves to Sent automatically: ❌

## Limits & quirks
- Max concurrent IMAP connections per user/IP: ...
- ...

## Implications
- e.g. "No QRESYNC → UID-range diff sync path required"
```
