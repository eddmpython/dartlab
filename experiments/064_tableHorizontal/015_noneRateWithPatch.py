"""
실험 ID: 064-015
실험명: _stripUnitHeader 패치 반영 후 None 비율 측정 (Company 없이)

목적:
- company.py의 _stripUnitHeader 로직을 재현하여 패치 적용 후 None 비율 측정
- Company 인스턴스 생성 비용 없이 빠르게 전수 검증

실험일: 2026-03-17
"""

import re
import sys
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
    _parseKeyValueOrMatrix,
    _parseMultiYear,
    splitSubtables,
)


def _isPeriodCol(c: str) -> bool:
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))


_SUFFIX_RE = re.compile(r"(사업)?부문$")
_KISU_RE = re.compile(r"제\d+기\s*(?:\d*분기)?\s*\(?(당기|전기|전전기|당반기|전반기)\)?")
_UNIT_ONLY_RE = re.compile(r"^\(?\s*단위\s*[:/]?\s*[^)]*\)?\s*$")
_DATE_ONLY_RE = re.compile(r"^\(?\s*기준일\s*:")


def _stripUnitHeader(sub: list[str]) -> list[str] | None:
    """company.py의 _stripUnitHeader 재현."""
    firstRow = None
    for line in sub:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            continue
        firstRow = [c for c in cells if c.strip()]
        break

    if firstRow is None or len(firstRow) != 1:
        return None
    h = firstRow[0].strip()
    if not (_UNIT_ONLY_RE.match(h) or _DATE_ONLY_RE.match(h)):
        return None

    sepIdx = -1
    for i, line in enumerate(sub):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            sepIdx = i
            break

    if sepIdx < 0 or sepIdx + 1 >= len(sub):
        return None

    remainder = sub[sepIdx + 1:]
    if not remainder:
        return None

    hasSep = any(
        all(set(c.strip()) <= {"-", ":"} for c in line.strip("|").split("|") if c.strip())
        for line in remainder
    )
    if hasSep:
        return remainder

    if len(remainder) >= 2:
        headerLine = remainder[0]
        colCount = len(headerLine.strip("|").split("|"))
        sepLine = "| " + " | ".join(["---"] * colCount) + " |"
        return [headerLine, sepLine] + remainder[1:]

    return None


def _isJunkItem(name: str) -> bool:
    stripped = re.sub(r"[,.\-\s]", "", name)
    return stripped.isdigit() or not stripped


def _normalizeItem(name: str) -> str:
    name = _SUFFIX_RE.sub("", name).strip()
    m = _KISU_RE.search(name)
    if m:
        return m.group(1)
    return name


