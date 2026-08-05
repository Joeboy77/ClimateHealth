import ast
from pathlib import Path

import pytest

DOMAIN_ROOT = Path(__file__).resolve().parents[2] / "climahealth" / "domain"

FORBIDDEN_IMPORT_ROOTS = {
    "fastapi",
    "starlette",
    "uvicorn",
    "httpx",
    "requests",
    "sqlalchemy",
    "socket",
    "urllib",
    "anthropic",
    "openai",
}

ALLOWED_IMPORT_ROOTS = {"pydantic", "climahealth"}


def domain_modules() -> list[Path]:
    return sorted(DOMAIN_ROOT.rglob("*.py"))


def imported_roots(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".")[0])
    return roots


@pytest.mark.parametrize("module_path", domain_modules(), ids=lambda path: path.name)
def test_domain_module_imports_no_infrastructure(module_path):
    assert not imported_roots(module_path) & FORBIDDEN_IMPORT_ROOTS


@pytest.mark.parametrize("module_path", domain_modules(), ids=lambda path: path.name)
def test_domain_module_imports_only_stdlib_pydantic_or_itself(module_path):
    import sys

    unexpected = {
        root
        for root in imported_roots(module_path)
        if root not in ALLOWED_IMPORT_ROOTS and root not in sys.stdlib_module_names
    }

    assert unexpected == set()
