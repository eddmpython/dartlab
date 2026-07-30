"""scan 공개 ``universe`` 계약 회귀.

engines.scan spec 이 발행한 ``universe`` (entity-set 선택자) 를 scanClass facade 가
실제로 구현하는지, 미지원 형태를 조용히 축 함수로 흘려 raw ``TypeError`` 를 내지
않고 loud 하게 거부하는지 고정한다.
"""

from __future__ import annotations

import inspect

import polars as pl
import pytest

import dartlab
from dartlab.scan.scanClass import (
    Scan,
    _normalizeMarket,
    _normalizeStockCodes,
    _resolveRequestedUniverse,
)

pytestmark = pytest.mark.unit


def testUniverseParameterExists() -> None:
    """__call__ 시그니처에 universe 파라미터가 실재한다."""
    assert "universe" in inspect.signature(Scan.__call__).parameters


@pytest.mark.parametrize(
    ("value", "expected"),
    [("KR", "KR"), ("kr", "KR"), ("DART", "KR"), ("US", "US"), ("edgar", "US")],
)
def testNormalizeMarketAlias(value: str, expected: str) -> None:
    """시장 alias 는 KR/US 정규 코드로 해소된다."""
    assert _normalizeMarket(value) == expected


@pytest.mark.parametrize("value", ["JP", "KOSPI", "", "  "])
def testNormalizeMarketRejectsUnsupported(value: str) -> None:
    """미지원 시장 문자열은 loud 하게 거부된다."""
    with pytest.raises(ValueError, match="지원하지 않는 market|문자열이어야"):
        _normalizeMarket(value)


def testNormalizeStockCodesZeroPadsAndUppercases() -> None:
    """KR 숫자코드는 zero-pad, US ticker 는 대문자 변이를 함께 담는다."""
    variants = _normalizeStockCodes(["5930", "aapl"])
    assert "005930" in variants  # zero-pad
    assert "5930" in variants  # raw
    assert "AAPL" in variants  # upper


@pytest.mark.parametrize("value", [[], "005930", [""], [123]])
def testNormalizeStockCodesRejectsBad(value: object) -> None:
    """빈 목록·문자열·비문자열 원소는 loud 거부."""
    with pytest.raises(ValueError):
        _normalizeStockCodes(value)


def testResolveMarketDict() -> None:
    """{"market": ...} 형태가 시장으로 해소된다."""
    market, codes = _resolveRequestedUniverse({"market": "US"}, None)
    assert market == "US"
    assert codes is None


def testResolveStockCodesDict() -> None:
    """{"stockCodes": [...]} 는 시장 없이 종목 필터만 만든다."""
    market, codes = _resolveRequestedUniverse({"stockCodes": ["005930"]}, None)
    assert market is None
    assert codes is not None and "005930" in codes


def testUniverseAndMarketConflictRejected() -> None:
    """universe 와 market 이 서로 다른 시장이면 거부한다."""
    with pytest.raises(ValueError, match="서로 다른 시장"):
        _resolveRequestedUniverse("KR", "US")


def testUniverseSameMarketAllowed() -> None:
    """universe 와 market 이 같은 시장이면 통과한다."""
    market, _codes = _resolveRequestedUniverse("US", "EDGAR")
    assert market == "US"


def testIndustryHintRoutedToIndustryEngine() -> None:
    """universe industryHint 는 산업 SSOT 중복을 피해 industry 엔진으로 라우팅한다."""
    with pytest.raises(ValueError, match="industryHint"):
        _resolveRequestedUniverse({"industryHint": "반도체"}, None)


def testUnknownUniverseKeyRejected() -> None:
    """알 수 없는 universe 키는 조용히 무시하지 않고 거부한다."""
    with pytest.raises(ValueError, match="지원하지 않는 universe 키"):
        _resolveRequestedUniverse({"sector": "x"}, None)


def testUnknownUniverseTypeRejected() -> None:
    """str/dict 가 아닌 universe 는 거부한다."""
    with pytest.raises(ValueError, match="str 또는 dict"):
        _resolveRequestedUniverse(123, None)  # type: ignore[arg-type]


def testUnsupportedMarketOnAxisRejected() -> None:
    """KR 전용 축에 universe='US' 를 주면 데이터 로드 전에 거부한다."""
    with pytest.raises(ValueError, match="지원하지 않습니다"):
        dartlab.scan("governance", universe="US")


def _syntheticProfitability(**_kwargs: object) -> pl.DataFrame:
    """축 함수 대역. 세 종목 합성 결과 (종목명 join 회피용 종목코드 컬럼)."""
    return pl.DataFrame(
        {
            "종목코드": ["005930", "000660", "035720"],
            "ROE": [10.0, 12.0, 8.0],
        }
    )


def testUniverseStockCodesFiltersResult(monkeypatch: pytest.MonkeyPatch) -> None:
    """universe stockCodes 가 전종목 결과를 요청 종목으로 좁힌다."""
    monkeypatch.setattr(
        "dartlab.scan.financial.profitability.scanProfitability",
        _syntheticProfitability,
        raising=True,
    )
    out = dartlab.scan("profitability", universe={"stockCodes": ["005930", "035720"]})
    assert isinstance(out, pl.DataFrame)
    assert set(out["종목코드"].to_list()) == {"005930", "035720"}


def testUniverseNoLongerLeaksTypeError(monkeypatch: pytest.MonkeyPatch) -> None:
    """universe='KR' 이 축 함수로 새어 raw TypeError 를 내지 않는다 (결함 회귀)."""
    monkeypatch.setattr(
        "dartlab.scan.financial.profitability.scanProfitability",
        _syntheticProfitability,
        raising=True,
    )
    out = dartlab.scan("profitability", universe="KR")
    assert isinstance(out, pl.DataFrame)
    assert out.height == 3


def testUniverseUsRoutesToEdgarDispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """US 지원 축에 universe='US' 는 EDGAR dispatcher 로 분기한다."""
    captured: dict[str, object] = {}

    def _fakeDispatch(axis: str, kwargs: dict) -> pl.DataFrame:
        captured["axis"] = axis
        return pl.DataFrame({"ticker": ["AAPL"], "ROE": [30.0]})

    monkeypatch.setattr("dartlab.scan.scanClass._edgarDispatch", _fakeDispatch, raising=True)
    out = dartlab.scan("profitability", universe="US")
    assert captured["axis"] == "profitability"
    assert isinstance(out, pl.DataFrame)
    assert out["ticker"].to_list() == ["AAPL"]
