"""L0 기간 표기 회귀.

`resolveLatestPeriod` 는 이 모듈이 스스로 만드는 표준형('2024-Q1')에서 최신 기간을
틀리게 골랐다. 대시가 있으면 'Q1' 을 정수로 넘겨 예외가 나고, 그 예외를 (0,0,0) 으로
삼키는 바람에 모든 키가 같아져 `max` 가 입력 첫 원소를 돌려줬다. 유일한 호출부가 set 을
list 로 넘기므로 사용자에게 보이는 `dataAsOf.latestPeriod` 가 실행마다 달랐다.

여기 고정하는 것은 두 표기가 같은 답을 내는 것, 그리고 입력 순서에 흔들리지 않는 것이다.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.core.utils.period import (
    dropPeriodsAfter,
    formatPeriod,
    parseAsOfPeriod,
    resolveLatestPeriod,
)


def testStandardFormatFromThisModuleResolvesCorrectly() -> None:
    """이 모듈이 만드는 표기를 이 모듈이 못 읽으면 안 된다."""

    periods = [formatPeriod(2024, 1), formatPeriod(2025, 4), formatPeriod(2023, 2)]

    assert resolveLatestPeriod(periods) == formatPeriod(2025, 4)


def testDashedAndUndashedAgree() -> None:
    """대시 유무는 표기 차이일 뿐이라 판정이 달라지면 안 된다."""

    assert resolveLatestPeriod(["2024-Q1", "2025-Q4", "2023-Q2"]) == "2025-Q4"
    assert resolveLatestPeriod(["2024Q1", "2025Q4", "2023Q2"]) == "2025Q4"


def testResultDoesNotDependOnInputOrder() -> None:
    """호출부가 set 을 list 로 넘긴다. 순서에 흔들리면 답이 실행마다 바뀐다."""

    periods = ["2024-Q1", "2025-Q4", "2023-Q2"]
    expected = "2025-Q4"

    assert resolveLatestPeriod(periods) == expected
    assert resolveLatestPeriod(list(reversed(periods))) == expected
    assert resolveLatestPeriod([periods[1], periods[2], periods[0]]) == expected


def testQuarterBeatsAnnualInTheSameYear() -> None:
    """같은 해면 분기가 연간보다 뒤다. 연간이 이기면 최신 분기가 가려진다."""

    assert resolveLatestPeriod(["2025", "2025-Q4"]) == "2025-Q4"


def testLaterYearWinsOverEarlierQuarter() -> None:
    """연도가 먼저다. 분기 숫자가 커도 이전 연도가 이기면 안 된다."""

    assert resolveLatestPeriod(["2024-Q4", "2025-Q1"]) == "2025-Q1"


@pytest.mark.parametrize("periods", [[], None, [None, ""], ["", None]])
def testEmptyInputResolvesToNothing(periods: object) -> None:
    """고를 것이 없으면 None 이다."""

    assert resolveLatestPeriod(periods) is None


def testNonPeriodStringsDoNotWinOverRealPeriods() -> None:
    """알 수 없는 표기가 최신으로 뽑히면 위층이 엉뚱한 기간을 인용한다."""

    assert resolveLatestPeriod(["알수없음", "2025-Q3"]) == "2025-Q3"


def testAsOfReadsTheThreeShapesUsersActuallyType() -> None:
    """붙여 쓴 분기, ISO 날짜, 연도 셋을 다 읽어야 한다."""

    assert parseAsOfPeriod("2024Q1") == (2024, 1)
    assert parseAsOfPeriod("2024q3") == (2024, 3)
    assert parseAsOfPeriod("2024-06-30") == (2024, 2)
    assert parseAsOfPeriod("2024") == (2024, None)


def testAsOfRefusesWhatItCannotRead() -> None:
    """못 읽은 것을 연도로 넘겨짚으면 멀쩡한 표가 빈다."""

    assert parseAsOfPeriod("garbage") == (None, None)
    assert parseAsOfPeriod("") == (None, None)
    assert parseAsOfPeriod("20240630") == (None, None)


def testFutureColumnsAreDropped() -> None:
    """as-of 이후 기간이 남으면 그 답은 그때 알 수 없던 것을 본 답이다."""

    df = pl.DataFrame({"항목": ["매출액"], "2023": [1], "2024Q1": [2], "2024Q3": [3], "2025": [4]})

    kept = dropPeriodsAfter(df, "2024Q1").columns

    assert kept == ["항목", "2023", "2024Q1"]


def testUnreadableAsOfDropsNothing() -> None:
    """as-of 를 못 읽었다고 표를 비우면 안 된다. 그것은 조용한 자료 손실이다."""

    df = pl.DataFrame({"2023": [1], "2024": [2]})

    assert dropPeriodsAfter(df, "garbage").columns == ["2023", "2024"]


def testYearOnlyAsOfKeepsEveryQuarterOfThatYear() -> None:
    """연도만 준 as-of 는 그 해 전체를 뜻한다. 분기를 임의로 좁히지 않는다."""

    df = pl.DataFrame({"2023": [1], "2024Q1": [2], "2024Q4": [3], "2025Q1": [4]})

    assert dropPeriodsAfter(df, "2024").columns == ["2023", "2024Q1", "2024Q4"]


def testBothProvidersShareTheOneGuard() -> None:
    """dart 와 edgar 가 각자 규칙을 가지면 한쪽 시장만 조용히 미래를 본다."""

    from dartlab.providers.dart.company import _filterPeriodColumnsByAsOf as dartFilter
    from dartlab.providers.edgar.company import _filterPeriodColumnsByAsOf as edgarFilter

    assert dartFilter is dropPeriodsAfter
    assert edgarFilter is dropPeriodsAfter
