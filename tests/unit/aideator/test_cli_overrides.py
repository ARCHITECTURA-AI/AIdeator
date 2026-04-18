"""Unit tests for CLI overrides and entrypoints."""

from __future__ import annotations

import argparse
from unittest.mock import patch


class TestCommandServe:
    """Tests for the serve CLI command."""

    def test_serve_has_run_server_function(self) -> None:
        from aideator.cli import run_server
        assert callable(run_server)

    def test_serve_defaults(self) -> None:
        import inspect

        from aideator.cli import run_server
        sig = inspect.signature(run_server)
        params = sig.parameters
        assert params["host"].default == "127.0.0.1"
        assert params["port"].default == 8000
        assert params["reload"].default is False

    def test_command_serve_extracts_args(self) -> None:
        from aideator.cli import command_serve
        args = argparse.Namespace(
            host="0.0.0.0",
            port=9000,
            reload=True,
            db=None,
            docs=None,
        )
        with patch("aideator.cli.run_server") as mock_run, \
             patch("aideator.cli.open_browser"):
            command_serve(args)
            mock_run.assert_called_once_with(
                host="0.0.0.0", port=9000, reload=True, db_url=None, docs_dir=None
            )

    def test_command_serve_with_db_override(self) -> None:
        from aideator.cli import command_serve
        args = argparse.Namespace(
            host="127.0.0.1",
            port=8000,
            reload=False,
            db="sqlite:///:memory:",
            docs=None,
        )
        with patch("aideator.cli.run_server") as mock_run, \
             patch("aideator.cli.open_browser"):
            command_serve(args)
            mock_run.assert_called_once_with(
                host="127.0.0.1", port=8000, reload=False,
                db_url="sqlite:///:memory:", docs_dir=None
            )


class TestCommandRebuildDocs:
    """Tests for the rebuild-docs CLI command."""

    def test_has_command_rebuild_docs(self) -> None:
        from aideator.cli import command_rebuild_docs
        assert callable(command_rebuild_docs)


class TestCommandConfigInit:
    """Tests for the config init CLI command."""

    def test_has_command_config_init(self) -> None:
        from aideator.cli import command_config_init
        assert callable(command_config_init)


class TestCommandConfigShow:
    """Tests for the config show CLI command."""

    def test_has_command_config_show(self) -> None:
        from aideator.cli import command_config_show
        assert callable(command_config_show)


class TestParserConstruction:
    """Tests for CLI argument parser."""

    def test_main_parser_exists(self) -> None:
        from aideator.cli import main
        assert callable(main)

    def test_serve_entrypoint_exists(self) -> None:
        from aideator.cli import serve_entrypoint
        assert callable(serve_entrypoint)

    def test_rebuild_docs_entrypoint_exists(self) -> None:
        from aideator.cli import rebuild_docs_entrypoint
        assert callable(rebuild_docs_entrypoint)
