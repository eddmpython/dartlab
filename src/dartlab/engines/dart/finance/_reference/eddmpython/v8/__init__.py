"""FinanceSearch v8 - 온톨로지 기반 계정 매핑 시스템"""

from .parquetMapper import MappingResult, ParquetMapper
from .search import FinanceSearch
from .standardMapping import StandardMapper
from .synonymLearner import SynonymLearner

# Optional: OntologyMapper requires owlready2
try:
    from .ontologyBuilder import OntologyBuilder
    from .ontologyMapper import OntologyMapper

    __all__ = [
        "FinanceSearch",
        "StandardMapper",
        "SynonymLearner",
        "OntologyMapper",
        "ParquetMapper",
        "MappingResult",
        "OntologyBuilder",
    ]
except ImportError:
    __all__ = ["FinanceSearch", "StandardMapper", "SynonymLearner", "ParquetMapper", "MappingResult"]
