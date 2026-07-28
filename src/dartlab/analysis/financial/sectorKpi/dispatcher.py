"""sectorKpi dispatcher — 업종 자동 감지 + 모듈 dispatch.

업종명/업종코드에서 sectorKpi 모듈 키를 매핑하고, 해당 모듈의 calc 함수를
호출해 dict 결과를 반환한다.
"""

from __future__ import annotations

import logging
from typing import Any

from dartlab.core.sector import IndustryGroup

log = logging.getLogger(__name__)

# WICS 중분류 -> sectorKpi 모듈. 어휘의 정본은 `core.sector.IndustryGroup` 이다.
#
# 예전 표는 "건설업"·"종합건설"·"디지털콘텐츠" 같은 평문 키를 substring 으로 맞췄는데,
# 그 문자열은 이 repo 어느 업종 어휘에도 없어서 접근자가 살아 있었더라도 한 건도
# 매칭되지 않았다. enum 동등 비교로 바꿔 오탐과 미탐을 함께 없앤다.
#
# "미디어와엔터테인먼트"와 "인터넷과카탈로그소매"는 예전 표가 게임으로 보냈지만 각각
# 방송·엔터와 온라인 유통이라 게임 KPI 가 맞지 않는다. 둘은 뺐다.
_SECTOR_MAP: dict[IndustryGroup, str] = {
    IndustryGroup.CONSTRUCTION: "construction",
    IndustryGroup.SEMICONDUCTOR: "semiconductor",
    IndustryGroup.DISPLAY: "semiconductor",
    IndustryGroup.GAME: "gaming",
    IndustryGroup.PHARMA_BIO: "pharma",
}


def detectSector(company: Any) -> str | None:
    """업종 분류에서 sectorKpi 모듈 키 반환.

    예전 구현은 ``company.industryName`` 다음 ``company.industry`` 를 문자열로 읽었다.
    앞 이름은 Company 에 없고 뒤 이름은 dict 를 돌려주는 **메서드**라, ``keyword in industry``
    가 메서드 객체를 순회하려다 TypeError 를 던졌다. 모든 DART 기업에서 그랬고 story 의
    "업종 특수 KPI" 블록이 그 예외를 삼켜 늘 비어 있었다. 지금은 ``company.sector`` 가
    주는 WICS 중분류 enum 으로 판정한다.

    Capabilities:
        - WICS 중분류 enum 동등 매칭 → sectorKpi 모듈명 (construction/semiconductor/gaming/pharma).

    Guide:
        company.sector 의 industryGroup 을 _SECTOR_MAP 에서 조회.

    When:
        sectorKpi() 진입 직전 dispatch 키 확인.

    How:
        SectorInfo.industryGroup enum 을 키로 dict 조회. 미등재 업종은 None.

    Requires:
        company 가 sector 속성 보유 (DART Company). 없으면 None.

    Raises:
        없음. 업종 판정 실패는 None.

    Returns:
        str | None — 모듈 키 ("construction" 등) 또는 미매칭 시 None.

    Example:
        >>> detectSector(현대건설)
        "construction"

    See Also:
        - sectorKpi : 본 dispatch 키를 받아 실제 calc 호출.
        - dartlab.core.sector.IndustryGroup : 업종 어휘 정본.

    AIContext:
        섹터별 특화 KPI 라우팅 결정 근거.
    """
    try:
        info = getattr(company, "sector", None)
    except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        log.debug("업종 조회 실패: %s", exc)
        return None
    group = getattr(info, "industryGroup", None)
    if group is None:
        return None
    return _SECTOR_MAP.get(group)


def sectorKpi(company: Any) -> dict | None:
    """업종 자동 감지 → 해당 모듈 dispatch → calc 결과 dict 반환.

    Capabilities:
        - detectSector → 4 모듈 (construction/semiconductor/gaming/pharma) 중 1 선택 호출.

    Guide:
        detectSector() 키로 lazy import 후 calc{Sector}Kpis 호출.

    When:
        업종 특화 분석 시 (일반 ratio 외에 도메인 KPI 필요).

    How:
        sector key switch → lazy import → calc 결과 wrap.

    Requires:
        company 가 sector 모듈 calc 함수 입력 계약 만족.

    Raises:
        없음. ImportError/AttributeError/ValueError/TypeError try 흡수 후 None.

    Returns:
        dict | None
            sector : str — 감지된 업종 ("construction" / "semiconductor" / ...)
            kpis : dict — 업종별 KPI dict

    Example:
        >>> sectorKpi(현대건설)
        {"sector": "construction", "kpis": {...}}

    See Also:
        - detectSector : 업종 키 매핑.

    AIContext:
        섹터 한정 deep-dive KPI 진입점.
    """
    sector = detectSector(company)
    if not sector:
        return None

    try:
        if sector == "construction":
            from dartlab.analysis.financial.sectorKpi.construction import calcConstructionKpis

            kpis = calcConstructionKpis(company)
        elif sector == "semiconductor":
            from dartlab.analysis.financial.sectorKpi.semiconductor import calcSemiconductorKpis

            kpis = calcSemiconductorKpis(company)
        elif sector == "gaming":
            from dartlab.analysis.financial.sectorKpi.gaming import calcGamingKpis

            kpis = calcGamingKpis(company)
        elif sector == "pharma":
            from dartlab.analysis.financial.sectorKpi.pharma import calcPharmaKpis

            kpis = calcPharmaKpis(company)
        else:
            return None
    except (ImportError, AttributeError, ValueError, TypeError) as e:
        log.debug("sectorKpi %s 실행 실패: %s", sector, e)
        return None

    if not kpis:
        return None
    return {"sector": sector, "kpis": kpis}
