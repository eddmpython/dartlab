"""Beneish 호환 계산기가 proxy 점수를 발행하지 않는 회귀.

`@memoizedCalc` 가 붙어 있었다. 그 래퍼는 첫 인자가 Company 인 계산기 전용이라 서명을
`wrapper(company, *, basePeriod, overrides)` 로 바꾼다. 그런데 이 함수는 키워드 전용 순수
계산기라, 붙는 순간 모든 호출이 `TypeError: unexpected keyword argument 'salesT'` 로 죽었다.

호출 가능성 회귀는 유지하되, 현재 서명만으로는 Beneish 원식 TATA/LVGI와 순수
감가상각을 재현할 수 없으므로 숫자와 판정을 발행하지 않는 계약을 고정한다.
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


def testLegacyInputReturnsStructuredUnavailable() -> None:
    """옛 proxy 입력이 그럴듯한 점수나 clean 판정으로 바뀌면 안 된다."""

    result = calcBeneishMScore(**_SOUND_INPUT)

    assert isinstance(result, dict)
    assert result["status"] == "unavailable"
    assert result["mScore"] is None
    assert result["zone"] == "unavailable"
    assert result["components"] == {}
    assert result["reasonCode"] == "canonical_inputs_unavailable"


def testUnavailableNamesCanonicalGaps() -> None:
    """재활성화에 필요한 원식 계정이 기계 판독 가능해야 한다."""

    result = calcBeneishMScore(**_SOUND_INPUT)

    assert "long_term_debt" in result["missingCanonicalInputs"]
    assert "pure_depreciation_expense" in result["missingCanonicalInputs"]
    assert result["requirements"]["asOfRequired"] is True


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
