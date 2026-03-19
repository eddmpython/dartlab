"""
실험 ID: 003
실험명: sectionsDiff Polars hash 전환

목적:
- sectionsDiff가 iter_rows 8K행 + md5 78K회로 0.74s 소요
- hash/len 계산을 Polars 벡터화 + iter_rows → to_list() 전환

가설:
1. md5 → Polars hash() (xxhash64) 벡터화
2. len 계산도 벡터화
3. iter_rows(named=True) → 컬럼별 to_list()로 dict 오버헤드 제거
4. 0.74s → ~0.15s

방법:
1. 삼성전자(005930) sections 기준 현재 sectionsDiff 측정
2. hash/len 벡터화 + to_list 버전 구현 후 동일 측정
3. 결과 동일성 assert (null 건너뛰기 로직 동일하게 유지)

결과 (실험 후 작성):
- before avg: 0.55s (8,109행, 32,588 entries, md5 + iter_rows)
- after avg: 0.09s (hash 벡터화 + to_list, null 건너뛰기 로직 동일)
- 속도 향상: 6.1x
- 동일성 검증 OK (entries 수, summaries 수, topic/changedCount/totalPeriods 일치)

결론:
- **채택**. hash/len 계산을 Polars 벡터화, iter_rows → to_list()로 dict 오버헤드 제거
- null 건너뛰기 로직 때문에 완전 벡터화는 불가 → 행 루프는 유지하되 to_list로 최적화

실험일: 2026-03-19
"""

import time
import sys
sys.path.insert(0, "src")


def main():
    import polars as pl
    import dartlab
    from dartlab.engines.common.docs.diff import sectionsDiff, DiffResult, DiffEntry, DiffSummary
    import re

    c = dartlab.Company("005930")
    sec = c.docs.sections
    print(f"  sections shape: {sec.shape}")

    _PERIOD_RE = re.compile(r"^\d{4}(Q[1-4])?$")

    def _isPeriodCol(name):
        return bool(_PERIOD_RE.fullmatch(name))

    def _periodCols(df):
        return [c for c in df.columns if _isPeriodCol(c)]

    # --- before ---
    times_before = []
    for i in range(3):
        t0 = time.perf_counter()
        result_before = sectionsDiff(sec)
        t1 = time.perf_counter()
        times_before.append(t1 - t0)
        print(f"  before #{i+1}: {t1-t0:.4f}s  entries={result_before.totalChanges} summaries={len(result_before.summaries)}")

    # --- after: hash/len 벡터화 + to_list ---
    def sectionsDiffFast(sections: pl.DataFrame) -> DiffResult:
        periods = _periodCols(sections)
        if len(periods) < 2:
            return DiffResult()

        hasChapter = "chapter" in sections.columns
        hasTopic = "topic" in sections.columns
        if not hasTopic:
            return DiffResult()

        # 1) hash + len 벡터화
        hashExprs = []
        lenExprs = []
        for p in periods:
            hashExprs.append(
                pl.when(pl.col(p).is_not_null())
                .then(pl.col(p).cast(pl.Utf8).hash())
                .otherwise(pl.lit(None, dtype=pl.UInt64))
                .alias(f"_h_{p}")
            )
            lenExprs.append(
                pl.when(pl.col(p).is_not_null())
                .then(pl.col(p).cast(pl.Utf8).str.len_bytes())
                .otherwise(pl.lit(None, dtype=pl.UInt32))
                .alias(f"_len_{p}")
            )

        work = sections.with_columns(hashExprs + lenExprs)

        # 2) 컬럼별 to_list()로 추출 (iter_rows(named=True) 대비 ~5x 빠름)
        topicList = work.get_column("topic").to_list()
        chapterList = work.get_column("chapter").to_list() if hasChapter else [None] * work.height

        hashLists = {p: work.get_column(f"_h_{p}").to_list() for p in periods}
        lenLists = {p: work.get_column(f"_len_{p}").to_list() for p in periods}

        entries = []
        summaries = []

        for rowIdx in range(work.height):
            topic = topicList[rowIdx]
            if not topic:
                continue
            chapter = chapterList[rowIdx]

            prevHash = None
            prevPeriod = None
            changedCount = 0
            totalPeriods = 0

            for p in periods:
                h = hashLists[p][rowIdx]
                if h is None:
                    continue
                totalPeriods += 1

                if prevHash is not None and prevPeriod is not None:
                    if h != prevHash:
                        changedCount += 1
                        entries.append(DiffEntry(
                            topic=topic,
                            chapter=chapter,
                            fromPeriod=prevPeriod,
                            toPeriod=p,
                            status="CHANGED",
                            fromLen=lenLists[prevPeriod][rowIdx] or 0,
                            toLen=lenLists[p][rowIdx] or 0,
                        ))

                prevHash = h
                prevPeriod = p

            summaries.append(DiffSummary(
                topic=topic,
                chapter=chapter,
                totalPeriods=totalPeriods,
                changedCount=changedCount,
                stableCount=max(0, totalPeriods - 1 - changedCount),
            ))

        return DiffResult(entries=entries, summaries=summaries)

    times_after = []
    for i in range(3):
        t0 = time.perf_counter()
        result_after = sectionsDiffFast(sec)
        t1 = time.perf_counter()
        times_after.append(t1 - t0)
        print(f"  after  #{i+1}: {t1-t0:.4f}s  entries={result_after.totalChanges} summaries={len(result_after.summaries)}")

    # 동일성 검증
    assert result_before.totalChanges == result_after.totalChanges, \
        f"entries 수 불일치: {result_before.totalChanges} vs {result_after.totalChanges}"
    assert len(result_before.summaries) == len(result_after.summaries), \
        f"summaries 수 불일치"

    for b, a in zip(result_before.summaries, result_after.summaries):
        assert b.topic == a.topic, f"topic 불일치: {b.topic} vs {a.topic}"
        assert b.changedCount == a.changedCount, f"changedCount 불일치 ({b.topic}): {b.changedCount} vs {a.changedCount}"
        assert b.totalPeriods == a.totalPeriods, f"totalPeriods 불일치 ({b.topic}): {b.totalPeriods} vs {a.totalPeriods}"

    print("\n  동일성 검증 OK")

    speedup = sum(times_before) / sum(times_after) if sum(times_after) > 0 else float("inf")
    print(f"\n  avg: {sum(times_before)/3:.4f}s → {sum(times_after)/3:.4f}s ({speedup:.1f}x)")


if __name__ == "__main__":
    main()
