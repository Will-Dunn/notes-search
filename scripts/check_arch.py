#!/usr/bin/env python3
"""
Validate hexagonal architecture import rules.
Exit 0 if clean, exit 1 with violation details if any layer boundary is crossed.

Rules:
  core/      → may only import from core/, ports/, stdlib
  ports/     → may only import from core/models, abc, stdlib
  adapters/  → may import from ports/, core/, stdlib, any third-party
  container  → unrestricted
  cli.py     → may import container, config, logger, httpx, typer, stdlib
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent / "notes_search"

_OLD_MODULES = {"commands", "utils", "db"}


def get_imports(filepath: Path) -> list[str]:
    tree = ast.parse(filepath.read_text(), filename=str(filepath))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def layer_of(filepath: Path) -> str:
    rel = filepath.relative_to(ROOT)
    parts = rel.parts
    if parts[0] == "core":
        return "core"
    if parts[0] == "ports":
        return "ports"
    if parts[0] == "adapters":
        return "adapters"
    if parts[0] == "container.py":
        return "container"
    if parts[0] == "cli.py":
        return "cli"
    return "other"


def check_import(importer_layer: str, module: str) -> str | None:
    """Return a violation message, or None if the import is allowed."""
    if not module.startswith("notes_search."):
        return None

    inner = module[len("notes_search."):]
    imported_layer = inner.split(".")[0]

    if imported_layer in _OLD_MODULES:
        return f"import from removed module '{imported_layer}' (old structure)"

    if importer_layer == "core":
        if imported_layer in ("adapters", "container", "cli"):
            return f"core must not import from {imported_layer}"

    if importer_layer == "ports":
        if imported_layer in ("adapters", "container", "cli"):
            return f"ports must not import from {imported_layer}"
        if imported_layer == "core" and not inner.startswith("core.models"):
            return "ports may only import from core.models"

    if importer_layer == "adapters":
        if imported_layer in ("container", "cli"):
            return f"adapters must not import from {imported_layer}"

    if importer_layer == "cli":
        if imported_layer in ("core", "ports", "adapters"):
            return (
                f"cli must not import from {imported_layer} directly — use container"
            )

    return None


def main() -> int:
    violations = []
    py_files = [f for f in ROOT.rglob("*.py") if "__pycache__" not in str(f)]
    for filepath in sorted(py_files):
        layer = layer_of(filepath)
        if layer == "other":
            continue
        for module in get_imports(filepath):
            msg = check_import(layer, module)
            if msg:
                violations.append(
                    f"  {filepath.relative_to(ROOT.parent)}: {msg} ({module!r})"
                )

    if violations:
        print("Architecture violations found:")
        for v in violations:
            print(v)
        return 1

    print(f"Architecture OK — checked {len(py_files)} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
