"""대주주 거래 분석 모듈."""

from dartlab.engines.docsParser.finance.relatedPartyTx.pipeline import relatedPartyTx
from dartlab.engines.docsParser.finance.relatedPartyTx.types import RelatedPartyTxResult

__all__ = ["relatedPartyTx", "RelatedPartyTxResult"]
