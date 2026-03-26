"""실험 ID: 093-003
실험명: 2-pass 방식 sections 메모리 최적화 PoC

목적:
- 현재 sections()는 모든 period의 text를 topicMap dict에 축적 → 490MB 피크
- 2-pass 방식: Pass 1에서 메타만 축적, Pass 2에서 텍스트를 한 번만 회수
- 단, _expandStructuredRows가 text를 sub-segment로 분해하므로
  원본 rowIdx로 직접 참조 불가 → 대안 전략 필요

가설:
1. Pass 1(구조분석)에서 text를 읽되 topicMap에 축적 안 하면 피크 ~300MB
2. text는 period별로 처리 후 즉시 해제하면 동시 보유가 1 period분으로 제한
3. 최종 DataFrame 구성을 period별 column 단위로 하면 이중 보유 제거

방법:
1. 기존 sections()를 복제하여 "period별 즉시 column화" 방식으로 변경
2. topicMap[key][period] = text 대신, period 처리 완료 시
   해당 period의 text를 바로 result dict의 column으로 넣고 나머지 해제
3. psutil RSS로 각 단계 피크 측정

결과 (실험 후 작성):
| 지표              | 기존 방식  | 2-pass PoC | 변화       |
|-------------------|-----------|------------|-----------|
| 피크 RSS          | ~491MB    | 494.4MB    | +3MB (악화)|
| 소요 시간         | 3.33s     | 9.22s      | +177% (악화)|
| 최종 RSS          | +221MB    | 469.8MB    | 동급       |
| DataFrame shape   | (8599,70) | (8599,44)  | 컬럼 수 다름|
| DataFrame size    | -         | 89.42MB    | -         |

- load 단계에서 이미 404.9MB → iterPeriodSubsets가 parquet 전체를 Polars로 로드
- periodColumns에 모든 period의 text를 동시 보유 → topicMap과 본질적으로 동일
- period별 pop()으로 해제해도, 이미 모든 period text가 메모리에 올라온 후임
- DataFrame shape 차이(44 vs 70): 메타 컬럼(pathVariants, cadence 등) 미구현

결론:
- **가설 기각**: periodColumns 방식은 topicMap과 메모리 패턴이 동일하다.
  text를 Python str로 추출하는 시점(iter_rows → _expandStructuredRows)에서
  이미 Python heap에 복제되므로, dict 구조를 바꿔도 동시 보유량은 줄지 않는다.
- 근본 문제는 "모든 period의 text를 Python heap에 동시 보유"하는 것이며,
  이를 해결하려면:
  (1) text를 Python str로 추출하지 않고 Polars Series 안에서 처리하거나
  (2) period별로 parquet를 분리 로드하여 1개 period씩만 Python heap에 올리거나
  (3) text structure 분석 자체를 Rust/native로 옮겨야 한다.
- iterPeriodSubsets 내부에서 parquet 전체(150MB+)가 Rust heap에 로드되는 것도
  불가피한 오버헤드 — scan_parquet predicate pushdown으로도 body text가 96%이므로 효과 없음.
- 속도도 2.8배 느려짐 (3.33s → 9.22s) — 기존 방식보다 모든 면에서 열위.

실험일: 2026-03-24
"""

import gc
import os
import sys
import time

sys.path.insert(0, "src")


def getRssMb() -> float:
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


