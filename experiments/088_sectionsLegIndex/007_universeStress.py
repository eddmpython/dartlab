"""
실험 ID: 088-007
실험명: sections LegIndex universe stress

목적:
- 샘플 6개에서 끝나지 않고 50개, 283개 DART 종목으로 확장했을 때 materialization/index/query가 감당 가능한지 본다.
- 속도 우선 설계가 실제 corpus 확장에서도 유지되는지 확인한다.

가설:
1. filtered topic + lastN period + row-level unit 설계면 283개에서도 실행 가능하다.
2. query latency는 corpus가 커져도 수 ms~수십 ms 수준에 머문다.

방법:
1. sample6, stress50, stress283 세 단계를 순차 실행한다.
2. 각 단계에서 unit materialize, index build, 고정 query 4개 검색을 수행한다.
3. units, materializeSec, indexBuildSec, median/p95 latency, peakMemoryMb를 기록한다.

결과 (실험 후 작성):
- sample2: units 18,841 / materialize 33.7534s / index 1.9580s / median 1.3849ms / p95 2.2623ms / peakMemoryMb 1275.2
- sample6Cached: units 79,576 / materialize 0.0460s / index 8.6464s / median 0.3684ms / p95 0.4580ms / peakMemoryMb 1500.75
- errors: 전 단계 0
- exploratory note: stress8 추가 시 peakMemoryMb 2223.32로 과도해 기본 실행에서 제외

결론:
- cached sample6까지는 재실행이 빠르지만 fresh materialization은 2종목에서도 1.2GB를 넘는다.
- stress8 실험이 2.2GB까지 올라가서 현재 장비 기준 기본 stress 단계는 6 cached까지만 유지하는 것이 맞다.
- 다음 최적화는 candidate pruning보다 먼저 unit materialization 메모리 절감이다.

실험일: 2026-03-23
"""

from __future__ import annotations

import importlib.util
import json
import os
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


def selectedStageCodes(mod) -> dict[str, list[str]]:
    raw = os.getenv("LEGINDEX_STRESS_SIZES", "").strip()
    if raw:
        stageCodes: dict[str, list[str]] = {}
        for item in raw.split(","):
            item = item.strip()
            if not item:
                continue
            label, size = item.split(":", 1)
            stageCodes[label.strip()] = mod.availableDocCodes(int(size))
        return stageCodes
    return {
        "sample2": mod.SAMPLE_CODES[:2],
        "sample6Cached": mod.SAMPLE_CODES,
    }


def main() -> None:
    mod = loadUnitModule()
    summary = mod.runUniverseStressExperiment(stageCodes=selectedStageCodes(mod))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
