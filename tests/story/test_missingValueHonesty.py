"""결측을 그럴듯한 숫자로 메우던 자리에 대한 회귀.

네 자리에서 없는 값이 있는 값 행세를 했다.

부도확률을 못 구하면 0 이 들어가 "부도확률(1Y) 0.00%" 가 찍혔다. 결측을 하필 가장 안심되는
값으로 바꾼 것이고, 사람이 그대로 믿고 행동하는 숫자다. 종합 점수는 반대로 0/100 이 되어
가장 나쁜 회사로 보였다. 같은 파일의 다른 지표들은 이미 결측을 "-" 로 적고 있었다.

궤적 격차를 못 구하면 0 이 들어가 "격차 0%. 서사와 무관하게 안정" 이 붙었다. 바로 앞에 세
배 차이 나는 가격 셋을 나열해 놓고 결과가 서사와 무관하다고 말했다.

매출이 그대로일 때 영업 레버리지를 0 으로 뒀다. 정의되지 않는 자리인데 무조건 감쇠로
읽혀서 터미널 성장률을 0.3%p 깎았고, 근거로는 마진이 좋아진 숫자를 붙였다.

블록 빌더가 터지면 빈 목록만 남기고 아무 데도 기록하지 않았다. 데이터가 없어 빈 블록과
빌더가 터져 빈 블록이 구분되지 않아, 보고서가 완전한 얼굴로 나갔다.
"""

from __future__ import annotations

import pytest

from dartlab.story.blockMap import BlockMap
from dartlab.story.builders.credit import creditScoreBlock
from dartlab.story.narrative import _cwChainRevMargin, buildValuationImpact
from dartlab.story.registry import _makeSafeCall
from dartlab.story.storyTree import narrateStoryTree

pytestmark = [pytest.mark.unit]


def _creditText(data: dict) -> str:
    return " ".join(str(block.__dict__) for block in creditScoreBlock(data))


def testMissingDefaultProbabilityIsNotRenderedAsZero() -> None:
    """결측을 가장 안심되는 값으로 바꾸면 안 된다."""

    text = _creditText({"grade": "BBB", "gradeDescription": "보통"})

    assert "0.00%" not in text
    assert "미산출" in text


def testMissingScoreIsNotRenderedAsZero() -> None:
    """반대편도 같다. 결측이 최악 점수가 되어도 안 된다."""

    text = _creditText({"grade": "BBB", "gradeDescription": "보통"})

    assert "0.0/100" not in text


def testPresentValuesAreStillRendered() -> None:
    """정직하게 만드느라 있는 값을 지우면 안 된다."""

    text = _creditText({"grade": "AA", "gradeDescription": "우수", "score": 82.0, "pdEstimate": 0.35})

    assert "0.35%" in text
    assert "82.0/100" in text


def testMissingSpreadOmitsTheStabilityClaim() -> None:
    """모르는 것을 안정으로 읽으면 안 된다."""

    tree = {
        "probable": {"label": "유력", "dFV": 50000},
        "plausible": {"label": "개연", "dFV": 30000},
        "possible": {"label": "가능", "dFV": 90000},
        "summary": {"count": 3},
    }

    text = narrateStoryTree(tree)

    assert "서사와 무관하게 안정" not in text
    assert "격차" not in text


def testKnownSpreadStillSpeaks() -> None:
    """격차를 알면 그대로 말해야 한다."""

    tree = {
        "probable": {"label": "유력", "dFV": 50000},
        "plausible": {"label": "개연", "dFV": 48000},
        "possible": {"label": "가능", "dFV": 52000},
        "summary": {"count": 3, "spreadPct": 8.0},
    }

    assert "서사와 무관하게 안정" in narrateStoryTree(tree)


def testFlatRevenueLeavesOperatingLeverageUndefined() -> None:
    """나눌 것이 없으면 값이 없는 것이지 0 이 아니다."""

    chain = _cwChainRevMargin(lambda key: {"revenueGrowth": 0.0, "operatingMargin": 2.5}[key])

    assert chain is not None
    assert chain["direction"] == "undefined"
    assert chain["weight"] is None


def testUndefinedLeverageDoesNotCutTerminalGrowth() -> None:
    """정의되지 않은 값이 밸류에이션을 깎으면 안 된다."""

    chain = _cwChainRevMargin(lambda key: {"revenueGrowth": 0.0, "operatingMargin": 2.5}[key])

    impact = buildValuationImpact([chain])

    assert impact["terminalGrowthAdj"] == 0.0


def testRealDampeningStillCutsTerminalGrowth() -> None:
    """진짜 감쇠까지 못 잡으면 안 된다."""

    chain = _cwChainRevMargin(lambda key: {"revenueGrowth": 10.0, "operatingMargin": -1.0}[key])

    assert chain["direction"] == "dampen"
    assert buildValuationImpact([chain])["terminalGrowthAdj"] < 0


def testBlockBuildFailureIsRecorded() -> None:
    """빌더가 터진 것과 데이터가 없는 것은 다른 사건이다."""

    failures: list[dict] = []
    safe = _makeSafeCall(failures)

    def _brokenBuilder():
        raise KeyError("없는 계정")

    assert safe(_brokenBuilder) == []
    assert len(failures) == 1
    assert failures[0]["code"] == "BLOCK_BUILD_FAILED"
    assert failures[0]["builder"] == "_brokenBuilder"


def testOptionalSourceFailureIsRecordedWithoutBreakingStory() -> None:
    """스토리의 보조 source 고장은 lens gap으로 남고 다른 블록은 계속 만든다."""
    from dartlab.core.offlineGuard import OfflineViolation
    from dartlab.gather.types import SourceAttemptsExhaustedError, SourceUnavailableError

    failures: list[dict] = []
    safe = _makeSafeCall(failures)

    def _offlineBuilder():
        raise SourceAttemptsExhaustedError(
            "history",
            [
                ("naver", ExceptionGroup("connect", [OfflineViolation("blocked")])),
                ("fmp", SourceUnavailableError("key missing")),
            ],
        )

    assert safe(_offlineBuilder) == []
    assert failures == [
        {
            "code": "BLOCK_BUILD_FAILED",
            "builder": "_offlineBuilder",
            "error": "SourceAttemptsExhaustedError",
            "message": str(
                SourceAttemptsExhaustedError(
                    "history",
                    [
                        ("naver", ExceptionGroup("connect", [OfflineViolation("blocked")])),
                        ("fmp", SourceUnavailableError("key missing")),
                    ],
                )
            ),
        }
    ]


def testStoryDoesNotHideMixedAggregatedSourceFailure() -> None:
    """외부 source 집계에 섞인 로컬 오류는 story 경계에서도 전파한다."""
    from dartlab.gather.types import SourceAttemptsExhaustedError

    safe = _makeSafeCall([])

    def _brokenBuilder():
        raise SourceAttemptsExhaustedError("history", [("local", ValueError("invalid cached row"))])

    with pytest.raises(SourceAttemptsExhaustedError):
        safe(_brokenBuilder)


def testBlockMapCarriesTheFailures() -> None:
    """기록이 결과까지 따라와야 보고서가 결손을 감추지 않는다."""

    blockMap = BlockMap({"growth": []}, buildFailures=[{"code": "BLOCK_BUILD_FAILED"}])

    assert blockMap.buildFailures == [{"code": "BLOCK_BUILD_FAILED"}]
    assert BlockMap({"growth": []}).buildFailures == []
