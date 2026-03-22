"""타법인출자 현황 분석 모듈."""

from dartlab.engines.company.dart.docs.finance.investmentInOther.pipeline import investmentInOther
from dartlab.engines.company.dart.docs.finance.investmentInOther.types import InvestmentInOtherResult

__all__ = ["investmentInOther", "InvestmentInOtherResult"]
