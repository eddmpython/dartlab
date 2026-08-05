"""재무제표 시계열에서 판단 재료를 뽑아 답변 표면에 함께 싣는다.

왜 필요한가. DartLab 은 모델 루프를 설치형 CLI 에 넘긴 중개상이라 답변을 직접 고쳐 쓸 수
없다. 답변 품질을 올리는 유일한 정공법은 **건네주는 근거 자체를 판단 가능한 형태로 만드는
것**이다. 원시 수치 표만 주면 마진과 증감률과 기저효과 판별을 모델이 매번 손으로 해야 하고,
그 계산을 잘하는 모델과 못하는 모델 사이에서 답변 품질이 갈린다.

실측 배경(2026-08-06). 강한 모델은 손익 표만 받고도 원가율 하락이 이익 개선의 몸통임을
스스로 찾아냈고 2023FY 저점이 기저효과임을 지적했다. 같은 표를 받은 약한 모델은 "영업이익
5 배 성장" 으로 끝낼 수 있다. 그 차이를 모델에 맡기지 않고 표에 실어 보낸다.

계산은 이미 손에 있는 시계열만 쓴다. 추가 조회가 없으므로 지연이 늘지 않는다.
`Panel` wide DataFrame 의 형태와 내용은 건드리지 않는다. 여기서 만드는 것은 표현 계층의
병존 projection 이다.
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


def _growthRows(indexed: dict[str, dict[str, Any]], periods: list[str]) -> list[dict[str, Any]]:
    """대표 항목의 전기 대비 증감률. periods 는 최신이 앞이므로 다음 원소가 직전 기간이다."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key in _GROWTH_ROWS:
        row = indexed.get(key)
        if row is None or row.get("item") in seen:
            continue
        values = row.get("values")
        cells: list[str] = []
        for index, period in enumerate(periods):
            current = _numeric(values, period)
            prior = _numeric(values, periods[index + 1]) if index + 1 < len(periods) else None
            if current is None or prior is None or prior == 0:
                cells.append("-")
            else:
                cells.append(_formatPercent((current - prior) / abs(prior) * 100, signed=True))
        built = _row(f"{row.get('item')} 증감률", cells)
        if built:
            seen.add(str(row.get("item")))
            out.append(built)
    return out


def _balanceRows(indexed: dict[str, dict[str, Any]], periods: list[str]) -> list[dict[str, Any]]:
    """재무상태표 비율. 분모가 항목마다 달라 짝을 명시한다."""
    balanced = _withDerivedEquity(indexed, periods)
    out: list[dict[str, Any]] = []
    for label, numeratorKeys, denominatorKeys in _BS_RATIOS:
        cells = _ratioCells(_pick(balanced, numeratorKeys), _pick(balanced, denominatorKeys), periods)
        built = _row(label, cells)
        if built:
            out.append(built)
    return out


def _cashRows(indexed: dict[str, dict[str, Any]], periods: list[str]) -> list[dict[str, Any]]:
    """현금흐름표. 영업으로 번 현금이 설비투자를 덮는지가 첫 질문이다."""
    operating = _pick(indexed, _OCF_KEYS)
    capex = _pick(indexed, _CAPEX_KEYS)
    if operating is None or capex is None:
        return []
    cells: list[str] = []
    for period in periods:
        flow = _numeric(operating.get("values"), period)
        spend = _numeric(capex.get("values"), period)
        # 취득액은 양수로 보고되므로 절대값을 뺀다.
        cells.append("-" if flow is None or spend is None else _formatAmount(flow - abs(spend)))
    built = _row("잉여현금흐름 (영업 - 설비투자)", cells)
    return [built] if built else []


def _marginRows(indexed: dict[str, dict[str, Any]], periods: list[str]) -> list[dict[str, Any]]:
    """매출 대비 비율. 손익계산서에서만 성립한다."""
    sales = _pick(indexed, _SALES_KEYS)
    if sales is None:
        return []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key, label in _RATIO_ROWS:
        if label in seen:
            continue
        built = _row(label, _ratioCells(indexed.get(key), sales, periods))
        if built:
            seen.add(label)
            out.append(built)
    return out


