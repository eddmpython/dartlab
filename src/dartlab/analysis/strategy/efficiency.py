"""2-4 효율성 분석 -- 회전율, CCC."""

from __future__ import annotations

from dartlab.analysis.strategy._helpers import buildTimeline, getRatioSeries


def calcTurnoverTrend(company) -> dict | None:
    """총자산/매출채권/재고 회전율 시계열."""
    result = getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    totalAsset = buildTimeline(data, "totalAssetTurnover", years)
    receivables = buildTimeline(data, "receivablesTurnover", years)
    inventory = buildTimeline(data, "inventoryTurnover", years)

    if not totalAsset and not receivables and not inventory:
        return None

    return {
        "totalAssetTurnover": totalAsset,
        "receivablesTurnover": receivables,
        "inventoryTurnover": inventory,
    }


def calcCccTrend(company) -> dict | None:
    """CCC 구성요소 시계열: DSO + DIO - DPO = CCC."""
    result = getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    ccc = buildTimeline(data, "ccc", years)
    dso = buildTimeline(data, "dso", years)
    dio = buildTimeline(data, "dio", years)
    dpo = buildTimeline(data, "dpo", years)

    if not ccc:
        return None

    return {"ccc": ccc, "dso": dso, "dio": dio, "dpo": dpo}


def calcEfficiencyFlags(company) -> list[str]:
    """효율성 경고/기회 플래그."""
    flags: list[str] = []
    result = getRatioSeries(company)
    if result is None:
        return flags

    data, _years = result

    # 총자산회전율 하락 추세
    tat = data.get("RATIO", {}).get("totalAssetTurnover", [])
    recent = [v for v in tat[-3:] if v is not None]
    if len(recent) >= 3 and all(recent[i] > recent[i + 1] for i in range(len(recent) - 1)):
        flags.append(f"총자산회전율 3기 연속 하락 ({recent[-1]:.2f}회)")

    # CCC 악화
    ccc = data.get("RATIO", {}).get("ccc", [])
    recentCcc = [v for v in ccc[-2:] if v is not None]
    if len(recentCcc) >= 2:
        diff = recentCcc[-1] - recentCcc[0]
        if diff > 20:
            flags.append(f"CCC {diff:.0f}일 악화 ({recentCcc[-1]:.0f}일)")
        if recentCcc[-1] < 0:
            flags.append(f"CCC {recentCcc[-1]:.0f}일 -- 운전자본 유리 구조")

    return flags
