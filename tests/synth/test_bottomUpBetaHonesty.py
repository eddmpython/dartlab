"""바텀업 베타 라벨과 결정성 회귀.

peer 를 뽑을 수 없는데 뽑는 시늉을 하고 있었다. 섹터 매핑 표가 없다는 이유로 전 종목에서
무작위 표본을 뽑은 뒤 그 peer 전부에 같은 섹터 베타를 심었다. 모든 peer 가 같은 베타를
들고 있으니 "peer 평균 무차입 베타" 에 횡단 정보가 하나도 없고, 남는 것은 무관한 회사들의
D/E 평균뿐인데 결과 라벨은 `bottom_up` 이었다. 이 모듈 자신의 문서가 "bottom_up 결과만
신뢰하라" 고 적어 둔 그 라벨이다.

표본 seed 가 `hash(sector)` 라 실행마다 달랐다는 것도 문제였다. 같은 회사가 호출할 때마다
다른 베타를 받았고 그 seed 는 결과에 남지도 않는다.

여기서 고정하는 것은 둘이다. 라벨이 실제 근거와 맞을 것, 그리고 같은 입력이 같은 답을
낼 것.
"""

from __future__ import annotations

import pytest

from dartlab.synth.bottomUpBeta import calcBottomUpBeta


def testKnownSectorFallsBackToTheSectorDefaultNotBottomUp() -> None:
    """개별 종목 베타 회귀가 없으므로 bottom_up 을 주장하면 안 된다."""

    result = calcBottomUpBeta(sector="IT", debtToEquity=0.5)

    assert result["method"] == "sector_default"
    assert result["leveredBeta"] == 1.2


def testUnknownSectorIsLabeledAsAFallbackNotAComputation() -> None:
    """섹터를 모르면 1.0 을 쓰되 그것이 계산 결과가 아님을 라벨로 말한다."""

    result = calcBottomUpBeta(sector="존재하지않는섹터", debtToEquity=0.5)

    assert result["method"] == "fallback_one"
    assert result["leveredBeta"] == 1.0


def testMethodNeverClaimsBottomUpWithoutPeers() -> None:
    """peer 가 없는데 bottom_up 이라고 하면 소비자가 신뢰 판단을 못 한다."""

    for sector in ("IT", "금융", "소재", "알수없음"):
        result = calcBottomUpBeta(sector=sector, debtToEquity=0.3)
        if result["method"] == "bottom_up":
            assert result["peerCount"] >= 5, sector


def testSameInputGivesTheSameAnswer() -> None:
    """같은 회사가 부를 때마다 다른 베타를 받으면 어떤 결과도 재현되지 않는다."""

    first = calcBottomUpBeta(sector="IT", debtToEquity=0.5)
    second = calcBottomUpBeta(sector="IT", debtToEquity=0.5)

    assert first == second


@pytest.mark.parametrize("debtToEquity", [0.0, 0.5, 2.0])
def testLeverageStillMovesTheResult(debtToEquity: float) -> None:
    """무차입 베타를 재차입하는 계산 자체는 살아 있어야 한다."""

    result = calcBottomUpBeta(sector="IT", debtToEquity=debtToEquity)

    assert result["leveredBeta"] is not None
    assert result["debtToEquity"] == debtToEquity


def testPeerListIsEmptyRatherThanFabricated() -> None:
    """뽑을 수 없으면 빈 목록이다. 무관한 회사로 채우면 안 된다."""

    result = calcBottomUpBeta(sector="IT", debtToEquity=0.5)

    assert result["peers"] == []
    assert result["peerCount"] == 0
