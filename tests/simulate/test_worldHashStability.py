"""세계 모델 재현 해시의 소스 위치 독립성 회귀.

`LawSpec.fn` 의 기본값이 익명 람다였다. `_canonical` 은 callable 을 해싱할 때 코드 객체를
marshal 하는데, 그 안에 파일 이름과 첫 줄 번호가 들어간다. 그래서 그 람다 위에 빈 줄 하나만
넣어도 `executableHash` 와 `runHash` 가 바뀌었다. 파일을 옮기면 당연히 바뀌었다.

재현성을 재려고 만든 해시가 소스 편집에 흔들리면 그 해시는 아무 것도 재지 못한다. 같은
모델과 같은 입력으로 두 번 돌린 것이 서로 다른 실행으로 기록되고, 그 둘이 정말 같은지
확인할 방법이 사라진다.

지금 저장소의 `LawSpec` 생성 30 곳은 전부 `fn` 을 명시하므로 이것은 잠재 함정이었다.
기본값을 쓰는 코드가 하나만 생기면 곧바로 살아난다.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
from dataclasses import replace

import pytest

from dartlab.simulate.world import (
    ActionSpec,
    LawSpec,
    StrategySpec,
    VariableSpec,
    WorldModel,
    executableHashFor,
)
from dartlab.simulate.worldTypes import SimulationSpecError, _canonical, _noOpLaw, _stableHash

pytestmark = [pytest.mark.unit]

_TYPES_PATH = pathlib.Path(__file__).resolve().parents[2] / "src" / "dartlab" / "simulate" / "worldTypes.py"
_HASH_SNIPPET = (
    "from dartlab.simulate.worldTypes import LawSpec,_canonical,_stableHash;"
    "print(_stableHash(_canonical(LawSpec(lawId='x',outputs=()))))"
)


class _MutableLawState:
    def __init__(self, multiplier: float) -> None:
        self.multiplier = multiplier


_MUTABLE_LAW_STATE = _MutableLawState(1.0)


def _contractLaw(ctx):
    return {"result": ctx.actions["invest"] - ctx.actionCost}


def _statefulContractLaw(ctx):
    return {"result": _MUTABLE_LAW_STATE.multiplier * ctx.actions["invest"] - ctx.actionCost}


def _contractModel(
    *,
    variable: VariableSpec | None = None,
    action: ActionSpec | None = None,
    law: LawSpec | None = None,
) -> WorldModel:
    return WorldModel(
        modelId="hash-contract",
        version="1",
        variables=(variable or VariableSpec("result", "currency", "metric", lower=-100.0, upper=100.0),),
        actions=(
            action
            or ActionSpec(
                "invest",
                "currency",
                0.0,
                10.0,
                leadSteps=1,
                costPerUnit=0.25,
                effectEvidence="accountingIdentity",
                provenance="experiment:v1",
            ),
        ),
        laws=(
            law
            or LawSpec(
                "resultLaw",
                outputs=("result",),
                actionInputs=("invest",),
                usesActionCost=True,
                evidenceKind="accountingIdentity",
                provenance="identity:v1",
                parameters={"scale": 1.0},
                fn=_contractLaw,
            ),
        ),
        stepFrequency="month",
        stepSpan=1,
    )


def _contractStrategy() -> StrategySpec:
    return StrategySpec(
        "baseline",
        ({"invest": 1.0},),
        refs=("policy://baseline",),
        isBaseline=True,
        policyVersion="1",
        policyProvenance="approved:v1",
    )


def _hashInSubprocess() -> str:
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", _HASH_SNIPPET], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def testDefaultLawIsNamedNotALambda() -> None:
    """익명 람다면 이름이 `<lambda>` 라 위치 말고는 식별할 것이 없다."""

    assert LawSpec(lawId="x", outputs=()).fn is _noOpLaw
    assert _noOpLaw.__name__ == "_noOpLaw"


def testDefaultLawSealIsPositionFree() -> None:
    """봉인값에 코드 해시가 아니라 고정 표식이 들어가야 한다."""

    sealed = _canonical(_noOpLaw)

    assert sealed == {
        "type": "callable",
        "name": "dartlab.simulate.worldTypes._noOpLaw",
        "codeHash": "noOpLaw",
    }


def testDefaultLawReturnsNothing() -> None:
    """봉인을 고정하느라 동작을 바꾸면 안 된다."""

    assert _noOpLaw(None) == {}


def testHashSurvivesSourceLineShift() -> None:
    """결함의 핵심이다. 빈 줄을 넣어도 재현 해시는 그대로여야 한다."""

    original = _TYPES_PATH.read_text(encoding="utf-8")
    marker = "def _noOpLaw(_state) -> dict:"
    assert marker in original

    before = _hashInSubprocess()
    try:
        _TYPES_PATH.write_text(original.replace(marker, "\n\n\n\n\n" + marker, 1), encoding="utf-8")
        after = _hashInSubprocess()
    finally:
        _TYPES_PATH.write_text(original, encoding="utf-8")

    assert before == after


def testRealLawsAreStillHashedByCode() -> None:
    """기본 법칙만 예외다. 진짜 법칙은 코드가 바뀌면 해시도 바뀌어야 한다."""

    def lawA(_state):
        return {"y": 1.0}

    def lawB(_state):
        return {"y": 2.0}

    assert _stableHash(_canonical(lawA)) != _stableHash(_canonical(lawB))


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (None, "None"),
        (True, 1),
        ((1,), [1]),
        (["a,b", "c"], ["a", "b,c"]),
        ({"a:b": "c"}, {"a": "b:c"}),
    ],
)
def testCanonicalEncodingPreservesTypesAndValueBoundaries(left, right) -> None:
    assert _stableHash({"value": left}) != _stableHash({"value": right})


def testCanonicalEncodingIsStableAcrossHashSeeds() -> None:
    snippet = (
        "from dartlab.simulate.worldTypes import _stableHash;"
        "keys={'alpha','beta','gamma'};"
        "print(_stableHash({'mapping':{key:len(key) for key in keys},'set':keys}))"
    )
    digests = []
    for seed in ("1", "2"):
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "-c", snippet],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PYTHONHASHSEED": seed},
        )
        digests.append(result.stdout.strip())

    assert digests[0] == digests[1]


@pytest.mark.parametrize(
    "changed",
    [
        VariableSpec("result", "won", "metric", lower=-100.0, upper=100.0),
        VariableSpec("result", "currency", "metric", lower=-99.0, upper=100.0),
        VariableSpec("result", "currency", "metric", lower=-100.0, upper=99.0),
        VariableSpec("result", "currency", "metric", frequency="monthEnd"),
        VariableSpec("result", "currency", "metric", timing="flow"),
        VariableSpec("result", "currency", "metric", transformId="log-v1"),
        VariableSpec("result", "currency", "metric", evidenceRole="observed"),
    ],
)
def testExecutableHashSealsVariableMeaning(changed: VariableSpec) -> None:
    strategy = _contractStrategy()

    assert executableHashFor(_contractModel(), (strategy,)) != executableHashFor(
        _contractModel(variable=changed), (strategy,)
    )


@pytest.mark.parametrize(
    "fieldAndValue",
    [
        ("unit", "won"),
        ("lower", 0.5),
        ("upper", 9.0),
        ("leadSteps", 2),
        ("costPerUnit", 0.5),
        ("effectEvidence", "explicitAssumption"),
        ("provenance", "experiment:v2"),
    ],
)
def testExecutableHashSealsActionMeaning(fieldAndValue: tuple[str, object]) -> None:
    fieldName, value = fieldAndValue
    model = _contractModel()
    changed = replace(model.actions[0], **{fieldName: value})
    strategy = _contractStrategy()

    assert executableHashFor(model, (strategy,)) != executableHashFor(_contractModel(action=changed), (strategy,))


@pytest.mark.parametrize(
    "fieldAndValue",
    [
        ("provenance", "identity:v2"),
        ("version", "2"),
        ("status", "partial"),
        ("parameters", {"scale": 2.0}),
        ("usesActionCost", False),
    ],
)
def testExecutableHashSealsLawMeaning(fieldAndValue: tuple[str, object]) -> None:
    fieldName, value = fieldAndValue
    model = _contractModel()
    changed = replace(model.laws[0], **{fieldName: value})
    if fieldName == "usesActionCost":
        changedAction = replace(model.actions[0], costPerUnit=0.0)
        baseline = _contractModel(action=changedAction)
        changedModel = _contractModel(action=changedAction, law=changed)
    else:
        baseline = model
        changedModel = _contractModel(law=changed)
    strategy = _contractStrategy()

    assert executableHashFor(baseline, (strategy,)) != executableHashFor(changedModel, (strategy,))


@pytest.mark.parametrize(
    "fieldAndValue",
    [
        ("actionsByStep", ({"invest": 2.0},)),
        ("refs", ("policy://replacement",)),
        ("isBaseline", False),
        ("policyVersion", "2"),
        ("policyProvenance", "approved:v2"),
    ],
)
def testExecutableHashSealsStaticPolicyMeaning(fieldAndValue: tuple[str, object]) -> None:
    model = _contractModel()
    strategy = _contractStrategy()
    fieldName, value = fieldAndValue
    changed = replace(strategy, **{fieldName: value})

    assert executableHashFor(model, (strategy,)) != executableHashFor(model, (changed,))


def testExecutableHashTracksMutableCustomGlobalState() -> None:
    law = replace(_contractModel().laws[0], fn=_statefulContractLaw)
    model = _contractModel(law=law)
    strategy = _contractStrategy()
    original = _MUTABLE_LAW_STATE.multiplier

    try:
        before = executableHashFor(model, (strategy,))
        _MUTABLE_LAW_STATE.multiplier = 2.0
        after = executableHashFor(model, (strategy,))
    finally:
        _MUTABLE_LAW_STATE.multiplier = original

    assert before != after


def testCanonicalEncodingFailsClosedForCyclicState() -> None:
    cyclic: list[object] = []
    cyclic.append(cyclic)

    with pytest.raises(SimulationSpecError, match="cyclic canonical value"):
        _canonical(cyclic)


def testCanonicalEncodingFailsClosedForOpaqueState() -> None:
    with pytest.raises(SimulationSpecError, match="canonical state is unsupported"):
        _canonical(object())
