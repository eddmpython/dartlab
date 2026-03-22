"""실험 ID: 065-002
실험명: 수평화 실패 37%의 실제 구성 분석

목적:
- 001에서 교차값 매칭 대상(multi_year 항목명 불일치)이 0건인 것으로 확인
- 진짜 37% 실패의 원인별 분포를 정확히 파악
- 각 원인별 개선 가능성과 ROI 평가

가설:
1. 37% 실패 중 대부분은 이력형/목록형 정상 스킵일 것
2. 실질 개선 가능한 영역은 kv/matrix의 항목명 겹침률 저하
3. 교차값 기반 접근은 kv/matrix에서도 적용 가능할 수 있음 (값 fingerprint)

방법:
1. 283종목 전수에서 수평화 실패 원인 분류
2. overlap_filtered의 세부 원인 (겹침률 분포 히스토그램)
3. kv/matrix에서 교차값 매칭 가능성 탐색

결과 (실험 후 작성):

결론:

실험일: 2026-03-18
"""

import sys
sys.path.insert(0, r"C:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\src")

import re
from collections import defaultdict, Counter
import polars as pl

from dartlab.engines.company.dart.docs.sections.tableParser import (
    splitSubtables,
    _headerCells,
    _isJunk,
    _dataRows,
    _classifyStructure,
    _parseMultiYear,
    _parseKeyValueOrMatrix,
    _normalizeItemName,
    _normalizeHeader,
)


def analyzeFailures(stockCode: str, stockName: str) -> dict:
    """단일 종목의 수평화 실패 원인 분류."""
    from dartlab import Company
    c = Company(stockCode)

    if c.docs.sections is None:
        return {"error": "no_sections"}

    sections = c.docs.sections
    tableRows = sections.filter(pl.col("blockType") == "table")

    if tableRows.is_empty():
        return {"error": "no_tables"}

    periodCols = sorted([col for col in tableRows.columns if re.match(r"\d{4}", col)])

    results = {
        "total_blocks": 0,
        "success": 0,          # 수평화 성공
        "overlap_low": 0,      # Jaccard < 0.3 (이력형 판정)
        "list_skip": 0,        # 항목 > 50
        "no_items": 0,         # 파싱 결과 항목 0
        "sparse": 0,           # fillRate < 0.5
        "overlap_detail": [],  # 각 실패의 Jaccard 값
        "kv_overlap_detail": [],  # kv/matrix에서의 실제 겹침률
    }

    topics = tableRows["topic"].unique().to_list()

    for topic in topics:
        topicRows = tableRows.filter(pl.col("topic") == topic)
        blockOrders = topicRows["blockOrder"].unique().to_list()

        for bo in blockOrders:
            boRow = topicRows.filter(pl.col("blockOrder") == bo)
            results["total_blocks"] += 1

            # 기간별 파싱 수행
            allItems = []
            seenItems = set()
            periodItemVal = {}

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

                    elif structType in ("key_value", "matrix"):
                        rows, headerNames, _ = _parseKeyValueOrMatrix(sub)
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

            # 분류
            if not allItems:
                results["no_items"] += 1
                continue

            # junk 필터
            junkRe = re.compile(r"^[\d,.\-\s]+$")
            allItems = [i for i in allItems if not junkRe.match(i) and i.strip()]
            if not allItems:
                results["no_items"] += 1
                continue

            # 목록형
            if len(allItems) > 50:
                results["list_skip"] += 1
                continue

            # 이력형 (Jaccard)
            periodItemSets = {}
            for item in allItems:
                for p in periodItemVal.get(item, {}):
                    if p not in periodItemSets:
                        periodItemSets[p] = set()
                    periodItemSets[p].add(item)

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
                    results["overlap_low"] += 1
                    results["overlap_detail"].append({
                        "topic": topic,
                        "overlap": avgOverlap,
                        "items": len(allItems),
                        "periods": len(periodItemSets),
                    })
                    continue

            # sparse 체크
            usedPeriods = [p for p in periodCols if any(p in periodItemVal.get(item, {}) for item in allItems)]
            if len(usedPeriods) >= 3 and len(allItems) > 15:
                totalCells = len(allItems) * len(usedPeriods)
                filledCells = sum(
                    1 for item in allItems for p in usedPeriods
                    if periodItemVal.get(item, {}).get(p)
                )
                fillRate = filledCells / totalCells if totalCells > 0 else 0
                if fillRate < 0.5:
                    results["sparse"] += 1
                    continue

            results["success"] += 1

    return results


