"""
실험 ID: 056-031
실험명: 최종 운영 가능성 검증

목적:
- 현재 sectionMappings 기반 sections 엔진 spike가 실전 운영 가능한 수준인지 최종 판정한다.

가설:
1. 공통 section 매핑은 운영 가능한 수준의 coverage와 실행 속도를 확보했다.
2. 남은 미흡수는 공통 core가 아니라 appendix/detail 위주라 운영 리스크가 제한적이다.

방법:
1. 최신 사업보고서 전체 기준 coverage를 계산한다.
2. 대표 10개 기업에서 sections() 실행 시간과 canonical hit를 측정한다.
3. 남은 미흡수 title이 appendix/detail 계열인지 비율을 계산한다.

결과 (실험 후 작성):

- coverage: `0.990`
- uncovered rows: `85`
- uncovered unique titles: `75`
- appendix/detail 비중: `0.976`
결론:

- 공통 section mapping은 **운영 가능한 수준**으로 판단한다.
- 남은 미흡수의 97.6%가 appendix/detail 계열이므로, 현재 공통 section map의 주된 리스크는 core section 누락이 아니다.
- 따라서 공통 section map은 현재 상태로 운영 가능하며, 이후 개선은 appendix/detail 계층 설계와 예외 누적 중심으로 진행한다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path
from time import perf_counter

import polars as pl

from dartlab.providers.dart.docs.sections.mapper import loadSectionMappings, normalizeSectionTitle
from dartlab.providers.dart.docs.sections.pipeline import sections

CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")
TARGET_CODES = ["005930", "000660", "035420", "035720", "005380", "005490", "012330", "051910", "066570", "207940"]
CANONICAL_KEYS = {"companyOverview", "companyHistory", "businessOverview", "salesOrder", "riskDerivative", "audit"}


def base_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_dir() -> Path:
    return base_dir() / "data" / "dart" / "docs"


def classify_remaining(title: str, chapter: str) -> str:
    if chapter == "XII":
        return "appendixDetail"
    if any(token in title for token in ["지적재산권", "특허", "수주", "생산설비", "영업설비", "세부내역", "(상세)"]):
        return "appendixLike"
    return "coreLike"


def latest_uncovered_stats() -> tuple[float, int, int, float]:
    covered = set(loadSectionMappings().keys())
    rows: list[dict[str, str]] = []
    total = 0
    for path in sorted(docs_dir().glob("*.parquet")):
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
            total += 1
            normalized = normalizeSectionTitle(title)
            if normalized in covered:
                continue
            rows.append(
                {
                    "chapter": current,
                    "normalized": normalized,
                    "bucket": classify_remaining(normalized, current),
                }
            )

    uncovered = (
        pl.DataFrame(rows)
        if rows
        else pl.DataFrame(
            {"chapter": [], "normalized": [], "bucket": []},
            schema={"chapter": pl.Utf8, "normalized": pl.Utf8, "bucket": pl.Utf8},
        )
    )
    coverage = 1 - (uncovered.height / total) if total else 0.0
    appendix_ratio = (
        uncovered.filter(pl.col("bucket") != "coreLike").height / uncovered.height if uncovered.height else 1.0
    )
    return (
        coverage,
        uncovered.height,
        uncovered.get_column("normalized").n_unique() if uncovered.height else 0,
        appendix_ratio,
    )


def runtime_stats() -> tuple[float, float, float]:
    elapsed_list: list[float] = []
    success = 0
    hit_total = 0
    for code in TARGET_CODES:
        started = perf_counter()
        df = sections(code)
        elapsed = perf_counter() - started
        elapsed_list.append(elapsed)
        if df is None:
            continue
        success += 1
        topics = set(df.get_column("topic").to_list())
        hit_total += len(CANONICAL_KEYS & topics)

    avg_elapsed = sum(elapsed_list) / len(elapsed_list)
    success_ratio = success / len(TARGET_CODES)
    avg_hits = hit_total / success if success else 0.0
    return avg_elapsed, success_ratio, avg_hits


def main() -> None:
    coverage, uncovered_rows, uncovered_unique, appendix_ratio = latest_uncovered_stats()
    avg_elapsed, success_ratio, avg_hits = runtime_stats()

    print("=" * 72)
    print("056-031 최종 운영 가능성 검증")
    print("=" * 72)
    print(f"coverage={coverage:.3f}")
    print(f"uncovered_rows={uncovered_rows}")
    print(f"uncovered_unique_titles={uncovered_unique}")
    print(f"appendix_ratio_in_uncovered={appendix_ratio:.3f}")
    print(f"avg_elapsed_sec={avg_elapsed:.3f}")
    print(f"success_ratio={success_ratio:.3f}")
    print(f"avg_canonical_hits={avg_hits:.3f}")


if __name__ == "__main__":
    main()
