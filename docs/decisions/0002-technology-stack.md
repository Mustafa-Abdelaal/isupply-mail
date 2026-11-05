# ADR-0002: Technology stack

- **Status:** Accepted (2026-11-05)
- **Date:** 2026-11-05
- **Deciders:** project owner (stated the constraints and delegated the choice), Claude (agent)
- **Decision:** server-side mail engine on Laravel 13 (PHP 8.4) + PostgreSQL + Redis, and one React 19 + TypeScript 6 SPA shipped as web, Electron 45 desktop and Capacitor 8 mobile apps
- **Related:** [requirements](../product/requirements.md) · [open questions](../product/open-questions.md) · [architecture](../architecture/overview.md) · [ADR-0004 mail engine](0004-server-side-mail-engine.md) · [ADR-0005 auth and credentials](0005-authentication-and-credential-custody.md)

## Context

We need one product on six targets (web, Windows, macOS, Linux, Android, iOS), built and maintained
mostly by AI agents with a small team. Facts that hold whatever we choose:

- **The web client cannot speak IMAP/SMTP.** Browsers have no raw TCP sockets, so a server-side
  gateway is required for web.
- **Mobile push needs a server component.** iOS and Android won't keep IMAP IDLE connections alive in
  the background.
- The mail server and auth model for `@isupply.com.eg` are not yet confirmed (open questions 1–5), and
  they may force OAuth2, Graph or EWS, or allow server-side push.
- Agents work best with statically typed languages, fast deterministic test runners, strong linters
  and analyzers, good docs, and one language across as many layers as possible.

**Owner direction (2026-11-05).** "My preferred backend is Laravel and for frontend usually React."
The owner wants a normal email app (send and receive, inbox and sent, filters, attachments, spam
filtering) modelled on well-known clients such as Thunderbird, on every platform including mobile,
and asked the agent to pick the best tools without a long comparison. The owner's GitHub profile also
lists Flutter, so option A was scored honestly rather than dropped.

## Decision drivers

Written before scoring (draft weights from the proposal). D6 rose from 4 to 5 once the owner stated a
stack preference.

| # | Driver | Weight |
|---|---|---|
| D1 | One shared codebase and UI across all six targets (velocity, consistency) | 5 |
| D2 | Mature email protocol and MIME libraries (IMAP extensions, robustness, OAuth2 SASL) | 5 |
| D3 | Safe, high-fidelity HTML email rendering on every platform (sandboxed webview/iframe) | 4 |
| D4 | Native integrations: secure storage, push, background work, `mailto:`, notifications | 4 |
| D5 | Performance with 100k-message folders, offline storage | 4 |
| D6 | Team familiarity and hiring and maintenance reality | 5 |
| D7 | Agent-friendliness: types, test speed, tooling, documentation quality | 3 |
| D8 | Backend fit (gateway, push relay, provisioning), ideally sharing the language | 3 |

## Options considered

### A. Flutter on every client, with a Laravel backend for the web gateway and push

- Pros: one UI toolkit for six targets; good native integrations; the owner has Flutter experience.
- Cons: two sync engines (Dart on devices, PHP gateway for web) or a web build that behaves
  differently; Dart's IMAP/MIME libraries are thin compared with PHP/Node/JVM ones; HTML email needs a
  platform webview per target anyway; the owner now prefers React.
- Risks: Flutter web is the weakest target, and web is where office staff live.

### B. TypeScript everywhere with on-device sync

React web through a gateway, Electron desktop with Node's IMAP libraries, React Native or Expo on mobile.

- Pros: excellent Node libraries (imapflow, mailparser); one language.
- Cons: mobile has no Node runtime and no raw sockets in JS, so mobile needs native IMAP modules or the
  gateway anyway; a React Native UI is a second UI codebase; on-device sync must be built three times.
- Risks: the hardest parts of an email client end up duplicated per platform.

### C. Kotlin Multiplatform plus Compose Multiplatform

