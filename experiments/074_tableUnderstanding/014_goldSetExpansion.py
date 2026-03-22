"""
실험 ID: 074-014
실험명: disagreement 기반 manual gold set 100개 구성

목적:
- 013의 전종목 disagreement에서 대표적인 경계 사례 100개를 체계적으로 뽑는다.
- 각 케이스에 대해 실제 markdown을 보고 올바른 action을 판정한다.
- 판정 기준: "이 표를 수평화하면 사용자에게 의미 있는 항목×기간 매트릭스가 나오는가?"

가설:
1. (raw_fallback, horizontalize) 87k건 중 상당수는 baseline이 수평화에 "성공"하지만
   결과 품질이 낮은 케이스(주석 표, 복잡 구조)일 것이다.
2. low-confidence disagreement에서 진짜 경계 사례가 집중될 것이다.
3. 100개 gold set이면 scorer v2 개선 방향이 확정될 것이다.

방법:
1. 013의 disagreement를 pair/topic/struct별로 층화 샘플링한다.
2. 각 사례의 실제 latest markdown을 수집하고, baseline 수평화 결과도 함께 확인한다.
3. 자동 판정 규칙:
   - baseline 수평화 성공 + 결과 fill_rate >= 0.5 + 항목 수 3~50 → "horizontalize"
   - baseline 수평화 성공이지만 fill_rate < 0.3 또는 항목 수 > 50 → "raw_fallback" or "list_skip"
   - baseline 실패 + numeric_ratio >= 0.4 + structureType == multi_year → "retry_alt_header"
   - baseline 실패 + row overlap < 0.2 across periods → "history_skip"
   - 나머지 → "raw_fallback"
4. 자동 판정 후, 확신 낮은 사례만 수동 검토 대상으로 플래그한다.

결과 (실험 후 작성):
- (실행 후 채움)

결론:
- (실행 후 채움)

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

# scorer를 인라인 — bundle/TableIR 메모리 비용 회피
ACTION_ORDER = ["horizontalize", "retry_alt_header", "list_skip", "history_skip", "raw_fallback"]


def score_entry_lite(entry: dict[str, object]) -> dict[str, object]:
    """006 scorer의 경량 인라인 버전. bundle/IR 없이 topic+struct+feature만 사용."""
    scores: dict[str, float] = defaultdict(float)
    topic = str(entry["topic"])
    arc = int(entry["approxRowCount"])
    nr = float(entry["numericRatio"])
    ds = str(entry["dominantStruct"])

    # topic prior (006과 동일)
    if topic in {"dividend", "rawMaterial", "salesOrder", "shareCapital", "majorHolder", "riskDerivative"}:
        scores["horizontalize"] += 0.55
    if topic in {"audit", "executivePay"}:
        scores["retry_alt_header"] += 0.45
    if topic in {"employee", "companyOverview"}:
        scores["list_skip"] += 0.45
    if topic in {"boardOfDirectors", "companyHistory"}:
        scores["history_skip"] += 0.45
    if topic in {"financialNotes", "consolidatedNotes", "fsSummary"}:
        scores["raw_fallback"] += 0.55

    # structure features (006과 동일, bundle 의존부 제외)
    if ds == "multi_year":
        scores["horizontalize"] += 0.3
    if ds in {"key_value", "matrix"}:
        scores["horizontalize"] += 0.1
        scores["retry_alt_header"] += 0.05
    if nr >= 0.45:
        scores["horizontalize"] += 0.2
    if arc >= 30:
        scores["list_skip"] += 0.3
    if arc >= 50:
        scores["list_skip"] += 0.2
    if not any(scores.values()):
        scores["raw_fallback"] += 0.1

    ordered = sorted(
        ((a, scores[a]) for a in ACTION_ORDER),
        key=lambda x: x[1], reverse=True,
    )
    best, second = ordered[0], ordered[1]
    confidence = round(best[1] - second[1], 4)
    return {"predictedAction": best[0], "confidence": confidence}

# -------------------------------------------------------------------
# disagreement pair별 샘플링 quota (총 100)
# -------------------------------------------------------------------
PAIR_QUOTA: dict[tuple[str, str], int] = {
    ("raw_fallback", "horizontalize"): 35,   # 87k — 가장 큰 불일치
    ("horizontalize", "raw_fallback"): 15,   # 18k — 반대 방향
    ("list_skip", "horizontalize"): 15,      # 16k
    ("history_skip", "horizontalize"): 15,   # 15k
    ("retry_alt_header", "horizontalize"): 10,  # 6k
    ("raw_fallback", "list_skip"): 5,        # 12k
    ("history_skip", "raw_fallback"): 5,     # 2.8k
}

# topic 다양성을 위한 topic당 최대
MAX_PER_TOPIC = 8


def period_columns(df: pl.DataFrame) -> list[str]:
    cols = [col for col in df.columns if len(col) >= 4 and col[:4].isdigit()]

    def sort_key(c: str) -> tuple[int, int]:
        year = int(c[:4])
        m = re.search(r"Q(\d)", c)
        return (year, int(m.group(1)) if m else 4)

    return sorted(cols, key=sort_key, reverse=True)


def latest_markdown(row: dict[str, object], pcols: list[str]) -> tuple[str | None, str | None]:
    for p in pcols:
        v = row.get(p)
        if isinstance(v, str) and "|" in v:
            return p, v
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


def classify_baseline(entry: dict[str, object], frame: pl.DataFrame, pcols: list[str]) -> tuple[str, pl.DataFrame | None]:
    result = horizontalizeTableBlock(frame, int(entry["blockOrder"]), pcols, None)
    if result is not None:
        return "horizontalize", result
    topic = str(entry["topic"])
    arc = int(entry["approxRowCount"])
    if topic in {"employee", "companyOverview"} or arc >= 25:
        return "list_skip", None
    if topic in {"boardOfDirectors", "companyHistory"}:
        return "history_skip", None
    if topic in {"audit", "executivePay"}:
        return "retry_alt_header", None
    return "raw_fallback", None


def judge_gold_action(
    entry: dict[str, object],
    baseline_action: str,
    baseline_result: pl.DataFrame | None,
    pcols: list[str],
) -> tuple[str, str, float]:
    """자동 판정 + 확신도. 반환: (goldAction, reason, confidence)"""
    topic = str(entry["topic"])
    arc = int(entry["approxRowCount"])
    nr = float(entry["numericRatio"])
    ds = str(entry["dominantStruct"])
    pc = int(entry["periodCount"])

    # Case 1: baseline 수평화 성공 — 결과 품질 판정
    if baseline_result is not None:
        item_count = baseline_result.height
        pcols_result = [c for c in baseline_result.columns if c != "항목"]
        if pcols_result:
            non_null = sum(
                1
                for c in pcols_result
                for v in baseline_result[c].to_list()
                if v is not None and str(v).strip()
            )
            total = item_count * len(pcols_result)
            fill_rate = non_null / total if total else 0.0
        else:
            fill_rate = 0.0

        # 수평화 성공 + 양호한 품질
        if item_count <= 50 and item_count >= 2 and fill_rate >= 0.4:
            return "horizontalize", f"baseline_ok items={item_count} fill={fill_rate:.2f}", 0.85
        # 수평화 성공이지만 너무 많은 항목 → list
        if item_count > 50:
            return "list_skip", f"baseline_ok_but_too_many items={item_count}", 0.75
        # 수평화 성공이지만 너무 sparse
        if fill_rate < 0.3 and item_count > 5:
            return "raw_fallback", f"baseline_ok_but_sparse fill={fill_rate:.2f}", 0.60
        # 항목이 1개뿐
        if item_count <= 1:
            return "raw_fallback", f"baseline_ok_but_trivial items={item_count}", 0.70
        # 그 외 성공 케이스
        return "horizontalize", f"baseline_ok items={item_count} fill={fill_rate:.2f}", 0.70

    # Case 2: baseline 실패 — 구조 기반 판정
    # 높은 숫자 비율 + multi_year 구조 → retry
    if nr >= 0.4 and ds == "multi_year":
        return "retry_alt_header", f"numeric_high nr={nr} struct={ds}", 0.70

    # 높은 숫자 비율 + matrix/key_value → 수평화 시도할 만함
    if nr >= 0.5 and ds in {"matrix", "key_value"} and arc <= 30:
        return "horizontalize", f"numeric_high_structure nr={nr} struct={ds} rows={arc}", 0.55

    # 많은 행 → list
    if arc > 50:
        return "list_skip", f"too_many_rows rows={arc}", 0.80

    # 행 drift가 심한 topic
    if topic in {"boardOfDirectors", "companyHistory"} and pc >= 3:
        return "history_skip", f"history_topic topic={topic} periods={pc}", 0.75

    # 복잡 주석 topic
    if topic in {"financialNotes", "consolidatedNotes"} and ds in {"skip", "matrix"}:
        return "raw_fallback", f"complex_notes topic={topic} struct={ds}", 0.80

    # 기본 fallback
    if arc <= 3 and nr < 0.2:
        return "raw_fallback", f"small_non_numeric rows={arc} nr={nr}", 0.65

    return "raw_fallback", f"default_fallback", 0.40


def build_gold_set() -> dict[str, object]:
    import gc

    data_dir = Path(config.dataDir)
    dart_ids = sorted(p.stem for p in (data_dir / "dart" / "docs").glob("*.parquet"))

    # 수집 버킷
    buckets: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    topic_counts: Counter[str] = Counter()
    start = perf_counter()
    errors = 0
    scanned = 0

    for stock_code in dart_ids:
        # 조기 종료: 모든 quota 채워졌으면
        if all(len(buckets[p]) >= q for p, q in PAIR_QUOTA.items()):
            break

        try:
            df = sections(stock_code)
        except Exception:
            errors += 1
            continue
        if df is None or df.is_empty() or "blockType" not in df.columns:
            del df
            continue
        table_df = df.filter(pl.col("blockType") == "table")
        del df  # 큰 DataFrame 즉시 해제
        if table_df.is_empty():
            del table_df
            continue
        pcols = period_columns(table_df)
        if not pcols:
            del table_df
            continue

        scanned += 1
        for row in table_df.iter_rows(named=True):
            # 이미 모든 quota 찼으면 내부 루프도 탈출
            if all(len(buckets[p]) >= q for p, q in PAIR_QUOTA.items()):
                break

            topic = str(row["topic"])
            block_order = int(row["blockOrder"])
            lp, md = latest_markdown(row, pcols)
            if not md:
                continue

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
                    1 for c in pcols
                    if isinstance(row.get(c), str) and "|" in str(row.get(c))
                ),
            }

            scorer_result = _scorer.score_entry(entry)
            scorer_action = str(scorer_result["predictedAction"])
            scorer_confidence = float(scorer_result["confidence"])

            baseline_action, baseline_df = classify_baseline(entry, table_df, pcols)

            if scorer_action == baseline_action:
                del baseline_df
                continue

            pair = (scorer_action, baseline_action)
            quota = PAIR_QUOTA.get(pair)
            if quota is None:
                del baseline_df
                continue
            if len(buckets[pair]) >= quota:
                del baseline_df
                continue
            if topic_counts[topic] >= MAX_PER_TOPIC:
                del baseline_df
                continue

            gold_action, reason, confidence = judge_gold_action(
                entry, baseline_action, baseline_df, pcols
            )
            del baseline_df

            candidate = {
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
                "goldAction": gold_action,
                "goldReason": reason,
                "goldConfidence": confidence,
                "needsReview": confidence < 0.65,
            }
            buckets[pair].append(candidate)
            topic_counts[topic] += 1

        del table_df
        # 매 20종목마다 GC
        if scanned % 20 == 0:
            gc.collect()

    elapsed = perf_counter() - start

    gold_set = []
    for pair, items in buckets.items():
        gold_set.extend(items)

    action_dist = Counter(g["goldAction"] for g in gold_set)
    review_count = sum(1 for g in gold_set if g["needsReview"])

    # scorer/baseline/gold 일치 분석
    scorer_correct = sum(1 for g in gold_set if g["scorerAction"] == g["goldAction"])
    baseline_correct = sum(1 for g in gold_set if g["baselineAction"] == g["goldAction"])

    return {
        "totalGold": len(gold_set),
        "elapsed": round(elapsed, 1),
        "errors": errors,
        "pairCounts": {f"{p[0]}->{p[1]}": len(items) for p, items in buckets.items()},
        "goldActionDist": action_dist.most_common(),
        "topicDist": Counter(g["topic"] for g in gold_set).most_common(15),
        "structDist": Counter(g["dominantStruct"] for g in gold_set).most_common(),
        "needsReview": review_count,
        "scorerAccuracy": round(scorer_correct / len(gold_set), 4) if gold_set else 0.0,
        "baselineAccuracy": round(baseline_correct / len(gold_set), 4) if gold_set else 0.0,
        "goldSet": gold_set,
    }


def main() -> None:
    result = build_gold_set()
    print(f"\n=== 074-014 gold set expansion ===")
    print(f"total gold: {result['totalGold']}, elapsed: {result['elapsed']}s, errors: {result['errors']}")
    print(f"\npair counts: {result['pairCounts']}")
    print(f"gold action dist: {result['goldActionDist']}")
    print(f"topic dist (top 15): {result['topicDist']}")
    print(f"struct dist: {result['structDist']}")
    print(f"needs review: {result['needsReview']}")
    print(f"\nscorer accuracy on gold: {result['scorerAccuracy']}")
    print(f"baseline accuracy on gold: {result['baselineAccuracy']}")
    print(f"\nsample gold entries:")
    for g in result["goldSet"][:15]:
        review = " [REVIEW]" if g["needsReview"] else ""
        print(f"  {g['stockCode']}:{g['topic']}:bo{g['blockOrder']} "
              f"struct={g['dominantStruct']} rows={g['approxRowCount']} "
              f"scorer={g['scorerAction']} baseline={g['baselineAction']} "
              f"gold={g['goldAction']} conf={g['goldConfidence']:.2f} "
              f"reason={g['goldReason']}{review}")


if __name__ == "__main__":
    main()
