"""타법인출자 현황 분석 모듈."""

from dartlab.engines.docsParser.finance.investmentInOther.pipeline import investmentInOther
from dartlab.engines.docsParser.finance.investmentInOther.types import InvestmentInOtherResult

__all__ = ["investmentInOther", "InvestmentInOtherResult"]