- Pros: strong JVM mail ecosystem; native performance.
- Cons: Compose for web and iOS is the least mature; nobody on the team knows Kotlin.

### D. Rust core plus thin UIs

- Pros: the highest robustness ceiling (async-imap, mail-parser).
- Cons: FFI to every UI, the steepest learning curve, and no team familiarity.

### E. Server-centric: a Laravel mail engine plus one React SPA on all six targets (chosen)

The backend owns IMAP/SMTP: it syncs mailboxes into PostgreSQL, sends through a durable outbox,
runs filters and the junk classifier, and pushes notifications. Every client is the same React SPA
talking HTTPS and WebSocket to the backend, shipped as a website, an Electron app and a Capacitor app.

- Pros: one sync engine, one MIME parser, one sanitizer and one UI for every platform; web and push
  come for free because the server already watches mailboxes; filters and spam rules run even when no
  client is open (Thunderbird can only filter while it runs); the owner's own stack.
- Cons: the backend holds staff mail credentials and a copy of mail, so it is the crown jewel
  (threat model T9); offline use is limited to what the client has cached; every action goes through
  the server, so latency is hidden with optimistic UI.
- Risks: per-IP connection limits and brute-force protection (cPHulk/fail2ban) on the mail host see
  all users arriving from one server IP. Mitigated in [ADR-0004](0004-server-side-mail-engine.md) and
  [ADR-0005](0005-authentication-and-credential-custody.md), and listed for IT in the open questions.

### Scoring (1 = poor, 5 = excellent)

| Driver | Weight | A Flutter | B TS on-device | C KMP | D Rust | E Laravel + React |
|---|---|---|---|---|---|---|
| D1 shared codebase and UI | 5 | 5 | 3 | 3 | 2 | 5 |
| D2 mature mail libraries | 5 | 2 | 4 | 4 | 4 | 4 |
| D3 safe HTML rendering | 4 | 3 | 4 | 3 | 3 | 5 |
| D4 native integrations | 4 | 5 | 4 | 4 | 3 | 3 |
| D5 100k folders, offline | 4 | 4 | 4 | 4 | 5 | 3 |
| D6 team familiarity | 5 | 2 | 4 | 1 | 1 | 5 |
| D7 agent-friendliness | 3 | 4 | 5 | 3 | 3 | 4 |
| D8 backend fit | 3 | 4 | 4 | 3 | 3 | 5 |
| **Weighted total (of 165)** | | **117** | **130** | **102** | **97** | **141** |

## Decision

We choose **E: a server-side mail engine on Laravel plus one React SPA packaged for every platform**,
because it is the only option that implements the hard parts of an email client (sync, MIME,
sanitizing, sending, filtering) exactly once while matching the owner's skills (D1, D3, D6, D8). Its
weak spots (D4, D5) are covered by mature shells (Capacitor and Electron plugins) and by the server
database, which pages 100k-message folders without holding them on the device.

Versions are the current stable releases on the decision date. Dependabot keeps them moving within
these major versions; a major upgrade is an ordinary PR, not a new ADR.

