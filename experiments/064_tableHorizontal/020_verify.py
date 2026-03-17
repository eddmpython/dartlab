"""quick verify after KISU_RE strengthened (no KISU_ONLY)"""

import sys, re
from collections import defaultdict
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "src"))
import polars as pl
from dartlab.engines.dart.docs.sections.pipeline import sections
from dartlab.engines.dart.docs.sections.tableParser import (
    splitSubtables, _headerCells, _isJunk, _dataRows, _classifyStructure,
    _parseMultiYear, _parseKeyValueOrMatrix,
)

def _isPeriodCol(c):
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))

_SUFFIX_RE = re.compile(r"(사업)?부문$")
_KISU_RE = re.compile(
    r"제\d+기\s*(?:\d*분기|반기|말)?\s*"
    r"\(?(당기|전기|전전기|당반기|전반기|당분기|전분기)\)?"
)
_UNIT_ONLY_RE = re.compile(
    r"^[\(\[\xef\xbc\x88<\u3008]?\s*"
    r"(?:<[^>]+>\s*)?"
    r"[\(\[\xef\xbc\x88]?\s*"
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
        all(set(c.strip()) <= {"-", ":"} for c in l.strip("|").split("|") if c.strip())
        for l in remainder
    )
    if hasSep:
        return remainder
    if len(remainder) >= 2:
        hl = remainder[0]
        cc = len(hl.strip("|").split("|"))
        sl = "| " + " | ".join(["---"] * cc) + " |"
        return [hl, sl] + remainder[1:]
    return None

def _normalizeItem(name):
    name = _SUFFIX_RE.sub("", name).strip()
    m = _KISU_RE.search(name)
    if m:
        return m.group(1)
    return name

def _isJunkItem(name):
    stripped = re.sub(r"[,.\-\s]", "", name)
    return stripped.isdigit() or not stripped


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir
    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    topic_stats = defaultdict(lambda: {"total": 0, "success": 0})

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
                boRow = topicFrame.filter(
                    (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
                )
                if boRow.is_empty():
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
                        if structType == "skip":
                            fixed = _stripUnitHeader(sub)
                            if fixed:
                                fhc = _headerCells(fixed)
                                fdr = _dataRows(fixed)
                                if fhc and not _isJunk(fhc) and fdr:
                                    structType = _classifyStructure(fhc)
                                    sub = fixed
                        if structType == "multi_year":
                            triples, _ = _parseMultiYear(sub, pYear)
                            collected = False
                            for rawItem, year, val in triples:
                                item = _normalizeItem(rawItem)
                                if year == str(pYear) and item:
                                    collected = True
                                    if item not in seenItems:
                                        allItems.append(item)
                                        seenItems.add(item)
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
                allItems = [it for it in allItems if not _isJunkItem(it)]
                if not allItems:
                    continue
                pSets = {}
                for item in allItems:
                    for p2 in periodItemVal.get(item, {}):
                        if p2 not in pSets:
                            pSets[p2] = set()
                        pSets[p2].add(item)
                if len(pSets) >= 2:
                    sets = list(pSets.values())
                    tO = 0; tP = 0
                    for ii in range(len(sets)):
                        for jj in range(ii + 1, min(ii + 4, len(sets))):
                            u = len(sets[ii] | sets[jj])
                            inter = len(sets[ii] & sets[jj])
                            if u > 0:
                                tO += inter / u
                                tP += 1
                    aO = tO / tP if tP else 0
                    if aO < 0.3 and len(allItems) > 5:
                        continue
                if len(allItems) > 50:
                    continue
                usedP = [p for p in periodCols if any(p in periodItemVal.get(it, {}) for it in allItems)]
                if not usedP:
                    continue
                topic_stats[topic]["success"] += 1
        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(codes)}]...")

    total_blocks = sum(s["total"] for s in topic_stats.values())
    total_success = sum(s["success"] for s in topic_stats.values())
    print(f"\n전체: {total_blocks} blocks, success={total_success}({total_success*100/total_blocks:.1f}%)")

    before = {
        "audit": (1731, 1210), "dividend": (1425, 1161), "riskDerivative": (2246, 1950),
        "financialNotes": (37404, 16230), "consolidatedNotes": (25340, 9446),
        "mdna": (3540, 2113), "internalControl": (1056, 983),
        "rawMaterial": (1753, 1644), "salesOrder": (1074, 917),
    }
    for topic in sorted(before.keys()):
        s = topic_stats[topic]
        t, su = s["total"], s["success"]
        pct = su * 100 / t if t else 0
        bT, bS = before[topic]
        bP = bS * 100 / bT
        print(f"  {topic:30s} {bP:.1f}% -> {pct:.1f}% (diff={pct-bP:+.1f}%p)")
