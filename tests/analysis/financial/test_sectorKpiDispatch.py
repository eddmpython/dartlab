"""sectorKpi 업종 판정과 게임 IP 표 파싱 가드.

두 결함을 붙든다.

첫째, 업종 판정이 ``company.industryName`` 다음 ``company.industry`` 를 문자열로 읽었다.
앞 이름은 Company 에 없고 뒤 이름은 dict 를 돌려주는 메서드라 모든 DART 기업에서
TypeError 가 났다. story 의 "업종 특수 KPI" 블록이 그것을 삼켜 늘 비어 있었다.

둘째, 게임 KPI 가 매출액을 ``float("85,374")`` 로 넣어 ValueError 를 냈고 넓은 except 가
결과를 통째로 지웠다. 이름 열도 품목이 아니라 매출유형을 읽어 IP 가 한 덩어리가 됐다.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

from dartlab.analysis.financial.sectorKpi.dispatcher import _SECTOR_MAP, detectSector
from dartlab.analysis.financial.sectorKpi.gaming import _splitHeader
from dartlab.core.sector import IndustryGroup, Sector, SectorInfo


class _Company:
    """sector 속성만 가진 최소 stub."""

    def __init__(self, group: IndustryGroup | None) -> None:
        self.sector = (
            SectorInfo(sector=Sector.IT, industryGroup=group, confidence=1.0, source="test")
            if group is not None
            else None
        )


class _MethodIndustryCompany:
    """industry 를 메서드로 가진 실제 Company 모양."""

    def industry(self) -> dict:
        return {"industry": "semiconductor"}


class TestDetectSector:
    def test_maps_industry_group(self):
        assert detectSector(_Company(IndustryGroup.SEMICONDUCTOR)) == "semiconductor"
        assert detectSector(_Company(IndustryGroup.CONSTRUCTION)) == "construction"
        assert detectSector(_Company(IndustryGroup.GAME)) == "gaming"
        assert detectSector(_Company(IndustryGroup.PHARMA_BIO)) == "pharma"

    def test_unmapped_group_is_none(self):
        assert detectSector(_Company(IndustryGroup.BANK)) is None

    def test_missing_sector_is_none(self):
        assert detectSector(_Company(None)) is None
        assert detectSector(object()) is None

    def test_method_industry_does_not_raise(self):
        """industry 가 메서드여도 예외 없이 None. 옛 구현은 여기서 TypeError 였다."""
        assert detectSector(_MethodIndustryCompany()) is None

    def test_map_keys_are_industry_group_members(self):
        """평문 문자열 키 재유입 차단. 어휘 정본은 IndustryGroup 이다."""
        assert _SECTOR_MAP
        for key in _SECTOR_MAP:
            assert isinstance(key, IndustryGroup)


class TestGamingHeaderSplit:
    def test_period_column_is_amount_name_column_repeats_itself(self):
        """머리글이 제 열 이름을 되풀이하면 이름 열, 기수 아래 매출액이면 금액 열."""
        header = {
            "사업부문": "사업부문",
            "구분": "구분",
            "품목": "품목",
            "제30기 1분기": "매출액",
            "제30기 1분기.1": "비율",
            "제29기": "매출액",
        }
        amountCol, nameCol = _splitHeader(header)
        assert amountCol == "제30기 1분기"  # 최신 기수 (DART 표는 최신을 왼쪽에)
        assert nameCol == "품목"  # 가장 잘게 쪼갠 이름

    def test_sales_type_column_is_not_amount(self):
        """ "매출유형" 은 이름 안에 매출이 들어 있을 뿐 금액 열이 아니다."""
        header = {
            "사업부문": "사업부문",
            "매출유형": "매출유형",
            "제18기 1분기": "매출액",
            "제18기 1분기.1": "비중",
        }
        amountCol, nameCol = _splitHeader(header)
        assert amountCol == "제18기 1분기"
        assert nameCol == "매출유형"

    def test_operating_revenue_label_counts_as_amount(self):
        """영업수익도 금액 열이다. 대상회사는 품목이 아니라 이름 열에서 뺀다."""
        header = {
            "품목": "품목",
            "제품명": "제품명",
            "대상회사": "대상회사",
            "제29기(2026년 1분기)": "영업수익",
            "제29기(2026년 1분기).1": "비율",
        }
        amountCol, nameCol = _splitHeader(header)
        assert amountCol == "제29기(2026년 1분기)"
        assert nameCol == "제품명"

    def test_table_without_amount_column_is_rejected(self):
        """게임 라인업 표처럼 금액이 없는 표는 고르지 않는다."""
        header = {"IP": "검은사막", "플랫폼": "PC", "게임명": "검은사막"}
        amountCol, _ = _splitHeader(header)
        assert amountCol is None
