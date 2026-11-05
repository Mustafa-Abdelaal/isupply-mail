# Plan 0002: MVP mail client on Laravel + React (issue #2)

- **Status:** In progress
- **Branch:** feat/2-mvp-mail-client
- **Spec / ADR:** [ADR-0002](../decisions/0002-technology-stack.md) · [ADR-0004](../decisions/0004-server-side-mail-engine.md) · [ADR-0005](../decisions/0005-authentication-and-credential-custody.md) · [requirements](../product/requirements.md)

## Goal

A working iSupply Mail for `@isupply.com.eg` on web, desktop and mobile: sign in with address and
password, read (safely), search, organize, compose and send with attachments, filters and junk
handling, notifications. Done = every step below is checked, `scripts/check --full` is green, the UI
is verified in LTR/RTL and light/dark, and the PR is open with evidence.

## Approach

ADR-0002 option E: Laravel 13 owns IMAP/SMTP (sync into PostgreSQL, operation log, outbox, filters,
junk, push) and one React SPA runs everywhere (browser, Electron, Capacitor). Rejected alternatives
are scored in ADR-0002.

## Steps

- [x] 1. Decision records: ADR-0002 accepted, ADR-0004, ADR-0005, domain fixed to `isupply.com.eg`, product memory
- [ ] 2. Scaffold `apps/api`, `apps/web`, `apps/desktop`, `apps/mobile`; pnpm workspace; toolchain pins; dev services (PostgreSQL, Redis, GreenMail)
- [ ] 3. Wire `scripts/*`, hooks, settings, ignores, Dependabot and CI to the stack (no `STACK:` markers left)
- [ ] 4. Backend auth: IMAP-verified sign-in, domain allowlist, encrypted credentials, Sanctum cookies + device tokens, devices list/revoke
- [ ] 5. Backend sync: IMAP session wrapper, folders (roles, UTF-7, delimiter), STATUS-driven incremental sync, UIDVALIDITY reset, threading, realtime events, scheduler, IDLE watcher
- [ ] 6. Backend read path: MIME parser passing the 19-fixture conformance suite, HTML risk analyzer, allowlist sanitizer, remote-content gate, cid images, attachment downloads with filename neutralization
- [ ] 7. Backend actions and sending: operation log, flags/move/delete/junk with undo, outbox with undo-send and unknown-outcome handling, drafts, uploads, search (Arabic normalization), contacts
- [ ] 8. Backend filters, junk classifier, block/allow lists, push (Web Push, FCM, APNs) with a null driver
- [ ] 9. Web client core: sign-in, shell, folders, virtualized list, reader, actions, realtime, shortcuts, i18n en/ar + RTL, dark mode
- [ ] 10. Web client composer, search, settings (preferences, signature, filters, junk, devices)
- [ ] 11. Native shells: platform adapters, Electron (hardened, packaging), Capacitor (Android/iOS projects, push)
- [ ] 12. Verify: Playwright E2E, `/verify-ui` screenshots, reviewer subagents, docs sync, PR

## Test plan

- Unit + feature (PHPUnit on PostgreSQL): auth, policies, operation log, outbox, filters, junk classifier, search normalization.
- Fixture conformance (PHPUnit): every `fixtures/email/manifest.json` entry through the app's parser and analyzer, mirroring `scripts/tests/_support.py::conformance_errors`; sanitizer output has no dangerous constructs.
- Integration (PHPUnit `@group integration`, GreenMail): sign-in, folder sync, new mail, flags, move, send + Sent, drafts.
- Web (Vitest + Testing Library + MSW): components in loading/empty/error/success states.
- E2E (Playwright, full stack + GreenMail): sign in, read, compose and send, search, filters.

## Risks and rollback

- Real host unknown (open questions 1–5, 17–19): settings are configuration (`MAIL_IMAP_*`, `MAIL_SMTP_*`), so pointing at the real host is an env change; OAuth2 hosts need a new ADR.
- GreenMail lacks CONDSTORE/QRESYNC/SPECIAL-USE: those paths are optional fast paths; the fallback is what GreenMail exercises.
- Pushing is to the feature branch only; `main` is protected.

## Decisions log (made without asking, per owner preference P-1)

- One PR for the MVP (issue #2) with logical commits, rather than a stack of PRs: the owner reviews outcomes, not steps.
- PHP floor 8.3 (this container) with Symfony 7.4 LTS and PHPUnit 12; production images on PHP 8.4.
- TypeScript 6.0, not 7: typescript-eslint supports `<6.1`.
- Android 9+ and iOS 16+ (requirement N-09), above Capacitor 8's own floor, so Vite 8's default build targets run in every webview.
- shadcn/ui on Radix rather than Base UI: fewer of the test-automation quirks the owner hit in Postboy.

## Acceptance evidence

| Item | Evidence |
|---|---|
| | |

## Discovered (out of scope — file as issues)

## Progress log

- 2026-11-05: decisions recorded (ADR-0002/0004/0005), domain corrected, issue #2 and branch created.
- 2026-11-05: paused mid step 2 (Laravel skeleton + packages + full schema, JS workspace manifests). WIP checkpoint pushed; see HANDOVER.md.
