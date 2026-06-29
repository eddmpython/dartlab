"""naver.products 단위 테스트 — ETF·ETN JSON(euc-kr) 파싱·필터 (네트워크 없음)."""

from __future__ import annotations

import json

import pytest

from dartlab.gather.infra.http import runAsync
from dartlab.gather.sources.naver import products

pytestmark = pytest.mark.unit


def _etfRow(code, name, tab=1):
    return {
        "itemcode": code,
        "etfTabCode": tab,
        "itemname": name,
        "nowVal": 10000,
        "changeRate": -0.7,
        "nav": 9990.0,
        "threeMonthEarnRate": 5.1,
        "quant": 12345,
        "amonut": 678,
        "marketSum": 9000,
    }


def _etnRow(code, name):
    return {
        "itemcode": code,
        "itemname": name,
        "nowVal": 26,
        "changeRate": 0.0,
        "accQuant": 140945630,
        "accAmount": 3665,
        "marketSum": 884,
        "listedStockCount": 1000000,
        "prevClose": 26,
        "highVal": 27,
        "lowVal": 25,
    }


_ETF_BYTES = json.dumps(
    {"result": {"etfItemList": [_etfRow("069500", "KODEX 200"), _etfRow("229200", "KODEX 코스닥150")]}},
    ensure_ascii=False,
).encode("euc-kr")
_ETN_BYTES = json.dumps(
    {"result": {"etnItemList": [_etnRow("530036", "삼성 인버스 2X WTI원유 선물 ETN")]}},
    ensure_ascii=False,
).encode("euc-kr")


class _FakeResp:
    """fake httpx 응답 — content(euc-kr bytes)."""

    def __init__(self, content: bytes) -> None:
        self.content = content


class _FakeClient:
    """fake GatherHttpClient — etf/etn URL 로 euc-kr JSON 디스패치."""

    async def get(self, url: str, *, headers=None, **kwargs) -> _FakeResp:
        """etf→ETF bytes, 그 외→ETN bytes."""
        return _FakeResp(_ETF_BYTES if "etf" in url else _ETN_BYTES)


def test_collectEtf_parsesAndRenames():
    """ETF JSON(euc-kr) → 정리 컬럼 DataFrame."""
    df = runAsync(products.collectEtf(_FakeClient()))
    assert df.columns == [
        "code",
        "name",
        "price",
        "changeRate",
        "nav",
        "return3m",
        "volume",
        "amount",
        "marketCap",
        "tabCode",
    ]
    assert df.height == 2
    assert df["name"].to_list() == ["KODEX 200", "KODEX 코스닥150"]


def test_collectEtf_nameFilter():
    """target → 종목명 contains 필터."""
    df = runAsync(products.collectEtf(_FakeClient(), "코스닥"))
    assert df.height == 1
    assert df["code"][0] == "229200"


def test_collectEtn_parses():
    """ETN JSON(euc-kr) → 정리 컬럼 DataFrame."""
    df = runAsync(products.collectEtn(_FakeClient()))
    assert df.columns == [
        "code",
        "name",
        "price",
        "changeRate",
        "volume",
        "amount",
        "marketCap",
        "listedShares",
        "prevClose",
        "high",
        "low",
    ]
    assert df["code"].to_list() == ["530036"]
    assert "원유" in df["name"][0]


def test_collectProducts_emptyResult():
    """빈 목록 → 빈 DataFrame (스키마 유지)."""

    class _Empty(_FakeClient):
        async def get(self, url, *, headers=None, **kwargs):
            return _FakeResp(json.dumps({"result": {"etfItemList": []}}, ensure_ascii=False).encode("euc-kr"))

    df = runAsync(products.collectEtf(_Empty()))
    assert df.is_empty()
    assert "code" in df.columns
