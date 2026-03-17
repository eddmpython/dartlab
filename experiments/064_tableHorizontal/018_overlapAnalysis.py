"""
실험 ID: 064-018
실험명: overlap_filtered 상세 분석

목적:
- 핵심 topic의 overlap_filtered 케이스가 정상 스킵인지 과도한 필터인지 확인
- 겹침률 분포, 항목 수 분포 확인
- 기수명/날짜 포함 항목이 겹침률을 낮추는 패턴 확인

방법:
1. businessOverview, fsSummary, mdna, dividend에서 overlap_filtered 케이스 수집
2. overlap 값과 항목 수 분포 확인
3. 항목명 샘플 확인

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
    return name


def _isJunkItem(name):
    stripped = re.sub(r"[,.\-\s]", "", name)
    return stripped.isdigit() or not stripped


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir

    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    target_topics = ["businessOverview", "fsSummary", "mdna", "dividend",
                     "audit", "boardOfDirectors"]

    print(f"overlap_filtered 상세 분석")
    print("=" * 70)

    overlap_data = defaultdict(list)  # topic -> [(code, bo, overlap, itemCount, sample_items)]

    for i, code in enumerate(codes):
        try:
            sec = sections(code)
        except (FileNotFoundError, ValueError):
            continue
        if sec is None:
            continue

        periodCols = [c for c in sec.columns if _isPeriodCol(c)]

        for topic in target_topics:
            topicFrame = sec.filter(pl.col("topic") == topic)
            tTableRows = topicFrame.filter(pl.col("blockType") == "table")
            if tTableRows.is_empty():
                continue

            blockOrders = sorted(tTableRows["blockOrder"].unique().to_list())
            for bo in blockOrders:
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
                                fixedHc = _headerCells(fixed)
                                fixedDr = _dataRows(fixed)
                                if fixedHc and not _isJunk(fixedHc) and fixedDr:
                                    structType = _classifyStructure(fixedHc)
                                    sub = fixed

                        if structType == "multi_year":
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
                            if not any(1 for _, y, _ in triples if y == str(pYear)):
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

                allItems = [it for it in allItems if not _isJunkItem(it)]
                if not allItems:
                    continue
                if len(allItems) > 50:
                    continue

                # overlap 계산
                periodItemSets = {}
                for item in allItems:
                    for p2 in periodItemVal.get(item, {}):
                        if p2 not in periodItemSets:
                            periodItemSets[p2] = set()
                        periodItemSets[p2].add(item)

                if len(periodItemSets) < 2:
                    continue

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
                    overlap_data[topic].append({
                        "code": code, "bo": bo,
                        "overlap": avgOverlap,
                        "itemCount": len(allItems),
                        "items": allItems[:10],
                        "periodCount": len(periodItemSets),
                    })

        if (i + 1) % 100 == 0:
            print(f"  [{i+1}/{len(codes)}]...")

    # 결과
    for topic in target_topics:
        data = overlap_data.get(topic, [])
        if not data:
            continue
        print(f"\n{'='*70}")
        print(f"{topic}: {len(data)}건 overlap_filtered")
        print(f"{'='*70}")

        # overlap 분포
        overlaps = [d["overlap"] for d in data]
        itemCounts = [d["itemCount"] for d in data]
        print(f"  overlap: min={min(overlaps):.2f}, max={max(overlaps):.2f}, avg={sum(overlaps)/len(overlaps):.2f}")
        print(f"  itemCount: min={min(itemCounts)}, max={max(itemCounts)}, avg={sum(itemCounts)/len(itemCounts):.1f}")

        # overlap 히스토그램 (0-0.05, 0.05-0.1, 0.1-0.15, 0.15-0.2, 0.2-0.25, 0.25-0.3)
        bins = [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
        for k in range(len(bins) - 1):
            count = sum(1 for o in overlaps if bins[k] <= o < bins[k+1])
            print(f"    [{bins[k]:.2f}, {bins[k+1]:.2f}): {count}")

        # 샘플 (overlap 높은 것 = 가까스로 걸린 것)
        data_sorted = sorted(data, key=lambda d: -d["overlap"])
        print(f"\n  경계 근처 (overlap 0.2~0.3) 샘플:")
        for d in data_sorted[:5]:
            if d["overlap"] < 0.2:
                break
            print(f"    {d['code']} bo={d['bo']} overlap={d['overlap']:.3f} items={d['itemCount']} periods={d['periodCount']}")
            print(f"      {d['items'][:6]}")
