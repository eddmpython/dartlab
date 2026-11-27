"""지주회사 판정이 상장 목록의 지주 표기를 먼저 보는지 본다(2026-11-27 LG 회귀).

영업외손익의 세전이익 계정을 고치자 LG(003550)가 재무 기준으로는 지주회사가 아니게 됐다
(지분법이익이 영업이익의 15%). 예전 판정은 세전이익을 0 으로 읽은 오류가 우연히 맞힌 것이다.
LG·SK·GS 는 KIND 상장법인 목록 주요제품에 '지주회사' 를 적는다.
"""

from __future__ import annotations

from types import SimpleNamespace

import polars as pl
import pytest

from dartlab.analysis.financial import companyType


@pytest.fixture
def kindList(monkeypatch):
    """상장 목록을 작은 표로 바꾼다."""
    df = pl.DataFrame(
        {
            "종목코드": ["003550", "000320", "005930", "105560"],
            "주요제품": ["지주회사", "지주사업", "반도체, 휴대폰", "-"],
        }
    )
    import dartlab.gather.krx.listing.registry as registry

    monkeypatch.setattr(registry, "getKindList", lambda **_: df)
    return df


@pytest.mark.unit
@pytest.mark.parametrize(
    ("code", "name", "expected"),
    [
        ("003550", "LG", True),
        ("000320", "노루홀딩스", True),
        ("005930", "삼성전자", False),
        ("105560", "KB금융", False),
        ("086790", "하나금융지주", True),
        ("AAPL", "Apple Holdings", False),
    ],
)
def test_listed_as_holding(kindList, code, name, expected):
    company = SimpleNamespace(stockCode=code, corpName=name)
    assert companyType._listedAsHolding(company) is expected


@pytest.mark.unit
def test_check_holding_uses_listing_before_financials(kindList, monkeypatch):
    import dartlab.analysis.financial.earningsQuality as eq

    def noFinancials(_company):
        """재무 기준이 불리면 시험을 실패시킨다."""
        raise AssertionError("상장 목록에서 지주회사인데 재무 기준까지 갔다")

    monkeypatch.setattr(eq, "calcNonOperatingBreakdown", noFinancials)
    assert companyType._checkHolding(SimpleNamespace(stockCode="003550", corpName="LG")) is True
