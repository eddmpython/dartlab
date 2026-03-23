"""
실험 ID: 088-002
실험명: sections LegIndex build

목적:
- UnderstandingUnit를 6개 leg inverted index로 materialize할 수 있는지 확인한다.
- posting size와 build time이 이후 실시간 검색 요구를 감당할 수 있는지 본다.

가설:
1. 6개 leg posting list를 순수 Python dict/list로도 충분히 빠르게 만들 수 있다.
2. posting median size가 작으면 rare-leg-first 검색 전략이 유효하다.

방법:
1. 001에서 생성한 sampleUnits.parquet를 읽는다.
2. topicLeg, structureLeg, timeLeg, tableLeg, entityLeg, changeLeg posting을 만든다.
3. token 수, median posting size, buildSec를 기록한다.

결과 (실험 후 작성):
- recordCount: 79,576
- buildSec: 7.2009
- topicLeg tokens: 61 / median posting: 4,426.0
- structureLeg tokens: 11,857 / median posting: 7.0
- timeLeg tokens: 24 / median posting: 7,899.5
- tableLeg tokens: 57,491 / median posting: 2.0
- entityLeg tokens: 36,821 / median posting: 6.0
- changeLeg tokens: 4 / median posting: 59,160.0

결론:
- structure/entity/table leg가 매우 희소해서 rare-leg-first 전략의 기반이 충분하다.
- 8만 unit 규모에서도 index build가 7.2초 수준이라 오프라인 materialization 비용으로는 감당 가능하다.

실험일: 2026-03-23
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def loadUnitModule():
    path = Path(__file__).with_name("001_unitSchema.py")
    spec = importlib.util.spec_from_file_location("leg001", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    mod = loadUnitModule()
    summary = mod.runLegIndexBuildExperiment()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
