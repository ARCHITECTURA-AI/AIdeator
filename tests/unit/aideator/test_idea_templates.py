"""Unit tests for idea templates."""

from __future__ import annotations

import pytest

from aideator.idea_templates import TEMPLATES, get_template, list_templates


class TestIdeaTemplates:
    """Tests for built-in idea templates."""

    def test_three_templates_exist(self) -> None:
        assert len(TEMPLATES) == 3

    def test_template_ids_unique(self) -> None:
        ids = [tpl.id for tpl in TEMPLATES]
        assert len(ids) == len(set(ids))

    def test_all_fields_populated(self) -> None:
        for tpl in TEMPLATES:
            assert tpl.id, f"Template missing id"
            assert tpl.label, f"Template {tpl.id} missing label"
            assert tpl.description, f"Template {tpl.id} missing description"
            assert tpl.target_user, f"Template {tpl.id} missing target_user"
            assert tpl.context, f"Template {tpl.id} missing context"

    def test_get_template_found(self) -> None:
        tpl = get_template("saas-dev-tool")
        assert tpl is not None
        assert tpl.label == "SaaS Developer Tool"

    def test_get_template_not_found(self) -> None:
        tpl = get_template("nonexistent")
        assert tpl is None

    def test_list_templates_returns_dicts(self) -> None:
        templates = list_templates()
        assert len(templates) == 3
        for t in templates:
            assert "id" in t
            assert "label" in t
            assert "description" in t
            assert "target_user" in t
            assert "context" in t

    def test_templates_are_editable_after_selection(self) -> None:
        """Templates return plain strings; they don't enforce immutability
        on the form values (the user can edit them)."""
        templates = list_templates()
        for t in templates:
            # Values are strings, not frozen objects
            assert isinstance(t["description"], str)
            assert isinstance(t["target_user"], str)
