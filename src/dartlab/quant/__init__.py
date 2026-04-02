"""주가 기술적 분석 독립 엔진.

25개 기술적 지표, 9개 매매 신호, 종합 판단(강세/중립/약세).
dartlab.quant("005930") 또는 c.quant() 로 접근.

Usage::

    import dartlab

    dartlab.quant("005930")                    # 종합 판단
    dartlab.quant("005930", "indicators")      # 25개 지표 DataFrame
    dartlab.quant("005930", "signals")         # 최근 매매 신호
    dartlab.quant("005930", "beta")            # 시장 베타 + CAPM
    dartlab.quant("005930", "divergence")      # 재무-기술적 괴리 진단
    dartlab.quant("005930", "flags")           # 경고/기회 플래그
    dartlab.quant()                            # 가이드
"""

from __future__ import annotations

from dartlab.quant.analyzer import enrichWithIndicators, technicalVerdict

__all__ = ["Quant", "enrichWithIndicators", "technicalVerdict"]


class Quant:
    """주가 기술적 분석 독립 엔진.

    dartlab.quant("005930") 또는 c.quant() 로 접근.
    metric 없이 호출 시 종합 판단(verdict) 반환.
    """

    def __call__(self, stockCode=None, metric=None, **kwargs):
        """기술적 분석 실행.

        Args:
            stockCode: 종목코드 ("005930") 또는 ticker ("AAPL"). None이면 가이드.
            metric: "indicators", "signals", "beta", "divergence", "flags".
                    None이면 종합 판단(verdict).
            **kwargs: gather("price")에 전달할 추가 인자.

        Returns:
            dict, list, 또는 pl.DataFrame — metric에 따른 분석 결과.
        """
        if stockCode is None:
            return self._guide()

        ohlcv = self._fetchOHLCV(stockCode, **kwargs)
        if ohlcv is None or ohlcv.is_empty():
            return {"error": f"{stockCode} 주가 데이터 없음"}

        if metric == "indicators":
            return enrichWithIndicators(ohlcv)
        if metric == "signals":
            from dartlab.quant.extended import calcTechnicalSignals

            # Company 객체를 만들어서 전달 (캐시 공유)
            wrapper = _OHLCVWrapper(stockCode, ohlcv)
            return calcTechnicalSignals(wrapper)
        if metric == "beta":
            from dartlab.quant.extended import calcMarketBeta

            wrapper = _OHLCVWrapper(stockCode, ohlcv)
            return calcMarketBeta(wrapper)
        if metric == "divergence":
            from dartlab.quant.extended import calcFundamentalDivergence

            wrapper = _OHLCVWrapper(stockCode, ohlcv)
            return calcFundamentalDivergence(wrapper)
        if metric == "flags":
            from dartlab.quant.extended import calcMarketAnalysisFlags

            wrapper = _OHLCVWrapper(stockCode, ohlcv)
            return calcMarketAnalysisFlags(wrapper)

        # default: verdict
        return technicalVerdict(ohlcv)

    def _fetchOHLCV(self, stockCode, **kwargs):
        """gather("price")로 OHLCV 수집."""
        try:
            from dartlab.gather.entry import GatherEntry

            g = GatherEntry()
            return g("price", stockCode, **kwargs)
        except (ImportError, ValueError, TypeError, RuntimeError):
            return None

    def _guide(self):
        """metric 가이드 테이블."""
        import polars as pl

        rows = [
            {"metric": "verdict", "description": "종합 판단 (강세/중립/약세) + RSI/SMA/BB"},
            {"metric": "indicators", "description": "25개 기술적 지표 DataFrame"},
            {"metric": "signals", "description": "최근 매매 신호 이벤트"},
            {"metric": "beta", "description": "시장 베타 + CAPM + 해석"},
            {"metric": "divergence", "description": "재무-기술적 괴리 진단"},
            {"metric": "flags", "description": "기술적 경고/기회 플래그"},
        ]
        return pl.DataFrame(rows)


class _OHLCVWrapper:
    """OHLCV를 이미 보유한 경량 래퍼 — extended.py의 _fetchOHLCV 캐시 호환."""

    def __init__(self, stockCode: str, ohlcv):
        self.stockCode = stockCode
        self.currency = "KRW"
        self._cache = {"_quant_ohlcv": ohlcv}
