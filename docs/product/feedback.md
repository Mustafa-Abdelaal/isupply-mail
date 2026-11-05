# Owner feedback log

Every opinion, request or complaint from the owner, in their words, dated, with what was done.
Rules distilled from it live in [owner-preferences.md](owner-preferences.md).

| Date | What the owner said | What we did |
|---|---|---|
| 2026-11-05 | "I really don't have a clear vision myself or want to go to a deep stack comparisons and stuff right now. Use the best tools/stacks available to you to build a mail app cross-every-platform including mobile that works with our domain @isupply.com.eg, my prefered backend is laravel and for frontend usually use React" | Chose and recorded the stack in ADR-0002 (Laravel mail engine + one React SPA on web, Electron and Capacitor); corrected the domain to `isupply.com.eg` |
| 2026-11-05 | "For feature it's a normal email app that can send/receive email with inbox and outbound and filters and attachments and maybe spam filters. a usual mail app" | Moved message filters (R-19) and junk filtering (R-23) into the MVP; tracking issue #2 |
| 2026-11-05 | "I want you to run hands-out from now on and use your best judgement to work on it until it's done" | Recorded as P-1; work proceeds on `feat/2-mvp-mail-client` with decisions logged in the plan |
