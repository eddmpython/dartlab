"""브라우저에서 credit 이 통째로 죽던 두 결함 (회귀 가드).

브라우저는 KRX 로 나갈 수 없어 ``listing()`` 이 0 행 프레임을 돌려준다. 컬럼은 있지만
값이 하나도 없어 dtype 이 ``Null`` 이다. 그 상태에서 ``df["종목코드"] == "005930"`` 은
``TypeError: cannot convert Python type 'str' to Null`` 을 던진다.

``_fetchProfile`` 의 ``except`` 목록에 ``TypeError`` 가 없어서, 이 예외가 그대로
``Company.credit`` 을 타고 올라가 브라우저에서 credit 이 통째로 죽었다. 축을 뭘 넣든
같았다. scan 쪽은 같은 함정을 이미 알고 막아 뒀는데 credit · analysis · industry 셋은
안 막혀 있었다.

여기서는 브라우저 조건(0 행 Null dtype)을 그대로 만들어 세 진입점이 견디는지 본다.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.analysis.financial import _revenueSegment
from dartlab.credit.scoring import _metricsFetchers
from dartlab.industry import themes


def _emptyListing() -> pl.DataFrame:
    """브라우저가 실제로 돌려주는 모양. shape (0, 2), 두 컬럼 모두 Null dtype."""
    return pl.DataFrame({"회사명": [], "종목코드": []})


class _Company:
    """profile 수집이 건드리는 최소 표면만 가진 대역."""

    stockCode = "005930"
    sector = None
    market = "KR"


def test_emptyListing_reproducesTheOldCrash() -> None:
    """가드가 없으면 정말로 터진다는 것을 못 박는다.

    예외 종류는 polars 버전을 탄다. 브라우저(pyodide)의 polars 는 ``TypeError`` 를,
    지금 서버의 polars 는 ``NotImplementedError`` 를 낸다. 둘 다 옛 ``except`` 목록
    (ImportError · ValueError · KeyError) 밖이라 그대로 위로 올라간다. 그게 요점이다.
    """
    listing = _emptyListing()
    assert listing.schema["종목코드"] == pl.Null
    with pytest.raises((TypeError, NotImplementedError)):
        listing.filter(listing["종목코드"] == "005930")


def test_fetchProfile_survivesEmptyListing(monkeypatch) -> None:
    """credit 의 프로필 수집. 예전에는 여기서 터져 credit 전체가 죽었다."""
    monkeypatch.setattr("dartlab._listingDispatch.listing", _emptyListing)
    assert _metricsFetchers._fetchProfile(_Company()) is None


def test_revenueSegmentProfile_survivesEmptyListing(monkeypatch) -> None:
    """analysis 의 수익구조 프로필. 같은 패턴이었다."""
    monkeypatch.setattr("dartlab._listingDispatch.listing", _emptyListing)
    result = _revenueSegment.calcCompanyProfile(_Company())
    assert result is None or isinstance(result, dict)


def test_stockThemes_survivesEmptyListing(monkeypatch) -> None:
    """industry 의 테마 매칭. 컬럼 존재 검사만 있어 Null dtype 을 못 걸렀다."""
    monkeypatch.setattr("dartlab._listingDispatch.listing", _emptyListing)
    result = themes._stockThemes("005930")
    assert isinstance(result, pl.DataFrame)


def test_chsAdjustment_skipsWhenPriceUnavailable() -> None:
    """시세를 못 얻으면 CHS 보정만 건너뛴다. credit 이 죽으면 안 된다.

    브라우저는 스레드를 못 띄워 ``gather("price")`` 가 ``RuntimeError: can't start new
    thread`` 를 낸다. 옛 코드의 바깥 except 에는 RuntimeError 가 없어 그 예외가 그대로
    ``Company.credit`` 을 타고 올라갔다. 축을 뭘 넣든 브라우저에서 credit 이 죽었다.
    """
    from dartlab.credit import _engineCHS

    class _NoPrice:
        def gather(self, axis: str):
            raise RuntimeError("can't start new thread")

    result = _engineCHS._calcCHSAdjustment(_NoPrice(), 70.0)
    assert result["status"] == "unavailable"
    assert result["reason"] == "price_unavailable"
    assert result["adjustment"] == 0
