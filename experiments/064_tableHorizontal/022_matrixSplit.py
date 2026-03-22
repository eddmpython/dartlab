"""
실험 ID: 064-022
실험명: matrix multi-column 헤더별 분리 효과 측정

목적:
- 현재 파이프(|)로 합쳐지는 matrix 값을 헤더별 독립 항목으로 분리
- 분리 전후 성공률, 항목 수 변화, 이력형/목록형 감지 영향 확인

가설:
1. matrix 분리로 사용성이 크게 향상된다 (인원수=5 vs 5|-|-)
2. 항목 수 증가로 목록형(>50) 감지에 걸리는 경우는 드물다
3. 성공률에는 큰 변화 없다 (이미 성공하던 블록의 내용 개선)

방법:
1. 기존 방식 vs 분리 방식 비교 (30종목)
2. 분리 시 항목 수 변화 통계
3. 목록형/이력형 오탐 확인

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-17
"""

import sys, re
from collections import defaultdict, Counter
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "src"))
import polars as pl
from dartlab.engines.company.dart.docs.sections.pipeline import sections
from dartlab.engines.company.dart.docs.sections.tableParser import (
    splitSubtables, _headerCells, _isJunk, _dataRows, _classifyStructure,
    _parseMultiYear, _parseKeyValueOrMatrix, _normalizeItemName,
)

def _isPeriodCol(c):
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))

_SUFFIX_RE = re.compile(r"(사업)?부문$")
_KISU_RE = re.compile(
    r"제\d+기\s*(?:\d*분기|반기|말)?\s*"
    r"\(?(당기|전기|전전기|당반기|전반기|당분기|전분기)\)?"
)
_UNIT_ONLY_RE = re.compile(
    r"^[\(\[\（<〈]?\s*(?:<[^>]+>\s*)?[\(\[\（]?\s*"
    r"(?:단위|원화\s*단위|외화\s*단위|금액\s*단위).*$",
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


def _simulate(code, splitMatrix=False):
    """한 종목의 전 블록 수평화 시뮬레이션. splitMatrix=True면 matrix 분리 적용."""
    try:
        sec = sections(code)
    except (FileNotFoundError, ValueError):
        return None
    if sec is None:
        return None

    periodCols = [c for c in sec.columns if _isPeriodCol(c)]
    tableRows = sec.filter(pl.col("blockType") == "table")
    if tableRows.is_empty():
        return None

    results = {"total": 0, "success": 0, "items_before": 0, "items_after": 0,
               "list_blocked": 0, "split_applied": 0}

    for topic in tableRows["topic"].unique().to_list():
        topicFrame = sec.filter(pl.col("topic") == topic)
        tTable = topicFrame.filter(pl.col("blockType") == "table")
        bos = sorted(tTable["blockOrder"].unique().to_list())

        for bo in bos:
            results["total"] += 1
            boRow = topicFrame.filter(
                (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
            )
            if boRow.is_empty():
                continue

            allItems = []
            seenItems = set()
            periodItemVal = {}
            hadSplit = False

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
                            _PURE_KISU = {"당기", "전기", "전전기", "당반기", "전반기"}
                            headerHasPureKisu = any(c.strip() in _PURE_KISU for c in hc)
                            if not headerHasPureKisu:
                                rows, headerNames, _ = _parseKeyValueOrMatrix(sub)
                                for rawItem, vals in rows:
                                    item = _normalizeItem(rawItem)
                                    # matrix 분리 적용
                                    if splitMatrix and len(headerNames) >= 2 and len(vals) >= 2:
                                        hadSplit = True
                                        for hi, hname in enumerate(headerNames):
                                            v = vals[hi].strip() if hi < len(vals) else ""
                                            if not v:
                                                continue
                                            ci = f"{item}_{hname}"
                                            if ci not in seenItems:
                                                allItems.append(ci)
                                                seenItems.add(ci)
                                            if ci not in periodItemVal:
                                                periodItemVal[ci] = {}
                                            periodItemVal[ci][p] = v
                                    else:
                                        val = " | ".join(v for v in vals if v).strip()
                                        if val and item:
                                            if item not in seenItems:
                                                allItems.append(item)
                                                seenItems.add(item)
                                            if item not in periodItemVal:
                                                periodItemVal[item] = {}
                                            periodItemVal[item][p] = val

                    elif structType in ("key_value", "matrix"):
                        rows, headerNames, _ = _parseKeyValueOrMatrix(sub)
                        for rawItem, vals in rows:
                            item = _normalizeItem(rawItem)
                            # matrix 분리 적용
                            if splitMatrix and len(headerNames) >= 2 and len(vals) >= 2:
                                hadSplit = True
                                for hi, hname in enumerate(headerNames):
                                    v = vals[hi].strip() if hi < len(vals) else ""
                                    if not v:
                                        continue
                                    ci = f"{item}_{hname}"
                                    if ci not in seenItems:
                                        allItems.append(ci)
                                        seenItems.add(ci)
                                    if ci not in periodItemVal:
                                        periodItemVal[ci] = {}
                                    periodItemVal[ci][p] = v
                            else:
                                val = " | ".join(v for v in vals if v).strip()
                                if val and item:
                                    if item not in seenItems:
                                        allItems.append(item)
                                        seenItems.add(item)
                                    if item not in periodItemVal:
                                        periodItemVal[item] = {}
                                    periodItemVal[item][p] = val

            rawCount = len(allItems)
            allItems = [it for it in allItems if not _isJunkItem(it)]
            if not allItems:
                continue

            # 이력형 감지
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
                results["list_blocked"] += 1
                continue

            usedP = [p for p in periodCols if any(p in periodItemVal.get(it, {}) for it in allItems)]
            if not usedP:
                continue

            results["success"] += 1
            results["items_after"] += len(allItems)
            if hadSplit:
                results["split_applied"] += 1

    return results


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir
    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    # 전 종목 비교
    totals = {
        False: {"total": 0, "success": 0, "items": 0, "list_blocked": 0, "split_applied": 0},
        True: {"total": 0, "success": 0, "items": 0, "list_blocked": 0, "split_applied": 0},
    }

    for i, code in enumerate(codes):
        for splitMode in [False, True]:
            r = _simulate(code, splitMatrix=splitMode)
            if r is None:
                continue
            totals[splitMode]["total"] += r["total"]
            totals[splitMode]["success"] += r["success"]
            totals[splitMode]["items"] += r["items_after"]
            totals[splitMode]["list_blocked"] += r["list_blocked"]
            totals[splitMode]["split_applied"] += r["split_applied"]

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(codes)}]...")

    print("\n=== matrix multi-column 분리 효과 ===")
    for mode in [False, True]:
        t = totals[mode]
        label = "분리" if mode else "합침"
        pct = t["success"] * 100 / t["total"] if t["total"] else 0
        avgItems = t["items"] / t["success"] if t["success"] else 0
        print(f"  [{label}] total={t['total']} success={t['success']}({pct:.1f}%) "
              f"avgItems={avgItems:.1f} listBlocked={t['list_blocked']} "
              f"splitApplied={t['split_applied']}")

    # 차이
    d = totals[True]["success"] - totals[False]["success"]
    dp = d * 100 / totals[False]["total"] if totals[False]["total"] else 0
    print(f"\n  성공률 차이: {d:+d} ({dp:+.2f}%p)")
    print(f"  목록형 차단 증가: {totals[True]['list_blocked'] - totals[False]['list_blocked']:+d}")
