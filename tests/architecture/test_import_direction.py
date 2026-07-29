"""선언 계층 단방향 import의 얇은 Guard Index 접점."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_ROOT = REPO_ROOT / "tests" / "audit"
if str(AUDIT_ROOT) not in sys.path:
    sys.path.insert(0, str(AUDIT_ROOT))

from guard.indexer import LAYER_OF, ROOT_FACADE, buildIndex  # noqa: E402
from guard.rules import checkCoreImportBoundary, checkImportDirection  # noqa: E402

L0_L15 = {"core", "gather", "providers", "scan", "frame", "synth", "reference"}


def test_import_direction_downward_only() -> None:
    """모든 선언 계층에서 module-eager 역방향 import가 없어야 한다."""
    assert checkImportDirection(buildIndex(REPO_ROOT)) == []


def test_l0_l15_import_direction_strict() -> None:
    """현재 완료 게이트인 L0~L1.5는 core의 동적 경계까지 함께 닫는다."""
    records = [record for record in buildIndex(REPO_ROOT) if record.topPackage in L0_L15]
    assert checkCoreImportBoundary(records) == []
    assert checkImportDirection(records) == []


def test_layer_order_matchesArchitectureSsot() -> None:
    """레이어 별칭을 포함한 실행 계층표가 현재 architecture SSOT와 일치한다."""
    assert LAYER_OF["core"] == 0.0
    assert {LAYER_OF[name] for name in ("gather", "providers")} == {1.0}
    assert {LAYER_OF[name] for name in ("scan", "frame", "synth", "reference")} == {1.5}
    assert {LAYER_OF[name] for name in ("analysis", "macro", "quant", "industry", "credit")} == {2.0}
    assert LAYER_OF["dataHub"] == LAYER_OF["data"] == 2.5
    assert LAYER_OF["story"] == LAYER_OF["simulate"] == 3.0
    assert LAYER_OF["ai"] == LAYER_OF["mcp"] == 4.0


def test_everySourceModuleHasDeclaredLayer() -> None:
    """새 최상위 source가 계층 판정 밖으로 조용히 빠질 수 없어야 한다."""
    topPackages = {record.topPackage for record in buildIndex(REPO_ROOT)}
    assert topPackages <= set(LAYER_OF) | {ROOT_FACADE}
