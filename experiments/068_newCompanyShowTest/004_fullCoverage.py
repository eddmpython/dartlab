"""
실험 ID: 068-004
실험명: new Company show prototype - full local coverage

목적:
- 로컬 docs 보유 전체 종목에서 대표 10개 table-heavy topic 기준으로
  현재 Company.show(topic, block) 대비 prototype이 docs table block을 얼마나 더
  wide DataFrame으로 복구하는지 전수 측정한다
- 표본이 아니라 전체 로컬 universe 기준으로 흡수 가능성을 판단한다

가설:
1. 로컬 docs 전종목 기준으로도 prototype wide block 수가 현재 show()보다 유의미하게 많다
2. recovered block 수가 regression block 수보다 충분히 크다
3. boardOfDirectors, audit, salesOrder, executivePay 같은 핵심 topic에서 개선이 유지된다

방법:
1. `buildIndex("docs")`로 로컬 docs 보유 283종목을 집계한다
2. 각 종목의 대표 10개 table-heavy topic(`audit`, `boardOfDirectors`, `companyOverview`,
   `dividend`, `employee`, `executivePay`, `majorHolder`, `rawMaterial`,
   `riskDerivative`, `salesOrder`)만 대상으로 한다
3. 각 topic의 docs table block을 전부 순회한다
4. 현재 show 경로는 `_horizontalizeTableBlock()` 직접 호출로 측정하고,
   prototype wide 여부와 비교한다
5. 전체/토픽별 currentWide, protoWide, recovered, regression을 집계한다

결과 (실험 후 작성):
- 로컬 docs 보유 283종목 x 대표 10개 table-heavy topic 전수 완료
- 총 22,001 table block 검증
- currentWide: 16,050
- protoWide: 19,159
- recovered: 3,400
- regression: 291
- elapsed: 746.7초
- 핵심 topic:
  - boardOfDirectors: 2,071 -> 2,863, recovered 800, regression 8
  - rawMaterial: 1,160 -> 1,707, recovered 555, regression 8
  - riskDerivative: 1,913 -> 2,121, recovered 297, regression 89
  - audit: 1,261 -> 1,537, recovered 282, regression 6
  - salesOrder: 716 -> 965, recovered 253, regression 4
  - executivePay: 1,916 -> 2,093, recovered 226, regression 49

결론:
- 가설 1~3 채택
- 전종목 기준으로도 가능성은 충분히 확인됨
- 다만 `riskDerivative`, `executivePay`, `dividend`, `employee` 쪽 regression 정리가 흡수 전 필수

실험일: 2026-03-18
"""

from __future__ import annotations

import importlib.util
import sys
import time
from collections import defaultdict
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab import Company
from dartlab.core.dataLoader import buildIndex

