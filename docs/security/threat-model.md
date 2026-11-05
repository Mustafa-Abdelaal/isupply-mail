# Threat model

Living document. Extend it per feature with `/threat-model`, and review changes with the
`security-reviewer` subagent.

## Assets

| Asset | Why it matters |
|---|---|
| Mail credentials and OAuth tokens | Full access to a staff member's mailbox, and often to other systems through password resets |
| Message content and attachments | Contracts, prices, customer and supplier data, personal data |
| Contacts and communication patterns | Social-engineering fuel |
| Local cache on devices | Readable by whoever holds a lost or stolen device |
| Backend: gateway sessions, push tokens, provisioning signing key | One compromise affects every user |
| Release signing keys and CI secrets | Supply-chain compromise of every install |

## Adversaries

External phishers and malware senders (the most likely), network attackers (public Wi-Fi), thieves who
take devices, malicious or compromised dependencies, and a curious insider with backend access.

## Trust boundaries

1. Incoming message → our parser and renderer (**all content is hostile**)
2. App ↔ mail server, gateway and provisioning (network)
3. App ↔ OS (secure storage, file system, other apps through share/intents/URL schemes)
4. Backend ↔ mail server, and backend ↔ APNs/FCM
5. CI/CD ↔ repository, secrets and stores

## Top threats and required controls

| # | Threat (STRIDE) | Control | Verified by |
|---|---|---|---|
| T1 | Script execution through HTML email (E/I) | Allowlist sanitizer + sandbox with JS off + CSP | fixture 011; sanitizer tests |
| T2 | Tracking or IP leak through remote content (I) | Block by default; opt-in per message or sender; optional proxy | fixture 012 |
| T3 | Phishing through display-name or link spoofing (S) | External-sender banner, real link targets, lookalike-domain warning | fixture 011 link mismatch; UX review |
| T4 | Malicious attachment disguised by filename (S/E) | Filename neutralization, executable warning, no auto-open | fixture 019 |
| T5 | Credential theft from the device or logs (I) | OS secure storage only; logging redaction; crash-report scrubbing | code review; log tests |
| T6 | TLS downgrade or MITM (T/I) | Verified TLS only; STARTTLS fails closed; no bypass | integration tests; review |
| T7 | Protocol or header injection (T) | Library quoting and literals; CR/LF rejection in headers | unit tests with hostile strings |
| T8 | Data at rest on a lost device (I) | Platform encryption; app lock (later); remote wipe/revoke (R-20) | platform review |
| T9 | Gateway or push relay compromise (I/E) | Encrypt stored credentials, least privilege, no content in push, audit logs, rate limits | backend threat model (when designed) |
| T10 | Supply chain: dependencies or CI (T/E) | Pinned actions, Dependabot, least-privilege workflows, review of new deps, signed releases | `.github/` rules; review |
| T11 | Resource exhaustion through crafted MIME (D) | Limits on depth, parts and decoded size; streaming | fuzz and limit tests |
| T12 | Malicious autoconfig or discovery redirect (S/I) | Provisioning first; only accept hosts under the user's domain or known providers; never downgrade | discovery tests |

## Review checklist

Run this for any change touching mail content, credentials, network, storage, attachments,
dependencies or CI:

- [ ] Untrusted input (headers, parts, filenames, URLs, server responses) is validated and bounded
- [ ] HTML goes only through the sanitizer and sandbox; no new path renders raw HTML
- [ ] Remote resources stay blocked by default
- [ ] No credentials, tokens or message content in logs, analytics, crash reports, URLs or exceptions
- [ ] Secrets go only through the secure-storage adapter; sign-out wipes them
- [ ] TLS verification can't be disabled outside dev tooling
- [ ] Protocol commands and headers are built through quoting APIs; CR/LF rejected
- [ ] New dependency: maintained, license OK, no install scripts surprises, pinned
- [ ] CI changes: explicit least-privilege `permissions:`, no secrets to untrusted code
- [ ] Hostile fixtures still pass (011, 012, 019) and new risky shapes have fixtures
