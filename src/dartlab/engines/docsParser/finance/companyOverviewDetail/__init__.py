"""회사의 개요 분석 모듈."""

from dartlab.engines.docsParser.finance.companyOverviewDetail.pipeline import companyOverviewDetail
from dartlab.engines.docsParser.finance.companyOverviewDetail.types import CompanyOverviewDetailResult

__all__ = ["companyOverviewDetail", "CompanyOverviewDetailResult"]
