"""CLI entrypoints for serving API and rebuilding docs."""

from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from pathlib import Path
from typing import Any

import uvicorn

from aideator.paths import (
    ensure_dir,
    get_all_paths,
    get_default_config_path,
    resolve_path,
)
from aideator.rebuild_docs import rebuild_docs
from api.config import load_settings, settings


def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
    db_url: str | None = None,
    docs_dir: str | None = None,
) -> None:
    """Start the FastAPI server on the given host/port."""
    # Reload settings with CLI overrides
    global settings
    if db_url or docs_dir:
        settings = load_settings(cli_db_url=db_url, cli_docs_dir=docs_dir)

    uvicorn.run(
        "api.app:app",
        host=host,
        port=port,
        reload=reload,
        factory=False,
    )


def open_browser(url: str) -> None:
    """Open a URL in the user's default browser."""
    try:
        webbrowser.open(url)
    except Exception as exc:  # noqa: BLE001
        # Browser-open failures should not prevent the server from starting.
        print(f"Warning: could not open browser: {exc}", file=sys.stderr)


def command_serve(args: argparse.Namespace) -> None:
    """Run `aideator serve` behavior."""
    host = args.host
    port = args.port
    reload = args.reload
    db_url = getattr(args, "db", None)
    docs_dir = getattr(args, "docs", None)

    open_browser(f"http://{host}:{port}")
    run_server(host=host, port=port, reload=reload, db_url=db_url, docs_dir=docs_dir)


def command_rebuild_docs(args: argparse.Namespace) -> None:
    """Run `aideator rebuild-docs` behavior."""
    output_dir = args.output_dir
    if output_dir is None:
        output_dir = str(settings.app_docs_dir)

    # Ensure directory exists
    ensure_dir(Path(output_dir))

    result = rebuild_docs(output_dir=output_dir)
    print(f"Rebuilt docs: written={result['written']} output_dir={result['output_dir']}")


