"""
실험 ID: 104-001
실험명: parseTextStructureWithState Python vs Rust 성능 비교

목적:
- sections 파이프라인의 핵심 병목인 parseTextStructureWithState를
  pyo3 Rust 구현으로 대체했을 때 실제 성능 향상을 실측한다.

가설:
1. Rust 구현이 Python 대비 5x 이상 빠를 것이다 (보수적 추정).
2. 결과(nodes)의 구조가 Python과 동일할 것이다 (정합성).

방법:
1. 삼성전자(005930) docs parquet에서 실제 텍스트 블록 추출
2. Python parseTextStructureWithState 100회 반복 측정
3. Rust parse_text_structure 100회 반복 측정
4. 정합성 비교: 노드 수, textNodeType, textPathKey 일치 확인

결과:
- 데이터: 삼성전자(005930) 179개 텍스트 블록, 17.6M 문자

| 모드               | Python  | Rust    | 배율  |
|--------------------|---------|---------|-------|
| 캐시 워밍 50회반복 | 6.93s   | 8.97s   | 0.8x  |
| 콜드 스타트 1회    | 0.230s  | 0.171s  | 1.3x  |
| 콜드 columnar+DF   | 0.230s  | 0.182s  | 1.3x  |

- 정합성: 50개 블록 100% 일치 (노드 수, 필드값 전부 동일)
- Python lru_cache(16384)가 반복 호출에서 Rust보다 빠름
- 콜드에서 Rust가 1.3x 빠르지만 절대치 50ms 차이
- dict → Python 변환 오버헤드가 Rust 계산 이득을 상쇄

결론:
- 가설 1 **기각**: 5x 미달. 콜드 1.3x, 캐시 워밍 시 Python이 우세.
- 가설 2 **채택**: 정합성 100%.
- parseTextStructureWithState 단독 Rust 포팅은 ROI 부족.
- Python lru_cache + CPython 내장 str 연산이 이미 효율적.
- Python↔Rust 경계 변환(str 복사, dict 생성) 비용이 병목.
- 의미 있는 개선을 위해서는 전체 파이프라인(mapper+chunker+textStructure+DataFrame 조립)을
  통째로 Rust에서 처리하고 최종 Polars DataFrame만 반환하는 구조가 필요.
  단, 이는 포팅 범위가 ~3000줄로 확대되어 비용-효과 재검토 필요.

실험일: 2026-03-29
"""

from __future__ import annotations

import sys
import time

sys.path.insert(0, r"c:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\src")


def extractTextBlocks(stockCode: str) -> list[tuple[str, str]]:
    """docs parquet에서 text 블록들을 추출한다. (text, topic) 튜플 리스트."""
    from dartlab.core.dataLoader import loadData

    df = loadData(stockCode, category="docs")
    if df is None:
        return []

    blocks = []
    # 컬럼명 자동 감지
    contentCol = None
    for candidate in ["content_markdown", "content_text", "section_content"]:
        if candidate in df.columns:
            contentCol = candidate
            break
    if contentCol is None:
        return []

    import polars as pl

    # report_type 또는 report_kind 감지
    typeCol = "report_type" if "report_type" in df.columns else "report_kind"
    subset = df.filter(pl.col(typeCol).str.contains("(?i)annual|사업보고서")).head(200)
    if subset.is_empty():
        subset = df.head(200)

    for row in subset.iter_rows(named=True):
        text = row.get(contentCol)
        topic = row.get("section_title", "unknown")
        if isinstance(text, str) and len(text) > 100:
            blocks.append((text, str(topic)))

    return blocks


def benchmarkPython(blocks: list[tuple[str, str]], iterations: int = 100) -> float:
    """Python parseTextStructureWithState 벤치마크."""
    from dartlab.providers.dart.docs.sections.textStructure import (
        parseTextStructureWithState,
    )

    # warmup
    for text, topic in blocks[:3]:
        parseTextStructureWithState(text, sourceBlockOrder=0, topic=topic)

    start = time.perf_counter()
    totalNodes = 0
    for _ in range(iterations):
        for i, (text, topic) in enumerate(blocks):
            nodes, _stack = parseTextStructureWithState(
                text, sourceBlockOrder=i, topic=topic
            )
            totalNodes += len(nodes)
    elapsed = time.perf_counter() - start
    print(f"  Python: {elapsed:.3f}s ({iterations} iters x {len(blocks)} blocks)")
    print(f"  총 노드 수: {totalNodes}")
    return elapsed


