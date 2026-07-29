"""dartlab.gather.entry.dispatch real unit test (A 트랙 T1).

AXIS_REGISTRY 일관성 + AXIS_ALIASES + _resolveAxis + INDEX_SYMBOLS self-map +
_fetchNaverIndex 공통 HTTP 경로·기간·파싱 오류 검증.
"""

from __future__ import annotations

import importlib
from datetime import date

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.entry.dispatch`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.entry.dispatch")


def test_resolveAxis_registry() -> None:
    """registry key 직접 지정 시 그대로 반환 — case-sensitive."""
    from dartlab.gather.entry.dispatch import AXIS_REGISTRY, _resolveAxis

    for key in AXIS_REGISTRY:
        assert _resolveAxis(key) == key


def test_resolveAxis_alias() -> None:
    """AXIS_ALIASES 매핑 — 한글/별칭 → registry key 정상 변환."""
    from dartlab.gather.entry.dispatch import AXIS_ALIASES, _resolveAxis

    for alias, target in AXIS_ALIASES.items():
        assert _resolveAxis(alias) == target


def test_resolveAxis_unknown_raises() -> None:
    """미등록 축 / case 불일치 → ValueError."""
    from dartlab.gather.entry.dispatch import _resolveAxis

    with pytest.raises(ValueError, match="알 수 없는 gather 축"):
        _resolveAxis("nonexistent_axis")
    # case-sensitive 검증 — "Price" 는 registry key 가 아님
    with pytest.raises(ValueError):
        _resolveAxis("Price")


def test_INDEX_SYMBOLS_self_map() -> None:
    """INDEX_SYMBOLS — 정식 외부 API 심볼은 self-map (KOSPI/KOSDAQ/KPI200)."""
    from dartlab.gather.entry.dispatch import INDEX_SYMBOLS

    assert INDEX_SYMBOLS["KOSPI"] == "KOSPI"
    assert INDEX_SYMBOLS["KOSDAQ"] == "KOSDAQ"
    assert INDEX_SYMBOLS["KPI200"] == "KPI200"
    # 한글 alias
    assert INDEX_SYMBOLS["코스피"] == "KOSPI"
    assert INDEX_SYMBOLS["코스닥"] == "KOSDAQ"


def test_fetchNaverIndex_empty_response() -> None:
    """_fetchNaverIndex — 정상 HTTP 응답에 항목이 없으면 빈 DataFrame."""
    from dartlab.gather.entry import dispatch as dispatchMod

    class FakeResp:
        text = ""

    class FakeClient:
        async def get(self, *args, **kwargs):
            return FakeResp()

    df = dispatchMod._fetchNaverIndex("KOSPI", limit=10, client=FakeClient())
    assert isinstance(df, pl.DataFrame)
    assert df.is_empty()


def test_fetchNaverIndex_uses_common_client_and_filters_period() -> None:
    """지수 가격은 공통 클라이언트로 조회하고 start/end를 양 끝 포함 적용한다."""
    from dartlab.gather.entry import dispatch as dispatchMod

    class FakeResp:
        text = (
            '<item data="20260101|100|110|90|105|1000"/>'
            '<item data="20260102|105|115|95|110|1100"/>'
            '<item data="20260103|110|120|100|115|1200"/>'
        )

    class FakeClient:
        def __init__(self) -> None:
            self.params = None

        async def get(self, url, *, params, timeout):
            assert url == "https://fchart.stock.naver.com/sise.nhn"
            assert timeout == 15
            self.params = params
            return FakeResp()

    client = FakeClient()
    df = dispatchMod._fetchNaverIndex(
        "KOSPI",
        start="2026-01-02",
        end="2026-01-02",
        client=client,
    )

    assert client.params["count"] == 6000
    assert df["date"].to_list() == [date(2026, 1, 2)]
    assert df["close"].to_list() == [110.0]


def test_fetchNaverIndex_malformed_row_raises() -> None:
    """공급자 응답 손상은 빈 결과로 삼키지 않는다."""
    from dartlab.gather.entry import dispatch as dispatchMod

    class FakeResp:
        text = '<item data="20260101|bad|110|90|105|1000"/>'

    class FakeClient:
        async def get(self, *args, **kwargs):
            return FakeResp()

    with pytest.raises(ValueError, match="해석할 수 없습니다"):
        dispatchMod._fetchNaverIndex("KOSPI", client=FakeClient())
