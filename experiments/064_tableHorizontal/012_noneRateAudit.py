"""
실험 ID: 064-012
실험명: 283종목 topic별 None 비율 측정 + 개선 가능 패턴 탐색

목적:
- 현재 _horizontalizeTableBlock의 topic별 None 비율을 전수 측정
- None인데 수평화 가능한 케이스를 세분류
- 개선 가능한 패턴을 식별하고 수정안 검증

가설:
1. 단위행이 헤더로 인식되는 패턴(single_col_header)이 주요 실패 원인
2. multi_year 분기(Q) 스킵이 불필요한 None을 만듦
3. 위 2가지를 수정하면 None 비율 5%p 이상 감소

방법:
1. 283종목 전체 순회, topic × blockOrder별 수평화 시도
2. None인 경우 세부 원인 분류 (single_col_header, quarter_skip, junk, 목록형, 이력형 등)
3. 개선 가능 패턴 빈도 집계

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-17
"""

import sys
import re
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.engines.dart.docs.sections.pipeline import sections
from dartlab.engines.dart.docs.sections.tableParser import (
    splitSubtables,
    _headerCells,
    _isJunk,
    _dataRows,
    _classifyStructure,
    _parseMultiYear,
    _parseKeyValueOrMatrix,
)


def _isPeriodCol(c: str) -> bool:
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))


_SUFFIX_RE = re.compile(r"(사업)?부문$")
_KISU_RE = re.compile(r"제\d+기\s*(?:\d*분기)?\s*\(?(당기|전기|전전기|당반기|전반기)\)?")
_UNIT_ONLY_RE = re.compile(r"^\(?\s*단위\s*[:/]?\s*[^)]*\)?\s*$")
_BASEDATE_RE = re.compile(r"^\(?\s*기준일\s*:")


def _isJunkItem(name: str) -> bool:
    stripped = re.sub(r"[,.\-\s]", "", name)
    return stripped.isdigit() or not stripped