def command_config_init(args: argparse.Namespace) -> None:
    """Run `aideator config init` - Interactive configuration wizard."""
    config_path = get_default_config_path()

    print("=" * 60)
    print("AIdeator Configuration Wizard")
    print("=" * 60)
    print()

    # Check if config already exists
    if config_path.exists():
        print(f"Config file already exists at: {config_path}")
        response = input("Overwrite? [y/N]: ").strip().lower()
        if response not in ("y", "yes"):
            print("Aborted.")
            return
        print()

    # Prompt for mode
    print("Select default run mode:")
    print("  1) local-only - No outbound HTTP calls (most private)")
    print("  2) hybrid - Curated external calls with keyword-only payloads")
    print("  3) cloud-enabled - Full external integrations")
    print()

    mode_choice = input("Enter choice [1-3] (default: 1): ").strip() or "1"
    mode_map = {"1": "local-only", "2": "hybrid", "3": "cloud-enabled"}
    default_mode = mode_map.get(mode_choice, "local-only")

    # Prompt for LLM provider
    print()
    print("Select LLM provider:")
    print("  1) Ollama (local)")
    print("  2) OpenAI-compatible (e.g., OpenAI, Groq, etc.)")
    print("  3) Anthropic-compatible")
    print("  4) Mistral-compatible")
    print()

    llm_choice = input("Enter choice [1-4] (default: 1): ").strip() or "1"
    llm_map = {
        "1": ("ollama", "mistral:7b", "http://localhost:11434"),
        "2": ("openai-compatible", "gpt-4", ""),
        "3": ("anthropic-compatible", "claude-3-opus", ""),
        "4": ("mistral-compatible", "mistral-large", ""),
    }
    llm_provider, llm_model, llm_base = llm_map.get(llm_choice, ("ollama", "mistral:7b", "http://localhost:11434"))

    # If not local, ask for API details
    llm_api_key_env = "LLM_API_KEY"
    if llm_provider != "ollama":
        print()
        print(f"For {llm_provider}, please provide:")
        custom_base = input(f"  API Base URL [default: {llm_base or 'https://api.openai.com/v1'}]: ").strip()
        if custom_base:
            llm_base = custom_base
        custom_model = input(f"  Model [default: {llm_model}]: ").strip()
        if custom_model:
            llm_model = custom_model
        print()
        print("  Note: Store your API key in the environment variable LLM_API_KEY")
        print(f"  Example: export LLM_API_KEY='your-key-here'")
        print()

    # Prompt for search provider
    print("Select search provider:")
    print("  1) DuckDuckGo - Free web search, no API key needed (recommended)")
    print("  2) Tavily - AI-powered web search (requires API key, better quality)")
    print("  3) Exa - AI-native semantic search (requires API key, best quality)")
    print("  4) SearXNG - Self-hosted metasearch (requires running instance)")
    print("  5) None - URL extraction only, no web search (for offline/local-only)")
    print()

    search_choice = input("Enter choice [1-5] (default: 1): ").strip() or "1"
    search_map = {"1": "duckduckgo", "2": "tavily", "3": "exa", "4": "searxng", "5": "builtin"}
    search_provider = search_map.get(search_choice, "duckduckgo")

    searxng_url = "http://localhost:8888"
    if search_provider in ("tavily", "exa"):
        print()
        print(f"For {search_provider}, please provide:")
        env_var = f"{search_provider.upper()}_API_KEY"
        print(f"  Store your API key in the environment variable {env_var}")
        print(f"  Example: export {env_var}='your-key-here'")
        print()
    elif search_provider == "searxng":
        print()
        searxng_url = input(
            "  SearXNG instance URL [default: http://localhost:8888]: "
        ).strip() or "http://localhost:8888"
        print()
    elif search_provider == "duckduckgo":
        print()
        print("  DuckDuckGo search is free and requires no setup.")
        print("  Tip: For higher quality results, upgrade to Tavily or Exa later.")
        print()

    # Storage paths (optional customization)
    print("Storage paths (press Enter to use defaults):")
    print(f"  Default data directory: {get_all_paths()['user_data_dir']}")
    custom_data_dir = input("  Custom data directory (optional): ").strip()

    # Build config file content
    config_lines = [
        '# AIdeator Configuration File',
        '# Generated by `aideator config init`',
        '',
        '[core]',
        f'default_mode = "{default_mode}"',
        '',
        '[storage]',
    ]

    if custom_data_dir:
        data_path = resolve_path(custom_data_dir)
        config_lines.append(f'db_url = "sqlite:///{data_path}/aideator.db"')
        config_lines.append(f'docs_dir = "{data_path}/docs"')
    else:
        config_lines.append(f'# db_url = "sqlite:///{get_all_paths()["db_path"] }"')
        config_lines.append(f'# docs_dir = "{get_all_paths()["docs_dir"] }"')

    config_lines.extend([
        '',
        '[llm]',
        f'provider = "{llm_provider}"',
        f'model = "{llm_model}"',
    ])

    if llm_base:
        config_lines.append(f'api_base = "{llm_base}"')
    config_lines.append(f'api_key_env = "{llm_api_key_env}"')

    config_lines.extend([
        '',
        '[search]',
        f'provider = "{search_provider}"',
    ])

    if search_provider == "tavily":
        config_lines.append('tavily_api_key_env = "TAVILY_API_KEY"')
    elif search_provider == "exa":
        config_lines.append('exa_api_key_env = "EXA_API_KEY"')
    elif search_provider == "searxng":
        config_lines.append(f'searxng_instance_url = "{searxng_url}"')

    config_content = "\n".join(config_lines)

    # Ensure config directory exists
    ensure_dir(config_path.parent)

    # Write config file
    config_path.write_text(config_content, encoding="utf-8")

    print()
    print("=" * 60)
    print(f"Configuration saved to: {config_path}")
    print("=" * 60)
    print()
    print("Config file contents:")
    print("-" * 40)
    print(config_content)
    print("-" * 40)
    print()
    print("Next steps:")
    print(f"  1. Review the config file at: {config_path}")
    print(f"  2. Set any required API keys as environment variables")
    print(f"  3. Run 'aideator serve' to start the server")
    print()


