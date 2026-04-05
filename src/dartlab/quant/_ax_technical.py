"""기존 기술적 분석 코드를 축 인터페이스로 래핑.

indicators, signals, verdict, beta, divergence를 새 축 체계에 연결.
기존 analyzer.py, extended.py의 함수를 그대로 호출한다.
"""

from __future__ import annotations

from typing import Any

from dartlab.quant._helpers import fetch_ohlcv


class _OHLCVWrapper:
    """OHLCV를 이미 보유한 경량 래퍼 — extended.py의 _fetchOHLCV 캐시 호환."""

    def __init__(self, stockCode: str, ohlcv, market: str = "KR"):
        self.stockCode = stockCode
        self.currency = "KRW" if market == "KR" else "USD"
        self._cache = {"_quant_ohlcv": ohlcv}


def _get_ohlcv(stockCode: str, **kwargs):
    """OHLCV fetch + 검증."""
    ohlcv = fetch_ohlcv(stockCode, **kwargs)
    if ohlcv is None or ohlcv.is_empty():
        return None, {"error": f"{stockCode} 주가 데이터 없음"}
    return ohlcv, None


# ── 축 함수들 ────────────────────────────────────────────


def analyze_indicators(stockCode: str, **kwargs: Any) -> Any:
    """45개 기술적 지표 DataFrame."""
    ohlcv, err = _get_ohlcv(stockCode, **kwargs)
    if err:
        return err
    from dartlab.quant.analyzer import enrichWithIndicators

    return enrichWithIndicators(ohlcv)


def analyze_signals(stockCode: str, **kwargs: Any) -> Any:
    """최근 매매 신호."""
    ohlcv, err = _get_ohlcv(stockCode, **kwargs)
    if err:
        return err
    from dartlab.quant._helpers import resolve_market
    from dartlab.quant.extended import calcTechnicalSignals

    market = resolve_market(stockCode, kwargs.pop("market", "auto"))
    wrapper = _OHLCVWrapper(stockCode, ohlcv, market)
    return calcTechnicalSignals(wrapper)


def analyze_verdict(stockCode: str, **kwargs: Any) -> dict:
    """종합 기술적 판단."""
    ohlcv, err = _get_ohlcv(stockCode, **kwargs)
    if err:
        return err
    from dartlab.quant.analyzer import technicalVerdict

    return technicalVerdict(ohlcv)


def analyze_beta(stockCode: str, **kwargs: Any) -> dict:
    """시장 베타 + CAPM."""
    ohlcv, err = _get_ohlcv(stockCode, **kwargs)
    if err:
        return err
    from dartlab.quant._helpers import resolve_market
    from dartlab.quant.extended import calcMarketBeta

    market = resolve_market(stockCode, kwargs.pop("market", "auto"))
    wrapper = _OHLCVWrapper(stockCode, ohlcv, market)
    return calcMarketBeta(wrapper)


def analyze_divergence(stockCode: str, **kwargs: Any) -> dict:
    """재무-기술적 괴리 진단."""
    ohlcv, err = _get_ohlcv(stockCode, **kwargs)
    if err:
        return err
    from dartlab.quant._helpers import resolve_market
    from dartlab.quant.extended import calcFundamentalDivergence

    market = resolve_market(stockCode, kwargs.pop("market", "auto"))
    wrapper = _OHLCVWrapper(stockCode, ohlcv, market)
    return calcFundamentalDivergence(wrapper)