def sectionsOptimized(stockCode: str):
    """period별 즉시 column화 방식 — topicMap에 text 축적 안 함."""
    import polars as pl
    from dartlab.providers.dart.docs.sections.pipeline import (
        _comparablePathInfo,
        _expandStructuredRows,
        _reportRowsToTopicRows,
        _rowCadenceMeta,
        iterPeriodSubsets,
    )
    from dartlab.providers.dart.docs.sections.runtime import (
        applyProjections,
        chapterFromMajorNum,
        chapterTeacherTopics,
        detailTopicForTopic,
        projectionSuppressedTopics,
    )
    from dartlab.providers.dart.docs.sections._common import sortPeriods

    # --- Pass 1: 구조 분석 + period별 text 즉시 column 구성 ---
    # key = (topic, segmentKey)
    # keyMeta: 메타데이터 (chapter, blockType, textPath 등)
    # periodColumns: {period: {key: text}} — period별로 독립, 이전 period는 해제
    keyMeta: dict[tuple[str, str], dict[str, object]] = {}
    rowOrder: dict[tuple[str, str], dict[str, int]] = {}
    pathVariantsByKey: dict[tuple[str, str], set[str]] = {}
    parentPathVariantsByKey: dict[tuple[str, str], set[str]] = {}
    semanticPathVariantsByKey: dict[tuple[str, str], set[str]] = {}
    semanticParentPathVariantsByKey: dict[tuple[str, str], set[str]] = {}

    # 핵심 차이: periodColumns는 {period: {key: text}} 형태로,
    # period 처리 완료 시 해당 period의 dict만 보유
    periodColumns: dict[str, dict[tuple[str, str], str]] = {}

    periodRows: dict[str, list[dict[str, object]]] = {}
    validPeriods: list[str] = []
    latestAnnualRows = None
    suppressed = projectionSuppressedTopics()

    topicChapter: dict[str, str] = {}
    topicFirstSeq: dict[str, tuple[int, int]] = {}

    rssBeforeLoop = getRssMb()
    peakRss = rssBeforeLoop

    for periodKey, reportKind, ccol, subset in iterPeriodSubsets(stockCode):
        validPeriods.append(periodKey)
        topicRows = _reportRowsToTopicRows(subset, ccol)
        periodRows[periodKey] = topicRows
        if reportKind == "annual" and latestAnnualRows is None:
            latestAnnualRows = topicRows

    teacherTopics = chapterTeacherTopics(latestAnnualRows or [])
    validPeriods = sortPeriods(validPeriods)
    latestPeriod = validPeriods[-1] if validPeriods else ""

    rssAfterLoad = getRssMb()
    peakRss = max(peakRss, rssAfterLoad)
    print(f"[load 완료] RSS: {rssAfterLoad:.1f}MB (peak: {peakRss:.1f}MB)")

    def _representativePeriodRank(period):
        if not isinstance(period, str):
            return -1
        year = int(period[:4])
        quarter = {"Q1": 1, "Q2": 2, "Q3": 3}.get(period[4:], 4)
        return (year * 10) + quarter

    for _pIdx, periodKey in enumerate(validPeriods):
        projected = applyProjections(
            periodRows.pop(periodKey, []),
            teacherTopics,
        )
        # 이 period의 text를 임시 dict에 축적 (이전 period 것은 이미 periodColumns에 저장됨)
        periodTextMap: dict[tuple[str, str], str] = {}

        for row in _expandStructuredRows(projected):
            chapter = row["chapter"]
            topic = row["topic"]
            text = row["text"]
            blockType = row.get("blockType", "text")
            segmentKey = row.get("segmentKey")
            if not isinstance(chapter, str) or not isinstance(topic, str) or not isinstance(text, str):
                continue
            if not isinstance(blockType, str):
                blockType = "text"
            if not isinstance(segmentKey, str) or not segmentKey:
                continue
            if topic not in topicChapter:
                topicChapter[topic] = chapter
            if topic in suppressed.get(chapter, set()):
                continue
            if detailTopicForTopic(topic) is not None:
                continue

            key = (topic, segmentKey)
            # text를 period별 임시 dict에만 넣음 (topicMap 없음!)
            periodTextMap[key] = text

            # 메타데이터 축적 (text 제외)
            comparablePathKey, comparableParentPathKey = _comparablePathInfo(
                topic,
                str(row.get("textSemanticPathKey") or row.get("textPathKey") or "") or None,
            )
            majorNum = int(row.get("majorNum", 99))
            sortOrder = int(row.get("sortOrder", 999999))
            if topic not in topicFirstSeq or (majorNum, sortOrder) < topicFirstSeq[topic]:
                topicFirstSeq[topic] = (majorNum, sortOrder)

            orderInfo = rowOrder.setdefault(
                key,
                {
                    "latestRank": 999999999,
                    "latestMissing": 1,
                    "firstRank": 999999999,
                    "sourceBlockOrder": int(row.get("sourceBlockOrder") or 0),
                    "segmentOrder": int(row.get("segmentOrder") or 0),
                    "segmentOccurrence": int(row.get("segmentOccurrence") or 1),
                },
            )
            orderInfo["firstRank"] = min(orderInfo["firstRank"], sortOrder)
            orderInfo["sourceBlockOrder"] = min(orderInfo["sourceBlockOrder"], int(row.get("sourceBlockOrder") or 0))
            orderInfo["segmentOrder"] = min(orderInfo["segmentOrder"], int(row.get("segmentOrder") or 0))
            orderInfo["segmentOccurrence"] = min(orderInfo["segmentOccurrence"], int(row.get("segmentOccurrence") or 1))
            if periodKey == latestPeriod:
                orderInfo["latestMissing"] = 0
                orderInfo["latestRank"] = min(orderInfo["latestRank"], sortOrder)

            if isinstance(row.get("textPathKey"), str) and row.get("textPathKey"):
                pathVariantsByKey.setdefault(key, set()).add(str(row["textPathKey"]))
            if isinstance(row.get("textParentPathKey"), str) and row.get("textParentPathKey"):
                parentPathVariantsByKey.setdefault(key, set()).add(str(row["textParentPathKey"]))
            if isinstance(row.get("textSemanticPathKey"), str) and row.get("textSemanticPathKey"):
                semanticPathVariantsByKey.setdefault(key, set()).add(str(row["textSemanticPathKey"]))
            if isinstance(row.get("textSemanticParentPathKey"), str) and row.get("textSemanticParentPathKey"):
                semanticParentPathVariantsByKey.setdefault(key, set()).add(str(row["textSemanticParentPathKey"]))

            prevMeta = keyMeta.get(key)
            prevRank = _representativePeriodRank(prevMeta.get("_repPeriod")) if isinstance(prevMeta, dict) else -1
            currRank = _representativePeriodRank(periodKey)
            if prevMeta is None or currRank >= prevRank:
                keyMeta[key] = {
                    "chapter": chapter,
                    "topic": topic,
                    "blockType": blockType,
                    "sourceBlockOrder": int(row.get("sourceBlockOrder") or 0),
                    "textNodeType": row.get("textNodeType"),
                    "textStructural": row.get("textStructural"),
                    "textLevel": int(row["textLevel"]) if isinstance(row.get("textLevel"), int) else None,
                    "textPath": row.get("textPath"),
                    "textPathKey": row.get("textPathKey"),
                    "textParentPathKey": row.get("textParentPathKey"),
                    "textSemanticPathKey": row.get("textSemanticPathKey"),
                    "textSemanticParentPathKey": row.get("textSemanticParentPathKey"),
                    "textComparablePathKey": comparablePathKey,
                    "textComparableParentPathKey": comparableParentPathKey,
                    "segmentKey": segmentKey,
                    "segmentOrder": int(row.get("segmentOrder") or 0),
                    "segmentOccurrence": int(row.get("segmentOccurrence") or 1),
                    "sourceTopic": row.get("sourceTopic"),
                    "_repPeriod": periodKey,
                }

        # period 처리 완료 → periodTextMap을 periodColumns에 저장
        periodColumns[periodKey] = periodTextMap
        # projected, subset 등은 루프 스코프에서 자동 해제

        currentRss = getRssMb()
        peakRss = max(peakRss, currentRss)

        if _pIdx % 4 == 3:
            gc.collect()

    del periodRows
    gc.collect()

    rssAfterPass1 = getRssMb()
    peakRss = max(peakRss, rssAfterPass1)
    print(f"[Pass1 완료] RSS: {rssAfterPass1:.1f}MB (peak: {peakRss:.1f}MB)")
    print(f"  keys: {len(keyMeta)}, periods: {len(validPeriods)}")

    if not validPeriods or not keyMeta:
        return None

    # --- DataFrame 구성 (topicMap 없이, periodColumns에서 직접) ---
    cadenceMetaByKey = {}
    for key in keyMeta:
        pMap = {}
        for p in validPeriods:
            if key in periodColumns.get(p, {}):
                pMap[p] = periodColumns[p][key]
        cadenceMetaByKey[key] = _rowCadenceMeta(pMap)

    # 정렬
    topicIndex = {}
    for topic_seq in sorted(topicFirstSeq.items(), key=lambda x: x[1]):
        topicIndex[topic_seq[0]] = len(topicIndex)

    topicKeysByTopic: dict[str, list[tuple[str, str]]] = {}
    for key in keyMeta:
        topicKeysByTopic.setdefault(key[0], []).append(key)

    _CADENCE_SCOPE_PRIORITY = {"mixed": 0, "annual": 1, "quarterly": 2, "none": 3}

    def _topicRowSortKey(k):
        topic, _ = k
        majorNum, firstSeq = topicFirstSeq.get(topic, (99, 999999))
        tIdx = topicIndex.get(topic, 999999)
        info = rowOrder.get(k, {})
        cadenceMeta = cadenceMetaByKey.get(k, {})
        return (
            majorNum, firstSeq, tIdx,
            _CADENCE_SCOPE_PRIORITY.get(str(cadenceMeta.get("cadenceScope") or "none"), 9),
            int(info.get("latestMissing", 1)),
            int(info.get("latestRank", 999999999)),
            int(info.get("firstRank", 999999999)),
            int(info.get("segmentOccurrence", 1)),
            str(k[1]),
        )

    # period 컬럼 구축 — periodColumns에서 직접
    sortedTopics = [topic for topic, _ in sorted(topicFirstSeq.items(), key=lambda x: x[1])]
    orderedKeys: list[tuple[str, str]] = []
    for topic in sortedTopics:
        topicKeys = sorted(topicKeysByTopic.get(topic, []), key=_topicRowSortKey)
        orderedKeys.extend(topicKeys)

    # period별로 column 데이터를 구성하며 해당 period의 periodColumns 즉시 해제
    periodColData: dict[str, list[str | None]] = {}
    for period in validPeriods:
        pTextMap = periodColumns.pop(period, {})
        col = []
        for key in orderedKeys:
            col.append(pTextMap.get(key))
        periodColData[period] = col
        del pTextMap
        gc.collect()

    del periodColumns
    gc.collect()

    rssAfterPeriodCols = getRssMb()
    peakRss = max(peakRss, rssAfterPeriodCols)
    print(f"[period cols 완료] RSS: {rssAfterPeriodCols:.1f}MB (peak: {peakRss:.1f}MB)")

    # 메타 컬럼 구성
    nRows = len(orderedKeys)
    metaData = {
        "topic": [k[0] for k in orderedKeys],
        "segmentKey": [str(keyMeta.get(k, {}).get("segmentKey") or "") for k in orderedKeys],
        "chapter": [topicChapter.get(k[0]) for k in orderedKeys],
        "blockType": [str(keyMeta.get(k, {}).get("blockType") or "text") for k in orderedKeys],
    }

    # 합치기
    allData = {**metaData, **periodColData}
    del metaData, periodColData
    gc.collect()

    result = pl.DataFrame(allData)
    del allData
    gc.collect()

    rssAfterDf = getRssMb()
    peakRss = max(peakRss, rssAfterDf)
    print(f"[DataFrame 생성 후] RSS: {rssAfterDf:.1f}MB (peak: {peakRss:.1f}MB)")

    return result, peakRss


