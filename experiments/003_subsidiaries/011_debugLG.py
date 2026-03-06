"""LG에너지솔루션 2025 변동내역 디버깅."""
import re
from pathlib import Path
import polars as pl

exec(open("experiments/003_subsidiaries/007_v2Parse.py", encoding="utf-8").read().split("def main")[0])

df = pl.read_parquet("data/docsData/373220.parquet")
contents = extractNotes(df, "2025")
section = findSection(contents, "관계기업") or findSection(contents, "지분법") or findSection(contents, "공동기업")
rows = parseTableRows(section)

print(f"전체 행수: {len(rows)}")
for i in range(min(len(rows), 15)):
    cells = rows[i]
    print(f"[{i:>2}] ({len(cells)}셀) {' | '.join(cells)}")
print()

# 변동 추출 테스트
movements = extractMovements(rows)
print(f"\n변동내역: {len(movements)}개")
for mv in movements[:8]:
    print(f"  {mv.name}: opening={mv.opening}, closing={mv.closing}, equityIncome={mv.equityIncome}")
