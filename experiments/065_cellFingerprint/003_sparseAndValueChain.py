"""실험 ID: 065-003
실험명: sparse 실패의 원인 + 값 fingerprint 기반 행 매칭 PoC

목적:
- 10.9% sparse 실패의 실제 원인 파악 (항목명 불일치? 구조 변동?)
- kv/matrix에서 "값 fingerprint" 기반 행 매칭 가능성 검증
  - 같은 항목이 기간마다 다른 이름으로 등장할 때, 값 자체로 매칭
  - 예: "등기이사" (2024) == "사내이사" (2025) ← 값이 같으면 매칭

가설:
1. sparse 실패의 주요 원인은 항목명 미세 변동으로 인한 별개 항목 인식
2. 값 fingerprint(행 전체의 값 벡터)로 매칭하면 sparse 감소 가능
3. 숫자 값이 겹치는 경우 ambiguity가 높을 수 있음 (1, 2, 3 같은 값)

방법:
1. sparse 판정된 블록에서 실제 항목명/값 패턴 수집
2. 기간 간 항목명이 달라도 "값 벡터"가 유사한 행 찾기
3. 매칭 정확도, 충돌율 측정

결과 (실험 후 작성):

결론:

실험일: 2026-03-18
"""

import sys

sys.path.insert(0, r"C:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\src")

import re
from collections import Counter, defaultdict

import polars as pl

from dartlab.providers.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _headerCells,
    _isJunk,
    _normalizeItemName,
    _parseKeyValueOrMatrix,
    _parseMultiYear,
    splitSubtables,
)


def analyzeSparseBlocks(stockCode: str, stockName: str) -> list[dict]:
    """sparse 판정된 블록의 실제 항목명/값 패턴 수집."""
    from dartlab import Company
    c = Company(stockCode)

    if c.docs.sections is None:
        return []

    sections = c.docs.sections
    tableRows = sections.filter(pl.col("blockType") == "table")
    periodCols = sorted([col for col in tableRows.columns if re.match(r"\d{4}", col)])

    sparseBlocks = []
    topics = tableRows["topic"].unique().to_list()

    for topic in topics:
        topicRows = tableRows.filter(pl.col("topic") == topic)
        blockOrders = topicRows["blockOrder"].unique().to_list()

        for bo in blockOrders:
            boRow = topicRows.filter(pl.col("blockOrder") == bo)

            # 기간별 파싱
            allItems = []
            seenItems = set()
            periodItemVal = {}
            periodItemSets = defaultdict(set)

            for p in periodCols:
                md = boRow[p][0] if p in boRow.columns else None
                if md is None:
                    continue
                m = re.match(r"\d{4}", p)
                if not m:
                    continue
                pYear = int(m.group())

                for sub in splitSubtables(str(md)):
                    hc = _headerCells(sub)
                    if _isJunk(hc):
                        continue
                    dr = _dataRows(sub)
                    if not dr:
                        continue
                    structType = _classifyStructure(hc)

                    if structType == "multi_year" and "Q" not in p:
                        triples, _ = _parseMultiYear(sub, pYear)
                        for rawItem, year, val in triples:
                            item = _normalizeItemName(rawItem)
                            if year == str(pYear):
                                if item not in seenItems:
                                    allItems.append(item)
                                    seenItems.add(item)
                                if item not in periodItemVal:
                                    periodItemVal[item] = {}
                                periodItemVal[item][p] = val
                                periodItemSets[p].add(item)

                    elif structType in ("key_value", "matrix"):
                        rows, _, _ = _parseKeyValueOrMatrix(sub)
                        for rawItem, vals in rows:
                            item = _normalizeItemName(rawItem)
                            val = " | ".join(v for v in vals if v.strip()).strip()
                            if val:
                                if item not in seenItems:
                                    allItems.append(item)
                                    seenItems.add(item)
                                if item not in periodItemVal:
                                    periodItemVal[item] = {}
                                periodItemVal[item][p] = val
                                periodItemSets[p].add(item)

            # junk 필터
            junkRe = re.compile(r"^[\d,.\-\s]+$")
            allItems = [i for i in allItems if not junkRe.match(i) and i.strip()]
            if not allItems or len(allItems) > 50:
                continue

            # overlap 체크
            if len(periodItemSets) >= 2:
                sets = list(periodItemSets.values())
                totalOverlap = 0
                totalPairs = 0
                for i in range(len(sets)):
                    for j in range(i + 1, min(i + 4, len(sets))):
                        union = len(sets[i] | sets[j])
                        inter = len(sets[i] & sets[j])
                        if union > 0:
                            totalOverlap += inter / union
                            totalPairs += 1
                avgOverlap = totalOverlap / totalPairs if totalPairs else 0
                if avgOverlap < 0.3 and len(allItems) > 5:
                    continue  # 이력형

            # sparse 판정
            usedPeriods = [p for p in periodCols if any(p in periodItemVal.get(item, {}) for item in allItems)]
            if len(usedPeriods) >= 3 and len(allItems) > 15:
                totalCells = len(allItems) * len(usedPeriods)
                filledCells = sum(
                    1 for item in allItems for p in usedPeriods
                    if periodItemVal.get(item, {}).get(p)
                )
                fillRate = filledCells / totalCells if totalCells > 0 else 0
                if fillRate < 0.5:
                    # sparse 블록 발견!
                    sparseBlocks.append({
                        "topic": topic,
                        "bo": bo,
                        "items": len(allItems),
                        "periods": len(usedPeriods),
                        "fillRate": fillRate,
                        "allItems": allItems,
                        "periodItemVal": periodItemVal,
                        "usedPeriods": usedPeriods,
                        "periodItemSets": dict(periodItemSets),
                    })

    return sparseBlocks


