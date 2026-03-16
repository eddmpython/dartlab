"""실험 ID: 063-009
실험명: 테이블 구조 타입 자동 분류

목적:
- 서브테이블의 구조(컬럼 패턴)로 타입 자동 분류
- 내용(키워드)이 아니라 구조로 분류: 당기/전기 패턴, 단일값, 월별 등
- 단위 마커 추출
- 전 종목에서 구조 타입 분포 확인

가설:
1. 헤더 컬럼 패턴으로 3~5개 구조 타입이 전체의 90%+ 커버
2. 단위 마커는 대부분 "(단위: xxx)" 패턴으로 추출 가능

방법:
1. 서브테이블 헤더 분석 — 컬럼 패턴 추출
2. 구조 타입 자동 분류:
   - 당기/전기/전전기 패턴 → multi_year
   - 단일 키-값 (2컬럼) → key_value
   - 월별/분기별 → time_series
   - 기타 → matrix
3. 단위 추출 — "(단위: xxx)" 또는 별도 행
4. 전 종목 분포 확인

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-16
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl
from dartlab.engines.dart.docs.sections.pipeline import sections
from dartlab.core.dataLoader import _dataDir


def splitSubtables(md: str) -> list[list[str]]:
    tables, current = [], []
    for line in md.strip().split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            if current:
                tables.append(current)
                current = []
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if isSep and current:
            if len(current) >= 2:
                prev = current[:-1]
                if prev:
                    tables.append(prev)
                current = [current[-1], s]
            else:
                current.append(s)
        else:
            current.append(s)
    if current:
        tables.append(current)
    return tables


def getHeaderCells(lines: list[str]) -> list[str]:
    """서브테이블의 헤더 셀 목록."""
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if not isSep:
            return [c for c in cells if c.strip()]
    return []


def getDataRows(lines: list[str]) -> list[list[str]]:
    """구분선 이후 데이터 행들."""
    rows = []
    headerDone = False
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if isSep:
            headerDone = True
            continue
        if headerDone:
            rows.append([c for c in cells if c is not None])
    return rows


def extractUnit(lines: list[str]) -> str | None:
    """서브테이블에서 단위 추출."""
    full = "\n".join(lines)
    # (단위: xxx) 패턴
    m = re.search(r"\(\s*단위\s*:\s*([^)]+)\)", full)
    if m:
        return m.group(1).strip()
    # (단위 : xxx) 변형
    m = re.search(r"단위\s*:\s*([\w%,]+)", full)
    if m:
        return m.group(1).strip()
    return None


# ── 구조 패턴 ──
_MULTI_YEAR_KEYWORDS = {"당기", "전기", "전전기", "당반기", "전반기"}
_MONTH_PATTERN = re.compile(r"\d{1,2}월")
_QUARTER_PATTERN = re.compile(r"[1-4]분기|Q[1-4]")
_YEAR_PATTERN = re.compile(r"(20\d{2}|제\d+기)")


def classifyStructure(headerCells: list[str], dataRows: list[list[str]], lines: list[str]) -> str:
    """테이블 구조 타입 분류.

    Returns:
        - "multi_year": 당기/전기/전전기 구조 (3년 체인)
        - "key_value": 2컬럼 키-값
        - "monthly": 월별 데이터
        - "quarterly": 분기별 데이터
        - "yearly": 연도별 데이터
        - "matrix": 다차원 매트릭스
        - "label_only": 1컬럼 라벨만
        - "note": 주석/비고
    """
    headerJoined = " ".join(headerCells).strip()

    # 빈/주석 필터
    if not headerCells:
        return "note"
    if len(headerCells) == 1:
        h = headerCells[0]
        if h.startswith("※") or h.startswith("☞") or h.startswith("[△"):
            return "note"
        if len(h) < 5:
            return "note"
        return "label_only"

    # 당기/전기/전전기 패턴
    if any(kw in headerJoined for kw in _MULTI_YEAR_KEYWORDS):
        return "multi_year"

    # 월별
    monthMatches = _MONTH_PATTERN.findall(headerJoined)
    if len(monthMatches) >= 3:
        return "monthly"

    # 분기별
    quarterMatches = _QUARTER_PATTERN.findall(headerJoined)
    if len(quarterMatches) >= 2:
        return "quarterly"

    # 연도별 (헤더에 연도 2개+)
    yearMatches = _YEAR_PATTERN.findall(headerJoined)
    if len(yearMatches) >= 2:
        return "yearly"

    # 데이터 행에서도 확인 — 첫 데이터 행의 첫 셀에 연도/기수가 있으면 yearly
    if dataRows:
        firstCell = dataRows[0][0] if dataRows[0] else ""
        if _YEAR_PATTERN.search(firstCell):
            # 데이터 첫 행이 "제56기" 같은 것이면 multi_year일 가능성
            if any(kw in " ".join(dataRows[0]) for kw in _MULTI_YEAR_KEYWORDS):
                return "multi_year"

    # 2컬럼 키-값
    if len(headerCells) == 2:
        return "key_value"

    # 나머지
    return "matrix"


if __name__ == "__main__":
    # 삼성전자 단일 종목으로 먼저 상세 확인
    print("=== 삼성전자 서브테이블 구조 분류 ===\n")

    sec = sections("005930")
    tables = sec.filter(pl.col("blockType") == "table")
    periods = [c for c in tables.columns if c not in {"chapter", "topic", "blockType"}]

    structCounts = Counter()
    unitCounts = Counter()
    topicStructs: dict[str, Counter] = {}

    for row in tables.iter_rows(named=True):
        topic = row["topic"]
        if topic in {"consolidatedNotes", "financialNotes", "fsSummary"}:
            continue

        content = row.get(periods[-1])
        if not content:
            continue

        if topic not in topicStructs:
            topicStructs[topic] = Counter()

        subs = splitSubtables(str(content))
        for sub in subs:
            headerCells = getHeaderCells(sub)
            dataRows = getDataRows(sub)
            structType = classifyStructure(headerCells, dataRows, sub)
            unit = extractUnit(sub)

            structCounts[structType] += 1
            topicStructs[topic][structType] += 1
            if unit:
                unitCounts[unit] += 1

    print("구조 타입 분포:")
    total = sum(structCounts.values())
    for st, count in structCounts.most_common():
        print(f"  {st:15s}: {count:4d} ({count/total*100:5.1f}%)")

    print(f"\n단위 분포 ({len(unitCounts)}종):")
    for unit, count in unitCounts.most_common(15):
        print(f"  [{count:3d}] {unit}")

    print("\n주요 topic별 구조 타입:")
    for topic in ["companyOverview", "dividend", "employee", "majorHolder",
                   "audit", "shareCapital", "businessOverview", "salesOrder"]:
        if topic in topicStructs:
            dist = topicStructs[topic]
            parts = [f"{st}:{c}" for st, c in dist.most_common(3)]
            print(f"  {topic:25s}: {', '.join(parts)}")

    # 전 종목
    print("\n\n=== 전 종목 구조 타입 분포 ===\n")
    docsDir = _dataDir("docs")
    codes = sorted(p.stem for p in docsDir.glob("*.parquet"))

    allStructCounts = Counter()
    allUnitCounts = Counter()
    errors = 0

    for i, code in enumerate(codes):
        try:
            s = sections(code)
            if s is None or "blockType" not in s.columns:
                continue
            t = s.filter(pl.col("blockType") == "table")
            if t.is_empty():
                continue
            ps = [c for c in t.columns if c not in {"chapter", "topic", "blockType"}]
            if not ps:
                continue

            for r in t.iter_rows(named=True):
                topic = r["topic"]
                if topic in {"consolidatedNotes", "financialNotes", "fsSummary"}:
                    continue
                content = r.get(ps[-1])
                if not content:
                    continue
                for sub in splitSubtables(str(content)):
                    hc = getHeaderCells(sub)
                    dr = getDataRows(sub)
                    st = classifyStructure(hc, dr, sub)
                    unit = extractUnit(sub)
                    allStructCounts[st] += 1
                    if unit:
                        allUnitCounts[unit] += 1
        except (KeyError, ValueError, TypeError):
            errors += 1

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(codes)} 처리됨")

    print(f"\n처리: {len(codes)}종목 (에러: {errors})")
    total = sum(allStructCounts.values())
    print(f"전체 서브테이블: {total}")
    print("\n구조 타입 분포:")
    for st, count in allStructCounts.most_common():
        print(f"  {st:15s}: {count:5d} ({count/total*100:5.1f}%)")

    print(f"\n단위 분포 (상위 15):")
    for unit, count in allUnitCounts.most_common(15):
        print(f"  [{count:4d}] {unit}")