| Layer | Choice |
|---|---|
| Backend runtime | PHP 8.4 in production images; PHP 8.3 is the supported floor for development |
| Backend framework | Laravel 13 with Sanctum 4 (sessions and tokens), Reverb 1 (WebSockets), Horizon 5 (queues) |
| Mail protocols | `directorytree/imapengine` 1.x (IMAP, used through our own session wrapper), Symfony Mailer 7.4 LTS (SMTP submission) |
| MIME | `zbateson/mail-mime-parser` 4.x (parsing), Symfony Mime 7.4 (composition) |
| HTML safety | `symfony/html-sanitizer` 7.4 (allowlist, HTML5 parser) on the server; a sandboxed `<iframe>` with CSP on every client |
| Data | PostgreSQL 18 in production (16+ supported): mail metadata, bodies, search (`tsvector` + Arabic normalization). Redis 7+ for queues, cache, locks and broadcasting. Attachments and uploads on the Laravel filesystem (local disk or S3-compatible) |
| Push | Web Push (VAPID, `minishlink/web-push`) for browsers; FCM HTTP v1 (Android) and APNs (iOS) through small first-party HTTP clients; desktop uses the live WebSocket plus a tray icon |
| Web UI | React 19, TypeScript 6.0, Vite 8, React Router 8, TanStack Query 5 (server state), TanStack Virtual 3 (lists), Zustand 5 (UI state), Tailwind CSS 4, shadcn/ui on Radix primitives, lucide-react icons, TipTap 3 (composer), i18next 26 + react-i18next with ICU messages, Laravel Echo 2 |
| Desktop | Electron 45 + electron-builder 26 + electron-updater 6, loading the bundled SPA from a custom protocol |
| Mobile | Capacitor 8 with the official plugins (push notifications, preferences, filesystem, share, app, keyboard, status bar) and a Keychain/Keystore secure-storage plugin |
| Minimum OS | Evergreen browsers (Safari 16+); Windows 10+; macOS 13+; Ubuntu 22.04-class Linux; Android 9+ (API 28); iOS 16+ |
| Tests | PHPUnit 12 (feature tests on PostgreSQL, fixture conformance, GreenMail integration), Vitest 5 + Testing Library + MSW 3 (web), Playwright 1.x (end-to-end against GreenMail) |
| Tooling | pnpm 10 workspaces and Composer 2; Laravel Pint and Larastan 3 (PHP); ESLint 10 + typescript-eslint 8 and Prettier 3 (TypeScript). TypeScript stays on 6.0 because typescript-eslint does not support the native TypeScript 7 compiler yet |
| Layout | `apps/api` (Laravel), `apps/web` (React SPA), `apps/desktop` (Electron shell), `apps/mobile` (Capacitor shell) |
| Hosting | Docker images for the API, queue workers, scheduler, IMAP watcher and Reverb, behind TLS on a Linux VM; region and provider are open question 14 |

### Answers to the questions this ADR had to settle

1. **Client UI**: one React + TypeScript SPA for all six targets; minimum OS versions above.
2. **Sync engine placement**: on the server only (ADR-0004). Clients never speak IMAP or SMTP.
3. **Storage and search**: PostgreSQL on the server, encrypted at the disk level, with credentials
   additionally encrypted by an app key (ADR-0005). Clients cache only what they display: in memory on
   the web, and persisted on desktop and mobile so recent mail stays readable offline. Sign-out wipes it.
4. **HTML rendering**: the server parses and sanitizes once with an allowlist and blocks remote
   content; each client renders the result in a sandboxed iframe with no scripts, no same-origin
   access and a strict CSP. Links open externally.
5. **Backend scope**: everything server-side lives in one Laravel app: REST API, sync workers, IMAP
   IDLE watcher, outbox, filters, junk classifier, push relay, provisioning and WebSockets.
6. **Monorepo and tooling**: the layout and tools above; `scripts/*` stay the only interface.

## Consequences

- Positive: one implementation of every email behavior, tested once against the fixture corpus and the
  dev mail server; web and push work from day one; filters and junk rules run around the clock.
- Negative / trade-offs accepted: the server stores credentials and mail, so its security and backups
  matter as much as the mail server's; offline mode is "read what was cached, write drafts" rather than
  full offline sync; the first deployment needs a server, a domain and TLS.
- Follow-ups: run `/bootstrap-stack`; record the real `@isupply.com.eg` server profile with
  `/discover-mail-server`; ask IT to allow the backend's IP in the mail host's brute-force protection;
  a new ADR if discovery shows Microsoft 365 or Google Workspace (OAuth2 and possibly Graph).
- Revisit if: staff need full offline sync on laptops, the mail host forbids server-side access, or
  the company grows beyond what one backend region can serve.
