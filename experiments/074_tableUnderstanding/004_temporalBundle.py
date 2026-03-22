"""
실험 ID: 074-004
실험명: blockOrder drift를 넘는 temporal table bundle 구성

목적:
- 같은 stock/topic 안에서 blockOrder가 달라도 같은 논리 표를 묶는 실험용 bundle을 만든다.
- sections context를 활용해 header drift, unit drift, block drift를 진단한다.

가설:
1. 최신 markdown의 header signature + row core overlap만으로도 같은 논리 표를 상당수 묶을 수 있다.
2. dividend/audit/companyOverview 계열은 block drift가 실제로 관찰된다.
3. bundle 단위 요약은 scorer의 action 판단에 직접 도움이 된다.

방법:
1. 002의 sample topic rows를 불러온다.
2. 003의 TableIR를 각 row에 부착한다.
3. 같은 stock/topic 안에서 greedy clustering으로 bundle을 만든다.

결과 (실험 후 작성):
- sample topic rows 전체에서 temporal bundle `5,662개`를 만들었다.
- `block_drift` bundle `2,369개`, `header_drift` bundle `720개`, `unit_drift` bundle `706개`
- median member 수 `1.0`, median similarity `1.0`
- bundle 수가 특히 큰 topic: `fsSummary 1,489`, `financialNotes 960`, `consolidatedNotes 897`, `companyOverview 443`
- 실행 시간: 약 `149.9초`

결론:
- block drift는 실제로 꽤 많다. "blockOrder를 절대 기준으로 믿으면 안 된다"는 가정이 맞았다.
- 다만 greedy clustering이 보수적으로 동작해 member 1짜리 bundle이 많다. 즉 현 시점 bundle은 recall보다 precision 쪽에 치우쳐 있다.
- scorer에는 충분히 도움이 되지만, 장기적으로는 bundle matching을 더 공격적으로 개선해야 한다.

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import polars as pl

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
_ir = load_script("003_tableIR")


def jaccard(values1: list[str], values2: list[str]) -> float:
    set1 = {value for value in values1 if value}
    set2 = {value for value in values2 if value}
    union = len(set1 | set2)
    return len(set1 & set2) / union if union else 0.0


def row_to_ir(row: dict[str, object]):
    return _ir.build_table_ir(row)


def similarity(ir1, ir2) -> float:
    score = 0.0
    if ir1.structureType == ir2.structureType:
        score += 0.35
    if ir1.headerSignature == ir2.headerSignature:
        score += 0.35
    elif ir1.headerSignature and ir2.headerSignature and (
        ir1.headerSignature in ir2.headerSignature or ir2.headerSignature in ir1.headerSignature
    ):
        score += 0.2
    score += 0.25 * jaccard(ir1.rowCore, ir2.rowCore)
    if set(ir1.unitTokens) & set(ir2.unitTokens):
        score += 0.05
    return round(score, 4)


@lru_cache(maxsize=1)
def build_temporal_bundles() -> list[dict[str, object]]:
    rows = _seed.collect_sample_topic_rows()
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["stockCode"]), str(row["topic"]))].append(row)

    bundles: list[dict[str, object]] = []
    for (stock_code, topic), items in grouped.items():
        clusters: list[dict[str, object]] = []
        for row in sorted(items, key=lambda value: int(value["blockOrder"])):
            ir = row_to_ir(row)
            assigned = False
            for cluster in clusters:
                sim = similarity(ir, cluster["anchor"])
                if sim >= 0.55:
                    cluster["members"].append((row, ir, sim))
                    assigned = True
                    break
            if not assigned:
                clusters.append({"anchor": ir, "members": [(row, ir, 1.0)]})

        for index, cluster in enumerate(clusters, start=1):
            members = cluster["members"]
            block_orders = sorted({int(row["blockOrder"]) for row, _, _ in members})
            header_signatures = {ir.headerSignature for _, ir, _ in members if ir.headerSignature}
            unit_sets = {tuple(ir.unitTokens) for _, ir, _ in members if ir.unitTokens}
            row_overlaps = [sim for _, _, sim in members]
            bundles.append(
                {
                    "bundleId": f"{stock_code}:{topic}:tb{index}",
                    "stockCode": stock_code,
                    "topic": topic,
                    "blockOrders": block_orders,
                    "memberCount": len(members),
                    "structureTypes": Counter(ir.structureType for _, ir, _ in members).most_common(),
                    "meanMemberSimilarity": round(sum(row_overlaps) / len(row_overlaps), 4),
                    "meanRowCoreJaccard": round(
                        sum(jaccard(members[0][1].rowCore, ir.rowCore) for _, ir, _ in members) / len(members), 4
                    ),
                    "driftFlags": [
                        flag
                        for flag, cond in (
                            ("block_drift", len(block_orders) > 1),
                            ("header_drift", len(header_signatures) > 1),
                            ("unit_drift", len(unit_sets) > 1),
                        )
                        if cond
                    ],
                }
            )
    return bundles


def summarize_bundles() -> dict[str, object]:
    bundles = build_temporal_bundles()
    return {
        "bundleCount": len(bundles),
        "multiBlockBundles": sum(1 for bundle in bundles if "block_drift" in bundle["driftFlags"]),
        "headerDriftBundles": sum(1 for bundle in bundles if "header_drift" in bundle["driftFlags"]),
        "unitDriftBundles": sum(1 for bundle in bundles if "unit_drift" in bundle["driftFlags"]),
        "medianMembers": float(pl.Series([bundle["memberCount"] for bundle in bundles]).median()) if bundles else 0.0,
        "medianSimilarity": float(pl.Series([bundle["meanMemberSimilarity"] for bundle in bundles]).median())
        if bundles
        else 0.0,
        "topics": Counter(bundle["topic"] for bundle in bundles).most_common(10),
    }


def main() -> None:
    print(summarize_bundles())


if __name__ == "__main__":
    main()
