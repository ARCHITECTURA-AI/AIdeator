<p align="center">
  <img src="logo.png" alt="AIdeator logo" width="200" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AIdeator-Idea%20Validation%20Engine-4F46E5?style=for-the-badge" alt="AIdeator" />
</p>

<h1 align="center">AIdeator</h1>

<p align="center">
  <b>AI-powered idea validation engine with pluggable LLM and search providers</b>
</p>

<p align="center">
  <i>Validate product ideas with configurable privacy modes, search-backed signals, and benchmark scoring — all from a single local-first FastAPI service.</i>
</p>

<br/>

<p align="center">
  <img src="https://img.shields.io/badge/Setup-2%20Minutes-22C55E?style=flat-square" alt="Setup time" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.116%2B-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker compose" />
  <img src="https://img.shields.io/badge/Reports-HTML%20%2B%20PDF-6366F1?style=flat-square" alt="HTML+PDF reports" />
</p>

<p align="center">
  <a href="docs/architecture.md"><b>Architecture</b></a> ·
  <a href="docs/config.md"><b>Configuration</b></a> ·
  <a href="#quick-start"><b>Quick Start</b></a> ·
  <a href="docs/security-privacy.md"><b>Security & Privacy</b></a> ·
  <a href="../../issues"><b>Issues</b></a>
</p>

<br/>

## What is AIdeator?

AIdeator is a **local-first idea validation engine** that turns raw product ideas into structured validation reports with demand, competition, and risk scoring. It combines:

- **LLM-powered analysis** via Ollama (local), OpenAI, Anthropic, or Mistral
- **Search-backed signals** via built-in web fetch, Tavily, or Exa
- **Benchmark scoring** with 0–100 scores and percentile comparisons
- **Privacy modes** that control what data leaves your machine

Think of it as your AI research analyst for product ideas — run it locally with zero external calls, or connect cloud providers for deeper insights.

## Key Features

| Feature | Description |
|---------|-------------|
| 🔒 **Privacy modes** | `local-only`, `hybrid`, `cloud-enabled` — you control data egress |
| 🤖 **LLM providers** | Ollama (local), OpenAI-compatible, Anthropic, Mistral |
| 🔍 **Search providers** | Built-in (free), Tavily (AI search), Exa (semantic search) |
| 📊 **0–100 scoring** | Demand, competition, risk with `high/medium/low` bands |
| 📈 **Benchmarks** | Compare scores against 12 reference SaaS products |
| 📄 **HTML + PDF reports** | Print-optimized shareable reports with one click |
| 🎯 **Idea templates** | Quick-start templates for common SaaS categories |
| 🖥️ **Web dashboard** | Server-rendered UI with status badges, polling, and onboarding |
| ⚙️ **Config wizard** | `aideator config init` for interactive setup |

## Quick Start

```bash
# Clone and install
git clone https://github.com/ARCHITECTURA-AI/AIdeator
cd AIdeator
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .

# Configure (interactive wizard)
aideator config init

# Start the server
aideator serve
```

Default URL: **http://localhost:8000**

## Architecture

```
aideator/          # Core package: CLI, paths, LLM & search providers
├── llm/           # LLM provider abstraction (Ollama, OpenAI, Anthropic, Mistral)
├── search/        # Search providers (DuckDuckGo, SearXNG, Tavily, Exa, Builtin)
api/               # FastAPI app, routes, config, middleware
engine/            # Run orchestrator, card synthesizer, benchmark
db/                # In-memory repositories (ideas, runs, reports)
models/            # Data classes (Idea, Run, Report)
templates/         # Jinja2 HTML templates (dashboard, reports, settings)
docs/              # Generated markdown reports & project documentation
```

Detailed overview: [`docs/architecture.md`](docs/architecture.md)

## Search Providers

AIdeator supports a fully-tiered search abstraction, bringing context to the LLM's idea validation:

| Tier | Provider | Cost | Setup Needed | Best For |
|------|----------|------|--------------|----------|
| 🟢 **Free** | `duckduckgo` | $0 | None | General testing, personal use |
| 🟡 **Mid** | `tavily` | Paid | API Key | AI-optimized context gathering |
| 🔵 **High** | `exa` | Paid | API Key | Deep semantic research |
| ⚙️ **Self-hosted** | `searxng` | $0 (your infra) | SearXNG Instance | Power users, maximum privacy |
| ⬜ **Offline** | `builtin` | $0 | None | URL extraction only (no search) |

Configure via `aideator config init` or set `SEARCH_PROVIDER` env var.

## LLM Providers

| Provider | Local? | API Key? | Notes |
|----------|--------|----------|-------|
| **Ollama** | ✅ | No | Default, runs any GGUF model |
| **OpenAI-compatible** | ❌ | Yes | GPT-4o, Groq, etc. |
| **Anthropic-compatible** | ❌ | Yes | Claude models |
| **Mistral-compatible** | ❌ | Yes | Mistral models |

## Scoring System

Every validation run produces cards with **0–100 scores** and automatic bands:

| Score Range | Band | Meaning |
|-------------|------|---------|
| 70–100 | 🟢 High | Strong signal |
| 40–69 | 🟡 Medium | Moderate signal, needs investigation |
| 0–39 | 🔴 Low | Weak signal, high risk area |

Scores are compared against an internal benchmark corpus of 12 known SaaS products to provide percentile rankings.

## Privacy Modes

| Mode | External calls | Use case |
|------|---------------|----------|
| `local-only` | None | Fully offline, maximum privacy |
| `hybrid` | Keyword-only queries (10 words max) | Balanced privacy + signals |
| `cloud-enabled` | Full idea context | Maximum insight quality |

Set via `APP_DEFAULT_MODE=local|hybrid|cloud` environment variable.

## Docker

```bash
# Build and run
docker build -t your-org/aideator:latest .
docker run --rm -p 8000:8000 --env-file .env your-org/aideator:latest

# Or with compose
docker compose up
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `aideator serve` | Start the web server |
| `aideator config init` | Interactive configuration wizard |
| `aideator config show` | Display current configuration |
| `aideator rebuild-docs` | Rebuild markdown report artifacts |

Flags: `--host`, `--port`, `--reload`, `--db`, `--docs`

## Development

```bash
pip install -e ".[dev]"
make lint      # Ruff linting
make test      # Pytest suite
make dev       # Dev server with reload
```

Seed test data:

```bash
python scripts/seed_example.py
```

## Configuration

- **Config file**: `aideator.toml` (auto-created by `config init`)
- **Environment variables**: override config file values
- **CLI flags**: override everything

Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_DEFAULT_MODE` | `local` | Privacy mode |
| `LLM_PROVIDER` | `ollama` | LLM backend |
| `LLM_MODEL` | `mistral:7b` | Model name |
| `SEARCH_PROVIDER` | `builtin` | Search backend |
| `TAVILY_API_KEY` | — | Tavily API key |
| `EXA_API_KEY` | — | Exa API key |
| `LLM_API_KEY` | — | LLM API key |

Full reference: [`docs/config.md`](docs/config.md)

## Security

Local-only mode blocks all outbound HTTP by run-mode guardrails. See [`docs/security-privacy.md`](docs/security-privacy.md) for:
- Data residency guarantees per mode
- API key handling and rotation guidance
- Container hardening recommendations

## Version History

| Version | Phase |
|---------|-------|
| `1.0.0` | V1 — Full validation engine |
| `0.4.0` | PH-D — Plugin & eval |
| `0.3.0` | PH-C — Runtime & migration |
| `0.2.0` | PH-B — Web UI |
| `0.1.0` | PH-A — Foundation |

## License

MIT. See [`LICENSE`](LICENSE).