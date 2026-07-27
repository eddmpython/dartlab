"""팩터 종합순위 정렬 방향 회귀.

각 factor 순위를 `argsort(argsort(-x))` 로 만들었기 때문에 가장 좋은 종목이 0 을 받고
종합점수도 0 에 가깝다. 그런데 종합점수를 내림차순으로 정렬해 왔다. 그래서 가장 나쁜
종목이 1 위로 올라가 "상위 50 종목" 맨 앞에 섰다.

부호 하나가 뒤집힌 것이라 결과가 이상해 보이지도 않는다. 표는 정상적으로 채워지고 순위도
1 부터 붙는다. 다만 내용이 정확히 반대다. 공개 문서의 예제가 이 축을 그대로 안내한다.

여기서 고정하는 것은 "좋은 회사가 위에 온다" 하나다.
"""

from __future__ import annotations

import numpy as np


def _composite(margins: np.ndarray, roas: np.ndarray, debts: np.ndarray) -> np.ndarray:
    """구현과 같은 방식으로 종합점수를 만든다. 0 이 최고다."""

    n = len(margins)
    marginRank = np.argsort(np.argsort(-margins)) / max(n - 1, 1)
    roaRank = np.argsort(np.argsort(-roas)) / max(n - 1, 1)
    debtRank = np.argsort(np.argsort(debts)) / max(n - 1, 1)
    return (marginRank + roaRank + debtRank) / 3


def testCompositeIsZeroForTheBestCompany() -> None:
    """왜 방향이 중요한지부터 못 박는다. 종합점수는 낮을수록 좋다."""

    composites = _composite(
        np.array([30.0, 10.0, -5.0]),
        np.array([20.0, 5.0, -3.0]),
        np.array([10.0, 80.0, 400.0]),
    )

    assert composites[0] == 0.0
    assert composites[2] == 1.0


def testAscendingSortPutsTheBestCompanyFirst() -> None:
    """구현이 쓰는 정렬 방향이 이 성질과 맞아야 한다."""

    names = ["GOOD", "MID", "BAD"]
    composites = _composite(
        np.array([30.0, 10.0, -5.0]),
        np.array([20.0, 5.0, -3.0]),
        np.array([10.0, 80.0, 400.0]),
    )

    order = np.argsort(composites)

    assert names[order[0]] == "GOOD"
    assert names[order[-1]] == "BAD"


def testRankingModuleSortsAscending() -> None:
    """구현이 내림차순으로 돌아가면 다시 최악이 1 위가 된다."""

    import inspect

    from dartlab.quant.factor import ranking

    source = inspect.getsource(ranking.calcRanking)

    assert "order = np.argsort(composites)" in source
    assert "order = np.argsort(-composites)" not in source


def testReportedScoreRisesWithQuality() -> None:
    """사람이 읽는 점수는 높을수록 좋아야 한다. 내부 표현과 반대라 뒤집어 내보낸다."""

    composites = _composite(
        np.array([30.0, 10.0, -5.0]),
        np.array([20.0, 5.0, -3.0]),
        np.array([10.0, 80.0, 400.0]),
    )
    reported = [round(1.0 - float(value), 4) for value in composites]

    assert reported[0] > reported[1] > reported[2]
    assert reported[0] == 1.0