def horizontalizeWithPatch(
    topicFrame: pl.DataFrame, bo: int, periodCols: list[str]
) -> tuple[pl.DataFrame | None, str]:
    """company.py 로직 + _stripUnitHeader 재현. (result, failReason) 반환."""
    boRow = topicFrame.filter(
        (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
    )
    if boRow.is_empty():
        return None, "empty"

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

            # _stripUnitHeader 적용
            if structType == "skip":
                fixed = _stripUnitHeader(sub)
                if fixed is not None:
                    fixedHc = _headerCells(fixed)
                    fixedDr = _dataRows(fixed)
                    if fixedHc and not _isJunk(fixedHc) and fixedDr:
                        structType = _classifyStructure(fixedHc)
                        sub = fixed

            if structType == "multi_year":
                triples, _ = _parseMultiYear(sub, pYear)
                collected = False
                for rawItem, year, val in triples:
                    item = _normalizeItem(rawItem)
                    if year == str(pYear):
                        collected = True
                        if item not in seenItems:
                            allItems.append(item)
                            seenItems.add(item)
                        if item not in periodItemVal:
                            periodItemVal[item] = {}
                        periodItemVal[item][p] = val
                # multi_year fallback to kv/matrix
                if not collected and len(hc) >= 2:
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

    if not allItems:
        return None, "no_items"

    allItems = [it for it in allItems if not _isJunkItem(it)]
    if not allItems:
        return None, "all_junk"

    # 이력형 감지
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
            return None, "overlap_filtered"

    if len(allItems) > 50:
        return None, "list_type"

    usedPeriods = [p for p in periodCols
                   if any(p in periodItemVal.get(item, {}) for item in allItems)]
    if not usedPeriods:
        return None, "no_used_periods"

    schema = {"항목": pl.Utf8}
    for p in usedPeriods:
        schema[p] = pl.Utf8

    rows = []
    for item in allItems:
        if not any(periodItemVal.get(item, {}).get(p) for p in usedPeriods):
            continue
        row = {"항목": item}
        for p in usedPeriods:
            row[p] = periodItemVal.get(item, {}).get(p)
        rows.append(row)

    if not rows:
        return None, "empty_rows"

    return pl.DataFrame(rows, schema=schema), "success"


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir

    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    print(f"_stripUnitHeader 패치 반영 후 None 비율")
    print(f"종목 수: {len(codes)}")
    print("=" * 70)

    topic_stats = defaultdict(lambda: {"total": 0, "success": 0, "none": 0})
    fail_reasons = defaultdict(lambda: defaultdict(int))

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

        topics_list = tableRows["topic"].unique().to_list()
        for topic in topics_list:
            topicFrame = sec.filter(pl.col("topic") == topic)
            tTableRows = topicFrame.filter(pl.col("blockType") == "table")
            blockOrders = sorted(tTableRows["blockOrder"].unique().to_list())

            for bo in blockOrders:
                topic_stats[topic]["total"] += 1
                result, reason = horizontalizeWithPatch(topicFrame, bo, periodCols)
                if result is not None:
                    topic_stats[topic]["success"] += 1
                else:
                    topic_stats[topic]["none"] += 1
                    fail_reasons[topic][reason] += 1

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(codes)}]...")

    # 결과
    print(f"\n{'='*70}")
    print("topic별 성공/None 비율 (빈도 상위 30)")
    print(f"{'='*70}")

    sorted_topics = sorted(topic_stats.items(), key=lambda x: x[1]["total"], reverse=True)
    for topic, stats in sorted_topics[:30]:
        total = stats["total"]
        success = stats["success"]
        none_ct = stats["none"]
        success_pct = success * 100 / total if total else 0
        print(f"  {topic:35s} total={total:5d}  success={success:5d}({success_pct:5.1f}%)  none={none_ct:5d}({none_ct*100/total:.1f}%)")

    # 실패 원인
    print(f"\n{'='*70}")
    print("실패 원인 전체 집계")
    print(f"{'='*70}")
    total_reasons = defaultdict(int)
    for topic in fail_reasons:
        for reason, count in fail_reasons[topic].items():
            total_reasons[reason] += count
    for reason, count in sorted(total_reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason:35s} {count:6d}")

    # topic별 실패 원인 (상위 10)
    print(f"\n{'='*70}")
    print("topic별 실패 원인 상세 (상위 10)")
    print(f"{'='*70}")
    for topic, stats in sorted_topics[:10]:
        if topic not in fail_reasons:
            continue
        reasons = fail_reasons[topic]
        total_fail = sum(reasons.values())
        print(f"\n  {topic} (실패 {total_fail}건):")
        for reason, count in sorted(reasons.items(), key=lambda x: -x[1])[:5]:
            print(f"    {reason:30s} {count:5d} ({count*100/total_fail:.0f}%)")

    # 전체 요약
    total_blocks = sum(s["total"] for s in topic_stats.values())
    total_success = sum(s["success"] for s in topic_stats.values())
    total_none = sum(s["none"] for s in topic_stats.values())
    print(f"\n{'='*70}")
    print(f"전체: {total_blocks} blocks, success={total_success}({total_success*100/total_blocks:.1f}%), none={total_none}({total_none*100/total_blocks:.1f}%)")
    print(f"{'='*70}")
