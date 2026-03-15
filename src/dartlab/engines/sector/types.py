"""섹터 분류 데이터 타입."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Sector(str, Enum):
    """WICS 대분류 섹터."""

    ENERGY = "에너지"
    MATERIALS = "소재"
    INDUSTRIALS = "산업재"
    CONSUMER_DISC = "경기관련소비재"
    CONSUMER_STAPLES = "필수소비재"
    HEALTHCARE = "건강관리"
    FINANCIALS = "금융"
    IT = "IT"
    COMMUNICATION = "커뮤니케이션서비스"
    UTILITIES = "유틸리티"
    REAL_ESTATE = "부동산"
    UNKNOWN = "기타"


class IndustryGroup(str, Enum):
    """WICS 중분류 산업군."""

    ENERGY_EQUIP = "에너지장비및서비스"
    OIL_GAS = "석유와가스"

    CHEMICAL = "화학"
    CONSTRUCTION_MATERIALS = "건설자재"
    CONTAINERS = "용기와포장"
    METALS = "금속과광물"
    PAPER = "종이와목재"

    CAPITAL_GOODS = "자본재"
    COMMERCIAL_SERVICE = "상업서비스와공급품"
    TRANSPORTATION = "운송"
    AEROSPACE_DEFENSE = "항공우주와국방"
    CONSTRUCTION = "건설"
    MACHINERY = "기계"
    SHIPBUILDING = "조선"

    AUTO = "자동차와부품"
    CONSUMER_DURABLES = "내구소비재와의류"
    CONSUMER_SERVICE = "소비자서비스"
    MEDIA_ENTERTAINMENT = "미디어와엔터테인먼트"
    RETAIL = "소매(유통)"
    HOTEL_LEISURE = "호텔,레스토랑,레저"

    FOOD_STAPLES = "식품과기본식료품소매"
    FOOD_BEV_TOBACCO = "식품,음료,담배"
    HOUSEHOLD = "가정용품과개인용품"

    HEALTHCARE_EQUIP = "건강관리장비와서비스"
    PHARMA_BIO = "제약과바이오"

    BANK = "은행"
    DIVERSIFIED_FINANCIALS = "다각화된금융"
    INSURANCE = "보험"

    SOFTWARE = "소프트웨어와서비스"
    TECH_HARDWARE = "기술하드웨어와장비"
    SEMICONDUCTOR = "반도체와반도체장비"
    IT_SERVICE = "IT서비스"
    DISPLAY = "디스플레이"

    TELECOM = "전기통신서비스"
    MEDIA = "미디어"
    INTERNET = "인터넷과카탈로그소매"
    GAME = "게임엔터테인먼트"

    UTILITIES = "유틸리티"
    ELECTRIC = "전력"
    GAS_UTILITY = "가스"

    REAL_ESTATE = "부동산"
    REIT = "리츠"

    UNKNOWN = "기타"


@dataclass
class SectorInfo:
    """섹터 분류 결과."""

    sector: Sector
    industryGroup: IndustryGroup
    confidence: float
    source: str

    def __repr__(self):
        return (
            f"SectorInfo({self.sector.value}/{self.industryGroup.value}, conf={self.confidence:.2f}, src={self.source})"
        )


@dataclass
class SectorParams:
    """섹터별 밸류에이션 파라미터."""

    discountRate: float
    growthRate: float
    perMultiple: float
    pbrMultiple: float
    evEbitdaMultiple: float
    label: str
    description: str = ""
