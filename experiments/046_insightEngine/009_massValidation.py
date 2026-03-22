"""
실험 ID: 009
실험명: 대규모 종목 검증 — 등급 분포 + 이상치 발견

목적:
- 008 로직을 20종목 이상에 적용하여 등급 분포가 상식적인지 확인
- 업종별 편향 발견 (자동차/건설/유통 등 부채비율 높은 업종)
- 데이터 부족/에러가 나는 종목 파악
- 패키지 흡수 전 최종 안정성 검증

가설:
1. 대부분 종목에서 에러 없이 7개 등급이 산출된다
2. 등급 분포가 정규분포에 가까운 형태를 보인다 (A~F 골고루)
3. 금융업 감지가 은행/증권/보험 외 종목에서 오탐하지 않는다
4. Health F가 나오는 종목은 실제로 부채비율이 높은 업종이다

방법:
1. KOSPI 대형주 20종목 선정 (다양한 업종)
2. 008의 runFullAnalysis 실행
3. 등급 분포 히스토그램, 업종별 패턴 분석
4. 에러/이상치 종목 목록화

결과 (실험 후 작성):
- 20/20 종목 에러 없이 분석 완료
- 전체 등급 분포: A 23.6%, B 37.1%, C 12.9%, D 8.6%, F 15.0%, N 2.9%
- 카테고리별 분포
  Performance:  A:2 B:5 C:1 D:6 F:6 — 골고루 분포, 양호
  Profitability: A:4 B:6 C:5 D:3 F:2 — 가장 균형잡힌 분포
  Health:       A:3 B:5 C:8 F:4 — D 없음 (임계값 조정 검토)
  Cashflow:     A:14 B:5 F:1 — A에 심하게 편중 ★문제
  Governance:   B:13 D:3 N:4 — A/C/F 없음 (이진법적)
  Risk:         A:5 B:3 C:4 F:8 — F 과다
  Opportunity:  A:5 B:15 — C/D/F 없음 ★분별력 부족
- 금융업 감지: 4종목 정확, 오탐 0건
- Health F: 현대차(202%), SK이노(272%), SK(466%), 한국전력(441%)
- Governance N: NAVER, 카카오, 삼성생명, SK (report 데이터 미보유)

결론:
- 가설 1 채택: 20종목 전부 에러 없이 7개 등급 산출
- 가설 2 부분기각: B에 편중(37.1%), 정규분포보다 우상향 치우침
- 가설 3 채택: 금융업 감지 정확, 오탐 0건 (NAVER/카카오의 이자수익 1신호만으로는 미감지)
- 가설 4 채택: Health F 4종목 모두 부채비율 200% 이상 (SK 466%, 한전 441%)
- ★ Cashflow A 편중 문제: 20종목 중 14종목 A — 분별력이 거의 없음
  → 원인: 영업CF 양수 + FCF 양수이면 자동 A (4점/4점=100%)
  → 개선: FCF 크기, CF/매출 비율, CF 추세 등 세분화 필요
- ★ Opportunity 분별력 부족: A:5 B:15 — C 이하 없음
  → 원인: 긍정 요소 1개만 있어도 B, 3개 이상 A
  → 개선: 임계값 상향 또는 가중치 재설계
- Governance가 이진법적 (리스크 없으면 B, 있으면 D) → 중간 등급 필요
- Health에 D 등급이 없음 → C와 F 사이 gap 큼

실험일: 2026-03-09
"""

import sys

sys.path.insert(0, "src")

import importlib.util
from collections import Counter
from pathlib import Path

import dartlab

dartlab.verbose = False

protoPath = Path(__file__).parent / "008_financialInsightIntegration.py"
spec = importlib.util.spec_from_file_location("proto008", protoPath)
proto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proto)


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

CATEGORIES = ["performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"]


