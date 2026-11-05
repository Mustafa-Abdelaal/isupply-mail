# Open questions

The stack is decided ([ADR-0002](../decisions/0002-technology-stack.md)); these answers now tune
configuration and later ADRs rather than the stack.
Once a question is answered, move the answer into [requirements](requirements.md) or an ADR, and
strike the line through here.

## Mail server (highest impact)

1. **Where is `@isupply.com.eg` hosted?** cPanel or shared hosting, Google Workspace, Microsoft 365, Zoho,
   or self-hosted? Run `python3 scripts/email/discover.py isupply.com.eg` from a normal network (DNS is
   blocked in sandboxed sessions) and record the result with `/discover-mail-server`.
2. Which protocols does it offer: IMAP and SMTP only, or JMAP, Exchange ActiveSync, Microsoft Graph?
3. Which IMAP extensions are there (IDLE, CONDSTORE/QRESYNC, SPECIAL-USE, MOVE, COMPRESS)? Are there
   connection limits per account or per IP?
4. How do staff authenticate: plain password, app passwords, OAuth2/SSO, 2FA? Is there a central
   directory (LDAP or Azure AD) we could use for contacts and provisioning?
5. Do we control the server (can we install a push plugin such as Dovecot `push_notification`, or add
   autoconfig DNS records)?

## Users and rollout

6. How many staff, and what's the platform split (Android vs iPhone, Windows vs Mac vs Linux)?
7. Are devices company-managed (MDM), personal (BYOD) or mixed? This drives the distribution channel
   (App Store and Play vs MDM vs direct download) and admin features.
8. Which languages: Arabic and English only? Which Arabic digit style in the UI?
9. Do shared mailboxes or delegated access exist today (sales@, accounts@)?
10. Must anything be retained or archived for compliance (legal hold, minimum retention)?

## Product scope

11. Is calendar or contacts in scope beyond showing invites?
12. Should central signatures be enforced or only suggested? Who maintains them?
13. Is there a hard deadline or a pilot group?

## Operations and budget

14. ~~Is a small backend acceptable?~~ Yes: the backend is the mail engine
    ([ADR-0002](../decisions/0002-technology-stack.md)). **Still open:** where it runs (cloud provider,
    region, data residency) and the hosting budget.
15. Who operates it (on-call), and who owns Apple/Google developer accounts and code-signing
    certificates? Push needs a Firebase project (FCM service account) and an Apple APNs key; the
    backend runs without them, with push turned off.
16. ~~What is the team's existing expertise?~~ Laravel and React (owner, 2026-11-05). **Still open:**
    who maintains the app long-term.

## Questions for IT created by the server-side design

17. Can IT allow the backend server's IP in the mail host's brute-force protection (cPHulk or
    fail2ban)? Every staff sign-in and sync arrives from that one IP ([ADR-0004](../decisions/0004-server-side-mail-engine.md)).
18. What are the host's IMAP connection limits per user and per IP? The backend uses at most two
    connections per account (one IDLE watcher, one worker).
19. Does the host save sent mail into Sent by itself? (Most cPanel hosts don't; Microsoft 365 and
    Gmail do.) The backend appends to Sent unless told otherwise (`MAIL_SMTP_SAVES_SENT`).
