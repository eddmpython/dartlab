"""
실험 ID: 056-028
실험명: 잔여 미흡수 title 패턴 군집화

목적:
- 현재 sectionMappings.json에 흡수되지 않은 normalized title을 패턴별로 군집화해 다음 누적 규칙을 정한다.

가설:
1. 남은 미흡수 title은 company-specific appendix, 지적재산권, 수주/생산설비, MD&A 변형 등 소수 패턴으로 묶인다.
2. 패턴 군집화를 하면 sectionMappings에 계속 누적할 예외군과 별도 appendix 계층으로 둘 항목을 분리할 수 있다.

방법:
1. 최신 사업보고서 전체에서 현재 mapper 기준 미흡수 normalized title을 수집한다.
2. 정규식 기반으로 패턴 라벨을 부여한다.
3. 라벨별 분포와 상위 title을 출력한다.

결과 (실험 후 작성):

- rows: `85`
- uniqueTitles: `77`
- `appendixDetail`: 36
- `appendixIp`: 16
결론:

- 현재 남은 미흡수 title은 대부분 XII장 appendix/detail 계열이다.
- 따라서 공통 sectionMappings는 거의 수렴했고, 이후 확장은 공통 section 추가보다 appendix/detail 계층 설계가 더 중요하다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

from dartlab.engines.dart.docs.sections.mapper import loadSectionMappings, normalizeSectionTitle


CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")


def base_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_dir() -> Path:
    return base_dir() / "data" / "dart" / "docs"


def classify(title: str, chapter: str) -> str:
    if chapter == "XII":
        if "지적재산권" in title or "특허" in title:
            return "appendixIp"
        if "수주" in title:
            return "appendixOrder"
        if "생산설비" in title or "영업설비" in title:
            return "appendixFacilities"
        if "세부내역" in title or "(상세)" in title:
            return "appendixDetail"
        return "appendixOther"
    if chapter in {"IV", "V", "VI"}:
        if "예측정보" in title:
            return "mdnaCaution"
        if "재무상태 및 영업실적" in title:
            return "mdnaPerformance"
        if "유동성" in title or "자금조달" in title:
            return "mdnaLiquidity"
        if "투자의사결정" in title:
            return "mdnaOther"
        if title == "개요":
            return "mdnaOverview"
    if "파생상품거래 현황" in title:
        return "riskVariant"
    if "확인" in title:
        return "confirmation"
    return "other"


def load_uncovered() -> pl.DataFrame:
    covered = set(loadSectionMappings().keys())
    rows: list[dict[str, str]] = []
    for path in sorted(docs_dir().glob("*.parquet")):
        stock_code = path.stem
        df = pl.read_parquet(path).with_columns(pl.col("year"))
        annual = df.filter(pl.col("report_type").str.contains("사업보고서"))
        if annual.height == 0:
            continue
        latest_year = annual.get_column("year").max()
        if latest_year is None:
            continue
        current = ""
        titles = (
            annual.filter(pl.col("year") == latest_year).sort("section_order").get_column("section_title").to_list()
        )
        for raw in titles:
            title = (raw or "").strip()
            match = CHAPTER_RE.match(title)
            if match:
                current = match.group(1)
                continue
            if not current:
                continue
            normalized = normalizeSectionTitle(title)
            if normalized in covered:
                continue
            rows.append(
                {
                    "stockCode": stock_code,
                    "chapter": current,
                    "rawTitle": title,
                    "normalizedTitle": normalized,
                    "pattern": classify(normalized, current),
                }
            )
    return pl.DataFrame(rows)


def main() -> None:
    df = load_uncovered()
    summary = (
        df.group_by("pattern")
        .agg(pl.len().alias("rows"), pl.col("normalizedTitle").n_unique().alias("uniqueTitles"))
        .sort("rows", descending=True)
    )
    top_titles = (
        df.group_by(["pattern", "normalizedTitle"])
        .agg(pl.col("stockCode").n_unique().alias("companyCoverage"), pl.len().alias("rows"))
        .sort(["rows", "companyCoverage", "normalizedTitle"], descending=[True, True, False])
        .head(40)
    )

    print("=" * 72)
    print("056-028 잔여 미흡수 title 패턴 군집화")
    print("=" * 72)
    print(f"rows={df.height}")
    print(f"uniqueTitles={df.get_column('normalizedTitle').n_unique()}")
    print()
    print("[pattern summary]")
    print(summary)
    print()
    print("[top titles]")
    print(top_titles)


if __name__ == "__main__":
    main()
