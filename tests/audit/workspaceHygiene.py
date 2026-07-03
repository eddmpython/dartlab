"""워크스페이스 청결 자동 가드: repo 루트 stray + `.tmp/` 부패 검출.

CLAUDE.md "워크스페이스 청결" 강행규칙의 기계 게이트. 두 가지를 검사한다.
1) repo 루트 직속 엔트리가 allowlist 밖이면 위반. 세션이 흘리는 stray
   (`tmp/`, `.uv-cache-local/`, log/trace/png 류) 신설을 차단한다
   (2026-07-03 루트 잔재 3.1GB 사건 재발 방지).
2) 로컬 스크래치 `.tmp/` 안에서 장수 허용 목록 밖 엔트리가 STALE_DAYS 를
   넘기면 부패 잔재로 위반 (세션 PDF·contact-sheet·pytest-basetemp 류 축적 차단).
CI fresh checkout 에는 로컬 전용 엔트리가 없으므로 무해하게 통과하고,
로컬 preflight/lint 게이트에서 실질 검출이 일어난다.

Sig:
    main() -> int

Args:
    None: CLI argparse 없음. 진입점은 `if __name__ == "__main__":`.

Example:
    ``uv run python -X utf8 tests/audit/workspaceHygiene.py``

Returns:
    exit 0: 위반 없음.
    exit 2: 루트 stray 또는 `.tmp/` 부패 잔재 존재 (목록 stderr 출력).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

STALE_DAYS = 7

# repo 루트 직속 허용 엔트리. 신규 최상위 디렉토리/파일은 의도된 결정일 때만
# 여기 등록한다 (Guard Index 철학: 등록 없는 신규 = 회귀).
ALLOWED_ROOT = frozenset(
    {
        # git 추적 (git ls-tree HEAD 기준)
        ".env.example",
        ".githooks",
        ".github",
        ".gitignore",
        ".pre-commit-config.yaml",
        ".python-version",
        "CHANGELOG.md",
        "CITATION.cff",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "DEPRECATION.md",
        "LICENSE",
        "NOTICE",
        "README.md",
        "README_EN.md",
        "SECURITY.md",
        "blog",
        "codecov.yml",
        "infra",
        "landing",
        "mainPlan",
        "notebooks",
        "package-lock.json",
        "package.json",
        "product-smoke-quick.json",
        "pyodide",
        "pyproject.toml",
        "src",
        "tests",
        "ui",
        "uv.lock",
        # 로컬 전용 인프라 (gitignore 대상, 존재 자체는 정상)
        ".agents",
        ".benchmarks",
        ".claude",
        ".codex",
        ".dartlab",
        ".env",
        ".git",
        ".gitignore.local",
        ".hypothesis",
        ".import_linter_cache",
        ".mcp.json",
        ".playwright-cli",
        ".pytest_cache",
        ".ruff_cache",
        ".tmp",
        ".venv",
        ".vscode",
        "AGENTS.md",
        "CLAUDE.md",
        "data",
        "dist",
        "node_modules",
        "sns",
        # 도구 표준 transient (junk 아님)
        ".coverage",
        "coverage.xml",
        "desktop.ini",
    }
)

# `.tmp/` 장수 허용 디렉토리: 배선이 참조하는 로컬 자산만.
# dart·hf-contentIndex·search-hard-negative = search-productization 로컬 인덱스/평가,
# remotion-props = 캐러셀 렌더 props, dartlab-product-smoke = runProductSmokeWheel venv.
ALLOWED_TMP = frozenset(
    {
        "dart",
        "hf-contentIndex",
        "search-hard-negative",
        "remotion-props",
        "dartlab-product-smoke",
    }
)


def _rootStrays() -> list[str]:
    """루트 직속 allowlist 밖 엔트리 수집."""
    return sorted(entry.name for entry in _REPO.iterdir() if entry.name not in ALLOWED_ROOT)


def _tmpStaleEntries() -> list[str]:
    """`.tmp/` 안 장수 허용 밖 + STALE_DAYS 초과 (또는 stat 불가 ACL 잠금) 엔트리 수집."""
    tmpDir = _REPO / ".tmp"
    if not tmpDir.is_dir():
        return []
    cutoff = time.time() - STALE_DAYS * 86400
    stale: list[str] = []
    for entry in tmpDir.iterdir():
        if entry.name in ALLOWED_TMP:
            continue
        try:
            mtime = entry.stat().st_mtime
        except OSError:
            stale.append(f"{entry.name} (stat 불가: ACL 잠금 잔재, 관리자 takeown 필요)")
            continue
        if mtime < cutoff:
            stale.append(entry.name)
    return sorted(stale)


def main() -> int:
    """루트 stray + `.tmp/` 부패 잔재 검사."""
    violations = 0

    strays = _rootStrays()
    if strays:
        violations += len(strays)
        print(
            "[workspaceHygiene] FAIL: repo 루트 allowlist 밖 엔트리 (CLAUDE.md 워크스페이스 청결).",
            file=sys.stderr,
        )
        for name in strays:
            print(f"  - {name}", file=sys.stderr)
        print(
            "[workspaceHygiene] 잔재면 삭제, 의도된 신규 최상위면 tests/audit/workspaceHygiene.py"
            " ALLOWED_ROOT 에 등록.",
            file=sys.stderr,
        )

    staleEntries = _tmpStaleEntries()
    if staleEntries:
        violations += len(staleEntries)
        print(
            f"[workspaceHygiene] FAIL: .tmp/ 부패 잔재 (장수 허용 밖 + {STALE_DAYS}일 초과).",
            file=sys.stderr,
        )
        for name in staleEntries:
            print(f"  - .tmp/{name}", file=sys.stderr)
        print(
            "[workspaceHygiene] 스크래치는 일회용: 삭제하거나, 배선이 참조하는 장수 자산이면 ALLOWED_TMP 에 등록.",
            file=sys.stderr,
        )

    return 2 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
