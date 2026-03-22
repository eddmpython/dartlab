"""우발부채·채무보증·소송 분석 모듈."""

from dartlab.engines.company.dart.docs.finance.contingentLiability.pipeline import contingentLiability
from dartlab.engines.company.dart.docs.finance.contingentLiability.types import ContingentLiabilityResult

__all__ = ["contingentLiability", "ContingentLiabilityResult"]
