"""
실험 ID: 056-032
실험명: section title 정규화 ablation (공백/번호 제거 효과)

목적:
- section mapping 수평화에서 공백 제거와 leaf 번호 제거가 매핑 커버리지에 주는 영향을 정량 비교한다.

가설:
1. 공백 제거는 표기 흔들림을 줄여 커버리지를 개선한다.
2. `1.`/`가.` 같은 leaf prefix 제거는 동일 의미 title 병합에 유의미하다.
3. 공백 제거 + 번호 제거를 함께 쓰는 조합이 가장 높은 커버리지를 보인다.

방법:
1. data/dart/docs/*.parquet의 최신 사업보고서 section_title을 전수 스캔한다.
2. chapter 행(로마숫자)은 제외하고 leaf title만 비교한다.
3. normalization 조합 4개(raw, noSpace, noPrefix, noSpace+noPrefix)에 대해
   mapping key와 raw title을 동일 규칙으로 정규화한 뒤 coverage를 계산한다.

결과 (실험 후 작성):
- mappingKeys: 59
- latestLeafRows: 8,557
- coverage 비교:
  - raw: 0.9808 (uncovered 164)
  - noSpace: 0.9808 (uncovered 164)
  - noPrefix: 0.9845 (uncovered 133)
  - noSpaceNoPrefix: 0.9845 (uncovered 133)
  - noSpaceNoPrefixExt: 0.9845 (uncovered 133)

결론:
- 공백 제거 단독은 커버리지 개선 효과가 없다.
- leaf 번호 제거(`1.`, `가.`)는 커버리지를 +0.37%p 개선한다.
- 추가 확장 prefix(`1)`, `(1)`) 제거는 현재 데이터셋에서 추가 이득이 없다.

실험일: 2026-03-11
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import polars as pl


CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")
LEAF_PREFIX_RE = re.compile(r"^\d+\.\s*|^[가-힣]\.\s*")
LEAF_PREFIX_EXT_RE = re.compile(r"^\d+\.\s*|^\d+\)\s*|^\(\d+\)\s*|^[가-힣]\.\s*")
INDUSTRY_PREFIX_RE = re.compile(r"^\([^)]*업\)")
MULTISPACE_RE = re.compile(r"\s+")


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_dir() -> Path:
    return root_dir() / "data" / "dart" / "docs"


def mapping_path() -> Path:
    return (
        root_dir()
        / "src"
        / "dartlab"
        / "engines"
        / "dart"
        / "docs"
        / "sections"
        / "mapperData"
        / "sectionMappings.json"
    )


def normalize_common(text: str) -> str:
    out = text.strip()
    out = INDUSTRY_PREFIX_RE.sub("", out)
    out = out.replace("ㆍ", ",")
    return out.strip()


def normalize_raw(text: str) -> str:
    return normalize_common(text)


def normalize_no_space(text: str) -> str:
    out = normalize_common(text)
    return MULTISPACE_RE.sub("", out).strip()


def normalize_no_prefix(text: str) -> str:
    out = normalize_common(text)
    out = LEAF_PREFIX_RE.sub("", out)
    return out.strip()


def normalize_no_space_no_prefix(text: str) -> str:
    out = normalize_common(text)
    out = LEAF_PREFIX_RE.sub("", out)
    out = MULTISPACE_RE.sub("", out)
    return out.strip()


def normalize_no_space_no_prefix_ext(text: str) -> str:
    out = normalize_common(text)
    out = LEAF_PREFIX_EXT_RE.sub("", out)
    out = MULTISPACE_RE.sub("", out)
    return out.strip()


NORMALIZERS = {
    "raw": normalize_raw,
    "noSpace": normalize_no_space,
    "noPrefix": normalize_no_prefix,
    "noSpaceNoPrefix": normalize_no_space_no_prefix,
    "noSpaceNoPrefixExt": normalize_no_space_no_prefix_ext,
}


def latest_leaf_titles() -> list[str]:
    titles: list[str] = []
    for path in sorted(docs_dir().glob("*.parquet")):
        df = pl.read_parquet(path)
        annual = df.filter(pl.col("report_type").str.contains("사업보고서"))
        if annual.height == 0:
            continue
        latest_year = annual.get_column("year").max()
        if latest_year is None:
            continue

        rows = annual.filter(pl.col("year") == latest_year).sort("section_order").get_column("section_title").to_list()

        current_chapter = ""
        for raw in rows:
            title = (raw or "").strip()
            if not title:
                continue
            chapter_match = CHAPTER_RE.match(title)
            if chapter_match:
                current_chapter = chapter_match.group(1)
                continue
            if not current_chapter:
                continue
            titles.append(title)
    return titles


def load_mapping_keys() -> list[str]:
    raw = json.loads(mapping_path().read_text(encoding="utf-8"))
    return list(raw.keys())


def coverage_for(name: str, keys: list[str], titles: list[str]) -> dict[str, float | int | str]:
    normalizer = NORMALIZERS[name]
    norm_keys = {normalizer(key) for key in keys}
    norm_titles = [normalizer(title) for title in titles]

    total = len(norm_titles)
    uncovered = [title for title in norm_titles if title not in norm_keys]
    covered = total - len(uncovered)

    coverage = (covered / total) if total else 0.0
    unique_uncovered = len(set(uncovered))
    return {
        "mode": name,
        "totalRows": total,
        "coveredRows": covered,
        "coverage": round(coverage, 4),
        "uncoveredRows": len(uncovered),
        "uncoveredUnique": unique_uncovered,
    }


def main() -> None:
    keys = load_mapping_keys()
    titles = latest_leaf_titles()

    rows = [coverage_for(name, keys, titles) for name in NORMALIZERS]
    out = pl.DataFrame(rows).sort("coverage", descending=True)

    print("=" * 72)
    print("056-032 section title 정규화 ablation")
    print("=" * 72)
    print(f"mappingKeys={len(keys)}")
    print(f"latestLeafRows={len(titles)}")
    print(out)


if __name__ == "__main__":
    main()
