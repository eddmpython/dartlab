"""
실험 ID: 004-001
실험명: 비용의 성격별 분류 데이터 탐색

목적:
- DART 공시에서 "비용의 성격별 분류" 데이터가 어디에, 어떤 형태로 들어있는지 파악
- section_title, 텍스트 패턴, 테이블 구조를 확인

가설:
1. 비용의 성격별 분류는 주석(연결재무제표 주석) 섹션에 포함되어 있을 것
2. "성격별" 또는 "비용의 성격" 키워드로 해당 영역을 찾을 수 있을 것

방법:
1. 삼성전자 parquet 로드
2. 모든 section_title에서 "비용" 또는 "성격" 키워드 검색
3. 해당 섹션 내용 일부를 출력하여 테이블 구조 확인
4. 여러 연도에 걸쳐 형식 변화가 있는지 확인

결과 (실험 후 작성):

결론:

실험일: 2026-03-06
"""

import polars as pl

DATA_PATH = "data/docsData/005930.parquet"

df = pl.read_parquet(DATA_PATH)

print("=" * 80)
print("컬럼:", df.columns)
print(f"행 수: {df.height}")
print()

print("=" * 80)
print("section_title 유니크 값 (비용/성격 관련)")
print("=" * 80)

titles = df["section_title"].unique().sort().to_list()
for t in titles:
    if "비용" in t or "성격" in t or "판매비" in t or "매출원가" in t:
        print(f"  {t}")

print()
print("=" * 80)
print("전체 section_title 목록")
print("=" * 80)
for t in titles:
    print(f"  {t}")

print()
print("=" * 80)
print("'비용' 키워드가 section_content에 포함된 행 탐색")
print("=" * 80)

costRows = df.filter(pl.col("section_content").str.contains("비용의 성격"))
print(f"'비용의 성격' 포함 행: {costRows.height}개")

if costRows.height > 0:
    for row in costRows.iter_rows(named=True):
        print(f"\n--- year={row['year']}, report_type={row['report_type']}")
        print(f"    section_title: {row['section_title']}")
        content = row["section_content"]
        idx = content.find("비용의 성격")
        if idx >= 0:
            snippet = content[max(0, idx - 100):idx + 2000]
            print(f"    내용 (발견 위치 주변 2000자):")
            print(snippet[:2000])
            print("    ...")
