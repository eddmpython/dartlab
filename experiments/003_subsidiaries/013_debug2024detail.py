"""2024 횡전개 상세 분석.

기업별 2024 포맷 분류:
- 횡전개(기업명=열): 네이버, POSCO일부, SK하이닉스일부
- 일반 테이블: 삼성전자, 현대차, LG전자, 카카오, 삼성SDI, LG에너지
"""
import re
from pathlib import Path
import polars as pl

DATA_DIR = Path("data/docsData")
OUT = Path("experiments/003_subsidiaries/output")

exec(open("experiments/003_subsidiaries/007_v2Parse.py", encoding="utf-8").read().split("def main")[0])

out = []
def p(s=""):
    out.append(s)

# SK하이닉스 2024: 횡전개 변동내역 (기업명=열, 기초/취득/... = 행)
p("=" * 60)
p("SK하이닉스 2024 - 횡전개 변동")
p("=" * 60)

df = pl.read_parquet(str(DATA_DIR / "000660.parquet"))
contents = extractNotes(df, "2024")
section = findSection(contents, "관계기업") or findSection(contents, "지분법") or findSection(contents, "공동기업")
rows = parseTableRows(section)

# 횡전개 구간 식별: 기업명 행(기업명 셀 다수) 바로 다음에 항목행(기초, 취득 등)
for i, cells in enumerate(rows):
    if len(cells) < 10:
        continue
    # 기업명 행 감지: 첫 셀이 빈칸이고 나머지가 기업명
    nameCount = sum(1 for c in cells[1:] if _isNameCell(c))
    if nameCount >= 3:
        p(f"\n  기업명행 [{i}] ({len(cells)}셀): 기업명={nameCount}개")
        p(f"    첫 5개: {' | '.join(cells[:6])}")
        # 다음 행들 확인
        for j in range(i+1, min(i+10, len(rows))):
            jcells = rows[j]
            if len(jcells) < 5:
                break
            first = jcells[0].strip()
            numCount = sum(1 for c in jcells[1:] if parseAmount(c) is not None)
            p(f"    [{j}] ({len(jcells)}셀) {first}: 숫자셀={numCount}")


# POSCO홀딩스 2024: 횡전개 변동내역
p("\n" + "=" * 60)
p("POSCO홀딩스 2024 - 횡전개 변동")
p("=" * 60)

df = pl.read_parquet(str(DATA_DIR / "005490.parquet"))
contents = extractNotes(df, "2024")
section = findSection(contents, "관계기업") or findSection(contents, "지분법") or findSection(contents, "공동기업")
rows = parseTableRows(section)

for i, cells in enumerate(rows):
    if len(cells) < 15:
        continue
    nameCount = sum(1 for c in cells[1:] if _isNameCell(c))
    if nameCount >= 3:
        p(f"\n  기업명행 [{i}] ({len(cells)}셀): 기업명={nameCount}개")
        p(f"    첫 5개: {' | '.join(cells[:6])}")
        # 다음 행들 확인
        for j in range(i+1, min(i+10, len(rows))):
            jcells = rows[j]
            if len(jcells) < 5:
                break
            first = jcells[0].strip()
            numCount = sum(1 for c in jcells[1:] if parseAmount(c) is not None)
            p(f"    [{j}] ({len(jcells)}셀) {first}: 숫자셀={numCount}")


# 네이버 2024: 횡전개 프로필 + 변동
p("\n" + "=" * 60)
p("네이버 2024 - 횡전개 프로필")
p("=" * 60)

df = pl.read_parquet(str(DATA_DIR / "035420.parquet"))
contents = extractNotes(df, "2024")
section = findSection(contents, "관계기업") or findSection(contents, "지분법") or findSection(contents, "공동기업")
rows = parseTableRows(section)

# 당기/전기 구분 위치 파악
for i, cells in enumerate(rows):
    if len(cells) <= 2:
        c0 = cells[0].strip()
        if c0 in ("당기", "전기"):
            p(f"  [{i}] {c0} 구간 시작")
    if len(cells) > 100:
        nameCount = sum(1 for c in cells[1:] if _isNameCell(c))
        numCount = sum(1 for c in cells[1:] if parseAmount(c) is not None)
        first = cells[0].strip() if cells[0].strip() else "(빈)"
        p(f"  [{i}] ({len(cells)}셀) [{first}]: 기업명={nameCount}, 숫자={numCount}")

# 변동내역 구간 찾기
p("\n  변동내역 구간:")
for i, cells in enumerate(rows):
    if len(cells) > 100:
        first = cells[0].strip()
        if "기초" in first or "취득" in first or "처분" in first or "기말" in first or "배당" in first or "지분법" in first:
            numCount = sum(1 for c in cells[1:] if parseAmount(c) is not None)
            p(f"  [{i}] ({len(cells)}셀) {first}: 숫자={numCount}")


# 삼성전자 2024: v2 파서가 못잡는 이유 확인
p("\n" + "=" * 60)
p("삼성전자 2024 - 기존 파서 테스트")
p("=" * 60)

df = pl.read_parquet(str(DATA_DIR / "005930.parquet"))
contents = extractNotes(df, "2024")
section = findSection(contents, "관계기업") or findSection(contents, "지분법") or findSection(contents, "공동기업")
if section:
    rows = parseTableRows(section)
    profiles = extractProfiles(rows)
    movements = extractMovements(rows)
    simpleMovs = extractSimpleMovement(rows)
    p(f"  프로필: {len(profiles)}개")
    p(f"  변동: {len(movements)}개")
    p(f"  간단변동: {len(simpleMovs)}개")
    for sm in simpleMovs:
        p(f"    {sm['항목']}: 당기={sm['당기']} 전기={sm['전기']}")

    # 투자현황 테이블 구간 - 전기/당기 별로 별도 테이블
    p(f"\n  투자현황 가능 구간:")
    for i, cells in enumerate(rows):
        if len(cells) >= 4:
            cellStr = " ".join(cells)
            if "장부금액" in cellStr or "취득원가" in cellStr or "지분율" in cellStr:
                p(f"  [{i}] ({len(cells)}셀) {' | '.join(cells[:8])}")
else:
    p("  섹션 없음")


outPath = OUT / "debug_2024_detail.txt"
outPath.write_text("\n".join(out), encoding="utf-8")
print(f"결과 저장: {outPath} ({len(out)}줄)")
