"""
실험 ID: 088-003
실험명: sections query compiler

목적:
- 자연어 질문을 6개 leg query로 안정적으로 분해할 수 있는지 확인한다.
- 최신/변화/표 조회 의도가 leg token으로 분리되는지 검증한다.

가설:
1. 공시 질의는 topic/time/table/change/entity 축으로 비교적 안정적으로 분해된다.
2. 간단한 규칙만으로도 검색 후보군을 강하게 좁힐 수 있다.

방법:
1. 배당/원재료/사업/위험 관련 샘플 질의 4개를 준비한다.
2. compileQuery()를 실행해 leg별 token을 기록한다.
3. intent, topicLeg, timeLeg, tableLeg, changeLeg 분해를 수동 검토한다.

결과 (실험 후 작성):
- queryCount: 4
- 4/4 질의에서 핵심 topicLeg 추출 성공
- latest marker 분리: 1/1
- change marker 분리: 1/1
- table marker 분리: 2/2

결론:
- rule-based query compiler만으로도 현재 실험 범위의 의도 분해는 충분히 가능하다.
- 이후 성능 병목은 query compiler보다 unit/index 품질에 있을 가능성이 높다.

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
    summary = mod.runQueryCompilerExperiment()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
