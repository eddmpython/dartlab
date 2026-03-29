"""섹터별 밸류에이션 파라미터."""

from __future__ import annotations

from dartlab.core.sector.types import (
    IndustryGroup,
    Sector,
    SectorInfo,
    SectorParams,
)

S = Sector
G = IndustryGroup

SECTOR_PARAMS: dict[Sector, SectorParams] = {
    S.IT: SectorParams(
        discountRate=12.0,
        growthRate=5.0,
        perMultiple=18,
        pbrMultiple=2.0,
        evEbitdaMultiple=10,
        label="IT",
    ),
    S.HEALTHCARE: SectorParams(
        discountRate=15.0,
        growthRate=10.0,
        perMultiple=30,
        pbrMultiple=3.0,
        evEbitdaMultiple=15,
        label="건강관리",
    ),
    S.FINANCIALS: SectorParams(
        discountRate=9.0,
        growthRate=3.0,
        perMultiple=8,
        pbrMultiple=0.6,
        evEbitdaMultiple=8,
        label="금융",
    ),
    S.CONSUMER_DISC: SectorParams(
        discountRate=10.0,
        growthRate=3.0,
        perMultiple=12,
        pbrMultiple=1.0,
        evEbitdaMultiple=8,
        label="경기관련소비재",
    ),
    S.CONSUMER_STAPLES: SectorParams(
        discountRate=9.0,
        growthRate=2.0,
        perMultiple=15,
        pbrMultiple=1.5,
        evEbitdaMultiple=10,
        label="필수소비재",
    ),
    S.INDUSTRIALS: SectorParams(
        discountRate=10.0,
        growthRate=3.0,
        perMultiple=12,
        pbrMultiple=1.0,
        evEbitdaMultiple=7,
        label="산업재",
    ),
    S.MATERIALS: SectorParams(
        discountRate=11.0,
        growthRate=3.0,
        perMultiple=10,
        pbrMultiple=1.0,
        evEbitdaMultiple=6,
        label="소재",
    ),
    S.ENERGY: SectorParams(
        discountRate=10.0,
        growthRate=2.0,
        perMultiple=8,
        pbrMultiple=0.8,
        evEbitdaMultiple=5,
        label="에너지",
    ),
    S.UTILITIES: SectorParams(
        discountRate=8.0,
        growthRate=2.0,
        perMultiple=12,
        pbrMultiple=0.8,
        evEbitdaMultiple=7,
        label="유틸리티",
    ),
    S.REAL_ESTATE: SectorParams(
        discountRate=9.0,
        growthRate=2.0,
        perMultiple=15,
        pbrMultiple=1.0,
        evEbitdaMultiple=12,
        label="부동산",
    ),
    S.COMMUNICATION: SectorParams(
        discountRate=11.0,
        growthRate=5.0,
        perMultiple=18,
        pbrMultiple=2.0,
        evEbitdaMultiple=10,
        label="커뮤니케이션서비스",
    ),
    S.UNKNOWN: SectorParams(
        discountRate=10.0,
        growthRate=3.0,
        perMultiple=15,
        pbrMultiple=1.2,
        evEbitdaMultiple=8,
        label="기타",
    ),
}

