"""회사의 연혁 분석 모듈."""

from dartlab.providers.dart.docs.finance.companyHistory.pipeline import companyHistory
from dartlab.providers.dart.docs.finance.companyHistory.types import CompanyHistoryResult

__all__ = ["companyHistory", "CompanyHistoryResult"]
