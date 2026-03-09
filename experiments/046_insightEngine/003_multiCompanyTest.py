"""
실험 ID: 003
실험명: 복수 종목 교차 검증 — 인사이트 엔진 신뢰성 테스트

목적:
- 다양한 업종/규모의 종목에서 인사이트 엔진이 상식적인 결과를 내는지 검증
- 엣지 케이스 발견 (금융업, 적자 기업, 데이터 부족 종목)
- 불완전 연도(2025년 3분기까지) 문제 확인

가설:
1. 대부분 종목에서 등급이 상식적으로 나온다
2. 금융업(은행)은 유동비율 등이 다르게 나올 수 있다
3. 적자 기업은 Profitability/Cashflow에서 경고가 나온다

방법:
1. 삼성전자, 현대차, KB금융, 카카오, LG에너지솔루션 5종목
2. 002의 전체 파이프라인 실행
3. 등급 매트릭스 비교

결과 (실험 후 작성):
- 등급 매트릭스:
  삼성전자:      F B A A B F A
  현대자동차:     F B F F B F B
  KB금융:       F D F D D D C
  카카오:        F D C A N F B
  LG에너지솔루션:  D C C B B F B

결론:
- 가설 1 기각: Performance에서 불완전 연도 문제로 모든 종목이 F
- 가설 2 채택: KB금융 부채비율 1233%, 매출 None — 금융업 특수 처리 필요
- 가설 3 채택: 카카오 ROE -3.3%로 Profitability D, LG에너지 영업CF 양호+FCF 적자 = "적극 투자"
- 다음 실험: 불완전 연도 보정(004), 금융업 특수 처리(005)

실험일: 2026-03-09
"""

import sys
import importlib.util
from pathlib import Path

sys.path.insert(0, "src")

import dartlab
dartlab.verbose = False

protoPath = Path(__file__).parent / "002_insightPrototype.py"
spec = importlib.util.spec_from_file_location("proto", protoPath)
proto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proto)


STOCKS = {
    "005930": "삼성전자",
    "005380": "현대자동차",
    "105560": "KB금융",
    "035720": "카카오",
    "373220": "LG에너지솔루션",
}


def main():
    results = {}
    for code, name in STOCKS.items():
        print(f"\n{'#' * 70}")
        print(f"  {name} ({code})")
        print(f"{'#' * 70}")
        insights = proto.runFullAnalysis(code)
        if insights:
            results[code] = insights

    print(f"\n\n{'=' * 70}")
    print("  등급 매트릭스")
    print(f"{'=' * 70}")

    categories = ["performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"]

    header = f"{'종목':<15}" + "".join(f"{c:<15}" for c in categories)
    print(header)
    print("-" * len(header))

    for code, insights in results.items():
        name = STOCKS[code]
        row = f"{name:<15}"
        for cat in categories:
            if cat in insights:
                r = insights[cat]
                row += f"{r.grade:<15}"
            else:
                row += f"{'N/A':<15}"
        print(row)


if __name__ == "__main__":
    main()
