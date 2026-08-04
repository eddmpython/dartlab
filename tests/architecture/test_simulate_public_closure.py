"""simulate 공개 계약 폐쇄의 얇은 Guard Index 접점.

공개 호출계약 강행규칙(CLAUDE.md)의 simulate 판: 계약 표면은 frozen manifest
(guard.rules.SIMULATE_CONTRACT_CLOSURE) 6모듈로 고정되고, 나머지 스택은
scenario-simulator initiative 자산이라 import 한 줄로도 공개 표면이 될 수 없다.
승격·삭제는 manifest 수정(=의도적 계약 검토)으로만 한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_ROOT = REPO_ROOT / "tests" / "audit"
if str(AUDIT_ROOT) not in sys.path:
    sys.path.insert(0, str(AUDIT_ROOT))

from guard.indexer import buildIndex  # noqa: E402
from guard.rules import (  # noqa: E402
    SIMULATE_CONTRACT_CLOSURE,
    SIMULATE_OPERATIONAL_SURFACE,
    checkSimulateContractClosure,
)


def test_simulate_contract_closure_is_fixed_point() -> None:
    """계약 6모듈 밖 simulate 하위 모듈은 어떤 src 경로에서도 도달할 수 없어야 한다."""
    assert checkSimulateContractClosure(buildIndex(REPO_ROOT)) == []


def test_manifests_are_disjoint_and_minimal() -> None:
    """계약 폐쇄와 운영 표면은 겹치지 않고, 폐쇄는 실측된 6모듈 그대로여야 한다."""
    assert SIMULATE_CONTRACT_CLOSURE.isdisjoint(SIMULATE_OPERATIONAL_SURFACE)
    assert len(SIMULATE_CONTRACT_CLOSURE) == 6


def test_operational_surface_matches_cron_script_imports() -> None:
    """운영 manifest 는 월간 cron 스크립트의 실제 simulate import 와 일치해야 한다.

    manifest 만 넓히거나 cron 만 바뀌는 stale 사고를 양방향으로 잡는다.
    """
    import ast

    script = REPO_ROOT / ".github" / "scripts" / "sync" / "buildExpectations.py"
    tree = ast.parse(script.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("dartlab.simulate."):
            imported.add(node.module)
    # dataStore 는 expectationLedger 경유 전이 소비라 직접 import 목록에는 없어도 된다.
    assert imported <= SIMULATE_OPERATIONAL_SURFACE
    assert "dartlab.simulate.expectationCycle" in imported
