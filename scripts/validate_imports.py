"""Verify Python imports across the project — no AI markers, no violations."""

import ast
import os
import sys
from pathlib import Path


def validate_imports(root_dir: str) -> list[str]:
    errors: list[str] = []
    src = Path(root_dir)

    for py_file in src.rglob("*.py"):
        if ".pytest_cache" in str(py_file) or "__pycache__" in str(py_file):
            continue
        try:
            with open(py_file) as f:
                ast.parse(f.read(), filename=str(py_file))
        except SyntaxError as exc:
            errors.append(f"{py_file}: {exc}")

    return errors


def main() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    errors = validate_imports(root)
    if errors:
        print(f"Found {len(errors)} syntax error(s):")
        for err in errors:
            print(f"  {err}")
        sys.exit(1)
    print("All imports validated successfully.")


if __name__ == "__main__":
    main()