def valueFingerprint(sparseBlock: dict) -> dict:
    """sparse 블록에서 값 fingerprint 기반 행 매칭 시도.

    기간 A의 항목 X와 기간 B의 항목 Y가 같은 값을 공유하면,
    X와 Y는 같은 항목일 수 있다.
    """
    periodItemVal = sparseBlock["periodItemVal"]
    usedPeriods = sparseBlock["usedPeriods"]
    allItems = sparseBlock["allItems"]

    # 기간별 항목 존재 매핑
    periodItems = defaultdict(set)
    for item in allItems:
        for p in usedPeriods:
            if periodItemVal.get(item, {}).get(p):
                periodItems[p].add(item)

    # 연속 기간 간 비교
    valueMerges = []  # 값 기반 매칭 후보

    for i in range(len(usedPeriods) - 1):
        p1 = usedPeriods[i]
        p2 = usedPeriods[i + 1]

        items1 = periodItems.get(p1, set())
        items2 = periodItems.get(p2, set())

        # 이미 이름이 같은 항목
        shared = items1 & items2
        only1 = items1 - items2
        only2 = items2 - items1

        if not only1 or not only2:
            continue

        # only1의 값과 only2의 값 비교
        val1Map = {}  # val → item
        for item in only1:
            val = periodItemVal.get(item, {}).get(p1, "")
            normVal = re.sub(r"[,\s]", "", val)
            if normVal and len(normVal) >= 3:  # 너무 짧은 값은 제외
                if normVal not in val1Map:
                    val1Map[normVal] = item

        for item in only2:
            val = periodItemVal.get(item, {}).get(p2, "")
            normVal = re.sub(r"[,\s]", "", val)
            if normVal and normVal in val1Map:
                valueMerges.append({
                    "periods": f"{p1} → {p2}",
                    "item1": val1Map[normVal],
                    "item2": item,
                    "value": normVal,
                })

    # 매칭 결과 평가
    if valueMerges:
        # 동일 패턴 반복 수
        mergePatterns = Counter(f"{m['item1']} → {m['item2']}" for m in valueMerges)
        return {
            "total_merges": len(valueMerges),
            "unique_patterns": len(mergePatterns),
            "top_patterns": mergePatterns.most_common(5),
            "examples": valueMerges[:10],
        }

    return {"total_merges": 0}


