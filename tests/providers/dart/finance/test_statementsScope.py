"""받아 놓고 무시하던 재무제표 인자에 대한 회귀.

`statements()` 가 `scope` 와 `ifrsOnly` 를 서명에 두고 본문에서 한 번도 안 읽었다. 그래서
`statements(code, scope="separate")` 가 연결 재무제표를 돌려주면서 결과에는 "consolidated"
라고 적었다. 삼성전자로 재면 별도 매출 133 조 자리에 연결 매출 201 조가 나온다.

docstring 은 그 반대를 약속하고 있었다. "별도 재무제표 강제 -> statements(code,
scope='separate')" 가 Guide 섹션의 권장 사용법으로 적혀 있었고, 그 문서는 capability
카탈로그로 나가 다른 도구가 그대로 따라 쓴다.

배선은 이미 있었다. pivot 이 `fsDivPref` 로 연결과 별도를 구분해 읽는데 그 인자를 안
넘기고 있었을 뿐이다. 없는 기능을 지어낸 것이 아니라 끊긴 선을 이은 것이다.
"""

from __future__ import annotations

import pytest

from dartlab.providers.dart.finance.statements import _isIfrsEraKey, statements

SAMSUNG = "005930"


@pytest.fixture(scope="module")
def consolidated():
    return statements(SAMSUNG, scope="consolidated")


@pytest.fixture(scope="module")
def separate():
    return statements(SAMSUNG, scope="separate")


@pytest.mark.realData
def testSeparateScopeIsReportedHonestly(separate) -> None:
    """별도를 달라고 했으면 결과도 별도라고 적어야 한다."""

    assert separate is not None
    assert separate.scope == "separate"


@pytest.mark.realData
def testConsolidatedIsStillTheDefault(consolidated) -> None:
    """기본값을 바꾸면 기존 호출자의 숫자가 통째로 달라진다."""

    assert consolidated is not None
    assert consolidated.scope == "consolidated"
    assert statements(SAMSUNG).scope == "consolidated"


@pytest.mark.realData
def testSeparateReturnsDifferentNumbers(consolidated, separate) -> None:
    """결함의 핵심이다. 라벨만 바뀌고 숫자가 같으면 고친 것이 아니다."""

    consolidatedSales = consolidated.IS.row(0)
    separateSales = separate.IS.row(0)

    assert consolidatedSales[0] == separateSales[0] == "sales"
    assert consolidatedSales[1:4] != separateSales[1:4]


@pytest.mark.parametrize(
    ("key", "expected"),
    [("2009", False), ("2010", False), ("2011", True), ("2016", True), ("2024Q1", True)],
)
def testIfrsEraBoundary(key: str, expected: bool) -> None:
    """K-IFRS 의무 적용은 2011 년이다. 그 이전은 계정 구조가 다른 K-GAAP 이다."""

    assert _isIfrsEraKey(key) is expected


def testUnparseableKeyIsKept() -> None:
    """연도를 못 읽는다고 자료를 버리면, 거르려던 것보다 큰 손실이 난다."""

    assert _isIfrsEraKey("알 수 없음") is True


@pytest.mark.realData
def testIfrsFilterDoesNotDropModernYears() -> None:
    """거르기가 과하면 멀쩡한 최근 연도까지 사라진다."""

    filtered = statements(SAMSUNG, ifrsOnly=True)
    unfiltered = statements(SAMSUNG, ifrsOnly=False)

    assert filtered is not None
    assert unfiltered is not None
    assert filtered.nYears > 0
    assert filtered.nYears <= unfiltered.nYears
