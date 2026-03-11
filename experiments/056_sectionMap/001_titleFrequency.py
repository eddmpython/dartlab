"""
실험 ID: 056-001
실험명: section_title 전종목 빈도 분석

목적:
- docs parquet(270종목)에서 section_title 분포를 정량적으로 파악한다.
- 대분류(로마숫자)와 소분류 제목의 빈도 상위를 확인해 sectionMappings 표준화 우선순위를 정한다.

가설:
1. 대분류(장) 제목은 소수 패턴으로 수렴한다.
2. 소분류 제목은 변형이 많지만 상위 소수 항목이 전체의 대부분을 차지한다.

방법:
1. data/dart/docs/*.parquet를 전수 스캔한다.
2. section_title 컬럼을 읽고 로마숫자 대분류와 소분류 텍스트를 분리한다.
3. 대분류/소분류 빈도표를 계산한다.
4. 상위 항목 커버리지를 출력한다.

결과 (실험 후 작성):
- 스캔 파일 수: 270
- 총 section_title 행 수: 160,853
- 고유 section_title 수: 494
- 대분류 상위 빈도: UNKNOWN 116,604 / II 3,823 / VI 3,822 / VII 3,821 / VIII 3,820
- 소분류 상위 빈도: 임원 및 직원 등에 관한 사항 3,821 / 재무에 관한 사항 3,818 / 4. 주식의 총수 등 3,793
- Top10 소분류 커버리지: 23.20%

결론:
- 대분류 파싱이 가능한 로마숫자 제목은 충분히 일관적이며 II, VI, VII, VIII 등 핵심 장이 높은 빈도로 반복된다.
- `UNKNOWN`이 큰 이유는 section_title이 로마숫자 대분류가 아닌 소제목/하위목차 행을 다수 포함하기 때문으로 확인됐다.
- 다음 실험(002_autoNormalize.py)은 UNKNOWN 군집의 정규화 규칙(접두사 제거/특수문자 정규화/유사도 그룹핑)에 집중해야 한다.

실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl


CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")
SUB_RE = re.compile(r"^\s*(\d+)\.\s*(.*)$")


def docs_dir() -> Path:
    root = Path(__file__).resolve().parents[2]
    return root / "data" / "dart" / "docs"


def parse_section_title(title: str) -> tuple[str, str, str]:
    raw = (title or "").strip()
    m = CHAPTER_RE.match(raw)
    if not m:
        return ("UNKNOWN", "", raw)

    chapter = m.group(1)
    rest = m.group(2).strip()

    sm = SUB_RE.match(rest)
    if sm:
        return (chapter, sm.group(1), sm.group(2).strip())
    return (chapter, "", rest)


def load_titles(files: list[Path]) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    for fp in files:
        df = pl.read_parquet(fp, columns=["section_title"])
        df = df.with_columns(pl.col("section_title").cast(pl.Utf8).fill_null("").alias("section_title"))
        frames.append(df)

    if not frames:
        return pl.DataFrame({"section_title": []}, schema={"section_title": pl.Utf8})
    return pl.concat(frames, how="vertical")


def main() -> None:
    ddir = docs_dir()
    files = sorted(ddir.glob("*.parquet"))
    if not files:
        raise RuntimeError(f"docs parquet 없음: {ddir}")

    titles = load_titles(files)

    parsed = [parse_section_title(t) for t in titles["section_title"].to_list()]
    parsed_df = pl.DataFrame(
        parsed,
        schema={
            "chapter": pl.Utf8,
            "sub_num": pl.Utf8,
            "leaf_title": pl.Utf8,
        },
        orient="row",
    )

    chapter_freq = parsed_df.group_by("chapter").agg(pl.len().alias("count")).sort("count", descending=True)

    leaf_freq = (
        parsed_df.filter(pl.col("leaf_title") != "")
        .group_by("leaf_title")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
    )

    total_rows = parsed_df.height
    unique_titles = titles["section_title"].n_unique()

    top10_leaf = leaf_freq.head(10)
    top10_sum = int(top10_leaf["count"].sum()) if top10_leaf.height else 0
    top10_coverage = (top10_sum / total_rows * 100) if total_rows else 0.0

    print("=" * 72)
    print("056-001 section_title 빈도 분석")
    print("=" * 72)
    print(f"docs 파일 수: {len(files)}")
    print(f"총 section_title 행 수: {total_rows}")
    print(f"고유 section_title 수: {unique_titles}")
    print()

    print("[대분류 빈도 상위]")
    print(chapter_freq)
    print()

    print("[소분류(leaf_title) 상위 20]")
    print(leaf_freq.head(20))
    print()
    print(f"Top10 leaf coverage: {top10_coverage:.2f}% ({top10_sum}/{total_rows})")

    unknown_titles = (
        parsed_df.with_columns(titles["section_title"].alias("raw_title"))
        .filter(pl.col("chapter") == "UNKNOWN")
        .group_by("raw_title")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
        .head(20)
    )
    print()
    print("[UNKNOWN 상위 20]")
    print(unknown_titles)


if __name__ == "__main__":
    main()
