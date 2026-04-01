"""주가 기술적 분석 엔진 — 25개 지표 + 9개 신호 + 종합 판단.

tradix에서 이식한 벡터화 NumPy 엔진. gather("price") OHLCV와 연결.

사용법::

    import dartlab

    # 종합 판단
    dartlab.quant("005930")                # 삼성전자 기술적 분석
    dartlab.quant("005930", "verdict")     # 강세/중립/약세만

    # 지표 DataFrame
    dartlab.quant("005930", "indicators")  # 25개 지표 전체

    # Company 연결
    c = dartlab.Company("005930")
    c.quant()                              # 종합 판단
"""

from __future__ import annotations

from typing import Any

import polars as pl

from dartlab.quant.analyzer import enrichWithIndicators, technicalVerdict

__all__ = ["enrichWithIndicators", "technicalVerdict"]


class Quant:
    """기술적 분석 진입점 — scan/gather와 동일한 호출 패턴."""

    def __call__(
        self,
        stockCode: str | None = None,
        metric: str | None = None,
        **kwargs: Any,
    ) -> pl.DataFrame | dict | Any:
        """기술적 분석 실행.

        Args:
            stockCode: 종목코드. None이면 가이드 반환.
            metric: "verdict" | "indicators" | None(=verdict).

        Returns:
            가이드 DataFrame, 판단 dict, 또는 지표 DataFrame.
        """
        if stockCode is None:
            return self._guide()

        ohlcv = self._fetchOHLCV(stockCode, **kwargs)
        if ohlcv is None or ohlcv.is_empty():
            return {"error": f"{stockCode} 주가 데이터 없음"}

        if metric == "indicators":
            return enrichWithIndicators(ohlcv)

        if metric == "beta":
            from dartlab.quant.analyzer import _calcBeta, _fetchBenchmark

            market = _fetchBenchmark()
            if market is None or market.is_empty():
                return {"error": "시장 지수 수집 실패"}
            beta = _calcBeta(ohlcv, market)
            return beta if beta else {"error": "베타 계산 불가 (데이터 부족)"}

        return technicalVerdict(ohlcv)

    def _fetchOHLCV(self, stockCode: str, **kwargs: Any) -> pl.DataFrame | None:
        """gather("price")로 OHLCV 가져오기."""
        from dartlab.gather.entry import GatherEntry

        g = GatherEntry()
        try:
            return g("price", stockCode, **kwargs)
        except Exception:
            return None

    def _guide(self) -> pl.DataFrame:
        """가이드 DataFrame."""
        rows = [
            {"metric": "verdict", "description": "종합 판단 (강세/중립/약세) + RSI/SMA/BB + 상대강도 + 베타"},
            {"metric": "indicators", "description": "45개 기술적 지표 전체 (OHLCV + 지표 DataFrame)"},
            {"metric": "beta", "description": "실측 베타 + CAPM 기대수익률 (KOSPI 대비)"},
        ]
        return pl.DataFrame(rows)

    def __repr__(self) -> str:
        return (
            "Quant — 기술적 분석 엔진 (25개 지표, 9개 신호)\n"
            "  quant('005930')              → 종합 판단\n"
            "  quant('005930', 'indicators') → 25개 지표 DataFrame"
        )
