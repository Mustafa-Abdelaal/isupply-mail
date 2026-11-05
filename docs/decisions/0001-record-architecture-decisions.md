# ADR-0001: Record architecture decisions

- **Status:** Accepted (2026-11-05)
- **Date:** 2026-11-05
- **Deciders:** project owner
- **Related:** [ADR index](README.md)

## Context

This project is built largely by AI coding agents working in many short sessions, plus a small human
team. Agents start each session without memory. Without a written record of *why* things are the way
they are, agents (and people) will re-litigate settled questions, or quietly break assumptions.

## Decision

We record significant decisions as numbered Markdown ADRs in `docs/decisions/`, using
[template.md](template.md) and the `/adr` skill:

- Each ADR has a `- **Status:**` line, and the index ([README.md](README.md)) lists every ADR.
- Only humans accept ADRs. Once Accepted, an ADR is immutable, and changes happen through a
  superseding ADR. The repository's guard hook asks for confirmation before an accepted ADR is edited.
- `scripts/agent/validate_config.py` checks status lines and index membership in CI.

## Consequences

- Positive: durable context for agents; decisions are reviewable in PRs; history is preserved.
- Negative: a small writing overhead per decision. We accept it for decisions that are costly to reverse.