ROOT = Path(__file__).resolve().parent
PROTO_PATH = ROOT / "001_newCompanyShowPrototype.py"
CORE_TOPICS = [
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
    spec = importlib.util.spec_from_file_location("newCompanyShowProtoFull", PROTO_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def is_current_wide(payload) -> bool:
    return isinstance(payload, pl.DataFrame) and "항목" in payload.columns and payload.height > 0


def docs_topics_with_tables(frame: pl.DataFrame) -> list[str]:
    if frame.is_empty():
        return []
    topics = (
        frame.filter(pl.col("blockType") == "table")
        .select("topic")
        .unique()
        .sort("topic")
    )
    return [topic for topic in topics["topic"].to_list() if topic in CORE_TOPICS]


def main() -> None:
    proto = load_proto()
    universe = buildIndex("docs")
    stockRows = universe.select(["stockCode", "corpName"]).to_dicts()

    overall = defaultdict(int)
    topicStats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    recoveredRows: list[dict[str, object]] = []
    regressionRows: list[dict[str, object]] = []
    stockRowsSummary: list[dict[str, object]] = []

    started = time.time()

    for idx, stock in enumerate(stockRows, start=1):
        stockCode = stock["stockCode"]
        corpName = stock["corpName"]
        company = Company(stockCode)
        sections = company.sections
        docsFrame = sections.filter(pl.col("source") == "docs") if sections is not None else pl.DataFrame()
        topics = docs_topics_with_tables(docsFrame)

        stockBlocks = 0
        stockRecovered = 0
        stockRegression = 0
        stockCurrentWide = 0
        stockProtoWide = 0

        for topic in topics:
            topicFrame = proto.docs_topic_frame(company, topic)
            if topicFrame.is_empty():
                continue
            periodCols = proto.period_columns(topicFrame)
            blocks = proto.table_blocks(topicFrame)

            for blockOrder in blocks:
                stockBlocks += 1
                overall["blocks"] += 1
                topicStats[topic]["blocks"] += 1

                current = None
                if hasattr(company, "_horizontalizeTableBlock"):
                    current = company._horizontalizeTableBlock(topicFrame, blockOrder, periodCols)
                else:
                    current = company.show(topic, blockOrder)
                currentWide = is_current_wide(current)
                if currentWide:
                    overall["currentWide"] += 1
                    topicStats[topic]["currentWide"] += 1
                    stockCurrentWide += 1

                rendered = proto.render_block(topicFrame, blockOrder, periodCols)
                protoWides = [item for item in rendered if item.wide is not None]
                protoWide = bool(protoWides)
                if protoWide:
                    overall["protoWide"] += 1
                    topicStats[topic]["protoWide"] += 1
                    stockProtoWide += 1

                if protoWide and not currentWide:
                    overall["recovered"] += 1
                    topicStats[topic]["recovered"] += 1
                    stockRecovered += 1
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
                    stockRegression += 1
                    regressionRows.append(
                        {
                            "stockCode": stockCode,
                            "corpName": corpName,
                            "topic": topic,
                            "blockOrder": blockOrder,
                            "currentShape": str(current.shape),
                        }
                    )

        stockRowsSummary.append(
            {
                "stockCode": stockCode,
                "corpName": corpName,
                "blocks": stockBlocks,
                "currentWide": stockCurrentWide,
                "protoWide": stockProtoWide,
                "recovered": stockRecovered,
                "regression": stockRegression,
            }
        )

        if idx % 25 == 0 or idx == len(stockRows):
            elapsed = time.time() - started
            print(
                f"[{idx}/{len(stockRows)}] "
                f"blocks={overall['blocks']} "
                f"recovered={overall['recovered']} "
                f"regression={overall['regression']} "
                f"elapsed={elapsed:.1f}s"
            )

    elapsed = time.time() - started

    overallDf = pl.DataFrame(
        [{
            "stocks": len(stockRows),
            "tableBlocks": overall["blocks"],
            "currentWideBlocks": overall["currentWide"],
            "protoWideBlocks": overall["protoWide"],
            "recoveredBlocks": overall["recovered"],
            "regressionBlocks": overall["regression"],
            "elapsedSec": round(elapsed, 1),
        }]
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
    stockDf = pl.DataFrame(stockRowsSummary).sort(["recovered", "protoWide", "stockCode"], descending=[True, True, False])

    print("=== OVERALL ===")
    print(overallDf)
    print()
    print("=== BY TOPIC (top 30) ===")
    print(topicDf.head(30))
    print()
    print("=== BY STOCK (top 30 recovered) ===")
    print(stockDf.head(30))
    print()

    if recoveredRows:
        recoveredDf = pl.DataFrame(recoveredRows).sort(["fillRate", "periodCount"], descending=[True, True])
        print("=== RECOVERED (top 40) ===")
        print(recoveredDf.head(40))
        print()
    else:
        print("=== RECOVERED ===")
        print("none")
        print()

    if regressionRows:
        regressionDf = pl.DataFrame(regressionRows).sort(["topic", "stockCode", "blockOrder"])
        print("=== REGRESSION (top 40) ===")
        print(regressionDf.head(40))
        print()
    else:
        print("=== REGRESSION ===")
        print("none")
        print()


if __name__ == "__main__":
    pl.Config.set_tbl_rows(50)
    pl.Config.set_tbl_cols(12)
    pl.Config.set_fmt_str_lengths(60)
    main()
