"""실험 ID: 001
실험명: viewer() 기본 동작 검증

목적:
- sections DataFrame → viewer() dict 변환이 정상 동작하는지 확인
- 텍스트 블록의 diff 품질 확인 (의미 있는 변경이 잘 잡히는지)
- 테이블 블록의 cellDiffs 정확도 확인
- JSON 직렬화 가능 여부 확인
- 성능 측정 (< 500ms 목표)

가설:
1. viewer()가 sections의 모든 row를 block으로 변환할 수 있다
2. modified 블록의 diff가 단어 수준에서 의미 있는 변경을 잡는다
3. table 블록의 cellDiffs가 변경된 셀만 정확히 잡는다
4. 전체 처리 시간이 500ms 이내다

방법:
1. 삼성전자(005930) Company 생성
2. sections에서 topic 목록 확인
3. businessOverview에 대해 viewer() 호출
4. 결과 dict 구조, diff 품질, 성능 측정

결과 (실험 후 작성):
- 삼성전자 businessOverview: 162블록 (heading 88, text 38 modified, table 24 modified, added 3, removed 1)
- 성능: 381.6ms (목표 500ms 이내 — PASS)
- diff 품질: "30개 → 75개" 같은 숫자 변경, "또한 → 아울러" 같은 표현 변경 정확히 포착
- 테이블 cellDiffs: "제57기 반기 → 제57기 3분기", "26,331 → 42,522" 셀 단위 정확
- JSON 직렬화: 161,988bytes 성공
- 단독 뷰 (compare 없음): 161블록, status 없음 — 정상

결론:
- 채택. viewer()가 sections → 뷰어 dict 변환을 정상 수행.
- diff-match-patch 기반 단어 단위 diff가 사업보고서 텍스트에 적합.
- 테이블 셀 단위 비교도 정확. GUI에서 바로 소비 가능한 구조.
- 엔진 흡수 시 Company.viewer() 메서드로 노출 가능.

실험일: 2026-03-24
"""
import json
import time


def main():
    import dartlab

    print("=== viewer() 프로토타입 검증 ===\n")

    # 1. Company 생성
    t0 = time.perf_counter()
    c = dartlab.Company("005930")
    print(f"Company 생성: {time.perf_counter() - t0:.2f}s")

    # 2. sections 확인
    t1 = time.perf_counter()
    sec = c.docs.sections.raw
    print(f"sections 로드: {time.perf_counter() - t1:.2f}s")
    print(f"  rows: {sec.height}, cols: {sec.width}")

    # 기간 컬럼 확인
    import re
    periodCols = sorted([col for col in sec.columns if re.fullmatch(r"\d{4}(Q[1-4])?", col)], reverse=True)
    print(f"  periods: {periodCols[:6]}...")

    # topic 목록
    topics = sec.get_column("topic").unique().to_list()
    topics = [t for t in topics if t]
    print(f"  topics ({len(topics)}): {topics[:8]}...")

    # 3. viewer() 호출
    from dartlab.core.docs.viewer import viewer

    if len(periodCols) < 2:
        print("\n기간이 2개 미만 — 비교 불가")
        return

    basePeriod = periodCols[0]
    comparePeriod = periodCols[1]
    testTopic = "businessOverview" if "businessOverview" in topics else topics[0]

    print(f"\n--- viewer({testTopic}, {basePeriod}, {comparePeriod}) ---")
    t2 = time.perf_counter()
    doc = viewer(sec, testTopic, basePeriod, comparePeriod)
    elapsed = time.perf_counter() - t2
    print(f"  처리 시간: {elapsed*1000:.1f}ms")

    # 4. 결과 구조 확인
    print(f"\n--- 결과 요약 ---")
    print(f"  topic: {doc['topic']}")
    print(f"  basePeriod: {doc['basePeriod']}")
    print(f"  comparePeriod: {doc['comparePeriod']}")
    print(f"  availablePeriods: {doc['availablePeriods'][:6]}")
    print(f"  summary: {doc['summary']}")

    blocks = doc["blocks"]
    print(f"\n--- 블록 상세 (총 {len(blocks)}개) ---")
    for b in blocks[:15]:
        statusMark = {"added": "+", "removed": "-", "modified": "~", "unchanged": "=", None: " "}.get(b["status"], "?")
        kindMark = {"heading": "H", "text": "T", "table": "TB"}.get(b["kind"], "?")
        path = (b.get("path") or "")[:50]
        baseLen = len(str(b.get("base") or ""))
        diffCount = len(b.get("diff", []))
        cellDiffCount = len(b.get("cellDiffs", []))
        extra = ""
        if diffCount > 0:
            extra = f" diff:{diffCount}ops"
        if cellDiffCount > 0:
            extra = f" cellDiffs:{cellDiffCount}"
        print(f"  [{statusMark}] {kindMark} L{b.get('level') or '-'} | {path:<50} | base:{baseLen:>5}ch{extra}")

    # 5. diff 품질 확인 — modified 블록의 diff 내용
    modifiedBlocks = [b for b in blocks if b.get("status") == "modified" and b.get("diff")]
    if modifiedBlocks:
        print(f"\n--- diff 품질 확인 (modified 블록 {len(modifiedBlocks)}개 중 첫 2개) ---")
        for b in modifiedBlocks[:2]:
            print(f"\n  path: {b.get('path', '?')[:60]}")
            for op in b["diff"][:10]:
                marker = {"equal": "  ", "insert": "++", "delete": "--"}.get(op["type"], "??")
                text = op["text"][:80].replace("\n", "\\n")
                print(f"    {marker} {text}")
            if len(b["diff"]) > 10:
                print(f"    ... +{len(b['diff']) - 10}개 더")

    # 6. table cellDiffs 확인
    tableBlocks = [b for b in blocks if b.get("kind") == "table" and b.get("cellDiffs")]
    if tableBlocks:
        print(f"\n--- 테이블 cellDiffs (총 {len(tableBlocks)}개 테이블) ---")
        for b in tableBlocks[:2]:
            print(f"  path: {(b.get('path') or '?')[:60]}")
            for cd in b["cellDiffs"][:5]:
                print(f"    row:{cd['row']} col:{cd['col']} | '{cd['from'][:30]}' → '{cd['to'][:30]}'")

    # 7. JSON 직렬화 확인
    try:
        jsonStr = json.dumps(doc, ensure_ascii=False)
        print(f"\n--- JSON 직렬화 ---")
        print(f"  성공: {len(jsonStr):,}bytes")
    except (TypeError, ValueError) as e:
        print(f"\n--- JSON 직렬화 실패 ---")
        print(f"  {e}")

    # 8. 단독 뷰 (compare 없음)
    print(f"\n--- 단독 뷰 (compare 없음) ---")
    docSingle = viewer(sec, testTopic, basePeriod, None)
    print(f"  blocks: {len(docSingle['blocks'])}, summary: {docSingle['summary']}")

    # 9. 성능 요약
    print(f"\n=== 성능 요약 ===")
    print(f"  Company 생성: {time.perf_counter() - t0:.2f}s")
    print(f"  viewerDocument: {elapsed*1000:.1f}ms (목표: <500ms)")
    print(f"  {'PASS' if elapsed < 0.5 else 'FAIL'}: 성능 기준")


if __name__ == "__main__":
    main()
