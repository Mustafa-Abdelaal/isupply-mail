# HANDOVER — iSupply Mail MVP (paused 2026-11-05)

Where work stopped, what was asked, what was decided and built, and exactly what comes next.
Branch: **`feat/2-mvp-mail-client`** · Tracking issue: **#2** (MVP epic) · Plan/log:
[docs/plans/0002-mvp-mail-client.md](docs/plans/0002-mvp-mail-client.md).

> **State in one line:** decisions are recorded and the monorepo is scaffolded (Laravel API with full
> database schema, web/desktop/mobile package manifests). No application logic, UI or script wiring
> exists yet. This commit is a **WIP checkpoint**, so `scripts/check` is expected to be red until step 3 below.

---

## 1. Inputs received (owner, 2026-11-05)

1. **Session brief** (continuation prompt): the setup phase is complete (HEAD `e90ef93`, CI green). Next
   was the stack discussion: read ADR-0002, open questions, requirements and architecture; ask where
   mail is hosted (run `python3 scripts/email/discover.py` locally, because DNS is blocked in cloud
   sessions), team skills (Laravel and Flutter on the owner's GitHub profile), device mix and
   distribution, and whether a backend is acceptable. Then recommend a stack with a scored
   comparison, fill ADR-0002, and run `/bootstrap-stack` on a branch with a PR (pushing to `main` is blocked).
   Fixed constraints: browsers can't speak IMAP/SMTP (web needs a gateway); mobile push needs a server.
   Pending: Dependabot PR #1 (actions/checkout 6 → 7), the optional Claude GitHub workflows, branch
   protection. Cloud gotchas: no GraphQL for `gh` (use REST), start `dockerd` manually, install
   shellcheck/actionlint for lint parity.
2. **Owner direction** (it overrides the step-by-step discussion):
   - "I really don't have a clear vision… don't want deep stack comparisons right now. Use the best
     tools/stacks available to build a mail app **cross-every-platform including mobile** that works
     with our domain **@isupply.com.eg**."
   - "My preferred backend is **Laravel** and for frontend usually **React**."
   - "Use best apps like **Thunderbird** or others for inspiration; implement **Laravel's best practices**
     and general best practices; use the best tools available."
   - Features: "a normal email app: send/receive, inbox and outbound (sent), **filters**,
     **attachments**, maybe **spam filters**."
   - Shared the **Postboy "AI Workflow Blueprint"** (kernel/gates/loop layers, autonomous mode with an
     escalate list, commit report format, reviewer and product-owner subagents, product memory in
     `docs/product/`, one full test run per feature, short sessions, Docker-first).
   - "**Run hands-off** from now on, use your best judgement until it's done; ask only really
     general/big questions."
3. **This request**: write this handover at the repo root, then commit and push everything.

## 2. Findings about the environment

| Finding | Consequence |
|---|---|
| DNS-over-HTTPS lookup for `isupply.com.eg` was **denied** by the session's permission classifier | Mail host is still unknown. **Owner action:** run `python3 scripts/email/discover.py isupply.com.eg` on your machine and paste the output, then record it with `/discover-mail-server` |
| GitHub zipballs (`api.github.com`, `codeload.github.com`) return 403 via the proxy | Composer falls back to `git clone` installs: slow (~10 min for the skeleton) and prints harmless "ambiguous class resolution" warnings |
| `ui.shadcn.com` blocked (403) | shadcn/ui components must be written by hand (Radix + Tailwind + cva) |
| Electron binary not downloaded by `pnpm install` (no `dist/` in the electron package) | Check again when building the desktop shell; GitHub release assets may be blocked |
| Toolchain present: PHP 8.3.6 (all needed extensions incl. pdo_pgsql, redis, intl, sodium, pcntl), Composer 2.8, Node 22, pnpm 10.28, Docker 29, Java 21, PostgreSQL 16 server, Redis 7 | PHP 8.4 not installable → **PHP 8.3 is the dev floor**, production images use 8.4 |
| Current versions (Nov 2026): Laravel 13.40, Sanctum 4.3, Reverb 1.12, Horizon 5.50, ImapEngine 1.25.9, zbateson 4.0.8, React 19.3, Vite 8.3, TS 7.0 (Go-native), React Router 8.5, Capacitor 8.6, Electron 45 | typescript-eslint supports TS `<6.1` → **TypeScript pinned to 6.0.3**. `eslint-plugin-jsx-a11y` stops at ESLint 9 → using the maintained fork **`eslint-plugin-jsx-a11y-x`** with ESLint 10 |
| Capacitor 8 floors: Android API 24, iOS 15 | We target **Android 9 (API 28) and iOS 16** (requirement N-09; Vite 8 build targets) |

## 3. Decisions made (all recorded in docs)

- **[ADR-0002](docs/decisions/0002-technology-stack.md) (Accepted under owner delegation)**: option E,
  a **server-side mail engine on Laravel 13** (PostgreSQL + Redis, Sanctum, Reverb, Horizon;
  ImapEngine for IMAP, Symfony Mailer/Mime 7.4 LTS, zbateson parser, symfony/html-sanitizer) plus
  **one React 19 + TS 6 SPA** shipped as **web, Electron 45 desktop and Capacitor 8 mobile**. Scored
  141/165 vs TS on-device 130, Flutter 117, KMP 102, Rust 97. Layout: `apps/{api,web,desktop,mobile}`.
- **[ADR-0004](docs/decisions/0004-server-side-mail-engine.md)**: PostgreSQL mirror keyed by (folder,
  UIDVALIDITY, UID); STATUS-driven incremental sync, windowed first sync + backfill, CONDSTORE fast
  path, UID-diff fallback; lazy bodies via `BODY.PEEK[]`; durable **operation log** (`mail_operations`)
  applied in order per account; **outbox with undo-send** (10 s) and "unknown" outcome after a DATA
  timeout (never auto-resent); filters + junk run server-side on arrival; Reverb realtime;
  content-free push (FCM/APNs/Web Push); ≤ 2 IMAP connections per account; scheduler + `mail:watch` IDLE daemon.
- **[ADR-0005](docs/decisions/0005-authentication-and-credential-custody.md)**: the mail server is
  the identity provider (IMAP login = sign-in, domain allowlist `MAIL_DOMAINS`); passwords stored only
  as libsodium secretbox ciphertext under `MAIL_CREDENTIALS_KEY` (`k1:base64:` key-id prefix for
  rotation); web uses Sanctum cookie sessions, desktop/mobile use per-device tokens in OS secure
  storage; throttled sign-in; "needs password" state on rejection; OAuth2 left for a later ADR.
- Domain corrected **`isupply.com` → `isupply.com.eg`** across docs, skills and tooling (anonymizer keeps both).
- Requirements: **R-19 filters** and new **R-23 junk filtering** moved into the MVP; R-24 vacation responder = later.
- Open questions updated: Q14/Q16 answered, Q15 extended (Firebase + APNs keys), new IT questions
  **Q17–19** (allowlist the backend IP in cPHulk/fail2ban, connection limits, does SMTP auto-save to Sent).
- Product memory added: [owner-preferences.md](docs/product/owner-preferences.md) (P-1…P-6) and
  [feedback.md](docs/product/feedback.md).
- Smaller calls (logged in the plan): one MVP PR rather than stacked PRs; shadcn on Radix (not Base UI);
  pnpm **catalog** shares Capacitor/TypeScript versions between `apps/web` and `apps/mobile`.

## 4. What exists now (this commit)

| Area | Done |
|---|---|
| GitHub | Issue **#2** "MVP: iSupply Mail on Laravel + React…" (labels epic, type:feature, all platforms); branch `feat/2-mvp-mail-client` |
| Docs | ADR-0002 filled + Accepted; ADR-0004, ADR-0005 new; ADR index; requirements; open questions; owner preferences; feedback log; plan 0002; domain fix |
| `apps/api` | Laravel 13 skeleton (Blade/Vite/skeleton CI removed); Sanctum (`install:api`), Reverb, Horizon installed; packages: imapengine, zbateson, symfony html-sanitizer/mailer/mime 7.4, minishlink/web-push, larastan (dev); `.env.example` with all engine/realtime/push settings; `phpunit.xml` on PostgreSQL `isupply_mail_test` with an `integration` group excluded by default; backend agent guide `apps/api/CLAUDE.md` (replaced Laravel Boost's bootstrap text) |
| Database schema (migrations run OK) | `users` (ULID, no password), `sessions`, `personal_access_tokens` (ulidMorphs), `mail_accounts`, `mail_folders`, `messages` (+ generated `search_vector` tsvector, GIN), `message_bodies`, `mail_operations`, `outgoing_messages` (drafts + outbox), `uploads`, `mail_filters`, `sender_rules`, `junk_tokens`, `contacts`, `push_subscriptions` |
| JS workspace | Root `package.json` (ESLint 10, Prettier 3 + tailwind plugin, TS 6.0), `pnpm-workspace.yaml` with catalog, `.prettierrc.json`, `.prettierignore`, `.nvmrc`, lockfile; `apps/web` (package.json with all deps, tsconfigs, `vite.config.ts` with `/api` proxy and Vitest config); `apps/desktop` and `apps/mobile` package.json only |
| Not yet written | Models, any `app/Mail/*` code, controllers/routes, web `src/`, ESLint config file, Electron/Capacitor code, script wiring, CI |

**Gate note:** ADR-0002 is Accepted, so `scripts/fmt|lint|test` now expect wired app checks and fail
until step 3. This WIP commit was made with `ISUPPLY_SKIP_PRECOMMIT_GATE=1` (the hook's documented
opt-out for the gate step only; the secret scan and other checks still ran) because you asked for
a checkpoint. CI on this branch will be red until wiring lands.

## 5. Remaining plan (in order; task numbers match the plan file)

2. **Finish scaffold**: models (Laravel 13 attribute style `#[Fillable]`, `HasUlids`), `config/mailbox.php`,
   `routes/channels.php` (`users.{id}`), `pint.json`, `phpstan.neon` (Larastan level 6), root
   `eslint.config.js` (react-hooks, react-refresh, jsx-a11y-x, tanstack-query), minimal `apps/web/src`
   that builds, Electron `src/main.ts`/`preload.ts`, `capacitor.config.ts` (+ `cap add android/ios`, minSdk 28 / iOS 16).
3. **Wire `scripts/*`** (replace every `STACK:` marker): setup (composer install, pnpm install, `.env`
   from example + `key:generate` + `mail:key` + Reverb keys), fmt (Pint + Prettier, `--check`), lint
   (Larastan, ESLint, `tsc -b`), test (PHPUnit incl. **PHP fixture conformance test mirroring
   `scripts/tests/_support.py::conformance_errors`**, Vitest; `--integration` → PHPUnit group), dev
   (web/server/desktop/android/ios), doctor; `format-file.sh` mapping; protected paths for
   `composer.lock`-like generated files (+ hook tests); settings allowlist; Dependabot (composer, npm);
   CI jobs (backend with Postgres/Redis services, web, integration with GreenMail, e2e, desktop
   matrix, Android, iOS). Workflow/hook edits need human confirmation by repo rule.
4. **Auth**: `CredentialCipher` (sodium, key ids), `Provisioning` (domain check, server settings,
   username format, refuse `encryption=none` except loopback + local/testing), `MailAuthenticator`
   interface (real = IMAP login; fake in tests), `POST /api/auth/login` (cookie for web, token for
   native with device name), logout, `GET /api/me`, re-enter password, devices list/revoke, throttling,
   plain-language errors, `GET /api/provisioning` (public config, VAPID key, Reverb settings).
5. **Sync engine** (`app/Mail/Imap`, `app/Mail/Sync`): `ImapClient` over ImapEngine's `ImapConnection`
   (subclass to add `UID EXPUNGE`), folder discovery (LIST + SPECIAL-USE, English/Arabic name
   fallbacks, modified UTF-7, delimiter, parent ids), `FolderSynchronizer` per ADR-0004, previews via
   partial fetch, threading (Message-ID/References lookups + subject fallback), contacts upsert,
   events → Reverb, jobs `SyncAccount`/`SyncFolder` with `WithoutOverlapping` per account, scheduler,
   `mail:watch` (stream_select IDLE multiplexer, re-IDLE < 29 min, backoff).
6. **Read path** (`app/Mail/Mime`): `MessageParser` (zbateson) producing the same summary as
   `emaillib.summarize`; `HtmlRiskAnalyzer` (port of `_HtmlRisk`); `HtmlSanitizer` (symfony allowlist,
   remote images blocked unless allowed, `cid:` → temporary signed URLs at response time, links
   `target=_blank rel=noopener`); filename neutralization (fixture 019); raw-source cache on the private
   disk; endpoints: message with body, thread, attachment download, signed inline image, allow remote content.
7. **Actions + sending**: `OperationRecorder` (optimistic DB update + log row) and
   `ApplyMailOperations` job (STORE/MOVE/COPY+EXPUNGE fallback/APPEND, rollback + broadcast on permanent
   failure); bulk flag/move/delete/junk endpoints; drafts autosave (APPEND to Drafts with `\Draft`,
   delete previous UID); uploads; send with undo (`send_at`, cancel endpoint), Symfony Mime build (Bcc
   envelope only, RFC 2231 filenames, text alternative), SMTP with TLS policy, APPEND to Sent unless
   `MAIL_SMTP_SAVES_SENT`, `\Answered`/`$Forwarded`; search endpoint (tsquery prefix, Arabic
   normalization, filters from/attachments/unread/flagged/date/folder); contact suggestions.
8. **Filters + junk + push**: filter CRUD/reorder/run-now and engine (conditions from/to/cc/subject/
   body/size/has-attachment; actions move/mark read/flag/junk/delete/stop); junk = server headers +
   sender block/allow + Robinson-Fisher Bayes on hashed tokens trained by Junk/Not junk (with untraining);
   push senders (Web Push via minishlink, FCM HTTP v1 and APNs via small JWT clients, null driver).
9. **Web client core**: providers (TanStack Query, i18n en/ar with RTL, theme), API client (Sanctum
   CSRF cookie on web, bearer on native), sign-in, responsive three-pane shell (stack on phones),
   folder tree with unread counts, virtualized list with multi-select and swipe-free actions, reader in
   a sandboxed iframe (no scripts, no same-origin, CSP) with remote-content banner, attachments,
   conversation view, optimistic actions with undo toasts, Echo realtime, keyboard shortcuts
   (j/k, c, r, a, f, e, #, s, /, ?), dark mode.
10. **Composer, search, settings**: TipTap composer (recipients autocomplete, attachments drag-drop,
    reply/forward quoting, signature, autosave, undo send), search with chips, settings pages
    (preferences, signature, filters editor, junk lists, devices).
11. **Native shells**: platform adapter (secure storage, notifications, push registration, save/share
    files, open external, mailto); Electron hardened (contextIsolation, sandbox, `app://` protocol,
    navigation blocked, `safeStorage`, tray, electron-builder for Win/macOS/Linux, updater); Capacitor
    (Android/iOS projects, push notifications plugin, secure storage plugin).
12. **Verify and ship**: Playwright E2E against GreenMail, `/verify-ui` screenshots (LTR/RTL,
    light/dark, phone/desktop), reviewer subagents in parallel (security, code, protocol, UX/a11y,
    platform), fix findings, docs sync (README, AGENTS.md status/repo map, architecture physical layout,
    testing strategy, DEPLOYMENT.md with production Docker Compose), open the PR for issue #2 with evidence.

## 6. Resume checklist (fresh cloud session)

```bash
git fetch origin feat/2-mvp-mail-client && git switch feat/2-mvp-mail-client
scripts/setup                                   # git hooks; app wiring arrives in step 3
cd apps/api && composer install && cp -n .env.example .env && php artisan key:generate
# fill REVERB_APP_KEY/SECRET and MAIL_CREDENTIALS_KEY (k1:base64:<32 random bytes>) — never print .env
pg_ctlcluster 16 main start                     # role isupply / isupply-dev-pw; DBs isupply_mail, isupply_mail_test
redis-server --daemonize yes
php artisan migrate
cd ../.. && pnpm install
dockerd > /tmp/dockerd.log 2>&1 &  && scripts/dev-mail up   # GreenMail for integration tests
```

Create the Postgres role/DBs if missing:
`su postgres -c "psql -c \"CREATE ROLE isupply LOGIN PASSWORD 'isupply-dev-pw' CREATEDB\""` then
`su postgres -c "createdb -O isupply isupply_mail; createdb -O isupply isupply_mail_test"`.

Resume prompt: *"Continue iSupply Mail from HANDOVER.md and docs/plans/0002-mvp-mail-client.md on
branch feat/2-mvp-mail-client: finish step 2 (models, config, minimal web/desktop/mobile code), then
step 3 (wire scripts and CI), then the backend steps 4–8. Work hands-off per owner preference P-1."*

## 7. Waiting on the owner (none of it blocks development)

- Run `python3 scripts/email/discover.py isupply.com.eg` locally and paste the output (mail host,
  auth model; Microsoft 365 or Google would mean an OAuth2 ADR).
- Answer IT questions Q17–Q19 in [open-questions.md](docs/product/open-questions.md); where to host
  the backend (Q14); Firebase project + APNs key for push (Q15).
- Decide on Dependabot PR #1 (actions/checkout 6 → 7, green CI).
- Optional: enable the Claude GitHub workflows and branch protection (steps in docs/agentic/README.md).
