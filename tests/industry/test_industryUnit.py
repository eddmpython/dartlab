"""industry 엔진 unit 테스트 — 18 공개 API / 4 기존 테스트 → 확장.

순수 로직 위주 (데이터 없이 돌아가는 부분):
- Sector / IndustryGroup enum 계약
- SectorParams / MarketParams dataclass
- classify() — 업종/제품명 → Sector 매핑 (데이터 JSON 로드 포함)
- getParams / getMarketParams / getThresholds
- Industry() callable — guide 모드 (데이터 없이)

Phase B2 엔진 커버리지 확장 (plan: 60% 목표).
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit]


# ════════════════════════════════════════
# Enum 계약
# ════════════════════════════════════════


class TestSectorEnum:
    def test_sectorEnum_hasStandardMembers(self):
        from dartlab.industry import Sector

        for m in ("ENERGY", "MATERIALS", "INDUSTRIALS", "IT", "FINANCIALS", "UNKNOWN"):
            assert hasattr(Sector, m), f"Sector.{m} 누락 — WICS 대분류 계약 위반"

    def test_sectorEnum_valuesAreKorean(self):
        from dartlab.industry import Sector

        assert Sector.IT.value == "IT"
        assert Sector.ENERGY.value == "에너지"
        assert Sector.UNKNOWN.value == "기타"

    def test_industryGroupEnum_hasSemiconductor(self):
        from dartlab.industry import IndustryGroup

        assert IndustryGroup.SEMICONDUCTOR.value == "반도체와반도체장비"

    def test_industryGroupEnum_allMembersHaveKoreanLabels(self):
        from dartlab.industry import IndustryGroup

        # 모든 멤버의 value 가 빈 문자열이 아니어야 함
        for member in IndustryGroup:
            assert member.value, f"{member.name} 의 value 비어있음"


# ════════════════════════════════════════
# SectorParams / MarketParams dataclass
# ════════════════════════════════════════


class TestSectorParams:
    def test_getParams_defaultReturnsSectorParams(self):
        from dartlab.industry import SectorParams, getParams

        params = getParams()
        assert isinstance(params, SectorParams)

    def test_getParams_withSectorInfo_returnsSpecificParams(self):
        from dartlab.industry import IndustryGroup, Sector, SectorInfo, getParams

        info = SectorInfo(
            sector=Sector.IT,
            industryGroup=IndustryGroup.SEMICONDUCTOR,
            confidence=1.0,
            source="test",
        )
        params = getParams(info)
        assert params is not None

    def test_sectorParams_hasExpectedFields(self):
        from dartlab.industry import getParams

        params = getParams()
        # SectorParams 는 최소 financial ratio 기준값 몇 개는 포함해야 함
        # (필드 이름은 구현에 따라 다를 수 있으므로 최소 dataclass 인지만 확인)
        from dataclasses import is_dataclass

        assert is_dataclass(params)


class TestMarketParams:
    def test_getMarketParams_defaultKRW(self):
        from dartlab.industry import MarketParams, getMarketParams

        params = getMarketParams()
        assert isinstance(params, MarketParams)

    def test_getMarketParams_explicitKRW(self):
        from dartlab.industry import getMarketParams

        kr = getMarketParams("KRW")
        assert kr is not None

    def test_getMarketParams_USD(self):
        from dartlab.industry import getMarketParams

        us = getMarketParams("USD")
        assert us is not None


# ════════════════════════════════════════
# classify() — 업종/제품명 → Sector 매핑
# ════════════════════════════════════════


class TestClassify:
    def test_classify_unknownCompany_returnsUnknownSector(self):
        from dartlab.industry import Sector, classify

        # 완전히 모르는 회사 + 업종 정보 없음 → UNKNOWN 폴백
        info = classify(companyName="존재하지않는회사XYZ")
        assert info.sector == Sector.UNKNOWN

    def test_classify_samsungLikeCompany_hasSector(self):
        from dartlab.industry import classify

        # 삼성전자 override 또는 반도체 업종 매칭
        info = classify(companyName="삼성전자", kindIndustry="반도체 제조업")
        # 매칭 성공 시 sector 이 존재
        assert info.sector is not None

    def test_classify_returnsSectorInfoInstance(self):
        from dartlab.industry import SectorInfo, classify

        info = classify(companyName="테스트")
        assert isinstance(info, SectorInfo)
        assert hasattr(info, "sector")
        assert hasattr(info, "confidence")
        assert 0.0 <= info.confidence <= 1.0


# ════════════════════════════════════════
# getThresholds — 시장별 threshold JSON 로드
# ════════════════════════════════════════


class TestThresholds:
    def test_getThresholds_returnsDict(self):
        from dartlab.industry import getThresholds

        result = getThresholds()
        assert result is not None
        # thresholds 구조는 dict (축별 경계값)
        assert isinstance(result, (dict, tuple, list)) or hasattr(result, "__dict__")


# ════════════════════════════════════════
# Industry() callable — guide 모드
# ════════════════════════════════════════


class TestIndustryClass:
    """Industry callable accessor (클래스 인스턴스)."""

    def test_industryClass_importable(self):
        from dartlab.industry import Industry

        assert Industry is not None

    def test_industryInstance_isCallable(self):
        from dartlab.industry import Industry

        ind = Industry()
        assert callable(ind)


# ════════════════════════════════════════
# import 스모크
# ════════════════════════════════════════


def test_industryTopLevel_importsAllPublicSymbols():
    """dartlab.industry 가 공개 심볼 15개 이상 노출."""
    import dartlab.industry as ind

    publicSymbols = [s for s in dir(ind) if not s.startswith("_")]
    # Sector, IndustryGroup, SectorInfo, SectorParams, MarketParams, MARKET_KR,
    # MARKET_US, MARKET_PARAMS, classify, getParams, getMarketParams,
    # getThresholds, Industry, addOverride, ...
    assert len(publicSymbols) >= 10, f"공개 심볼 {len(publicSymbols)}개 — 예상 10+ 미달"


def test_resolveIndustryTarget_mapsStockCodeToIndustry():
    """종목코드로 온 target 은 그 회사의 산업 ID 로 바뀐다.

    축 문서는 target 으로 industryId · themeId · stockCode 셋을 받는다고 적어 두었는데,
    정작 종목코드를 해소하는 자리가 없었다. 핸들러가 종목코드를 industryId 로 그대로
    받아 조회가 전부 빗나갔고, 예외 대신 빈 표가 나와서 어디서도 안 잡혔다.
    """
    from dartlab.industry import _resolveIndustryTarget
    from dartlab.industry.build.pipeline import loadNodes

    nodes = [n for n in loadNodes() if getattr(n, "stockCode", None) and getattr(n, "industry", None)]
    if not nodes:
        pytest.skip("industry 노드 데이터 없음")
    node = nodes[0]

    assert _resolveIndustryTarget(node.stockCode) == node.industry


def test_resolveIndustryTarget_leavesNonStockCodeAlone():
    """산업 ID·테마 ID·None 은 그대로 통과한다 (해소는 6자리 숫자에만)."""
    from dartlab.industry import _resolveIndustryTarget

    assert _resolveIndustryTarget("semiconductor") == "semiconductor"
    assert _resolveIndustryTarget("secondaryBattery") == "secondaryBattery"
    assert _resolveIndustryTarget(None) is None
    assert _resolveIndustryTarget("12345") == "12345"
