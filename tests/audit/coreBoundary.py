"""core 경계 lint — `src/dartlab/core/` 안 무엇이 살 수 있는가 강제.

정책 SSOT:
    - `src/dartlab/skills/specs/operation/architecture.md` §L0 정의
      "L0 (core) = 타입·유틸·SSOT 데이터·공용 보안/관측 primitive"
      "core 는 L0 primitive 만. 상위 계층 import 금지."

세 가드:
    1. 상위 layer import 금지 — 정적 import와 동적 import를 같은 Guard Index로 검사.
       concrete 상위 대상은 예외 없이 차단하고 caller-owned generic loader만 허용.
    2. denylist — 명시적으로 core 가 아닌 경로
       (cross/, _entries/, show.py, select.py, messaging.py).
    3. 디렉터리 화이트리스트 — 정의 외 신규 디렉터리 신설 차단. baseline 갱신 시 PR
       으로만 변경 (CHANGELOG + architecture.md 동시 갱신 강제).

cycleScan.py 가 양방향 cycle 만 잡고 "core 안 내용물" 은 안 보는 갭을 메운다.
F4 "정공법 A (core 강등)" 만능 회귀를 차단하는 게 본 lint 의 존재 이유.

실행::

    uv run python -X utf8 tests/audit/coreBoundary.py            # 보고
    uv run python -X utf8 tests/audit/coreBoundary.py --strict   # 위반 ≥ 1 → exit 2

종료 코드:
    0 — 위반 0 (또는 --strict 미지정 시 모든 경우)
    2 — 위반 ≥ 1 + --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from guard.indexer import buildIndex
from guard.rules import checkCoreImportBoundary

for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if callable(_reconfigure):
        _reconfigure(encoding="utf-8", errors="replace")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CORE = _REPO_ROOT / "src" / "dartlab" / "core"

# 명시적 denylist — architecture.md / core_boundary.md 정의에 따른 확정 위반.
# 각 항목: (core 기준 상대 경로, 위반 사유, 가야 할 곳)
_DENYLIST: tuple[tuple[str, str, str], ...] = (
    ("cross", "L2 도메인 조합 (architecture #4 — story 가 단독 부담)", "story/cross/ 또는 skills"),
    ("_entries", "Company API entry = L4 표면 (architecture L4)", "dartlab/_entries/ 또는 company/"),
    ("show.py", "Company.show() API = L4", "company/show.py 또는 dartlab/"),
    ("select.py", "Company.select() API = L4", "company/select.py 또는 dartlab/"),
    ("messaging.py", "cli/server messaging = ≥ L1", "cli/messaging.py 또는 server/messaging.py"),
)

# 정의된 (= 허용된) 1 차 디렉터리 — 이 외 신규 디렉터리 신설은 PR 필요.
# architecture.md L0 정의 + 현재 SSOT 데이터 구조.
_ALLOWED_DIRS: frozenset[str] = frozenset(
    {
        "_entries",  # denylist에 있지만 이전 전까지 존재를 추적
        "accounts",  # DART/EDGAR 공용 계정 정규화 SSOT
        "cache",  # L0 cache infra
        "capability",  # capability infra (generated 만 denylist)
        "cross",  # denylist 에 있지만 디렉터리 자체는 존재 인정 (이전 전까지)
        "data",  # parser data
        "docs",  # denylist 에 있지만 디렉터리 자체는 존재 인정 (이전 전까지)
        "indicators",  # gather/synth 공용 vectorized primitive
        "mappers",  # SSOT mapper
        "naming",  # SSOT naming
        "providers",  # credential/secret 공용 보안 primitive
        "render",  # render protocol
        "search",  # L0 search infra
        "sector",  # SSOT sector classification
        "utils",  # L0 utils
    }
)


def _isPyFile(p: Path) -> bool:
    return p.suffix == ".py" and not p.name.endswith(".pyc")


def _checkUpstreamImports() -> list[str]:
    """가드 1 — Guard Index와 같은 정적·동적 core import 경계를 적용한다."""
    violations = checkCoreImportBoundary(buildIndex(_REPO_ROOT))
    return [f"{item.path}:{item.line}  {item.message}  ({item.rule})" for item in violations]


def _checkDenylist() -> list[str]:
    """가드 2 — 명시적 denylist 경로 존재 여부."""
    violations: list[str] = []
    for relPath, reason, suggestion in _DENYLIST:
        target = _CORE / relPath
        if target.exists():
            rel = target.relative_to(_REPO_ROOT)
            violations.append(f"{rel}\n      이유: {reason}\n      이전 권고: {suggestion}")
    return violations


def _checkDirectoryWhitelist() -> list[str]:
    """가드 3 — core/ 1 차 디렉터리 화이트리스트 (정의 외 신설 차단)."""
    violations: list[str] = []
    if not _CORE.exists():
        return violations
    for child in _CORE.iterdir():
        if not child.is_dir() or child.name == "__pycache__":
            continue
        if child.name not in _ALLOWED_DIRS:
            rel = child.relative_to(_REPO_ROOT)
            violations.append(
                f"{rel}/  (화이트리스트 외 디렉터리 — architecture.md L0 정의 + _ALLOWED_DIRS 확장 PR 필요)"
            )
    return violations


def _topLevelFileStats() -> dict[str, int]:
    """진단 — core/ 1 차 .py 라인 카운트 상위. denylist 후보 자동 검토용."""
    stats: dict[str, int] = {}
    if not _CORE.exists():
        return stats
    for child in _CORE.iterdir():
        if not child.is_file() or child.suffix != ".py":
            continue
        try:
            lines = sum(1 for _ in child.open(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        stats[child.name] = lines
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="위반 ≥ 1 → exit 2")
    parser.add_argument("--quiet", action="store_true", help="violations 만 출력")
    args = parser.parse_args()

    upstream = _checkUpstreamImports()
    deny = _checkDenylist()
    whitelist = _checkDirectoryWhitelist()

    total = len(upstream) + len(deny) + len(whitelist)

    if not args.quiet:
        print("=" * 72)
        print("core 경계 lint")
        print("=" * 72)

    if upstream:
        print(f"\n[가드 1] 상위 layer import — {len(upstream)} 건")
        for v in upstream:
            print(f"  {v}")
    elif not args.quiet:
        print("\n[가드 1] 상위 layer import — 0 건 OK")

    if deny:
        print(f"\n[가드 2] denylist — {len(deny)} 건")
        for v in deny:
            print(f"  {v}")
    elif not args.quiet:
        print("\n[가드 2] denylist — 0 건 OK")

    if whitelist:
        print(f"\n[가드 3] 디렉터리 화이트리스트 외 — {len(whitelist)} 건")
        for v in whitelist:
            print(f"  {v}")
    elif not args.quiet:
        print("\n[가드 3] 디렉터리 화이트리스트 — 0 건 OK")

    if not args.quiet:
        stats = _topLevelFileStats()
        if stats:
            top = sorted(stats.items(), key=lambda kv: kv[1], reverse=True)[:5]
            print("\n[진단] core/ 1 차 .py 라인 상위 5:")
            for name, lines in top:
                print(f"  {lines:>6}  {name}")

        print(f"\n총 위반: {total} 건")
        if total > 0:
            print("→ 이전 대상은 PLAN.md 현 phase 종료 조건과 묶어 처리.")

    if args.strict and total > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
