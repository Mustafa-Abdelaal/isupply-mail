# ADR-0005: Authentication, client sessions and credential custody

- **Status:** Accepted (2026-11-05)
- **Date:** 2026-11-05
- **Deciders:** project owner (delegated), Claude (agent)
- **Related:** [ADR-0002](0002-technology-stack.md) · [ADR-0004](0004-server-side-mail-engine.md) · [discovery-and-auth.md](../domain/discovery-and-auth.md) · [threat model](../security/threat-model.md) T5, T6, T9 · R-01, R-20, N-01

## Context

Zero configuration (R-01) means staff type only their address and password. Because the backend syncs
mail while users are away (ADR-0004), it must hold a usable credential for every account, so that
credential needs custody that a stolen database or a log file can't break. Clients must also prove
who they are to the backend on six platforms, and browsers must never hold a token that JavaScript
can read (AGENTS.md rule 2).

## Decision drivers

| # | Driver | Weight (1–5) |
|---|---|---|
| D1 | No credential readable from a database dump, backup, log or browser storage | 5 |
| D2 | Zero configuration: address + password, nothing else | 5 |
| D3 | Revocable per device; sign-out really signs out | 4 |
| D4 | No new identity system for IT to run | 4 |
| D5 | Room for OAuth2 if the host turns out to be Microsoft 365 or Google | 3 |

## Options considered

- **A. A separate app account** (our own passwords): a second password for staff and a user database
  for IT. Rejected on D2 and D4.
- **B. The mail server as the identity provider (chosen)**: sign-in succeeds when IMAP `LOGIN` (or
  `AUTHENTICATE`) succeeds against the provisioned host; the user record is created on first sign-in.
- **C. Company SSO** (Azure AD/LDAP): best long term if it exists, unknown today (open question 4).

## Decision

We choose **B**, with these rules:

1. **Domain allowlist and provisioning.** Only addresses in `MAIL_DOMAINS` (default
   `isupply.com.eg`) may sign in. Servers, ports, TLS mode and the username pattern come from the
   backend's provisioning config, never from the client, so a client can't point the backend at an
   attacker's server (threat T12).
2. **Verification.** Sign-in opens an IMAP session with verified TLS and authenticates. Errors map to
   the plain-language messages in discovery-and-auth.md. Attempts are throttled per address and per
   client IP, which also protects the shared backend IP from the mail host's brute-force lockout.
3. **Custody.** The mail password is stored only as ciphertext (libsodium secretbox, XSalsa20-Poly1305)
   under a dedicated key, `MAIL_CREDENTIALS_KEY`, separate from `APP_KEY`, with a key id prefix so keys
   can rotate. It is decrypted only inside the worker that opens the IMAP/SMTP session, is never
   serialized into queued jobs, API responses or logs, and is wiped when the user signs out of every
   device or an admin revokes the account.
4. **Password changes.** When the host rejects the stored password, the account is marked
   "needs password", syncing stops, and clients ask the user to enter the new one.
5. **Client sessions.**
   - **Web**: Sanctum SPA authentication: an HttpOnly, Secure, SameSite=Lax session cookie plus a
     CSRF token. Nothing secret is reachable from JavaScript or `localStorage`.
   - **Desktop and mobile**: a Sanctum personal access token per device, stored only through the
     platform secure-storage adapter (Keychain, Android Keystore, Electron `safeStorage`), sent as a
     bearer token, and listed under Settings → Devices so it can be revoked.
6. **OAuth2 later.** The IMAP/SMTP session layer accepts either a password or an XOAUTH2 token, so a
   Microsoft 365 or Google host needs a new ADR and an OAuth client, not a rewrite.

## Consequences

- Positive: one password (the mail password) for staff; no user database for IT; per-device revoke;
  a database dump alone reveals no credentials.
- Negative / trade-offs accepted: whoever controls the running backend and its key can read mail, as
  with any server-side client; the backend needs good secret handling (`MAIL_CREDENTIALS_KEY` in the
  deployment's secret store, never in git).
- Follow-ups: an admin revoke and remote-wipe policy (R-20); app lock on mobile; OAuth2 ADR if needed.
- Revisit if: IT introduces SSO, or the host requires OAuth2.
