"""engine_call 자동 gather retry — empty 결과 시 company.update() 호출."""

from __future__ import annotations

from unittest.mock import patch

import polars as pl
import pytest

from dartlab.ai.tools.engineCall import _companyShow


class _MockCompany:
    """panel() 가 첫 호출은 빈, 두 번째 호출은 정상 DataFrame 반환."""

    def __init__(self, *, second_call_rows: int = 1, update_returns: dict | None = None) -> None:
        self.corpName = "테스트 주식회사"
        self.stockCode = "005930"
        self._call_count = 0
        self._second_call_rows = second_call_rows
        self._update_returns = update_returns if update_returns is not None else {"finance": 12}
        self.update_called = False

    def panel(self, topic: str) -> pl.DataFrame:
        self._call_count += 1
        if self._call_count == 1:
            return pl.DataFrame({"snakeId": [], "항목": [], "2025Q4": []})
        return pl.DataFrame(
            {
                "snakeId": ["total_assets"] * self._second_call_rows,
                "항목": ["자산총계"] * self._second_call_rows,
                "2025Q4": [514_531_000_000] * self._second_call_rows,
            }
        )

    def update(self, *, categories: list[str]) -> dict:
        self.update_called = True
        return self._update_returns


@pytest.mark.unit
def test_auto_gather_retries_after_empty_result() -> None:
    """첫 show() 가 빈 → update() 자동 호출 → 두 번째 show() 가 정상 → autoGatherUsed=True."""
    company = _MockCompany(second_call_rows=1, update_returns={"finance": 12})
    with patch("dartlab.ai.tools.engineCall._resolveCompany", return_value=company):
        result = _companyShow({"target": "005930", "topic": "BS"})
    assert result.ok is True
    assert company.update_called is True
    assert result.data is not None
    assert result.data.get("autoGatherUsed") is True
    assert "자동 update 후 재조회 성공" in result.summary


@pytest.mark.unit
def test_auto_gather_skipped_when_first_call_succeeds() -> None:
    """첫 show() 가 정상 → update() 호출 X → autoGatherUsed=False."""

    class _StableCompany(_MockCompany):
        def panel(self, topic: str) -> pl.DataFrame:
            self._call_count += 1
            return pl.DataFrame(
                {
                    "snakeId": ["total_assets"],
                    "항목": ["자산총계"],
                    "2025Q4": [514_531_000_000],
                }
            )

    company = _StableCompany()
    with patch("dartlab.ai.tools.engineCall._resolveCompany", return_value=company):
        result = _companyShow({"target": "005930", "topic": "BS"})
    assert result.ok is True
    assert company.update_called is False
    assert result.data is not None
    assert result.data.get("autoGatherUsed") is False


@pytest.mark.unit
def test_auto_gather_disabled_via_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """DARTLAB_AUTO_GATHER=0 면 빈 결과 시 update() 호출 X — 기존 동작 유지."""
    monkeypatch.setenv("DARTLAB_AUTO_GATHER", "0")
    # 모듈 reload 효과를 위해 _AUTO_GATHER_ENABLED 를 직접 패치
    with patch("dartlab.ai.tools.engineCall._AUTO_GATHER_ENABLED", False):
        company = _MockCompany(second_call_rows=1)
        with patch("dartlab.ai.tools.engineCall._resolveCompany", return_value=company):
            result = _companyShow({"target": "005930", "topic": "BS"})
    assert result.ok is False
    assert result.error == "empty_result"
    assert company.update_called is False


@pytest.mark.unit
def test_requested_annual_period_binds_value_and_date_refs() -> None:
    """YYYY 요청은 해당 연도 Q4 누적값을 value/date ref의 기준시점으로 사용한다."""

    class _IncomeCompany(_MockCompany):
        def panel(self, topic: str) -> pl.DataFrame:
            return pl.DataFrame(
                {
                    "snakeId": ["revenue"],
                    "항목": ["매출액"],
                    "2025Q4": [400_000_000_000],
                    "2024Q1": [70_000_000_000],
                    "2024Q2": [80_000_000_000],
                    "2024Q3": [90_000_000_000],
                    "2024Q4": [60_000_000_000],
                }
            )

    company = _IncomeCompany()
    with (
        patch("dartlab.ai.tools.engineCall._resolveCompany", return_value=company),
        patch("dartlab.ai.tools.engineCall.buildPeriodToFiling", return_value={}),
        patch("dartlab.ai.tools.engineCall.getDcrBadge", return_value=None),
        patch("dartlab.ai.tools.engineCall.getIndustryBadge", return_value=None),
    ):
        result = _companyShow({"target": "005930", "topic": "IS", "period": "2024", "freq": "Y"})

    assert result.ok is True
    valueRef = next(ref for ref in result.refs if ref.kind == "valueRef")
    dateRef = next(ref for ref in result.refs if ref.kind == "dateRef")
    assert valueRef.payload["period"] == "2024FY"
    assert valueRef.payload["value"] == 300_000_000_000
    assert dateRef.payload["period"] == "2024FY"
