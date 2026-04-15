# Security and Privacy

## Design Principles

AIdeator is **local-first by default**. The privacy mode system ensures that data egress is explicit, auditable, and user-controlled.

## Privacy Modes

### `local-only` (default)

**Guarantees:**
- Zero outbound HTTP calls during run execution
- Idea title, description, target user, and context never leave the machine
- Search signals are skipped entirely
- LLM must be a local provider (e.g., Ollama)

**Caveats:**
- Logs may include run IDs, timestamps, and status metadata
- If a cloud LLM provider is configured but mode is `local-only`, search is still blocked but LLM calls depend on provider configuration
- Avoid placing secrets in idea content fields

### `hybrid`

**Guarantees:**
- Search queries are truncated to **10 keywords maximum** — no full idea text is sent
- Only the search query payload leaves the machine (no description, context, or target user)
- LLM outbound follows provider configuration

**What external providers see:**
- A keyword-only search query like `"AI code review developer tool SaaS"`
- LLM prompts (if a cloud LLM is configured)

### `cloud-enabled`

**Guarantees:**
- Full idea context may be sent to external search and LLM providers
- Run payloads should be treated as potentially externalized data

**What external providers see:**
- Full search queries including title + description
- Full LLM prompts with idea context

## Data Storage

| Data | Location | Format |
|------|----------|--------|
| Ideas, runs, reports | `APP_DB_URL` (default: SQLite file) | In-memory dict or SQLite |
| Markdown reports | `APP_DOCS_DIR` (default: `~/.local/share/aideator/docs`) | `.md` files |
| Config file | `~/.config/aideator/config.toml` | TOML |
| Logs | stdout/stderr | Text or JSON |

No data is stored on remote servers. All persistence is local to the configured paths.

## API Keys

### Storage
- API keys are loaded from **environment variables** or the **config file**
- Keys in config file are stored in plain text — use file permissions to restrict access
- The `config show` command redacts secrets in output

### Rotation
- Keys can be rotated by updating the environment variable or config file
- No session caching — new keys take effect on next server restart

### Per-provider keys

| Provider | Environment Variable | Required? |
|----------|---------------------|-----------|
| Tavily | `TAVILY_API_KEY` | Only if `SEARCH_PROVIDER=tavily` |
| Exa | `EXA_API_KEY` | Only if `SEARCH_PROVIDER=exa` |
| OpenAI | `LLM_API_KEY` | Only if `LLM_PROVIDER=openai-compatible` |
| Anthropic | `LLM_API_KEY` | Only if `LLM_PROVIDER=anthropic-compatible` |
| Mistral | `LLM_API_KEY` | Only if `LLM_PROVIDER=mistral-compatible` |
| Ollama | — | No key needed (local) |
| Built-in search | — | No key needed |

## Telemetry

- **No remote telemetry** is configured by default
- Logs go to stdout/stderr only
- No analytics, tracking, or usage reporting
- Set `LOG_JSON=true` for machine-parseable log format

## Network Egress Summary

| Mode | Search Provider | LLM Provider | Outbound Calls |
|------|----------------|-------------|----------------|
| `local-only` | Any | Ollama (local) | **None** |
| `local-only` | Any | Cloud (misconfigured) | LLM only ⚠️ |
| `hybrid` | Builtin | Ollama | **None** |
| `hybrid` | Tavily/Exa | Cloud LLM | Search + LLM |
| `cloud-enabled` | Tavily/Exa | Cloud LLM | Full egress |

## Container Hardening

For production or sensitive environments:

```yaml
# docker-compose.yml example
services:
  aideator:
    image: your-org/aideator:latest
    environment:
      APP_DEFAULT_MODE: local
      LOG_JSON: "true"
    # Block all outbound except localhost
    networks:
      - internal
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
```

**Recommendations:**
- Run with `APP_DEFAULT_MODE=local` in regulated environments
- Use read-only filesystem with tmpfs for temporary files
- Store secrets in a secret manager (Docker secrets, Vault, cloud KMS)
- Keep external API keys empty for guaranteed offline operation
- Apply network egress controls at the container/host level
- Centralize logs in approved internal observability systems only
- Review mode defaults before release (`APP_DEFAULT_MODE` and env files)

## Reporting Vulnerabilities

Please report security issues by opening a private issue on the [GitHub repository](https://github.com/ARCHITECTURA-AI/AIdeator/security/advisories).
