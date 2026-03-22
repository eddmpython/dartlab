"""
실험 ID: 064-008
실험명: 283종목 show(topic, block) 품질 전수 점검

목적:
- 모든 topic의 show(topic, block) 품질 자동 점검
- None인 table 블록의 원인 분류 (이력형 vs 수평화 가능한데 실패)
- 수평화 가능한데 실패하는 케이스 패턴 분석

방법:
1. 283종목 전체에서 table 블록 수집
2. _horizontalizeTableBlock 결과가 None인 것 분류
3. 원인별 카운트: 이력형/목록형/데이터없음/기타

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-17
"""

import re
import sys
import traceback
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.engines.company.dart.docs.sections.pipeline import sections
from dartlab.engines.company.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _headerCells,
    _isJunk,
    _normalizeItemName,
    _parseKeyValueOrMatrix,
    _parseMultiYear,
    splitSubtables,
)


def _isPeriodCol(c: str) -> bool:
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))


def diagnoseTableBlock(topicFrame: pl.DataFrame, blockOrder: int, periodCols: list[str]) -> dict:
    """table 블록이 None인 원인을 분석."""
    boRow = topicFrame.filter(
        (pl.col("blockOrder") == blockOrder) & (pl.col("blockType") == "table")
    )
    if boRow.is_empty():
        return {"reason": "no_table_row"}

    # 각 기간에서 서브테이블 파싱 시도
    total_subs = 0
    total_junk = 0
    total_nodata = 0
    total_skip_struct = 0
    all_struct_types = []
    all_item_counts = []
    period_item_sets = {}
    sample_headers = []
    sample_items = []

    for p in periodCols:
        md = boRow[p][0] if p in boRow.columns else None
        if md is None:
            continue
        m = re.match(r"\d{4}", p)
        if m is None:
            continue
        pYear = int(m.group())

        for sub in splitSubtables(str(md)):
            total_subs += 1
            hc = _headerCells(sub)
            if _isJunk(hc):
                total_junk += 1
                continue
            dr = _dataRows(sub)
            if not dr:
                total_nodata += 1
                continue

            structType = _classifyStructure(hc)
            all_struct_types.append(structType)

            if structType == "skip":
                total_skip_struct += 1
                if len(sample_headers) < 3:
                    sample_headers.append(" | ".join(hc))
                continue

            items_this = set()
            if structType == "multi_year" and "Q" not in p:
                triples, _ = _parseMultiYear(sub, pYear)
                for item, year, val in triples:
                    items_this.add(item)
            elif structType in ("key_value", "matrix"):
                rows, _, _ = _parseKeyValueOrMatrix(sub)
                for item, vals in rows:
                    items_this.add(item)

            all_item_counts.append(len(items_this))
            if len(sample_items) < 5 and items_this:
                sample_items.extend(list(items_this)[:3])

            if p not in period_item_sets:
                period_item_sets[p] = set()
            period_item_sets[p] |= items_this

    # 분석
    if total_subs == 0:
        return {"reason": "no_subtables"}
    if total_subs == total_junk + total_nodata:
        return {"reason": "all_junk_or_empty", "subs": total_subs, "junk": total_junk, "nodata": total_nodata}
    if total_skip_struct > 0 and total_skip_struct == total_subs - total_junk - total_nodata:
        return {"reason": "struct_skip_only", "headers": sample_headers}

    # 항목 수 분석
    total_items = sum(len(s) for s in period_item_sets.values())
    max_items = max(all_item_counts) if all_item_counts else 0

    # 겹침률 분석
    if len(period_item_sets) >= 2:
        sets = list(period_item_sets.values())
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
    else:
        avgOverlap = 1.0

    # 이력형 판정
    is_history = avgOverlap < 0.3 and max_items > 5

    # 목록형 판정
    is_list = max_items > 50

    # 숫자만 항목
    junk_items = sum(1 for item in set().union(*period_item_sets.values()) if re.sub(r"[,.\-\s]", "", item).isdigit() or not re.sub(r"[,.\-\s]", "", item))

    # multi_year에서 Q 기간뿐
    struct_types_set = set(all_struct_types) - {"skip"}
    has_only_multi_year = struct_types_set == {"multi_year"}
    quarter_only = all("Q" in p for p in period_item_sets.keys())

    return {
        "reason": "parsed_but_filtered",
        "struct_types": list(struct_types_set),
        "max_items": max_items,
        "avg_overlap": round(avgOverlap, 2),
        "is_history": is_history,
        "is_list": is_list,
        "junk_items": junk_items,
        "total_items_all_periods": total_items,
        "periods_with_items": len(period_item_sets),
        "quarter_only_multi_year": has_only_multi_year and quarter_only,
        "sample_items": sample_items[:5],
    }


