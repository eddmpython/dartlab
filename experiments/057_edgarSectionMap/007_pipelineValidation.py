"""
실험 ID: 057-007
실험명: sections 파이프라인 전종목 무에러 검증

목적:
- 현재 수집된 전체 ticker에 대해 sections() 파이프라인이 에러 없이 동작하는지 확인한다.
- topic/period 통계를 수집하여 수평화 품질을 점검한다.

가설:
1. 매핑 커버리지 100%이므로 전종목 무에러 예상.
2. topic 수는 10-K 기준 15~35, 10-Q 기준 10~20 범위.

방법:
1. data/edgar/docs/*.parquet 전체 순회
2. sections(ticker) 호출, 에러/None/성공 분류
3. 성공 시 shape, topic 수, period 수 기록
4. 실패 시 에러 메시지 기록

결과 (실험 후 작성):

결론:

실험일: 2026-03-13
"""

from __future__ import annotations

import traceback
from pathlib import Path

from dartlab import config
from dartlab.engines.company.edgar.docs.sections.pipeline import sections


def main() -> None:
    docsDir = Path(config.dataDir) / "edgar" / "docs"
    files = sorted(docsDir.glob("*.parquet"))
    if not files:
        print("docs 없음")
        return

    tickers = [f.stem for f in files]
    print(f"=== 057-007 sections pipeline validation ===")
    print(f"tickers: {len(tickers)}")
    print()

    success = 0
    noneCount = 0
    errors: list[tuple[str, str]] = []
    stats: list[dict[str, object]] = []

    for i, ticker in enumerate(tickers):
        try:
            result = sections(ticker)
            if result is None:
                noneCount += 1
                print(f"  [{i+1}/{len(tickers)}] {ticker} → None")
            else:
                success += 1
                nTopics = result.height
                nPeriods = len(result.columns) - 1
                stats.append({
                    "ticker": ticker,
                    "topics": nTopics,
                    "periods": nPeriods,
                })
                if (i + 1) % 50 == 0 or i == 0:
                    print(f"  [{i+1}/{len(tickers)}] {ticker} → {nTopics} topics × {nPeriods} periods")
        except Exception as e:
            errors.append((ticker, traceback.format_exc()))
            print(f"  [{i+1}/{len(tickers)}] {ticker} → ERROR: {e}")

    print()
    print(f"=== RESULT ===")
    print(f"success: {success}")
    print(f"none:    {noneCount}")
    print(f"errors:  {len(errors)}")

    if stats:
        topics = [s["topics"] for s in stats]
        periods = [s["periods"] for s in stats]
        print(f"\ntopics  min={min(topics)} max={max(topics)} avg={sum(topics)/len(topics):.1f}")
        print(f"periods min={min(periods)} max={max(periods)} avg={sum(periods)/len(periods):.1f}")

    if errors:
        print(f"\n--- ERRORS ---")
        for ticker, tb in errors[:5]:
            print(f"\n{ticker}:")
            print(tb[-500:])


if __name__ == "__main__":
    main()
