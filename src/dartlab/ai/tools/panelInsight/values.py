"""표에서 값을 꺼내고 읽기 좋게 만드는 원시 도구.

재무제표 매핑은 같은 계정을 여러 이름으로 준다. 하나만 보면 표에서 조용히 빠지므로
이름 후보를 상수로 모아 두고 실제로 있는 행을 고른다. 여기에는 판단이 없다.
"""

from __future__ import annotations

from typing import Any

# 손익계산서에서 매출을 분모로 삼는 비율들. snakeId 는 재무제표 매핑의 정본 이름이다.
_SALES_KEYS = ("sales", "revenue")
_RATIO_ROWS: tuple[tuple[str, str], ...] = (
    ("cost_of_sales", "매출원가율"),
    ("gross_profit", "매출총이익률"),
    ("selling_and_administrative_expenses", "판관비율"),
    # 같은 계정이 매핑에 따라 다른 이름으로 온다. 하나만 보면 표에서 조용히 빠진다.
    ("sga_expenses", "판관비율"),
    ("operating_profit", "영업이익률"),
    ("operating_income", "영업이익률"),
    ("net_income", "순이익률"),
    ("net_profit", "순이익률"),
    ("profit", "순이익률"),
)
# 재무상태표. 분모가 매출이 아니라 항목별로 다르다.
_BS_RATIOS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("부채비율", ("total_liabilities",), ("total_stockholders_equity", "total_equity")),
    ("자기자본비율", ("total_stockholders_equity", "total_equity"), ("total_assets",)),
    ("유동비율", ("current_assets",), ("current_liabilities",)),
    ("현금비중", ("cash_and_cash_equivalents",), ("total_assets",)),
)
_OCF_KEYS = ("cash_flows_from_operating_activities", "operating_cashflow")
_ICF_KEYS = ("cash_flows_from_investing_activities", "investing_cashflow")
_FCF_KEYS = ("cash_flows_from_financing_activities", "financing_cashflow")
_CAPEX_KEYS = ("purchase_of_property_plant_and_equipment", "capital_expenditures")

# 증감률을 보여 줄 대표 항목. 전 행을 다 보이면 표가 읽히지 않는다.
_GROWTH_ROWS = (
    "sales",
    "revenue",
    "operating_profit",
    "operating_income",
    "net_income",
    "net_profit",
    "profit",
    "gross_profit",
    "total_assets",
    "total_liabilities",
    "total_stockholders_equity",
    "cash_flows_from_operating_activities",
    "operating_cashflow",
)
# 기저효과 판정 임계. 기간 최고치의 이 비율보다 낮은 시작점은 증감률을 부풀린다.
_BASE_EFFECT_RATIO = 0.35
_MIN_PERIODS_FOR_POSITION = 3


def _numeric(values: Any, period: str) -> float | None:
    """기간 하나의 수치를 float 로. 값이 없거나 숫자가 아니면 None 이다."""
    if not isinstance(values, dict):
        return None
    raw = values.get(period)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    return float(raw)


def _seriesByKey(timeseries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """snakeId 로 행을 찾을 수 있게 색인한다. 같은 id 는 첫 행이 이긴다."""
    indexed: dict[str, dict[str, Any]] = {}
    for row in timeseries:
        key = str(row.get("snakeId") or "")
        if key and key not in indexed:
            indexed[key] = row
    return indexed


def _pick(indexed: dict[str, dict[str, Any]], keys: tuple[str, ...]) -> dict[str, Any] | None:
    """같은 뜻의 여러 이름 중 실제로 있는 행을 고른다."""
    for key in keys:
        if key in indexed:
            return indexed[key]
    return None


def _withDerivedEquity(indexed: dict[str, dict[str, Any]], periods: list[str]) -> dict[str, dict[str, Any]]:
    """자본 행이 표에 없으면 자산에서 부채를 빼서 채운다.

    실측(2026-08-06): 재무상태표 요약은 대표 항목만 담아 `total_liabilities` 에서 끊긴다.
    그래서 부채비율과 자기자본비율이 통째로 빠졌다. 재무상태표의 대표 지표인데 없는 것이다.
    자본 = 자산 - 부채는 추정이 아니라 회계 항등식이므로 유도해도 사실이 흐려지지 않는다.
    """
    if _pick(indexed, ("total_stockholders_equity", "total_equity")) is not None:
        return indexed
    assets = indexed.get("total_assets")
    liabilities = indexed.get("total_liabilities")
    if assets is None or liabilities is None:
        return indexed
    values: dict[str, float] = {}
    for period in periods:
        top = _numeric(assets.get("values"), period)
        bottom = _numeric(liabilities.get("values"), period)
        if top is not None and bottom is not None:
            values[period] = top - bottom
    if not values:
        return indexed
    return {
        **indexed,
        "total_stockholders_equity": {
            "snakeId": "total_stockholders_equity",
            "item": "자본총계",
            "values": values,
            "formatted": {},
        },
    }


def _formatPercent(value: float | None, *, signed: bool = False) -> str:
    """비율을 읽기 좋은 한 칸으로. 없으면 하이픈이다.

    증감률은 부호를 붙인 퍼센트다. 퍼센트끼리의 차이가 아니므로 퍼센트포인트가 아니다.
    """
    if value is None:
        return "-"
    return f"{value:+.1f}%" if signed else f"{value:.1f}%"


def _row(label: str, cells: list[str]) -> dict[str, Any] | None:
    """모든 칸이 비었으면 행을 만들지 않는다. 하이픈만 있는 줄은 소음이다."""
    return {"label": label, "cells": cells} if any(cell != "-" for cell in cells) else None


def _ratioCells(numerator: dict[str, Any] | None, denominator: dict[str, Any] | None, periods: list[str]) -> list[str]:
    """분자와 분모를 기간별로 나눈 백분율 칸. 어느 쪽이든 없으면 하이픈이다."""
    if numerator is None or denominator is None:
        return ["-"] * len(periods)
    cells: list[str] = []
    for period in periods:
        top = _numeric(numerator.get("values"), period)
        bottom = _numeric(denominator.get("values"), period)
        cells.append("-" if top is None or not bottom else _formatPercent(top / bottom * 100))
    return cells


def _formatAmount(value: float) -> str:
    """금액을 조원 억원 단위 한 칸으로. 부호를 살려 증감을 그대로 읽게 한다."""
    absolute = abs(value)
    if absolute >= 1e12:
        return f"{value / 1e12:+,.1f}조원"
    if absolute >= 1e8:
        return f"{value / 1e8:+,.0f}억원"
    return f"{value:+,.0f}원"
