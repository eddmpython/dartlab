"""WICS 섹터 분류 엔진.

KIND 업종명 + 주요제품 키워드로 투자 관점 섹터 분류.

사용법::

    from dartlab.analysis.comparative.sector import classify, getParams

    info = classify("삼성전자", kindIndustry="통신 및 방송 장비 제조업")
    info.sector       # Sector.IT
    info.industryGroup  # IndustryGroup.SEMICONDUCTOR

    params = getParams(info)
    params.perMultiple  # 15
    params.discountRate  # 13.0
"""

from dartlab.analysis.comparative.sector.classifier import classify
from dartlab.analysis.comparative.sector.params import getParams
from dartlab.analysis.comparative.sector.types import (
    IndustryGroup,
    Sector,
    SectorInfo,
    SectorParams,
)

__all__ = [
    "classify",
    "getParams",
    "IndustryGroup",
    "Sector",
    "SectorInfo",
    "SectorParams",
]
