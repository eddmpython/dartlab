"""타법인출자 현황 분석 모듈."""

from dartlab.providers.dart.docs.finance.subsidiary.pipeline import subsidiary
from dartlab.providers.dart.docs.finance.subsidiary.types import SubsidiaryInvestment, SubsidiaryResult

__all__ = ["subsidiary", "SubsidiaryInvestment", "SubsidiaryResult"]
