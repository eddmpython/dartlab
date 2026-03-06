"""
실험 ID: 004-004
실험명: 비용의 성격별 분류 — 파싱 실패 원인 분석

목적:
- 003에서 실패한 케이스들의 원인 파악
- 크게 두 가지: (A) 섹션 자체를 못 찾는 경우, (B) 테이블 구조가 다른 경우

방법:
1. 섹션 미발견 종목(동화약품, 현대건설, 유진증권) — 키워드 존재 여부, 주석 섹션 구조 확인
2. 파싱 실패 종목(기아, SK하이닉스, 금호전기, 동국홀딩스) — 테이블 구조 유형 분류

결과 (실험 후 작성):

결론:

실험일: 2026-03-06
"""

import re
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.core.reportSelector import selectReport

DATA_DIR = Path("data/docsData")

FAIL_CODES = {
    "000020": "동화약품",
    "000720": "현대건설",
    "001200": "유진증권",
}

TABLE_FAIL_CODES = {
    "000270": "기아",
    "000660": "SK하이닉스",
    "001210": "금호전기",
    "001230": "동국홀딩스",
}


def getLatestReport(df: pl.DataFrame) -> pl.DataFrame | None:
    years = sorted(df["year"].unique().to_list(), reverse=True)
    for y in years:
        r = selectReport(df, y, reportKind="annual")
        if r is not None:
            return r
    return None


print("=" * 80)
print("PART A: 섹션 미발견 종목 — 키워드 존재 여부 확인")
print("=" * 80)

for code, name in FAIL_CODES.items():
    fpath = DATA_DIR / f"{code}.parquet"
    if not fpath.exists():
        print(f"\n{name} ({code}): 파일 없음")
        continue

    df = pl.read_parquet(str(fpath))
    report = getLatestReport(df)
    if report is None:
        print(f"\n{name} ({code}): 보고서 없음")
        continue

    print(f"\n{name} ({code}) — year={report['year'][0]}")

    allSections = report["section_title"].to_list()
    noteSections = [s for s in allSections if "주석" in s]
    print(f"  주석 섹션: {noteSections}")

    allContents = report.filter(
        pl.col("section_title").str.contains("주석")
    )["section_content"].to_list()

    if not allContents:
        allContents = report["section_content"].to_list()
        print(f"  (주석 없음, 전체 섹션에서 검색)")

    found = False
    for content in allContents:
        idx = content.find("비용의 성격")
        if idx >= 0:
            found = True
            snippet = content[max(0, idx - 100):idx + 300]
            print(f"  '비용의 성격' 발견! (content 내 위치: {idx})")

            nearLines = content[max(0, idx - 200):idx + 50].split("\n")
            for nl in nearLines[-5:]:
                print(f"    > {nl[:120]}")
            break

    if not found:
        costRows = df.filter(pl.col("section_content").str.contains("비용의 성격"))
        if costRows.height > 0:
            sample = costRows.head(1)
            print(f"  최신 보고서에는 없지만 다른 데이터에서 발견됨")
            print(f"    year={sample['year'][0]}, report_type={sample['report_type'][0]}")
            print(f"    section_title={sample['section_title'][0]}")
        else:
            print(f"  전체 데이터에도 '비용의 성격' 없음")


print()
print("=" * 80)
print("PART B: 테이블 구조 실패 종목 — 테이블 패턴 분류")
print("=" * 80)

for code, name in TABLE_FAIL_CODES.items():
    fpath = DATA_DIR / f"{code}.parquet"
    if not fpath.exists():
        continue

    df = pl.read_parquet(str(fpath))
    report = getLatestReport(df)
    if report is None:
        continue

    allContents = report.filter(
        pl.col("section_title").str.contains("주석")
    )["section_content"].to_list()

    print(f"\n{name} ({code})")

    for content in allContents:
        lines = content.split("\n")
        startIdx = None

        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|"):
                continue
            m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
            if m and "비용의 성격" in m.group(2):
                startIdx = i
                break

        if startIdx is None:
            continue

        endIdx = None
        for i in range(startIdx + 1, len(lines)):
            s = lines[i].strip()
            if s.startswith("|"):
                continue
            m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
            if m:
                endIdx = i
                break

        if endIdx is None:
            endIdx = min(startIdx + 80, len(lines))

        sectionLines = lines[startIdx:endIdx]

        tableLines = [l for l in sectionLines if l.strip().startswith("|")]
        hasMultiTable = False
        tableCount = 0
        prevWasTable = False
        for l in sectionLines:
            isTable = l.strip().startswith("|")
            if isTable and not prevWasTable:
                tableCount += 1
            prevWasTable = isTable

        hasDanggi = any("당기" in l for l in sectionLines if not l.strip().startswith("|"))
        hasJeongi = any("전기" in l for l in sectionLines if not l.strip().startswith("|"))
        hasSplitPeriod = any("당기" in l and "전기" not in l for l in tableLines[:3])
        hasMultiCol = any(
            len([c for c in l.split("|") if c.strip()]) >= 4
            for l in tableLines[:5]
        )

        print(f"  테이블 블록 수: {tableCount}")
        print(f"  테이블 행 수: {len(tableLines)}")
        print(f"  당기/전기 별도 블록: {'Y' if hasDanggi or hasJeongi else 'N'}")
        print(f"  단일 컬럼(공시금액): {'Y' if not hasMultiCol else 'N'}")
        print(f"  멀티 컬럼(판관비/원가/합계): {'Y' if hasMultiCol else 'N'}")
        print(f"  --- 첫 30행 ---")
        for l in sectionLines[:30]:
            print(f"    {l[:120]}")
        break
