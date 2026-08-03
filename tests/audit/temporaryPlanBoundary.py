"""임시 설계와 영구 제품 계약의 경계를 검사한다.

영구 자산은 임시 설계 경로를 인용하지 않는다. 완료 설계를 보관하는 `_done`
폴더도 허용하지 않는다. 정책 파일과 이 감사 자체는 검사 대상에서 제외한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN_ROOT = _REPO / "mainPlan"
_TEXT_SUFFIXES = frozenset(
    {
        ".css",
        ".html",
        ".js",
        ".json",
        ".md",
        ".mjs",
        ".py",
        ".sql",
        ".svelte",
        ".toml",
        ".ts",
        ".tsx",
        ".yaml",
        ".yml",
    }
)
_ROOT_FILES = (
    "ARCHITECTURE.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "DEPRECATION.md",
    "README.md",
    "README_EN.md",
    "SECURITY.md",
)
_PERMANENT_ROOTS = (
    ".github",
    "blog",
    "docs",
    "infra",
    "landing",
    "notebooks",
    "pyodide",
    "src",
    "tests",
    "ui",
)
_EXCLUDED = {
    Path("tests/audit/checkUiDataWiring.mjs"),
    Path("tests/audit/temporaryPlanBoundary.py"),
    Path("tests/audit/workspaceHygiene.py"),
}
_EXCLUDED_ROOTS = (
    Path("landing/.svelte-kit"),
    Path("landing/build"),
    Path("tests/_attempts"),
)


def _isExcluded(relative: Path) -> bool:
    """정책 검사 자체, 졸업 전 실험, 생성 산출물을 영구 자산에서 제외한다."""
    return relative in _EXCLUDED or any(relative == root or root in relative.parents for root in _EXCLUDED_ROOTS)


def _candidateFiles() -> list[Path]:
    """검사할 영구 텍스트 파일을 결정론 순서로 반환한다."""
    files = [(_REPO / name) for name in _ROOT_FILES if (_REPO / name).is_file()]
    for rootName in _PERMANENT_ROOTS:
        root = _REPO / rootName
        if not root.is_dir():
            continue
        files.extend(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in _TEXT_SUFFIXES)
    return sorted(set(files))


def _permanentReferences() -> list[str]:
    """임시 설계 디렉터리 이름을 인용한 영구 파일을 찾는다."""
    violations: list[str] = []
    for path in _candidateFiles():
        relative = path.relative_to(_REPO)
        if _isExcluded(relative):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "mainPlan" in text:
            violations.append(relative.as_posix())
    return violations


def main() -> int:
    """영구 역참조와 완료 보관 폴더가 없으면 0을 반환한다."""
    violations = _permanentReferences()
    doneRoot = _PLAN_ROOT / "_done"
    if doneRoot.exists():
        violations.append("mainPlan/_done")

    if violations:
        print("[temporaryPlanBoundary] FAIL: 임시 설계를 영구 자산이나 완료 보관소로 사용했습니다.", file=sys.stderr)
        for value in sorted(set(violations)):
            print(f"  - {value}", file=sys.stderr)
        return 2

    print("[temporaryPlanBoundary] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
