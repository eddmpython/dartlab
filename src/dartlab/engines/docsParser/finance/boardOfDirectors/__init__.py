"""이사회 분석 모듈."""

from dartlab.engines.docsParser.finance.boardOfDirectors.pipeline import boardOfDirectors
from dartlab.engines.docsParser.finance.boardOfDirectors.types import BoardResult

__all__ = ["boardOfDirectors", "BoardResult"]
