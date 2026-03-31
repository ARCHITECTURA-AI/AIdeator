"""PH-C red-baseline unit tests (TC-U-200+)."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any


def _require_callable(module_path: str, *names: str) -> Callable[..., Any]:
    module = importlib.import_module(module_path)
    for name in names:
        value = getattr(module, name, None)
        if callable(value):
            return value
    joined = ", ".join(names)
    raise AssertionError(f"Expected callable [{joined}] in {module_path}")


def test_tc_u_200_multi_user_scope_enforcement_helper() -> None:
    """TC-U-200 -> PH-C FRs, SAFE-001."""
    _require_callable("infra.authz", "enforce_user_scope", "assert_row_scope")


def test_tc_u_201_backup_manifest_validation_helper() -> None:
    """TC-U-201 -> SAFE-004."""
    _require_callable("infra.backup", "validate_backup_manifest", "build_backup_manifest")


def test_tc_u_202_migration_invariant_guard_helper() -> None:
    """TC-U-202 -> INV-003, INV-005, INV-006."""
    _require_callable("migrations.guard", "verify_invariants_after_migration", "assert_invariants")
