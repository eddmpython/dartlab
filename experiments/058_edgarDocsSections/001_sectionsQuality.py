"""
실험 ID: 058-001
실험명: EDGAR sections 수평화 품질 검증

목적:
- sections() 파이프라인이 반환하는 DataFrame의 실질 품질을 검증한다.
- content 길이 분포, 공백률, form별 topic 분포를 확인한다.

가설:
1. 10-K topic은 대부분 수천 자 이상의 실질 content를 가진다.
2. 10-Q topic도 주요 항목(MD&A, Financial Statements)은 실질 content가 있다.
3. 공백(None) 비율은 topic × period 매트릭스에서 자연스러운 수준 (10-K는 연 1회, 10-Q는 분기별)

방법:
1. 대표 ticker 10개에서 sections() 호출
2. 각 cell의 text 길이 측정
3. None 비율, topic별 평균 content 길이, form별 분포 출력

결과 (실험 후 작성):

결론:

실험일: 2026-03-13
"""

from __future__ import annotations

from dartlab.engines.edgar.docs.sections.pipeline import sections


SAMPLE_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
    "JPM", "BAC", "JNJ", "PFE", "XOM",
]


def main() -> None:
    print("=== 058-001 sections 수평화 품질 검증 ===\n")

    for ticker in SAMPLE_TICKERS:
        df = sections(ticker)
        if df is None:
            print(f"{ticker}: None")
            continue

        topics = df["topic"].to_list()
        periods = [c for c in df.columns if c != "topic"]
        totalCells = len(topics) * len(periods)
        nonNullCount = 0
        lengths: list[int] = []

        for row in df.iter_rows(named=True):
            for p in periods:
                val = row.get(p)
                if val is not None:
                    nonNullCount += 1
                    lengths.append(len(str(val)))

        fillRate = nonNullCount / totalCells * 100 if totalCells else 0
        avgLen = sum(lengths) / len(lengths) if lengths else 0
        medLen = sorted(lengths)[len(lengths) // 2] if lengths else 0

        formTopics: dict[str, int] = {}
        for t in topics:
            form = t.split("::")[0] if "::" in t else "unknown"
            formTopics[form] = formTopics.get(form, 0) + 1

        print(f"{ticker}: {len(topics)} topics × {len(periods)} periods")
        print(f"  fill: {fillRate:.1f}% ({nonNullCount}/{totalCells})")
        print(f"  content len: avg={avgLen:.0f} med={medLen} min={min(lengths) if lengths else 0} max={max(lengths) if lengths else 0}")
        print(f"  form topics: {formTopics}")
        print()


if __name__ == "__main__":
    main()
