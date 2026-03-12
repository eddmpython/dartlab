"""
실험 ID: 056-002
실험명: boundary 후보 추출

목적:
- 최근 연도에 세분화가 증가한 사업보고서에서 canonical boundary 후보를 추출한다.
- 삼성전자 2021 -> 2022 사업보고서 변화를 기준 샘플로 삼아 chapter별 세분화 후보를 확인한다.

가설:
1. 2021 -> 2022 전환 구간에서 반복 가능한 canonical boundary가 추가된다.
2. 추가된 경계는 단순 title 증가가 아니라 사업보고서 개정 구조를 반영한다.

방법:
1. 삼성전자 docs parquet에서 사업보고서만 필터링한다.
2. 2021/2022 section_title 집합을 비교한다.
3. 2022에 새로 등장한 항목을 boundary 후보로 기록한다.
4. chapter별 세분화 수를 계산한다.

결과 (실험 후 작성):

- 2021 사업보고서 section 수: 31
- 2022 사업보고서 section 수: 47
- 추가된 boundary 후보 수: 24
- II장: `1. 사업의 개요`, `2. 주요 제품 및 서비스`, `3. 원재료 및 생산설비`, `4. 매출 및 수주상황`, `5. 위험관리 및 파생거래`, `6. 주요계약 및 연구개발활동`, `7. 기타 참고사항`
결론:

- 삼성전자 2022 사업보고서는 chapter 유지 + 하위 경계 세분화 패턴을 명확히 보여준다.
- 056의 canonical boundary teacher 샘플로 삼성전자 2022를 활용할 수 있다.
실험일: 2026-03-11
"""

from __future__ import annotations

from pathlib import Path

import polars as pl


def load_annual(stock_code: str) -> pl.DataFrame:
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "dart" / "docs" / f"{stock_code}.parquet"
    df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
    return df.filter(pl.col("report_type").str.contains("사업보고서"))


def year_titles(df: pl.DataFrame, year: str) -> list[str]:
    return df.filter(pl.col("year") == year).sort("section_order").get_column("section_title").to_list()


def chapter_counts(titles: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    current = "FRONT"
    for title in titles:
        stripped = title.strip()
        if stripped[:2] in {"I.", "V.", "X."} or stripped.startswith(
            ("II.", "III.", "IV.", "VI.", "VII.", "VIII.", "IX.", "XI.", "XII.")
        ):
            current = stripped.split()[0].replace(".", "")
            counts.setdefault(current, 0)
        else:
            counts[current] = counts.get(current, 0) + 1
    return counts


def main() -> None:
    df = load_annual("005930")
    titles_2021 = year_titles(df, "2021")
    titles_2022 = year_titles(df, "2022")

    set_2021 = set(titles_2021)
    set_2022 = set(titles_2022)
    added = sorted(set_2022 - set_2021)
    removed = sorted(set_2021 - set_2022)

    print("=" * 72)
    print("056-002 boundary 후보 추출")
    print("=" * 72)
    print(f"2021 rows: {len(titles_2021)}")
    print(f"2022 rows: {len(titles_2022)}")
    print(f"added: {len(added)}")
    for item in added:
        print(f" + {item}")
    print(f"removed: {len(removed)}")
    for item in removed:
        print(f" - {item}")
    print()
    print("[chapter detail counts]")
    print("2021", chapter_counts(titles_2021))
    print("2022", chapter_counts(titles_2022))


if __name__ == "__main__":
    main()
