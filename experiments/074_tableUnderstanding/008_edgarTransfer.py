"""
실험 ID: 074-008
실험명: DART-first understanding scorer의 EDGAR 전이 검증

목적:
- DART에서 만든 sections-aware table understanding scorer가 EDGAR markdown table에도 어느 정도 통하는지 본다.
- 무엇이 그대로 전이되고 무엇이 DART 전용 prior에 묶이는지 구분한다.

가설:
1. structureType, numericRatio, rowCore overlap 같은 피처는 EDGAR에도 일부 전이된다.
2. topic prior가 없는 상태라 raw_fallback 비중이 올라간다.
3. EDGAR는 HTML->markdown 변환 흔적 때문에 header drift/raw_fallback이 더 많다.

방법:
1. AAPL/MSFT/NVDA/AMZN/META/TSLA를 샘플 ticker로 고정한다.
2. 각 ticker의 table row 중 period coverage가 있는 topic/block을 최대 8개씩 뽑는다.
3. DART scorer를 수정 없이 적용해 action 분포와 drift flag를 본다.

결과 (실험 후 작성):
- EDGAR sample `48개` table entry에 scorer를 그대로 적용했다.
- prediction 분포: `list_skip 16`, `horizontalize 15`, `raw_fallback 12`, `history_skip 5`
- sample topic은 `10-Q::partIItem1FinancialStatements 6`, `10-Q::partIIItem6Exhibits 6`, `10-Q::partIIItem2UnregisteredSalesAndUseOfProceeds 6`가 상위였다.
- drift flag는 샘플에서 유의미하게 잡히지 않았다.
- 실행 시간: 약 `146.4초`

결론:
- DART-first scorer의 구조 피처 일부는 EDGAR에도 전이된다.
- 다만 topic prior가 없으니 list/raw 쪽으로 보수적으로 쏠린다.
- EDGAR는 "그대로도 조금 통한다" 수준이며, 실제 공통 엔진으로 가려면 EDGAR 전용 topic prior나 header noise 대응이 추가로 필요하다.

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import re
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

import polars as pl

from dartlab.providers.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _headerCells,
    _isJunk,
    splitSubtables,
)
from dartlab.providers.edgar.docs.sections.pipeline import sections as edgar_sections

ROOT = Path(__file__).resolve().parent
EDGAR_SAMPLE = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA"]


def load_script(stem: str):
    path = ROOT / f"{stem}.py"
    module_name = f"_exp074_{stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_scorer = load_script("006_understandingScorer")


def period_sort_key(value: str) -> tuple[int, int]:
    year = int(value[:4])
    match = re.search(r"Q(\d)", value)
    quarter = int(match.group(1)) if match else 4
    return year, quarter


def period_columns(df: pl.DataFrame) -> list[str]:
    cols = [col for col in df.columns if len(col) >= 4 and col[:4].isdigit()]
    return sorted(cols, key=period_sort_key, reverse=True)


@lru_cache(maxsize=None)
def topic_frame(ticker: str, topic: str) -> pl.DataFrame | None:
    df = edgar_sections(ticker)
    if df is None or df.is_empty():
        return None
    frame = df.filter((pl.col("topic") == topic) & (pl.col("blockType") == "table"))
    return frame if not frame.is_empty() else None


def latest_markdown(row: dict[str, object], period_cols: list[str]) -> tuple[str | None, str | None]:
    for period in period_cols:
        value = row.get(period)
        if isinstance(value, str) and "|" in value:
            return period, value
    return None, None


def approx_row_count(md: str) -> int:
    return sum(len(_dataRows(sub)) for sub in splitSubtables(md))


def numeric_ratio(md: str) -> float:
    data_cells = [cell.strip() for sub in splitSubtables(md) for row in _dataRows(sub) for cell in row if cell.strip()]
    if not data_cells:
        return 0.0
    numeric = sum(1 for cell in data_cells if re.search(r"-?[\d,]+(?:\.\d+)?", cell))
    return round(numeric / len(data_cells), 4)


def dominant_structure(md: str) -> str:
    counts: Counter[str] = Counter()
    for sub in splitSubtables(md):
        hc = _headerCells(sub)
        if not hc or _isJunk(hc):
            continue
        counts[_classifyStructure(hc)] += 1
    return counts.most_common(1)[0][0] if counts else "skip"


def collect_edgar_entries() -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for ticker in EDGAR_SAMPLE:
        df = edgar_sections(ticker)
        if df is None or df.is_empty():
            continue
        period_cols = period_columns(df)
        table = df.filter(pl.col("blockType") == "table")
        ranked = []
        for row in table.iter_rows(named=True):
            latest_period, md = latest_markdown(row, period_cols)
            if not md:
                continue
            period_count = sum(1 for col in period_cols if isinstance(row.get(col), str) and "|" in str(row.get(col)))
            ranked.append(
                {
                    "stockCode": ticker,
                    "topic": str(row["topic"]),
                    "blockOrder": int(row["blockOrder"]),
                    "latestPeriod": latest_period,
                    "latestMarkdown": md,
                    "periodCount": period_count,
                    "approxRowCount": approx_row_count(md),
                    "numericRatio": numeric_ratio(md),
                    "dominantStruct": dominant_structure(md),
                }
            )
        ranked.sort(key=lambda value: (-int(value["periodCount"]), -int(value["approxRowCount"]), str(value["topic"])))
        entries.extend(ranked[:8])
    return entries


def evaluate_transfer() -> dict[str, object]:
    entries = collect_edgar_entries()
    predictions: Counter[str] = Counter()
    drift_flags: Counter[str] = Counter()
    for entry in entries:
        decision = _scorer.score_entry(
            {
                **entry,
                "goldAction": "unknown",
                "goldKind": "unknown",
                "goldHeaderAxis": "unknown",
                "goldRowAlignment": "none",
                "reason": "edgar transfer sample",
            }
        )
        predictions[str(decision["predictedAction"])] += 1
        for flag in decision["driftFlags"]:
            drift_flags[str(flag)] += 1
    return {
        "entryCount": len(entries),
        "topics": Counter(str(entry["topic"]) for entry in entries).most_common(12),
        "predictions": predictions.most_common(),
        "driftFlags": drift_flags.most_common(),
    }


def main() -> None:
    print(evaluate_transfer())


if __name__ == "__main__":
    main()