INDUSTRY_GROUP_PARAMS: dict[IndustryGroup, SectorParams] = {
    G.SEMICONDUCTOR: SectorParams(
        discountRate=13.0,
        growthRate=7.0,
        perMultiple=15,
        pbrMultiple=2.5,
        evEbitdaMultiple=8,
        label="반도체",
    ),
    G.DISPLAY: SectorParams(
        discountRate=12.0,
        growthRate=4.0,
        perMultiple=12,
        pbrMultiple=1.5,
        evEbitdaMultiple=6,
        label="디스플레이",
    ),
    G.SOFTWARE: SectorParams(
        discountRate=12.0,
        growthRate=8.0,
        perMultiple=25,
        pbrMultiple=4.0,
        evEbitdaMultiple=15,
        label="소프트웨어",
    ),
    G.PHARMA_BIO: SectorParams(
        discountRate=16.0,
        growthRate=12.0,
        perMultiple=35,
        pbrMultiple=4.0,
        evEbitdaMultiple=18,
        label="제약/바이오",
    ),
    G.BANK: SectorParams(
        discountRate=8.0,
        growthRate=2.0,
        perMultiple=6,
        pbrMultiple=0.5,
        evEbitdaMultiple=6,
        label="은행",
    ),
    G.INSURANCE: SectorParams(
        discountRate=9.0,
        growthRate=3.0,
        perMultiple=8,
        pbrMultiple=0.7,
        evEbitdaMultiple=7,
        label="보험",
    ),
    G.DIVERSIFIED_FINANCIALS: SectorParams(
        discountRate=10.0,
        growthRate=4.0,
        perMultiple=10,
        pbrMultiple=1.0,
        evEbitdaMultiple=8,
        label="증권/기타금융",
    ),
    G.AUTO: SectorParams(
        discountRate=10.0,
        growthRate=3.0,
        perMultiple=8,
        pbrMultiple=0.8,
        evEbitdaMultiple=5,
        label="자동차",
    ),
    G.SHIPBUILDING: SectorParams(
        discountRate=11.0,
        growthRate=4.0,
        perMultiple=10,
        pbrMultiple=0.9,
        evEbitdaMultiple=6,
        label="조선",
    ),
    G.CONSTRUCTION: SectorParams(
        discountRate=10.0,
        growthRate=2.0,
        perMultiple=8,
        pbrMultiple=0.6,
        evEbitdaMultiple=5,
        label="건설",
    ),
    G.AEROSPACE_DEFENSE: SectorParams(
        discountRate=11.0,
        growthRate=6.0,
        perMultiple=18,
        pbrMultiple=2.0,
        evEbitdaMultiple=12,
        label="항공우주/방산",
    ),
    G.CHEMICAL: SectorParams(
        discountRate=11.0,
        growthRate=3.0,
        perMultiple=10,
        pbrMultiple=1.0,
        evEbitdaMultiple=6,
        label="화학",
    ),
    G.METALS: SectorParams(
        discountRate=10.0,
        growthRate=2.0,
        perMultiple=8,
        pbrMultiple=0.6,
        evEbitdaMultiple=5,
        label="철강/비철",
    ),
    G.GAME: SectorParams(
        discountRate=13.0,
        growthRate=8.0,
        perMultiple=20,
        pbrMultiple=3.0,
        evEbitdaMultiple=12,
        label="게임",
    ),
    G.INTERNET: SectorParams(
        discountRate=12.0,
        growthRate=7.0,
        perMultiple=25,
        pbrMultiple=3.5,
        evEbitdaMultiple=15,
        label="인터넷",
    ),
    G.MEDIA: SectorParams(
        discountRate=11.0,
        growthRate=5.0,
        perMultiple=15,
        pbrMultiple=2.0,
        evEbitdaMultiple=10,
        label="미디어/엔터",
    ),
    G.TELECOM: SectorParams(
        discountRate=9.0,
        growthRate=2.0,
        perMultiple=10,
        pbrMultiple=1.0,
        evEbitdaMultiple=6,
        label="통신",
    ),
    G.RETAIL: SectorParams(
        discountRate=10.0,
        growthRate=3.0,
        perMultiple=12,
        pbrMultiple=1.2,
        evEbitdaMultiple=8,
        label="유통",
    ),
    G.FOOD_BEV_TOBACCO: SectorParams(
        discountRate=9.0,
        growthRate=2.0,
        perMultiple=15,
        pbrMultiple=1.5,
        evEbitdaMultiple=10,
        label="음식료",
    ),
    G.OIL_GAS: SectorParams(
        discountRate=10.0,
        growthRate=2.0,
        perMultiple=8,
        pbrMultiple=0.7,
        evEbitdaMultiple=5,
        label="정유/가스",
    ),
    G.ELECTRIC: SectorParams(
        discountRate=8.0,
        growthRate=2.0,
        perMultiple=12,
        pbrMultiple=0.8,
        evEbitdaMultiple=7,
        label="전력",
    ),
}

DEFAULT_PARAMS = SectorParams(
    discountRate=10.0,
    growthRate=3.0,
    perMultiple=15,
    pbrMultiple=1.2,
    evEbitdaMultiple=8,
    label="기타",
)


def getParams(sectorInfo: SectorInfo) -> SectorParams:
    """SectorInfo에서 최적 파라미터 반환 (중분류 우선, 없으면 대분류).

    Args:
        sectorInfo: 분류 결과.

    Returns:
        해당 섹터/산업군의 밸류에이션 파라미터.
    """
    if sectorInfo.industryGroup != G.UNKNOWN:
        params = INDUSTRY_GROUP_PARAMS.get(sectorInfo.industryGroup)
        if params is not None:
            return params
    return SECTOR_PARAMS.get(sectorInfo.sector, DEFAULT_PARAMS)
