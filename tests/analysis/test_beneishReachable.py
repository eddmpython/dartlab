"""Beneish M-Score 가 호출 즉시 죽던 것에 대한 회귀.

`@memoizedCalc` 가 붙어 있었다. 그 래퍼는 첫 인자가 Company 인 계산기 전용이라 서명을
`wrapper(company, *, basePeriod, overrides)` 로 바꾼다. 그런데 이 함수는 키워드 전용 순수
계산기라, 붙는 순간 모든 호출이 `TypeError: unexpected keyword argument 'salesT'` 로 죽었다.

더 나쁜 것은 언제 죽느냐다. 이 계산은 여덟 계정이 전부 있을 때만 불린다. 자료가 갖춰진
회사일수록 확실히 터졌고, 자료가 없는 회사에서는 애초에 호출되지 않아 조용했다. 그래서
"분식 회계 탐지" 라는 기능이 정상 데이터에서만 작동하지 않는 상태로 남아 있었다.

예외는 `calcQualityAnomalies` 밖으로 그대로 새어 나갔다. 그 함수의 except 절이
`TypeError` 를 잡지 않기 때문이다.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from dartlab.analysis.financial._earningsQualityCalcs import calcBeneishMScore

pytestmark = [pytest.mark.unit]

_SOUND_INPUT = {
    "salesT": 110.0,
    "salesT1": 100.0,
    "receivablesT": 12.0,
    "receivablesT1": 10.0,
    "cogsT": 60.0,
    "cogsT1": 55.0,
    "sgaT": 20.0,
    "sgaT1": 18.0,
    "grossPropertyT": 80.0,
    "grossPropertyT1": 75.0,
    "totalAssetsT": 200.0,
    "totalAssetsT1": 190.0,
    "netIncomeT": 15.0,
    "ocfT": 18.0,
    "leverageT": 0.4,
    "leverageT1": 0.38,
    "depreciationT": 8.0,
    "depreciationT1": 7.5,
}


def testSoundInputProducesAScore() -> None:
    """결함의 핵심이다. 자료가 갖춰진 정상 경로가 예외 없이 값을 내야 한다."""

    result = calcBeneishMScore(**_SOUND_INPUT)

    assert isinstance(result, dict)
    assert isinstance(result.get("mScore"), float)


def testVerdictFollowsTheThreshold() -> None:
    """M-Score 는 -2.22 를 기준으로 갈린다. 값과 판정이 따로 놀면 안 된다."""

    result = calcBeneishMScore(**_SOUND_INPUT)

    assert result["mScore"] < -2.22
    assert "낮음" in result["interpretation"]


def testNoCompanyMemoizationDecorator() -> None:
    """Company 전용 래퍼를 순수 계산기에 붙이면 서명이 통째로 바뀐다."""

    source = pathlib.Path(calcBeneishMScore.__globals__["__file__"]).read_text(encoding="utf-8")
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "calcBeneishMScore")
    decorators = {getattr(d, "id", getattr(d, "attr", "")) for d in node.decorator_list}

    assert "memoizedCalc" not in decorators


def testMemoizedCalcIsOnlyOnCompanyCalculators() -> None:
    """같은 실수가 다른 데서 반복되지 않게 라이브러리 전체를 본다.

    `memoizedCalc` 래퍼는 첫 위치 인자로 company 를 받는다. 위치 인자가 하나도 없는 함수에
    붙어 있으면 그 함수는 부르는 순간 죽는다.
    """
    root = pathlib.Path(__file__).resolve().parents[2] / "src" / "dartlab"
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            names = {getattr(d, "id", getattr(d, "attr", "")) for d in node.decorator_list}
            if "memoizedCalc" in names and not node.args.args:
                offenders.append(f"{path.relative_to(root).as_posix()}::{node.name}")

    assert not offenders, f"위치 인자 없는 함수에 memoizedCalc: {offenders}"
