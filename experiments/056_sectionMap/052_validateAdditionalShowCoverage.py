"""Company.show() 추가 topic coverage 검증.

목표:
- docs 보유 전종목에서 다음 topic의 반환 계약을 점검한다.
  - costByNature: sections/detailTopic extractor 우선 + legacy fallback
  - tangibleAsset: legacy parser 유지

실행:
    ./.venv-wsl/bin/python -X utf8 experiments/056_sectionMap/052_validateAdditionalShowCoverage.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import polars as pl

import dartlab.engines.dart.company as dart_company
from dartlab.engines.dart.company import Company

DOCS_DIR = Path("data/dart/docs")
OUTPUT_DIR = Path("data/dart/docs/sectionsViews")
TOPICS = ["costByNature", "tangibleAsset"]
RESULTS_PATH = OUTPUT_DIR / "companyShowCoverage.additional.results.parquet"
FAILURES_PATH = OUTPUT_DIR / "companyShowCoverage.additional.failures.parquet"
SUMMARY_PATH = OUTPUT_DIR / "companyShowCoverage.additional.summary.parquet"
CHECKPOINT_EVERY = 10
STOCK_TIMEOUT_SECONDS = 150


def _local_only_ensure_data(stockCode: str, category: str) -> bool:
    return (Path("data/dart") / category / f"{stockCode}.parquet").exists()


dart_company._ensureData = _local_only_ensure_data


def stock_codes() -> list[str]:
    return sorted(path.stem for path in DOCS_DIR.glob("*.parquet"))


def _load_existing(path: Path) -> pl.DataFrame:
    if not path.exists():
        return pl.DataFrame()
    return pl.read_parquet(path)


def _processed_pairs(results: pl.DataFrame, failures: pl.DataFrame) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    if not results.is_empty():
        pairs.update(
            (str(row["stockCode"]), str(row["topic"]))
            for row in results.select(["stockCode", "topic"]).iter_rows(named=True)
        )
    if not failures.is_empty():
        pairs.update(
            (str(row["stockCode"]), str(row["topic"]))
            for row in failures.select(["stockCode", "topic"]).iter_rows(named=True)
        )
    return pairs


def summarize(results: pl.DataFrame, failures: pl.DataFrame) -> pl.DataFrame:
    if results.is_empty():
        return pl.DataFrame()

    failure_keys = set()
    if not failures.is_empty():
        failure_keys = {(row["stockCode"], row["topic"]) for row in failures.to_dicts()}

    with_status = results.with_columns(
        pl.struct(["stockCode", "topic"]).map_elements(
            lambda row: (row["stockCode"], row["topic"]) in failure_keys,
            return_dtype=pl.Boolean,
        ).alias("hasFailure")
    )

    return (
        with_status
        .group_by("topic")
        .agg(
            pl.len().alias("stocks"),
            pl.col("ok").sum().alias("dfCount"),
            pl.col("hasSubtopic").sum().alias("subtopicCount"),
            pl.col("isEmpty").sum().alias("emptyCount"),
            pl.col("hasFailure").sum().alias("failureCount"),
            pl.col("height").mean().round(2).alias("avgHeight"),
            pl.col("width").mean().round(2).alias("avgWidth"),
        )
        .sort("topic")
    )


def _run_stock_check(stock_code: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    child = f"""
import json
from pathlib import Path
import polars as pl
import dartlab.engines.dart.company as dart_company
from dartlab.engines.dart.company import Company

TOPICS = {TOPICS!r}
STOCK_CODE = {stock_code!r}

def _local_only_ensure_data(stockCode: str, category: str) -> bool:
    return (Path("data/dart") / category / f"{{stockCode}}.parquet").exists()

dart_company._ensureData = _local_only_ensure_data

rows = []
failures = []
try:
    company = Company(STOCK_CODE)
except Exception as exc:  # noqa: BLE001
    for topic in TOPICS:
        failures.append({{
            "stockCode": STOCK_CODE,
            "topic": topic,
            "stage": "init",
            "error": type(exc).__name__,
            "message": str(exc),
        }})
else:
    for topic in TOPICS:
        try:
            payload = company.show(topic)
            rows.append({{
                "stockCode": STOCK_CODE,
                "topic": topic,
                "ok": isinstance(payload, pl.DataFrame),
                "height": payload.height if isinstance(payload, pl.DataFrame) else None,
                "width": payload.width if isinstance(payload, pl.DataFrame) else None,
                "hasSubtopic": isinstance(payload, pl.DataFrame) and "subtopic" in payload.columns,
                "isEmpty": payload.is_empty() if isinstance(payload, pl.DataFrame) else None,
            }})
        except Exception as exc:  # noqa: BLE001
            failures.append({{
                "stockCode": STOCK_CODE,
                "topic": topic,
                "stage": "show",
                "error": type(exc).__name__,
                "message": str(exc),
            }})

