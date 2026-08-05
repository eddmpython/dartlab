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
    ("operating_profit", "영업이익률"),
    ("net_income", "순이익률"),
    ("profit", "순이익률"),
)
# 증감률을 보여 줄 대표 항목. 전 행을 다 보이면 표가 읽히지 않는다.
_GROWTH_ROWS = ("sales", "revenue", "operating_profit", "net_income", "profit", "gross_profit")
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


def _formatPercent(value: float | None, *, signed: bool = False) -> str:
    """비율을 읽기 좋은 한 칸으로. 없으면 하이픈이다.

    증감률은 부호를 붙인 퍼센트다. 퍼센트끼리의 차이가 아니므로 퍼센트포인트가 아니다.
    """
    if value is None:
        return "-"
    return f"{value:+.1f}%" if signed else f"{value:.1f}%"


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
    sales = _pick(indexed, _SALES_KEYS)
    out: list[dict[str, Any]] = []

    # 증감률. periods 는 최신이 앞이므로 다음 원소가 직전 기간이다.
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
        if any(cell != "-" for cell in cells):
            seen.add(str(row.get("item")))
            out.append({"label": f"{row.get('item')} 증감률", "cells": cells})

    # 매출 대비 비율. 손익계산서에서만 성립한다.
    if sales is not None:
        salesValues = sales.get("values")
        seenRatio: set[str] = set()
        for key, label in _RATIO_ROWS:
            row = indexed.get(key)
            if row is None or label in seenRatio:
                continue
            values = row.get("values")
            cells = []
            for period in periods:
                numerator = _numeric(values, period)
                denominator = _numeric(salesValues, period)
                if numerator is None or not denominator:
                    cells.append("-")
                else:
                    cells.append(_formatPercent(numerator / denominator * 100))
            if any(cell != "-" for cell in cells):
                seenRatio.add(label)
                out.append({"label": label, "cells": cells})
    return out


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
    if not rows and not notes and not bridge:
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
    if notes:
        lines.append("## 기간 내 위치")
        lines.extend(f"- {note}" for note in notes)
        lines.append("")
    return "\n".join(lines)
