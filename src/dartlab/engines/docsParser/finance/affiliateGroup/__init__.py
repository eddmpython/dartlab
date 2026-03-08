"""계열회사 현황 분석 모듈."""

from dartlab.engines.docsParser.finance.affiliateGroup.pipeline import affiliateGroup
from dartlab.engines.docsParser.finance.affiliateGroup.types import AffiliateGroupResult

__all__ = ["affiliateGroup", "AffiliateGroupResult"]
