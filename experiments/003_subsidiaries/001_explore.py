"""관계기업/종속기업 주석 구조 탐색.

주석에서 관계기업, 종속기업, 투자 관련 섹션을 찾고
어떤 테이블 구조가 있는지 파악한다.
"""

import re
from pathlib import Path

import polars as pl

DATA_DIR = Path("data/docsData")
OUT = Path("experiments/003_subsidiaries/output")
OUT.mkdir(exist_ok=True)


def extractNotes(df: pl.DataFrame, year: str) -> list[str]:
    """해당 연도 연결재무제표 주석 content 목록."""
    notes = df.filter(
        (pl.col("year") == year)
        & pl.col("section_title").str.contains("연결재무제표")
        & pl.col("section_title").str.contains("주석")
    )
    return notes["section_content"].to_list()


def findNumberedSections(content: str) -> list[tuple[int, str, int, int]]:
    """번호 매긴 섹션 목록 반환: [(번호, 제목, 시작줄, 끝줄), ...]"""
    lines = content.split("\n")
    sections = []

    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("|"):
            continue
        m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
        if m:
            num = int(m.group(1))
            title = m.group(2).strip()
            sections.append((num, title, i))

    result = []
    for j, (num, title, start) in enumerate(sections):
        end = sections[j + 1][2] if j + 1 < len(sections) else len(lines)
        result.append((num, title, start, end))
    return result


def main():
    path = DATA_DIR / "005930.parquet"
    df = pl.read_parquet(str(path))
    years = sorted(df["year"].unique().to_list(), reverse=True)

    out = []

    def p(s=""):
        out.append(s)

    p("=" * 80)
    p("삼성전자 주석 — 관계기업/종속기업 관련 섹션 탐색")
    p("=" * 80)

    # 관련 키워드
    KEYWORDS = ["종속", "관계기업", "공동기업", "지분법", "투자", "연결대상"]

    for year in years[:5]:
        contents = extractNotes(df, year)
        if not contents:
            continue

        p(f"\n{'=' * 60}")
        p(f"  {year}")
        p(f"{'=' * 60}")

        for content in contents:
            sections = findNumberedSections(content)
            lines = content.split("\n")

            for num, title, start, end in sections:
                # 키워드 매칭
                if any(kw in title for kw in KEYWORDS):
                    sectionText = "\n".join(lines[start:end])
                    lineCount = end - start

                    # 테이블 행 개수
                    tableLines = [l for l in lines[start:end] if l.strip().startswith("|")]
                    tableCount = len(tableLines)

                    p(f"\n  {num}. {title}")
                    p(f"    줄수: {lineCount}, 테이블행: {tableCount}")

                    # 첫 100줄만 출력
                    preview = sectionText[:3000]
                    for line in preview.split("\n")[:80]:
                        p(f"    {line}")
                    if lineCount > 80:
                        p(f"    ... ({lineCount - 80}줄 생략)")

    # 모든 주석 섹션 제목 목록 (패턴 파악용)
    p(f"\n\n{'=' * 80}")
    p("전체 주석 섹션 제목 목록 (최근 3년)")
    p("=" * 80)

    for year in years[:3]:
        contents = extractNotes(df, year)
        if not contents:
            continue

        p(f"\n  {year}:")
        for content in contents:
            sections = findNumberedSections(content)
            for num, title, start, end in sections:
                marker = " ★" if any(kw in title for kw in KEYWORDS) else ""
                p(f"    {num:>2}. {title}{marker}")

    outPath = OUT / "explore_samsung.txt"
    outPath.write_text("\n".join(out), encoding="utf-8")
    print(f"결과 저장: {outPath}")
    print(f"총 {len(out)}줄")


if __name__ == "__main__":
    main()
