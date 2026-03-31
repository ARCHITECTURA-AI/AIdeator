---
sync:
  source: "Notion — 08 Decisions NON_OBVIOUS Register"
  source_url: "https://www.notion.so/33031f13482781fe81b8e805647c0e4d"
  approved_version: v0.1
  planning_readiness: Go
  synced_at: "2026-03-30"
---

# NON_OBVIOUS (Mirror)

- NO-001: Keep `db/`, `docs/`, `logs/` separate.
- NO-002: SQLite canonical; `docs/` derived.
- NO-003: Never log idea content or secrets.
- NO-004: Default bind `127.0.0.1`, not `0.0.0.0`.
- NO-005: Export guarantee as portable JSON/NDJSON.
- NO-006: `local-only` must be first-class, not degraded.
- NO-007: `rebuild-docs` is additive and DB read-only.
- NO-008: No hidden network calls.
- NO-009: Config over code for provider/model/tier/source lists.
- NO-010: Mode immutable per run.
- NO-011: Cursor/Claude notes mandatory in generated artifacts.
- NO-012: Evidence cards require citations.
