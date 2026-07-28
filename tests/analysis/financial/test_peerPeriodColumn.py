"""시장 백분위의 기준 기간 선택 가드.

이름만 보고 최신 기간 열을 고르면 아직 공시가 거의 안 들어온 분기를 집는다. 2026 년
7 월 기준 ROE 표의 최신 열은 2026Q3 인데 2,812 종목 중 2 종목(0.1%) 만 값이 있었고,
삼성전자도 비어 있어 시장 백분위가 어느 회사에서도 나오지 않았다. 비교분석 축 셋이
통째로 None 이던 원인이다.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit

from dartlab.analysis.financial.peerBenchmark import _latestPeriodCol


def _frame(fill: dict[str, list[float | None]]) -> pl.DataFrame:
    return pl.DataFrame({"종목코드": [f"{i:06d}" for i in range(len(next(iter(fill.values()))))], **fill})


class TestLatestPeriodCol:
    def test_skips_barely_filled_newest_quarter(self):
        """갓 시작한 분기는 이름이 최신이어도 기준이 될 수 없다."""
        df = _frame(
            {
                "2026Q3": [1.0] + [None] * 9,  # 10 중 1 만 참
                "2026Q1": [float(i) for i in range(10)],  # 전부 참
            }
        )
        assert _latestPeriodCol(df) == "2026Q1"

    def test_picks_newest_among_well_filled(self):
        df = _frame(
            {
                "2026Q1": [float(i) for i in range(10)],
                "2025Q4": [float(i) for i in range(10)],
            }
        )
        assert _latestPeriodCol(df) == "2026Q1"

    def test_slightly_thinner_newest_still_wins(self):
        """수집 진도 차이는 정상이다. 문턱은 가장 잘 찬 열 대비 상대값이다."""
        df = _frame(
            {
                "2026Q1": [float(i) for i in range(9)] + [None],  # 10 중 9
                "2025Q4": [float(i) for i in range(10)],
            }
        )
        assert _latestPeriodCol(df) == "2026Q1"

    def test_no_period_column_is_none(self):
        assert _latestPeriodCol(pl.DataFrame({"종목코드": ["005930"]})) is None

    def test_all_empty_is_none(self):
        df = _frame({"2026Q3": [None] * 5, "2026Q1": [None] * 5})
        assert _latestPeriodCol(df) is None
