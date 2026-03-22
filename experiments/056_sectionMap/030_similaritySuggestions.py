"""
실험 ID: 056-030
실험명: 미흡수 title 유사 키 추천

목적:
- 미흡수 title에 대해 기존 sectionMappings 키와의 유사도를 계산해 자동 추천 후보를 만들 수 있는지 검증한다.

가설:
1. 남은 예외 중 일부는 기존 canonical key와 유사도가 높아 자동 추천 후보로 활용 가능하다.
2. similarity는 자동 확정보다 수동 검토용 추천 계층으로 쓰는 것이 적절하다.

방법:
1. 현재 mapper 기준 미흡수 normalized title을 수집한다.
2. 기존 sectionMappings 키와 문자열 유사도를 계산한다.
3. 상위 추천 키와 점수를 출력한다.

결과 (실험 후 작성):

- 일부 미흡수 title은 기존 key와 유사도가 충분히 높아 추천 후보로 활용 가능
- `매출및수주상황(상세) -> 매출및수주상황 (0.778)`
- `연구개발실적 -> 연구개발실적(상세) (0.750)`
- `신용파생상품거래현황(상세) -> 파생상품거래현황 (0.727)`
결론:

- similarity는 자동 확정 규칙으로 쓰기보다, 수동 검토용 추천 계층으로 사용하는 것이 적절하다.
- 공통 section 정규화 + 하드코딩 예외로 대부분 흡수하고, 남은 예외는 similarity 추천을 보고 sectionMappings에 누적하는 흐름이 적합하다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path

import polars as pl

from dartlab.engines.company.dart.docs.sections.mapper import loadSectionMappings, normalizeSectionTitle


CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")


def base_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_dir() -> Path:
    return base_dir() / "data" / "dart" / "docs"


def load_uncovered_titles() -> list[str]:
    covered = set(loadSectionMappings().keys())
    titles: set[str] = set()
    for path in sorted(docs_dir().glob("*.parquet")):
        df = pl.read_parquet(path).with_columns(pl.col("year"))
        annual = df.filter(pl.col("report_type").str.contains("사업보고서"))
        if annual.height == 0:
            continue
        latest_year = annual.get_column("year").max()
        if latest_year is None:
            continue
        current = ""
        rows = annual.filter(pl.col("year") == latest_year).sort("section_order").get_column("section_title").to_list()
        for raw in rows:
            title = (raw or "").strip()
            match = CHAPTER_RE.match(title)
            if match:
                current = match.group(1)
                continue
            if not current:
                continue
            normalized = normalizeSectionTitle(title)
            if normalized not in covered:
                titles.add(normalized)
    return sorted(titles)


def top_matches(title: str, candidates: list[str], limit: int = 3) -> list[tuple[str, float]]:
    scored = []
    for candidate in candidates:
        ratio = SequenceMatcher(None, title, candidate).ratio()
        scored.append((candidate, ratio))
    scored.sort(key=lambda x: (-x[1], x[0]))
    return scored[:limit]


def main() -> None:
    uncovered = load_uncovered_titles()
    candidates = sorted(loadSectionMappings().keys())

    print("=" * 72)
    print("056-030 미흡수 title 유사 키 추천")
    print("=" * 72)
    for title in uncovered[:30]:
        matches = top_matches(title, candidates)
        formatted = ", ".join(f"{key} ({score:.3f})" for key, score in matches)
        print(f"{title} -> {formatted}")


if __name__ == "__main__":
    main()
