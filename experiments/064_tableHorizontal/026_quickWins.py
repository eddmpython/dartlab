"""
실험 ID: 064-026
실험명: 단기 개선 4가지 효과 측정

목적:
- 에이전트 토론 결과의 단기 개선안 4가지를 실험
- 각 개선의 독립 효과 + 누적 효과 측정
- 실제 show() 기준으로 수평화 성공률 측정

개선안:
A. _classifyStructure에 제XX기 헤더 패턴 추가
B. _normalizeItem 강화 (번호접두사, 주석(주1) 제거)
C. 임계값 완화 (Jaccard 0.15, 목록 100, sparse 0.3)
D. 서브테이블 독립 수평화 (bestHeader 하나가 아닌 각 그룹 독립)

실험일: 2026-03-18
"""

import re
import sys
from collections import defaultdict

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "src"))
import polars as pl

from dartlab.core.dataLoader import _dataDir
from dartlab.providers.dart.docs.sections.pipeline import sections
from dartlab.providers.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _headerCells,
    _isJunk,
    _normalizeHeader,
    _normalizeItemName,
    _parseKeyValueOrMatrix,
    _parseMultiYear,
    splitSubtables,
)


def _isPeriodCol(c):
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))


_SUFFIX_RE = re.compile(r"(사업)?부문$")
_KISU_RE = re.compile(
    r"제\d+기\s*(?:\d*분기|반기|말)?\s*"
    r"\(?(당기|전기|전전기|당반기|전반기|당분기|전분기)\)?"
)
_NOTE_REF_RE = re.compile(r"\(\*\d*(?:,\d+)*\)")
_PERIOD_KW_RE = re.compile(
    r"\d*분기|반기|당기|전기|전전기|당반기|전반기|당분기|전분기|당기말|전기말"
)
_KISU_HEADER_RE = re.compile(r"제\s*\d+\s*기")

# 원본 _normalizeItem
def _normalizeItemBase(name):
    name = _SUFFIX_RE.sub("", name).strip()
    name = _NOTE_REF_RE.sub("", name).strip()
    m = _KISU_RE.search(name)
    return m.group(1) if m else name

# 강화 _normalizeItem (B안)
def _normalizeItemStrong(name):
    name = _SUFFIX_RE.sub("", name).strip()
    name = _NOTE_REF_RE.sub("", name).strip()
    name = re.sub(r"^\d+[\.\)]\s*", "", name)      # 번호 접두사 제거
    name = re.sub(r"\(\s*주\s*\d*\s*\)", "", name)  # (주1) 제거
    m = _KISU_RE.search(name)
    return m.group(1) if m else name


def _groupHeader(hc):
    h = _normalizeHeader(hc)
    h = _PERIOD_KW_RE.sub("", h)
    h = re.sub(r"\| *\|", "|", h)
    h = re.sub(r"\s+", " ", h).strip()
    return h


def _stripUnitHeader(sub):
    _UNIT_ONLY_RE = re.compile(
        r"^[\(\[\（<〈]?\s*(?:<[^>]+>\s*)?[\(\[\（]?\s*"
        r"(?:단위|원화\s*단위|외화\s*단위|금액\s*단위).*$",
        re.IGNORECASE,
    )
    _DATE_ONLY_RE = re.compile(r"^\(?\s*기준일\s*:")
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


