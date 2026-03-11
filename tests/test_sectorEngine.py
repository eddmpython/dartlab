"""sectorEngine 테스트."""

from dartlab.engines.sector import (
    IndustryGroup,
    Sector,
    SectorInfo,
    classify,
    getParams,
)


class TestClassifyOverride:
    """수동 오버라이드 분류 테스트."""

    def test_samsung(self):
        info = classify("삼성전자")
        assert info.sector == Sector.IT
        assert info.industryGroup == IndustryGroup.SEMICONDUCTOR
        assert info.confidence == 1.0
        assert info.source == "override"

    def test_sk_hynix(self):
        info = classify("SK하이닉스")
        assert info.sector == Sector.IT
        assert info.industryGroup == IndustryGroup.SEMICONDUCTOR

    def test_kakao(self):
        info = classify("카카오")
        assert info.sector == Sector.COMMUNICATION
        assert info.industryGroup == IndustryGroup.INTERNET

    def test_hyundai_motor(self):
        info = classify("현대자동차")
        assert info.sector == Sector.CONSUMER_DISC
        assert info.industryGroup == IndustryGroup.AUTO

    def test_kb_financial(self):
        info = classify("KB금융")
        assert info.sector == Sector.FINANCIALS
        assert info.industryGroup == IndustryGroup.BANK

    def test_samsung_life(self):
        info = classify("삼성생명")
        assert info.sector == Sector.FINANCIALS
        assert info.industryGroup == IndustryGroup.INSURANCE

    def test_kepco(self):
        info = classify("한국전력")
        assert info.sector == Sector.UTILITIES
        assert info.industryGroup == IndustryGroup.ELECTRIC

    def test_celltrion(self):
        info = classify("셀트리온")
        assert info.sector == Sector.HEALTHCARE
        assert info.industryGroup == IndustryGroup.PHARMA_BIO

    def test_sk_innovation(self):
        info = classify("SK이노베이션")
        assert info.sector == Sector.ENERGY
        assert info.industryGroup == IndustryGroup.OIL_GAS

    def test_samsung_ct(self):
        info = classify("삼성물산")
        assert info.sector == Sector.INDUSTRIALS
        assert info.industryGroup == IndustryGroup.CONSTRUCTION

    def test_partial_match(self):
        info = classify("삼성전자우")
        assert info.sector == Sector.IT
        assert info.source == "override_partial"
        assert info.confidence == 0.95


class TestClassifyKSIC:
    """KSIC 매핑 분류 테스트."""

    def test_semiconductor(self):
        info = classify("무명반도체", kindIndustry="반도체 제조업")
        assert info.sector == Sector.IT
        assert info.industryGroup == IndustryGroup.SEMICONDUCTOR
        assert info.source == "ksic"

    def test_pharma(self):
        info = classify("무명제약", kindIndustry="의약품 제조업")
        assert info.sector == Sector.HEALTHCARE
        assert info.industryGroup == IndustryGroup.PHARMA_BIO

    def test_steel(self):
        info = classify("무명철강", kindIndustry="1차 철강 제조업")
        assert info.sector == Sector.MATERIALS
        assert info.industryGroup == IndustryGroup.METALS

    def test_bank(self):
        info = classify("무명은행", kindIndustry="은행 및 저축기관")
        assert info.sector == Sector.FINANCIALS
        assert info.industryGroup == IndustryGroup.BANK

    def test_construction(self):
        info = classify("무명건설", kindIndustry="건물 건설업")
        assert info.sector == Sector.INDUSTRIALS
        assert info.industryGroup == IndustryGroup.CONSTRUCTION

    def test_food(self):
        info = classify("무명식품", kindIndustry="기타 식품 제조업")
        assert info.sector == Sector.CONSUMER_STAPLES
        assert info.industryGroup == IndustryGroup.FOOD_BEV_TOBACCO

    def test_telecom(self):
        info = classify("무명통신", kindIndustry="전기 통신업")
        assert info.sector == Sector.COMMUNICATION
        assert info.industryGroup == IndustryGroup.TELECOM


