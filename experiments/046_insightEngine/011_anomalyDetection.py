"""
실험 ID: 011
실험명: 이상치 탐지 — Earnings Quality + 구조 급변 감지

목적:
- 재무 데이터에서 투자자가 주의해야 할 이상 신호를 자동 탐지
- 010의 insight 등급과 별개로, 구체적 이상 패턴을 플래그로 출력
- 패키지 흡수 시 anomalies 필드로 활용

가설:
1. 영업이익↑ but 영업CF↓ 패턴은 20종목 중 2건 이상 탐지된다 (Earnings Quality 이슈)
2. 매출채권/재고 급증 패턴은 제조업에서 유의미한 신호이다
3. 전년 대비 50% 이상 급변하는 BS 항목이 존재하는 종목이 5개 이상이다
4. 금융업은 고유한 이상치 패턴을 보인다 (부채비율 급변 등)

방법:
1. 6개 이상치 탐지 룰 설계 및 구현
2. 20종목 일괄 적용
3. 탐지 빈도, 업종 패턴 분석
4. 오탐(false positive) 수동 검토

결과 (실험 후 작성):
- 26건 탐지 (13/20종목), danger 5건, warning 12건, info 9건
- 카테고리별: marginDivergence 10, balanceSheetShift 7, earningsQuality 6, cashBurn 1, financialSector 1, workingCapital 1
- Earnings Quality (이익↑ but CF↓): LG화학, LG에너지솔루션, LG, 셀트리온, 현대자동차 — 5건
- 금융업 오탐 수정: KB금융/미래에셋증권의 영업CF 적자는 금융업 특성 → earningsQuality/cashBurn 제외로 해소
- 현대자동차: 순이익 흑자(91,807억) but 영업CF 적자(-39,009억) — 자동차 할부금융 특성
- SK 그룹: 단기차입금 +512%, 영업외손익 급변 — 지주회사 구조 반영
- LG 그룹: 4건 최다 (이익품질 + 재고과잉 + 차입변동 + 마진개선)
- 이상 없음 7종목: 삼성전자, POSCO홀딩스, NAVER, KB금융, 신한지주, 미래에셋증권, 삼성물산

결론:
- 가설 1 채택: "이익↑ but CF↓" 패턴 5건 탐지 (현대차, LG화학, LG에너지, LG, 셀트리온)
- 가설 2 부분기각: 매출채권 급증은 1건만 탐지 (LG 재고), 대부분 종목 데이터 불충분
- 가설 3 채택: BS 급변 7건 (단기차입금/장기차입금 급변이 주요 패턴)
- 가설 4 채택: 금융업 earningsQuality/cashBurn 제외 필요 확인, 부채비율 급변 탐지 유효
- 6개 탐지 룰 중 marginDivergence가 가장 빈번 (10건) — 영업외손익 급변이 흔함
- workingCapital 룰은 매출 데이터 없는 종목에서 작동 불가 → 개선 여지

실험일: 2026-03-09
"""

import sys
sys.path.insert(0, "src")

from dataclasses import dataclass
from typing import Optional
from collections import Counter

import dartlab
dartlab.verbose = False

from dartlab.engines.financeEngine.pivot import buildTimeseries, buildAnnual
from dartlab.engines.financeEngine.ratios import calcRatios
from dartlab.engines.financeEngine.extract import getLatest, getAnnualValues


@dataclass
class Anomaly:
    severity: str
    category: str
    text: str
    value: Optional[float] = None


def _yoyChange(vals: list[Optional[float]]) -> Optional[float]:
    valid = [(i, v) for i, v in enumerate(vals) if v is not None]
    if len(valid) < 2:
        return None
    _, prev = valid[-2]
    _, curr = valid[-1]
    if prev and prev != 0:
        return ((curr - prev) / abs(prev)) * 100
    return None


