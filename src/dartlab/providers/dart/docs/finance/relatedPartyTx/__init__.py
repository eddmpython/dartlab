"""대주주 거래 분석 모듈."""

from dartlab.providers.dart.docs.finance.relatedPartyTx.pipeline import relatedPartyTx
from dartlab.providers.dart.docs.finance.relatedPartyTx.types import RelatedPartyTxResult

__all__ = ["relatedPartyTx", "RelatedPartyTxResult"]