def derivedRows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """같은 표에서 바로 계산되는 비율과 증감률 행을 만든다.

    Args:
        summary: `Company.panel` tool 결과의 summary (periods, timeseries).

    Returns:
        list[dict[str, Any]]: `{label, cells}` 목록. cells 는 기간 순서와 같다.

    Example:
        `rows = derivedRows(summary)`
    """
    periods = [str(p) for p in (summary.get("periods") or [])]
    timeseries = [row for row in (summary.get("timeseries") or []) if isinstance(row, dict)]
    if len(periods) < 2 or not timeseries:
        return []

    indexed = _seriesByKey(timeseries)
    return [
        *_growthRows(indexed, periods),
        *_balanceRows(indexed, periods),
        *_cashRows(indexed, periods),
        *_marginRows(indexed, periods),
    ]


def positionNotes(summary: dict[str, Any]) -> list[str]:
    """조회 기간 안에서 지금 수치가 어디에 있는지, 기저효과가 있는지 적는다.

    판정이 아니라 사실만 적는다. "성장이 좋다" 가 아니라 "이 시점이 기간 최저이고 최고의
    몇 % 수준이라 이 시점 기준 증감률은 부풀려진다" 까지가 이 함수의 몫이다.

    Args:
        summary: `Company.panel` tool 결과의 summary.

    Returns:
        list[str]: 사람이 읽는 한 줄 노트 목록.

    Example:
        `notes = positionNotes(summary)`
    """
    periods = [str(p) for p in (summary.get("periods") or [])]
    timeseries = [row for row in (summary.get("timeseries") or []) if isinstance(row, dict)]
    if len(periods) < _MIN_PERIODS_FOR_POSITION or not timeseries:
        return []

    indexed = _seriesByKey(timeseries)
    notes: list[str] = []
    for key in ("operating_profit", "net_income", "profit", "sales", "revenue"):
        row = indexed.get(key)
        if row is None:
            continue
        values = row.get("values")
        formatted = row.get("formatted") or {}
        pairs = [(period, _numeric(values, period)) for period in periods]
        pairs = [(period, value) for period, value in pairs if value is not None]
        if len(pairs) < _MIN_PERIODS_FOR_POSITION:
            continue
        highPeriod, highValue = max(pairs, key=lambda item: item[1])
        lowPeriod, lowValue = min(pairs, key=lambda item: item[1])
        if highValue <= 0:
            continue
        item = row.get("item")
        latestPeriod, latestValue = pairs[0]
        if latestPeriod == highPeriod:
            notes.append(f"{item}은 {latestPeriod}이 조회 기간 최고치입니다 ({formatted.get(latestPeriod, '-')}).")
        elif latestPeriod == lowPeriod:
            notes.append(f"{item}은 {latestPeriod}이 조회 기간 최저치입니다 ({formatted.get(latestPeriod, '-')}).")

        # 기저효과. 기간 최저가 최고의 일정 비율에 못 미치면 그 시점 기준 증감률은 부풀려진다.
        if lowValue > 0 and lowValue / highValue < _BASE_EFFECT_RATIO and lowPeriod != latestPeriod:
            share = lowValue / highValue * 100
            notes.append(
                f"{item} {lowPeriod} 값 {formatted.get(lowPeriod, '-')}은 기간 최고치의 {share:.0f}% 수준입니다. "
                f"이 시점을 기준으로 잡은 증감률은 기저효과가 큽니다."
            )
        elif lowValue <= 0 < highValue and lowPeriod != latestPeriod:
            notes.append(
                f"{item}은 {lowPeriod}에 적자 또는 0 이하였습니다 ({formatted.get(lowPeriod, '-')}). "
                f"적자 기준 증감률은 배수로 읽지 마십시오."
            )
        if len(notes) >= 4:
            break
    return notes[:4]