def detectEarningsQuality(aSeries: dict, isFinancial: bool = False) -> list[Anomaly]:
    anomalies = []

    if isFinancial:
        return anomalies

    opIncomeVals = getAnnualValues(aSeries, "IS", "operating_income")
    opCfVals = getAnnualValues(aSeries, "CF", "operating_cashflow")

    opGrowth = _yoyChange(opIncomeVals)
    cfGrowth = _yoyChange(opCfVals)

    if opGrowth is not None and cfGrowth is not None:
        if opGrowth > 10 and cfGrowth < -10:
            anomalies.append(Anomaly(
                "danger", "earningsQuality",
                f"이익↑(+{opGrowth:.0f}%) but 영업CF↓({cfGrowth:.0f}%) — 이익 품질 의심",
                opGrowth - cfGrowth,
            ))
        elif opGrowth > 0 and cfGrowth < 0 and abs(cfGrowth) > 20:
            anomalies.append(Anomaly(
                "warning", "earningsQuality",
                f"이익 증가(+{opGrowth:.0f}%) 대비 영업CF 감소({cfGrowth:.0f}%)",
                opGrowth - cfGrowth,
            ))

    netIncomeVals = getAnnualValues(aSeries, "IS", "net_income")
    niGrowth = _yoyChange(netIncomeVals)

    if niGrowth is not None and cfGrowth is not None:
        latestNi = None
        latestCf = None
        for v in reversed(netIncomeVals):
            if v is not None:
                latestNi = v
                break
        for v in reversed(opCfVals):
            if v is not None:
                latestCf = v
                break

        if latestNi and latestCf and latestNi > 0 and latestCf < 0:
            anomalies.append(Anomaly(
                "danger", "earningsQuality",
                f"순이익 흑자({latestNi/1e8:,.0f}억) but 영업CF 적자({latestCf/1e8:,.0f}억)",
            ))

    return anomalies


def detectWorkingCapitalAnomaly(aSeries: dict) -> list[Anomaly]:
    anomalies = []

    arVals = getAnnualValues(aSeries, "BS", "trade_receivables")
    if not arVals:
        arVals = getAnnualValues(aSeries, "BS", "trade_and_other_receivables")
    invVals = getAnnualValues(aSeries, "BS", "inventories")
    revVals = getAnnualValues(aSeries, "IS", "revenue")

    arGrowth = _yoyChange(arVals)
    invGrowth = _yoyChange(invVals)
    revGrowth = _yoyChange(revVals)

    if arGrowth is not None and revGrowth is not None:
        if arGrowth > revGrowth + 20 and arGrowth > 30:
            anomalies.append(Anomaly(
                "warning", "workingCapital",
                f"매출채권 급증(+{arGrowth:.0f}%) > 매출 증가(+{revGrowth:.0f}%) — 수금 지연 가능",
                arGrowth - revGrowth,
            ))

    if invGrowth is not None and revGrowth is not None:
        if invGrowth > revGrowth + 30 and invGrowth > 40:
            anomalies.append(Anomaly(
                "warning", "workingCapital",
                f"재고자산 급증(+{invGrowth:.0f}%) > 매출 증가(+{revGrowth:.0f}%) — 재고 과잉 가능",
                invGrowth - revGrowth,
            ))
        elif invGrowth is not None and invGrowth > 50:
            anomalies.append(Anomaly(
                "info", "workingCapital",
                f"재고자산 대폭 증가(+{invGrowth:.0f}%)",
                invGrowth,
            ))

    return anomalies


def detectBalanceSheetShift(aSeries: dict) -> list[Anomaly]:
    anomalies = []

    checkItems = [
        ("BS", "total_liabilities", "부채총계"),
        ("BS", "short_term_borrowings", "단기차입금"),
        ("BS", "long_term_borrowings", "장기차입금"),
        ("BS", "bonds", "사채"),
        ("BS", "total_equity", "자본총계"),
    ]

    for sjDiv, snakeId, label in checkItems:
        vals = getAnnualValues(aSeries, sjDiv, snakeId)
        change = _yoyChange(vals)
        if change is not None and abs(change) > 50:
            direction = "급증" if change > 0 else "급감"
            severity = "warning" if abs(change) > 100 else "info"
            anomalies.append(Anomaly(
                severity, "balanceSheetShift",
                f"{label} {direction} ({change:+.0f}%)",
                change,
            ))

    equityVals = getAnnualValues(aSeries, "BS", "total_equity")
    valid = [v for v in equityVals if v is not None]
    if valid and valid[-1] is not None and valid[-1] < 0:
        anomalies.append(Anomaly(
            "danger", "balanceSheetShift",
            f"자본잠식 ({valid[-1]/1e8:,.0f}억)",
            valid[-1],
        ))

    return anomalies


