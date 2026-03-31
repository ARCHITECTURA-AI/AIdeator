"""CLI entrypoints for serving API and rebuilding docs."""

from __future__ import annotations

import argparse
import sys
import webbrowser

import uvicorn

from aideator.rebuild_docs import rebuild_docs
from api.config import settings


def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Start the FastAPI server on the given host/port."""
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

    open_browser(f"http://{host}:{port}")
    run_server(host=host, port=port, reload=reload)


def command_rebuild_docs(args: argparse.Namespace) -> None:
    """Run `aideator rebuild-docs` behavior."""
    result = rebuild_docs(output_dir=args.output_dir)
    print(f"Rebuilt docs: written={result['written']} output_dir={result['output_dir']}")


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

    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the FastAPI server and open the browser",
        description="Start the AIdeator FastAPI server and open the browser at http://host:port",
    )
    serve_parser.set_defaults(func=command_serve)

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
    docs_parser.set_defaults(func=command_rebuild_docs)

    return parser


def serve_entrypoint() -> None:
    """Zero-arg console entrypoint for aideator-serve."""
    args = argparse.Namespace(
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
    command_serve(args)


def rebuild_docs_entrypoint() -> None:
    """Zero-arg console entrypoint for aideator-rebuild-docs."""
    args = argparse.Namespace(output_dir=str(settings.app_docs_dir))
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
