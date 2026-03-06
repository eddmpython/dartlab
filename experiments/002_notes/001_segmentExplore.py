"""부문별 보고 주석 구조 탐색.

연결재무제표 주석에서 "부문별 보고" 섹션을 추출하고,
삼성전자의 연도별 테이블 구조를 파악한다.
"""

import re
import sys
from pathlib import Path

import polars as pl

DATA_DIR = Path("data/docsData")


# ── 1. 주석에서 "부문별 보고" 영역 추출 ─────────────────────────


def extractNotes(df: pl.DataFrame, year: str) -> list[str]:
    """해당 연도 연결재무제표 주석 content 목록 반환."""
    notes = df.filter(
        (pl.col("year") == year)
        & pl.col("section_title").str.contains("연결재무제표")
        & pl.col("section_title").str.contains("주석")
    )
    return notes["section_content"].to_list()


def findSegmentSection(contents: list[str]) -> str | None:
    """주석 content들에서 '부문별 보고' 영역 텍스트 추출.

    번호가 매겨진 주석 항목(예: "29. 부문별 보고")을 찾아서
    다음 번호 항목까지의 텍스트를 반환한다.
    """
    for content in contents:
        lines = content.split("\n")
        startIdx = None
        endIdx = None

        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|"):
                continue

            # "29. 부문별 보고" 같은 패턴
            m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
            if m:
                title = m.group(2).strip()
                if "부문" in title and "보고" in title:
                    startIdx = i
                elif startIdx is not None and endIdx is None:
                    # 다음 번호 항목 = 부문별 보고 끝
                    endIdx = i
                    break

        if startIdx is not None:
            if endIdx is None:
                endIdx = len(lines)
            return "\n".join(lines[startIdx:endIdx])

    return None


# ── 2. 삼성전자 연도별 부문별 보고 구조 확인 ──────────────────────

def main():
    path = DATA_DIR / "005930.parquet"
    df = pl.read_parquet(str(path))

    years = sorted(df["year"].unique().to_list(), reverse=True)

    print("=" * 70)
    print("삼성전자 부문별 보고 주석 탐색")
    print("=" * 70)

    for year in years[:10]:  # 최근 10년
        contents = extractNotes(df, year)
        if not contents:
            print(f"\n{year}: 주석 없음")
            continue

        segment = findSegmentSection(contents)
        if segment is None:
            print(f"\n{year}: 부문별 보고 없음")
            continue

        lines = segment.split("\n")
        print(f"\n{'=' * 50}")
        print(f"{year}: 부문별 보고 ({len(lines)}줄)")
        print(f"{'=' * 50}")

        # 전체 내용 출력 (테이블 구조 파악용)
        for line in lines[:80]:
            print(line[:130])
        if len(lines) > 80:
            print(f"... (총 {len(lines)}줄)")

        # 테이블 행 분석
        tableRows = [l for l in lines if l.strip().startswith("|")]
        print(f"\n  테이블 행 수: {len(tableRows)}")
        if tableRows:
            # 첫 테이블의 컬럼 수
            cells = [c.strip() for c in tableRows[0].split("|") if c.strip()]
            print(f"  첫 행 셀 수: {len(cells)}")
            print(f"  첫 행: {tableRows[0][:120]}")

    print("\n\n")

    # ── 3. 최신 연도 상세 파싱 시도 ─────────────────────────────

    year = years[0]
    contents = extractNotes(df, year)
    segment = findSegmentSection(contents)
    if segment is None:
        print("최신 연도 부문별 보고 없음")
        return

    print("=" * 70)
    print(f"상세 분석: {year}")
    print("=" * 70)

    lines = segment.split("\n")

    # 테이블 단위로 분리 (빈 줄 또는 비테이블 줄이 경계)
    tables: list[list[str]] = []
    currentTable: list[str] = []

    for line in lines:
        s = line.strip()
        if s.startswith("|") and "|" in s[1:]:
            currentTable.append(s)
        else:
            if currentTable:
                tables.append(currentTable)
                currentTable = []
    if currentTable:
        tables.append(currentTable)

    print(f"\n테이블 수: {len(tables)}")
    for idx, table in enumerate(tables):
        print(f"\n--- 테이블 {idx + 1} ({len(table)}행) ---")
        # 헤더 (첫 행)
        cells = [c.strip() for c in table[0].split("|") if c.strip()]
        print(f"  컬럼: {cells}")

        # 데이터 행 (처음 5개)
        for row in table[1:6]:
            rowCells = [c.strip() for c in row.split("|") if c.strip()]
            print(f"  {rowCells}")
        if len(table) > 6:
            print(f"  ... ({len(table) - 1}개 데이터행)")


if __name__ == "__main__":
    main()
