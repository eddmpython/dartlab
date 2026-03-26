"""
실험 ID: 058-004
실험명: 10-K / 10-Q 대응 topic content 비교

목적:
- 의미적 대응 쌍 (예: 10-K::item7Mdna vs 10-Q::partIItem2Mdna)의 content를 비교한다.
- 분기별 MD&A가 연간 MD&A와 어떤 관계인지 파악한다.
- form 경계를 넘는 시계열 비교의 실용성을 검증한다.

가설:
1. 10-Q MD&A는 10-K MD&A보다 짧지만 동일 구조를 따른다.
2. Risk Factors는 연간/분기 모두 유사 길이 (업데이트 패턴).
3. Financial Statements는 연간이 훨씬 길다 (분기는 condensed).

방법:
1. 대응 쌍별로 10-K/10-Q content 길이 시계열 비교
2. 최신 연간과 최신 분기의 content 길이 비율 분석

결과 (실험 후 작성):

결론:

실험일: 2026-03-13
"""

from __future__ import annotations

import polars as pl

from dartlab.providers.edgar.docs.sections.pipeline import sections

SEMANTIC_PAIRS = {
    "riskFactors": ("item1ARiskFactors", "partIIItem1ARiskFactors"),
    "mdna": ("item7Mdna", "partIItem2Mdna"),
    "financialStatements": ("item8FinancialStatements", "partIItem1FinancialStatements"),
    "controls": ("item9AControlsAndProcedures", "partIItem4ControlsAndProcedures"),
    "legalProceedings": ("item3LegalProceedings", "partIIItem1LegalProceedings"),
}


def analyzeContentComparison(ticker: str) -> None:
    df = sections(ticker)
    if df is None:
        print(f"{ticker}: None")
        return

    periods = [c for c in df.columns if c != "topic"]
    annualPeriods = sorted([p for p in periods if "Q" not in p], reverse=True)
    quarterPeriods = sorted([p for p in periods if "Q" in p], reverse=True)

    topicData: dict[str, dict[str, str | None]] = {}
    for row in df.iter_rows(named=True):
        topicId = row["topic"].split("::")[1] if "::" in row["topic"] else row["topic"]
        topicData[topicId] = {p: row.get(p) for p in periods}

    print(f"=== {ticker} ===")
    print(f"{'pair':<25} {'10-K latest':>12} {'10-Q latest':>12} {'ratio':>7} {'10-K avg':>10} {'10-Q avg':>10}")
    print("-" * 80)

    for name, (kId, qId) in SEMANTIC_PAIRS.items():
        kData = topicData.get(kId, {})
        qData = topicData.get(qId, {})

        kLens = [len(kData[p]) for p in annualPeriods if kData.get(p)]
        qLens = [len(qData[p]) for p in quarterPeriods if qData.get(p)]

        kLatest = kLens[0] if kLens else 0
        qLatest = qLens[0] if qLens else 0
        ratio = f"{qLatest / kLatest:.2f}" if kLatest else "-"
        kAvg = sum(kLens) / len(kLens) if kLens else 0
        qAvg = sum(qLens) / len(qLens) if qLens else 0

        print(f"{name:<25} {kLatest:>10,} {qLatest:>10,} {ratio:>7} {kAvg:>10,.0f} {qAvg:>10,.0f}")
    print()


def main() -> None:
    print("=== 058-004 cross-form content 비교 ===\n")
    for ticker in ["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL"]:
        analyzeContentComparison(ticker)


if __name__ == "__main__":
    main()
