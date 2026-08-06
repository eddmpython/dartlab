"""손에 있는 시계열만으로 계산되는 파생 지표.

원시 수치 표만 주면 마진과 증감률과 기저효과 판별을 모델이 매번 손으로 해야 하고,
그 계산을 잘하는 모델과 못하는 모델 사이에서 답변 품질이 갈린다. 그 차이를 모델에
맡기지 않고 표에 실어 보낸다. 추가 조회가 없으므로 지연이 늘지 않는다.
"""

from __future__ import annotations

from typing import Any

from .values import (
    _BS_RATIOS,
    _CAPEX_KEYS,
    _FCF_KEYS,
    _GROWTH_ROWS,
    _ICF_KEYS,
    _OCF_KEYS,
    _RATIO_ROWS,
    _SALES_KEYS,
    _formatAmount,
    _formatPercent,
    _numeric,
    _pick,
    _ratioCells,
    _row,
    _seriesByKey,
    _withDerivedEquity,
)

# 기저효과 판정 임계. 기간 최고치의 이 비율보다 낮은 시작점은 증감률을 부풀린다.
_BASE_EFFECT_RATIO = 0.35
_MIN_PERIODS_FOR_POSITION = 3


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
