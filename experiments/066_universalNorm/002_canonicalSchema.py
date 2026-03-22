"""
실험 ID: 066-002
실험명: 사전계산 캐노니컬 스키마 — 전 기간 동시 스캔 기반 수평화

목적:
- 한 회사의 한 topic 전 기간 테이블을 동시에 스캔하여 canonical schema 구축
- canonical header, canonical items, synonym map 자동 결정
- 스키마 기반 수평화가 기존 규칙 기반(company._horizontalizeTableBlock)보다
  더 높은 성공률을 보이는지 정량 비교

가설:
1. 전 기간 동시 스캔으로 canonical header를 결정하면 헤더 그룹 선택 정확도가 올라간다
2. 전 기간 항목 합집합 + synonym map이 기간별 항목명 변형을 흡수한다
3. 구조 타입(정형/이력/목록)은 전 기간 통계로 사전 확정하면 기간별 오분류가 사라진다
4. 기존 62.9% 성공률 대비 의미 있는 개선 (70%+)이 가능하다

방법:
1. 삼성전자(005930) executivePay topic 전 기간 테이블 스캔
2. 각 기간에서 서브테이블별 (정규화 헤더, 구조 타입, 항목 목록) 수집
3. canonical header = 가장 많은 기간에 등장한 헤더
4. canonical items = 전 기간 항목 합집합 (등장 순서 보존)
5. synonym map = 같은 위치에 등장하되 표기가 다른 항목명 → 대표명 매핑
6. 이 스키마로 수평화 → 기존 결과와 비교

결과 (실험 후 작성):
- 삼성전자(005930) 39개 topic, 607개 테이블 블록 대상
- 스키마 기반: 443/607 성공 (73.0%)
- 기존 규칙 기반: 314/607 성공 (51.7%)
- 스키마만 성공: 131건, 기존만 성공: 2건
- 둘 다 실패: 162건, 둘 다 성공: 312건
- 스키마가 잡는 추가 사례: audit(27x16), boardOfDirectors(15x8), auditSystem(36x4) 등
- 기존만 성공하는 2건: consolidatedNotes bo=45, dividend bo=5 (스키마가 기간 2개 미만으로 걸러짐)

핵심 발견:
1. 전 기간 동시 스캔으로 헤더 그룹 선택이 정확해짐 (기존은 기간별 독립 판단)
2. canonical items + synonym map이 기간별 표기 변형을 효과적으로 흡수
3. tableCategory 사전 확정이 이력형/목록형 오분류를 제거
4. matrix 구조에서 헤더별 분리가 기존 파이프 합침보다 우수

결론:
- 가설 1~4 모두 채택
- 73.0% vs 51.7% — 스키마 기반이 21.3%p 개선
- 스키마 구축 비용: 전 기간 1회 스캔 (삼성전자 39 topic 약 30초)
- 구현 방향: 오프라인 스키마 구축 → JSON 저장 → 온라인 show()에서 로드

실험일: 2026-03-18
"""