def _formatAmount(value: float) -> str:
    """금액을 조원 억원 단위 한 칸으로. 부호를 살려 증감을 그대로 읽게 한다."""
    absolute = abs(value)
    if absolute >= 1e12:
        return f"{value / 1e12:+,.1f}조원"
    if absolute >= 1e8:
        return f"{value / 1e8:+,.0f}억원"
    return f"{value:+,.0f}원"


def profitBridge(summary: dict[str, Any]) -> list[str]:
    """이익 변동을 매출 효과와 마진 효과로 정확히 쪼갠다.

    이익이 늘었을 때 물량이 끌었는지 마진이 끌었는지가 판단을 가른다. 애널리스트가 손으로
    하는 작업이고 부호와 분모를 헷갈리기 쉬운 계산이라 우리가 정확히 해서 건넨다.

    분해는 항등식이라 두 기여분의 합이 실제 변동과 정확히 일치한다.
    영업이익 = 매출 x 영업이익률 이므로
    변동 = (매출 변동 x 직전 영업이익률) + (영업이익률 변동 x 당기 매출) 이다.

    Args:
        summary: `Company.panel` tool 결과의 summary.

    Returns:
        list[str]: 사람이 읽는 한 줄 노트 목록. 계산할 수 없으면 빈 목록이다.

    Example:
        `notes = profitBridge(summary)`
    """
    periods = [str(p) for p in (summary.get("periods") or [])]
    timeseries = [row for row in (summary.get("timeseries") or []) if isinstance(row, dict)]
    if len(periods) < 2 or not timeseries:
        return []

    indexed = _seriesByKey(timeseries)
    sales = _pick(indexed, _SALES_KEYS)
    profit = _pick(indexed, ("operating_profit",))
    if sales is None or profit is None:
        return []

    current, prior = periods[0], periods[1]
    salesNow = _numeric(sales.get("values"), current)
    salesPrev = _numeric(sales.get("values"), prior)
    profitNow = _numeric(profit.get("values"), current)
    profitPrev = _numeric(profit.get("values"), prior)
    if None in (salesNow, salesPrev, profitNow, profitPrev) or not salesNow or not salesPrev:
        return []

    marginNow = profitNow / salesNow
    marginPrev = profitPrev / salesPrev
    volumeEffect = (salesNow - salesPrev) * marginPrev
    marginEffect = (marginNow - marginPrev) * salesNow
    total = profitNow - profitPrev
    if total == 0:
        return []

    driver = "마진" if abs(marginEffect) > abs(volumeEffect) else "매출 물량"
    formatted = profit.get("formatted") or {}
    return [
        f"{profit.get('item')}은 {prior} {formatted.get(prior, '-')}에서 {current} "
        f"{formatted.get(current, '-')}으로 {_formatAmount(total)} 변동했습니다.",
        f"매출 변동 기여 {_formatAmount(volumeEffect)} (매출 {_formatAmount(salesNow - salesPrev)} x "
        f"직전 이익률 {marginPrev * 100:.1f}%).",
        f"이익률 변동 기여 {_formatAmount(marginEffect)} (이익률 {(marginNow - marginPrev) * 100:+.1f}%p x "
        f"당기 매출 {salesNow / 1e12:,.1f}조원).",
        f"변동의 몸통은 {driver}입니다.",
    ]


