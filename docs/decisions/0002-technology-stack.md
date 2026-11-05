# ADR-0002: Technology stack

- **Status:** Proposed — pending the stack discussion
- **Date:** 2026-11-05
- **Deciders:** project owner (+ team)
- **Decision:** _to be filled on acceptance — languages, frameworks and versions per layer_
- **Related:** [requirements](../product/requirements.md) · [open questions](../product/open-questions.md) · [architecture](../architecture/overview.md)

## Context

We need one product on six targets (web, Windows, macOS, Linux, Android, iOS), built and maintained
mostly by AI agents with a small team. Facts that hold whatever we choose:

- **The web client cannot speak IMAP/SMTP.** Browsers have no raw TCP sockets, so a server-side
  gateway is required for web.
- **Mobile push needs a server component.** iOS and Android won't keep IMAP IDLE connections alive in
  the background.
- The mail server and auth model for `@isupply.com` are not yet confirmed (open questions 1–5), and
  they may force OAuth2, Graph or EWS, or allow server-side push.
- Agents work best with statically typed languages, fast deterministic test runners, strong linters
  and analyzers, good docs, and one language across as many layers as possible.

## Decision drivers (draft weights, to be agreed)

| # | Driver | Weight |
|---|---|---|
| D1 | One shared codebase and UI across all six targets (velocity, consistency) | 5 |
| D2 | Mature email protocol and MIME libraries (IMAP extensions, robustness, OAuth2 SASL) | 5 |
| D3 | Safe, high-fidelity HTML email rendering on every platform (sandboxed webview/iframe) | 4 |
| D4 | Native integrations: secure storage, push, background work, `mailto:`, notifications | 4 |
| D5 | Performance with 100k-message folders, offline storage | 4 |
| D6 | Team familiarity and hiring and maintenance reality | 4 |
| D7 | Agent-friendliness: types, test speed, tooling, documentation quality | 3 |
| D8 | Backend fit (gateway, push relay, provisioning), ideally sharing the language | 3 |

## Options to evaluate

These are starting points for the discussion. Use the `tech-researcher` subagent for current, cited
facts before scoring.

- **A. Flutter (Dart)**: one UI toolkit for all six targets, with Dart email libraries for
  native/desktop and a backend gateway for web.
- **B. TypeScript everywhere**: React web, Tauri or Electron for desktop, React Native or Expo for
  mobile, Node backend, and shared TS core packages.
- **C. Kotlin Multiplatform plus Compose Multiplatform**: a shared Kotlin core, Compose UI (iOS and web
  support maturity to verify), and a JVM-mail-ecosystem backend.
- **D. Rust core plus thin UIs**: the sync engine and MIME in Rust via FFI, with Flutter, native or Tauri
  UIs. The highest robustness ceiling, but the highest complexity.
- **E. Server-centric**: a backend does all IMAP/SMTP sync (or JMAP, for example via a JMAP server in
  front of the mailbox). Every client is a thin API/JMAP client; web and mobile push come naturally.
  Can be combined with A–D.

## Questions this ADR must answer when accepted

1. The client UI framework(s) and language, with minimum OS versions.
2. Where the sync engine runs: on the device (all native targets) or on the server (gateway or JMAP), or both.
3. Local storage engine and search index; encryption at rest per platform.
4. The HTML rendering approach per platform (sandboxed iframe or webview, sanitizer library).
5. Backend scope (web gateway, push relay, provisioning and config service), its language, and hosting.
6. Monorepo layout, package manager, build and release tooling, and the test frameworks per tier.

## Decision

_Pending._ On acceptance, fill in **Decision** in the header, set the status to `Accepted (date)`,
then run `/bootstrap-stack`.
