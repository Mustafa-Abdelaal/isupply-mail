---
name: threat-model
description: Design-time security analysis (STRIDE) for a feature or component of the email client — assets, data flows, trust boundaries, threats, mitigations and security acceptance criteria — recorded in docs/security/threat-model.md. Use for anything touching mail rendering, credentials, sync/storage, attachments, network, push or backend services.
argument-hint: "[feature | spec path | component]"
---

# Threat-model a feature

Input: `$ARGUMENTS`. Read [the threat model](../../../docs/security/threat-model.md) first. Extend it,
don't fork it.

## Steps

1. **Scope.** State what the feature does, which spec or ADR it comes from, and which platforms it
   runs on.
2. **Assets.** Identify what an attacker wants: credentials and tokens, message content, attachments,
   contacts, session cookies, the local cache, signing keys, push tokens.
3. **Data flow.** Draw (Mermaid or bullet list) every hop: user → UI → app core → storage, network →
   mail server/gateway, push service, OS integrations. Mark each **trust boundary**.
4. **STRIDE per boundary.** Fill a row per threat: Spoofing, Tampering, Repudiation, Information
   disclosure, Denial of service, Elevation of privilege. Email-specific threats to always consider:
   - hostile HTML/CSS/SVG in message bodies (XSS, UI redress), sanitizer bypasses, `cid:`/`data:` abuse
   - remote content used for tracking or for leaking IP addresses and read receipts
   - phishing: display-name spoofing, lookalike domains, link text vs href mismatch, "internal"-looking senders
   - attachment filename spoofing (RTL override), path traversal on save, auto-open of executables
   - credential theft: insecure storage, logs or crash reports, TLS downgrade (STARTTLS stripping), phishing login screens
   - IMAP/SMTP command or header injection through user-controlled strings
   - local data at rest on lost or stolen devices; backups; multi-user desktops
   - gateway or push relay compromise (if a backend exists): it holds mail access, so treat it as crown jewels
   - supply chain: dependencies, CI secrets, auto-update channel signing
5. **Mitigations.** For each threat give a concrete control, its status (existing/planned) and an owner.
   Prefer controls the platform enforces over app logic.
6. **Security acceptance criteria.** Write testable `SEC-n` criteria into the spec and add hostile
   fixtures via `/email-fixture` where relevant.
7. **Second opinion.** Spawn the `security-reviewer` subagent on the draft and verify its findings.
8. **Record.** Add or update the component's section in the threat model, and link it from the spec.
   Anything that needs a decision becomes an `/adr`.
