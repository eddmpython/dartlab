"""rank 엔진 unit tests — mock 데이터로 핵심 함수 동작 검증.

buildSnapshot은 전체 종목 순회라 무거우므로 mock.
RankInfo, presets, screen, benchmark, getRank는 순수 로직으로 테스트.
"""

from __future__ import annotations

from dataclasses import asdict

import polars as pl
import pytest

pytestmark = pytest.mark.unit


# ── RankInfo dataclass ──


def test_rankinfo_creation():
    from dartlab.scan.screen import RankInfo

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
    from dartlab.scan.screen import RankInfo

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
    from dartlab.scan.screen import RankInfo

    ri = RankInfo(stockCode="X", corpName="Y", sector="Z", industryGroup="W")
    d = asdict(ri)
    assert d["stockCode"] == "X"
    assert d["revenue"] is None


def test_rankinfo_none_repr():
    """revenue가 None이면 repr에 N/A 표시."""
    from dartlab.scan.screen import RankInfo

    ri = RankInfo(stockCode="X", corpName="테스트", sector="IT", industryGroup="기타")
    assert "N/A" in repr(ri)


# ── presets ──


def test_presets_returns_dict():
    from dartlab.scan.screen import presets

    result = presets()
    assert isinstance(result, dict)
    assert len(result) >= 5
    assert "가치주" in result
    assert "성장주" in result
    assert "고위험" in result


def test_presets_descriptions_are_strings():
    from dartlab.scan.screen import presets

    for name, desc in presets().items():
        assert isinstance(name, str)
        assert isinstance(desc, str)
        assert len(desc) > 0


# ── screen with mock market ratios ──


def _make_market_ratios() -> pl.DataFrame:
    """screen 테스트용 가짜 시장 비율 DataFrame."""
    return pl.DataFrame(
        {
            "stockCode": ["001", "002", "003", "004", "005"],
            "corpName": ["A사", "B사", "C사", "D사", "E사"],
            "sector": ["IT", "금융", "IT", "소재", "IT"],
            "industryGroup": ["반도체", "은행", "SW", "화학", "반도체"],
            "revenueTTM": [200e9, 50e9, 300e9, 10e9, 150e9],
            "operatingIncomeTTM": [20e9, 5e9, 60e9, 1e9, 30e9],
            "netIncomeTTM": [15e9, 4e9, 50e9, 0.5e9, 25e9],
            "totalAssets": [500e9, 2000e9, 100e9, 80e9, 1500e9],
            "totalEquity": [300e9, 200e9, 70e9, 50e9, 800e9],
            "roe": [15.0, 5.0, 25.0, 3.0, 18.0],
            "roa": [8.0, 1.0, 15.0, 2.0, 10.0],
            "operatingMargin": [10.0, 8.0, 20.0, 5.0, 15.0],
            "netMargin": [7.0, 6.0, 16.0, 3.0, 12.0],
            "grossMargin": [40.0, None, 55.0, 30.0, 45.0],
            "ebitdaMargin": [15.0, 12.0, 25.0, 8.0, 20.0],
            "costOfSalesRatio": [60.0, None, 45.0, 70.0, 55.0],
            "sgaRatio": [20.0, None, 15.0, 25.0, 18.0],
            "debtRatio": [66.0, 900.0, 42.0, 60.0, 87.0],
            "currentRatio": [200.0, 50.0, 300.0, 160.0, 180.0],
            "quickRatio": [150.0, 40.0, 250.0, 120.0, 140.0],
            "equityRatio": [60.0, 10.0, 70.0, 62.0, 53.0],
            "interestCoverage": [20.0, 2.0, 50.0, 10.0, 30.0],
            "netDebtRatio": [30.0, None, 10.0, 20.0, 40.0],
            "noncurrentRatio": [40.0, 80.0, 20.0, 50.0, 45.0],
            "totalAssetTurnover": [0.4, 0.03, 3.0, 0.12, 0.1],
            "inventoryTurnover": [8.0, None, 12.0, 6.0, 10.0],
            "receivablesTurnover": [6.0, None, 10.0, 4.0, 8.0],
            "payablesTurnover": [5.0, None, 8.0, 3.0, 7.0],
            "fcf": [10e9, -5e9, 40e9, 1e9, 20e9],
            "operatingCfMargin": [12.0, -3.0, 22.0, 6.0, 18.0],
            "operatingCfToNetIncome": [1.2, 0.8, 1.5, 0.9, 1.3],
            "capexRatio": [5.0, 2.0, 3.0, 8.0, 4.0],
            "dividendPayoutRatio": [30.0, 40.0, 20.0, 50.0, 25.0],
        }
    )


def _get_screen_module():
    """screen 모듈 객체 반환 (__init__의 screen 함수와 이름 충돌 방지)."""
    import importlib

    return importlib.import_module("dartlab.scan.screen.screen")


def test_screen_value_preset(monkeypatch):
    """가치주 프리셋: roe>=10, debtRatio<=100, operatingMargin>=5, currentRatio>=150."""
    screen_mod = _get_screen_module()
    monkeypatch.setattr(screen_mod, "_MARKET_RATIOS", _make_market_ratios())

    df = screen_mod.screen("가치주", verbose=False)
    assert isinstance(df, pl.DataFrame)
    # 001(roe=15, debt=66, opm=10, cr=200) ✓
    # 003(roe=25, debt=42, opm=20, cr=300) ✓
    # 005(roe=18, debt=87, opm=15, cr=180) ✓
    assert df.height >= 3
    codes = df["stockCode"].to_list()
    assert "001" in codes
    assert "003" in codes
    assert "005" in codes
    # 002(roe=5) ✗, 004(roe=3) ✗
    assert "002" not in codes


def test_screen_invalid_preset():
    """존재하지 않는 프리셋은 ValueError."""
    from dartlab.scan.screen import screen

    with pytest.raises(ValueError, match="알 수 없는 프리셋"):
        screen("존재하지않는프리셋")


def test_screen_custom(monkeypatch):
    screen_mod = _get_screen_module()
    monkeypatch.setattr(screen_mod, "_MARKET_RATIOS", _make_market_ratios())

    df = screen_mod.screenCustom([pl.col("sector") == "IT", pl.col("roe") >= 18], verbose=False)
    assert df.height == 2  # 003(roe=25) + 005(roe=18)


def test_benchmark_structure(monkeypatch):
    screen_mod = _get_screen_module()
    monkeypatch.setattr(screen_mod, "_MARKET_RATIOS", _make_market_ratios())

    df = screen_mod.benchmark(verbose=False)
    assert isinstance(df, pl.DataFrame)
    assert "sector" in df.columns
    assert "count" in df.columns
    assert df.height > 0


# ── getRank with mock cache ──


def test_getRank_no_snapshot(monkeypatch):
    """스냅샷이 없으면 None 반환."""
    import dartlab.scan.screen.rank as mod

    monkeypatch.setattr(mod, "_SNAPSHOT", None)
    monkeypatch.setattr(mod, "_loadCache", lambda: None)
    from dartlab.scan.screen import getRank

    assert getRank("005930") is None
