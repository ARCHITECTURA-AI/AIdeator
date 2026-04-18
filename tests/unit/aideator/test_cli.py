"""Unit tests for aideator.cli module."""

from __future__ import annotations


class TestBuildParser:
    """Tests for CLI argument parser."""

    def test_parser_creation(self):
        """Should create parser successfully."""
        from aideator.cli import build_parser

        parser = build_parser()
        assert parser is not None
        assert parser.prog == "aideator"

    def test_default_args(self):
        """Should have correct default arguments."""
        from aideator.cli import build_parser

        parser = build_parser()
        args = parser.parse_args([])
        assert args.host == "127.0.0.1"
        assert args.port == 8000
        assert args.reload is False

    def test_custom_args(self):
        """Should accept custom arguments."""
        from aideator.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--host", "0.0.0.0", "--port", "9000", "--reload"])
        assert args.host == "0.0.0.0"
        assert args.port == 9000
        assert args.reload is True


class TestServeCommand:
    """Tests for serve command."""

    def test_serve_parser_has_db_flag(self):
        """Serve command should have --db flag."""
        from aideator.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["serve", "--db", "sqlite:///test.db"])
        assert args.db == "sqlite:///test.db"

    def test_serve_parser_has_docs_flag(self):
        """Serve command should have --docs flag."""
        from aideator.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["serve", "--docs", "/test/docs"])
        assert args.docs == "/test/docs"


class TestRebuildDocsCommand:
    """Tests for rebuild-docs command."""

    def test_rebuild_docs_parser_has_output_dir(self):
        """Rebuild-docs command should have --output-dir flag."""
        from aideator.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["rebuild-docs", "--output-dir", "/custom/docs"])
        assert args.output_dir == "/custom/docs"

    def test_rebuild_docs_parser_has_docs_flag(self):
        """Rebuild-docs command should have --docs flag."""
        from aideator.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["rebuild-docs", "--docs", "/test/docs"])
        assert args.docs == "/test/docs"


class TestConfigCommands:
    """Tests for config commands."""

    def test_config_init_parser_exists(self):
        """Should have config init subcommand."""
        from aideator.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["config", "init"])
        assert args.command == "config"
        assert args.config_command == "init"
        assert hasattr(args, "func")

    def test_config_show_parser_exists(self):
        """Should have config show subcommand."""
        from aideator.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["config", "show"])
        assert args.command == "config"
        assert args.config_command == "show"
        assert hasattr(args, "func")

    def test_config_set_llm_provider_parser_exists(self):
        """Should have config set-llm-provider subcommand."""
        from aideator.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["config", "set-llm-provider"])
        assert args.command == "config"
        assert args.config_command == "set-llm-provider"
        assert hasattr(args, "func")


class TestPathOverrides:
    """Tests for CLI path override functionality."""

    def test_cli_db_url_override(self):
        """CLI --db should override environment and defaults."""
        from aideator.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["serve", "--db", "sqlite:///override.db"])
        assert args.db == "sqlite:///override.db"

    def test_cli_docs_dir_override(self):
        """CLI --docs should override environment and defaults."""
        from aideator.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["serve", "--docs", "/override/docs"])
        assert args.docs == "/override/docs"
