# apps/api — Laravel mail engine and API

Loaded when working in `apps/api`. The repo-wide rules in `/AGENTS.md` still apply; this adds the
backend conventions. Architecture: [ADR-0004](../../docs/decisions/0004-server-side-mail-engine.md),
[ADR-0005](../../docs/decisions/0005-authentication-and-credential-custody.md).

## Commands (always through the repo scripts)

| Task | Command |
|---|---|
| Format · lint (Pint, Larastan) · tests | `scripts/fmt` · `scripts/lint` · `scripts/test` (filter: `scripts/test -k Name`) |
| Integration tests (GreenMail) | `scripts/dev-mail up && scripts/test --integration` |
| Run API + workers + Reverb + scheduler + IDLE watcher | `scripts/dev server` |

## Layout

| Path | Holds |
|---|---|
| `app/Http/Controllers/Api` | Thin controllers: authorize → Form Request → action/service → API Resource |
| `app/Http/Requests` · `app/Http/Resources` | Validation and the JSON contract (the SPA's `src/api/types.ts` mirrors the Resources) |
| `app/Mail/Imap` | IMAP session wrapper over ImapEngine's low-level connection, UTF-7 names, response parsing |
| `app/Mail/Mime` | Message parsing (`MessageParser`, conformance-tested), HTML risk analysis, sanitizer, filenames |
| `app/Mail/Sync` | Folder discovery, folder sync, threading |
| `app/Mail/Operations` | The operation log: flags, moves, deletes, drafts, sends (ADR-0004) |
| `app/Mail/Filters` · `app/Mail/Junk` | Message rules and the junk classifier |
| `app/Mail/Push` | Push senders (Web Push, FCM, APNs) behind one interface |
| `app/Jobs` · `app/Console/Commands` | Queue jobs (one account at a time) and artisan commands (`mail:watch`, `mail:key`) |

## Rules

1. **Controllers stay thin.** Validation in Form Requests, authorization in policies (or explicit
   ownership checks), JSON shape in API Resources, behavior in `app/Mail/*` services and jobs. Return
   404 (not 403) for another user's resources, so existence isn't revealed.
2. **Never block a request on IMAP for a mutation.** Update the mirror, append a `MailOperation`, and
   let `ApplyMailOperations` talk to the server. Reads may sync a stale folder on demand.
3. **Credentials**: only `MailAccount::password()` decrypts, only inside jobs or the sign-in action.
   Never pass a password into a job payload, an exception message, a log line or a Resource.
4. **IMAP identity** is (folder, UIDVALIDITY, UID). Fetch with `BODY.PEEK`. Build commands only
   through ImapEngine's token/literal API (`Str::literal`, `Str::list`), never string concatenation.
5. **HTML goes out only after `HtmlSanitizer`**, with remote content blocked unless the user allowed it.
6. **Tests**: feature tests use `RefreshDatabase` on PostgreSQL (`isupply_mail_test`). IMAP/SMTP flows
   are integration tests (`#[Group('integration')]`, names contain `integration`) against GreenMail,
   skipped unless `ISUPPLY_INTEGRATION=1`. Parsing changes run the fixture conformance test.
7. **IDs** are ULIDs (`HasUlids`) on every table we own.

## Traps

- Laravel's own `MAIL_*` env vars configure the framework mailer (unused). The mail engine reads
  `MAIL_IMAP_*`, `MAIL_SMTP_*`, `MAIL_DOMAINS`, `MAIL_CREDENTIALS_KEY` through `config/mailbox.php`.
- Composer falls back to `git clone` installs in cloud sessions (GitHub zipballs are blocked), so the
  first `composer install` is slow and prints harmless "ambiguous class resolution" warnings.
- GreenMail has no SPECIAL-USE, CONDSTORE or QRESYNC, and uses `.` as the delimiter: the fallback
  paths are what integration tests exercise.