def classifyFailure(
    sec: pl.DataFrame, topic: str, bo: int, periodCols: list[str]
) -> str:
    """None인 table 블록의 실패 원인을 분류."""
    topicFrame = sec.filter(pl.col("topic") == topic)
    boRow = topicFrame.filter(
        (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
    )
    if boRow.is_empty():
        return "empty_row"

    reasons = defaultdict(int)
    allItems_raw = []

    for p in periodCols:
        md = boRow[p][0] if p in boRow.columns else None
        if md is None:
            continue
        m = re.match(r"\d{4}", p)
        if m is None:
            continue
        pYear = int(m.group())
        isQ = "Q" in p

        for sub in splitSubtables(str(md)):
            hc = _headerCells(sub)
            if _isJunk(hc):
                reasons["junk_header"] += 1
                continue
            dr = _dataRows(sub)
            if not dr:
                reasons["no_data_rows"] += 1
                continue

            structType = _classifyStructure(hc)

            if structType == "skip":
                # 단위행이 헤더로 인식된 경우?
                nonEmpty = [c for c in hc if c.strip()]
                if len(hc) == 1 or (len(nonEmpty) == 1 and _UNIT_ONLY_RE.match(nonEmpty[0])):
                    reasons["single_col_header_unit"] += 1
                elif len(nonEmpty) == 1 and _BASEDATE_RE.match(nonEmpty[0]):
                    reasons["single_col_header_basedate"] += 1
                else:
                    reasons["struct_skip"] += 1
                continue

            if structType == "multi_year":
                if isQ:
                    # 분기에서 multi_year 스킵 중
                    triples, _ = _parseMultiYear(sub, pYear)
                    current = [t for t in triples if t[1] == str(pYear)]
                    if current:
                        reasons["multi_year_quarter_fixable"] += 1
                    else:
                        reasons["multi_year_quarter_nodata"] += 1
                else:
                    triples, _ = _parseMultiYear(sub, pYear)
                    current = [t for t in triples if t[1] == str(pYear)]
                    if current:
                        allItems_raw.extend([t[0] for t in current])
                        reasons["multi_year_ok"] += 1
                    else:
                        reasons["multi_year_no_current"] += 1

            elif structType in ("key_value", "matrix"):
                rows, _, _ = _parseKeyValueOrMatrix(sub)
                if rows:
                    allItems_raw.extend([r[0] for r in rows])
                    reasons["kv_ok"] += 1
                else:
                    reasons["kv_noparse"] += 1

    # allItems_raw 필터
    filtered = [it for it in allItems_raw if not _isJunkItem(it)]

    if not reasons:
        return "no_markdown"

    if filtered:
        # 파싱은 됐는데 후속 필터(이력형/목록형)에서 걸림
        if len(set(filtered)) > 50:
            return "list_type_filtered"
        return "overlap_filtered"

    # 주 원인
    top = max(reasons.items(), key=lambda x: x[1])[0]
    return top


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir

    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    print(f"283종목 topic별 수평화 None 비율 측정")
    print(f"종목 수: {len(codes)}")
    print("=" * 70)

    # --- Phase 1: 현재 show() 경로의 None 비율 ---
    topic_stats = defaultdict(lambda: {"total": 0, "success": 0, "none": 0})
    failure_reasons = defaultdict(lambda: defaultdict(int))
    fixable_samples = defaultdict(list)  # topic -> [(code, bo, reason)]

    for i, code in enumerate(codes):
        try:
            sec = sections(code)
        except (FileNotFoundError, ValueError):
            continue
        if sec is None:
            continue

        periodCols = [c for c in sec.columns if _isPeriodCol(c)]
        tableRows = sec.filter(pl.col("blockType") == "table")
        if tableRows.is_empty():
            continue

        topics = tableRows["topic"].unique().to_list()

        for topic in topics:
            topicFrame = sec.filter(pl.col("topic") == topic)
            tTableRows = topicFrame.filter(pl.col("blockType") == "table")
            blockOrders = sorted(tTableRows["blockOrder"].unique().to_list())

            for bo in blockOrders:
                topic_stats[topic]["total"] += 1

                # _horizontalizeTableBlock 재현
                boRow = topicFrame.filter(
                    (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
                )
                if boRow.is_empty():
                    topic_stats[topic]["none"] += 1
                    continue

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
                                item = _SUFFIX_RE.sub("", rawItem).strip()
                                m2 = _KISU_RE.search(item)
                                if m2:
                                    item = m2.group(1)
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
                                item = _SUFFIX_RE.sub("", rawItem).strip()
                                m2 = _KISU_RE.search(item)
                                if m2:
                                    item = m2.group(1)
                                val = " | ".join(v for v in vals if v).strip()
                                if val:
                                    if item not in seenItems:
                                        allItems.append(item)
                                        seenItems.add(item)
                                    if item not in periodItemVal:
                                        periodItemVal[item] = {}
                                    periodItemVal[item][p] = val

                allItems = [it for it in allItems if not _isJunkItem(it)]

                if not allItems:
                    topic_stats[topic]["none"] += 1
                    reason = classifyFailure(sec, topic, bo, periodCols)
                    failure_reasons[topic][reason] += 1
                    if reason in ("single_col_header_unit", "single_col_header_basedate",
                                  "multi_year_quarter_fixable") and len(fixable_samples[topic]) < 3:
                        fixable_samples[topic].append((code, bo, reason))
                    continue

                # 이력형/목록형 필터
                periodItemSets = {}
                for item in allItems:
                    for p2 in periodItemVal.get(item, {}):
                        if p2 not in periodItemSets:
                            periodItemSets[p2] = set()
                        periodItemSets[p2].add(item)
                if len(periodItemSets) >= 2:
                    sets = list(periodItemSets.values())
                    totalOverlap = 0
                    totalPairs = 0
                    for ii in range(len(sets)):
                        for jj in range(ii + 1, min(ii + 4, len(sets))):
                            union = len(sets[ii] | sets[jj])
                            inter = len(sets[ii] & sets[jj])
                            if union > 0:
                                totalOverlap += inter / union
                                totalPairs += 1
                    avgOverlap = totalOverlap / totalPairs if totalPairs else 0
                    if avgOverlap < 0.3 and len(allItems) > 5:
                        topic_stats[topic]["none"] += 1
                        failure_reasons[topic]["overlap_filtered"] += 1
                        continue

                if len(allItems) > 50:
                    topic_stats[topic]["none"] += 1
                    failure_reasons[topic]["list_type_filtered"] += 1
                    continue

                usedPeriods = [p for p in periodCols
                               if any(p in periodItemVal.get(item, {}) for item in allItems)]
                if not usedPeriods:
                    topic_stats[topic]["none"] += 1
                    failure_reasons[topic]["no_used_periods"] += 1
                    continue

                topic_stats[topic]["success"] += 1

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(codes)}]...")

    # --- 결과 출력 ---
    print(f"\n{'='*70}")
    print("topic별 성공/None 비율 (빈도 상위 30)")
    print(f"{'='*70}")

    sorted_topics = sorted(topic_stats.items(), key=lambda x: x[1]["total"], reverse=True)
    for topic, stats in sorted_topics[:30]:
        total = stats["total"]
        success = stats["success"]
        none_ct = stats["none"]
        success_pct = success * 100 / total if total else 0
        none_pct = none_ct * 100 / total if total else 0
        print(f"  {topic:35s} total={total:5d}  success={success:5d}({success_pct:5.1f}%)  none={none_ct:5d}({none_pct:5.1f}%)")

    # --- 실패 원인 ---
    print(f"\n{'='*70}")
    print("topic별 주요 실패 원인 (빈도 상위 15)")
    print(f"{'='*70}")
    for topic, stats in sorted_topics[:15]:
        if topic not in failure_reasons:
            continue
        reasons = failure_reasons[topic]
        total_fail = sum(reasons.values())
        print(f"\n  {topic} (실패 {total_fail}건):")
        for reason, count in sorted(reasons.items(), key=lambda x: -x[1])[:5]:
            pct = count * 100 / total_fail if total_fail else 0
            print(f"    {reason:35s} {count:5d} ({pct:.0f}%)")

    # --- 개선 가능 패턴 ---
    print(f"\n{'='*70}")
    print("개선 가능 패턴 샘플")
    print(f"{'='*70}")
    fixable_total = 0
    for topic, reason_counts in failure_reasons.items():
        for reason in ("single_col_header_unit", "single_col_header_basedate",
                       "multi_year_quarter_fixable"):
            fixable_total += reason_counts.get(reason, 0)

    print(f"개선 가능 패턴 총 건수: {fixable_total}")
    for topic in sorted(fixable_samples.keys()):
        print(f"\n  {topic}:")
        for code, bo, reason in fixable_samples[topic]:
            print(f"    {code} bo={bo} — {reason}")

    # --- 전체 요약 ---
    total_blocks = sum(s["total"] for s in topic_stats.values())
    total_success = sum(s["success"] for s in topic_stats.values())
    total_none = sum(s["none"] for s in topic_stats.values())
    print(f"\n{'='*70}")
    print(f"전체 요약: {total_blocks} blocks, success={total_success}({total_success*100/total_blocks:.1f}%), none={total_none}({total_none*100/total_blocks:.1f}%)")
    print(f"{'='*70}")
