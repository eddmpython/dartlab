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


# ── EDGAR(US) parity 게이트: DART 인벤토리와 동급을 기계 강제 (전문에이전트 아키텍트 감사) ──
def _hasUsData(ticker: str) -> bool:
    """로컬 edgar sections artifact + panel 존재 여부."""
    from dartlab.providers.edgar.docs.sections.sectionsStorage import hasSectionsArtifact

    return hasSectionsArtifact(ticker) and (_dataDir("edgarPanel") / f"{ticker.upper()}.parquet").exists()


_US_FIXTURE = "AAPL"
_US_ENABLED = [_US_FIXTURE] if _hasUsData(_US_FIXTURE) else []


@pytest.mark.skipif(not _US_ENABLED, reason="로컬 edgar 데이터 없음")
def test_usItemsEnumerated():
    """US 인벤토리는 SEC Item 을 15+ 열거(edgar docs 병렬 surface, DART narrative+report 대응)."""
    inv = reportInventory(_US_FIXTURE, marketNs="us")
    byKind = inv["summary"]["byKind"]
    assert byKind.get("item", 0) >= 15, f"US Item 15+ 기대, 실제 {byKind}"
    assert inv["summary"]["total"] >= 20, f"US 총 20+ 기대(재무 5표 + Item), 실제 {inv['summary']['total']}"


@pytest.mark.skipif(not _US_ENABLED, reason="로컬 edgar 데이터 없음")
def test_usHandleNamespaceAndUniqueness():
    """US item handle 은 form-namespaced(form::itemId) + 회사 내 유일(collision 0)."""
    inv = reportInventory(_US_FIXTURE, marketNs="us")
    handles = [u["handle"] for u in inv["units"]]
    assert len(handles) == len(set(handles)), "US handle collision"
    for u in inv["units"]:
        if u["kind"] == "item":
            assert u["handle"].split("::", 1)[0] in ("10-K", "10-Q", "20-F", "40-F"), f"bad namespace {u['handle']}"


@pytest.mark.skipif(not _US_ENABLED, reason="로컬 edgar 데이터 없음")
def test_usRoundTripEveryItem():
    """US parity 크럭스: 모든 item handle 이 get() 으로 non-empty round-trip(enumeration theater 차단)."""
    d = dossier(_US_FIXTURE, marketNs="us")
    inv = reportInventory(_US_FIXTURE, marketNs="us")
    dead = []
    for u in inv["units"]:
        if u["kind"] != "item":
            continue
        df = d.get(u["handle"])
        if df is None or getattr(df, "height", 0) == 0:
            dead.append(u["handle"])
    gc.collect()
    assert not dead, f"US round-trip 실패 handle: {dead[:10]}"


@pytest.mark.skipif(not _US_ENABLED, reason="로컬 edgar 데이터 없음")
def test_usMaterializeItemsRoundTrip():
    """US materialize(items) 배치 경로도 전 item non-empty(sections 1회 로드 slice 정합)."""
    mat = dossier(_US_FIXTURE, marketNs="us").materialize(kinds=("item",))
    gc.collect()
    dead = [h for h, v in mat.items() if v is None or getattr(v, "height", 0) == 0]
    assert not dead, f"US materialize 실패 handle: {dead[:10]}"
