"""
실험 ID: 064-019
실험명: 패치 적용 후 None 비율 재측정

패치:
1. _UNIT_ONLY_RE 강화 (원화단위/외화단위 변형)
2. _KISU_ONLY_RE 추가 (기수만 항목명 제거)

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
_KISU_ONLY_RE = re.compile(
    r"^제\d+기\s*(?:\d*분기|반기|말)?\s*"
    r"(?:\(\d{4}년[^)]*\))?\s*$"
)
_UNIT_ONLY_RE = re.compile(
    r"^[\(\[\（<〈]?\s*"
    r"(?:<[^>]+>\s*)?"
    r"[\(\[\（]?\s*"
    r"(?:단위|원화\s*단위|외화\s*단위|금액\s*단위)"
    r".*$",
    re.IGNORECASE,
)
_DATE_ONLY_RE = re.compile(r"^\(?\s*기준일\s*:")


def _stripUnitHeader(sub):
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


def _normalizeItem(name):
    name = _SUFFIX_RE.sub("", name).strip()
    m = _KISU_RE.search(name)
    if m:
        return m.group(1)
    if _KISU_ONLY_RE.match(name):
        return ""
    return name


def _isJunkItem(name):
    stripped = re.sub(r"[,.\-\s]", "", name)
    return stripped.isdigit() or not stripped


def horizontalize(topicFrame, bo, periodCols):
    boRow = topicFrame.filter(
        (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
    )
    if boRow.is_empty():
        return None

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

            if structType == "skip":
                fixed = _stripUnitHeader(sub)
                if fixed:
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
                        if item and item not in seenItems:
                            allItems.append(item)
                            seenItems.add(item)
                        if item:
                            if item not in periodItemVal:
                                periodItemVal[item] = {}
                            periodItemVal[item][p] = val
                if not collected and len(hc) >= 2:
                    rows, _, _ = _parseKeyValueOrMatrix(sub)
                    for rawItem, vals in rows:
                        item = _normalizeItem(rawItem)
                        val = " | ".join(v for v in vals if v).strip()
                        if val and item:
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
                    if val and item:
                        if item not in seenItems:
                            allItems.append(item)
                            seenItems.add(item)
                        if item not in periodItemVal:
                            periodItemVal[item] = {}
                        periodItemVal[item][p] = val

    if not allItems:
        return None

    allItems = [it for it in allItems if not _isJunkItem(it)]
    if not allItems:
        return None

    # overlap check
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
            return None

    if len(allItems) > 50:
        return None

    usedPeriods = [p for p in periodCols
                   if any(p in periodItemVal.get(item, {}) for item in allItems)]
    if not usedPeriods:
        return None

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
        return None

    return pl.DataFrame(rows, schema=schema)


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir

    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    print(f"패치 후 None 비율 재측정: {len(codes)}종목")
    print("=" * 70)

    topic_stats = defaultdict(lambda: {"total": 0, "success": 0, "none": 0})

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

        for topic in tableRows["topic"].unique().to_list():
            topicFrame = sec.filter(pl.col("topic") == topic)
            tTable = topicFrame.filter(pl.col("blockType") == "table")
            bos = sorted(tTable["blockOrder"].unique().to_list())
            for bo in bos:
                topic_stats[topic]["total"] += 1
                result = horizontalize(topicFrame, bo, periodCols)
                if result is not None:
                    topic_stats[topic]["success"] += 1
                else:
                    topic_stats[topic]["none"] += 1

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(codes)}]...")

    total_blocks = sum(s["total"] for s in topic_stats.values())
    total_success = sum(s["success"] for s in topic_stats.values())
    total_none = total_blocks - total_success
    print(f"\n전체: {total_blocks} blocks, success={total_success}({total_success*100/total_blocks:.1f}%), none={total_none}({total_none*100/total_blocks:.1f}%)")

    # 비교 (015 기준)
    print(f"\n{'='*70}")
    print("topic별 비교 (before=015, after=019)")
    print(f"{'='*70}")

    # 015 기준 (하드코딩)
    before = {
        "financialNotes": (37404, 16230), "consolidatedNotes": (25340, 9446),
        "businessOverview": (5558, 3466), "fundraising": (4604, 2438),
        "fsSummary": (4080, 2021), "mdna": (3540, 2113),
        "boardOfDirectors": (3173, 2170), "executivePay": (3068, 1736),
        "companyOverview": (2721, 2035), "otherReferences": (2623, 1423),
        "majorHolder": (2584, 2270), "riskDerivative": (2246, 1950),
        "employee": (2226, 1676), "auditSystem": (2047, 1669),
        "rawMaterial": (1753, 1644), "audit": (1731, 1210),
        "companyHistory": (1680, 1016), "majorContractsAndRnd": (1661, 1342),
        "dividend": (1425, 1161), "contingentLiability": (1421, 1103),
        "salesOrder": (1074, 917), "relatedPartyTx": (1030, 881),
    }

    sorted_topics = sorted(topic_stats.items(), key=lambda x: x[1]["total"], reverse=True)
    for topic, stats in sorted_topics[:30]:
        total = stats["total"]
        success = stats["success"]
        pct = success * 100 / total if total else 0

        if topic in before:
            bTotal, bSuccess = before[topic]
            bPct = bSuccess * 100 / bTotal
            diff = pct - bPct
            marker = f" ({diff:+.1f}%p)" if abs(diff) > 0.1 else ""
        else:
            marker = ""

        print(f"  {topic:35s} total={total:5d}  success={success:5d}({pct:5.1f}%){marker}")
