"""
실험 ID: 074-013
실험명: 전종목 scorer vs baseline disagreement mining

목적:
- 현행 scorer(006)와 baseline(005)이 서로 다른 판단을 내리는 table block을 전수 수집한다.
- 오분류 패턴(어떤 topic/구조/피처 조합에서 불일치가 많은지)을 정량화한다.
- 다음 단계(014 gold set 확대)에서 사람이 봐야 할 후보를 체계적으로 뽑는다.

가설:
1. 전종목 319개에서 scorer-baseline 불일치 비율은 20~40%일 것이다.
2. 불일치가 집중되는 topic/구조 조합이 있고, 그것이 hard-case의 핵심이다.
3. scorer가 horizontalize로 보내지만 baseline이 실패(None)하는 케이스가 가장 많을 것이다.

방법:
1. DART 전종목 docs parquet를 순회하며 sections를 생성한다.
2. 각 table block에 대해 scorer action과 baseline action을 동시에 계산한다.
3. 두 판단이 다른 케이스를 수집하고, topic/구조/피처별 불일치 분포를 집계한다.

결과 (실험 후 작성):
- 전종목 `319개`, table block `269,812개`, disagreement `161,961건 (60.0%)`
- scorer 분포: `raw_fallback 153,217` / `horizontalize 60,165` / `history_skip 23,642` / `list_skip 23,499` / `retry_alt_header 9,289`
- baseline 분포: `horizontalize 164,906` / `raw_fallback 74,183` / `list_skip 22,022` / `history_skip 5,341` / `retry_alt_header 3,360`
- 최대 불일치 pair: `(scorer=raw_fallback, baseline=horizontalize) 87,737건` — scorer가 raw로 보수적으로 보내지만 baseline은 수평화 성공
- 불일치 집중 topic: `fsSummary 50,291` / `financialNotes 30,462` / `consolidatedNotes 19,807` / `companyOverview 9,024` / `boardOfDirectors 7,698`
- 구조별 불일치: `skip 88,201` / `matrix 43,350` / `key_value 19,558` / `multi_year 10,852`
- low-confidence disagreement (<0.1): `32,380건`
- 에러 `0건`, 실행 시간 `1,763.2초`

결론:
- 가설 1 기각: 불일치 비율은 20~40%가 아니라 **60%**로 훨씬 높았다.
- 가설 2 채택: fsSummary/financialNotes/consolidatedNotes 3개 topic이 불일치의 62%를 차지한다.
- 가설 3 기각: scorer→horizontalize / baseline→None이 아니라, **scorer→raw_fallback / baseline→horizontalize**가 압도적 (87,737건).
  즉 scorer가 주석/재무요약 topic을 일괄 raw로 밀어버리는 topic prior가 과도하게 보수적이다.
- baseline은 실제 horizontalizer 성공률이 높지만 세부 action taxonomy가 없고, scorer는 taxonomy는 있지만 raw_fallback에 과다 쏠려 있다.
- 다음 단계: 이 87k건 중 대표 사례를 뽑아 "baseline이 진짜 맞는지 / scorer가 맞는지" manual gold로 판정해야 한다.

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter

import polars as pl

from dartlab import config
from dartlab.engines.dart._table_horizontalizer import horizontalizeTableBlock
from dartlab.engines.dart.docs.sections.pipeline import sections
from dartlab.engines.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _headerCells,
    _isJunk,
    splitSubtables,
)

ROOT = Path(__file__).resolve().parent


def load_script(stem: str):
    path = ROOT / f"{stem}.py"
    module_name = f"_exp074_{stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_seed = load_script("002_seedGoldSet")
_scorer = load_script("006_understandingScorer")


def period_columns(df: pl.DataFrame) -> list[str]:
    cols = [col for col in df.columns if len(col) >= 4 and col[:4].isdigit()]

    def sort_key(c: str) -> tuple[int, int]:
        year = int(c[:4])
        m = re.search(r"Q(\d)", c)
        return (year, int(m.group(1)) if m else 4)

    return sorted(cols, key=sort_key, reverse=True)


def numeric_ratio(md: str) -> float:
    data_cells: list[str] = []
    for sub in splitSubtables(md):
        for row in _dataRows(sub):
            data_cells.extend(cell.strip() for cell in row if cell.strip())
    if not data_cells:
        return 0.0
    numeric = sum(1 for cell in data_cells if re.search(r"-?[\d,]+(?:\.\d+)?", cell))
    return round(numeric / len(data_cells), 4)


def approx_row_count(md: str) -> int:
    return sum(len(_dataRows(sub)) for sub in splitSubtables(md))


def dominant_structure(md: str) -> str:
    counts: Counter[str] = Counter()
    for sub in splitSubtables(md):
        hc = _headerCells(sub)
        if not hc or _isJunk(hc):
            continue
        counts[_classifyStructure(hc)] += 1
    return counts.most_common(1)[0][0] if counts else "skip"


def latest_markdown(row: dict[str, object], period_cols: list[str]) -> tuple[str | None, str | None]:
    for period in period_cols:
        value = row.get(period)
        if isinstance(value, str) and "|" in value:
            return period, value
    return None, None


def classify_baseline(entry: dict[str, object], frame: pl.DataFrame, pcols: list[str]) -> str:
    """baseline: horizontalizer 성공이면 horizontalize, 실패면 heuristic fallback."""
    result = horizontalizeTableBlock(frame, int(entry["blockOrder"]), pcols, None)
    if result is not None:
        return "horizontalize"
    topic = str(entry["topic"])
    arc = int(entry["approxRowCount"])
    if topic in {"employee", "companyOverview"} or arc >= 25:
        return "list_skip"
    if topic in {"boardOfDirectors", "companyHistory"}:
        return "history_skip"
    if topic in {"audit", "executivePay"}:
        return "retry_alt_header"
    return "raw_fallback"


def mine_disagreements() -> dict[str, object]:
    data_dir = Path(config.dataDir)
    dart_ids = sorted(p.stem for p in (data_dir / "dart" / "docs").glob("*.parquet"))

    total_blocks = 0
    disagreements: list[dict[str, object]] = []
    scorer_dist: Counter[str] = Counter()
    baseline_dist: Counter[str] = Counter()
    topic_disagree: Counter[str] = Counter()
    struct_disagree: Counter[str] = Counter()
    pair_disagree: Counter[tuple[str, str]] = Counter()
    errors = 0
    start = perf_counter()

    for stock_code in dart_ids:
        try:
            df = sections(stock_code)
        except Exception:
            errors += 1
            continue
        if df is None or df.is_empty():
            continue
        if "blockType" not in df.columns:
            continue
        table_df = df.filter(pl.col("blockType") == "table")
        if table_df.is_empty():
            continue
        pcols = period_columns(table_df)
        if not pcols:
            continue

        for row in table_df.iter_rows(named=True):
            topic = str(row["topic"])
            block_order = int(row["blockOrder"])
            lp, md = latest_markdown(row, pcols)
            if not md:
                continue
            total_blocks += 1

            entry = {
                "stockCode": stock_code,
                "topic": topic,
                "blockOrder": block_order,
                "latestPeriod": lp,
                "latestMarkdown": md,
                "approxRowCount": approx_row_count(md),
                "numericRatio": numeric_ratio(md),
                "dominantStruct": dominant_structure(md),
                "periodCount": sum(
                    1
                    for col in pcols
                    if isinstance(row.get(col), str) and "|" in str(row.get(col))
                ),
            }

            # scorer action
            scorer_result = _scorer.score_entry(entry)
            scorer_action = str(scorer_result["predictedAction"])
            scorer_confidence = float(scorer_result["confidence"])

            # baseline action
            baseline_action = classify_baseline(entry, table_df, pcols)

            scorer_dist[scorer_action] += 1
            baseline_dist[baseline_action] += 1

            if scorer_action != baseline_action:
                topic_disagree[topic] += 1
                struct_disagree[str(entry["dominantStruct"])] += 1
                pair_disagree[(scorer_action, baseline_action)] += 1
                disagreements.append(
                    {
                        "stockCode": stock_code,
                        "topic": topic,
                        "blockOrder": block_order,
                        "dominantStruct": str(entry["dominantStruct"]),
                        "approxRowCount": int(entry["approxRowCount"]),
                        "numericRatio": float(entry["numericRatio"]),
                        "periodCount": int(entry["periodCount"]),
                        "scorerAction": scorer_action,
                        "scorerConfidence": scorer_confidence,
                        "baselineAction": baseline_action,
                    }
                )

    elapsed = perf_counter() - start
    disagree_rate = round(len(disagreements) / total_blocks, 4) if total_blocks else 0.0

    return {
        "totalStocks": len(dart_ids),
        "totalBlocks": total_blocks,
        "disagreements": len(disagreements),
        "disagreeRate": disagree_rate,
        "errors": errors,
        "elapsed": round(elapsed, 1),
        "scorerDist": scorer_dist.most_common(),
        "baselineDist": baseline_dist.most_common(),
        "topicDisagree": topic_disagree.most_common(15),
        "structDisagree": struct_disagree.most_common(),
        "pairDisagree": pair_disagree.most_common(10),
        "lowConfDisagreeCount": sum(
            1 for d in disagreements if d["scorerConfidence"] < 0.1
        ),
        "sampleDisagreements": disagreements[:30],
    }


def main() -> None:
    result = mine_disagreements()
    print(f"\n=== 074-013 disagreement mining ===")
    print(f"stocks: {result['totalStocks']}, blocks: {result['totalBlocks']}, "
          f"disagree: {result['disagreements']} ({result['disagreeRate']:.1%}), "
          f"errors: {result['errors']}, elapsed: {result['elapsed']}s")
    print(f"\nscorer dist: {result['scorerDist']}")
    print(f"baseline dist: {result['baselineDist']}")
    print(f"\ntop topic disagree: {result['topicDisagree']}")
    print(f"struct disagree: {result['structDisagree']}")
    print(f"pair disagree (scorer, baseline): {result['pairDisagree']}")
    print(f"low-conf disagree (<0.1): {result['lowConfDisagreeCount']}")
    print(f"\nsample disagreements (first 10):")
    for d in result["sampleDisagreements"][:10]:
        print(f"  {d['stockCode']}:{d['topic']}:bo{d['blockOrder']} "
              f"struct={d['dominantStruct']} rows={d['approxRowCount']} "
              f"scorer={d['scorerAction']}({d['scorerConfidence']:.2f}) "
              f"baseline={d['baselineAction']}")


if __name__ == "__main__":
    main()
