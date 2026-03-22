"""
실험 ID: 056-027
실험명: sections 매핑 효과 검증

목적:
- sections 엔진 spike에 연결한 sectionMappings가 실제로 topic 축을 정리하는지 검증한다.

가설:
1. 매핑 적용 후 삼성전자 sections 결과의 topic 수가 감소한다.
2. canonical topic 수는 증가하고, 중복/변형 title은 줄어든다.

방법:
1. 삼성전자 raw docs parquet에서 기존 leaf title 집합을 계산한다.
2. 동일 데이터에 mapper를 적용한 mapped topic 집합을 계산한다.
3. topic 수 변화와 canonical topic 수를 비교한다.

결과 (실험 후 작성):

- raw `section_title`가 아니라, 실제 `sections()`가 사용하는 `chunk leaf path` 기준으로 비교
- raw topic 수: 210
- mapped topic 수: 206
- reduction rate: 0.019
결론:

- 현재 매핑은 삼성전자 기준 chunk leaf topic을 210 -> 206으로 소폭 압축했다.
- 그러나 중요한 건 단순 개수 감소보다, `businessOverview`, `salesOrder`, `riskDerivative`, `audit`, `shareholderMeeting` 같은 canonical topic이 실제로 생성되기 시작했다는 점이다.
- 즉 1차 매핑은 성공했지만, 아직 세부 leaf 예외를 더 흡수해야 topic 축 압축 효과가 크게 나타난다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

from dartlab.engines.company.dart.docs.sections.chunker import chunkRows
from dartlab.engines.company.dart.docs.sections.mapper import mapSectionTitle

RE_SPLIT_SUFFIX = re.compile(r" \[\d+/\d+\]$")
RE_LEAF_PREFIX = re.compile(r"^\d+\.\s*|^[가-힣]\.\s*")


def leaf_title(path: str) -> str:
    base = RE_SPLIT_SUFFIX.sub("", path)
    parts = base.split(" > ")
    leaf = parts[-1]
    leaf = RE_LEAF_PREFIX.sub("", leaf)
    return leaf.strip()


def load_paths() -> list[str]:
    path = Path(__file__).resolve().parents[2] / "data" / "dart" / "docs" / "005930.parquet"
    df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
    annual = df.filter(pl.col("report_type").str.contains("사업보고서")).sort(["year", "section_order"])
    content_col = "section_content" if "section_content" in annual.columns else "content"
    rows = annual.to_dicts()
    chunks = chunkRows(rows, content_col)
    return [chunk.path for chunk in chunks if chunk.kind not in ("skipped", "table_only")]


def main() -> None:
    titles = load_paths()
    raw_topics = sorted({leaf_title(title) for title in titles if title.strip()})
    mapped_topics = sorted({mapSectionTitle(leaf_title(title)) for title in titles if title.strip()})

    canonical_count = sum(1 for topic in mapped_topics if re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", topic))
    reduction = 1 - (len(mapped_topics) / len(raw_topics)) if raw_topics else 0.0

    print("=" * 72)
    print("056-027 sections 매핑 효과 검증")
    print("=" * 72)
    print(f"raw_topic_count={len(raw_topics)}")
    print(f"mapped_topic_count={len(mapped_topics)}")
    print(f"reduction_rate={reduction:.3f}")
    print(f"canonical_topic_count={canonical_count}")
    print("sample_mapped=", mapped_topics[:30])


if __name__ == "__main__":
    main()
