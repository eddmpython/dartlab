"""
실험 ID: 056-009
실험명: 업종 접두사 정규화 검증

목적:
- II장 등에서 나타나는 업종 접두사(`(금융업)`, `(제조서비스업)` 등)를 제거하면 canonical boundary 커버리지가 개선되는지 검증한다.

가설:
1. 업종 접두사 제거만으로 II장 커버리지가 유의미하게 상승한다.
2. exact match보다 normalized match가 canonical boundary에 적합하다.

방법:
1. 대표 10개 기업 최신 사업보고서의 II장 boundary를 수집한다.
2. teacher(삼성전자) II장과 exact match, normalized match를 각각 계산한다.

결과 (실험 후 작성):

- II장 exact avg coverage: 0.80
- II장 normalized avg coverage: 0.80
- 현재 대표 10개 샘플에서는 업종 접두사 제거만으로 평균 커버리지가 추가 상승하지 않았다.
- 이는 II장의 차이가 단순 접두사 문제가 아니라 업종별 boundary 자체 차이도 포함함을 시사한다.
결론:

- 현재 대표 10개 샘플에서는 업종 접두사 제거만으로 평균 커버리지가 추가 상승하지 않았다.
- 이는 II장의 차이가 단순 접두사 문제가 아니라 업종별 boundary 자체 차이도 포함함을 시사한다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

TARGET_CODES = ["005930", "000660", "035420", "035720", "005380", "005490", "012330", "051910", "066570", "207940"]
CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")
PREFIX_RE = re.compile(r"^\([^)]*업\)")


def load_latest_titles(stock_code: str) -> list[str]:
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "dart" / "docs" / f"{stock_code}.parquet"
    df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
    annual = df.filter(pl.col("report_type").str.contains("사업보고서"))
    latest_year = annual.get_column("year").max()
    if latest_year is None:
        raise RuntimeError(f"사업보고서 없음: {stock_code}")
    return annual.filter(pl.col("year") == latest_year).sort("section_order").get_column("section_title").to_list()


def chapter_items(titles: list[str], chapter_target: str) -> list[str]:
    current = ""
    items: list[str] = []
    for title in titles:
        stripped = title.strip()
        m = CHAPTER_RE.match(stripped)
        if m:
            current = m.group(1)
            continue
        if current == chapter_target:
            items.append(stripped)
    return items


def normalize(title: str) -> str:
    title = PREFIX_RE.sub("", title.strip())
    title = re.sub(r"\s+", " ", title)
    return title


def main() -> None:
    teacher = set(chapter_items(load_latest_titles("005930"), "II"))
    teacher_norm = {normalize(t) for t in teacher}
    exact_scores: list[float] = []
    norm_scores: list[float] = []

    for code in TARGET_CODES:
        items = set(chapter_items(load_latest_titles(code), "II"))
        items_norm = {normalize(t) for t in items}
        exact_scores.append(len(items & teacher) / len(teacher))
        norm_scores.append(len(items_norm & teacher_norm) / len(teacher_norm))

    print("=" * 72)
    print("056-009 업종 접두사 정규화 검증")
    print("=" * 72)
    print(f"II exact avg coverage: {sum(exact_scores) / len(exact_scores):.2f}")
    print(f"II normalized avg coverage: {sum(norm_scores) / len(norm_scores):.2f}")


if __name__ == "__main__":
    main()
