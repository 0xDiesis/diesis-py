"""Regenerate Python ABI package re-exports."""

from __future__ import annotations

from pathlib import Path

GENERATED_DIR = Path(__file__).resolve().parents[1] / "src" / "diesis" / "abi" / "generated"
HEADER = '"""Auto-generated ABI re-exports."""\n\n'


def generate_exports(generated_dir: Path) -> None:
    modules = sorted(path.stem for path in generated_dir.glob("*.py") if path.stem != "__init__")
    lines = [HEADER]
    lines.extend(f"from .{module} import *  # noqa: F401, F403\n" for module in modules)
    generated_dir.joinpath("__init__.py").write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    generate_exports(GENERATED_DIR)
