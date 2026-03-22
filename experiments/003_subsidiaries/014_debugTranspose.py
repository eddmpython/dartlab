"""횡전개 파서 디버깅."""
import re
from pathlib import Path

import polars as pl

DATA_DIR = Path("data/docsData")
exec(open("experiments/003_subsidiaries/007_v2Parse.py", encoding="utf-8").read().split("def main")[0])

out = []
def p(s=""):
    out.append(s)

# POSCO홀딩스 2024 - 변동 블록 디버깅
p("POSCO홀딩스 2024 - 횡전개 블록")
p("=" * 60)

df = pl.read_parquet(str(DATA_DIR / "005490.parquet"))
contents = extractNotes(df, "2024")
section = findSection(contents, "관계기업") or findSection(contents, "지분법") or findSection(contents, "공동기업")
rows = parseTableRows(section)

blocks = _findTransposedBlocks(rows)
p(f"블록 수: {len(blocks)}")
for bi, block in enumerate(blocks):
    p(f"\n  블록[{bi}] period={block['period']}, type={block['blockType']}, startRow={block['startRow']}")
    p(f"  기업명 수: {sum(1 for n in block['names'] if n)}")
    p(f"  기업명: {[n for n in block['names'][:5] if n]}")
    p(f"  항목 수: {len(block['items'])}")
    for itemName, vals in list(block['items'].items())[:8]:
        valPreview = [v for v in vals[:5]]
        p(f"    [{itemName}] ({len(vals)}개): {valPreview}")

# 삼성전자 2024 - 횡전개 블록
p("\n\n삼성전자 2024 - 횡전개 블록")
p("=" * 60)

df = pl.read_parquet(str(DATA_DIR / "005930.parquet"))
contents = extractNotes(df, "2024")
section = findSection(contents, "관계기업") or findSection(contents, "지분법") or findSection(contents, "공동기업")
rows = parseTableRows(section)

blocks = _findTransposedBlocks(rows)
p(f"블록 수: {len(blocks)}")
for bi, block in enumerate(blocks):
    p(f"\n  블록[{bi}] period={block['period']}, type={block['blockType']}, startRow={block['startRow']}")
    p(f"  기업명: {[n for n in block['names'][:5] if n]}")
    p(f"  항목 수: {len(block['items'])}")
    for itemName in list(block['items'].keys())[:8]:
        p(f"    [{itemName}]")

# 현대차 2024 - 횡전개 블록
p("\n\n현대차 2024 - 횡전개 블록")
p("=" * 60)

df = pl.read_parquet(str(DATA_DIR / "005380.parquet"))
contents = extractNotes(df, "2024")
section = findSection(contents, "관계기업") or findSection(contents, "지분법") or findSection(contents, "공동기업")
rows = parseTableRows(section)

blocks = _findTransposedBlocks(rows)
p(f"블록 수: {len(blocks)}")
for bi, block in enumerate(blocks):
    p(f"\n  블록[{bi}] period={block['period']}, type={block['blockType']}, startRow={block['startRow']}")
    p(f"  기업명: {[n for n in block['names'][:5] if n]}")
    p(f"  항목: {list(block['items'].keys())[:5]}")

# LG에너지솔루션 2024 - 횡전개 블록
p("\n\nLG에너지솔루션 2024 - 횡전개 블록")
p("=" * 60)

df = pl.read_parquet(str(DATA_DIR / "373220.parquet"))
contents = extractNotes(df, "2024")
section = findSection(contents, "관계기업") or findSection(contents, "지분법") or findSection(contents, "공동기업")
rows = parseTableRows(section)

blocks = _findTransposedBlocks(rows)
p(f"블록 수: {len(blocks)}")
for bi, block in enumerate(blocks):
    p(f"\n  블록[{bi}] period={block['period']}, type={block['blockType']}, startRow={block['startRow']}")
    p(f"  기업명: {[n for n in block['names'][:5] if n]}")
    p(f"  항목: {list(block['items'].keys())[:5]}")


outPath = Path("experiments/003_subsidiaries/output/debug_transpose.txt")
outPath.write_text("\n".join(out), encoding="utf-8")
print(f"결과 저장: {outPath} ({len(out)}줄)")
