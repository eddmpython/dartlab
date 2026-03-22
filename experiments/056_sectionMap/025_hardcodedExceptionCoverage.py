"""
실험 ID: 056-025
실험명: 하드코딩 예외 매핑 커버리지 검증

목적:
- 기본 정규화 기반 draft mapping에 하드코딩 예외 매핑을 추가했을 때 최신 사업보고서 커버리지가 얼마나 오르는지 확인한다.

가설:
1. uncovered 상위 예외 몇 개만 하드코딩해도 raw coverage가 유의미하게 상승한다.
2. section 매핑도 account 매핑처럼 규칙 + 하드코딩 조합이 가장 현실적이다.

방법:
1. 최신 사업보고서 전체 raw title을 수집한다.
2. draft mapping만 적용한 baseline coverage를 계산한다.
3. uncovered 상위 예외 title에 하드코딩 매핑을 추가한 뒤 coverage를 다시 계산한다.

결과 (실험 후 작성):

- baseline coverage: 0.963
- hardcoded coverage: 0.980
- delta: +0.017
- 추가 하드코딩 예외 수: 7
결론:

- section 매핑도 account 매핑과 마찬가지로 `기본 정규화 + 하드코딩 예외` 조합이 효과적이다.
- 상위 예외 7개만 추가해도 raw coverage가 96.3% -> 98.0%로 상승했다.
- 따라서 다음 단계는 예외 패턴을 더 확장하기보다, 이 하드코딩 예외를 draft 파일에 실제로 병합하는 것이다.
실험일: 2026-03-11
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import polars as pl

CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")
INDUSTRY_PREFIX_RE = re.compile(r"^\([^)]*업\)")

HARDCODED_EXCEPTIONS = {
    "1. 공시내용 진행 및 변경사항": "disclosureChanges",
    "2. 영업의 현황": "businessStatus",
    "4. 연구개발실적(상세)": "rndDetail",
    "4. 연구개발 실적(상세)": "rndDetail",
    "4. 영업설비": "operatingFacilities",
    "5. 재무건전성 등 기타 참고사항": "financialSoundnessOtherReference",
    "1. 전문가의 확인": "expertConfirmation",
}


def base_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_dir() -> Path:
    return base_dir() / "data" / "dart" / "docs"


def draft_path() -> Path:
    return Path(__file__).resolve().parent / "output" / "sectionMappings.draft.json"


def normalize_title(title: str) -> str:
    text = title.strip()
    text = INDUSTRY_PREFIX_RE.sub("", text)
    text = text.replace("ㆍ", ",")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def latest_title_rows() -> list[dict[str, str]]:
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
        for raw_title in titles:
            stripped = (raw_title or "").strip()
            match = CHAPTER_RE.match(stripped)
            if match:
                current = match.group(1)
                continue
            if not current:
                continue
            rows.append(
                {
                    "stockCode": stock_code,
                    "chapter": current,
                    "rawTitle": stripped,
                    "normalizedTitle": normalize_title(stripped),
                }
            )
    return rows


def coverage(df: pl.DataFrame, mapping_keys: set[str]) -> float:
    total = df.height
    covered = df.filter(pl.col("normalizedTitle").is_in(list(mapping_keys))).height
    return covered / total if total else 0.0


def main() -> None:
    draft_mapping = json.loads(draft_path().read_text(encoding="utf-8"))
    df = pl.DataFrame(latest_title_rows())

    baseline = coverage(df, set(draft_mapping.keys()))
    combined_mapping = {**draft_mapping, **HARDCODED_EXCEPTIONS}
    improved = coverage(df, set(combined_mapping.keys()))

    print("=" * 72)
    print("056-025 하드코딩 예외 매핑 커버리지 검증")
    print("=" * 72)
    print(f"baseline_coverage={baseline:.3f}")
    print(f"hardcoded_coverage={improved:.3f}")
    print(f"delta={improved - baseline:.3f}")
    print(f"hardcoded_count={len(HARDCODED_EXCEPTIONS)}")


if __name__ == "__main__":
    main()
