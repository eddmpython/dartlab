"""대주주 거래 분석 모듈."""

from dartlab.engines.company.dart.docs.finance.relatedPartyTx.pipeline import relatedPartyTx
from dartlab.engines.company.dart.docs.finance.relatedPartyTx.types import RelatedPartyTxResult

__all__ = ["relatedPartyTx", "RelatedPartyTxResult"]
