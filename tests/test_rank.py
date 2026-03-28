"""rank 엔진 unit tests — mock 데이터로 핵심 함수 동작 검증.

buildSnapshot은 전체 종목 순회라 무거우므로 mock.
RankInfo, getRank는 순수 로직으로 테스트.
"""

from __future__ import annotations

from dataclasses import asdict

import pytest

pytestmark = pytest.mark.unit


# ── RankInfo dataclass ──


def test_rankinfo_creation():
    from dartlab.scan.rank import RankInfo

    ri = RankInfo(
        stockCode="005930",
        corpName="삼성전자",
        sector="IT",
        industryGroup="반도체",
        revenue=300_000_000_000_000,
        revenueRank=1,
        revenueTotal=2500,
        sizeClass="large",
    )
    assert ri.stockCode == "005930"
    assert ri.sizeClass == "large"
    assert ri.revenueRank == 1


def test_rankinfo_repr():
    from dartlab.scan.rank import RankInfo

    ri = RankInfo(
        stockCode="005930",
        corpName="삼성전자",
        sector="IT",
        industryGroup="반도체",
        revenueRank=1,
        revenueTotal=2500,
        revenueRankInSector=1,
        revenueSectorTotal=50,
        sizeClass="large",
    )
    text = repr(ri)
    assert "삼성전자" in text
    assert "1/2500" in text


def test_rankinfo_asdict():
    from dartlab.scan.rank import RankInfo

    ri = RankInfo(stockCode="X", corpName="Y", sector="Z", industryGroup="W")
    d = asdict(ri)
    assert d["stockCode"] == "X"
    assert d["revenue"] is None


def test_rankinfo_none_repr():
    """revenue가 None이면 repr에 N/A 표시."""
    from dartlab.scan.rank import RankInfo

    ri = RankInfo(stockCode="X", corpName="테스트", sector="IT", industryGroup="기타")
    assert "N/A" in repr(ri)


# ── getRank with mock cache ──


def test_getRank_no_snapshot(monkeypatch):
    """스냅샷이 없으면 None 반환."""
    import dartlab.scan.rank as mod

    monkeypatch.setattr(mod, "_SNAPSHOT", None)
    monkeypatch.setattr(mod, "_loadCache", lambda: None)
    from dartlab.scan.rank import getRank

    assert getRank("005930") is None