def command_config_show(args: argparse.Namespace) -> None:
    """Run `aideator config show` - Display effective configuration."""
    config_path = get_default_config_path()

    print("=" * 60)
    print("AIdeator Effective Configuration")
    print("=" * 60)
    print()

    # Show config file location
    print(f"Config file: {config_path}")
    print(f"Exists: {config_path.exists()}")
    print()

    # Show paths
    print("Storage Paths:")
    for name, path in get_all_paths().items():
        exists = "✓" if path.exists() else "✗"
        print(f"  {name}: {path} [{exists}]")
    print()

    # Show effective config (redacted)
    print("Effective Configuration (secrets redacted):")
    print("-" * 40)
    config_dict = settings.to_dict(redact_secrets=True)
    _print_config_dict(config_dict)
    print()

    # Show environment variables
    print("Relevant Environment Variables:")
    print("-" * 40)
    env_vars = [
        "APP_ENV",
        "APP_HOST",
        "APP_PORT",
        "APP_DB_URL",
        "APP_DOCS_DIR",
        "APP_DEFAULT_MODE",
        "LLM_PROVIDER",
        "LLM_MODEL",
        "LLM_API_BASE",
        "LLM_API_KEY",
        "SEARCH_PROVIDER",
        "SEARCH_API_KEY",
        "TAVILY_API_KEY",
        "EXA_API_KEY",
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
    ]
    for var in env_vars:
        value = os.environ.get(var, "")
        if value:
            # Redact API keys
            if "KEY" in var or "SECRET" in var:
                display = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            else:
                display = value
            print(f"  {var}={display}")
        else:
            print(f"  {var}=(not set)")
    print()


def _print_config_dict(config: dict[str, Any], indent: int = 0) -> None:
    """Pretty print config dictionary."""
    for key, value in config.items():
        if isinstance(value, dict):
            print("  " * indent + f"[{key}]")
            _print_config_dict(value, indent + 1)
        else:
            print("  " * indent + f"{key} = {value}")


def command_config_set_llm_provider(args: argparse.Namespace) -> None:
    """Run `aideator config set-llm-provider` - Set LLM provider interactively."""
    config_path = get_default_config_path()

    print("=" * 60)
    print("Configure LLM Provider")
    print("=" * 60)
    print()

    # Load existing config if present
    existing_config = ""
    if config_path.exists():
        existing_config = config_path.read_text(encoding="utf-8")

    # Provider selection
    print("Select LLM provider:")
    print("  1) Ollama (local)")
    print("  2) OpenAI-compatible")
    print("  3) Anthropic-compatible")
    print("  4) Mistral-compatible")
    print()

    choice = input("Enter choice [1-4]: ").strip()
    providers = {
        "1": ("ollama", "http://localhost:11434", "mistral:7b"),
        "2": ("openai-compatible", "https://api.openai.com/v1", "gpt-4"),
        "3": ("anthropic-compatible", "https://api.anthropic.com", "claude-3-opus"),
        "4": ("mistral-compatible", "https://api.mistral.ai", "mistral-large"),
    }

    provider, default_base, default_model = providers.get(choice, providers["1"])

    # Get API base
    api_base = input(f"API Base URL [default: {default_base}]: ").strip()
    if not api_base:
        api_base = default_base

    # Get model
    model = input(f"Model [default: {default_model}]: ").strip()
    if not model:
        model = default_model

    # Get API key env var name
    api_key_env = input("API Key Environment Variable [default: LLM_API_KEY]: ").strip()
    if not api_key_env:
        api_key_env = "LLM_API_KEY"

    # Update config file
    ensure_dir(config_path.parent)

    # Simple TOML section replacement
    llm_section = f"""[llm]
provider = "{provider}"
model = "{model}"
api_base = "{api_base}"
api_key_env = "{api_key_env}"
"""

    if "[llm]" in existing_config:
        # Replace existing section
        import re

        pattern = r"\[llm\].*?(?=\n\[|\Z)"
        new_config = re.sub(pattern, llm_section.strip() + "\n\n", existing_config, flags=re.DOTALL)
    else:
        # Append new section
        new_config = existing_config + "\n" + llm_section if existing_config else llm_section

    config_path.write_text(new_config, encoding="utf-8")

    print()
    print(f"LLM provider configuration updated in: {config_path}")
    print()
    print(f"Remember to set your API key:")
    print(f"  export {api_key_env}='your-api-key-here'")
    print()