if __name__ == "__main__":
    # 10종목으로 빠른 검증
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
    print("수평화 실패 원인 분류 (10종목)")
    print("=" * 80)

    grand = defaultdict(int)
    allOverlapDetails = []

    for code, name in TEST_STOCKS:
        print(f"\n--- {name} ({code}) ---")
        r = analyzeFailures(code, name)

        if "error" in r:
            print(f"  에러: {r['error']}")
            continue

        total = r["total_blocks"]
        print(f"  전체: {total}")
        print(f"  성공: {r['success']} ({r['success']/total*100:.1f}%)")
        print(f"  overlap_low (이력형): {r['overlap_low']} ({r['overlap_low']/total*100:.1f}%)")
        print(f"  list_skip (목록형): {r['list_skip']} ({r['list_skip']/total*100:.1f}%)")
        print(f"  no_items (파싱 실패): {r['no_items']} ({r['no_items']/total*100:.1f}%)")
        print(f"  sparse: {r['sparse']} ({r['sparse']/total*100:.1f}%)")

        for k in ["total_blocks", "success", "overlap_low", "list_skip", "no_items", "sparse"]:
            grand[k] += r[k]
        allOverlapDetails.extend(r["overlap_detail"])

    print("\n\n" + "=" * 80)
    print("종합")
    print("=" * 80)
    total = grand["total_blocks"]
    print(f"  전체: {total}")
    print(f"  성공: {grand['success']} ({grand['success']/total*100:.1f}%)")
    print(f"  overlap_low: {grand['overlap_low']} ({grand['overlap_low']/total*100:.1f}%)")
    print(f"  list_skip: {grand['list_skip']} ({grand['list_skip']/total*100:.1f}%)")
    print(f"  no_items: {grand['no_items']} ({grand['no_items']/total*100:.1f}%)")
    print(f"  sparse: {grand['sparse']} ({grand['sparse']/total*100:.1f}%)")

    # overlap_low 세부 분석
    if allOverlapDetails:
        print(f"\n\noverlap_low 분포:")

        # overlap 구간별
        buckets = {"0.0-0.1": 0, "0.1-0.2": 0, "0.2-0.3": 0}
        for d in allOverlapDetails:
            ov = d["overlap"]
            if ov < 0.1:
                buckets["0.0-0.1"] += 1
            elif ov < 0.2:
                buckets["0.1-0.2"] += 1
            else:
                buckets["0.2-0.3"] += 1

        for k, v in buckets.items():
            print(f"  {k}: {v}건")

        # topic별
        topicCounts = Counter(d["topic"] for d in allOverlapDetails)
        print(f"\n  topic별:")
        for topic, cnt in topicCounts.most_common(15):
            items_avg = sum(d["items"] for d in allOverlapDetails if d["topic"] == topic) / cnt
            print(f"    {topic}: {cnt}건, 평균 항목 {items_avg:.0f}개")

    # overlap 0.2~0.3 구간 = 경계 사례 상세
    borderline = [d for d in allOverlapDetails if 0.15 <= d["overlap"] < 0.3]
    if borderline:
        print(f"\n\n경계 사례 (overlap 0.15~0.3): {len(borderline)}건")
        for d in borderline[:10]:
            print(f"  {d['topic']}: overlap={d['overlap']:.3f}, items={d['items']}, periods={d['periods']}")
