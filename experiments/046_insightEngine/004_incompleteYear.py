"""
실험 ID: 004
실험명: 불완전 연도 보정 — YoY vs 완전연도 비교

목적:
- 최신 연도가 4분기 미만일 때 Performance 성장률이 왜곡되는 문제 해결
- 보정 전략 비교: (A) 불완전 연도 제외 (B) 분기 기반 YoY (C) TTM 비교
- 삼성전자 실제 데이터로 각 전략의 결과 차이 검증

가설:
1. 불완전 연도를 제외하고 마지막 완전 연도 기준 YoY를 계산하면 성장률이 현실적으로 나온다
2. 분기 기반 YoY(같은 분기 전년 동기 비교)도 유효하지만, 계절성에 취약할 수 있다
3. TTM(최근 4분기 합) 대비 전년 TTM 비교가 가장 안정적이다

방법:
1. 삼성전자 분기/연간 시계열에서 불완전 연도 감지
2. 세 가지 보정 전략 구현 + 비교
3. 5종목에서 보정 전/후 Performance 등급 비교

결과 (실험 후 작성):
- 전략별 매출 성장률 비교 (불완전 연도 * 표시)
  삼성전자:     현재 -20.3% → A +16.2% / B +1.2% / C +25.3% *
  현대자동차:    현재 -20.4% → A +7.7% / B -6.1% / C -7.1% *
  KB금융:      현재 N/A → A N/A / B N/A / C N/A *
  카카오:       현재 -24.0% → A +4.2% / B -5.9% / C -41.1% *
  LG에너지솔루션: 현재 -24.1% → A -24.1% / B -21.5% / C -18.3% *
- 전략 C의 카카오 -41.1%는 이상치 (TTM 범위 문제)

결론:
- 가설 1 채택: 전략 A(불완전 연도 제외)가 가장 안정적이고 직관적
- 가설 2 부분 채택: 분기 YoY(B)도 유효하나 단일 분기라 변동성 큼
- 가설 3 부분 기각: TTM(C)은 카카오에서 이상치 발생 — 분기 데이터 품질에 민감
- 권장: 전략 A를 기본으로, 전략 C는 보조 지표로 참고

실험일: 2026-03-09
"""

import sys
sys.path.insert(0, "src")

from typing import Optional

import dartlab
dartlab.verbose = False

from dartlab.engines.financeEngine.pivot import buildTimeseries, buildAnnual
from dartlab.engines.financeEngine.extract import getAnnualValues


STOCK = "005930"


def detectIncompleteYear(qPeriods: list[str]) -> tuple[str, int]:
    """최신 연도의 분기 수 반환."""
    lastPeriod = qPeriods[-1]
    lastYear = lastPeriod.split("_")[0]
    qCount = sum(1 for p in qPeriods if p.startswith(lastYear))
    return lastYear, qCount


def strategyA_excludeIncomplete(
    annualSeries: dict, years: list[str], qPeriods: list[str]
) -> tuple[Optional[float], Optional[float], str]:
    """전략 A: 불완전 연도 제외, 마지막 완전 연도 기준 YoY."""
    lastYear, qCount = detectIncompleteYear(qPeriods)

    revVals = getAnnualValues(annualSeries, "IS", "revenue")
    opVals = getAnnualValues(annualSeries, "IS", "operating_income")

    if qCount < 4:
        useYears = years[:-1]
        useRev = revVals[:-1]
        useOp = opVals[:-1]
        label = f"불완전연도({lastYear}, {qCount}Q) 제외 → {useYears[-1]} 기준"
    else:
        useYears = years
        useRev = revVals
        useOp = opVals
        label = f"완전연도 — {useYears[-1]} 기준"

    revGrowth = _yoy(useRev)
    opGrowth = _yoy(useOp)
    return revGrowth, opGrowth, label


def strategyB_quarterYoY(
    qSeries: dict, qPeriods: list[str]
) -> tuple[Optional[float], Optional[float], str]:
    """전략 B: 최신 분기 vs 전년 동기 비교."""
    revVals = qSeries.get("IS", {}).get("revenue", [])
    opVals = qSeries.get("IS", {}).get("operating_income", [])

    if len(qPeriods) < 5:
        return None, None, "분기 데이터 부족"

    lastQ = qPeriods[-1]
    lastYear, lastQNum = lastQ.split("_")
    targetQ = f"{int(lastYear) - 1}_{lastQNum}"

    if targetQ not in qPeriods:
        return None, None, f"전년 동기({targetQ}) 없음"

    currIdx = qPeriods.index(lastQ)
    prevIdx = qPeriods.index(targetQ)

    revCurr = revVals[currIdx] if currIdx < len(revVals) else None
    revPrev = revVals[prevIdx] if prevIdx < len(revVals) else None
    opCurr = opVals[currIdx] if currIdx < len(opVals) else None
    opPrev = opVals[prevIdx] if prevIdx < len(opVals) else None

    revGrowth = _growth(revCurr, revPrev)
    opGrowth = _growth(opCurr, opPrev)
    label = f"분기 YoY: {lastQ} vs {targetQ}"
    return revGrowth, opGrowth, label


