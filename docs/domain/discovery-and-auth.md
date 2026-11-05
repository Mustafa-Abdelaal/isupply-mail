# Zero-config account setup: discovery, provisioning and authentication

Zero configuration is the product's core promise (R-01). A staff member types an address and a
password, and the app must find the right servers, authenticate safely and store credentials securely.

## How the app should find server settings (in order)

1. **Central provisioning** (preferred, because we control `isupply.com.eg`): the app ships, or fetches
   from our backend over HTTPS (signed and versioned), a provisioning profile for `@isupply.com.eg`
   containing the IMAP and SMTP hosts, ports and security, the auth method, the signature template,
   feature flags and minimum app version. This is fast, deterministic and lets IT change servers
   without app updates.
2. **Domain autoconfig** (Thunderbird format): `https://autoconfig.<domain>/mail/config-v1.1.xml` and
   `https://<domain>/.well-known/autoconfig/mail/config-v1.1.xml`. IT can publish this for the domain,
   and it also helps Thunderbird and other clients.
3. **Thunderbird ISPDB** (`https://autoconfig.thunderbird.net/v1.1/<domain>`) for big providers.
4. **DNS SRV** (RFC 6186 / 8314): `_submissions._tcp`, `_submission._tcp`, `_imaps._tcp`, `_imap._tcp`,
   plus `_jmap._tcp` (RFC 8620).
5. **MX fingerprint**: Google, Microsoft 365, Zoho, GoDaddy and others mean known settings and known
   auth requirements.
6. **Guesses** (`mail.<domain>`, `imap.<domain>`, `smtp.<domain>`), verified by probing. They are
   never used without a successful TLS plus login test.

`scripts/email/discover.py` implements steps 2–6 for research. `/discover-mail-server` turns the
results into a server profile in `docs/domain/server-profiles/`.

**Security**: never downgrade to plaintext because discovery suggested it. Only accept discovered
hosts under the user's domain or a known provider; otherwise warn. An attacker-controlled autoconfig
can harvest passwords.

## Authentication

| Method | When | Notes |
|---|---|---|
| Password over TLS (SASL PLAIN/LOGIN) | cPanel/shared hosting, self-hosted | Most likely for `@isupply.com.eg`; confirm. Test once at sign-in and show a plain-language error ("wrong password" vs "can't reach server") |
| App password | Google/iCloud/Yahoo with 2FA | Explain it in the UI only if relevant |
| OAuth2 (XOAUTH2 / OAUTHBEARER) | Google Workspace, Microsoft 365 (mandatory there) | Authorization Code + **PKCE** in the **system browser** (never an embedded webview). Store the refresh token in secure storage. Needs app registration with the provider |
| Kerberos/NTLM | On-prem Exchange | Out of scope unless the open questions say otherwise |

## Credential storage (N-01)

| Platform | Store |
|---|---|
| iOS / macOS | Keychain (accessibility `AfterFirstUnlockThisDeviceOnly` for background sync, excluded from backups) |
| Android | Android Keystore-backed encryption (no plain SharedPreferences) |
| Windows | Credential Manager / DPAPI |
| Linux | Secret Service (libsecret). Detect when it's missing and explain; never fall back to plaintext silently |
| Web | No raw mail password in the browser: the gateway holds credentials server-side (encrypted) and the browser gets an httpOnly, SameSite session cookie |

Sign-out (and admin revoke, R-20) wipes the credentials, tokens and local cache.

## Error messages people understand

| Situation | Say |
|---|---|
| Auth failed | "That password didn't work for name@isupply.com.eg. Check it and try again." (plus a "Forgot password?" link per IT policy) |
| Server unreachable | "Can't reach the iSupply mail server. Check your internet connection." |
| TLS failure | "The connection to the mail server isn't secure, so we stopped." Never offer "continue anyway" |
| Account locked/disabled | "Your account is locked. Contact IT." |
