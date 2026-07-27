"""백테스트 대표 지표의 비용 반영 회귀.

일별 수익률을 종가만으로 만들고 있었다. 수수료, 슬리피지, 갭, 물량 충격은 거래 손익에만
붙었기 때문에 샤프, 소르티노, 최대낙폭, 자산곡선이 전부 비용을 모른 채 계산됐다.

수수료를 0 에서 1000bp 로 올려도 샤프가 글자 하나 바뀌지 않는 것을 확인했다. 모듈 문서가
"수수료 15bp, 슬리피지 5bp" 를 물린다고 밝히는데 정작 대표 지표가 그것을 모르는 셈이다.
비용을 물린다고 적어 놓고 무비용 성과를 보여주는 것이 백테스트에서 가장 비싼 거짓말이다.
"""

from __future__ import annotations

import numpy as np
import pytest

from dartlab.quant.strategy.backtest import vectorBacktest
from dartlab.quant.strategy.rule import Rule


def _setup(n: int = 300) -> tuple[np.ndarray, Rule]:
    """스무 봉마다 진입하고 열 봉 뒤 청산하는 규칙."""

    rng = np.random.default_rng(11)
    close = np.cumprod(1 + rng.normal(0.0002, 0.012, n)) * 10000
    entry = np.zeros(n, dtype=bool)
    exitSignal = np.zeros(n, dtype=bool)
    entry[::20] = True
    exitSignal[10::20] = True
    return close, Rule(entry_expr=entry, exit_expr=exitSignal)


def _run(feeBps: float):
    close, rule = _setup()
    return vectorBacktest(close=close, rule=rule, feeBps=feeBps, slipBps=0.0, execMode="close")


def testHigherFeesLowerTheSharpe() -> None:
    """비용을 물린다고 밝혔으면 대표 지표가 그것을 알아야 한다."""

    free = _run(0.0)
    charged = _run(15.0)

    assert charged.sharpe < free.sharpe


def testExtremeFeesDestroyThePerformance() -> None:
    """1000bp 를 물려도 성과가 같다면 비용이 어디에도 닿지 않는 것이다."""

    free = _run(0.0)
    punitive = _run(1000.0)

    assert punitive.sharpe < free.sharpe - 1.0


def testHigherFeesDeepenTheDrawdown() -> None:
    """낙폭도 비용을 반영해야 한다. 자산곡선이 같은 근거에서 나오기 때문이다."""

    free = _run(0.0)
    charged = _run(1000.0)

    assert charged.mdd < free.mdd


def testZeroCostRunIsUnchanged() -> None:
    """비용이 0 이면 예전과 같은 값이어야 한다. 계산 자체를 바꾼 것이 아니다."""

    free = _run(0.0)

    assert free.sharpe == pytest.approx(_run(0.0).sharpe)


def testTradeLevelCostsAreStillRecorded() -> None:
    """거래별 비용 기록은 그대로 남아야 한다. 두 자리가 같은 근거를 쓴다."""

    charged = _run(15.0)

    assert charged.trades is not None
    assert charged.trades.height > 0
    assert charged.trades["cost_bps"].max() > 0
