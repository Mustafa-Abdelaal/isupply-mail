---
name: adr
description: Record an architecture decision as a numbered ADR in docs/decisions/ — context, drivers, options with honest trade-offs, decision, consequences — update the index, and supersede (never edit) accepted ADRs. Use for stack, protocol, storage, security, platform or cross-cutting choices.
argument-hint: "[decision title]"
---

# Record an architecture decision

Existing ADRs:
!`ls docs/decisions/ 2>/dev/null || true`

Write an ADR when a choice is costly to reverse, affects several components or platforms, constrains
future work, or will make someone later ask "why did we do it this way?". Library choices count when
they become foundational (protocol, storage, rendering, state). Everyday code choices don't need one.

## Steps

1. **Number and file.** Take the next 4-digit number and create
   `docs/decisions/NNNN-kebab-title.md` from [the template](../../../docs/decisions/template.md).
2. **Context.** State the forces in plain language: requirements (R-xx IDs), constraints, the team,
   deadlines, and links to specs and threat models.
3. **Decision drivers.** Give 4–8 weighted criteria, written before you look at options (otherwise
   they get rationalized after the fact).
4. **Options.** List at least two real alternatives, plus "do nothing" when that's viable. For each,
   give pros, cons, risks and a criteria score table. Use the `tech-researcher` subagent for current,
   cited facts (maintenance status, platform support, licenses) and never rely on memory for
   versions.
5. **Decision and consequences.** Name the option, explain why it wins on the drivers, then list
   consequences (positive, negative, follow-ups) and the conditions that would make us revisit it.
6. **Status.** Use `- **Status:** Proposed` and add a row to the
   [index](../../../docs/decisions/README.md). Ask the user to decide. Only a human accepts an ADR.
7. **On acceptance**, change the status line to `Accepted (YYYY-MM-DD)`. From then on the file is
   immutable, and the guard hook will ask before any edit.
8. **Superseding.** Write a new ADR stating `Supersedes ADR-NNNN`, then change only the old one's
   status line to `Superseded by ADR-MMMM`. The hook asks for confirmation on that edit, which is
   expected.

## Special cases

- **ADR-0002 (technology stack)**: once it is Accepted with concrete versions, the next step is
  `/bootstrap-stack`.
- **Security-relevant decisions** link the threat model section they change.
