"""Strategy DSL — boolean rule + vectorized backtest + walk-forward + CPCV.

사용자가 가설을 boolean expression 으로 컴포즈하고 (가중치 박지 마라!) 백테스트로
검증하는 폐쇄루프. 시총 횡단면 의존 0, 외부 라이브러리 0 (numpy + polars + scipy.norm).

핵심:
    Signal — key→numpy array 컨테이너 (getattr 접근)
    Rule   — entry/exit boolean expression + sizing/stop 명시 주입
    BacktestResult — equity/returns/trades + sharpe/sortino/mdd/dsr/pbo
    walkForward: refit 가능한 OOS 검증
    cpcv: 고정 룰 CPCV path 구조 temporal stress (OOS 아님)

사용 예:
    >>> import dartlab
    >>> c = dartlab.Company("005930")
    >>> from dartlab.quant.strategy import Signal, Rule
    >>> s = Signal()
    >>> sig_df = c.quant("신호", series=True)
    >>> s.add("rsi_oversold", sig_df["rsiSignal"] == 1)
    >>> rule = Rule.entry(s.rsi_oversold).exit(...)
    >>> bt = c.quant("backtest", rule=rule, nTrials=1)
    >>> print(f"Sharpe={bt.sharpe:.2f} DSR={bt.dsr:.2f}")
"""

from .backtest import BacktestResult, cpcv, multiAssetBacktest, vectorBacktest, walkForward
from .metrics import (
    dsr,
    expectancy,
    exposure,
    mdd,
    pbo,
    profitFactor,
    sharpe,
    sortino,
    turnover,
    winrate,
)
from .presets import STYLE_KR_ONLY, STYLE_REGISTRY, resolveStyle
from .rule import Rule
from .signal import Signal

__all__ = [
    "Signal",
    "Rule",
    "BacktestResult",
    "vectorBacktest",
    "walkForward",
    "cpcv",
    "multiAssetBacktest",
    "STYLE_REGISTRY",
    "STYLE_KR_ONLY",
    "resolveStyle",
    # metrics
    "sharpe",
    "sortino",
    "mdd",
    "winrate",
    "profitFactor",
    "expectancy",
    "turnover",
    "exposure",
    "dsr",
    "pbo",
]