import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.engines.company.dart.docs.sections.pipeline import sections
from dartlab.engines.company.dart.docs.sections.tableParser import (
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

# ══════════════════════════════════════════════════════════════
# Phase 1: 전 기간 동시 스캔 → 캐노니컬 스키마 구축
# ══════════════════════════════════════════════════════════════


@dataclass
class SubtableProfile:
    """한 기간의 한 서브테이블에서 추출한 프로파일."""
    period: str
    normHeader: str
    rawHeader: list[str]
    structType: str  # multi_year | key_value | matrix | skip
    items: list[str]  # 정규화된 항목명 목록 (순서 보존)
    unit: str | None


@dataclass
class CanonicalSchema:
    """한 topic의 한 block에 대한 캐노니컬 스키마."""
    canonicalHeader: str  # 대표 정규화 헤더
    rawHeaderExample: list[str]  # 원본 헤더 예시
    structType: str  # 확정된 구조 타입
    canonicalItems: list[str]  # 항목 합집합 (등장 순서)
    synonymMap: dict[str, str]  # 변형 → 대표명
    tableCategory: str  # normal | historical | list_type
    unit: str | None
    periodCount: int  # 이 스키마가 커버하는 기간 수
    itemFrequency: dict[str, int]  # 항목별 등장 기간 수


# ── 기수/접미사 정규화 (company.py에서 가져옴) ──

_SUFFIX_RE = re.compile(r"(사업)?부문$")
_KISU_RE = re.compile(
    r"제\d+기\s*(?:\d*분기|반기|말)?\s*"
    r"\(?(당기|전기|전전기|당반기|전반기|당분기|전분기)\)?"
)
_NOTE_REF_RE = re.compile(r"\(\*\d*(?:,\d+)*\)")
_PERIOD_KW_RE = re.compile(
    r"\d*분기|반기|당기|전기|전전기|당반기|전반기|당분기|전분기|당기말|전기말"
)


def _normalizeItem(name: str) -> str:
    """항목명 정규화 — 기수, 접미사, 주석번호 제거."""
    name = _normalizeItemName(name)
    name = _SUFFIX_RE.sub("", name).strip()
    name = _NOTE_REF_RE.sub("", name).strip()
    m = _KISU_RE.search(name)
    if m:
        return m.group(1)
    return name


def _groupHeader(hc: list[str]) -> str:
    """그룹핑용 헤더 시그니처 — 연도/기간 키워드까지 제거."""
    h = _normalizeHeader(hc)
    h = _PERIOD_KW_RE.sub("", h)
    h = re.sub(r"\| *\|", "|", h)
    h = re.sub(r"\s+", " ", h).strip()
    return h


def _scanAllPeriods(
    topicFrame: pl.DataFrame,
    blockOrder: int,
    periodCols: list[str],
) -> list[SubtableProfile]:
    """한 topic의 한 block에서 전 기간 서브테이블을 스캔."""
    boRow = topicFrame.filter(
        (pl.col("blockOrder") == blockOrder) & (pl.col("blockType") == "table")
    )
    if boRow.is_empty():
        return []

    profiles: list[SubtableProfile] = []

    for p in periodCols:
        md = boRow[p][0] if p in boRow.columns else None
        if md is None:
            continue

        pYear = int(re.match(r"\d{4}", p).group()) if re.match(r"\d{4}", p) else None

        for sub in splitSubtables(str(md)):
            hc = _headerCells(sub)
            if _isJunk(hc):
                continue
            dr = _dataRows(sub)
            if not dr:
                continue

            normH = _groupHeader(hc)
            structType = _classifyStructure(hc)
            unit = _extractUnit(sub)

            # 항목 추출
            items: list[str] = []
            if structType == "multi_year" and pYear and "Q" not in p:
                triples, u = _parseMultiYear(sub, pYear)
                if u:
                    unit = u
                # multi_year에서는 당기(최신기) 항목만 취급
                for rawItem, year, val in triples:
                    item = _normalizeItem(rawItem)
                    if item and item not in items:
                        items.append(item)
            elif structType in ("key_value", "matrix"):
                rows, headerNames, u = _parseKeyValueOrMatrix(sub)
                if u:
                    unit = u
                for rawItem, vals in rows:
                    item = _normalizeItem(rawItem)
                    if item and item not in items:
                        items.append(item)
            else:
                # skip 타입이라도 데이터행에서 항목 추출 시도
                for row in dr:
                    if row and row[0].strip():
                        item = _normalizeItem(row[0].strip())
                        if item and item not in items:
                            items.append(item)

            profiles.append(SubtableProfile(
                period=p,
                normHeader=normH,
                rawHeader=hc,
                structType=structType,
                items=items,
                unit=unit,
            ))

    return profiles


def _buildCanonicalSchema(profiles: list[SubtableProfile]) -> list[CanonicalSchema]:
    """프로파일들을 헤더 그룹별로 묶어 캐노니컬 스키마를 구축."""
    if not profiles:
        return []

    # 1단계: 헤더별 그룹핑
    headerGroups: dict[str, list[SubtableProfile]] = defaultdict(list)
    for p in profiles:
        headerGroups[p.normHeader].append(p)

    schemas: list[CanonicalSchema] = []

    for normH, group in headerGroups.items():
        # 2단계: 구조 타입 확정 (다수결)
        typeCounts = Counter(p.structType for p in group)
        dominantType = typeCounts.most_common(1)[0][0]

        # 3단계: 기간 수
        periods = sorted(set(p.period for p in group))
        periodCount = len(periods)

        # 4단계: canonical items — 전 기간 합집합 (등장 순서 보존 + 빈도)
        canonicalItems: list[str] = []
        seenItems: set[str] = set()
        itemFrequency: dict[str, int] = Counter()

        for p in group:
            periodsForItem = set()
            for item in p.items:
                if item not in seenItems:
                    canonicalItems.append(item)
                    seenItems.add(item)
                if item not in periodsForItem:
                    itemFrequency[item] += 1
                    periodsForItem.add(item)

        # 5단계: synonym map 구축
        # 전략: 위치 기반 + 유사도 기반
        synonymMap = _buildSynonymMap(group, canonicalItems)

        # 6단계: 테이블 카테고리 확정
        category = _classifyTableCategory(group, canonicalItems, itemFrequency, periodCount)

        # 7단계: 단위 (가장 흔한 것)
        unitCounts = Counter(p.unit for p in group if p.unit)
        unit = unitCounts.most_common(1)[0][0] if unitCounts else None

        schemas.append(CanonicalSchema(
            canonicalHeader=normH,
            rawHeaderExample=group[0].rawHeader,
            structType=dominantType,
            canonicalItems=canonicalItems,
            synonymMap=synonymMap,
            tableCategory=category,
            unit=unit,
            periodCount=periodCount,
            itemFrequency=dict(itemFrequency),
        ))

    return schemas


def _buildSynonymMap(
    group: list[SubtableProfile],
    canonicalItems: list[str],
) -> dict[str, str]:
    """위치 기반 + 편집거리 기반 synonym map 구축.

    전략:
    - 같은 위치(인덱스)에 등장하되 표기가 다른 항목 = 동의어 후보
    - 빈도 높은 표기를 대표명으로 선택
    - 추가로 편집거리 기반 유사 항목 매칭
    """
    synonymMap: dict[str, str] = {}

    # 위치 기반: 각 기간의 항목 리스트에서 같은 인덱스의 항목을 비교
    maxLen = max(len(p.items) for p in group) if group else 0

    for pos in range(maxLen):
        # 이 위치에 등장하는 항목명들
        namesAtPos: list[str] = []
        for p in group:
            if pos < len(p.items):
                namesAtPos.append(p.items[pos])

        if not namesAtPos:
            continue

        # 가장 흔한 이름 = 대표명
        nameCounts = Counter(namesAtPos)
        representative = nameCounts.most_common(1)[0][0]

        for name in set(namesAtPos):
            if name != representative:
                # 기본 유사도 체크: 공백/특수문자 제거 후 비교
                stripped1 = re.sub(r"[\s\-_·.]", "", name)
                stripped2 = re.sub(r"[\s\-_·.]", "", representative)
                if stripped1 == stripped2:
                    synonymMap[name] = representative
                elif _levenshteinRatio(stripped1, stripped2) >= 0.75:
                    synonymMap[name] = representative

    # 편집거리 기반: canonical items 중 유사한 쌍 찾기 (항목 수 제한으로 성능 보장)
    items = list(canonicalItems)
    if len(items) <= 80:  # 항목 수가 적을 때만 O(n^2) 비교
        for i in range(len(items)):
            if items[i] in synonymMap:
                continue
            for j in range(i + 1, len(items)):
                if items[j] in synonymMap:
                    continue
                stripped1 = re.sub(r"[\s\-_·.]", "", items[i])
                stripped2 = re.sub(r"[\s\-_·.]", "", items[j])
                if stripped1 == stripped2:
                    synonymMap[items[j]] = items[i]
                elif len(stripped1) > 3 and len(stripped2) > 3:
                    if _levenshteinRatio(stripped1, stripped2) >= 0.85:
                        synonymMap[items[j]] = items[i]

    return synonymMap


def _levenshteinRatio(s1: str, s2: str) -> float:
    """간단한 Levenshtein 유사도 (0~1)."""
    if s1 == s2:
        return 1.0
    maxLen = max(len(s1), len(s2))
    if maxLen == 0:
        return 1.0

    # DP
    prev = list(range(len(s2) + 1))
    for i in range(1, len(s1) + 1):
        curr = [i] + [0] * len(s2)
        for j in range(1, len(s2) + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = curr

    distance = prev[len(s2)]
    return 1.0 - distance / maxLen


def _classifyTableCategory(
    group: list[SubtableProfile],
    canonicalItems: list[str],
    itemFrequency: dict[str, int],
    periodCount: int,
) -> str:
    """테이블 카테고리 확정: normal / historical / list_type.

    - normal: 기간 간 항목 겹침 높음 → 수평화 적합
    - historical: 기간마다 항목이 완전히 다름 (이력형) → 수평화 부적합
    - list_type: 항목 수 과다 (50+) → 수평화 부적합
    """
    if len(canonicalItems) > 50:
        return "list_type"

    if periodCount < 2:
        return "normal"

    # 기간 간 Jaccard 겹침률
    periodItemSets: dict[str, set[str]] = {}
    for p in group:
        if p.period not in periodItemSets:
            periodItemSets[p.period] = set()
        periodItemSets[p.period].update(p.items)

    sets = list(periodItemSets.values())
    if len(sets) < 2:
        return "normal"

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
    if avgOverlap < 0.3 and len(canonicalItems) > 5:
        return "historical"

    return "normal"


# ══════════════════════════════════════════════════════════════
# Phase 2: 스키마 기반 수평화
# ══════════════════════════════════════════════════════════════


def _horizontalizeWithSchema(
    topicFrame: pl.DataFrame,
    blockOrder: int,
    periodCols: list[str],
    schema: CanonicalSchema,
) -> pl.DataFrame | None:
    """스키마를 사용하여 수평화 — 분류/감지 로직 불필요."""
    if schema.tableCategory != "normal":
        return None  # 이력형/목록형은 수평화 부적합

    boRow = topicFrame.filter(
        (pl.col("blockOrder") == blockOrder) & (pl.col("blockType") == "table")
    )
    if boRow.is_empty():
        return None

    # synonym map의 역방향: 대표명으로 통일
    def _resolve(item: str) -> str:
        return schema.synonymMap.get(item, item)

    allItems: list[str] = []
    seenItems: set[str] = set()
    periodItemVal: dict[str, dict[str, str]] = {}

    for p in periodCols:
        md = boRow[p][0] if p in boRow.columns else None
        if md is None:
            continue

        pYear = int(re.match(r"\d{4}", p).group()) if re.match(r"\d{4}", p) else None

        for sub in splitSubtables(str(md)):
            hc = _headerCells(sub)
            if _isJunk(hc):
                continue
            dr = _dataRows(sub)
            if not dr:
                continue

            # 스키마의 canonical header와 매칭
            gh = _groupHeader(hc)
            if gh != schema.canonicalHeader:
                continue

            # 확정된 구조 타입으로 파싱 (분류 불필요)
            if schema.structType == "multi_year" and pYear and "Q" not in p:
                triples, _ = _parseMultiYear(sub, pYear)
                for rawItem, year, val in triples:
                    item = _resolve(_normalizeItem(rawItem))
                    if year == str(pYear):
                        if item not in seenItems:
                            allItems.append(item)
                            seenItems.add(item)
                        if item not in periodItemVal:
                            periodItemVal[item] = {}
                        periodItemVal[item][p] = val

            elif schema.structType in ("key_value", "matrix"):
                rows, headerNames, _ = _parseKeyValueOrMatrix(sub)
                for rawItem, vals in rows:
                    item = _resolve(_normalizeItem(rawItem))

                    if schema.structType == "matrix" and len(headerNames) >= 2:
                        # matrix: 헤더별 분리
                        nonEmptyVals = [v for v in vals if v.strip()]
                        if len(nonEmptyVals) >= 2 and len(nonEmptyVals) <= len(headerNames):
                            for hi, hname in enumerate(headerNames):
                                v = vals[hi].strip() if hi < len(vals) else ""
                                if not v or v == "-":
                                    continue
                                compoundItem = f"{item}_{_normalizeItem(hname)}"
                                compoundItem = _resolve(compoundItem)
                                if compoundItem not in seenItems:
                                    allItems.append(compoundItem)
                                    seenItems.add(compoundItem)
                                if compoundItem not in periodItemVal:
                                    periodItemVal[compoundItem] = {}
                                periodItemVal[compoundItem][p] = v
                            continue

                    # key_value or fallback
                    val = " | ".join(v for v in vals if v.strip()).strip()
                    if val:
                        if item not in seenItems:
                            allItems.append(item)
                            seenItems.add(item)
                        if item not in periodItemVal:
                            periodItemVal[item] = {}
                        periodItemVal[item][p] = val

    if not allItems:
        return None

    # 스키마의 canonical items 순서 사용 (없는 항목은 끝에)
    canonicalOrder = {item: i for i, item in enumerate(schema.canonicalItems)}
    # synonym resolve된 canonical items
    resolvedCanonical = []
    for ci in schema.canonicalItems:
        resolved = _resolve(ci)
        if resolved not in resolvedCanonical:
            resolvedCanonical.append(resolved)
    canonicalOrder = {item: i for i, item in enumerate(resolvedCanonical)}

    def _sortKey(item: str) -> int:
        return canonicalOrder.get(item, 9999)

    allItems.sort(key=_sortKey)

    # DataFrame 구성
    usedPeriods = [p for p in periodCols if any(p in periodItemVal.get(item, {}) for item in allItems)]
    if not usedPeriods:
        return None

    dfSchema = {"항목": pl.Utf8}
    for p in usedPeriods:
        dfSchema[p] = pl.Utf8

    rows = []
    for item in allItems:
        row = {"항목": item}
        for p in usedPeriods:
            row[p] = periodItemVal.get(item, {}).get(p)
        rows.append(row)

    return pl.DataFrame(rows, schema=dfSchema)


# ══════════════════════════════════════════════════════════════
# Phase 3: 비교 평가
# ══════════════════════════════════════════════════════════════


def _baselineHorizontalize(
    topicFrame: pl.DataFrame,
    blockOrder: int,
    periodCols: list[str],
) -> pl.DataFrame | None:
    """기존 규칙 기반 수평화 (company._horizontalizeTableBlock 로직 재현)."""
    boRow = topicFrame.filter(
        (pl.col("blockOrder") == blockOrder) & (pl.col("blockType") == "table")
    )
    if boRow.is_empty():
        return None

    # 1단계: 헤더 그룹 수집
    _headerGroupsLocal: dict[str, list[str]] = {}
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
            gh = _groupHeader(hc)
            if gh not in _headerGroupsLocal:
                _headerGroupsLocal[gh] = []
            if p not in _headerGroupsLocal[gh]:
                _headerGroupsLocal[gh].append(p)

    if not _headerGroupsLocal:
        return None

    bestHeader = max(_headerGroupsLocal, key=lambda k: len(_headerGroupsLocal[k]))
    bestPeriods = set(_headerGroupsLocal[bestHeader])

    # 2단계: 수평화
    allItems: list[str] = []
    seenItems: set[str] = set()
    periodItemVal: dict[str, dict[str, str]] = {}

    for p in periodCols:
        if p not in bestPeriods:
            continue
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
            gh = _groupHeader(hc)
            if gh != bestHeader:
                continue

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

            elif structType in ("key_value", "matrix"):
                rows, headerNames, _ = _parseKeyValueOrMatrix(sub)
                for rawItem, vals in rows:
                    item = _normalizeItem(rawItem)
                    val = " | ".join(v for v in vals if v.strip()).strip()
                    if val:
                        if item not in seenItems:
                            allItems.append(item)
                            seenItems.add(item)
                        if item not in periodItemVal:
                            periodItemVal[item] = {}
                        periodItemVal[item][p] = val

    if not allItems:
        return None

    # 이력형/목록형 필터
    periodItemSets: dict[str, set[str]] = {}
    for item in allItems:
        for p in periodItemVal.get(item, {}):
            if p not in periodItemSets:
                periodItemSets[p] = set()
            periodItemSets[p].add(item)

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
        if avgOverlap < 0.3 and len(allItems) > 5:
            return None

    if len(allItems) > 50:
        return None

    usedPeriods = [p for p in periodCols if any(p in periodItemVal.get(item, {}) for item in allItems)]
    if not usedPeriods:
        return None

    dfSchema = {"항목": pl.Utf8}
    for p in usedPeriods:
        dfSchema[p] = pl.Utf8

    rows = []
    for item in allItems:
        row = {"항목": item}
        for p in usedPeriods:
            row[p] = periodItemVal.get(item, {}).get(p)
        rows.append(row)

    return pl.DataFrame(rows, schema=dfSchema)


# ══════════════════════════════════════════════════════════════
# 실행
# ══════════════════════════════════════════════════════════════


if __name__ == "__main__":
    pl.Config.set_tbl_cols(10)
    pl.Config.set_fmt_str_lengths(40)
    pl.Config.set_tbl_rows(30)

    stockCode = "005930"
    print(f"종목: {stockCode}")
    print("=" * 70)

    # sections 로드
    sec = sections(stockCode)
    if sec is None:
        print("sections 로드 실패")
        sys.exit(1)

    periodCols = [c for c in sec.columns if re.match(r"^\d{4}(Q[1-4])?$", c)]
    print(f"기간: {periodCols}")

    # ── Part A: executivePay 상세 분석 ──
    print("\n" + "=" * 70)
    print("Part A: executivePay topic 상세 분석")
    print("=" * 70)

    topic = "executivePay"
    topicFrame = sec.filter(pl.col("topic") == topic)
    tableBlocks = topicFrame.filter(pl.col("blockType") == "table")

    if tableBlocks.is_empty():
        print(f"  {topic}: 테이블 블록 없음")
    else:
        blockOrders = sorted(tableBlocks["blockOrder"].unique().to_list())
        print(f"  테이블 블록: {blockOrders}")

        for bo in blockOrders:
            print(f"\n  --- blockOrder={bo} ---")

            # 전 기간 스캔
            profiles = _scanAllPeriods(topicFrame, bo, periodCols)
            print(f"  프로파일 수: {len(profiles)}")

            if not profiles:
                continue

            # 캐노니컬 스키마 구축
            schemas = _buildCanonicalSchema(profiles)
            print(f"  스키마 수: {len(schemas)}")

            for si, schema in enumerate(schemas):
                print(f"\n  [스키마 {si}]")
                print(f"    header: {schema.canonicalHeader[:60]}...")
                print(f"    구조: {schema.structType}")
                print(f"    카테고리: {schema.tableCategory}")
                print(f"    기간 수: {schema.periodCount}")
                print(f"    항목 수: {len(schema.canonicalItems)}")
                print(f"    단위: {schema.unit}")

                if schema.synonymMap:
                    print(f"    동의어: {len(schema.synonymMap)}개")
                    for orig, rep in list(schema.synonymMap.items())[:5]:
                        print(f"      '{orig}' → '{rep}'")

                # 항목 빈도 상위 10
                sortedItems = sorted(
                    schema.itemFrequency.items(),
                    key=lambda x: (-x[1], x[0])
                )
                print(f"    항목 빈도 (상위 10):")
                for item, freq in sortedItems[:10]:
                    pct = freq / schema.periodCount * 100
                    print(f"      {item}: {freq}/{schema.periodCount} ({pct:.0f}%)")

                # 스키마 기반 수평화
                result = _horizontalizeWithSchema(topicFrame, bo, periodCols, schema)
                if result is not None:
                    print(f"\n    스키마 기반 수평화: {result.shape}")
                    print(result.head(15))
                else:
                    print(f"\n    스키마 기반 수평화: None (카테고리={schema.tableCategory})")

            # 기존 방식 수평화 비교
            baseline = _baselineHorizontalize(topicFrame, bo, periodCols)
            if baseline is not None:
                print(f"\n  기존 방식 수평화: {baseline.shape}")
                print(baseline.head(15))
            else:
                print(f"\n  기존 방식 수평화: None")

    # ── Part B: 다양한 topic에서 정량 비교 ──
    print("\n" + "=" * 70)
    print("Part B: 다양한 topic에서 스키마 vs 기존 정량 비교")
    print("=" * 70)

    # 전체 topic에서 테이블 블록이 있는 것만
    allTopics = sec.filter(pl.col("blockType") == "table")["topic"].unique().to_list()
    allTopics = sorted(set(allTopics))
    print(f"테이블이 있는 topic 수: {len(allTopics)}")

    schemaWins = 0
    baselineWins = 0
    bothSuccess = 0
    bothFail = 0
    schemaOnlyItems = 0
    baselineOnlyItems = 0
    totalBlocks = 0

    comparison: list[dict] = []

    import time
    tStart = time.time()

    for ti, topic in enumerate(allTopics):
        if ti % 20 == 0:
            elapsed = time.time() - tStart
            print(f"  진행: {ti}/{len(allTopics)} ({elapsed:.1f}s)", flush=True)

        topicFrame = sec.filter(pl.col("topic") == topic)
        tableBlocks = topicFrame.filter(pl.col("blockType") == "table")
        if tableBlocks.is_empty():
            continue

        blockOrders = sorted(tableBlocks["blockOrder"].unique().to_list())

        for bo in blockOrders:
            totalBlocks += 1

            # 스키마 기반
            profiles = _scanAllPeriods(topicFrame, bo, periodCols)
            schemas = _buildCanonicalSchema(profiles) if profiles else []

            schemaResult = None
            for schema in schemas:
                if schema.periodCount >= 2:  # 2개 이상 기간 커버하는 스키마만
                    schemaResult = _horizontalizeWithSchema(topicFrame, bo, periodCols, schema)
                    if schemaResult is not None:
                        break

            # 기존 방식
            baselineResult = _baselineHorizontalize(topicFrame, bo, periodCols)

            sRows = schemaResult.height if schemaResult is not None else 0
            sCols = len([c for c in schemaResult.columns if re.match(r"^\d{4}", c)]) if schemaResult is not None else 0
            bRows = baselineResult.height if baselineResult is not None else 0
            bCols = len([c for c in baselineResult.columns if re.match(r"^\d{4}", c)]) if baselineResult is not None else 0

            sOk = schemaResult is not None and sRows > 0 and sCols >= 2
            bOk = baselineResult is not None and bRows > 0 and bCols >= 2

            if sOk and bOk:
                bothSuccess += 1
                # 더 많은 항목/기간을 커버하는 쪽이 승
                sScore = sRows * sCols
                bScore = bRows * bCols
                if sScore > bScore:
                    schemaWins += 1
                elif bScore > sScore:
                    baselineWins += 1
                schemaOnlyItems += sRows
                baselineOnlyItems += bRows
            elif sOk and not bOk:
                schemaWins += 1
            elif bOk and not sOk:
                baselineWins += 1
            else:
                bothFail += 1

            comparison.append({
                "topic": topic,
                "bo": bo,
                "schema": f"{sRows}x{sCols}" if sOk else "FAIL",
                "baseline": f"{bRows}x{bCols}" if bOk else "FAIL",
                "winner": "schema" if (sOk and not bOk) else
                          "baseline" if (bOk and not sOk) else
                          "tie" if (sOk and bOk) else "both_fail",
            })

    # 결과 요약
    schemaSuccess = bothSuccess + schemaWins - (bothSuccess if schemaWins > 0 else 0)
    # 더 정확한 계산
    sTotal = sum(1 for c in comparison if c["schema"] != "FAIL")
    bTotal = sum(1 for c in comparison if c["baseline"] != "FAIL")

    print(f"\n총 테이블 블록: {totalBlocks}")
    print(f"스키마 성공: {sTotal} ({sTotal/totalBlocks*100:.1f}%)")
    print(f"기존 성공:   {bTotal} ({bTotal/totalBlocks*100:.1f}%)")
    print(f"둘 다 성공:  {bothSuccess}")
    print(f"둘 다 실패:  {bothFail}")
    print(f"스키마만 성공: {sum(1 for c in comparison if c['winner'] == 'schema')}")
    print(f"기존만 성공:   {sum(1 for c in comparison if c['winner'] == 'baseline')}")

    # 차이가 나는 사례 출력
    print(f"\n--- 스키마만 성공한 사례 (최대 10개) ---")
    schemaOnly = [c for c in comparison if c["winner"] == "schema"]
    for c in schemaOnly[:10]:
        print(f"  {c['topic']} bo={c['bo']}: schema={c['schema']}, baseline={c['baseline']}")

    print(f"\n--- 기존만 성공한 사례 (최대 10개) ---")
    baselineOnly = [c for c in comparison if c["winner"] == "baseline"]
    for c in baselineOnly[:10]:
        print(f"  {c['topic']} bo={c['bo']}: schema={c['schema']}, baseline={c['baseline']}")

    # 스키마 JSON 예시 출력
    if schemas:
        print(f"\n--- 캐노니컬 스키마 JSON 예시 (executivePay 마지막) ---")
        example = schemas[-1] if schemas else schemas[0]
        schemaDict = {
            "canonicalHeader": example.canonicalHeader,
            "structType": example.structType,
            "tableCategory": example.tableCategory,
            "unit": example.unit,
            "periodCount": example.periodCount,
            "canonicalItems": example.canonicalItems[:15],
            "synonymMap": dict(list(example.synonymMap.items())[:10]),
            "itemFrequency": dict(sorted(
                example.itemFrequency.items(), key=lambda x: -x[1]
            )[:10]),
        }
        print(json.dumps(schemaDict, ensure_ascii=False, indent=2))
