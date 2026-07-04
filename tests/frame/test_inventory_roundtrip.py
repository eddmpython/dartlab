"""인벤토리 round-trip 정합성 (전문에이전트 Tier-1 게이트).

두 불변식: (1) 모든 handle 이 materialize 로 non-empty 추출(dead handle 0), (2) handle 유일(collision 0).
정규화 wide board 에서 열거하므로 by construction 성립해야 한다. 로컬 panel 필요라 데이터 없으면 skip.
materialize 는 무겁다(회사당 board 1회 + note cell 재읽기)라 표본 소수.
"""

from __future__ import annotations

import gc

import pytest

from dartlab.core.dataLoader import _dataDir
from dartlab.frame.inventory import reportInventory
from dartlab.frame.workbench import dossier


def _hasData(code: str) -> bool:
    """로컬 panel parquet 존재 여부."""
    return (_dataDir("panel") / f"{code}.parquet").exists()


_RESOLVE_SAMPLE = [c for c in ["005930"] if _hasData(c)]
_UNIQUE_SAMPLE = [c for c in ["005930", "000660"] if _hasData(c)]


@pytest.mark.skipif(not _RESOLVE_SAMPLE, reason="로컬 panel 데이터 없음")
@pytest.mark.parametrize("code", _RESOLVE_SAMPLE)
def test_everyHandleResolvesNonEmpty(code: str):
    """모든 인벤토리 handle 이 materialize 로 non-empty 추출된다(dead handle 0)."""
    d = dossier(code)
    inv = reportInventory(code)
    mat = d.materialize()
    dead = []
    for u in inv["units"]:
        df = mat.get(u["handle"])
        if df is None or getattr(df, "height", 0) == 0:
            dead.append((u["kind"], u["handle"]))
    gc.collect()
    assert not dead, f"resolve 실패 handle: {dead[:10]}"


@pytest.mark.skipif(not _UNIQUE_SAMPLE, reason="로컬 panel 데이터 없음")
@pytest.mark.parametrize("code", _UNIQUE_SAMPLE)
def test_handleUniqueness(code: str):
    """handle 은 회사 내 유일(collision 0)."""
    inv = reportInventory(code)
    handles = [u["handle"] for u in inv["units"]]
    gc.collect()
    dupes = [h for h in set(handles) if handles.count(h) > 1]
    assert not dupes, f"handle collision: {dupes[:10]}"
