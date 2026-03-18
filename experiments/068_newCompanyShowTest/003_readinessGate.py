"""
실험 ID: 068-003
실험명: new Company show prototype - readiness gate

목적:
- sample validation 결과를 바탕으로 prototype이 흡수 검토 단계에 들어갈 수 있는지 gate를 건다
- recovered/regression, 핵심 topic 커버리지, 예외 발생 여부를 단일 출력으로 정리한다

가설:
1. recovered block이 regression block보다 충분히 많으면 흡수 검토 가치가 있다
2. audit/salesOrder/boardOfDirectors/executivePay에서 recovered 또는 높은 protoWide rate가 나타나야 한다

방법:
1. 002 sample validation을 동일 표본으로 재실행한다
2. overall recovered/regression을 읽고 핵심 topic 지표를 확인한다
3. PASS / WARN / FAIL로 readiness를 판정한다

결과 (실험 후 작성):
- 표본 954 block 기준:
  - currentWide 633
  - protoWide 884
  - protoGain +251
  - recovered 271
  - regression 20
- readiness gate:
  - overall PASS
  - audit PASS
  - salesOrder PASS
  - boardOfDirectors PASS
  - executivePay PASS

결론:
- PASS
- Company 흡수 prototype 작업 착수 후보로 판단

실험일: 2026-03-18
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import polars as pl


ROOT = Path(__file__).resolve().parent
VALIDATION_PATH = ROOT / "002_sampleValidation.py"

CORE_TOPICS = ["audit", "salesOrder", "boardOfDirectors", "executivePay"]


def load_validation():
    spec = importlib.util.spec_from_file_location("newCompanyShowValidation", VALIDATION_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_validation()
    proto = module.load_proto()

    overall = {"blocks": 0, "currentWide": 0, "protoWide": 0, "recovered": 0, "regression": 0}
    topicStats: dict[str, dict[str, int]] = {}

    for stockCode, _corpName in module.SAMPLE_STOCKS:
        company = module.Company(stockCode)
        for topic in module.SAMPLE_TOPICS:
            topicFrame = proto.docs_topic_frame(company, topic)
            if topicFrame.is_empty():
                continue
            periodCols = proto.period_columns(topicFrame)
            for blockOrder in proto.table_blocks(topicFrame):
                overall["blocks"] += 1
                topicStats.setdefault(topic, {"blocks": 0, "currentWide": 0, "protoWide": 0, "recovered": 0, "regression": 0})
                topicStats[topic]["blocks"] += 1

                current = company.show(topic, blockOrder)
                currentWide = module.is_current_wide(current)
                if currentWide:
                    overall["currentWide"] += 1
                    topicStats[topic]["currentWide"] += 1

                protoWide = any(item.wide is not None for item in proto.render_block(topicFrame, blockOrder, periodCols))
                if protoWide:
                    overall["protoWide"] += 1
                    topicStats[topic]["protoWide"] += 1

                if protoWide and not currentWide:
                    overall["recovered"] += 1
                    topicStats[topic]["recovered"] += 1
                if currentWide and not protoWide:
                    overall["regression"] += 1
                    topicStats[topic]["regression"] += 1

    recovered = overall["recovered"]
    regression = overall["regression"]
    protoGain = overall["protoWide"] - overall["currentWide"]

    gateLines: list[tuple[str, str]] = []
    if regression == 0 and recovered > 0:
        gateLines.append(("overall", "PASS"))
    elif recovered >= max(3, regression * 2):
        gateLines.append(("overall", "PASS"))
    elif protoGain > 0:
        gateLines.append(("overall", "WARN"))
    else:
        gateLines.append(("overall", "FAIL"))

    for topic in CORE_TOPICS:
        stat = topicStats.get(topic, {"blocks": 0, "currentWide": 0, "protoWide": 0, "recovered": 0, "regression": 0})
        blocks = stat["blocks"]
        protoRate = stat["protoWide"] / blocks if blocks else 0.0
        if stat["recovered"] > 0 or protoRate >= 0.7:
            status = "PASS"
        elif protoRate > 0:
            status = "WARN"
        else:
            status = "FAIL"
        gateLines.append((topic, status))

    gateDf = pl.DataFrame(
        [{"target": target, "status": status} for target, status in gateLines]
    )

    summaryDf = pl.DataFrame([{
        "tableBlocks": overall["blocks"],
        "currentWideBlocks": overall["currentWide"],
        "protoWideBlocks": overall["protoWide"],
        "protoGain": protoGain,
        "recoveredBlocks": recovered,
        "regressionBlocks": regression,
    }])

    print("=== READINESS SUMMARY ===")
    print(summaryDf)
    print()
    print("=== READINESS GATE ===")
    print(gateDf)


if __name__ == "__main__":
    pl.Config.set_tbl_rows(20)
    pl.Config.set_tbl_cols(10)
    pl.Config.set_fmt_str_lengths(40)
    main()
