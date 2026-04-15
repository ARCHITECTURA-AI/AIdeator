# AIdeator Scope Lock (V1)

## Approval Status

- Planning readiness: **GO**
- Lock scope: **V1 implementation window**
- Lock authority: this file + `Final-v1-plan.md`
- Change policy: any deviation requires explicit `CR-*` entry before implementation

## Supersedes

This scope lock supersedes the previous PH-D lock. PH-A through PH-D baselines are treated as complete.

## V1 Features (Locked In)

1. **Storage & Runtime** (§1): cross-platform path helpers, config integration, CLI overrides
2. **LLM Provider Config** (§2): provider abstraction (Ollama, OpenAI, Anthropic, Mistral), registry, UI
3. **Search Provider Abstraction** (§3): `SearchProvider` ABC, builtin (minimal web fetch), Tavily, Exa, registry
4. **Configuration UX** (§4): TOML config file, `config init` wizard, `config show`
5. **Web UI v1** (§5): dashboard with badges/scores, create idea + run flow, polling
6. **Report Sharing** (§6): HTML report route, print-optimized CSS PDF export
7. **Scoring & Benchmarking** (§7): 0–100 scores + band (new runs only), internal benchmark percentiles
8. **Onboarding** (§8): first-run detection, banner, idea templates
9. **Docs & Positioning** (§9): README rewrite, config docs, security/privacy docs
10. **Tests & Quality Gates** (§10): unit/e2e/smoke tests, release checklist

## Resolved Decisions

- PDF export: print-optimized CSS + browser print (no WeasyPrint)
- Builtin search: minimal web fetch only (no Reddit/GitHub/YouTube adapters in V1)
- Score migration: only new runs use 0–100 scale; existing runs unchanged
- Scope override: V1 supersedes PH-D lock

Carry-forward constraints still mandatory:

- `INV-001`..`INV-008`
- `SAFE-001`..`SAFE-003`
- `NFR-001`, `NFR-002`, `NFR-004`, `NFR-007`, `NFR-008`, `NFR-009`, `NFR-010`

## Out-of-Scope Features (Locked Out)

No implementation work for:

- Reddit, GitHub, YouTube source adapters (post-V1)
- Server-side PDF generation (WeasyPrint)
- Retroactive score migration for existing runs
- Post-V1 expansion not represented in `Final-v1-plan.md`

## Test-First Policy

- Start work from `docs/test-plan.md` and `docs/traceability.md`, not from ad-hoc implementation ideas.
- Every code change must point to affected plan section (§1–§10).
- A V1 item is not complete until mapped tests are green.

## Enforcement Rules

- No opportunistic expansion beyond V1 lock.
- No new ID families; keep `FR-*`, `NFR-*`, `INV-*`, `SAFE-*`, `TC-*`, `ADR-*`, `CR-*`.
- If scope is disputed or unstable, stop implementation and resolve docs first.

## Approval Record

- State: **ACTIVE V1 LOCK**
- This file is the enforceable boundary for implementation decisions.