print(json.dumps({{"rows": rows, "failures": failures}}, ensure_ascii=False))
"""
    try:
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", "-c", child],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=STOCK_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return (
            [],
            [
                {
                    "stockCode": stock_code,
                    "topic": topic,
                    "stage": "stock-timeout",
                    "error": "TimeoutExpired",
                    "message": "stock timeout",
                }
                for topic in TOPICS
            ],
        )

    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout or "subprocess failed").strip()
        return (
            [],
            [
                {
                    "stockCode": stock_code,
                    "topic": topic,
                    "stage": "subprocess",
                    "error": f"returncode={proc.returncode}",
                    "message": message[:500],
                }
                for topic in TOPICS
            ],
        )

    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        return (
            [],
            [
                {
                    "stockCode": stock_code,
                    "topic": topic,
                    "stage": "subprocess",
                    "error": "NoOutput",
                    "message": "subprocess produced no output",
                }
                for topic in TOPICS
            ],
        )

    try:
        payload = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        return (
            [],
            [
                {
                    "stockCode": stock_code,
                    "topic": topic,
                    "stage": "subprocess",
                    "error": type(exc).__name__,
                    "message": lines[-1][:500],
                }
                for topic in TOPICS
            ],
        )
    return payload.get("rows", []), payload.get("failures", [])


def _flush(results: pl.DataFrame, failures: pl.DataFrame) -> None:
    if not failures.is_empty() and not results.is_empty():
        success_pairs = results.select(["stockCode", "topic"]).unique()
        failures = failures.join(success_pairs, on=["stockCode", "topic"], how="anti")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results.write_parquet(RESULTS_PATH)
    failures.write_parquet(FAILURES_PATH)
    summarize(results, failures).write_parquet(SUMMARY_PATH)


def validate() -> tuple[pl.DataFrame, pl.DataFrame]:
    results = _load_existing(RESULTS_PATH)
    failures = _load_existing(FAILURES_PATH)
    processed = _processed_pairs(results, failures)

    rows: list[dict[str, object]] = []
    failure_rows: list[dict[str, object]] = []
    processed_stocks = 0

    for stock_code in stock_codes():
        pending_topics = [topic for topic in TOPICS if (stock_code, topic) not in processed]
        if not pending_topics:
            continue
        stock_rows, stock_failures = _run_stock_check(stock_code)
        for row in stock_rows:
            if (row["stockCode"], row["topic"]) not in processed:
                rows.append(row)
        for failure in stock_failures:
            if (failure["stockCode"], failure["topic"]) not in processed:
                failure_rows.append(failure)

        processed_stocks += 1
        if processed_stocks % CHECKPOINT_EVERY == 0:
            if rows:
                results = (
                    pl.concat([results, pl.DataFrame(rows)], how="diagonal_relaxed")
                    if not results.is_empty()
                    else pl.DataFrame(rows)
                )
                rows = []
            if failure_rows:
                new_failures = pl.DataFrame(failure_rows)
                failures = (
                    pl.concat([failures, new_failures], how="diagonal_relaxed")
                    if not failures.is_empty()
                    else new_failures
                )
                failures = failures.unique(
                    subset=["stockCode", "topic", "stage", "error", "message"],
                    keep="last",
                )
                failure_rows = []
            _flush(results, failures)
            print(f"[checkpoint] processed={processed_stocks}")

    if rows:
        results = (
            pl.concat([results, pl.DataFrame(rows)], how="diagonal_relaxed")
            if not results.is_empty()
            else pl.DataFrame(rows)
        )
    if failure_rows:
        new_failures = pl.DataFrame(failure_rows)
        failures = (
            pl.concat([failures, new_failures], how="diagonal_relaxed")
            if not failures.is_empty()
            else new_failures
        )
        failures = failures.unique(
            subset=["stockCode", "topic", "stage", "error", "message"],
            keep="last",
        )

    return results, failures


def main() -> None:
    results, failures = validate()
    summary = summarize(results, failures)

    print("\n[company.show additional coverage summary]")
    print(summary)
    if not failures.is_empty():
        print("\n[failures]")
        print(failures)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results.write_parquet(RESULTS_PATH)
    failures.write_parquet(FAILURES_PATH)
    summary.write_parquet(SUMMARY_PATH)


if __name__ == "__main__":
    main()
