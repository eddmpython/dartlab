"""
실험 ID: 056-029
실험명: section map 배치 준비 검증

목적:
- 현재 production spike 상태가 실전 배치 준비 수준인지 다기업 기준으로 검증한다.

가설:
1. sectionMappings.json이 연결된 sections()는 대표 기업 묶음에서 에러 없이 동작한다.
2. canonical topic이 여러 회사에서 실제로 출력된다.

방법:
1. 대표 10개 기업에 대해 sections()를 실행한다.
2. 실행 시간, topic 수, canonical topic 존재 여부를 수집한다.
3. 실패/에러 여부를 출력한다.

결과 (실험 후 작성):

- 대표 10개 기업에서 sections() 실행 검증 완료
- 10개 기업 모두 `status=ok`
- 평균 실행 시간: `1.387초`
- 평균 topic 수: `217.3`
결론:

- 현재 production spike는 대표 기업 묶음에서 에러 없이 동작한다.
- 핵심 canonical topic이 다기업에서 실제로 출력되므로, 공통 section 매핑은 실전 배치 준비 수준으로 볼 수 있다.
실험일: 2026-03-11
"""

from __future__ import annotations

from time import perf_counter

import polars as pl

from dartlab.engines.dart.docs.sections.pipeline import sections


TARGET_CODES = [
    "005930",
    "000660",
    "035420",
    "035720",
    "005380",
    "005490",
    "012330",
    "051910",
    "066570",
    "207940",
]
CANONICAL_KEYS = {
    "companyOverview",
    "companyHistory",
    "businessOverview",
    "salesOrder",
    "riskDerivative",
    "audit",
}


def main() -> None:
    rows: list[dict[str, object]] = []
    for code in TARGET_CODES:
        started = perf_counter()
        df = sections(code)
        elapsed = perf_counter() - started
        if df is None:
            rows.append(
                {
                    "stockCode": code,
                    "elapsedSec": round(elapsed, 3),
                    "topicCount": 0,
                    "canonicalHits": 0,
                    "status": "no_data",
                }
            )
            continue

        topics = set(df.get_column("topic").to_list())
        hits = len(CANONICAL_KEYS & topics)
        rows.append(
            {
                "stockCode": code,
                "elapsedSec": round(elapsed, 3),
                "topicCount": df.height,
                "canonicalHits": hits,
                "status": "ok",
            }
        )

    out = pl.DataFrame(rows)
    print("=" * 72)
    print("056-029 section map 배치 준비 검증")
    print("=" * 72)
    print(out)
    print()
    print(
        out.select(
            pl.col("elapsedSec").mean().alias("avgElapsedSec"),
            pl.col("topicCount").mean().alias("avgTopicCount"),
            pl.col("canonicalHits").mean().alias("avgCanonicalHits"),
        )
    )


if __name__ == "__main__":
    main()
