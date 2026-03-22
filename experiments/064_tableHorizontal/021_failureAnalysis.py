"""
실험 ID: 064-021
실험명: 테이블 수평화 실패 패턴 분석

목적:
- block None 반환의 구체적 원인 분류
- 개선 가능한 실패 패턴 식별
- 괄호 내용 차이, 단위 헤더 실패 등 구체적 사례 수집

가설:
1. 실패의 상당 부분이 단위 헤더 복구 실패 (skip 분류 후 _stripUnitHeader 미동작)
2. 괄호 내용 차이로 항목 분산 → 겹침률 하락 → 이력형 오분류
3. multi_year Q 기간 파싱 실패가 상당 비율

방법:
1. 전 종목 순회, 실패 블록의 원인을 카테고리별 분류
2. 각 카테고리별 샘플 수집
3. 개선 가능성 평가

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-17
"""

import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "src"))
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


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir
    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    # 실패 원인 카테고리
    failReasons = Counter()  # reason → count
    failSamples = defaultdict(list)  # reason → [(code, topic, bo, sample)]
    MAX_SAMPLES = 5

    # 괄호 차이 분석
    bracketDiffs = []  # (code, topic, items_per_period)

    totalBlocks = 0
    successBlocks = 0

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
                totalBlocks += 1
                boRow = topicFrame.filter(
                    (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
                )
                if boRow.is_empty():
                    failReasons["empty_boRow"] += 1
                    continue

                allItems = []
                seenItems = set()
                periodItemVal = {}
                periodItemSets_debug = {}  # period → set of items (before filter)

                noDataPeriods = 0
                skipPeriods = 0
                skipAfterUnit = 0
                multiYearFailed = 0

                for p in periodCols:
                    md = boRow[p][0] if p in boRow.columns else None
                    if md is None:
                        noDataPeriods += 1
                        continue
                    m = re.match(r"\d{4}", p)
                    if m is None:
                        continue
                    pYear = int(m.group())

                    periodItems = set()

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
                                else:
                                    skipAfterUnit += 1
                            else:
                                skipPeriods += 1

                        if structType == "multi_year":
                            triples, _ = _parseMultiYear(sub, pYear)
                            collected = False
                            for rawItem, year, val in triples:
                                item = _normalizeItem(rawItem)
                                if year == str(pYear) and item:
                                    collected = True
                                    periodItems.add(item)
                                    if item not in seenItems:
                                        allItems.append(item)
                                        seenItems.add(item)
                                    if item not in periodItemVal:
                                        periodItemVal[item] = {}
                                    periodItemVal[item][p] = val
                            if not collected:
                                multiYearFailed += 1
                                # fallback
                                _PURE_KISU = {"당기", "전기", "전전기", "당반기", "전반기"}
                                headerHasPureKisu = any(c.strip() in _PURE_KISU for c in hc)
                                if len(hc) >= 2 and not headerHasPureKisu:
                                    rows, _, _ = _parseKeyValueOrMatrix(sub)
                                    for rawItem, vals in rows:
                                        item = _normalizeItem(rawItem)
                                        val = " | ".join(v for v in vals if v).strip()
                                        if val and item:
                                            periodItems.add(item)
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
                                    periodItems.add(item)
                                    if item not in seenItems:
                                        allItems.append(item)
                                        seenItems.add(item)
                                    if item not in periodItemVal:
                                        periodItemVal[item] = {}
                                    periodItemVal[item][p] = val

                    if periodItems:
                        periodItemSets_debug[p] = periodItems

                # 필터 전 항목 수
                rawCount = len(allItems)

                # 숫자만 항목 필터
                allItems = [it for it in allItems if not _isJunkItem(it)]

                if not allItems:
                    if rawCount == 0:
                        if skipPeriods > 0:
                            reason = "skip_no_unit_match"
                        elif noDataPeriods == len(periodCols):
                            reason = "all_periods_null"
                        elif multiYearFailed > 0:
                            reason = "multi_year_parse_fail"
                        else:
                            reason = "no_data_rows"
                    else:
                        reason = "all_junk_items"
                    failReasons[reason] += 1
                    if len(failSamples[reason]) < MAX_SAMPLES:
                        sample_md = None
                        for p in periodCols:
                            v = boRow[p][0] if p in boRow.columns else None
                            if v is not None:
                                sample_md = str(v)[:300]
                                break
                        failSamples[reason].append((code, topic, bo, sample_md))
                    continue

                # 이력형 감지
                pSets = {}
                for item in allItems:
                    for p2 in periodItemVal.get(item, {}):
                        if p2 not in pSets:
                            pSets[p2] = set()
                        pSets[p2].add(item)

                isHistory = False
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
                        isHistory = True

                if isHistory:
                    failReasons["history_skip"] += 1
                    continue

                # 목록형 감지
                if len(allItems) > 50:
                    failReasons["list_skip"] += 1
                    continue

                # 사용 기간 확인
                usedP = [p for p in periodCols if any(p in periodItemVal.get(it, {}) for it in allItems)]
                if not usedP:
                    failReasons["no_used_periods"] += 1
                    continue

                # 괄호 차이 분석: 기간별 항목 겹침 중 괄호 때문에 불일치하는 것
                if len(periodItemSets_debug) >= 2:
                    allUnion = set()
                    for s in periodItemSets_debug.values():
                        allUnion |= s
                    # 괄호 포함 항목 중 비슷한 것 찾기
                    bracketItems = [it for it in allUnion if "(" in it]
                    for bi in bracketItems:
                        base = bi.split("(")[0]
                        variants = [it for it in allUnion if it.startswith(base + "(") and it != bi]
                        if variants:
                            bracketDiffs.append((code, topic, bi, variants))

                successBlocks += 1

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(codes)}]...")

    print(f"\n=== 전체 결과 ===")
    print(f"총 블록: {totalBlocks}")
    print(f"성공: {successBlocks} ({successBlocks*100/totalBlocks:.1f}%)")
    print(f"실패: {totalBlocks - successBlocks} ({(totalBlocks-successBlocks)*100/totalBlocks:.1f}%)")

    print(f"\n=== 실패 원인 분류 ===")
    for reason, count in failReasons.most_common():
        pct = count * 100 / totalBlocks
        print(f"  {reason:30s} {count:6d} ({pct:.1f}%)")

    print(f"\n=== 실패 샘플 ===")
    for reason in ["skip_no_unit_match", "no_data_rows", "multi_year_parse_fail", "all_junk_items", "all_periods_null"]:
        samples = failSamples.get(reason, [])
        if samples:
            print(f"\n--- {reason} ---")
            for code, topic, bo, sample in samples[:3]:
                print(f"  [{code}] {topic} bo={bo}")
                if sample:
                    print(f"    {sample[:200]}")

    print(f"\n=== 괄호 차이 분석 ===")
    print(f"괄호 변형 발견: {len(bracketDiffs)}건")
    for code, topic, bi, variants in bracketDiffs[:10]:
        print(f"  [{code}] {topic}: '{bi}' vs {variants}")
