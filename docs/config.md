# Configuration Reference

AIdeator supports three configuration sources in priority order:

1. **CLI arguments** (highest priority)
2. **Environment variables**
3. **Config file** (`aideator.toml`)
4. **Default values** (lowest priority)

## Quick Setup

```bash
# Interactive wizard (recommended)
aideator config init

# View current configuration
aideator config show
```

## Config File (`aideator.toml`)

Location: `~/.config/aideator/config.toml` (Linux/macOS) or `%APPDATA%\aideator\config.toml` (Windows)

```toml
[core]
default_mode = "local"          # local | hybrid | cloud

[storage]
db_url = "sqlite:///~/.local/share/aideator/aideator.db"
docs_dir = "~/.local/share/aideator/docs"

[llm]
provider = "ollama"             # ollama | openai-compatible | anthropic-compatible | mistral-compatible
model = "mistral:7b"
api_base = "http://localhost:11434"
api_key_env = "LLM_API_KEY"    # Name of env var containing API key

[search]
provider = "duckduckgo"         # duckduckgo | searxng | tavily | exa | builtin
searxng_instance_url = "http://localhost:8888" # (if using searxng)
tavily_api_key_env = "TAVILY_API_KEY"
exa_api_key_env = "EXA_API_KEY"
```

## Environment Variables

### Core

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `local` | Environment (`local`, `dev`, `prod`) |
| `APP_HOST` | `0.0.0.0` | Server bind host |
| `APP_PORT` | `8000` | Server bind port |
| `APP_DEFAULT_MODE` | `local` | Privacy mode: `local`, `hybrid`, `cloud` |
| `DEFAULT_MODE` | — | Legacy alias for `APP_DEFAULT_MODE` |

### Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_DB_URL` | `sqlite:///~/.../aideator.db` | Database URL |
| `APP_DOCS_DIR` | `~/.../aideator/docs` | Markdown report output directory |

### LLM

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | LLM provider name |
| `LLM_MODEL` | `mistral:7b` | Model identifier |
| `LLM_API_BASE` | `http://localhost:11434` | API base URL |
| `LLM_API_KEY` | — | API key for cloud LLM providers |

### Search

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARCH_PROVIDER` | `duckduckgo` | Search provider name (`duckduckgo`, `searxng`, `tavily`, `exa`, `builtin`) |
| `SEARXNG_URL` | `http://localhost:8888` | SearXNG instance URL |
| `SEARCH_API_KEY` | — | Fallback search API key |
| `TAVILY_API_KEY` | — | Tavily-specific API key |
| `EXA_API_KEY` | — | Exa-specific API key |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `info` | Log level: `debug`, `info`, `warn`, `error` |
| `LOG_JSON` | `false` | Emit JSON-formatted logs |

## CLI Flags

### `aideator serve`

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `127.0.0.1` | Server host |
| `--port` | `8000` | Server port |
| `--reload` | `false` | Enable auto-reload for development |
| `--db` | — | Override database URL |
| `--docs` | — | Override docs output directory |

### `aideator config init`

Interactive wizard that creates `aideator.toml` with guided prompts for:
- Privacy mode selection
- LLM provider and model configuration
- Search provider setup
- API key configuration

### `aideator config show`

Displays the current effective configuration with secrets redacted.

## Privacy Modes

### `local-only` (default)

```bash
APP_DEFAULT_MODE=local
```

- No outbound HTTP calls during run execution
- LLM must be local (e.g., Ollama)
- Search signals are skipped
- Maximum privacy guarantee

### `hybrid`

```bash
APP_DEFAULT_MODE=hybrid
```

- Search queries truncated to **10 keywords** (no full idea text sent)
- Cloud LLM allowed if configured
- Balanced privacy vs. signal quality

### `cloud-enabled`

```bash
APP_DEFAULT_MODE=cloud
```

- Full idea context may be sent to external providers
- Richest search signals and LLM analysis
- Treat all run data as potentially externalized

## Provider Setup

### Ollama (local, free)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull mistral:7b

# Config
LLM_PROVIDER=ollama
LLM_MODEL=mistral:7b
LLM_API_BASE=http://localhost:11434
```

### OpenAI

```bash
LLM_PROVIDER=openai-compatible
LLM_MODEL=gpt-4o
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=sk-...
```

### DuckDuckGo Search (default, free)

```bash
SEARCH_PROVIDER=duckduckgo
```

### SearXNG (self-hosted metasearch)

```bash
SEARCH_PROVIDER=searxng
SEARXNG_URL=http://localhost:8888
```

### Tavily Search

```bash
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-...
```

### Exa Search

```bash
SEARCH_PROVIDER=exa
EXA_API_KEY=exa-...
```

## Overrides

Priority: CLI flag → Environment variable → Config file → Default

```bash
# Example: override DB for one-off test
aideator serve --db "sqlite:///:memory:"

# Example: override mode via env
APP_DEFAULT_MODE=cloud aideator serve
```

## Logging

Logs are emitted to stdout/stderr. In containers, use `docker logs`.

Example events:

```
event=app_startup env=local host=0.0.0.0 port=8000 default_mode=local-only
event=run_created run_id=<id> idea_id=<id> mode=local-only tier=low
event=search_signals_start provider=tavily mode=hybrid query_len=45
event=search_signals_done provider=tavily results_count=5
event=run_succeeded run_id=<id> duration_ms=1234
```
