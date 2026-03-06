"""각 기업별 관계기업 섹션의 실제 테이블 헤더 패턴 디버깅.

파싱이 안 되는 이유를 파악하기 위해
각 기업/연도별 첫 10행을 출력한다.
"""

import re
from pathlib import Path

import polars as pl

DATA_DIR = Path("data/docsData")
OUT = Path("experiments/003_subsidiaries/output")
OUT.mkdir(exist_ok=True)


def extractNotes(df: pl.DataFrame, year: str) -> list[str]:
    filtered = df.filter(
        (pl.col("year") == year)
        & pl.col("report_type").str.contains("사업보고서")
        & ~pl.col("report_type").str.contains("기재정정|첨부")
        & pl.col("section_title").str.contains("연결재무제표")
        & pl.col("section_title").str.contains("주석")
    )
    if filtered.height == 0:
        filtered = df.filter(
            (pl.col("year") == year)
            & pl.col("section_title").str.contains("연결재무제표")
            & pl.col("section_title").str.contains("주석")
        )
    return filtered["section_content"].to_list()


def findSection(contents: list[str], keyword: str) -> str | None:
    for content in contents:
        lines = content.split("\n")
        startIdx = None
        endIdx = None
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|"):
                continue
            m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
            if m:
                title = m.group(2).strip()
                if keyword in title:
                    startIdx = i
                elif startIdx is not None and endIdx is None:
                    endIdx = i
                    break
        if startIdx is not None:
            if endIdx is None:
                endIdx = len(lines)
            return "\n".join(lines[startIdx:endIdx])
    return None


def parseTableRows(text: str) -> list[list[str]]:
    rows = []
    for line in text.split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        # 후행 빈 셀 제거 (XBRL 패딩)
        while cells and not cells[-1]:
            cells.pop()
        if not cells:
            continue
        if all(re.match(r"^-+$", c) for c in cells if c):
            continue
        if not any(c.strip() for c in cells):
            continue
        rows.append(cells)
    return rows


COMPANIES = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("005380", "현대차"),
    ("066570", "LG전자"),
    ("035420", "네이버"),
    ("035720", "카카오"),
    ("005490", "POSCO홀딩스"),
    ("006400", "삼성SDI"),
    ("373220", "LG에너지솔루션"),
]


def main():
    out = []

    def p(s=""):
        out.append(s)

    p("=" * 80)
    p("관계기업 섹션 테이블 헤더 디버깅")
    p("=" * 80)

    for code, name in COMPANIES:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            continue

        df = pl.read_parquet(str(path))
        years = sorted(df["year"].unique().to_list(), reverse=True)

        p(f"\n{'=' * 60}")
        p(f"  {name} ({code})")
        p(f"{'=' * 60}")

        for year in years[:3]:
            contents = extractNotes(df, year)
            if not contents:
                p(f"\n  {year}: 주석 없음")
                continue

            section = findSection(contents, "관계기업")
            if section is None:
                section = findSection(contents, "지분법")
            if section is None:
                p(f"\n  {year}: 관계기업 섹션 없음")
                continue

            rows = parseTableRows(section)
            p(f"\n  {year}: 테이블행 {len(rows)}개")

            # 첫 20행의 셀 수와 내용 출력
            p(f"  --- 처음 20행 ---")
            for i, row in enumerate(rows[:20]):
                cellPreview = " | ".join(row[:8])
                if len(row) > 8:
                    cellPreview += f" | ... (+{len(row) - 8})"
                p(f"    [{i:>3}] ({len(row)}셀) {cellPreview}")

            # 헤더 패턴 찾기: "기업명" or "기 업 명" 포함 행
            p(f"  --- 헤더 후보 (기업명/지분율/당기/기초 키워드) ---")
            for i, row in enumerate(rows):
                cellStr = " ".join(row)
                if any(kw in cellStr for kw in ["기업명", "기 업 명", "지분율", "당기말", "당분기말", "기초"]):
                    p(f"    [{i:>3}] ({len(row)}셀) {' | '.join(row[:10])}")

    outPath = OUT / "debug_headers.txt"
    outPath.write_text("\n".join(out), encoding="utf-8")
    print(f"결과 저장: {outPath}")
    print(f"총 {len(out)}줄")

    # 핵심만 콘솔
    for line in out:
        if "===" in line or "---" in line or "헤더 후보" in line or "[" in line:
            print(line)


if __name__ == "__main__":
    main()
