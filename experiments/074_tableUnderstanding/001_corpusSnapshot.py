"""
실험 ID: 074-001
실험명: sections-aware table corpus snapshot

목적:
- 로컬 DART/EDGAR docs 코퍼스의 실제 규모와 실험용 분석 샘플을 고정한다.
- 이후 실험이 어떤 데이터 스냅샷을 기준으로 한 것인지 재현 가능하게 만든다.

가설:
1. 로컬 DART docs는 300개 이상 회사, EDGAR docs는 900개 이상 ticker를 포함한다.
2. sample sections 기준으로 DART table topic은 audit/dividend/companyOverview 계열이 반복적으로 등장한다.
3. 전수 sections 파싱은 무겁기 때문에 raw corpus는 전수, sections 요약은 대표 샘플로 고정하는 편이 현실적이다.

방법:
1. `data/dart/docs`, `data/edgar/docs` parquet 파일 수를 전수 카운트한다.
2. DART 18개, EDGAR 6개 대표 종목 샘플을 고정한다.
3. 샘플에 대해 sections를 실제 생성하여 rows, table rows, topic 분포를 집계한다.

결과 (실험 후 작성):
- raw corpus: DART docs `319개`, EDGAR docs `974개`
- DART sample 18개 sections 집계: `186,006행`, table rows `22,312행`, unique table topic `51개`, median period cols `35.0`, elapsed `47.487초`
- EDGAR sample 6개 sections 집계: `9,335행`, table rows `169행`, unique table topic `35개`, median period cols `66.0`, elapsed `7.637초`
- DART sample top table topic: `appendixSchedule`, `consolidatedNotes`, `financialStatements`, `audit`, `contingentLiability`가 모두 `18/18`
- EDGAR sample top table topic: `10-K::item16Form10KSummary`, `10-K::item1ARiskFactors`, `10-Q::partIIItem2UnregisteredSalesAndUseOfProceeds`가 모두 `6/6`

결론:
- raw corpus는 충분히 크고, sections 기반 table topic도 풍부하다.
- 다만 전수 sections 파싱은 비싸므로 이후 실험은 raw corpus 전수 + sections sample 고정 전략이 맞다.
- DART는 docs table 실험의 주 코퍼스로 충분하고, EDGAR는 샘플 전이 검증 레일로 쓰는 것이 현실적이다.

실험일: 2026-03-20
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

import polars as pl

from dartlab import config
from dartlab.providers.dart.docs.sections.pipeline import sections as dart_sections
from dartlab.providers.edgar.docs.sections.pipeline import sections as edgar_sections

DART_PREFERRED = [
    "005930",
    "000660",
    "035720",
    "035420",
    "373220",
    "068270",
    "005380",
    "105560",
    "051910",
    "003550",
    "034730",
    "096770",
]

EDGAR_PREFERRED = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA"]


@dataclass
class SampleStats:
    ids: list[str]
    parsed: int
    total_rows: int
    table_rows: int
    unique_topics: int
    median_period_cols: float
    top_topics: list[tuple[str, int]]
    elapsed_sec: float


def period_columns(df: pl.DataFrame) -> list[str]:
    cols: list[str] = []
    for col in df.columns:
        if len(col) >= 4 and col[:4].isdigit():
            cols.append(col)
    return cols


def stable_sample(all_ids: list[str], preferred: list[str], limit: int) -> list[str]:
    picked: list[str] = []
    seen: set[str] = set()
    for value in preferred + all_ids:
        if value in seen or value not in all_ids:
            continue
        picked.append(value)
        seen.add(value)
        if len(picked) >= limit:
            break
    return picked


def analyze_sections(ids: list[str], loader) -> SampleStats:
    topic_counter: Counter[str] = Counter()
    total_rows = 0
    table_rows = 0
    parsed = 0
    period_counts: list[int] = []
    start = perf_counter()
    for value in ids:
        df = loader(value)
        if df is None or df.is_empty():
            continue
        parsed += 1
        total_rows += df.height
        if "blockType" in df.columns:
            table = df.filter(pl.col("blockType") == "table")
            table_rows += table.height
            if not table.is_empty():
                for topic in table["topic"].unique().to_list():
                    topic_counter[str(topic)] += 1
                period_counts.extend([len(period_columns(table))] * max(table.height, 1))
        else:
            period_counts.extend([len(period_columns(df))] * max(df.height, 1))
    elapsed = perf_counter() - start
    return SampleStats(
        ids=ids,
        parsed=parsed,
        total_rows=total_rows,
        table_rows=table_rows,
        unique_topics=len(topic_counter),
        median_period_cols=round(float(pl.Series(period_counts).median()) if period_counts else 0.0, 2),
        top_topics=topic_counter.most_common(10),
        elapsed_sec=round(elapsed, 3),
    )


def build_snapshot() -> dict[str, object]:
    data_dir = Path(config.dataDir)
    dart_ids = sorted(path.stem for path in (data_dir / "dart" / "docs").glob("*.parquet"))
    edgar_ids = sorted(path.stem for path in (data_dir / "edgar" / "docs").glob("*.parquet"))
    dart_sample = stable_sample(dart_ids, DART_PREFERRED, 18)
    edgar_sample = stable_sample(edgar_ids, EDGAR_PREFERRED, 6)
    return {
        "dataDir": str(data_dir),
        "dartRawCount": len(dart_ids),
        "edgarRawCount": len(edgar_ids),
        "dartSample": asdict(analyze_sections(dart_sample, dart_sections)),
        "edgarSample": asdict(analyze_sections(edgar_sample, edgar_sections)),
    }


def main() -> None:
    print(build_snapshot())


if __name__ == "__main__":
    main()
