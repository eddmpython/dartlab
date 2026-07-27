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

import pathlib
import subprocess
import sys

import pytest

from dartlab.simulate.worldTypes import LawSpec, _canonical, _noOpLaw, _stableHash

pytestmark = [pytest.mark.unit]

_TYPES_PATH = pathlib.Path(__file__).resolve().parents[2] / "src" / "dartlab" / "simulate" / "worldTypes.py"
_HASH_SNIPPET = (
    "from dartlab.simulate.worldTypes import LawSpec,_canonical,_stableHash;"
    "print(_stableHash(_canonical(LawSpec(lawId='x',outputs=()))))"
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

    assert sealed == {"callable": "dartlab.simulate.worldTypes._noOpLaw", "codeHash": "noOpLaw"}


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
