"""
실험 ID: 066-004
실험명: 캐노니컬 스키마 283종목 전수 검증

목적:
- 002_canonicalSchema.py의 로직을 283종목 전수에서 검증
- 기존 방식 대비 성공률 비교
- 새로 수평화되는 블록의 실제 데이터 품질 확인

방법:
1. 283종목 전수 스캔
2. 각 topic/block에서 스키마 기반 vs 기존 기반 성공 여부 비교
3. 스키마만 성공한 사례의 실제 DataFrame 샘플 수집

결과 (실행 후 작성):
-

결론:
-

실험일: 2026-03-18
"""

import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.core.dataLoader import _dataDir
from dartlab.providers.dart.docs.sections.pipeline import sections
from dartlab.providers.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _extractUnit,
    _headerCells,
    _isJunk,
    _normalizeHeader,
    _normalizeItemName,
    _parseKeyValueOrMatrix,
    _parseMultiYear,
    splitSubtables,
)

# 002에서 가져온 핵심 함수들
_SUFFIX_RE = re.compile(r"(사업)?부문$")
_KISU_RE = re.compile(r"제\d+기\s*(?:\d*분기|반기|말)?\s*\(?(당기|전기|전전기|당반기|전반기|당분기|전분기)\)?")
_NOTE_REF_RE = re.compile(r"\(\*\d*(?:,\d+)*\)")
_PERIOD_KW_RE = re.compile(r"\d*분기|반기|당기|전기|전전기|당반기|전반기|당분기|전분기|당기말|전기말")

def _normalizeItem(name):
    name = _normalizeItemName(name)
    name = _SUFFIX_RE.sub("", name).strip()
    name = _NOTE_REF_RE.sub("", name).strip()
    m = _KISU_RE.search(name)
    return m.group(1) if m else name

def _groupHeader(hc):
    h = _normalizeHeader(hc)
    h = _PERIOD_KW_RE.sub("", h)
    h = re.sub(r"\| *\|", "|", h)
    h = re.sub(r"\s+", " ", h).strip()
    return h

