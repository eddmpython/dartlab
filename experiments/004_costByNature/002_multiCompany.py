"""
실험 ID: 004-002
실험명: 비용의 성격별 분류 — 다종목 패턴 확인

목적:
- 여러 종목에서 "비용의 성격별 분류" 테이블 존재 여부 확인
- 주석 번호, 계정 항목, 테이블 형식의 종목 간 차이 파악
- 분기/반기보고서에도 포함되는지 확인

가설:
1. K-IFRS 의무공시 항목이므로 거의 모든 종목에 존재할 것
2. 계정 항목은 종목마다 다를 수 있지만 기본 구조(제품변동, 원재료, 급여, 감가상각 등)는 유사
3. 분기/반기보고서 주석에도 포함될 것

방법:
1. 10개 종목 샘플링
2. 각 종목에서 "비용의 성격" 키워드 존재 여부, 주석 번호, 계정 항목 추출
3. 분기/반기/사업보고서별 존재 여부 확인

결과 (실험 후 작성):

결론:

실험일: 2026-03-06
"""

import re
from pathlib import Path

import polars as pl

DATA_DIR = Path("data/docsData")

files = sorted(DATA_DIR.glob("*.parquet"))[:10]

print(f"분석 대상: {len(files)}개 종목")
print("=" * 80)

for f in files:
    df = pl.read_parquet(str(f))
    corpName = df["corp_name"][0] if "corp_name" in df.columns else f.stem

    costRows = df.filter(pl.col("section_content").str.contains("비용의 성격"))

    if costRows.height == 0:
        print(f"\n{corpName} ({f.stem}): 비용의 성격 데이터 없음")
        continue

    reportTypes = costRows["report_type"].unique().to_list()
    years = sorted(costRows["year"].unique().to_list())

    hasBiz = any("사업보고서" in rt for rt in reportTypes)
    hasQuarter = any("분기보고서" in rt for rt in reportTypes)
    hasSemi = any("반기보고서" in rt for rt in reportTypes)

    print(f"\n{corpName} ({f.stem})")
    print(f"  행 수: {costRows.height}개")
    print(f"  연도: {years[0]}~{years[-1]}")
    print(f"  사업보고서: {'O' if hasBiz else 'X'} | 분기보고서: {'O' if hasQuarter else 'X'} | 반기보고서: {'O' if hasSemi else 'X'}")

    sample = costRows.filter(pl.col("report_type").str.contains("사업보고서")).head(1)
    if sample.height == 0:
        sample = costRows.head(1)

    content = sample["section_content"][0]
    idx = content.find("비용의 성격")
    if idx < 0:
        continue

    noteMatch = re.search(r"(\d+)\.\s*비용의 성격", content[max(0, idx - 20):idx + 30])
    noteNum = noteMatch.group(1) if noteMatch else "?"

    tableStart = content.find("|", idx)
    if tableStart < 0:
        print(f"  주석번호: {noteNum}번 (테이블 없음)")
        continue

    tableEnd = content.find("\n\n", tableStart)
    if tableEnd < 0:
        tableEnd = min(tableStart + 3000, len(content))

    tableText = content[tableStart:tableEnd]
    lines = [l for l in tableText.split("\n") if l.strip().startswith("|") and "---" not in l]

    accounts = []
    for line in lines:
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if cells and not any(k in cells[0] for k in ["단위", "구 분", "구분"]):
            accounts.append(cells[0])

    print(f"  주석번호: {noteNum}번")
    print(f"  계정 항목 ({len(accounts)}개): {accounts[:12]}")
