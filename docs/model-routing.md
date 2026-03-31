---
sync:
  source: "Notion — 09 Conventions §4"
  source_url: "https://www.notion.so/33031f1348278165ab18fca50d777e3a"
  approved_version: v0.1
  planning_readiness: Go
  synced_at: "2026-03-30"
---

# Model Routing (Mirror)

## Routing file
`config/model_routing.yaml`

## Required shape
```yaml
roles:
  analysis:
    low:
      prompt: analysis_v1.0.0
      model: ollama/mistral:7b
      temperature: 0.2
      max_tokens: 1024
    medium:
      prompt: analysis_v1.0.0
      model: openai/gpt-4o-mini
      temperature: 0.2
      max_tokens: 2048
  synthesis:
    low:
      prompt: synthesis_v1.0.0
      model: ollama/mistral:7b
      temperature: 0.3
      max_tokens: 2048
    medium:
      prompt: synthesis_v1.0.0
      model: openai/gpt-4o-mini
      temperature: 0.3
      max_tokens: 4096
```

## Rules
- Config over code (NO-009).
- Prompt versions immutable after release.
- Mode/tier/provider changes require versioned release updates.