def _levenshteinRatio(s1, s2):
    if s1 == s2: return 1.0
    maxLen = max(len(s1), len(s2))
    if maxLen == 0: return 1.0
    prev = list(range(len(s2) + 1))
    for i in range(1, len(s1) + 1):
        curr = [i] + [0] * len(s2)
        for j in range(1, len(s2) + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            curr[j] = min(curr[j-1]+1, prev[j]+1, prev[j-1]+cost)
        prev = curr
    return 1.0 - prev[len(s2)] / maxLen


def schemaHorizontalize(sec, topic, bo, periodCols):
    """캐노니컬 스키마 기반 수평화 (002에서 추출)."""
    topicFrame = sec.filter(pl.col("topic") == topic)
    boRow = topicFrame.filter(
        (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
    )
    if boRow.is_empty():
        return None

    # 1. 전 기간 스캔 → 프로파일
    headerGroups = defaultdict(list)  # normHeader → [(period, items, structType)]
    for p in periodCols:
        md = boRow[p][0] if p in boRow.columns else None
        if md is None:
            continue
        pYear = int(re.match(r"\d{4}", p).group()) if re.match(r"\d{4}", p) else None
        for sub in splitSubtables(str(md)):
            hc = _headerCells(sub)
            if _isJunk(hc): continue
            dr = _dataRows(sub)
            if not dr: continue
            gh = _groupHeader(hc)
            st = _classifyStructure(hc)
            items = []
            if st == "multi_year" and pYear:
                triples, _ = _parseMultiYear(sub, pYear)
                for rawItem, year, val in triples:
                    item = _normalizeItem(rawItem)
                    if item and item not in items:
                        items.append(item)
            elif st in ("key_value", "matrix"):
                rows, hn, _ = _parseKeyValueOrMatrix(sub)
                for rawItem, vals in rows:
                    item = _normalizeItem(rawItem)
                    if item and item not in items:
                        items.append(item)
            headerGroups[gh].append({"period": p, "items": items, "structType": st})

    if not headerGroups:
        return None

    # 2. 가장 큰 헤더 그룹 선택
    bestHeader = max(headerGroups, key=lambda k: len(set(e["period"] for e in headerGroups[k])))
    group = headerGroups[bestHeader]
    periods = sorted(set(e["period"] for e in group))
    if len(periods) < 2:
        return None

    # 3. canonical items + synonym map
    canonicalItems = []
    seenItems = set()
    itemFreq = Counter()
    for entry in group:
        for item in entry["items"]:
            if item not in seenItems:
                canonicalItems.append(item)
                seenItems.add(item)
            itemFreq[item] += 1

    # synonym map (위치 기반)
    synonymMap = {}
    maxLen = max(len(e["items"]) for e in group) if group else 0
    for pos in range(maxLen):
        namesAtPos = [e["items"][pos] for e in group if pos < len(e["items"])]
        if not namesAtPos: continue
        representative = Counter(namesAtPos).most_common(1)[0][0]
        for name in set(namesAtPos):
            if name != representative:
                s1 = re.sub(r"[\s\-_·.]", "", name)
                s2 = re.sub(r"[\s\-_·.]", "", representative)
                if s1 == s2 or (len(s1) > 3 and _levenshteinRatio(s1, s2) >= 0.75):
                    synonymMap[name] = representative

    # 4. 이력형/목록형 감지
    if len(canonicalItems) > 50:
        return None
    periodItemSets = defaultdict(set)
    for entry in group:
        periodItemSets[entry["period"]].update(entry["items"])
    sets = list(periodItemSets.values())
    if len(sets) >= 2:
        tO = tP = 0
        for i in range(len(sets)):
            for j in range(i+1, min(i+4, len(sets))):
                u = len(sets[i] | sets[j])
                inter = len(sets[i] & sets[j])
                if u > 0: tO += inter/u; tP += 1
        if tP > 0 and tO/tP < 0.3 and len(canonicalItems) > 5:
            return None

    # 5. 수평화
    def resolve(item):
        return synonymMap.get(item, item)

    allItems = []
    seenFinal = set()
    periodItemVal = {}

    for p in periods:
        md = boRow[p][0] if p in boRow.columns else None
        if md is None: continue
        pYear = int(re.match(r"\d{4}", p).group()) if re.match(r"\d{4}", p) else None
        for sub in splitSubtables(str(md)):
            hc = _headerCells(sub)
            if _isJunk(hc): continue
            dr = _dataRows(sub)
            if not dr: continue
            gh = _groupHeader(hc)
            if gh != bestHeader: continue
            st = _classifyStructure(hc)

            if st == "multi_year" and pYear:
                triples, _ = _parseMultiYear(sub, pYear)
                for rawItem, year, val in triples:
                    item = resolve(_normalizeItem(rawItem))
                    if year == str(pYear) and item:
                        if item not in seenFinal:
                            allItems.append(item)
                            seenFinal.add(item)
                        if item not in periodItemVal: periodItemVal[item] = {}
                        periodItemVal[item][p] = val
            elif st in ("key_value", "matrix"):
                rows, headerNames, _ = _parseKeyValueOrMatrix(sub)
                for rawItem, vals in rows:
                    item = resolve(_normalizeItem(rawItem))
                    nonEmpty = [v for v in vals if v.strip()]
                    if len(headerNames) >= 2 and len(nonEmpty) >= 2 and len(nonEmpty) <= len(headerNames):
                        for hi, hname in enumerate(headerNames):
                            v = vals[hi].strip() if hi < len(vals) else ""
                            if not v or v == "-": continue
                            ci = f"{item}_{hname}"
                            if ci not in seenFinal:
                                allItems.append(ci)
                                seenFinal.add(ci)
                            if ci not in periodItemVal: periodItemVal[ci] = {}
                            periodItemVal[ci][p] = v
                    else:
                        val = " | ".join(v for v in vals if v.strip()).strip()
                        if val and item:
                            if item not in seenFinal:
                                allItems.append(item)
                                seenFinal.add(item)
                            if item not in periodItemVal: periodItemVal[item] = {}
                            periodItemVal[item][p] = val

    def _isJunkItem(name):
        stripped = re.sub(r"[,.\-\s]", "", name)
        return stripped.isdigit() or not stripped
    allItems = [it for it in allItems if not _isJunkItem(it)]
    if not allItems:
        return None

    usedP = [p for p in periodCols if any(p in periodItemVal.get(it, {}) for it in allItems)]
    if len(usedP) < 2:
        return None

    rows = []
    for item in allItems:
        if not any(periodItemVal.get(item, {}).get(p) for p in usedP):
            continue
        row = {"항목": item}
        for p in usedP:
            row[p] = periodItemVal.get(item, {}).get(p)
        rows.append(row)

    if not rows:
        return None
    schema = {"항목": pl.Utf8}
    for p in usedP:
        schema[p] = pl.Utf8
    return pl.DataFrame(rows, schema=schema)


if __name__ == "__main__":
    pl.Config.set_tbl_cols(6)
    pl.Config.set_fmt_str_lengths(60)

    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    totalBlocks = 0
    schemaSuccess = 0
    baselineSuccess = 0  # 기존 show() 기반 (company.py)
    schemaOnly = 0
    baselineOnly = 0
    bothSuccess = 0
    bothFail = 0
    schemaOnlySamples = []

    tStart = time.time()

    for ci, code in enumerate(codes):
        try:
            sec = sections(code)
        except Exception:
            continue
        if sec is None:
            continue

        periodCols = [c for c in sec.columns if re.match(r"^\d{4}(Q[1-4])?$", c)]
        tableRows = sec.filter(pl.col("blockType") == "table")
        if tableRows.is_empty():
            continue

        # 기존 방식: Company.show() 사용
        try:
            from dartlab.providers.dart.company import Company
            comp = Company(code)
        except Exception:
            continue

        for topic in tableRows["topic"].unique().to_list():
            topicFrame = sec.filter(pl.col("topic") == topic)
            tTable = topicFrame.filter(pl.col("blockType") == "table")
            for bo in tTable["blockOrder"].unique().to_list():
                totalBlocks += 1

                # 스키마 기반
                sResult = schemaHorizontalize(sec, topic, bo, periodCols)
                sOk = sResult is not None and "항목" in sResult.columns and sResult.height > 0

                # 기존 기반
                bResult = comp.show(topic, bo)
                bOk = bResult is not None and "항목" in bResult.columns

                if sOk and bOk:
                    bothSuccess += 1
                elif sOk and not bOk:
                    schemaOnly += 1
                    if len(schemaOnlySamples) < 20:
                        schemaOnlySamples.append((code, topic, bo, sResult))
                elif bOk and not sOk:
                    baselineOnly += 1
                else:
                    bothFail += 1

                if sOk: schemaSuccess += 1
                if bOk: baselineSuccess += 1

        if (ci + 1) % 50 == 0:
            elapsed = time.time() - tStart
            print(f"  [{ci+1}/{len(codes)}] {elapsed:.0f}s schema={schemaSuccess} baseline={baselineSuccess}")

    elapsed = time.time() - tStart
    print(f"\n{'='*60}")
    print(f"283종목 전수 검증 ({elapsed:.0f}s)")
    print(f"{'='*60}")
    print(f"총 blocks: {totalBlocks}")
    print(f"스키마 성공: {schemaSuccess} ({schemaSuccess*100/totalBlocks:.1f}%)")
    print(f"기존 성공:   {baselineSuccess} ({baselineSuccess*100/totalBlocks:.1f}%)")
    print(f"둘 다 성공:  {bothSuccess}")
    print(f"스키마만:    {schemaOnly}")
    print(f"기존만:      {baselineOnly}")
    print(f"둘 다 실패:  {bothFail}")

    print(f"\n=== 스키마만 성공한 사례 (실제 데이터) ===")
    for code, topic, bo, result in schemaOnlySamples[:10]:
        pCols = [c for c in result.columns if c != "항목"]
        print(f"\n[{code}] {topic} bo={bo}: {result.shape}")
        print(result.select(["항목"] + pCols[-2:]).head(5))