def auditStock(code: str) -> list[dict]:
    """한 종목의 모든 table 블록에서 수평화 결과 점검."""
    results = []

    try:
        sec = sections(code)
    except Exception as e:
        return [{"code": code, "error": str(e)}]

    if sec is None:
        return [{"code": code, "error": "sections None"}]

    periodCols = [c for c in sec.columns if _isPeriodCol(c)]
    topics = sec["topic"].unique().to_list()

    # _horizontalizeTableBlock와 동일한 로직으로 수평화 시도
    from dartlab.engines.company.dart.docs.sections.tableParser import (
        _normalizeItemName as _ni,
    )
    _SUFFIX_RE = re.compile(r"(사업)?부문$")
    _KISU_RE = re.compile(r"제\d+기\s*(?:\d*분기)?\s*\(?(당기|전기|전전기|당반기|전반기)\)?")

    def _normalizeItem(name: str) -> str:
        name = _SUFFIX_RE.sub("", name).strip()
        m = _KISU_RE.search(name)
        if m:
            return m.group(1)
        return name

    for topic in topics:
        topicFrame = sec.filter(pl.col("topic") == topic)
        tableRows = topicFrame.filter(pl.col("blockType") == "table")
        if tableRows.is_empty():
            continue

        blockOrders = sorted(tableRows["blockOrder"].unique().to_list())
        for bo in blockOrders:
            boRow = topicFrame.filter(
                (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
            )
            if boRow.is_empty():
                continue

            # _horizontalizeTableBlock 로직 재현
            allItems = []
            seenItems = set()
            periodItemVal = {}

            for p in periodCols:
                md = boRow[p][0] if p in boRow.columns else None
                if md is None:
                    continue
                m = re.match(r"\d{4}", p)
                if m is None:
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
                            item = _normalizeItem(rawItem)
                            if year == str(pYear):
                                if item not in seenItems:
                                    allItems.append(item)
                                    seenItems.add(item)
                                if item not in periodItemVal:
                                    periodItemVal[item] = {}
                                periodItemVal[item][p] = val
                    elif structType in ("key_value", "matrix"):
                        rows, _, _ = _parseKeyValueOrMatrix(sub)
                        for rawItem, vals in rows:
                            item = _normalizeItem(rawItem)
                            val = " | ".join(v for v in vals if v).strip()
                            if val:
                                if item not in seenItems:
                                    allItems.append(item)
                                    seenItems.add(item)
                                if item not in periodItemVal:
                                    periodItemVal[item] = {}
                                periodItemVal[item][p] = val

            # 품질 필터 재현
            def _isJunkItem(name):
                stripped = re.sub(r"[,.\-\s]", "", name)
                return stripped.isdigit() or not stripped

            allItems = [item for item in allItems if not _isJunkItem(item)]

            # 이력형/목록형 감지 재현
            periodItemSets = {}
            for item in allItems:
                for p in periodItemVal.get(item, {}):
                    if p not in periodItemSets:
                        periodItemSets[p] = set()
                    periodItemSets[p].add(item)

            avgOverlap = 1.0
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

            is_history = avgOverlap < 0.3 and len(allItems) > 5
            is_list = len(allItems) > 50

            # 결과 기록
            success = len(allItems) > 0 and not is_history and not is_list
            # usedPeriods 체크
            if success:
                usedPeriods = [p for p in periodCols if any(p in periodItemVal.get(item, {}) for item in allItems)]
                if not usedPeriods:
                    success = False

            reason = "success"
            if not allItems:
                reason = "no_items"
            elif is_history:
                reason = "history_skip"
            elif is_list:
                reason = "list_skip"

            results.append({
                "code": code,
                "topic": topic,
                "blockOrder": bo,
                "success": success,
                "reason": reason,
                "itemCount": len(allItems),
                "avgOverlap": round(avgOverlap, 2),
                "periodCount": len(periodItemSets),
                "sampleItems": allItems[:3] if allItems else [],
            })

    return results


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir

    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    print(f"품질 점검: {len(codes)}종목")
    print("=" * 70)

    allResults = []
    errorCodes = []

    for i, code in enumerate(codes):
        try:
            results = auditStock(code)
            if results and "error" in results[0]:
                errorCodes.append(code)
                continue
            allResults.extend(results)
        except Exception as e:
            errorCodes.append(code)
            if (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(codes)}] {code}: ERROR — {e}")
            continue

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(codes)}] 완료... ({len(allResults)} blocks)")

    print(f"\n총 {len(allResults)} table 블록")
    print(f"에러 종목: {len(errorCodes)}")

    # 결과 분류
    successCount = sum(1 for r in allResults if r["success"])
    failCount = sum(1 for r in allResults if not r["success"])
    print(f"  수평화 성공: {successCount} ({successCount*100/len(allResults):.1f}%)")
    print(f"  수평화 None: {failCount} ({failCount*100/len(allResults):.1f}%)")

    # None 원인 분류
    reasons = defaultdict(list)
    for r in allResults:
        if not r["success"]:
            reasons[r["reason"]].append(r)

    print(f"\nNone 원인 분류:")
    for reason, cases in sorted(reasons.items(), key=lambda x: -len(x[1])):
        print(f"  {reason}: {len(cases)}건")
        # topic별 분포
        topicCounts = defaultdict(int)
        for c in cases:
            topicCounts[c["topic"]] += 1
        topTopics = sorted(topicCounts.items(), key=lambda x: -x[1])[:10]
        for topic, count in topTopics:
            print(f"    {topic}: {count}건")

    # history_skip 상세 — 실제 이력형 vs 수평화 가능
    print(f"\n{'='*70}")
    print("history_skip 상세 분석")
    print(f"{'='*70}")
    history_cases = reasons.get("history_skip", [])
    if history_cases:
        # overlap 분포
        overlaps = [c["avgOverlap"] for c in history_cases]
        items = [c["itemCount"] for c in history_cases]
        print(f"  겹침률 분포: min={min(overlaps):.2f}, max={max(overlaps):.2f}, avg={sum(overlaps)/len(overlaps):.2f}")
        print(f"  항목수 분포: min={min(items)}, max={max(items)}, avg={sum(items)/len(items):.1f}")
        # 겹침률별 bucket
        buckets = {"<0.1": 0, "0.1-0.2": 0, "0.2-0.3": 0}
        for o in overlaps:
            if o < 0.1:
                buckets["<0.1"] += 1
            elif o < 0.2:
                buckets["0.1-0.2"] += 1
            else:
                buckets["0.2-0.3"] += 1
        print(f"  겹침률 bucket: {dict(buckets)}")

        # 항목 수 6~15 구간 (수평화 가능한데 스킵됐을 가능성)
        borderline = [c for c in history_cases if c["itemCount"] <= 15]
        print(f"\n  경계선 케이스 (항목≤15): {len(borderline)}건")
        for c in borderline[:10]:
            print(f"    {c['code']}:{c['topic']} bo={c['blockOrder']} items={c['itemCount']} overlap={c['avgOverlap']} samples={c['sampleItems']}")

    # no_items 상세 — 왜 파싱 실패?
    print(f"\n{'='*70}")
    print("no_items 상세 분석")
    print(f"{'='*70}")
    noitems_cases = reasons.get("no_items", [])
    if noitems_cases:
        # 샘플 10개에서 원인 분석
        from dartlab.engines.company.dart.docs.sections.pipeline import sections as load_sections
        sample_codes = list(set(c["code"] for c in noitems_cases[:100]))[:5]
        for code in sample_codes:
            try:
                sec = load_sections(code)
            except Exception:
                continue
            if sec is None:
                continue
            periodCols = [c for c in sec.columns if _isPeriodCol(c)]
            code_cases = [c for c in noitems_cases if c["code"] == code][:3]
            for case in code_cases:
                topic = case["topic"]
                bo = case["blockOrder"]
                topicFrame = sec.filter(pl.col("topic") == topic)
                diag = diagnoseTableBlock(topicFrame, bo, periodCols)
                print(f"\n  {code}:{topic} bo={bo}: {diag}")

    # 핵심 topic별 성공률
    print(f"\n{'='*70}")
    print("핵심 topic별 성공률")
    print(f"{'='*70}")
    key_topics = ["dividend", "audit", "salesOrder", "companyOverview", "employee",
                  "majorHolder", "shareCapital", "executivePay", "rawMaterial", "riskDerivative"]
    for topic in key_topics:
        topic_results = [r for r in allResults if r["topic"] == topic]
        if not topic_results:
            continue
        ok = sum(1 for r in topic_results if r["success"])
        total = len(topic_results)
        print(f"  {topic}: {ok}/{total} ({ok*100/total:.0f}%)")
        # 실패 원인
        fails = [r for r in topic_results if not r["success"]]
        if fails:
            fail_reasons = defaultdict(int)
            for f in fails:
                fail_reasons[f["reason"]] += 1
            for reason, cnt in sorted(fail_reasons.items(), key=lambda x: -x[1]):
                print(f"    {reason}: {cnt}")
