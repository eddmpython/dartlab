"""
실험 ID: 074-002
실험명: topic prior 기반 seed gold set 구성

목적:
- 완전 수작업 gold set 전에, sections-aware table understanding 실험을 반복할 수 있는 seed review set을 만든다.
- 실제 로컬 table block 위에서 action prior와 구조 피처를 함께 고정한다.

가설:
1. topic prior만으로도 `horizontalize / raw_fallback / history_skip / list_skip / retry_alt_header` seed set을 만들 수 있다.
2. DART 대표 topic만 뽑아도 action 분포가 한쪽으로 심하게 쏠리지 않는다.
3. seed set은 baseline과 scorer를 비교하는 초기 검증용으로 충분하다.

방법:
1. 001의 DART sample company를 불러온다.
2. 지정한 topic prior에 해당하는 table row를 스캔한다.
3. topic별로 periodCount, latest markdown, dominant structure, rowCount를 계산해 seed label을 붙인다.

결과 (실험 후 작성):
- seed set `60개`를 구성했다. topic당 `4개`씩, 총 `15개 topic`을 포함한다.
- action 분포: `horizontalize 24`, `raw_fallback 12`, `retry_alt_header 8`, `history_skip 8`, `list_skip 8`
- dominant struct 분포: `matrix 28`, `skip 17`, `multi_year 9`, `key_value 6`
- median periodCount `41.0`, median rowCount `14.0`
- 실행 시간: 약 `148.2초`

결론:
- 완전 수작업 gold set은 아니지만, topic prior와 실제 block 피처를 결합한 seed review set으로는 충분하다.
- action 분포가 한쪽으로 무너지지 않아 baseline/scorer 비교용 초기 좌표계로 쓸 수 있다.
- 다음 단계에서 사람이 더 봐야 하는 건 `retry_alt_header`와 `raw_fallback` 경계 사례다.

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import re
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import polars as pl

from dartlab.engines.company.dart.docs.sections.pipeline import sections
from dartlab.engines.company.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _headerCells,
    _isJunk,
    splitSubtables,
)

ROOT = Path(__file__).resolve().parent

TOPIC_PRIORS: dict[str, tuple[str, str, str]] = {
    "dividend": ("horizontalize", "comparative", "기간 비교형 배당 테이블"),
    "rawMaterial": ("horizontalize", "comparative", "원재료 가격/조달 구조 비교형"),
    "salesOrder": ("horizontalize", "comparative", "수주잔고/매출 구조 비교형"),
    "shareCapital": ("horizontalize", "snapshot", "자본 구조 현황형"),
    "majorHolder": ("horizontalize", "snapshot", "대주주 현황형"),
    "riskDerivative": ("horizontalize", "comparative", "파생상품 리스크 비교형"),
    "audit": ("retry_alt_header", "snapshot", "감사 표는 헤더 변형이 잦음"),
    "executivePay": ("retry_alt_header", "snapshot", "임원보수 표는 다중행 헤더가 잦음"),
    "employee": ("list_skip", "list", "직원/임원 목록형으로 길어지는 경우가 많음"),
    "companyOverview": ("list_skip", "list", "회사개요 하위 표는 목록형 폭발이 잦음"),
    "boardOfDirectors": ("history_skip", "history", "이사회/인물 테이블은 이력형 변화가 큼"),
    "companyHistory": ("history_skip", "history", "연혁 테이블은 항목 drift가 큼"),
    "financialNotes": ("raw_fallback", "complex_note", "주석은 구조가 복잡해 raw 보존이 안전"),
    "consolidatedNotes": ("raw_fallback", "complex_note", "연결 주석은 구조가 복잡해 raw 보존이 안전"),
    "fsSummary": ("raw_fallback", "complex_note", "재무요약은 mixed structure 비중이 큼"),
}


def load_script(stem: str):
    path = ROOT / f"{stem}.py"
    module_name = f"_exp074_{stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_snapshot = load_script("001_corpusSnapshot")


def period_sort_key(value: str) -> tuple[int, int]:
    year = int(value[:4])
    match = re.search(r"Q(\d)", value)
    quarter = int(match.group(1)) if match else 4
    return year, quarter


def period_columns(df: pl.DataFrame) -> list[str]:
    cols = [col for col in df.columns if len(col) >= 4 and col[:4].isdigit()]
    return sorted(cols, key=period_sort_key, reverse=True)


def latest_markdown(row: dict[str, object], period_cols: list[str]) -> tuple[str | None, str | None]:
    for period in period_cols:
        value = row.get(period)
        if isinstance(value, str) and "|" in value:
            return period, value
    return None, None


def numeric_ratio(md: str) -> float:
    data_cells: list[str] = []
    for sub in splitSubtables(md):
        for row in _dataRows(sub):
            data_cells.extend(cell.strip() for cell in row if cell.strip())
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


def approx_row_count(md: str) -> int:
    return sum(len(_dataRows(sub)) for sub in splitSubtables(md))


@lru_cache(maxsize=None)
def topic_frame(stock_code: str, topic: str) -> pl.DataFrame | None:
    df = sections(stock_code)
    if df is None or df.is_empty():
        return None
    frame = df.filter((pl.col("topic") == topic) & (pl.col("blockType") == "table"))
    return frame if not frame.is_empty() else None


@lru_cache(maxsize=1)
def collect_sample_topic_rows() -> list[dict[str, object]]:
    snapshot = _snapshot.build_snapshot()
    sample_codes = snapshot["dartSample"]["ids"]
    rows: list[dict[str, object]] = []
    for stock_code in sample_codes:
        df = sections(stock_code)
        if df is None or df.is_empty():
            continue
        period_cols = period_columns(df)
        table = df.filter(pl.col("blockType") == "table")
        if table.is_empty():
            continue
        for row in table.iter_rows(named=True):
            topic = str(row["topic"])
            if topic not in TOPIC_PRIORS:
                continue
            latest_period, md = latest_markdown(row, period_cols)
            if not md:
                continue
            action, kind, reason = TOPIC_PRIORS[topic]
            rows.append(
                {
                    "stockCode": stock_code,
                    "topic": topic,
                    "blockOrder": int(row["blockOrder"]),
                    "bundleId": f"{stock_code}:{topic}:bo{int(row['blockOrder'])}",
                    "periodCount": sum(1 for col in period_cols if isinstance(row.get(col), str) and "|" in str(row.get(col))),
                    "latestPeriod": latest_period,
                    "latestMarkdown": md,
                    "approxRowCount": approx_row_count(md),
                    "numericRatio": numeric_ratio(md),
                    "dominantStruct": dominant_structure(md),
                    "goldAction": action,
                    "goldKind": kind,
                    "goldHeaderAxis": "period" if kind == "comparative" else ("mixed" if action == "raw_fallback" else "entity"),
                    "goldRowAlignment": "row_core" if action == "horizontalize" else "none",
                    "reason": reason,
                }
            )
    return rows


@lru_cache(maxsize=None)
def build_seed_gold_set(limit_per_topic: int = 4) -> list[dict[str, object]]:
    picked: list[dict[str, object]] = []
    per_topic: dict[str, int] = defaultdict(int)
    candidates = sorted(
        collect_sample_topic_rows(),
        key=lambda row: (
            row["topic"],
            -int(row["periodCount"]),
            -int(row["approxRowCount"]),
            row["stockCode"],
            int(row["blockOrder"]),
        ),
    )
    for row in candidates:
        topic = str(row["topic"])
        if per_topic[topic] >= limit_per_topic:
            continue
        picked.append(row)
        per_topic[topic] += 1
    return picked


def summarize_seed_set(limit_per_topic: int = 4) -> dict[str, object]:
    seed = build_seed_gold_set(limit_per_topic=limit_per_topic)
    return {
        "count": len(seed),
        "topics": Counter(str(row["topic"]) for row in seed).most_common(),
        "actions": Counter(str(row["goldAction"]) for row in seed).most_common(),
        "structs": Counter(str(row["dominantStruct"]) for row in seed).most_common(),
        "medianPeriodCount": float(pl.Series([int(row["periodCount"]) for row in seed]).median()) if seed else 0.0,
        "medianRowCount": float(pl.Series([int(row["approxRowCount"]) for row in seed]).median()) if seed else 0.0,
    }


def main() -> None:
    print(summarize_seed_set())


if __name__ == "__main__":
    main()