# 영업·투자·재무 세 흐름의 부호 조합은 기업이 지금 어느 국면인지 말한다. 애널리스트가
# 현금흐름표를 볼 때 가장 먼저 읽는 것이고 기계로 정확히 판별된다. 판정이 아니라
# 통상적인 해석을 적고, 확정 서술은 하지 않는다.
_CASH_PATTERNS: dict[tuple[str, str, str], str] = {
    ("+", "-", "-"): "영업으로 벌어 투자하고 외부 자금을 갚는 형태입니다. 성숙한 현금 창출 구조에서 흔합니다.",
    ("+", "-", "+"): "영업으로 벌면서 외부 자금을 더 당겨 투자하는 형태입니다. 확장 국면에서 흔합니다.",
    ("+", "+", "-"): "영업 현금에 자산 처분을 더해 외부 자금을 갚는 형태입니다. 구조조정 국면에서 흔합니다.",
    (
        "-",
        "+",
        "+",
    ): "영업에서 현금이 빠지는데 자산 처분과 외부 조달로 메우는 형태입니다. 지속 가능성을 따로 확인해야 합니다.",
    (
        "-",
        "-",
        "+",
    ): "영업 현금이 마이너스인 채 외부 자금으로 투자하는 형태입니다. 초기 성장과 자금 소진이 같은 모양이라 구분이 필요합니다.",
    ("-", "+", "-"): "영업 현금이 마이너스라 자산을 팔아 빚을 갚는 형태입니다. 압박 신호로 읽힙니다.",
}


def cashFlowPattern(summary: dict[str, Any]) -> list[str]:
    """영업·투자·재무 현금흐름의 부호 조합과 그 통상적 해석을 적는다.

    Args:
        summary: `Company.panel` tool 결과의 summary. 현금흐름표가 아니면 빈 목록이다.

    Returns:
        list[str]: 사람이 읽는 한 줄 노트 목록.

    Example:
        `notes = cashFlowPattern(summary)`
    """
    periods = [str(p) for p in (summary.get("periods") or [])]
    timeseries = [row for row in (summary.get("timeseries") or []) if isinstance(row, dict)]
    if not periods or not timeseries:
        return []

    indexed = _seriesByKey(timeseries)
    flows = [_pick(indexed, keys) for keys in (_OCF_KEYS, _ICF_KEYS, _FCF_KEYS)]
    if any(flow is None for flow in flows):
        return []

    latest = periods[0]
    values = [_numeric(flow.get("values"), latest) for flow in flows if flow is not None]
    if len(values) != 3 or any(value is None for value in values):
        return []

    signs = tuple("+" if value > 0 else "-" for value in values if value is not None)
    labels = [str(flow.get("item")) for flow in flows if flow is not None]
    formatted = [(flow.get("formatted") or {}).get(latest, "-") for flow in flows if flow is not None]
    notes = [f"{latest} 기준 {labels[0]} {formatted[0]}, {labels[1]} {formatted[1]}, {labels[2]} {formatted[2]}."]
    reading = _CASH_PATTERNS.get(signs)  # type: ignore[arg-type]
    if reading:
        notes.append(reading)
    return notes


