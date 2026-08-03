"""문서 예제가 실제로 도는지에 대한 회귀.

docstring 과 Skill OS spec 은 사람에게만 읽히는 글이 아니다. capability 카탈로그로 그대로
나가서 다른 도구가 복사해 실행한다. 그런데 자유 조립 예제가 쓰는 `b["margin"]` 과
`b["cashflow"]` 는 카탈로그에 없는 키였다. 복사하면 KeyError 다. 진짜 키는 `marginTrend`
와 `cashFlowOverview` 다.

보고서 관점도 열두 개를 등록해 놓고 문서는 열한 개라 적었고, 빠진 `dashboard` 는 렌즈
지도에도 없어서 fallback 으로 렌즈 하나짜리로 조용히 내려앉았다. 일부러 좁힌 `audit` 과
등록을 빠뜨린 것이 결과만 봐서는 구분되지 않았다.
"""

from __future__ import annotations

import pytest

from dartlab.story import reportTypes
from dartlab.story.catalog import resolveKey
from dartlab.story.lensProducts import _REPORT_ENGINES, enginesForReportType

pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize("key", ["growth", "marginTrend", "cashFlowOverview"])
def testDocumentedBlockKeysResolve(key: str) -> None:
    """문서가 예제로 내보이는 키는 카탈로그에 있어야 한다."""

    assert resolveKey(key) is not None


@pytest.mark.parametrize("key", ["margin", "cashflow"])
def testTheOldExampleKeysAreStillAbsent(key: str) -> None:
    """예제를 고친 이유를 못 박는다. 이 키들은 실재하지 않는다."""

    assert resolveKey(key) is None


def testEveryReportTypeHasAnExplicitLensMap() -> None:
    """fallback 이 등록 누락을 삼키면 좁힌 것과 빠뜨린 것이 구분되지 않는다."""

    missing = sorted(set(reportTypes.REPORT_TYPES) - set(_REPORT_ENGINES))

    assert not missing, f"렌즈 지도에 없는 reportType: {missing}"


def testDashboardGetsMoreThanOneLens() -> None:
    """스냅샷 계열이 렌즈 하나로 내려앉던 자리다."""

    assert len(enginesForReportType("dashboard")) > 1


def testInvestmentReportUsesEveryDecisionLens() -> None:
    assert enginesForReportType("investment") == ("analysis", "industry", "macro")
    assert len(reportTypes.REPORT_TYPES["investment"].focusQuestions) >= 5
    assert reportTypes.REPORT_TYPES["investment"].sectionOrder == ("종합평가", "수익구조", "현금흐름")


def testNarrowReportTypesStayNarrow() -> None:
    """일부러 좁힌 것까지 넓히면 안 된다."""

    assert enginesForReportType("audit") == ("analysis",)
