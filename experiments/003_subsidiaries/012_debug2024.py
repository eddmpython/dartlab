"""2024 XBRL 횡전개 포맷 탐색.

2024년 데이터는 기업명이 열 헤더로 들어가는 전치(transpose) 형태.
각 기업의 실제 구조를 확인한다.
"""
import re
from pathlib import Path

import polars as pl

DATA_DIR = Path("data/docsData")
OUT = Path("experiments/003_subsidiaries/output")
OUT.mkdir(exist_ok=True)

# 007_v2Parse.py의 extractNotes, findSection, parseTableRows 로드
exec(open("experiments/003_subsidiaries/007_v2Parse.py", encoding="utf-8").read().split("def main")[0])

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

out = []

def p(s=""):
    out.append(s)

for code, name in COMPANIES:
    path = DATA_DIR / f"{code}.parquet"
    if not path.exists():
        continue

    df = pl.read_parquet(str(path))
    contents = extractNotes(df, "2024")
    if not contents:
        p(f"\n{name}: 2024 주석 없음")
        continue

    section = findSection(contents, "관계기업")
    if section is None:
        section = findSection(contents, "지분법")
    if section is None:
        section = findSection(contents, "공동기업")
    if section is None:
        p(f"\n{name}: 2024 관계기업 섹션 없음")
        continue

    rows = parseTableRows(section)
    p(f"\n{'='*60}")
    p(f"  {name} ({code}) - 2024")
    p(f"{'='*60}")
    p(f"  총 행수: {len(rows)}")

    # 모든 행의 셀 수 분포
    cellCounts = {}
    for r in rows:
        n = len(r)
        cellCounts[n] = cellCounts.get(n, 0) + 1
    p(f"  셀수 분포: {sorted(cellCounts.items())}")

    # 거대행(>30셀) 존재 여부 → 횡전개 가능성
    bigRows = [(i, len(r)) for i, r in enumerate(rows) if len(r) > 30]
    if bigRows:
        p(f"  거대행: {len(bigRows)}개")
        for idx, cnt in bigRows[:3]:
            p(f"    [{idx}] {cnt}셀: {' | '.join(rows[idx][:8])}...")
            # 이 행에 기업명이 있는지 확인
            alphaCount = sum(1 for c in rows[idx] if _isNameCell(c))
            numCount = sum(1 for c in rows[idx] if parseAmount(c) is not None)
            p(f"      기업명셀={alphaCount}, 숫자셀={numCount}")
    else:
        p(f"  거대행 없음 → 일반 테이블")

    # 처음 20행 출력
    p(f"\n  처음 20행:")
    for i in range(min(len(rows), 20)):
        cells = rows[i]
        preview = ' | '.join(cells[:10])
        extra = f" ...+{len(cells)-10}" if len(cells) > 10 else ""
        p(f"  [{i:>3}] ({len(cells):>4}셀) {preview}{extra}")

    # 거대행 바로 다음 행들도 보기
    if bigRows:
        firstBig = bigRows[0][0]
        p(f"\n  거대행[{firstBig}] 이후 행:")
        for i in range(firstBig, min(firstBig + 15, len(rows))):
            cells = rows[i]
            preview = ' | '.join(cells[:10])
            extra = f" ...+{len(cells)-10}" if len(cells) > 10 else ""
            p(f"  [{i:>3}] ({len(cells):>4}셀) {preview}{extra}")

outPath = OUT / "debug_2024.txt"
outPath.write_text("\n".join(out), encoding="utf-8")
print(f"결과 저장: {outPath} ({len(out)}줄)")
