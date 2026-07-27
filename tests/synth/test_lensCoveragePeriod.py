"""렌즈 계약이 회계 기간을 시점으로 오독하던 것에 대한 회귀.

look-ahead 검사가 `dataAsOf` 의 모든 값을 "언제 알았나"로 읽었다. 그런데 `latestPeriod` 는
시점이 아니라 범위다. "어디까지 담았나" 를 뜻한다.

`latestPeriod: "2026"` 을 2026-12-31 로 읽으면, 2026 년 7 월에 2026 년 반기까지 받은 지극히
정상적인 결과가 "미래 자료를 봤다" 로 걸린다. 실제로 공개 계약인
`Company.analysis("종합평가")` 가 그 이유로 통째로 죽고 있었다. 격리 venv 에 wheel 을 설치해
돌리는 사용자 경험 검사에서 열한 항목 중 이 하나만 실패했다.

범위에서 look-ahead 는 그 기간이 시작하기도 전에 담았다고 할 때 생긴다. 그래서 끝이 아니라
시작으로 잰다. 시점형 값은 예전처럼 그 시점으로 잰다.

여기서 고정하는 것은 둘이다. 진행 중인 기간의 부분 수집은 통과한다, 아직 시작도 안 한 기간과
미래 시점 수집은 여전히 막힌다. 뒤엣것을 잃으면 이 검사는 존재 이유가 없어진다.
"""

from __future__ import annotations

from datetime import date

import pytest

from dartlab.synth.lensContract import _temporalLowerBound, _temporalUpperBound, _validateTime

pytestmark = [pytest.mark.unit]

_BOUNDARY = "2026-07-28"


def _time(dataAsOf) -> dict:
    return {"asOf": _BOUNDARY, "knowledgeBoundary": _BOUNDARY, "dataAsOf": dataAsOf}


@pytest.mark.parametrize(
    ("period", "expected"),
    [
        ("2026", date(2026, 1, 1)),
        ("FY2027", date(2027, 1, 1)),
        ("2026Q2", date(2026, 4, 1)),
        ("2026Q4", date(2026, 10, 1)),
        ("2026H1", date(2026, 1, 1)),
        ("2026-03", date(2026, 3, 1)),
        ("2026-03-15", date(2026, 3, 15)),
    ],
)
def testPeriodStartsAreComputed(period: str, expected: date) -> None:
    """기간의 시작을 정확히 짚어야 판정이 맞는다."""

    assert _temporalLowerBound(period) == expected


def testPlainDatesAreUnchangedByTheLowerBound() -> None:
    """날짜는 범위가 아니다. 시작과 끝이 같아야 한다."""

    assert _temporalLowerBound("2026-03-15") == _temporalUpperBound("2026-03-15")


@pytest.mark.parametrize("period", ["2026", "2025", "2026Q2", "2026H1"])
def testPartialCoverageOfAStartedPeriodPasses(period: str) -> None:
    """결함의 핵심이다. 이미 시작한 기간을 부분적으로 담는 것은 정상이다."""

    _validateTime(_time({"latestPeriod": period, "retrievedAt": _BOUNDARY}))


@pytest.mark.parametrize("period", ["2027", "FY2028", "2026Q4"])
def testCoverageOfANotYetStartedPeriodIsBlocked(period: str) -> None:
    """시작도 안 한 기간을 담았다면 그것은 미래를 본 것이다."""

    with pytest.raises(ValueError, match="knowledgeBoundary"):
        _validateTime(_time({"latestPeriod": period}))


@pytest.mark.parametrize("moment", ["2026-09-01", "2026-07-29"])
def testFutureInstantsAreStillBlocked(moment: str) -> None:
    """시점형 값의 판정은 그대로여야 한다. 이것을 잃으면 검사가 무의미해진다."""

    with pytest.raises(ValueError, match="knowledgeBoundary"):
        _validateTime(_time({"retrievedAt": moment}))

    with pytest.raises(ValueError, match="knowledgeBoundary"):
        _validateTime(_time(moment))


def testPastInstantsPass() -> None:
    """경계 이전 수집은 정상이다."""

    _validateTime(_time({"retrievedAt": "2026-01-15"}))
    _validateTime(_time("2026-01-15"))


def testSynthesisAxisBuildsEndToEnd() -> None:
    """실제로 죽던 공개 계약이 다시 도는지 본다. 단위 판정만으로는 못 잡는다."""

    import dartlab

    with dartlab.Company("005930") as company:
        product = company.analysis("종합평가")

    assert isinstance(product, dict)
