"""
실험 ID: 058-002
실험명: EDGAR Company.docs namespace 프로토타입

목적:
- EDGAR Company에 docs namespace를 붙이는 프로토타입을 실험한다.
- DART의 _DocsAccessor 패턴을 참고하되 EDGAR는 레거시 파서 없이 sections만 노출.

가설:
1. sections()가 이미 동작하므로 DocsAccessor에 감싸기만 하면 된다.
2. filings() 목록도 parquet에서 추출 가능하다.
3. DART처럼 retrievalBlocks/contextSlices는 아직 불필요 — sections만 먼저.

방법:
1. EDGAR Company를 확장하지 않고, 독립 프로토타입으로 docs namespace 구현
2. sections, filings, show(topic, period) 3개 메서드 검증
3. 대표 ticker에서 동작 확인

결과 (실험 후 작성):

결론:

실험일: 2026-03-13
"""

from __future__ import annotations

import polars as pl

from dartlab import config
from dartlab.core.dataLoader import loadData
from dartlab.providers.edgar.docs.sections.pipeline import sections


class EdgarDocsProto:
    """EDGAR docs namespace 프로토타입."""

    def __init__(self, ticker: str):
        self.ticker = ticker

    @property
    def sections(self) -> pl.DataFrame | None:
        return sections(self.ticker)

    def filings(self) -> pl.DataFrame | None:
        df = loadData(self.ticker, category="edgarDocs")
        if df is None or df.is_empty():
            return None
        if "period_key" not in df.columns or "accession_no" not in df.columns:
            return None

        cols = ["period_key", "form_type", "accession_no", "filed_date"]
        available = [c for c in cols if c in df.columns]
        filingsDf = (
            df.select(available)
            .unique(subset=["accession_no"])
            .sort("period_key", descending=True)
        )
        return filingsDf

    def show(self, topic: str, period: str | None = None) -> str | None:
        sec = self.sections
        if sec is None:
            return None

        topicRow = sec.filter(pl.col("topic") == topic)
        if topicRow.is_empty():
            return None

        if period is not None:
            if period not in topicRow.columns:
                return None
            return topicRow[period][0]

        periods = [c for c in topicRow.columns if c != "topic"]
        for p in periods:
            val = topicRow[p][0]
            if val is not None:
                return val
        return None


def main() -> None:
    print("=== 058-002 EDGAR docs namespace 프로토타입 ===\n")

    for ticker in ["AAPL", "MSFT", "TSLA"]:
        docs = EdgarDocsProto(ticker)

        sec = docs.sections
        if sec is None:
            print(f"{ticker}: sections None")
            continue

        print(f"{ticker}: {sec.height} topics × {len(sec.columns) - 1} periods")

        filings = docs.filings()
        if filings is not None:
            print(f"  filings: {filings.height}")

        topics = sec["topic"].to_list()
        businessTopic = next((t for t in topics if "Business" in t or "business" in t), None)
        if businessTopic:
            text = docs.show(businessTopic)
            if text:
                print(f"  show('{businessTopic}'): {len(text)} chars")
                print(f"    preview: {text[:200]}...")
        print()


if __name__ == "__main__":
    main()