def detectCashBurn(aSeries: dict, isFinancial: bool = False) -> list[Anomaly]:
    anomalies = []

    cashVals = getAnnualValues(aSeries, "BS", "cash_and_equivalents")
    cashChange = _yoyChange(cashVals)

    if cashChange is not None and cashChange < -50:
        anomalies.append(Anomaly(
            "warning", "cashBurn",
            f"현금성 자산 급감 ({cashChange:.0f}%)",
            cashChange,
        ))

    opCfVals = getAnnualValues(aSeries, "CF", "operating_cashflow")
    invCfVals = getAnnualValues(aSeries, "CF", "investing_cashflow")
    finCfVals = getAnnualValues(aSeries, "CF", "financing_cashflow")

    latestOp = None
    latestInv = None
    latestFin = None
    for v in reversed(opCfVals):
        if v is not None:
            latestOp = v
            break
    for v in reversed(invCfVals):
        if v is not None:
            latestInv = v
            break
    for v in reversed(finCfVals):
        if v is not None:
            latestFin = v
            break

    if not isFinancial and latestOp is not None and latestOp < 0 and latestFin is not None and latestFin > 0:
        anomalies.append(Anomaly(
            "warning", "cashBurn",
            f"영업CF 적자({latestOp/1e8:,.0f}억) + 재무CF 양수({latestFin/1e8:,.0f}억) — 차입으로 영업적자 보전",
        ))

    return anomalies


def detectMarginDivergence(aSeries: dict) -> list[Anomaly]:
    anomalies = []

    revVals = getAnnualValues(aSeries, "IS", "revenue")
    opVals = getAnnualValues(aSeries, "IS", "operating_income")
    niVals = getAnnualValues(aSeries, "IS", "net_income")

    validRev = [v for v in revVals if v is not None]
    validOp = [v for v in opVals if v is not None]
    validNi = [v for v in niVals if v is not None]

    if len(validRev) >= 2 and len(validOp) >= 2:
        prevMargin = (validOp[-2] / validRev[-2] * 100) if validRev[-2] and validRev[-2] != 0 else None
        currMargin = (validOp[-1] / validRev[-1] * 100) if validRev[-1] and validRev[-1] != 0 else None

        if prevMargin is not None and currMargin is not None:
            marginShift = currMargin - prevMargin
            if abs(marginShift) > 5:
                direction = "개선" if marginShift > 0 else "악화"
                severity = "info" if marginShift > 0 else "warning"
                anomalies.append(Anomaly(
                    severity, "marginDivergence",
                    f"영업이익률 {direction} ({prevMargin:.1f}% → {currMargin:.1f}%, {marginShift:+.1f}%p)",
                    marginShift,
                ))

    if len(validOp) >= 2 and len(validNi) >= 2:
        prevGap = validNi[-2] - validOp[-2] if validOp[-2] is not None and validNi[-2] is not None else None
        currGap = validNi[-1] - validOp[-1] if validOp[-1] is not None and validNi[-1] is not None else None

        if prevGap is not None and currGap is not None:
            gapChange = currGap - prevGap
            if abs(gapChange) > 0 and validOp[-1] and validOp[-1] != 0:
                gapRatio = (abs(gapChange) / abs(validOp[-1])) * 100
                if gapRatio > 30:
                    anomalies.append(Anomaly(
                        "warning", "marginDivergence",
                        f"영업외손익 급변 (영업이익 대비 {gapRatio:.0f}% 규모 변동)",
                        gapRatio,
                    ))

    return anomalies


def detectFinancialSectorAnomaly(aSeries: dict, isFinancial: bool) -> list[Anomaly]:
    if not isFinancial:
        return []

    anomalies = []

    liabVals = getAnnualValues(aSeries, "BS", "total_liabilities")
    equityVals = getAnnualValues(aSeries, "BS", "total_equity") or getAnnualValues(aSeries, "BS", "equity_including_nci")

    validLiab = [v for v in liabVals if v is not None]
    validEq = [v for v in equityVals if v is not None]

    if len(validLiab) >= 2 and len(validEq) >= 2:
        prevDr = (validLiab[-2] / validEq[-2] * 100) if validEq[-2] and validEq[-2] > 0 else None
        currDr = (validLiab[-1] / validEq[-1] * 100) if validEq[-1] and validEq[-1] > 0 else None

        if prevDr is not None and currDr is not None:
            drShift = currDr - prevDr
            if abs(drShift) > 100:
                direction = "급증" if drShift > 0 else "급감"
                anomalies.append(Anomaly(
                    "warning", "financialSector",
                    f"금융업 부채비율 {direction} ({prevDr:.0f}% → {currDr:.0f}%, {drShift:+.0f}%p)",
                    drShift,
                ))

    niVals = getAnnualValues(aSeries, "IS", "net_income")
    niChange = _yoyChange(niVals)
    if niChange is not None and niChange < -30:
        anomalies.append(Anomaly(
            "warning", "financialSector",
            f"금융업 순이익 급감 ({niChange:.0f}%)",
            niChange,
        ))

    return anomalies


