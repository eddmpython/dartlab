"""네이버 2025 변동내역 디버깅."""
import re
from pathlib import Path
import polars as pl

DATA_DIR = Path("data/docsData")

def extractNotes(df, year):
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

def findSection(contents, keyword):
    for content in contents:
        lines = content.split("\n")
        startIdx = endIdx = None
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|"): continue
            m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
            if m:
                title = m.group(2).strip()
                if keyword in title:
                    startIdx = i
                elif startIdx is not None and endIdx is None:
                    endIdx = i; break
        if startIdx is not None:
            return "\n".join(lines[startIdx:(endIdx or len(lines))])
    return None

def parseTableRows(text):
    rows = []
    for line in text.split("\n"):
        s = line.strip()
        if not s.startswith("|"): continue
        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "": cells = cells[1:]
        if cells and cells[-1] == "": cells = cells[:-1]
        while cells and not cells[-1]: cells.pop()
        if not cells: continue
        if all(re.match(r"^-+$", c) for c in cells if c): continue
        if not any(c.strip() for c in cells): continue
        rows.append(cells)
    return rows

df = pl.read_parquet(str(DATA_DIR / "035420.parquet"))
contents = extractNotes(df, "2025")
section = findSection(contents, "관계기업") or findSection(contents, "공동기업")
rows = parseTableRows(section)

print(f"전체 행수: {len(rows)}")
print()

# Row 148~160 범위 출력 (변동내역 헤더 근처)
for i in range(max(0, 148), min(len(rows), 165)):
    cells = rows[i]
    print(f"[{i:>3}] ({len(cells)}셀) {' | '.join(cells[:12])}")
    if len(cells) > 12:
        print(f"      ... (+{len(cells)-12})")
