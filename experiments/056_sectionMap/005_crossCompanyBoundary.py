"""
실험 ID: 056-005
실험명: 다기업 공통 boundary 추출

목적:
- 삼성전자 단일 teacher를 넘어 여러 대형주 사업보고서를 비교해 chapter별 공통 boundary를 추출한다.
- 비어 있던 장(IV, VII, IX, X 포함)의 공통 경계를 보강한다.

가설:
1. 최근 연도 대형주의 사업보고서를 묶으면 chapter별 공통 boundary가 더 안정적으로 드러난다.
2. 삼성전자에서 비어 있던 장도 타 기업을 통해 canonical boundary 후보를 채울 수 있다.

방법:
1. 대표 대형주 10개 종목의 최신 사업보고서를 읽는다.
2. chapter 아래 하위 title을 집계한다.
3. 출현 기업 수가 높은 title을 공통 boundary 후보로 본다.

결과 (실험 후 작성):

- 비교 기업 수: 10개
- I장 공통 boundary: 5/5가 10개 기업 모두 일치
- II장 공통 boundary: 7개 core가 8개 기업에서 동일하게 반복
- III장 공통 boundary: `2. 연결재무제표`를 제외하면 거의 전 기업 공통
결론:

- 삼성전자 2022 draft는 상당 부분 범용 canonical boundary로 확장 가능하다.
- 다만 II장 업종 접두사 변형(`(금융업)`, `(제조서비스업)`)과 XII장 상세표는 업종별/회사별 보정 계층이 필요하다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import polars as pl


CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")
TARGET_CODES = [
    "005930",
    "000660",
    "035420",
    "035720",
    "005380",
    "005490",
    "012330",
    "051910",
    "066570",
    "207940",
]


def load_latest_annual_titles(stock_code: str) -> list[str]:
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "dart" / "docs" / f"{stock_code}.parquet"
    df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
    annual = df.filter(pl.col("report_type").str.contains("사업보고서"))
    latest_year = annual.get_column("year").max()
    if latest_year is None:
        raise RuntimeError(f"사업보고서 없음: {stock_code}")
    return annual.filter(pl.col("year") == latest_year).sort("section_order").get_column("section_title").to_list()


def chapter_map(titles: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    current: str | None = None
    for title in titles:
        stripped = title.strip()
        match = CHAPTER_RE.match(stripped)
        if match:
            chapter = match.group(1)
            current = chapter
            result.setdefault(chapter, [])
            continue
        if current is not None:
            result.setdefault(current, []).append(stripped)
    return result


def main() -> None:
    per_chapter: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    used_codes: list[str] = []

    for code in TARGET_CODES:
        titles = load_latest_annual_titles(code)
        used_codes.append(code)
        cmap = chapter_map(titles)
        for chapter, items in cmap.items():
            for item in items:
                per_chapter[chapter][item].add(code)

    print("=" * 72)
    print("056-005 다기업 공통 boundary 추출")
    print("=" * 72)
    print(f"대상 기업 수: {len(used_codes)}")
    print(f"종목: {', '.join(used_codes)}")

    for chapter in sorted(per_chapter.keys()):
        ranked = sorted(
            per_chapter[chapter].items(),
            key=lambda kv: (-len(kv[1]), kv[0]),
        )
        print(f"\n[{chapter}] top candidates")
        for title, codes in ranked[:10]:
            print(f" - {title} :: {len(codes)}개 기업")


if __name__ == "__main__":
    main()
