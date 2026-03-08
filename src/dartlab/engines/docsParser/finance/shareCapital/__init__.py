"""주식의 총수 분석 모듈."""

from dartlab.engines.docsParser.finance.shareCapital.pipeline import shareCapital
from dartlab.engines.docsParser.finance.shareCapital.types import ShareCapitalResult

__all__ = ["shareCapital", "ShareCapitalResult"]
