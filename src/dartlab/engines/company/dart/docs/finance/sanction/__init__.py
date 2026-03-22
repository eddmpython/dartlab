"""제재 현황 분석 모듈."""

from dartlab.engines.company.dart.docs.finance.sanction.pipeline import sanction
from dartlab.engines.company.dart.docs.finance.sanction.types import SanctionResult

__all__ = ["sanction", "SanctionResult"]
