"""실험 ID: 065-001
실험명: 교차값 기반 행 매칭 — multi_year 당기/전기 값 체인

목적:
- DART 보고서의 multi_year 테이블에서 "당기/전기/전전기" 값이 기간 간 겹치는 성질을 이용
- 항목명이 달라도 교차값으로 같은 항목을 매칭할 수 있는지 검증
- 현재 62.9% 수평화 성공률(overlap_filtered 37%)의 근본 개선 가능성 평가

가설:
1. 2024보고서의 "당기=X" == 2025보고서의 "전기=X" → 같은 항목임을 확인 가능
2. 교차값 매칭으로 항목명 불일치 문제를 우회할 수 있다
3. multi_year 타입에서 교차값 체인이 80% 이상의 행에서 성립한다

방법:
1. 삼성전자 등 10종목의 실제 sections 데이터에서 multi_year 테이블 추출
2. 연속 기간의 당기/전기 값 교차 검증
3. 항목명 일치/불일치별 교차값 일치율 측정
4. 교차값 기반 매칭의 정확도, 충돌율, 커버리지 측정

결과 (실험 후 작성):

결론:

실험일: 2026-03-18
"""

import sys

sys.path.insert(0, r"C:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\src")

import re
from collections import defaultdict

import polars as pl

from dartlab.engines.company.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _headerCells,
    _isJunk,
    _normalizeItemName,
    _parseMultiYear,
    splitSubtables,
)


