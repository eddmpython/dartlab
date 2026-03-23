"""
실험 ID: 088-004
실험명: sections table stitch benchmark

목적:
- table row unit을 period 축으로 다시 이어붙이는 stitch graph가 성립하는지 확인한다.
- rowFingerprint + tableFingerprint + comparablePath 조합이 period 정렬에 충분한지 본다.

가설:
1. table row를 rowFingerprint 기준으로 묶으면 같은 행의 기간별 horizontal stitch가 가능하다.
2. 헤더 보존과 숫자 정렬 정확도는 높은 수준을 유지한다.

방법:
1. sampleUnits의 table unit만 대상으로 fingerprint group을 만든다.
2. period 2개 이상을 갖는 그룹을 stitched group으로 본다.
3. rowLabel 일관성, 헤더 보존, 숫자 포함 행 비율을 지표로 계산한다.

결과 (실험 후 작성):
- groups: 26,595
- matchedGroups: 4,463
- rowStitchPrecision: 0.9568
- rowStitchRecall: 0.1678
- headerPreservation: 0.9967
- numericAlignmentAccuracy: 0.77

결론:
- precision은 높아서 stitch key 자체는 안정적이다.
- recall은 아직 낮아서 더 많은 table block을 같은 comparable group으로 묶는 규칙이 필요하다.
- 숫자 정렬 정확도가 기대보다 낮아서 row canonicalization과 unit/주석 정규화가 추가로 필요하다.
- v1에서는 “정확한 stitch 우선, coverage는 후속 확장” 전략이 맞다.

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
    summary = mod.runTableStitchExperiment()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