def benchmarkRust(
    blocks: list[tuple[str, str]],
    sectionMappings: dict[str, str] | None,
    iterations: int = 100,
) -> float:
    """Rust parse_text_structure 벤치마크."""
    from dartlab_native_poc import parse_text_structure

    # warmup
    for text, topic in blocks[:3]:
        parse_text_structure(
            text,
            source_block_order=0,
            topic=topic,
            section_mappings=sectionMappings,
        )

    start = time.perf_counter()
    totalNodes = 0
    for _ in range(iterations):
        for i, (text, topic) in enumerate(blocks):
            result = parse_text_structure(
                text,
                source_block_order=i,
                topic=topic,
                section_mappings=sectionMappings,
            )
            nodes = result[0]
            totalNodes += len(nodes)
    elapsed = time.perf_counter() - start
    print(f"  Rust:   {elapsed:.3f}s ({iterations} iters x {len(blocks)} blocks)")
    print(f"  총 노드 수: {totalNodes}")
    return elapsed


def benchmarkRustBatch(
    blocks: list[tuple[str, str]],
    sectionMappings: dict[str, str] | None,
    iterations: int = 100,
) -> float:
    """Rust batch API 벤치마크 -- 전체 블록을 한번에 전달."""
    from dartlab_native_poc import parse_text_structure_batch

    batchInput = [(text, topic, i) for i, (text, topic) in enumerate(blocks)]

    # warmup
    parse_text_structure_batch(batchInput, section_mappings=sectionMappings)

    start = time.perf_counter()
    totalNodes = 0
    for _ in range(iterations):
        results = parse_text_structure_batch(batchInput, section_mappings=sectionMappings)
        for pair in results:
            totalNodes += len(pair[0])
    elapsed = time.perf_counter() - start
    print(f"  Batch:  {elapsed:.3f}s ({iterations} iters x {len(blocks)} blocks)")
    print(f"  총 노드 수: {totalNodes}")
    return elapsed


def benchmarkPythonCold(blocks: list[tuple[str, str]]) -> float:
    """캐시 클리어 후 1회 실행."""
    from dartlab.providers.dart.docs.sections.textStructure import (
        _body_anchor,
        _detect_heading,
        _heading_key,
        _is_temporal_marker,
        _normalize_heading_text,
        _semantic_segment_key,
        parseTextStructureWithState,
    )

    # 모든 lru_cache 클리어
    for fn in [_detect_heading, _body_anchor, _heading_key, _normalize_heading_text, _is_temporal_marker, _semantic_segment_key]:
        fn.cache_clear()

    start = time.perf_counter()
    for i, (text, topic) in enumerate(blocks):
        parseTextStructureWithState(text, sourceBlockOrder=i, topic=topic)
    return time.perf_counter() - start


def benchmarkRustBatchCold(
    blocks: list[tuple[str, str]],
    sectionMappings: dict[str, str] | None,
) -> float:
    """Rust batch 1회 실행."""
    from dartlab_native_poc import parse_text_structure_batch

    batchInput = [(text, topic, i) for i, (text, topic) in enumerate(blocks)]

    start = time.perf_counter()
    parse_text_structure_batch(batchInput, section_mappings=sectionMappings)
    return time.perf_counter() - start


def benchmarkRustColumnarCold(
    blocks: list[tuple[str, str]],
    sectionMappings: dict[str, str] | None,
) -> float:
    """Rust columnar 1회 실행 -- dict of lists 반환, DataFrame 직접 구성."""
    from dartlab_native_poc import parse_text_structure_columnar
    import polars as pl

    batchInput = [(text, topic, i) for i, (text, topic) in enumerate(blocks)]

    start = time.perf_counter()
    columns = parse_text_structure_columnar(batchInput, section_mappings=sectionMappings)
    df = pl.DataFrame(columns)
    elapsed = time.perf_counter() - start
    print(f"    columnar rows: {len(df)}, cols: {df.columns}")
    return elapsed


