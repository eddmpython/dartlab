"""
실험 ID: 061-002
실험명: index 문서 순서 정렬 — I~XII장 순서 재현

목적:
- 현재 index가 소스별 나열인 것을 사업보고서 장 순서로 정렬
- sections의 행 순서(majorNum, seq)를 index에 반영
- finance/report를 해당 chapter 안의 적절한 위치에 삽입
- 정렬 결과가 실제 사업보고서 구조와 일치하는지 검증

가설:
1. sections 행 번호(enumerate) = 문서 순서 보존
2. finance는 III장, report는 해당 chapter에 삽입 가능
3. 정렬 후 삼성전자 index가 I→II→III→...→XII 순서

방법:
1. sections DataFrame 로드 → 각 topic의 chapter/순서 추출
2. finance/report topics에 chapter/순서 부여
3. 전체 정렬키 (chapterOrder, subOrder)로 sort
4. 현재 index와 비교

결과 (실험 후 작성):
- 삼성전자 95행 index를 I~XII장 순서로 정렬 성공
- finance(★)가 III장에, report(◆)가 해당 chapter에 올바르게 삽입
- topic 집합 현재 index와 동일 (누락/추가 없음)
- 발견: XII장에 미매핑 topic 대량 (sectionMappings 056 과제)
- 발견: _chapterMap()에 auditOpinion, outsideDirector 누락 → XII로 빠짐

결론:
- 정렬키 (chapterOrder, subOrder) 방식 채택
- sections DataFrame에 chapter 컬럼 추가 필요 (pipeline.py)
- _chapterMap() 하드코딩 보강 필요

실험일: 2026-03-14
"""

import sys
sys.path.insert(0, "src")

import polars as pl


def buildOrderedIndex(c):
    """문서 순서를 보존하는 index 구성."""
    from dartlab.engines.company.dart.docs.sections.chunker import parseMajorNum
    from dartlab.engines.company.dart.docs.sections.runtime import chapterFromMajorNum

    rows = []
    _CHAPTER_ORDER = {
        "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
        "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
        "XI": 11, "XII": 12,
    }

    sec = c.docs.sections
    sectionTopicOrder = {}
    if sec is not None and "topic" in sec.columns:
        for idx, topic in enumerate(sec["topic"].to_list()):
            if isinstance(topic, str) and topic:
                chapter = c._chapterForTopic(topic)
                chapterNum = _CHAPTER_ORDER.get(chapter, 12)
                sectionTopicOrder[topic] = (chapterNum, 100 + idx)

    financeStmts = []
    for stmtIdx, stmt in enumerate(("BS", "IS", "CIS", "CF", "SCE")):
        df = getattr(c, stmt, None)
        if df is None:
            continue
        periodCols = [col for col in df.columns if col not in ("account", "category", "metric") and not col.startswith("_")]
        periods = f"{periodCols[-1]}..{periodCols[0]}" if len(periodCols) > 1 else (periodCols[0] if periodCols else "-")
        financeStmts.append({
            "chapter": "III",
            "topic": stmt,
            "label": {"BS": "재무상태표", "IS": "손익계산서", "CIS": "포괄손익계산서", "CF": "현금흐름표", "SCE": "자본변동표"}.get(stmt, stmt),
            "kind": "finance",
            "source": "finance",
            "periods": periods,
            "shape": f"{df.height}x{df.width}",
            "_sortKey": (3, stmtIdx),
        })

    rsPair = c._ratioSeries() if c._hasFinance else None
    if rsPair is not None:
        series, years = rsPair
        financeStmts.append({
            "chapter": "III",
            "topic": "ratios",
            "label": "재무비율",
            "kind": "finance",
            "source": "finance",
            "periods": f"{years[-1]}..{years[0]}" if len(years) > 1 else "-",
            "shape": "-",
            "_sortKey": (3, 5),
        })

    docsRows = []
    if sec is not None and "topic" in sec.columns:
        periodCols = [col for col in sec.columns if col != "topic"]
        periodRange = f"{periodCols[-1]}..{periodCols[0]}" if len(periodCols) > 1 else "-"
        for idx, topic in enumerate(sec["topic"].to_list()):
            if not isinstance(topic, str) or not topic:
                continue
            chapter = c._chapterForTopic(topic)
            chapterNum = _CHAPTER_ORDER.get(chapter, 12)
            docsRows.append({
                "chapter": chapter,
                "topic": topic,
                "label": c._topicLabel(topic),
                "kind": "docs",
                "source": "docs",
                "periods": periodRange,
                "shape": "-",
                "_sortKey": (chapterNum, 100 + idx),
            })

    reportRows = []
    if c._hasReport:
        from dartlab.engines.company.dart.report.types import API_TYPES, API_TYPE_LABELS
        existingTopics = {r["topic"] for r in financeStmts + docsRows}
        for rIdx, apiType in enumerate(API_TYPES):
            if apiType in existingTopics:
                continue
            df = c.report.extract(apiType)
            if df is None or df.is_empty():
                continue
            chapter = c._chapterForTopic(apiType)
            chapterNum = _CHAPTER_ORDER.get(chapter, 12)
            reportRows.append({
                "chapter": chapter,
                "topic": apiType,
                "label": API_TYPE_LABELS.get(apiType, apiType),
                "kind": "report",
                "source": "report",
                "periods": "-",
                "shape": f"{df.height}x{df.width}",
                "_sortKey": (chapterNum, 200 + rIdx),
            })

    allRows = financeStmts + docsRows + reportRows
    allRows.sort(key=lambda r: r["_sortKey"])

    for r in allRows:
        del r["_sortKey"]

    return pl.DataFrame(allRows) if allRows else pl.DataFrame()


def main():
    from dartlab.engines.company.dart.company import Company

    c = Company("005930")

    print("=" * 80)
    print("현재 index (소스별 나열)")
    print("=" * 80)
    currentIdx = c.index
    print(f"shape: {currentIdx.shape}")
    for row in currentIdx.iter_rows(named=True):
        print(f"  {row['chapter']:<30} {row['topic']:<25} {row['kind']:<8} {row['source']}")

    print()
    print("=" * 80)
    print("새 index (문서 순서)")
    print("=" * 80)
    newIdx = buildOrderedIndex(c)
    print(f"shape: {newIdx.shape}")

    currentChapter = None
    for row in newIdx.iter_rows(named=True):
        ch = row["chapter"]
        if ch != currentChapter:
            currentChapter = ch
            print(f"\n  [{ch}]")
        marker = ""
        if row["kind"] == "finance":
            marker = " ★"
        elif row["kind"] == "report":
            marker = " ◆"
        print(f"    {row['topic']:<30} {row['kind']:<8} {row['label']}{marker}")

    print()
    print("=" * 80)
    print("비교")
    print("=" * 80)
    print(f"현재: {currentIdx.height}행")
    print(f"새:   {newIdx.height}행")

    currentTopics = set(currentIdx["topic"].to_list())
    newTopics = set(newIdx["topic"].to_list())
    missing = currentTopics - newTopics
    extra = newTopics - currentTopics
    if missing:
        print(f"누락: {missing}")
    if extra:
        print(f"추가: {extra}")
    if not missing and not extra:
        print("topic 집합 동일")


if __name__ == "__main__":
    main()