def runAnomalyDetection(stockCode: str, isFinancial: bool = False) -> list[Anomaly]:
    aResult = buildAnnual(stockCode)
    if aResult is None:
        return []
    aSeries, _ = aResult

    anomalies = []
    anomalies.extend(detectEarningsQuality(aSeries, isFinancial))
    anomalies.extend(detectWorkingCapitalAnomaly(aSeries))
    anomalies.extend(detectBalanceSheetShift(aSeries))
    anomalies.extend(detectCashBurn(aSeries, isFinancial))
    anomalies.extend(detectMarginDivergence(aSeries))
    anomalies.extend(detectFinancialSectorAnomaly(aSeries, isFinancial))

    anomalies.sort(key=lambda a: {"danger": 0, "warning": 1, "info": 2}.get(a.severity, 3))
    return anomalies


STOCKS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "005380": "현대자동차",
    "005490": "POSCO홀딩스",
    "035420": "NAVER",
    "035720": "카카오",
    "105560": "KB금융",
    "055550": "신한지주",
    "006800": "미래에셋증권",
    "032830": "삼성생명",
    "051910": "LG화학",
    "373220": "LG에너지솔루션",
    "066570": "LG전자",
    "003550": "LG",
    "000270": "기아",
    "068270": "셀트리온",
    "028260": "삼성물산",
    "096770": "SK이노베이션",
    "034730": "SK",
    "015760": "한국전력",
}

FINANCIAL_STOCKS = {"105560", "055550", "006800", "032830"}

if __name__ == "__main__":
    import importlib.util
    from pathlib import Path

    protoPath = Path(__file__).parent / "010_gradingCalibration.py"
    spec = importlib.util.spec_from_file_location("proto010", protoPath)
    proto = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proto)

    allAnomalies = {}
    categoryCounts = Counter()
    severityCounts = Counter()

    print(f"{'=' * 80}")
    print("  이상치 탐지 (20종목)")
    print(f"{'=' * 80}")

    for code, name in STOCKS.items():
        isFinancial = code in FINANCIAL_STOCKS
        anomalies = runAnomalyDetection(code, isFinancial)
        allAnomalies[code] = anomalies

        if anomalies:
            finLabel = " [금융]" if isFinancial else ""
            print(f"\n  {name}{finLabel} ({code}) — {len(anomalies)}건")
            for a in anomalies:
                icon = {"danger": "!!!", "warning": " ! ", "info": " i "}[a.severity]
                print(f"    [{icon}] {a.text}")
                categoryCounts[a.category] += 1
                severityCounts[a.severity] += 1
        else:
            print(f"\n  {name} ({code}) — 이상 없음")

    print(f"\n\n{'=' * 80}")
    print("  탐지 통계")
    print(f"{'=' * 80}")

    totalAnomalies = sum(len(a) for a in allAnomalies.values())
    stocksWithAnomalies = sum(1 for a in allAnomalies.values() if a)
    print(f"\n  총 탐지: {totalAnomalies}건 ({stocksWithAnomalies}/20종목)")

    print(f"\n  심각도별 분포")
    for sev in ["danger", "warning", "info"]:
        c = severityCounts.get(sev, 0)
        print(f"    {sev:10s}: {c}건")

    print(f"\n  카테고리별 분포")
    for cat, cnt in sorted(categoryCounts.items(), key=lambda x: -x[1]):
        print(f"    {cat:25s}: {cnt}건")

    print(f"\n\n{'=' * 80}")
    print("  종목별 이상치 수")
    print(f"{'=' * 80}")

    ranked = sorted(allAnomalies.items(), key=lambda x: len(x[1]), reverse=True)
    for code, anomalies in ranked:
        name = STOCKS[code]
        dangerCnt = sum(1 for a in anomalies if a.severity == "danger")
        warningCnt = sum(1 for a in anomalies if a.severity == "warning")
        infoCnt = sum(1 for a in anomalies if a.severity == "info")
        barD = "!" * dangerCnt
        barW = "*" * warningCnt
        barI = "." * infoCnt
        print(f"  {name:<15} {len(anomalies):>2}건  {barD}{barW}{barI}")
