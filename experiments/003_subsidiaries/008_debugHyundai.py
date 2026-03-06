"""현대차 2025 변동내역 디버깅."""
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

MOVEMENT_COL_MAP = {
    "기초": "opening", "기 초": "opening",
    "기말": "closing", "기 말": "closing",
    "취득": "acquisition", "취 득": "acquisition",
    "처분": "disposal", "처 분": "disposal",
    "취득(처분)": "acqDisp",
    "지분법손익": "equityIncome", "지분법이익(손실)": "equityIncome",
    "배당": "dividend", "배당금": "dividend", "배 당": "dividend",
    "손상": "impairment", "손상차손": "impairment",
    "기타": "other", "기타증감액": "other", "기타변동": "other",
}

MOVEMENT_KEYWORDS = ["기초", "기 초"]

df = pl.read_parquet(str(DATA_DIR / "005380.parquet"))
contents = extractNotes(df, "2025")
section = findSection(contents, "관계기업") or findSection(contents, "공동기업")
rows = parseTableRows(section)

print(f"전체 행수: {len(rows)}")
print()

# 변동내역 헤더 후보 찾기
for i, cells in enumerate(rows):
    cellStr = " ".join(cells)
    hasOpening = any(kw in cellStr for kw in MOVEMENT_KEYWORDS)
    if hasOpening and len(cells) >= 3:
        movKws = sum(1 for kw in MOVEMENT_COL_MAP if kw in cellStr)
        if movKws >= 2:
            print(f"[{i:>3}] MOVEMENT HEADER ({len(cells)}셀, {movKws}kw)")
            print(f"      {' | '.join(cells[:10])}")
            # 매핑 결과
            for j, h in enumerate(cells):
                norm = re.sub(r"[\s·ㆍ\u3000]", "", re.sub(r"\(\*?\d*\)", "", h)).strip()
                matched = None
                for kw, field in MOVEMENT_COL_MAP.items():
                    kwNorm = re.sub(r"[\s·ㆍ\u3000]", "", kw)
                    if kwNorm in norm or norm in kwNorm:
                        matched = field; break
                print(f"        [{j}] '{h}' → norm='{norm}' → {matched}")
            # 이후 5행
            for j in range(1, 6):
                if i+j < len(rows):
                    r = rows[i+j]
                    print(f"  [{i+j:>3}] ({len(r)}셀) {' | '.join(r[:8])}")
            print()
