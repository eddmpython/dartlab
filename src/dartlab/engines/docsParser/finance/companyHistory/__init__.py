"""회사의 연혁 분석 모듈."""

from dartlab.engines.docsParser.finance.companyHistory.pipeline import companyHistory
from dartlab.engines.docsParser.finance.companyHistory.types import CompanyHistoryResult

__all__ = ["companyHistory", "CompanyHistoryResult"]