def command_forge(args: argparse.Namespace) -> None:
    """Run `aideator forge <idea_id>` behavior."""
    from uuid import UUID
    from db.ideas import get_idea
    from db.reports import get_report
    from db.runs import list_runs_for_idea
    from aideator.paths import get_report_path_for_idea
    from engine.forge import forge_concept_file
    import sys

    try:
        idea_id = UUID(args.idea_id)
    except ValueError:
        print(f"Error: Invalid UUID format: {args.idea_id}", file=sys.stderr)
        sys.exit(1)

    idea = get_idea(idea_id)
    if not idea:
        print(f"Error: Idea not found: {idea_id}", file=sys.stderr)
        sys.exit(1)

    # Latest successful run
    runs = list_runs_for_idea(idea_id)
    success_runs = [r for r in runs if r.status == "succeeded"]
    latest_run = max(success_runs, key=lambda r: r.updated_at, default=None)

    if not latest_run:
        print(f"Error: No successful runs found for idea: {idea_id}", file=sys.stderr)
        sys.exit(1)

    report = get_report(latest_run.run_id)
    if not report:
        print(f"Error: Report data not found for run: {latest_run.run_id}", file=sys.stderr)
        sys.exit(1)

    artifact_path = get_report_path_for_idea(idea_id)
    content = artifact_path.read_text(encoding="utf-8") if artifact_path.exists() else "No synthesized content available."

    demand_score = "N/A"
    demand_summary = "Ready for initial development."
    for card in report.cards:
        if card.get("type") == "demand":
            demand_score = str(card.get("score", "N/A"))
            demand_summary = card.get("summary", demand_summary)

    print(f"Forging local assets for: {idea.title}...")
    abs_path = forge_concept_file(
        idea_title=idea.title,
        demand_score=demand_score,
        demand_summary=demand_summary,
        report_content=content,
        root_dir="."
    )
    print(f"[v] Created: {abs_path}")


def command_main(args: argparse.Namespace) -> None:
    """Default behavior for `aideator` with no subcommand."""
    command_serve(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aideator",
        description=(
            "AIdeator - local-first FastAPI service for idea validation "
            "and markdown reports"
        ),
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface to bind (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (for local development)",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    # serve command
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the FastAPI server and open the browser",
        description="Start the AIdeator FastAPI server and open the browser at http://host:port",
    )
    serve_parser.add_argument(
        "--db",
        dest="db",
        help="Override database URL (e.g., sqlite:///path/to/db.sqlite3)",
    )
    serve_parser.add_argument(
        "--docs",
        dest="docs",
        help="Override docs directory path",
    )
    serve_parser.set_defaults(func=command_serve)

    # rebuild-docs command
    docs_parser = subparsers.add_parser(
        "rebuild-docs",
        help="Rebuild AIdeator documentation",
        description="Rebuild AIdeator markdown docs from succeeded runs",
    )
    docs_parser.add_argument(
        "--output-dir",
        default=str(settings.app_docs_dir),
        help=f"Output directory for rebuilt docs (default: {settings.app_docs_dir})",
    )
    docs_parser.add_argument(
        "--docs",
        dest="docs",
        help="Override docs directory path",
    )
    docs_parser.set_defaults(func=command_rebuild_docs)

    # config command
    config_parser = subparsers.add_parser(
        "config",
        help="Configuration commands",
        description="Manage AIdeator configuration",
    )
    config_subparsers = config_parser.add_subparsers(dest="config_command", metavar="<config-command>")

    # config init
    config_init_parser = config_subparsers.add_parser(
        "init",
        help="Initialize configuration file interactively",
        description="Create a new aideator.toml config file with interactive prompts",
    )
    config_init_parser.set_defaults(func=command_config_init)

    # config show
    config_show_parser = config_subparsers.add_parser(
        "show",
        help="Show effective configuration",
        description="Display current effective configuration with paths and settings",
    )
    config_show_parser.set_defaults(func=command_config_show)

    # config set-llm-provider
    config_llm_parser = config_subparsers.add_parser(
        "set-llm-provider",
        help="Configure LLM provider",
        description="Set up LLM provider (Ollama, OpenAI-compatible, etc.)",
    )
    config_llm_parser.set_defaults(func=command_config_set_llm_provider)

    # forge command
    forge_parser = subparsers.add_parser(
        "forge",
        help="Forge local concept files",
        description="Create a concept.md file in the root directory with the latest intelligence and build prompts",
    )
    forge_parser.add_argument(
        "idea_id",
        help="The UUID of the idea to forge assets for",
    )
    forge_parser.set_defaults(func=command_forge)

    return parser


def serve_entrypoint() -> None:
    """Zero-arg console entrypoint for aideator-serve."""
    args = argparse.Namespace(
        host="127.0.0.1",
        port=8000,
        reload=False,
        db=None,
        docs=None,
    )
    command_serve(args)


def rebuild_docs_entrypoint() -> None:
    """Zero-arg console entrypoint for aideator-rebuild-docs."""
    args = argparse.Namespace(
        output_dir=str(settings.app_docs_dir),
        docs=None,
    )
    command_rebuild_docs(args)


def main() -> None:
    """Primary console entrypoint for `aideator`."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        command_main(args)
        return

    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        sys.exit(1)
    func(args)


if __name__ == "__main__":
    main()
