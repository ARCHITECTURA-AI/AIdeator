"""CLI entrypoints for serving API and rebuilding docs."""

from __future__ import annotations

import argparse
from cmd.rebuild_docs import rebuild_docs

import uvicorn

from api.config import settings


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aideator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="Run FastAPI server")
    serve_parser.add_argument("--host", default=settings.app_host)
    serve_parser.add_argument("--port", type=int, default=settings.app_port)
    serve_parser.add_argument("--reload", action="store_true", help="Enable reload explicitly")

    docs_parser = subparsers.add_parser("rebuild-docs", help="Rebuild markdown report artifacts")
    docs_parser.add_argument("--output-dir", default=str(settings.app_docs_dir))
    return parser


def run_serve(*, host: str, port: int, reload: bool) -> None:
    uvicorn.run("api.app:app", host=host, port=port, reload=reload)


def run_rebuild_docs(*, output_dir: str) -> None:
    result = rebuild_docs(output_dir=output_dir)
    print(f"Rebuilt docs: written={result['written']} output_dir={result['output_dir']}")


def serve_entrypoint() -> None:
    run_serve(host=settings.app_host, port=settings.app_port, reload=settings.reload_enabled)


def rebuild_docs_entrypoint() -> None:
    run_rebuild_docs(output_dir=str(settings.app_docs_dir))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "serve":
        run_serve(host=args.host, port=args.port, reload=args.reload or settings.reload_enabled)
        return
    if args.command == "rebuild-docs":
        run_rebuild_docs(output_dir=args.output_dir)
        return
    parser.error(f"Unknown command: {args.command}")
