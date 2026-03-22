"""실험 ID: 063-006
실험명: 헤더 내용 기반 서브테이블 매칭

목적:
- 순번 기반 매칭이 불안정하므로 헤더 내용으로 매칭
- 같은 topic 내에서 기간별로 같은 헤더의 서브테이블을 찾아 수평화 가능성 확인
- 헤더 정규화 → 매칭률 측정

가설:
1. 헤더 정규화 후 같은 테이블 유형끼리 매칭률 90%+ 가능
2. 주요 topic(companyOverview, employee, dividend 등)에서 안정적 매칭

방법:
1. 서브테이블 분리
2. 헤더 정규화 (연도/분기/단위 제거)
3. 같은 topic 내에서 기간별 정규화 헤더 매칭
4. 매칭된 서브테이블끼리 항목(첫 컬럼) 수평화 시도

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-16
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl
from dartlab.engines.company.dart.docs.sections.pipeline import sections


def splitSubtables(md: str) -> list[list[str]]:
    """구분선 기준 서브테이블 분리."""
    tables: list[list[str]] = []
    current: list[str] = []

    for line in md.strip().split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            if current:
                tables.append(current)
                current = []
            continue

        cells = [c.strip() for c in stripped.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())

        if isSep and current:
            if len(current) >= 2:
                prevTable = current[:-1]
                if prevTable:
                    tables.append(prevTable)
                current = [current[-1], stripped]
            else:
                current.append(stripped)
        else:
            current.append(stripped)

    if current:
        tables.append(current)

    return tables


def subtableHeader(lines: list[str]) -> str:
    """첫 번째 비구분선 줄."""
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if not isSep:
            return " | ".join(c.strip() for c in cells if c.strip())
    return ""


def normalizeHeader(header: str) -> str:
    """헤더 정규화 — 연도/분기/단위/공백 제거."""
    h = re.sub(r"\d{4}(Q\d)?", "", header)
    h = re.sub(r"제\s*\d+\s*기", "", h)
    h = re.sub(r"\(\s*단위\s*:\s*[^)]+\)", "", h)
    h = re.sub(r"\(\s*기준일\s*:?[^)]*\)", "", h)
    h = re.sub(r"기준일\s*:?[^|]*", "", h)
    h = re.sub(r"\d+\.\d+\.\d+", "", h)
    h = re.sub(r"\s+", " ", h).strip()
    h = re.sub(r"^[\s|]+$", "", h)
    return h


def parseSubtableRows(lines: list[str]) -> list[tuple[str, str]]:
    """서브테이블 → (항목, 나머지) 리스트. 헤더/구분선 제외."""
    rows: list[tuple[str, str]] = []
    headerDone = False
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if isSep:
            headerDone = True
            continue
        if not headerDone:
            continue
        label = cells[0] if cells else ""
        value = " | ".join(cells[1:]) if len(cells) > 1 else ""
        if label.strip():
            rows.append((label.strip(), value.strip()))
    return rows


if __name__ == "__main__":
    sec = sections("005930")
    if sec is None:
        print("sections None")
        sys.exit(1)

    tables = sec.filter(pl.col("blockType") == "table")
    periods = [c for c in tables.columns if c not in {"chapter", "topic", "blockType"}]

    # notes 제외 (서브테이블 700+개로 별도 처리 필요)
    skipTopics = {"consolidatedNotes", "financialNotes", "fsSummary"}

    print("=== 헤더 기반 서브테이블 매칭 ===\n")

    for row in tables.iter_rows(named=True):
        topic = row["topic"]
        if topic in skipTopics:
            continue

        # 기간별 서브테이블 수집
        periodSubs: dict[str, list[tuple[str, list[str]]]] = {}  # period → [(normHeader, lines)]
        for p in periods:
            content = row.get(p)
            if content is None:
                continue
            subs = splitSubtables(str(content))
            periodSubs[p] = [
                (normalizeHeader(subtableHeader(sub)), sub)
                for sub in subs
            ]

        if not periodSubs:
            continue

        # 정규화 헤더별로 기간 그룹핑
        headerPeriods: dict[str, list[str]] = defaultdict(list)
        for p, subs in periodSubs.items():
            for normH, _ in subs:
                if normH:
                    headerPeriods[normH].append(p)

        # 결과 출력
        totalPeriods = len(periodSubs)
        stableHeaders = [(h, ps) for h, ps in headerPeriods.items() if len(ps) >= totalPeriods * 0.5]

        if not stableHeaders:
            continue

        print(f"▶ {topic} ({totalPeriods}기간)")
        for h, ps in sorted(stableHeaders, key=lambda x: -len(x[1])):
            pct = len(ps) / totalPeriods * 100
            print(f"  [{len(ps):2d}/{totalPeriods} {pct:5.1f}%] {h[:70]}")

        # 가장 안정적인 헤더의 서브테이블로 수평화 시도
        bestHeader = max(stableHeaders, key=lambda x: len(x[1]))
        bh, bps = bestHeader
        print(f"  → 수평화 시도: '{bh[:50]}' ({len(bps)}기간)")

        # 각 기간에서 해당 헤더의 서브테이블 항목 추출
        periodItems: dict[str, dict[str, str]] = {}
        allItems: list[str] = []
        seenItems: set[str] = set()

        for p in bps:
            for normH, lines in periodSubs[p]:
                if normH == bh:
                    items = parseSubtableRows(lines)
                    itemMap: dict[str, str] = {}
                    for label, value in items:
                        if label not in seenItems:
                            allItems.append(label)
                            seenItems.add(label)
                        itemMap[label] = value
                    periodItems[p] = itemMap
                    break

        if allItems and len(periodItems) >= 2:
            # 최근 3기간만 미리보기
            previewPeriods = sorted(periodItems.keys())[-3:]
            print(f"  항목 {len(allItems)}개, 미리보기:")
            for item in allItems[:5]:
                vals = [periodItems.get(p, {}).get(item, "-")[:20] for p in previewPeriods]
                print(f"    {item:20s} | {'  |  '.join(vals)}")
            if len(allItems) > 5:
                print(f"    ... +{len(allItems) - 5}개")
        print()
