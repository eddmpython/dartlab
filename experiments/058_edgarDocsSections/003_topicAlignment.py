"""
실험 ID: 058-003
실험명: 10-K / 10-Q topic 정렬 분석

목적:
- 10-K와 10-Q의 topic이 어떻게 겹치고 보완하는지 분석한다.
- 수평화 DataFrame에서 연간(10-K)과 분기별(10-Q) topic이 period 축에서 어떻게 분포하는지 확인한다.
- 동일 의미 topic (예: 10-K::item1ARiskFactors vs 10-Q::partIIItem1ARiskFactors)의 연결 가능성 탐색.

가설:
1. 10-K topic은 연간 period에만, 10-Q topic은 분기 period에만 값이 있을 것이다.
2. Risk Factors, MD&A, Financial Statements 등은 10-K/10-Q 양쪽에 존재하며 의미적으로 대응된다.
3. 대응 쌍을 식별하면 form 경계를 넘는 시계열 비교가 가능해진다.

방법:
1. 대표 ticker의 sections에서 topic별 period 채움 패턴 분석
2. 10-K/10-Q 의미적 대응 쌍 식별
3. 대응 쌍의 content 길이 비교

결과 (실험 후 작성):

결론:

실험일: 2026-03-13
"""

from __future__ import annotations

import polars as pl

from dartlab.providers.edgar.docs.sections.pipeline import sections


def analyzeTopicAlignment(ticker: str) -> None:
    df = sections(ticker)
    if df is None:
        print(f"{ticker}: None")
        return

    periods = [c for c in df.columns if c != "topic"]
    annualPeriods = [p for p in periods if "Q" not in p]
    quarterPeriods = [p for p in periods if "Q" in p]

    print(f"=== {ticker} ===")
    print(f"periods: {len(periods)} total ({len(annualPeriods)} annual, {len(quarterPeriods)} quarter)")
    print()

    print(f"{'topic':<55} {'annual':>7} {'quarter':>7} {'form'}")
    print("-" * 85)

    for row in df.iter_rows(named=True):
        topic = row["topic"]
        form = topic.split("::")[0] if "::" in topic else "?"
        topicId = topic.split("::")[1] if "::" in topic else topic

        annualFilled = sum(1 for p in annualPeriods if row.get(p) is not None)
        quarterFilled = sum(1 for p in quarterPeriods if row.get(p) is not None)

        print(f"{topicId:<55} {annualFilled:>4}/{len(annualPeriods):<3} {quarterFilled:>4}/{len(quarterPeriods):<3} {form}")

    print()

    tenKTopics = [r["topic"].split("::")[1] for r in df.iter_rows(named=True) if r["topic"].startswith("10-K::")]
    tenQTopics = [r["topic"].split("::")[1] for r in df.iter_rows(named=True) if r["topic"].startswith("10-Q::")]

    semanticPairs = {
        "riskFactors": ("item1ARiskFactors", "partIIItem1ARiskFactors"),
        "mdna": ("item7Mdna", "partIItem2Mdna"),
        "financialStatements": ("item8FinancialStatements", "partIItem1FinancialStatements"),
        "controls": ("item9AControlsAndProcedures", "partIItem4ControlsAndProcedures"),
        "legalProceedings": ("item3LegalProceedings", "partIIItem1LegalProceedings"),
        "exhibits": ("item15ExhibitsAndSchedules", "partIIItem6Exhibits"),
    }

    print("--- 의미적 대응 쌍 ---")
    for name, (kId, qId) in semanticPairs.items():
        kExists = kId in tenKTopics
        qExists = qId in tenQTopics
        mark = "OK" if kExists and qExists else ("K only" if kExists else ("Q only" if qExists else "NONE"))
        print(f"  {name:<25} 10-K::{kId:<45} {'Y' if kExists else 'N'}  |  10-Q::{qId:<45} {'Y' if qExists else 'N'}  [{mark}]")
    print()


def main() -> None:
    print("=== 058-003 topic alignment 분석 ===\n")
    for ticker in ["AAPL", "MSFT", "JPM"]:
        analyzeTopicAlignment(ticker)


if __name__ == "__main__":
    main()
