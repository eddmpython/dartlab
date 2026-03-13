"""Jupyter 노트북 코드 셀의 Python syntax 검증.

모든 .ipynb 파일의 코드 셀을 ast.parse로 검증한다.
실행은 하지 않으므로 데이터 없이도 CI에서 동작한다.

사용법:
    python scripts/validateNotebooks.py
"""

import ast
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {"_backup", ".ipynb_checkpoints", "node_modules", ".venv"}


def findNotebooks(root: Path) -> list[Path]:
    notebooks = []
    for p in root.rglob("*.ipynb"):
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        notebooks.append(p)
    return sorted(notebooks)


def validateNotebook(path: Path) -> list[str]:
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"{path}: JSON parse error: {exc}"]

    cells = data.get("cells", [])
    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        if not source.strip():
            continue
        # IPython magic (%, !) 라인 제거
        lines = []
        for line in source.splitlines():
            stripped = line.lstrip()
            if stripped.startswith(("%", "!")):
                lines.append("")
            else:
                lines.append(line)
        cleaned = "\n".join(lines)
        if not cleaned.strip():
            continue
        try:
            ast.parse(cleaned, filename=f"{path}:cell[{i}]")
        except SyntaxError as exc:
            errors.append(f"{path}:cell[{i}] line {exc.lineno}: {exc.msg}")
    return errors


def main() -> int:
    notebooks = findNotebooks(REPO_ROOT)
    if not notebooks:
        print("No notebooks found.")
        return 0

    allErrors: list[str] = []
    for nb in notebooks:
        errs = validateNotebook(nb)
        allErrors.extend(errs)

    print(f"Checked {len(notebooks)} notebooks")
    if allErrors:
        print(f"Found {len(allErrors)} syntax errors:")
        for e in allErrors:
            print(f"  {e}")
        return 1

    print("All notebooks passed syntax check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
