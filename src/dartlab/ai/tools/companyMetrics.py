"""회사 재무 metric 추출 — ai/tools 단일 SSOT.

여러 비교/대시보드 도구(peerCompareN · compileFinancialDashboard)가 공유하는
*유일한* 재무 추출 지점. 단일 종목 Company → 표준 metric dict 로 변환한다.
finance 파사드(`panel("IS"/"BS")`, 대소문자 대문자)를 쓰므로 KR(DART)·US(EDGAR)
양쪽을 한 경로로 커버한다 (native acode 셀은 KR 전용이라 cross-market 회귀를 부른다).

호출계약 SSOT: 새 도구가 재무를 추출할 때는 `panel("IS"/"BS")` 를 직접 부르지 말고
본 `companyMetrics` 를 재사용한다 (`tests/audit/aiToolsSingleExtraction.py` 강제).
"""

from __future__ import annotations

from typing import Any

import polars as pl

# snakeId 별칭 — Company.panel 의 실제 키. 사용자 친화 metric 키 ↔ snakeId 매핑.
_METRIC_TO_SNAKE = {
    "revenue": "sales",
    "operatingProfit": "operating_profit",
    "netIncome": "net_incomenet_loss_for_the_year_attributable_toowners_of_parent_equity",
    "totalAssets": "total_assets",
    "totalEquity": "total_stockholders_equity",
    "totalLiabilities": "total_liabilities",
}


def _latestValueFromShow(table: pl.DataFrame, snakeId: str) -> float | None:
    """Company.panel 결과에서 (snakeId, latest period) 셀 값."""
    if not isinstance(table, pl.DataFrame) or table.is_empty():
        return None
    if "snakeId" not in table.columns:
        return None
    periods = [c for c in table.columns if c[:4].isdigit()]
    if not periods:
        return None
    latest = periods[0]
    sub = table.filter(pl.col("snakeId") == snakeId)
    if sub.is_empty():
        return None
    val = sub[0, latest]
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _latestPeriodFromShow(table: pl.DataFrame | None) -> str | None:
    """Company.panel 표에서 최신 공개 기간을 반환한다."""
    if not isinstance(table, pl.DataFrame) or table.is_empty():
        return None
    return next((str(column) for column in table.columns if str(column)[:4].isdigit()), None)


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def companyMetrics(company: Any) -> dict[str, Any]:
    """단일 Company → 비교용 metric dict.

    IS/BS 각각 1 회 panel 호출. _METRIC_TO_SNAKE 매핑으로 실제 snakeId 추출.
    """
    metrics: dict[str, Any] = {}
    if company is None:
        return metrics
    is_df = _safe(lambda: company.panel("IS"))
    bs_df = _safe(lambda: company.panel("BS"))
    metrics["sourcePeriods"] = {
        "IS": _latestPeriodFromShow(is_df),
        "BS": _latestPeriodFromShow(bs_df),
    }
    is_metrics = ("revenue", "operatingProfit", "netIncome")
    bs_metrics = ("totalAssets", "totalEquity", "totalLiabilities")
    for key in is_metrics:
        snake = _METRIC_TO_SNAKE[key]
        metrics[key] = _latestValueFromShow(is_df, snake) if is_df is not None else None
    for key in bs_metrics:
        snake = _METRIC_TO_SNAKE[key]
        metrics[key] = _latestValueFromShow(bs_df, snake) if bs_df is not None else None
    eq = metrics.get("totalEquity")
    liab = metrics.get("totalLiabilities")
    ni = metrics.get("netIncome")
    metrics["debtRatio"] = round(liab / eq * 100, 2) if eq and liab is not None else None
    metrics["roe"] = round(ni / eq * 100, 2) if eq and ni is not None else None
    return metrics


__all__ = ["companyMetrics"]