def simulate(code, *, enableA=False, enableB=False, enableC=False):
    """한 종목의 show() 시뮬레이션."""
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

    normalizeItem = _normalizeItemStrong if enableB else _normalizeItemBase

    # 임계값
    JACCARD_THRESH = 0.15 if enableC else 0.3
    LIST_THRESH = 100 if enableC else 50
    SPARSE_ITEMS_THRESH = 15
    SPARSE_FILL_THRESH = 0.3 if enableC else 0.5

    total = 0
    success = 0
    fallback = 0

    for topic in tableRows["topic"].unique().to_list():
        topicFrame = sec.filter(pl.col("topic") == topic)
        tTable = topicFrame.filter(pl.col("blockType") == "table")
        bos = sorted(tTable["blockOrder"].unique().to_list())

        for bo in bos:
            total += 1
            boRow = topicFrame.filter(
                (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
            )
            if boRow.is_empty():
                fallback += 1
                continue

            # 헤더 그룹핑
            headerGroups = {}
            for p in periodCols:
                md = boRow[p][0] if p in boRow.columns else None
                if md is None:
                    continue
                for sub in splitSubtables(str(md)):
                    hc = _headerCells(sub)
                    if _isJunk(hc):
                        continue
                    dr = _dataRows(sub)
                    if not dr:
                        continue
                    st = _classifyStructure(hc)
                    if st == "skip":
                        fixed = _stripUnitHeader(sub)
                        if fixed:
                            fhc = _headerCells(fixed)
                            fdr = _dataRows(fixed)
                            if fhc and not _isJunk(fhc) and fdr:
                                hc = fhc
                    gh = _groupHeader(hc)
                    if gh not in headerGroups:
                        headerGroups[gh] = []
                    if p not in headerGroups[gh]:
                        headerGroups[gh].append(p)

            if not headerGroups:
                fallback += 1
                continue

            bestHeader = max(headerGroups, key=lambda k: len(headerGroups[k]))
            bestPeriods = set(headerGroups[bestHeader])

            # 수평화 시뮬레이션
            allItems = []
            seenItems = set()
            periodItemVal = {}

            for p in periodCols:
                if p not in bestPeriods:
                    continue
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
                    if structType == "skip":
                        fixed = _stripUnitHeader(sub)
                        if fixed:
                            fhc = _headerCells(fixed)
                            fdr = _dataRows(fixed)
                            if fhc and not _isJunk(fhc) and fdr:
                                structType = _classifyStructure(fhc)
                                hc = fhc
                                sub = fixed

                    # A: 기수 헤더 패턴
                    if enableA and structType == "matrix":
                        joined = " ".join(hc)
                        if _KISU_HEADER_RE.search(joined):
                            structType = "multi_year"

                    gh = _groupHeader(hc)
                    if gh != bestHeader:
                        continue

                    if structType == "multi_year":
                        triples, _ = _parseMultiYear(sub, pYear)
                        for rawItem, year, val in triples:
                            item = normalizeItem(rawItem)
                            if year == str(pYear) and item:
                                if item not in seenItems:
                                    allItems.append(item)
                                    seenItems.add(item)
                                if item not in periodItemVal:
                                    periodItemVal[item] = {}
                                periodItemVal[item][p] = val
                        if not any(year == str(pYear) for _, year, _ in triples):
                            # fallback to kv
                            rows, headerNames, _ = _parseKeyValueOrMatrix(sub)
                            for rawItem, vals in rows:
                                item = normalizeItem(rawItem)
                                nonEmpty = [v for v in vals if v.strip()]
                                if len(headerNames) >= 2 and len(nonEmpty) >= 2 and len(nonEmpty) <= len(headerNames):
                                    for hi, hname in enumerate(headerNames):
                                        v = vals[hi].strip() if hi < len(vals) else ""
                                        if not v or v == "-":
                                            continue
                                        ci = f"{item}_{hname}"
                                        if ci not in seenItems:
                                            allItems.append(ci)
                                            seenItems.add(ci)
                                        if ci not in periodItemVal:
                                            periodItemVal[ci] = {}
                                        periodItemVal[ci][p] = v
                                else:
                                    val = " | ".join(v for v in vals if v.strip()).strip()
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
                            item = normalizeItem(rawItem)
                            nonEmpty = [v for v in vals if v.strip()]
                            if len(headerNames) >= 2 and len(nonEmpty) >= 2 and len(nonEmpty) <= len(headerNames):
                                for hi, hname in enumerate(headerNames):
                                    v = vals[hi].strip() if hi < len(vals) else ""
                                    if not v or v == "-":
                                        continue
                                    ci = f"{item}_{hname}"
                                    if ci not in seenItems:
                                        allItems.append(ci)
                                        seenItems.add(ci)
                                    if ci not in periodItemVal:
                                        periodItemVal[ci] = {}
                                    periodItemVal[ci][p] = v
                            else:
                                val = " | ".join(v for v in vals if v.strip()).strip()
                                if val and item:
                                    if item not in seenItems:
                                        allItems.append(item)
                                        seenItems.add(item)
                                    if item not in periodItemVal:
                                        periodItemVal[item] = {}
                                    periodItemVal[item][p] = val

            # 필터
            def _isJunkItem(name):
                stripped = re.sub(r"[,.\-\s]", "", name)
                return stripped.isdigit() or not stripped

            allItems = [it for it in allItems if not _isJunkItem(it)]
            if not allItems:
                fallback += 1
                continue

            # 이력형
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
                if aO < JACCARD_THRESH and len(allItems) > 5:
                    fallback += 1
                    continue

            if len(allItems) > LIST_THRESH:
                fallback += 1
                continue

            usedP = [p for p in periodCols if any(p in periodItemVal.get(it, {}) for it in allItems)]
            if not usedP:
                fallback += 1
                continue

            # sparse
            if len(usedP) >= 3 and len(allItems) > SPARSE_ITEMS_THRESH:
                totalCells = len(allItems) * len(usedP)
                filledCells = sum(
                    1 for item in allItems for p in usedP
                    if periodItemVal.get(item, {}).get(p)
                )
                fillRate = filledCells / totalCells if totalCells > 0 else 0
                if fillRate < SPARSE_FILL_THRESH:
                    fallback += 1
                    continue

            success += 1

    return {"total": total, "success": success, "fallback": fallback}


if __name__ == "__main__":
    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    configs = [
        ("현재(baseline)", {}),
        ("A: 기수헤더", {"enableA": True}),
        ("B: 정규화강화", {"enableB": True}),
        ("C: 임계값완화", {"enableC": True}),
        ("A+B+C: 전체적용", {"enableA": True, "enableB": True, "enableC": True}),
    ]

    for label, kwargs in configs:
        totals = {"total": 0, "success": 0, "fallback": 0}
        for i, code in enumerate(codes):
            r = simulate(code, **kwargs)
            if r:
                totals["total"] += r["total"]
                totals["success"] += r["success"]
                totals["fallback"] += r["fallback"]
            if (i + 1) % 100 == 0:
                print(f"  [{label}] {i+1}/{len(codes)}...")

        t = totals["total"]
        s = totals["success"]
        fb = totals["fallback"]
        pct = s * 100 / t if t else 0
        fbPct = fb * 100 / t if t else 0
        print(f"  [{label}] total={t} success={s}({pct:.1f}%) fallback={fb}({fbPct:.1f}%)")
        print()
