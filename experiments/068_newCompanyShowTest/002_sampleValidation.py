"""
실험 ID: 068-002
실험명: new Company show prototype - sample validation

목적:
- 새 show prototype이 현재 Company.show(topic, block)보다 실제로 더 많은 docs table block을
  wide DataFrame으로 구조화하는지 표본 검증한다
- 대표 종목/대표 topic에서 recovered block과 regression block을 수치로 확인한다

가설:
1. sample 10종목 x 핵심 topic에서 prototype wide block 수가 현재 show()보다 많다
2. audit, salesOrder, boardOfDirectors, executivePay에서 recovered block이 의미 있게 나온다
3. regression은 존재하더라도 recovered 대비 소수다

방법:
1. 대표 10종목과 핵심 docs topic 집합을 고정한다
2. 각 topic의 docs table block마다 현재 show() wide 여부를 측정한다
3. 001 prototype으로 block별 multi-schema 렌더링 후 wide 여부를 측정한다
4. overall/topic별 recovered/regression을 집계한다

결과 (실험 후 작성):
- 대표 10종목 x 10개 topic, 총 954 table block 검증
- 현재 show() wide: 633 blocks
- prototype wide: 884 blocks
- recovered: 271 blocks
- regression: 20 blocks
- topic별 recovered 상위:
  - boardOfDirectors 59
  - riskDerivative 35
  - executivePay 33
  - companyOverview 26
  - rawMaterial 25
  - audit 25
  - salesOrder 11
- 핵심 topic protoRate:
  - audit 0.939
  - salesOrder 0.969
  - boardOfDirectors 0.936
  - executivePay 0.885

결론:
- 가설 1~3 채택
- sample 기준으로 흡수 전 feasibility 충분

실험일: 2026-03-18
"""

from __future__ import annotations

import importlib.util
import sys
from collections import defaultdict
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab import Company

ROOT = Path(__file__).resolve().parent
PROTO_PATH = ROOT / "001_newCompanyShowPrototype.py"

SAMPLE_STOCKS: list[tuple[str, str]] = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("035420", "NAVER"),
    ("035720", "카카오"),
    ("005380", "현대차"),
    ("068270", "셀트리온"),
    ("051910", "LG화학"),
    ("105560", "KB금융"),
    ("034730", "SK"),
    ("028260", "삼성물산"),
]

SAMPLE_TOPICS = [
    "audit",
    "boardOfDirectors",
    "companyOverview",
    "dividend",
    "employee",
    "executivePay",
    "majorHolder",
    "rawMaterial",
    "riskDerivative",
    "salesOrder",
]


def load_proto():
    spec = importlib.util.spec_from_file_location("newCompanyShowProto", PROTO_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def is_current_wide(payload) -> bool:
    return isinstance(payload, pl.DataFrame) and "항목" in payload.columns and payload.height > 0


def main() -> None:
    proto = load_proto()
    overall = defaultdict(int)
    topicStats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    recoveredRows: list[dict[str, object]] = []
    regressionRows: list[dict[str, object]] = []

    for stockCode, corpName in SAMPLE_STOCKS:
        company = Company(stockCode)
        for topic in SAMPLE_TOPICS:
            topicFrame = proto.docs_topic_frame(company, topic)
            if topicFrame.is_empty():
                continue
            periodCols = proto.period_columns(topicFrame)
            for blockOrder in proto.table_blocks(topicFrame):
                overall["blocks"] += 1
                topicStats[topic]["blocks"] += 1

                current = company.show(topic, blockOrder)
                currentWide = is_current_wide(current)
                if currentWide:
                    overall["currentWide"] += 1
                    topicStats[topic]["currentWide"] += 1

                rendered = proto.render_block(topicFrame, blockOrder, periodCols)
                protoWides = [item for item in rendered if item.wide is not None]
                protoWide = bool(protoWides)
                if protoWide:
                    overall["protoWide"] += 1
                    topicStats[topic]["protoWide"] += 1

                if protoWide and not currentWide:
                    overall["recovered"] += 1
                    topicStats[topic]["recovered"] += 1
                    best = protoWides[0]
                    recoveredRows.append(
                        {
                            "stockCode": stockCode,
                            "corpName": corpName,
                            "topic": topic,
                            "blockOrder": blockOrder,
                            "schemaId": best.schema.schemaId,
                            "structType": best.schema.structType,
                            "periodCount": best.schema.periodCount,
                            "itemCount": len(best.schema.canonicalItems),
                            "fillRate": round(best.fillRate, 3),
                            "shape": str(best.wide.shape),
                        }
                    )

                if currentWide and not protoWide:
                    overall["regression"] += 1
                    topicStats[topic]["regression"] += 1
                    regressionRows.append(
                        {
                            "stockCode": stockCode,
                            "corpName": corpName,
                            "topic": topic,
                            "blockOrder": blockOrder,
                            "currentShape": str(current.shape),
                        }
                    )

    overallDf = pl.DataFrame(
        [
            {
                "sampleStocks": len(SAMPLE_STOCKS),
                "topics": len(SAMPLE_TOPICS),
                "tableBlocks": overall["blocks"],
                "currentWideBlocks": overall["currentWide"],
                "protoWideBlocks": overall["protoWide"],
                "recoveredBlocks": overall["recovered"],
                "regressionBlocks": overall["regression"],
            }
        ]
    )

    topicRows = []
    for topic in sorted(topicStats):
        stat = topicStats[topic]
        blocks = stat["blocks"]
        currentWide = stat["currentWide"]
        protoWide = stat["protoWide"]
        recovered = stat["recovered"]
        regression = stat["regression"]
        topicRows.append(
            {
                "topic": topic,
                "blocks": blocks,
                "currentWide": currentWide,
                "protoWide": protoWide,
                "recovered": recovered,
                "regression": regression,
                "currentRate": round(currentWide / blocks, 3) if blocks else 0.0,
                "protoRate": round(protoWide / blocks, 3) if blocks else 0.0,
            }
        )

    topicDf = pl.DataFrame(topicRows).sort(["recovered", "protoRate", "topic"], descending=[True, True, False])

    print("=== OVERALL ===")
    print(overallDf)
    print()
    print("=== BY TOPIC ===")
    print(topicDf)
    print()

    if recoveredRows:
        recoveredDf = pl.DataFrame(recoveredRows).sort(["fillRate", "periodCount"], descending=[True, True])
        print("=== RECOVERED (top 30) ===")
        print(recoveredDf.head(30))
        print()
    else:
        print("=== RECOVERED ===")
        print("none")
        print()

    if regressionRows:
        regressionDf = pl.DataFrame(regressionRows).sort(["topic", "stockCode", "blockOrder"])
        print("=== REGRESSION ===")
        print(regressionDf)
        print()
    else:
        print("=== REGRESSION ===")
        print("none")
        print()


if __name__ == "__main__":
    pl.Config.set_tbl_rows(40)
    pl.Config.set_tbl_cols(12)
    pl.Config.set_fmt_str_lengths(60)
    main()
