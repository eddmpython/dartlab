"""실험 ID: 063-005
실험명: 서브테이블 분리 + 헤더 기반 타입 분류

목적:
- 하나의 sections table 셀에 여러 서브테이블이 연결되어 있음
- 구분선(---) 기준으로 서브테이블을 분리
- 분리된 서브테이블의 헤더 패턴으로 타입 분류 가능성 확인

가설:
1. 대부분의 table 셀에서 서브테이블 분리가 가능하다 (구분선 기준)
2. 분리된 서브테이블 수는 topic별로 일관된 패턴이 있다
3. 같은 topic의 같은 위치(순번) 서브테이블은 같은 구조를 갖는다

방법:
1. 삼성전자 전 topic의 table 셀에서 서브테이블 분리
2. 여러 기간에 걸쳐 서브테이블 수/구조 비교
3. 같은 topic의 같은 순번 서브테이블끼리 헤더 일치율 확인

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-16
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.engines.company.dart.docs.sections.pipeline import sections


def splitSubtables(md: str) -> list[list[str]]:
    """markdown 텍스트에서 구분선(---) 기준으로 서브테이블 분리.

    Returns: 서브테이블별 줄 리스트. 각 서브테이블은 [헤더, 구분선, 데이터...].
    """
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
            # 구분선 직전이 헤더 → 새 서브테이블 시작
            # 직전 줄이 현재 테이블의 헤더인지, 새 테이블의 헤더인지 판단
            # 규칙: current의 마지막 줄이 헤더, 이 줄이 구분선 → 새 서브테이블 시작
            if len(current) >= 2:
                # 이전 서브테이블은 마지막 줄(헤더) 제외하고 저장
                prevTable = current[:-1]
                if prevTable:
                    tables.append(prevTable)
                # 새 서브테이블: 헤더 + 구분선
                current = [current[-1], stripped]
            else:
                # current에 1줄만 있으면 그게 헤더
                current.append(stripped)
        else:
            current.append(stripped)

    if current:
        tables.append(current)

    return tables


def subtableHeader(lines: list[str]) -> str:
    """서브테이블의 헤더(첫 번째 비구분선 줄) 추출."""
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if not isSep:
            return " | ".join(c.strip() for c in cells if c.strip())
    return ""


if __name__ == "__main__":
    sec = sections("005930")
    if sec is None:
        print("sections None")
        sys.exit(1)

    tables = sec.filter(pl.col("blockType") == "table")
    periods = [c for c in tables.columns if c not in {"chapter", "topic", "blockType"}]

    print(f"table 행: {tables.height}개")
    print(f"기간: {len(periods)}개")
    print()

    # 각 topic별로 최신 기간의 서브테이블 분리
    print("=== topic별 서브테이블 수 ===")
    topicSubtableCounts: dict[str, list[int]] = {}

    for row in tables.iter_rows(named=True):
        topic = row["topic"]
        counts = []
        for p in periods[-5:]:  # 최근 5기간만
            content = row.get(p)
            if content is None:
                continue
            subs = splitSubtables(str(content))
            counts.append(len(subs))

        if counts:
            topicSubtableCounts[topic] = counts

    for topic, counts in sorted(topicSubtableCounts.items()):
        avg = sum(counts) / len(counts)
        print(f"  {topic}: {counts} (평균 {avg:.1f}개)")

    # 상세 — companyOverview의 서브테이블 헤더
    print("\n=== companyOverview 서브테이블 상세 ===")
    coRow = tables.filter(pl.col("topic") == "companyOverview")
    if not coRow.is_empty():
        for p in [periods[-1], periods[-3]]:
            content = coRow[p][0]
            if content is None:
                continue
            subs = splitSubtables(str(content))
            print(f"\n{p}: {len(subs)}개 서브테이블")
            for i, sub in enumerate(subs):
                header = subtableHeader(sub)
                print(f"  [{i}] ({len(sub)}줄) {header[:80]}")

    # 같은 순번 서브테이블끼리 헤더 일치율
    print("\n=== 기간 간 서브테이블 헤더 일치 ===")
    coRow = tables.filter(pl.col("topic") == "companyOverview")
    if not coRow.is_empty():
        periodHeaders: dict[str, list[str]] = {}
        for p in periods:
            content = coRow[p][0]
            if content is None:
                continue
            subs = splitSubtables(str(content))
            periodHeaders[p] = [subtableHeader(sub) for sub in subs]

        # 순번별 헤더 통계
        maxSubs = max(len(v) for v in periodHeaders.values())
        for idx in range(min(maxSubs, 10)):
            headers = [periodHeaders[p][idx] for p in periodHeaders if idx < len(periodHeaders[p])]
            unique = set(headers)
            print(f"  순번 {idx}: {len(headers)}기간 중 고유 헤더 {len(unique)}종")
            if len(unique) <= 3:
                for h in unique:
                    print(f"    - {h[:60]}")
