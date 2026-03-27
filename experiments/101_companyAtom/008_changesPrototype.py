"""
실험 ID: 101-008
실험명: c.changes 프로토타입 — 형태와 속도 측정

목적:
- changes가 DataFrame인지 다른 형태인지 결정
- sections → changes 변환 속도 측정
- 사용자가 실제로 어떻게 쓸지 시뮬레이션

가설:
1. sections → changes 변환이 1초 이내
2. changes는 DataFrame이 자연스러움 (Polars 생태계 유지)

방법:
1. sections에서 변화 블록만 추출 → DataFrame으로 구성
2. 변환 시간 측정
3. 사용 시나리오 시뮬레이션

결과 (2026-03-27):
- 변환 속도: 첫 호출 4.6초 (hash 캐시 워밍), 이후 1.4초. 평균 2.5초
- changes DataFrame: 22,060행 × 10열 = 6.59 MB
- sections 대비: 79.3% 크기 (sections 8.32MB vs changes 6.59MB)
- 컬럼: fromPeriod, toPeriod, topic, pathKey, blockType, changeType, sizeA, sizeB, sizeDelta, preview
- Polars 네이티브 필터/집계 완벽 동작:
  - group_by(changeType) → 전체 요약 즉시
  - filter(fromPeriod=="2023") → 특정 기간 변화 즉시
  - filter(topic=="businessOverview") → topic 이력 즉시
  - filter(preview.str.contains("AI")) → 키워드 검색 즉시

결론:
- 가설 1 부분 확인: 첫 호출 4.6초 (hash 때문), 이후 1.4초. 캐시하면 1초대
- 가설 2 확인: DataFrame이 자연스러움 — Polars filter/group_by/sort 그대로 사용 가능
- changes는 sections와 같은 DataFrame이되, "변화만 모은 것"
- 사용성이 매우 좋음: 10열짜리 flat table이라 Polars 조작이 직관적

실험일: 2026-03-27
"""

import sys
import time
import hashlib
import re

sys.path.insert(0, "c:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

PERIOD_RE = re.compile(r"^\d{4}$")


def classifyChange(textA, textB):
    """변화 유형."""
    if textA is None and textB is not None:
        return "appeared"
    if textA is not None and textB is None:
        return "disappeared"
    strippedA = re.sub(r"[\d,.]+", "N", textA)
    strippedB = re.sub(r"[\d,.]+", "N", textB)
    if strippedA == strippedB:
        return "numeric"
    lenA, lenB = len(textA), len(textB)
    if lenA > 0 and abs(lenB - lenA) / lenA > 0.5:
        return "structural"
    return "wording"


def buildChanges(sections):
    """sections → changes DataFrame 변환."""
    import polars as pl

    annualCols = sorted([c for c in sections.columns if PERIOD_RE.match(c)])
    topics = sections.get_column("topic").to_list()
    pathKeys = sections.get_column("textPathKey").to_list() if "textPathKey" in sections.columns else [""] * sections.height
    blockTypes = sections.get_column("blockType").to_list() if "blockType" in sections.columns else [""] * sections.height

    rows = []
    for i in range(len(annualCols) - 1):
        colA, colB = annualCols[i], annualCols[i + 1]
        for rowIdx in range(sections.height):
            textA = sections[rowIdx, colA]
            textB = sections[rowIdx, colB]
            if textA is None and textB is None:
                continue
            hashA = hashlib.md5(textA.encode("utf-8")).hexdigest() if textA else None
            hashB = hashlib.md5(textB.encode("utf-8")).hexdigest() if textB else None
            if hashA == hashB:
                continue

            changeType = classifyChange(textA, textB)
            sizeA = len(textA) if textA else 0
            sizeB = len(textB) if textB else 0

            rows.append({
                "fromPeriod": colA,
                "toPeriod": colB,
                "topic": topics[rowIdx],
                "pathKey": pathKeys[rowIdx],
                "blockType": blockTypes[rowIdx],
                "changeType": changeType,
                "sizeA": sizeA,
                "sizeB": sizeB,
                "sizeDelta": sizeB - sizeA,
                "preview": ((textB or textA) or "")[:200],
            })

    return pl.DataFrame(rows)


def run():
    import dartlab
    import polars as pl

    c = dartlab.Company("005930")
    sections = c.docs.sections

    # 1. 속도 측정
    print("=" * 60)
    print("1. sections → changes 변환 속도")
    print("=" * 60)

    times = []
    for trial in range(3):
        t0 = time.perf_counter()
        changes = buildChanges(sections)
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
        print(f"  시행 {trial+1}: {elapsed:.3f}초")

    avg = sum(times) / len(times)
    print(f"  평균: {avg:.3f}초")
    print()

    # 2. changes DataFrame 형상
    print("=" * 60)
    print("2. changes DataFrame 형상")
    print("=" * 60)
    print(f"  행: {changes.height}, 열: {changes.width}")
    print(f"  메모리: {changes.estimated_size('mb'):.2f} MB")
    print(f"  컬럼: {changes.columns}")
    print()
    print(changes.head(10))
    print()

    # 3. 사용 시나리오 시뮬레이션
    print("=" * 60)
    print("3. 사용 시나리오")
    print("=" * 60)

    # 3a. 전체 요약
    print("\n  [c.changes] 전체 요약:")
    summary = (
        changes
        .group_by("changeType")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
    )
    print(summary)

    # 3b. 특정 기간
    print("\n  [c.changes.filter()] 2023→2024 변화:")
    period = changes.filter(
        (pl.col("fromPeriod") == "2023") & (pl.col("toPeriod") == "2024")
    )
    print(f"  {period.height}건")
    topicSummary = (
        period
        .group_by("topic", "changeType")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
        .head(10)
    )
    print(topicSummary)

    # 3c. 특정 topic 이력
    print("\n  [topic 필터] businessOverview 전체 변화:")
    biz = changes.filter(pl.col("topic") == "businessOverview")
    bizSummary = (
        biz
        .group_by("fromPeriod", "toPeriod")
        .agg([
            pl.len().alias("blocks"),
            pl.col("sizeDelta").sum().alias("totalDelta"),
        ])
        .sort("fromPeriod")
    )
    print(bizSummary)

    # 3d. structural만 (전략 전환 신호)
    print("\n  [changeType 필터] 구조적 재작성 (전략 전환):")
    structural = changes.filter(pl.col("changeType") == "structural")
    structSummary = (
        structural
        .group_by("fromPeriod", "toPeriod")
        .agg(pl.len().alias("count"))
        .sort("fromPeriod")
    )
    print(structSummary)

    # 3e. preview로 실제 내용 확인
    print("\n  [preview] AI 키워드 포함 변화:")
    aiChanges = changes.filter(pl.col("preview").str.contains("AI"))
    print(f"  {aiChanges.height}건")
    if aiChanges.height > 0:
        sample = aiChanges.select("fromPeriod", "toPeriod", "topic", "changeType", "preview").head(3)
        print(sample)

    # 4. sections vs changes 비교
    print()
    print("=" * 60)
    print("4. sections vs changes 비교")
    print("=" * 60)
    secMb = sections.estimated_size("mb")
    chgMb = changes.estimated_size("mb")
    print(f"  sections: {sections.height:,}행 × {sections.width}열 = {secMb:.2f} MB")
    print(f"  changes:  {changes.height:,}행 × {changes.width}열 = {chgMb:.2f} MB")
    print(f"  changes/sections: {chgMb/secMb*100:.1f}%")


if __name__ == "__main__":
    run()