def measure(stockCode: str):
    gc.collect()
    rssStart = getRssMb()
    print(f"[시작] RSS: {rssStart:.1f}MB")

    t0 = time.perf_counter()
    result = sectionsOptimized(stockCode)
    elapsed = time.perf_counter() - t0

    if result is None:
        print("결과 없음")
        return

    df, peakRss = result
    gc.collect()
    rssEnd = getRssMb()

    print(f"\n=== 2-pass PoC 결과 ({stockCode}) ===")
    print(f"소요 시간: {elapsed:.2f}s")
    print(f"피크 RSS: {peakRss:.1f}MB")
    print(f"최종 RSS: {rssEnd:.1f}MB")
    print(f"DataFrame shape: {df.shape}")
    print(f"DataFrame estimated_size: {df.estimated_size() / 1024 / 1024:.2f}MB")

    # 기존 방식과 비교
    print("\n--- 기존 방식 비교 실행 ---")
    gc.collect()
    rssBeforeOrig = getRssMb()

    from dartlab.providers.dart.docs.sections.pipeline import sections
    t1 = time.perf_counter()
    origDf = sections(stockCode)
    elapsedOrig = time.perf_counter() - t1

    gc.collect()
    rssAfterOrig = getRssMb()

    print(f"기존 소요 시간: {elapsedOrig:.2f}s")
    print(f"기존 RSS 증가: {rssAfterOrig - rssBeforeOrig:.1f}MB")
    if origDf is not None:
        print(f"기존 DataFrame shape: {origDf.shape}")


if __name__ == "__main__":
    stockCode = sys.argv[1] if len(sys.argv) > 1 else "005930"
    measure(stockCode)