def extractMultiYearFull(sub: list[str], periodYear: int) -> list[dict]:
    """multi_year 서브테이블에서 항목별 (당기, 전기, 전전기) 풀 추출.

    Returns: [{"item": str, "values": {"당기": val, "전기": val, ...}, "years": {"당기": year, ...}}]
    """
    sepIdx = -1
    for i, line in enumerate(sub):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            sepIdx = i
            break

    if sepIdx < 0 or sepIdx + 1 >= len(sub):
        return []

    # 기수 행
    kisuCells = [c.strip() for c in sub[sepIdx + 1].strip("|").split("|")]
    kisuLabels = []
    kisuNums = []
    for cell in kisuCells:
        m = re.search(r"제\s*(\d+)\s*기", cell)
        if m:
            kisuNums.append(int(m.group(1)))
            # 당기/전기 라벨 추출
            label_m = re.search(r"\((당기|전기|전전기|당반기|전반기)\)", cell)
            label = label_m.group(1) if label_m else f"기수{m.group(1)}"
            kisuLabels.append(label)

    if not kisuNums:
        return []

    maxKisu = max(kisuNums)
    kisuToYear = {kn: periodYear - maxKisu + kn for kn in kisuNums}

    results = []
    prevItem = ""
    _STOCK_TYPES = {"보통주", "우선주", "기타주식"}

    for line in sub[sepIdx + 2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            continue
        if not cells or not cells[0].strip():
            continue

        first = cells[0].strip()
        if first.startswith("※"):
            continue

        if first in _STOCK_TYPES and prevItem:
            itemName = _normalizeItemName(f"{prevItem}-{first}")
            valCells = cells[1:]
        elif len(cells) > 1 and cells[1].strip() in _STOCK_TYPES:
            stockType = cells[1].strip()
            itemName = _normalizeItemName(f"{first}-{stockType}")
            valCells = cells[2:]
            prevItem = first
        else:
            itemName = _normalizeItemName(first)
            valCells = cells[1:]
            prevItem = first

        values = {}
        years = {}
        # 뒤에서부터 기수 수만큼 역순 추출 (빈 컬럼 문제 회피)
        nonEmpty = [(i, v.strip()) for i, v in enumerate(valCells) if v.strip() and v.strip() != "-"]

        sortedKisu = sorted(kisuNums, reverse=True)
        for ki, kn in enumerate(sortedKisu):
            # 순서대로 매칭
            if ki < len(valCells):
                val = valCells[ki].strip()
                if val and val != "-" and val not in _STOCK_TYPES:
                    label = kisuLabels[ki] if ki < len(kisuLabels) else f"기수{kn}"
                    values[label] = val
                    years[label] = kisuToYear[kn]

        if values:
            results.append({
                "item": itemName,
                "values": values,
                "years": years,
            })

    return results


def crossValidate(periodData: dict[str, list[dict]]) -> dict:
    """연속 기간의 multi_year 파싱 결과에서 교차값 매칭 수행.

    Args:
        periodData: {period_label: [{"item", "values", "years"}]} — 기간별 파싱 결과

    Returns: 교차검증 통계
    """
    periods = sorted(periodData.keys())

    stats = {
        "total_pairs": 0,
        "cross_matched": 0,
        "name_matched": 0,      # 항목명도 일치
        "name_mismatched": 0,   # 항목명 불일치인데 값으로 매칭
        "ambiguous": 0,         # 같은 값이 여러 항목에 존재
        "no_overlap": 0,        # 교차값 없음
        "examples": [],
    }

    for i in range(len(periods) - 1):
        pCurr = periods[i]
        pNext = periods[i + 1]

        curr = periodData[pCurr]
        next_ = periodData[pNext]

        if not curr or not next_:
            continue

        # curr의 "당기" 값 → next의 "전기" 값 교차
        # curr에서 당기 값 수집: {값: [항목명]}
        currValues = defaultdict(list)
        for entry in curr:
            if "당기" in entry["values"]:
                val = entry["values"]["당기"]
                # 숫자 정규화 (쉼표, 공백 제거)
                normVal = re.sub(r"[,\s]", "", val)
                if normVal:
                    currValues[normVal].append(entry["item"])

        # next에서 전기 값 수집: {값: [항목명]}
        nextValues = defaultdict(list)
        for entry in next_:
            if "전기" in entry["values"]:
                val = entry["values"]["전기"]
                normVal = re.sub(r"[,\s]", "", val)
                if normVal:
                    nextValues[normVal].append(entry["item"])

        # 교차 매칭
        for entry in next_:
            if "전기" not in entry["values"]:
                continue

            stats["total_pairs"] += 1
            normVal = re.sub(r"[,\s]", "", entry["values"]["전기"])

            if normVal in currValues:
                currItems = currValues[normVal]

                if len(currItems) == 1:
                    stats["cross_matched"] += 1
                    matchedItem = currItems[0]

                    if matchedItem == entry["item"]:
                        stats["name_matched"] += 1
                    else:
                        stats["name_mismatched"] += 1
                        stats["examples"].append({
                            "period_pair": f"{pCurr} → {pNext}",
                            "value": normVal,
                            "curr_item": matchedItem,
                            "next_item": entry["item"],
                        })
                else:
                    stats["ambiguous"] += 1
            else:
                stats["no_overlap"] += 1

    return stats


def analyzeStock(stockCode: str, stockName: str, topic: str = "dividend"):
    """특정 종목의 특정 topic에서 교차검증 수행."""
    from dartlab import Company
    c = Company(stockCode)

    if c.docs.sections is None:
        print(f"  [{stockName}] sections 없음")
        return None

    sections = c.docs.sections
    topicRows = sections.filter(
        (pl.col("topic") == topic) & (pl.col("blockType") == "table")
    )

    if topicRows.is_empty():
        print(f"  [{stockName}] {topic} table 없음")
        return None

    # 기간 컬럼 추출
    periodCols = [col for col in topicRows.columns
                  if re.match(r"\d{4}", col) and "Q" not in col]
    periodCols = sorted(periodCols)

    print(f"  [{stockName}] {topic}: {len(periodCols)} 기간, {topicRows.height} table 행")

    # 기간별 multi_year 파싱
    periodData = {}

    for p in periodCols:
        pYear = int(p[:4])
        allEntries = []

        for row in topicRows.iter_rows(named=True):
            md = row.get(p)
            if md is None:
                continue

            for sub in splitSubtables(str(md)):
                hc = _headerCells(sub)
                if _isJunk(hc):
                    continue
                dr = _dataRows(sub)
                if not dr:
                    continue

                structType = _classifyStructure(hc)
                if structType == "multi_year":
                    entries = extractMultiYearFull(sub, pYear)
                    allEntries.extend(entries)

        if allEntries:
            periodData[p] = allEntries

    print(f"  [{stockName}] multi_year 파싱: {len(periodData)} 기간에서 데이터 추출")
    for p, entries in sorted(periodData.items()):
        items = [e["item"] for e in entries]
        print(f"    {p}: {len(entries)} 항목 — {items[:5]}{'...' if len(items) > 5 else ''}")

    # 교차검증
    if len(periodData) >= 2:
        stats = crossValidate(periodData)
        return stats

    return None


def analyzeKvMatrix(stockCode: str, stockName: str, topic: str = "audit"):
    """kv/matrix 타입에서 교차검증 가능성 분석.

    kv/matrix는 multi_year처럼 당기/전기 값이 내장되어 있지 않으므로,
    연속 기간의 같은 항목명의 값 변동을 분석.
    """
    from dartlab import Company
    c = Company(stockCode)

    if c.docs.sections is None:
        return None

    sections = c.docs.sections
    topicRows = sections.filter(
        (pl.col("topic") == topic) & (pl.col("blockType") == "table")
    )

    if topicRows.is_empty():
        return None

    from dartlab.engines.company.dart.docs.sections.tableParser import _parseKeyValueOrMatrix

    periodCols = [col for col in topicRows.columns
                  if re.match(r"\d{4}", col) and "Q" not in col]
    periodCols = sorted(periodCols)

    # 기간별 항목-값 수집
    periodItems = {}  # {period: {item: [values]}}

    for p in periodCols:
        items = defaultdict(list)
        for row in topicRows.iter_rows(named=True):
            md = row.get(p)
            if md is None:
                continue
            for sub in splitSubtables(str(md)):
                hc = _headerCells(sub)
                if _isJunk(hc):
                    continue
                dr = _dataRows(sub)
                if not dr:
                    continue
                structType = _classifyStructure(hc)
                if structType in ("key_value", "matrix"):
                    rows, headerNames, _ = _parseKeyValueOrMatrix(sub)
                    for item, vals in rows:
                        normItem = _normalizeItemName(item)
                        items[normItem] = vals
        if items:
            periodItems[p] = items

    # 기간 간 항목명 겹침률
    if len(periodItems) >= 2:
        periods = sorted(periodItems.keys())
        overlapRates = []
        for i in range(len(periods) - 1):
            s1 = set(periodItems[periods[i]].keys())
            s2 = set(periodItems[periods[i+1]].keys())
            union = len(s1 | s2)
            inter = len(s1 & s2)
            rate = inter / union if union > 0 else 0
            overlapRates.append(rate)

        avgOverlap = sum(overlapRates) / len(overlapRates)
        return {
            "topic": topic,
            "periods": len(periodItems),
            "avg_overlap": avgOverlap,
            "overlap_rates": overlapRates,
            "avg_items": sum(len(v) for v in periodItems.values()) / len(periodItems),
        }

    return None


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

    TOPICS_MY = ["dividend", "salesOrder", "rawMaterial", "riskDerivative"]
    TOPICS_KV = ["audit", "employee", "majorHolder", "companyOverview"]

    print("=" * 80)
    print("Part 1: multi_year 교차값 검증")
    print("=" * 80)

    allStats = defaultdict(lambda: defaultdict(int))
    allExamples = []

    for topic in TOPICS_MY:
        print(f"\n--- {topic} ---")
        topicTotal = defaultdict(int)

        for code, name in TEST_STOCKS:
            stats = analyzeStock(code, name, topic)
            if stats:
                for k in ["total_pairs", "cross_matched", "name_matched",
                          "name_mismatched", "ambiguous", "no_overlap"]:
                    topicTotal[k] += stats[k]
                    allStats[topic][k] += stats[k]
                allExamples.extend(stats.get("examples", []))

        if topicTotal["total_pairs"] > 0:
            tp = topicTotal["total_pairs"]
            print(f"\n  [{topic} 합계]")
            print(f"    전체 쌍: {tp}")
            print(f"    교차 매칭: {topicTotal['cross_matched']} ({topicTotal['cross_matched']/tp*100:.1f}%)")
            print(f"      - 항목명도 일치: {topicTotal['name_matched']}")
            print(f"      - 항목명 불일치(값으로 매칭): {topicTotal['name_mismatched']}")
            print(f"    모호(다중 매칭): {topicTotal['ambiguous']} ({topicTotal['ambiguous']/tp*100:.1f}%)")
            print(f"    교차값 없음: {topicTotal['no_overlap']} ({topicTotal['no_overlap']/tp*100:.1f}%)")

    print("\n\n" + "=" * 80)
    print("Part 2: 항목명 불일치 → 교차값 매칭 사례")
    print("=" * 80)

    for ex in allExamples[:20]:
        print(f"  {ex['period_pair']}: '{ex['curr_item']}' → '{ex['next_item']}' (값={ex['value']})")

    print(f"\n  총 항목명 불일치 매칭 사례: {len(allExamples)}건")

    print("\n\n" + "=" * 80)
    print("Part 3: kv/matrix 항목명 겹침률 (교차값 적용 불가 영역)")
    print("=" * 80)

    for topic in TOPICS_KV:
        print(f"\n--- {topic} ---")
        for code, name in TEST_STOCKS[:5]:
            result = analyzeKvMatrix(code, name, topic)
            if result:
                print(f"  [{name}] {result['periods']}기간, "
                      f"평균 항목 {result['avg_items']:.0f}개, "
                      f"평균 겹침률 {result['avg_overlap']:.1%}")

    print("\n\n" + "=" * 80)
    print("Part 4: 종합 교차값 매칭 효과 분석")
    print("=" * 80)

    grandTotal = defaultdict(int)
    for topic, stats in allStats.items():
        for k, v in stats.items():
            grandTotal[k] += v

    if grandTotal["total_pairs"] > 0:
        tp = grandTotal["total_pairs"]
        print(f"  전체 쌍: {tp}")
        print(f"  교차 매칭 성공: {grandTotal['cross_matched']} ({grandTotal['cross_matched']/tp*100:.1f}%)")
        print(f"    - 항목명 일치: {grandTotal['name_matched']} ({grandTotal['name_matched']/tp*100:.1f}%)")
        print(f"    - 항목명 불일치(값 매칭): {grandTotal['name_mismatched']} ({grandTotal['name_mismatched']/tp*100:.1f}%)")
        print(f"  모호(충돌): {grandTotal['ambiguous']} ({grandTotal['ambiguous']/tp*100:.1f}%)")
        print(f"  교차값 없음: {grandTotal['no_overlap']} ({grandTotal['no_overlap']/tp*100:.1f}%)")

        if grandTotal["cross_matched"] > 0:
            nameMatchRate = grandTotal["name_matched"] / grandTotal["cross_matched"] * 100
            print(f"\n  교차 매칭 중 항목명도 일치: {nameMatchRate:.1f}%")
            print(f"  → 항목명 불일치를 교차값으로 구원한 비율: "
                  f"{grandTotal['name_mismatched'] / grandTotal['cross_matched'] * 100:.1f}%")

    # 핵심 수치: 교차값이 "새로 매칭"할 수 있는 비율 vs 전체 개선 잠재력
    print(f"\n\n  === 결론 ===")
    print(f"  교차값 매칭이 해결할 수 있는 문제:")
    print(f"  - multi_year에서 항목명 불일치: {grandTotal['name_mismatched']}건")
    print(f"  - 이것은 전체 37% fallback 중 얼마인가? → Part 5에서 계산")
