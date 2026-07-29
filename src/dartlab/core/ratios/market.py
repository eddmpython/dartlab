"""주식수와 시장가치가 필요한 재무비율 계산."""

from __future__ import annotations

from dartlab.core.ratios.common import _calcEbitdaValue
from dartlab.core.ratios.models import RatioResult


def _calcPerShare(result: RatioResult) -> None:
    """발행주식수가 있을 때 주당지표를 채운다."""
    shares = result.sharesOutstanding
    if not shares or shares <= 0:
        return

    if result.netIncomeTTM is not None:
        result.eps = round(result.netIncomeTTM / shares, 0)

    equity = result.ownersEquity if result.ownersEquity is not None else result.totalEquity
    if equity is not None:
        result.bps = round(equity / shares, 0)

    if result.dividendsPaid is not None and result.dividendsPaid != 0:
        result.dps = round(abs(result.dividendsPaid) / shares, 0)


def _calcValuation(result: RatioResult) -> None:
    """시가총액이 있을 때 시장가치 멀티플을 채운다."""
    marketCap = result.marketCap
    if marketCap is None:
        return

    if result.netIncomeTTM is not None and result.netIncomeTTM > 0:
        result.per = round(marketCap / result.netIncomeTTM, 2)
    if result.totalEquity is not None and result.totalEquity > 0:
        result.pbr = round(marketCap / result.totalEquity, 2)
    if result.revenueTTM is not None and result.revenueTTM > 0:
        result.psr = round(marketCap / result.revenueTTM, 2)

    ebitda = _calcEbitdaValue(result.operatingIncomeTTM, result.depreciationExpense)
    if result.netDebt is not None and ebitda is not None and ebitda > 0:
        result.evEbitda = round((marketCap + result.netDebt) / ebitda, 2)