if __name__ == "__main__":
    TEST_STOCKS = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035420", "네이버"),
        ("005380", "현대차"),
        ("068270", "셀트리온"),
        ("105560", "KB금융"),
        ("051910", "LG화학"),
        ("003550", "LG"),
        ("028260", "삼성물산"),
        ("034730", "SK"),
    ]

    print("=" * 80)
    print("Part 1: sparse 블록 원인 분석")
    print("=" * 80)

    allSparse = []
    topicCounts = Counter()

    for code, name in TEST_STOCKS:
        blocks = analyzeSparseBlocks(code, name)
        print(f"\n--- {name}: {len(blocks)} sparse 블록 ---")

        for b in blocks[:3]:
            print(f"  {b['topic']} bo={b['bo']}: {b['items']}항목, "
                  f"{b['periods']}기간, fillRate={b['fillRate']:.2%}")

            # 기간별 항목 수 표시
            for p in b['usedPeriods'][:5]:
                items_in_p = sum(1 for item in b['allItems'] if b['periodItemVal'].get(item, {}).get(p))
                print(f"    {p}: {items_in_p}항목")

        allSparse.extend(blocks)
        for b in blocks:
            topicCounts[b["topic"]] += 1

    print(f"\n\n전체 sparse 블록: {len(allSparse)}")
    print(f"\ntopic별:")
    for topic, cnt in topicCounts.most_common(15):
        avgItems = sum(b["items"] for b in allSparse if b["topic"] == topic) / cnt
        avgFill = sum(b["fillRate"] for b in allSparse if b["topic"] == topic) / cnt
        print(f"  {topic}: {cnt}건, 평균 항목 {avgItems:.0f}개, 평균 fillRate {avgFill:.2%}")

    print("\n\n" + "=" * 80)
    print("Part 2: 값 fingerprint 매칭 PoC")
    print("=" * 80)

    totalMerges = 0
    mergeExamples = []

    for b in allSparse:
        result = valueFingerprint(b)
        if result["total_merges"] > 0:
            totalMerges += result["total_merges"]
            print(f"\n  {b['topic']}: {result['total_merges']}건 매칭 가능")
            for pat, cnt in result.get("top_patterns", []):
                print(f"    {pat} (x{cnt})")
            for ex in result.get("examples", [])[:3]:
                print(f"    값={ex['value']}: '{ex['item1']}' ↔ '{ex['item2']}'")
            mergeExamples.extend(result.get("examples", []))

    print(f"\n\n전체 값 매칭 후보: {totalMerges}건")

    if mergeExamples:
        print(f"\n항목명 불일치 유형 분석:")
        # 불일치 패턴 분류
        categories = Counter()
        for ex in mergeExamples:
            i1, i2 = ex["item1"], ex["item2"]
            if i1 == i2:
                categories["동일 (false positive)"] += 1
            elif i1 in i2 or i2 in i1:
                categories["부분 포함"] += 1
            elif len(set(i1) & set(i2)) > len(i1) * 0.5:
                categories["유사 문자열"] += 1
            else:
                categories["완전 다름"] += 1

        for cat, cnt in categories.most_common():
            print(f"  {cat}: {cnt}건")

    print(f"\n\n=== 결론 ===")
    print(f"sparse 블록 {len(allSparse)}건 중 값 매칭 가능: {totalMerges}건")
    if len(allSparse) > 0:
        print(f"개선 잠재력: {totalMerges / len(allSparse) * 100:.1f}% (sparse 블록 대비)")
        print(f"전체 수평화 대비: 미미 (sparse는 전체의 10.9%)")
