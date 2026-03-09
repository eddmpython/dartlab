"""
실험 ID: 005
실험명: 금융업 감지 + 임계값 조정

목적:
- KB금융(105560)이 부채비율 1233%, 매출 None으로 나오는 문제 해결
- finance parquet에서 금융업 여부를 자동 감지하는 방법 탐색
- 금융업 전용 임계값/대체 지표 설계

가설:
1. revenue가 None이고 operating_income이 있으면 금융업일 가능성 높다
2. 금융업은 부채비율 임계값을 대폭 올리거나 아예 평가에서 제외해야 한다
3. 금융업은 operating_income 기준으로 Performance를 판단할 수 있다

방법:
1. KB금융, 신한지주, 삼성생명, 미래에셋증권 등 금융업 종목 시계열 확인
2. 금융업 자동 감지 휴리스틱 설계
3. 금융업 전용 Health 임계값 테스트

결과 (실험 후 작성):
- 감지 정확도 6/6 (100%)
  KB금융:     금융업 O (4신호: revenue없음, 부채1233%, 유동자산없음, 이자수익존재)
  신한지주:    금융업 O (4신호)
  삼성생명:    금융업 O (4신호: 보험수익 존재)
  미래에셋증권:  금융업 O (3신호)
  삼성전자:    비금융 O (0신호)
  카카오:      비금융 O (1신호: 부채비율만 해당 없음)
- 금융업 Health 임계값: <1000% 양호, <1500% 보통, ≥1500% 높음

결론:
- 가설 1 채택: revenue=None + operating_income 존재가 가장 강력한 신호
- 가설 2 채택: 금융업 부채비율 임계값을 일반(200%) 대비 5~7.5배(1000~1500%)로 조정
- 가설 3 채택: 금융업은 operating_income 기준으로 Performance 판단 가능
- 감지 룰: 신호 2개 이상이면 금융업 (오탐 0건)
- 다음 과제: 금융업 Profitability 전용 지표(이자마진, CIR), Cashflow 특수 처리

실험일: 2026-03-09
"""

import sys
sys.path.insert(0, "src")

from typing import Optional

import dartlab
dartlab.verbose = False

from dartlab.engines.financeEngine.pivot import buildAnnual
from dartlab.engines.financeEngine.ratios import calcRatios
from dartlab.engines.financeEngine.extract import getLatest, getAnnualValues


FINANCIAL_STOCKS = {
    "105560": "KB금융",
    "055550": "신한지주",
    "032830": "삼성생명",
    "006800": "미래에셋증권",
}

NORMAL_STOCKS = {
    "005930": "삼성전자",
    "035720": "카카오",
}


def detectFinancialSector(series: dict, ratios) -> tuple[bool, list[str]]:
    """금융업 자동 감지 휴리스틱."""
    signals = []

    revVals = getAnnualValues(series, "IS", "revenue")
    opVals = getAnnualValues(series, "IS", "operating_income")
    hasRevenue = any(v is not None for v in revVals)
    hasOpIncome = any(v is not None for v in opVals)

    if not hasRevenue and hasOpIncome:
        signals.append("revenue 없고 operating_income 있음")

    if ratios.debtRatio is not None and ratios.debtRatio > 500:
        signals.append(f"부채비율 {ratios.debtRatio:.0f}% (500% 초과)")

    if ratios.currentRatio is None and ratios.currentAssets is None:
        signals.append("유동자산/유동부채 데이터 없음")

    interestIncome = getLatest(series, "IS", "interest_income")
    if interestIncome is not None:
        signals.append(f"이자수익 계정 존재 ({interestIncome/1e8:,.0f}억)")

    netInterestIncome = getLatest(series, "IS", "net_interest_income")
    if netInterestIncome is not None:
        signals.append(f"순이자수익 계정 존재 ({netInterestIncome/1e8:,.0f}억)")

    insuranceRevenue = getLatest(series, "IS", "insurance_revenue")
    if insuranceRevenue is not None:
        signals.append(f"보험수익 계정 존재 ({insuranceRevenue/1e8:,.0f}억)")

    isFinancial = len(signals) >= 2
    return isFinancial, signals


def analyzeStock(stockCode: str, stockName: str):
    print(f"\n{'=' * 60}")
    print(f"  {stockName} ({stockCode})")
    print(f"{'=' * 60}")

    result = buildAnnual(stockCode)
    if result is None:
        print("  데이터 없음")
        return

    series, years = result
    ratios = calcRatios(series)

    isFinancial, signals = detectFinancialSector(series, ratios)
    label = "금융업" if isFinancial else "일반"
    print(f"  감지 결과: {label} (신호 {len(signals)}개)")
    for s in signals:
        print(f"    → {s}")

    print(f"\n  주요 지표:")
    print(f"    revenue TTM:         {_fmt(ratios.revenueTTM)}")
    print(f"    operating_income TTM: {_fmt(ratios.operatingIncomeTTM)}")
    print(f"    net_income TTM:      {_fmt(ratios.netIncomeTTM)}")
    print(f"    부채비율:             {_fmtPct(ratios.debtRatio)}")
    print(f"    유동비율:             {_fmtPct(ratios.currentRatio)}")
    print(f"    ROE:                 {_fmtPct(ratios.roe)}")
    print(f"    영업이익률:           {_fmtPct(ratios.operatingMargin)}")

    if isFinancial:
        print(f"\n  [금융업 전용 Health 평가]")
        if ratios.debtRatio is not None:
            if ratios.debtRatio < 1000:
                print(f"    부채비율 {ratios.debtRatio:.0f}% — 금융업 기준 양호 (은행 평균 ~1500%)")
            elif ratios.debtRatio < 1500:
                print(f"    부채비율 {ratios.debtRatio:.0f}% — 금융업 기준 보통")
            else:
                print(f"    부채비율 {ratios.debtRatio:.0f}% — 금융업 기준으로도 높음")

    isKeys = list(series.get("IS", {}).keys())
    print(f"\n  IS 계정 목록 ({len(isKeys)}개):")
    for k in isKeys[:15]:
        val = getLatest(series, "IS", k)
        if val is not None:
            print(f"    {k}: {val/1e8:,.0f}억")

    return isFinancial


def _fmt(val: Optional[float]) -> str:
    if val is None:
        return "None"
    return f"{val/1e8:,.0f}억"


def _fmtPct(val: Optional[float]) -> str:
    if val is None:
        return "None"
    return f"{val:.1f}%"


if __name__ == "__main__":
    print("===== 금융업 종목 =====")
    financialResults = {}
    for code, name in FINANCIAL_STOCKS.items():
        financialResults[code] = analyzeStock(code, name)

    print("\n\n===== 일반 종목 (대조군) =====")
    normalResults = {}
    for code, name in NORMAL_STOCKS.items():
        normalResults[code] = analyzeStock(code, name)

    print(f"\n\n{'=' * 60}")
    print("  감지 정확도 요약")
    print(f"{'=' * 60}")

    for code, name in FINANCIAL_STOCKS.items():
        r = financialResults.get(code)
        correct = "O" if r else "X"
        print(f"  {name}: 금융업 감지 {correct}")

    for code, name in NORMAL_STOCKS.items():
        r = normalResults.get(code)
        correct = "O" if not r else "X (오탐)"
        print(f"  {name}: 비금융 감지 {correct}")
