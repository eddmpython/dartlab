"""buildSearchIndexUs openable 게이트. 손익신호(sales OR net_profit)면 검색에 포함.

금융·REIT 는 매출(sales) 태그가 비고 net_profit 만 있어도 열려야 한다(매출 only 게이트가
은행·REIT 수백 종목을 부당 제외하던 회귀 가드). 합성 parquet, 네트워크/OOM 무관.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit

_SCRIPT = Path(__file__).resolve().parents[2] / ".github" / "scripts" / "prebuild" / "buildSearchIndexUs.py"


def _loadBuild():
    """buildSearchIndexUs.build 함수 로드(스크립트라 importlib 경유)."""
    spec = importlib.util.spec_from_file_location("buildSearchIndexUsForTest", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build


def test_gate_includes_net_profit_only_company(tmp_path):
    """net_profit 만 있고 sales 없는 종목(은행·REIT)도 검색 포함, 매출 0 랭킹 하단."""
    build = _loadBuild()
    scanPath = tmp_path / "finance.parquet"
    tickersPath = tmp_path / "tickers.parquet"
    out = tmp_path / "search-index-us.json"

    pl.DataFrame(
        {
            "stockCode": ["MFG", "BANK", "SHELL"],
            "sales": [1_000_000_000.0, None, None],  # MFG 매출, BANK·SHELL 없음
            "net_profit": [50_000_000.0, 80_000_000.0, None],  # BANK 순이익만, SHELL 둘 다 없음
            "sector": ["manufacturing", "banks", None],
            "fy": [2024, 2024, 2024],
        }
    ).write_parquet(scanPath)
    pl.DataFrame(
        {
            "ticker": ["MFG", "BANK", "SHELL"],
            "title": ["Maker Inc", "Big Bank", "Empty Shell"],
            "exchange": ["NYSE", "NYSE", "NYSE"],
        }
    ).write_parquet(tickersPath)

    n = build(tickersPath, scanPath, out)
    rows = {r["stockCode"]: r for r in json.loads(out.read_text(encoding="utf-8"))}
    assert "MFG" in rows  # 매출 있음
    assert "BANK" in rows  # 순이익만 있어도 포함(회귀 가드 핵심)
    assert "SHELL" not in rows  # 손익신호 전무 제외
    assert rows["BANK"]["revenue"] == 0.0  # 매출 없으니 랭킹용 0
    assert rows["MFG"]["revenue"] > 0
    assert n == 2