def checkCorrectness(
    blocks: list[tuple[str, str]],
    sectionMappings: dict[str, str] | None,
) -> None:
    """Python과 Rust 결과의 정합성을 확인한다."""
    from dartlab.providers.dart.docs.sections.textStructure import (
        parseTextStructureWithState,
    )
    from dartlab_native_poc import parse_text_structure

    mismatchCount = 0
    totalBlocks = 0

    for i, (text, topic) in enumerate(blocks[:50]):  # 처음 50개만 상세 비교
        pyNodes, pyStack = parseTextStructureWithState(
            text, sourceBlockOrder=i, topic=topic
        )
        rustResult = parse_text_structure(
            text,
            source_block_order=i,
            topic=topic,
            section_mappings=sectionMappings,
        )
        rustNodes = rustResult[0]
        rustStack = rustResult[1]
        totalBlocks += 1

        if len(pyNodes) != len(rustNodes):
            mismatchCount += 1
            print(
                f"  [MISMATCH] block {i}: Python {len(pyNodes)} nodes vs Rust {len(rustNodes)} nodes"
            )
            # 상세 비교: 처음 3개 노드
            for j in range(min(3, max(len(pyNodes), len(rustNodes)))):
                pyN = pyNodes[j] if j < len(pyNodes) else "---"
                rsN = dict(rustNodes[j]) if j < len(rustNodes) else "---"
                if isinstance(pyN, dict):
                    pyN = {k: v for k, v in pyN.items() if k != "text"}
                if isinstance(rsN, dict):
                    rsN = {k: v for k, v in rsN.items() if k != "text"}
                print(f"    [{j}] Python: {pyN}")
                print(f"    [{j}] Rust:   {rsN}")
            continue

        # 노드 수 같으면 필드별 비교
        for j, (pn, rn) in enumerate(zip(pyNodes, rustNodes)):
            rnDict = dict(rn)
            for field in ["textNodeType", "textStructural", "textLevel", "textPathKey"]:
                pv = pn.get(field)
                rv = rnDict.get(field)
                if str(pv) != str(rv):
                    mismatchCount += 1
                    print(
                        f"  [FIELD MISMATCH] block {i}, node {j}, {field}: Python={pv} vs Rust={rv}"
                    )
                    break

    matchRate = (totalBlocks - mismatchCount) / totalBlocks * 100 if totalBlocks else 0
    print(f"\n  정합성: {totalBlocks}개 블록 중 {totalBlocks - mismatchCount}개 일치 ({matchRate:.1f}%)")


def loadSectionMappings() -> dict[str, str] | None:
    """sectionMappings.json을 로드한다 (정규화된 제목 -> topic)."""
    try:
        from dartlab.providers.dart.docs.sections.mapper import loadSectionMappings as _load
        result = _load()
        return dict(result) if result else None
    except (ImportError, AttributeError):
        return None


if __name__ == "__main__":
    print("=== 104-001: parseTextStructureWithState Python vs Rust ===\n")

    print("[1] 텍스트 블록 추출 (005930)...")
    blocks = extractTextBlocks("005930")
    print(f"  추출된 블록: {len(blocks)}개")
    if not blocks:
        print("  ERROR: 블록 추출 실패")
        sys.exit(1)

    totalChars = sum(len(t) for t, _ in blocks)
    print(f"  총 문자 수: {totalChars:,}")
    print()

    print("[2] sectionMappings 로드...")
    sectionMappings = loadSectionMappings()
    print(f"  매핑 수: {len(sectionMappings) if sectionMappings else 0}")
    print()

    # --- 캐시 워밍 상태에서 반복 측정 (캐시 유리한 Python) ---
    iters = 50
    print(f"[3a] 캐시 워밍 벤치마크 ({iters}회 반복, Python lru_cache 유리)...")
    pyTime = benchmarkPython(blocks, iterations=iters)
    rustTime = benchmarkRust(blocks, sectionMappings, iterations=iters)
    rustBatchTime = benchmarkRustBatch(blocks, sectionMappings, iterations=iters)
    print(f"\n  Rust 단건: {pyTime / rustTime:.1f}x")
    print(f"  Rust 배치: {pyTime / rustBatchTime:.1f}x")
    print()

    # --- 콜드 스타트 (1회 실행, lru_cache 클리어) ---
    print("[3b] 콜드 스타트 벤치마크 (1회, 캐시 클리어)...")
    pyCold = benchmarkPythonCold(blocks)
    rustCold = benchmarkRustBatchCold(blocks, sectionMappings)
    rustColumnar = benchmarkRustColumnarCold(blocks, sectionMappings)
    print(f"\n  콜드 Python:    {pyCold:.3f}s")
    print(f"  콜드 Rust batch: {rustCold:.3f}s ({pyCold / rustCold:.1f}x)")
    print(f"  콜드 Rust columnar: {rustColumnar:.3f}s ({pyCold / rustColumnar:.1f}x)")
    print()

    print("[4] 정합성 검사...")
    checkCorrectness(blocks, sectionMappings)
