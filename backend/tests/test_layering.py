import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "climahealth"

FORBIDDEN_IMPORTS_BY_LAYER: dict[str, tuple[str, ...]] = {
    "domain": ("climahealth.services", "climahealth.infrastructure", "climahealth.api"),
    "services": ("climahealth.infrastructure", "climahealth.api"),
    "infrastructure": ("climahealth.api",),
}


def modules_in(layer: str) -> list[Path]:
    return sorted((PACKAGE_ROOT / layer).rglob("*.py"))


def imported_modules(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    return imported


def layer_cases() -> list[tuple[str, Path]]:
    return [(layer, path) for layer in FORBIDDEN_IMPORTS_BY_LAYER for path in modules_in(layer)]


@pytest.mark.parametrize(
    ("layer", "module_path"),
    layer_cases(),
    ids=lambda item: item.name if isinstance(item, Path) else item,
)
def test_dependencies_point_inward(layer, module_path):
    forbidden_prefixes = FORBIDDEN_IMPORTS_BY_LAYER[layer]

    violations = {
        imported
        for imported in imported_modules(module_path)
        if imported.startswith(forbidden_prefixes)
    }

    assert violations == set(), f"{module_path.name} in '{layer}' imports outward: {violations}"