def observedRangeAnchors(summary: dict[str, Any]) -> list[str]:
    """관측된 마진 수준을 당기 매출에 대입해 판단이 바뀌는 지점을 숫자로 만든다.

    답변에서 가장 자주 빠지는 것이 "이 판단이 틀리려면 무엇이 일어나야 하나" 다. 캡슐이
    요구하는데도 안 나오는 이유는 반사실 추론이 어렵기 때문이다. 그런데 기준을 지어내지
    않고 **이 회사가 실제로 겪었던 마진 수준**을 쓰면 그 자리에서 산술이 된다.

    가정을 지어내지 않는 것이 핵심이다. 임의의 시나리오가 아니라 조회 기간에 실제로
    관측된 최저와 중앙값만 쓴다. 다른 조건이 같다는 전제도 문장에 명시한다.

    Args:
        summary: `Company.panel` tool 결과의 summary.

    Returns:
        list[str]: 사람이 읽는 한 줄 노트 목록. 손익계산서가 아니면 빈 목록이다.

    Example:
        `notes = observedRangeAnchors(summary)`
    """
    periods = [str(p) for p in (summary.get("periods") or [])]
    timeseries = [row for row in (summary.get("timeseries") or []) if isinstance(row, dict)]
    if len(periods) < _MIN_PERIODS_FOR_POSITION or not timeseries:
        return []

    indexed = _seriesByKey(timeseries)
    sales = _pick(indexed, _SALES_KEYS)
    profit = _pick(indexed, ("operating_profit", "operating_income"))
    if sales is None or profit is None:
        return []

    latest = periods[0]
    salesNow = _numeric(sales.get("values"), latest)
    profitNow = _numeric(profit.get("values"), latest)
    if not salesNow or profitNow is None:
        return []

    margins: list[tuple[str, float]] = []
    for period in periods:
        revenue = _numeric(sales.get("values"), period)
        income = _numeric(profit.get("values"), period)
        if revenue and income is not None:
            margins.append((period, income / revenue))
    if len(margins) < _MIN_PERIODS_FOR_POSITION:
        return []

    ordered = sorted(margins, key=lambda item: item[1])
    lowPeriod, lowMargin = ordered[0]
    medianPeriod, medianMargin = ordered[len(ordered) // 2]
    marginNow = profitNow / salesNow
    notes: list[str] = []
    if lowMargin < marginNow:
        notes.append(
            f"영업이익률이 조회 기간 최저인 {lowPeriod} 수준({lowMargin * 100:.1f}%)으로 돌아가면 "
            f"당기 매출 기준 영업이익은 {_formatAmount(salesNow * lowMargin).lstrip('+')}입니다. "
            f"다른 조건이 같다고 둔 산술이며 전망이 아닙니다."
        )
    if abs(medianMargin - marginNow) > 0.005 and medianPeriod not in {lowPeriod, latest}:
        notes.append(
            f"기간 중앙값 마진({medianMargin * 100:.1f}%, {medianPeriod})이면 "
            f"{_formatAmount(salesNow * medianMargin).lstrip('+')}입니다."
        )
    return notes


def cashFlowAnchors(summary: dict[str, Any]) -> list[str]:
    """현금흐름이 어디까지 내려가면 설비투자를 못 덮는지 임계값으로 적는다.

    실측(2026-08-06): 현금 질문 답변이 "사이클이 꺾이면 잉여현금흐름은 다시 음수가 될 수
    있다" 에서 멈췄다. 옳은 말이지만 임계값이 없으면 지켜볼 수가 없다. 손익에는 관측 마진
    앵커를 줬는데 현금흐름에는 같은 것이 없어서 생긴 비대칭이다.

    여기서도 가정을 지어내지 않는다. 당기 설비투자와 조회 기간에 실제로 겪은 최저
    영업현금흐름만 쓴다.

    Args:
        summary: `Company.panel` tool 결과의 summary. 현금흐름표가 아니면 빈 목록이다.

    Returns:
        list[str]: 사람이 읽는 한 줄 노트 목록.

    Example:
        `notes = cashFlowAnchors(summary)`
    """
    periods = [str(p) for p in (summary.get("periods") or [])]
    timeseries = [row for row in (summary.get("timeseries") or []) if isinstance(row, dict)]
    if len(periods) < 2 or not timeseries:
        return []

    indexed = _seriesByKey(timeseries)
    operating = _pick(indexed, _OCF_KEYS)
    capex = _pick(indexed, _CAPEX_KEYS)
    if operating is None or capex is None:
        return []

    latest = periods[0]
    spendNow = _numeric(capex.get("values"), latest)
    flowNow = _numeric(operating.get("values"), latest)
    if spendNow is None or flowNow is None:
        return []
    spendNow = abs(spendNow)

    notes: list[str] = []
    if flowNow > spendNow:
        notes.append(
            f"영업활동현금흐름이 당기 설비투자 {_formatAmount(spendNow).lstrip('+')} 아래로 내려가면 "
            f"잉여현금흐름이 음수가 됩니다. 지금은 {_formatAmount(flowNow).lstrip('+')}이라 "
            f"{_formatAmount(flowNow - spendNow)} 여유가 있습니다."
        )

    history = [(period, _numeric(operating.get("values"), period)) for period in periods]
    history = [(period, value) for period, value in history if value is not None]
    if len(history) >= _MIN_PERIODS_FOR_POSITION:
        lowPeriod, lowValue = min(history, key=lambda item: item[1])
        if lowPeriod != latest:
            notes.append(
                f"영업활동현금흐름이 조회 기간 최저인 {lowPeriod} 수준"
                f"({_formatAmount(lowValue).lstrip('+')})으로 돌아가면 당기 설비투자 기준 "
                f"잉여현금흐름은 {_formatAmount(lowValue - spendNow)}입니다. "
                f"다른 조건이 같다고 둔 산술이며 전망이 아닙니다."
            )
    return notes


# (표시 이름, 백분위 키, 분포 키, 높을수록 좋은가).
# 방향을 표에 박아 둔다. 부채비율은 낮을수록 안전한데 "상위 몇 %" 로 적으면 정반대로 읽힌다.
_SECTOR_AXES: tuple[tuple[str, str, str, bool], ...] = (
    ("영업이익률", "myOpmPercentile", "opmDistribution", True),
    ("ROE", "myRoePercentile", "roeDistribution", True),
    ("매출 성장률", "myCagrPercentile", "cagrDistribution", True),
    ("부채비율", "myDebtRatioPercentile", "debtRatioDistribution", False),
    ("유동비율", "myCurrentRatioPercentile", "currentRatioDistribution", True),
)


def sectorPositionLines(position: dict[str, Any] | None) -> list[str]:
    """수치를 판단으로 바꾸는 업종 내 위치를 문장으로 만든다.

    "영업이익률 13.1%" 는 그 자체로 좋고 나쁨을 말하지 않는다. 같은 업종 회사들이 어디에
    있는지를 알아야 판단이 된다. 분포와 백분위는 오래전부터 계산되고 있었지만 답변 표면에
    오지 않아 한 번도 쓰이지 않았다.

    표본이 작으면 백분위가 흔들린다. 몇 개 회사로 잰 값인지 함께 적어 과신을 막는다.

    Args:
        position: `getSectorPosition` 결과. 없으면 빈 목록이다.

    Returns:
        list[str]: 사람이 읽는 한 줄 노트 목록.

    Example:
        `lines = sectorPositionLines(position)`
    """
    if not isinstance(position, dict) or not position.get("peerCount"):
        return []
    industry = str(position.get("industryName") or position.get("industryId") or "동종 업종")
    peerCount = position.get("peerCount")
    lines: list[str] = []
    for label, percentileKey, distributionKey, higherIsBetter in _SECTOR_AXES:
        percentile = position.get(percentileKey)
        distribution = position.get(distributionKey)
        if not isinstance(percentile, (int, float)) or not isinstance(distribution, dict):
            continue
        median = distribution.get("median")
        sampled = distribution.get("n") or peerCount
        if higherIsBetter:
            parts = [f"{label} 업종 상위 {100 - float(percentile):.0f}%"]
            boundary, boundaryLabel = distribution.get("p90"), "상위 10% 경계"
        else:
            # 낮은 쪽에 있을수록 안전하다는 뜻을 문장 안에 넣는다. 숫자만 주면 뒤집혀 읽힌다.
            parts = [f"{label} 업종 하위 {float(percentile):.0f}% (낮을수록 안전)"]
            boundary, boundaryLabel = distribution.get("p10"), "가장 낮은 10% 경계"
        if isinstance(median, (int, float)):
            parts.append(f"중앙값 {float(median):.1f}%")
        if isinstance(boundary, (int, float)):
            parts.append(f"{boundaryLabel} {float(boundary):.1f}%")
        lines.append(f"- {', '.join(parts)} ({industry} {sampled}사 기준).")
    return lines


def contextMarkdown(
    dcrBadge: dict[str, Any] | None,
    industryBadge: dict[str, Any] | None,
    sectorPosition: dict[str, Any] | None = None,
) -> str:
    """이미 계산돼 붙어 있는 신용 등급과 산업 위치를 답변 표면으로 끌어올린다.

    두 뱃지는 오래전부터 tool 결과에 실려 있었지만 payload 안에만 있어서 실제 답변에는
    한 번도 쓰이지 않았다. 모델이 읽고 재사용하는 것은 markdown 본문이다. 계산이 이미
    끝난 것을 옮겨 적기만 하므로 비용이 없고, 수치 하나에 판단 기준이 생긴다.

    Args:
        dcrBadge: 신용 스코어카드 요약. 없으면 건너뛴다.
        industryBadge: 산업 분류와 국면과 동종 후보. 없으면 건너뛴다.

    Returns:
        str: 붙일 것이 없으면 빈 문자열이다.

    Example:
        `block = contextMarkdown(data.get("dcrBadge"), data.get("industryBadge"))`
    """
    lines: list[str] = []
    if isinstance(dcrBadge, dict) and dcrBadge.get("grade"):
        parts = [f"신용 {dcrBadge.get('grade')}"]
        if dcrBadge.get("outlook"):
            parts.append(f"전망 {dcrBadge['outlook']}")
        pd = dcrBadge.get("pdEstimate")
        if isinstance(pd, (int, float)):
            parts.append(f"1년 부도확률 {float(pd):.2f}%")
        if dcrBadge.get("investmentGrade") is not None:
            parts.append("투자등급" if dcrBadge["investmentGrade"] else "투기등급")
        lines.append(f"- {', '.join(parts)}.")
    if isinstance(industryBadge, dict) and industryBadge.get("industryName"):
        parts = [str(industryBadge["industryName"])]
        if industryBadge.get("stageName"):
            parts.append(str(industryBadge["stageName"]))
        if industryBadge.get("phase") and industryBadge["phase"] != "unknown":
            parts.append(f"국면 {industryBadge['phase']}")
        peers = [
            f"{peer.get('corpName')}({peer.get('stockCode')})"
            for peer in (industryBadge.get("peers") or [])
            if isinstance(peer, dict) and peer.get("corpName")
        ][:3]
        line = f"- 산업 {', '.join(parts)}."
        if peers:
            line += f" 같은 산업 비교 후보: {', '.join(peers)}."
        lines.append(line)
    lines.extend(sectorPositionLines(sectorPosition))
    if not lines:
        return ""
    return "## 회사 위치\n" + "\n".join(lines) + "\n"


def insightMarkdown(summary: dict[str, Any]) -> str:
    """파생 지표 표와 위치 노트를 markdown 한 덩어리로 만든다.

    Args:
        summary: `Company.panel` tool 결과의 summary.

    Returns:
        str: 붙일 것이 없으면 빈 문자열이다.

    Example:
        `block = insightMarkdown(summary)`
    """
    periods = [str(p) for p in (summary.get("periods") or [])][:12]
    rows = derivedRows(summary)
    notes = positionNotes(summary)
    bridge = profitBridge(summary)
    cash = cashFlowPattern(summary)
    anchors = observedRangeAnchors(summary) + cashFlowAnchors(summary)
    if not rows and not notes and not bridge and not cash and not anchors:
        return ""

    lines: list[str] = []
    if rows and periods:
        lines.append("## 파생 지표 (위 표에서 계산)")
        lines.append("| 지표 | " + " | ".join(periods) + " |")
        lines.append("|---|" + "|".join(["---:"] * len(periods)) + "|")
        for row in rows:
            cells = list(row["cells"])[: len(periods)]
            cells += ["-"] * (len(periods) - len(cells))
            lines.append(f"| {row['label']} | " + " | ".join(cells) + " |")
        lines.append("")
    if bridge:
        lines.append("## 이익 변동 요인 (직전 기간 대비)")
        lines.extend(f"- {note}" for note in bridge)
        lines.append("")
    if cash:
        lines.append("## 현금흐름 방향")
        lines.extend(f"- {note}" for note in cash)
        lines.append("")
    if notes:
        lines.append("## 기간 내 위치")
        lines.extend(f"- {note}" for note in notes)
        lines.append("")
    if anchors:
        lines.append("## 관측된 범위 기준 산술")
        lines.extend(f"- {note}" for note in anchors)
        lines.append("")
    return "\n".join(lines)