def main():
    results = {}
    errors = {}
    financialDetected = {}

    for code, name in STOCKS.items():
        print(f"\n  {'─' * 40}")
        print(f"  {name} ({code})")

        from dartlab.engines.financeEngine.pivot import buildAnnual
        from dartlab.engines.financeEngine.ratios import calcRatios
        aResult = buildAnnual(code)
        if aResult is None:
            errors[code] = "데이터 없음"
            print(f"    → 데이터 없음")
            continue

        aSeries, _ = aResult
        ratios = calcRatios(aSeries)
        isFinancial, signals = proto.detectFinancialSector(aSeries, ratios)
        financialDetected[code] = (isFinancial, signals)

        insights = proto.runFullAnalysis(code)
        if insights is None:
            errors[code] = "분석 실패"
            print(f"    → 분석 실패")
            continue

        grades = {}
        for cat in CATEGORIES:
            if cat in insights:
                grades[cat] = insights[cat].grade
        results[code] = grades

        gradeStr = " ".join(f"{g}" for g in grades.values())
        finLabel = " [금융]" if isFinancial else ""
        print(f"    → {gradeStr}{finLabel}")

    print(f"\n\n{'=' * 80}")
    print("  등급 매트릭스")
    print(f"{'=' * 80}")

    header = f"  {'종목':<15}"
    for cat in CATEGORIES:
        header += f" {cat[:5]:^7}"
    print(header)
    print(f"  {'─' * 70}")

    for code, name in STOCKS.items():
        if code not in results:
            print(f"  {name:<15} {'ERROR':^7}")
            continue
        grades = results[code]
        finLabel = "*" if financialDetected.get(code, (False,))[0] else ""
        row = f"  {name + finLabel:<15}"
        for cat in CATEGORIES:
            g = grades.get(cat, "?")
            row += f" {g:^7}"
        print(row)

    print(f"\n  * = 금융업 감지")

    print(f"\n\n{'=' * 80}")
    print("  등급 분포")
    print(f"{'=' * 80}")

    for cat in CATEGORIES:
        counter = Counter()
        for grades in results.values():
            g = grades.get(cat, "?")
            counter[g] += 1

        dist = " ".join(f"{g}:{c}" for g, c in sorted(counter.items()))
        print(f"  {cat:<15} {dist}")

    print(f"\n\n{'=' * 80}")
    print("  전체 등급 분포")
    print(f"{'=' * 80}")

    allGrades = Counter()
    for grades in results.values():
        for g in grades.values():
            allGrades[g] += 1

    total = sum(allGrades.values())
    for g in ["A", "B", "C", "D", "F", "N"]:
        c = allGrades.get(g, 0)
        pct = (c / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  {g}: {c:>3} ({pct:>5.1f}%) {bar}")

    print(f"\n\n{'=' * 80}")
    print("  금융업 감지 결과")
    print(f"{'=' * 80}")

    for code, name in STOCKS.items():
        if code in financialDetected:
            isF, sigs = financialDetected[code]
            label = "금융업" if isF else "일반"
            sigStr = f" ({len(sigs)}신호: {', '.join(sigs)})" if sigs else ""
            print(f"  {name:<15} {label}{sigStr}")

    if errors:
        print(f"\n\n{'=' * 80}")
        print("  에러 종목")
        print(f"{'=' * 80}")
        for code, err in errors.items():
            print(f"  {STOCKS[code]} ({code}): {err}")

    print(f"\n\n{'=' * 80}")
    print("  Health F 종목 분석")
    print(f"{'=' * 80}")

    for code, grades in results.items():
        if grades.get("health") == "F":
            name = STOCKS[code]
            aResult = buildAnnual(code)
            if aResult:
                aSeries, _ = aResult
                ratios = calcRatios(aSeries)
                dr = ratios.debtRatio
                cr = ratios.currentRatio
                isF = financialDetected.get(code, (False,))[0]
                print(f"  {name:<15} 부채비율={dr}% 유동비율={cr}% 금융업={isF}")

    print(f"\n  총 {len(results)}종목 분석 완료, {len(errors)}종목 에러")


if __name__ == "__main__":
    main()
