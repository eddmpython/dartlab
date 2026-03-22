"""자본금 변동 분석 모듈."""

from dartlab.engines.company.dart.docs.finance.capitalChange.pipeline import capitalChange
from dartlab.engines.company.dart.docs.finance.capitalChange.types import CapitalChangeResult

__all__ = ["capitalChange", "CapitalChangeResult"]