def strategyC_ttmComparison(
    qSeries: dict, qPeriods: list[str]
) -> tuple[Optional[float], Optional[float], str]:
    """전략 C: TTM(최근 4분기) vs 전년 TTM 비교."""
    revVals = qSeries.get("IS", {}).get("revenue", [])
    opVals = qSeries.get("IS", {}).get("operating_income", [])

    if len(revVals) < 8:
        return None, None, "TTM 계산에 8분기 이상 필요"

    revTTM = _ttmSum(revVals, -4)
    revPrevTTM = _ttmSum(revVals, -8, -4)
    opTTM = _ttmSum(opVals, -4)
    opPrevTTM = _ttmSum(opVals, -8, -4)

    revGrowth = _growth(revTTM, revPrevTTM)
    opGrowth = _growth(opTTM, opPrevTTM)

    lastQ = qPeriods[-1]
    prevQ = qPeriods[-5] if len(qPeriods) >= 5 else "?"
    label = f"TTM: ({qPeriods[-4]}~{lastQ}) vs ({prevQ}~{qPeriods[-5] if len(qPeriods) >= 5 else '?'})"
    return revGrowth, opGrowth, label


def _yoy(vals: list[Optional[float]]) -> Optional[float]:
    valid = [(i, v) for i, v in enumerate(vals) if v is not None]
    if len(valid) < 2:
        return None
    _, prev = valid[-2]
    _, curr = valid[-1]
    if prev and prev != 0:
        return ((curr - prev) / abs(prev)) * 100
    return None


def _growth(curr: Optional[float], prev: Optional[float]) -> Optional[float]:
    if curr is not None and prev is not None and prev != 0:
        return ((curr - prev) / abs(prev)) * 100
    return None


def _ttmSum(vals: list[Optional[float]], start: int, end: int = None) -> Optional[float]:
    sliced = vals[start:end] if end else vals[start:]
    nonNull = [v for v in sliced if v is not None]
    if len(nonNull) == 4:
        return sum(nonNull)
    return None


def runComparison(stockCode: str, stockName: str):
    print(f"\n{'=' * 70}")
    print(f"  {stockName} ({stockCode})")
    print(f"{'=' * 70}")

    qResult = buildTimeseries(stockCode)
    aResult = buildAnnual(stockCode)
    if qResult is None or aResult is None:
        print("  데이터 없음")
        return {}

    qSeries, qPeriods = qResult
    aSeries, aYears = aResult

    lastYear, qCount = detectIncompleteYear(qPeriods)
    print(f"  최신 연도: {lastYear} ({qCount}분기)")
    print(f"  연간 시계열: {aYears}")

    print(f"\n  {'전략':<35} {'매출 성장률':>12} {'영업이익 성장률':>15}")
    print(f"  {'-' * 65}")

    origRevGrowth = _yoy(getAnnualValues(aSeries, "IS", "revenue"))
    origOpGrowth = _yoy(getAnnualValues(aSeries, "IS", "operating_income"))
    print(f"  {'[현재] 단순 연간 YoY':<35} {_fmtPct(origRevGrowth):>12} {_fmtPct(origOpGrowth):>15}")

    revA, opA, labelA = strategyA_excludeIncomplete(aSeries, aYears, qPeriods)
    print(f"  [A] {labelA:<30} {_fmtPct(revA):>12} {_fmtPct(opA):>15}")

    revB, opB, labelB = strategyB_quarterYoY(qSeries, qPeriods)
    print(f"  [B] {labelB:<30} {_fmtPct(revB):>12} {_fmtPct(opB):>15}")

    revC, opC, labelC = strategyC_ttmComparison(qSeries, qPeriods)
    print(f"  [C] {labelC:<30} {_fmtPct(revC):>12} {_fmtPct(opC):>15}")

    return {
        "original": (origRevGrowth, origOpGrowth),
        "A": (revA, opA),
        "B": (revB, opB),
        "C": (revC, opC),
        "incomplete": qCount < 4,
    }


def _fmtPct(val: Optional[float]) -> str:
    if val is None:
        return "N/A"
    return f"{val:+.1f}%"


STOCKS = {
    "005930": "삼성전자",
    "005380": "현대자동차",
    "105560": "KB금융",
    "035720": "카카오",
    "373220": "LG에너지솔루션",
}


if __name__ == "__main__":
    allResults = {}
    for code, name in STOCKS.items():
        allResults[code] = runComparison(code, name)

    print(f"\n\n{'=' * 70}")
    print("  전략별 매출 성장률 비교 매트릭스")
    print(f"{'=' * 70}")
    print(f"  {'종목':<15} {'현재':>10} {'A(완전연도)':>12} {'B(분기YoY)':>12} {'C(TTM)':>10}")
    print(f"  {'-' * 60}")
    for code, name in STOCKS.items():
        r = allResults.get(code, {})
        if not r:
            continue
        orig = _fmtPct(r["original"][0])
        a = _fmtPct(r["A"][0])
        b = _fmtPct(r["B"][0])
        c = _fmtPct(r["C"][0])
        marker = " *" if r.get("incomplete") else ""
        print(f"  {name:<15} {orig:>10} {a:>12} {b:>12} {c:>10}{marker}")

    print(f"\n  * = 불완전 연도 감지됨")
    print(f"\n  권장: 전략 A (불완전 연도 제외) — 단순하고 안정적")
    print(f"        전략 C (TTM) — 분기 데이터 활용, 계절성 보정")
