"""주가 기술적 분석 — analysis("quant") 축의 내부 구현.

독립 엔진이 아님. c.analysis("quant", "기술적분석")으로 접근.
내부적으로 analyzer.py, indicators.py, signals.py를 제공.
"""

from __future__ import annotations

from dartlab.quant.analyzer import enrichWithIndicators, technicalVerdict

__all__ = ["enrichWithIndicators", "technicalVerdict"]
