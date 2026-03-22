"""
실험 ID: 001
실험명: 타법인출자 현황 섹션 구조 탐색

목적:
- 사업보고서 "타법인출자 현황" 섹션 데이터 구조 파악
- 테이블 헤더/셀 구조 분석

가설:
1. "타법인출자" 또는 "타법인 출자" 키워드로 섹션 검색 가능
2. 16셀 구조: 법인명/상장/취득일/목적/취득금액/기초3/증감3/기말3/재무2

방법:
1. 삼성전자 사업보고서에서 타법인출자 섹션 추출
2. 테이블 헤더/데이터 행 구조 분석

결과:
- 삼성전자 "3. 타법인출자 현황(상세)" 섹션 확인
- 16셀 구조: [0]법인명 [1]상장여부 [2]최초취득일 [3]출자목적 [4]최초취득금액
  [5]기초수량 [6]기초지분율 [7]기초장부가 [8]취득수량 [9]취득금액
  [10]평가손익 [11]기말수량 [12]기말지분율 [13]기말장부가 [14]총자산 [15]당기순손익
- 데이터 행: 삼성전기, 삼성SDI, 삼성중공업 등 자회사/관계사 목록

결론:
- 16셀 구조가 표준 패턴 → 다종목 비교 후 파서 구축 가능

실험일: 2026-03-07
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "docsData"

CODE = "005930"


def main():
    path = DATA_DIR / f"{CODE}.parquet"
    df = pl.read_parquet(str(path))
    corpName = df["corp_name"].unique().to_list()[0]
    years = sorted(df["year"].unique().to_list(), reverse=True)

    print(f"[{CODE}] {corpName}")
    print(f"연도: {years}")
    print("=" * 100)

    for year in years[:2]:
        rows = df.filter(
            (pl.col("year") == year)
            & pl.col("section_title").str.contains("타법인")
            & pl.col("report_type").str.contains("사업보고서")
            & ~pl.col("report_type").str.contains("기재정정|첨부")
        )
        if rows.height == 0:
            rows = df.filter(
                (pl.col("year") == year)
                & pl.col("section_title").str.contains("출자")
                & pl.col("report_type").str.contains("사업보고서")
            )
        if rows.height == 0:
            print(f"\n{year}: 타법인출자 섹션 없음")
            continue

        for i in range(rows.height):
            title = rows["section_title"][i]
            content = rows["section_content"][i]
            print(f"\n{year}: [{title}] ({len(content)}자)")

            lines = content.split("\n")
            tableLines = 0
            for line in lines:
                s = line.strip()
                if not s.startswith("|"):
                    continue
                cells = [c.strip() for c in s.split("|")]
                if cells and cells[0] == "":
                    cells = cells[1:]
                if cells and cells[-1] == "":
                    cells = cells[:-1]
                if len(cells) < 3:
                    continue
                tableLines += 1
                if tableLines <= 20:
                    print(f"  [{len(cells)}셀] {s[:200]}")

            print(f"  총 테이블 행: {tableLines}")


if __name__ == "__main__":
    main()