class TestClassifyKeyword:
    """키워드 기반 분류 테스트."""

    def test_semiconductor_keyword(self):
        info = classify("무명회사", mainProducts="DRAM, NAND 플래시메모리 제조")
        assert info.sector == Sector.IT
        assert info.industryGroup == IndustryGroup.SEMICONDUCTOR
        assert info.source == "keyword"

    def test_bio_keyword(self):
        info = classify("무명회사", mainProducts="항체 바이오시밀러 CDMO 서비스")
        assert info.sector == Sector.HEALTHCARE
        assert info.industryGroup == IndustryGroup.PHARMA_BIO
        assert info.source == "keyword"

    def test_game_keyword(self):
        info = classify("무명회사", mainProducts="모바일게임, MMORPG 개발 및 퍼블리싱")
        assert info.sector == Sector.COMMUNICATION
        assert info.industryGroup == IndustryGroup.GAME
        assert info.source == "keyword"

    def test_battery_keyword(self):
        info = classify("무명회사", mainProducts="리튬이온 2차전지, 양극재, ESS")
        assert info.sector == Sector.MATERIALS
        assert info.industryGroup == IndustryGroup.CHEMICAL
        assert info.source == "keyword"

    def test_holding_company_skips_keyword(self):
        info = classify("무명지주", kindIndustry="기타 금융업", mainProducts="지주회사, 배터리 리튬")
        assert info.source == "ksic"
        assert info.sector == Sector.FINANCIALS


class TestClassifyPriority:
    """분류 우선순위 테스트."""

    def test_override_over_ksic(self):
        info = classify("삼성전자", kindIndustry="통신 및 방송 장비 제조업")
        assert info.source == "override"
        assert info.industryGroup == IndustryGroup.SEMICONDUCTOR

    def test_keyword_over_ksic(self):
        info = classify("무명회사", kindIndustry="기타 화학제품 제조업", mainProducts="DRAM 반도체 장비")
        assert info.source == "keyword"
        assert info.industryGroup == IndustryGroup.SEMICONDUCTOR

    def test_unknown_fallback(self):
        info = classify("완전무명회사")
        assert info.sector == Sector.UNKNOWN
        assert info.industryGroup == IndustryGroup.UNKNOWN
        assert info.confidence == 0.0
        assert info.source == "unknown"


class TestGetParams:
    """섹터 파라미터 조회 테스트."""

    def test_semiconductor_params(self):
        info = SectorInfo(Sector.IT, IndustryGroup.SEMICONDUCTOR, 1.0, "override")
        params = getParams(info)
        assert params.label == "반도체"
        assert params.discountRate == 13.0
        assert params.perMultiple == 15

    def test_bank_params(self):
        info = SectorInfo(Sector.FINANCIALS, IndustryGroup.BANK, 1.0, "override")
        params = getParams(info)
        assert params.label == "은행"
        assert params.pbrMultiple == 0.5

    def test_unknown_group_falls_to_sector(self):
        info = SectorInfo(Sector.IT, IndustryGroup.UNKNOWN, 0.5, "test")
        params = getParams(info)
        assert params.label == "IT"

    def test_unknown_sector(self):
        info = SectorInfo(Sector.UNKNOWN, IndustryGroup.UNKNOWN, 0.0, "unknown")
        params = getParams(info)
        assert params.discountRate == 10.0

    def test_industry_group_preferred_over_sector(self):
        info = SectorInfo(Sector.COMMUNICATION, IndustryGroup.GAME, 1.0, "override")
        params = getParams(info)
        assert params.label == "게임"
        assert params.perMultiple == 20


class TestSectorInfoRepr:
    """SectorInfo repr 테스트."""

    def test_repr(self):
        info = classify("삼성전자")
        r = repr(info)
        assert "IT" in r
        assert "반도체" in r
        assert "1.00" in r


class TestSectorEnum:
    """Enum 값 테스트."""

    def test_sector_value(self):
        assert Sector.IT.value == "IT"
        assert Sector.FINANCIALS.value == "금융"

    def test_industry_group_value(self):
        assert IndustryGroup.SEMICONDUCTOR.value == "반도체와반도체장비"
        assert IndustryGroup.BANK.value == "은행"

    def test_sector_str(self):
        assert Sector.IT.value == "IT"
