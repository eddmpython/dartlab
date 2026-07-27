"""valuation.py 공통 헬퍼 — sectorKey 매핑 / price fetch / series + shares 추출."""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


_IG_TO_SECTOR_KEY: dict[str, str] = {
    "SEMICONDUCTOR": "반도체",
    "AUTO": "자동차",
    "CHEMICAL": "화학",
    "METALS": "철강",
    "CONSTRUCTION": "건설",
    "CONSTRUCTION_MATERIALS": "건설",
    "BANK": "금융/은행",
    "INSURANCE": "금융/보험",
    "DIVERSIFIED_FINANCIALS": "금융/증권",
    "SOFTWARE": "IT/소프트웨어",
    "IT_SERVICE": "IT/소프트웨어",
    "INTERNET": "IT/소프트웨어",
    "TECH_HARDWARE": "전자/하드웨어",
    "DISPLAY": "디스플레이",
    "TELECOM": "통신",
    "RETAIL": "유통",
    "FOOD_BEV_TOBACCO": "식품",
    "FOOD_STAPLES": "식품",
    "HOUSEHOLD": "식품",
    "PHARMA_BIO": "제약/바이오",
    "HEALTHCARE_EQUIP": "제약/바이오",
    "UTILITIES": "전력/에너지",
    "ELECTRIC": "전력/에너지",
    "GAS_UTILITY": "전력/에너지",
    "ENERGY_EQUIP": "에너지/자원",
    "OIL_GAS": "에너지/자원",
    "CAPITAL_GOODS": "산업재",
    "MACHINERY": "산업재",
    "TRANSPORTATION": "산업재",
    "COMMERCIAL_SERVICE": "산업재",
    "SHIPBUILDING": "조선",
    "CONSUMER_DURABLES": "섬유/의류",
    "CONSUMER_SERVICE": "유통",
    "MEDIA_ENTERTAINMENT": "미디어/엔터",
    "MEDIA": "미디어/엔터",
    "GAME": "게임",
    "REAL_ESTATE": "부동산",
    "REIT": "부동산",
    "AEROSPACE_DEFENSE": "산업재",
    "HOTEL_LEISURE": "유통",
}


def _resolveSectorKey(company: Any) -> str | None:
    """company.sector에서 SECTOR_ELASTICITY 키를 추출."""
    try:
        sectorInfo = company.sector
        if sectorInfo is None:
            return None
        igName = sectorInfo.industryGroup.name
        return _IG_TO_SECTOR_KEY.get(igName)
    except (AttributeError, ValueError):
        return None


def _fetchPriceContext(company: Any) -> dict | None:
    """gather.price에서 현재가/시총 가져오기 (sync).

    같은 company에 대해 세션 내 1회만 네트워크 호출.
    실패 시 None 반환 -- 시가 의존 calc만 graceful skip.
    """
    cache = getattr(company, "_cache", None)
    _KEY = "_priceContext"
    if cache is not None and _KEY in cache:
        return cache[_KEY]

    stockCode = getattr(company, "stockCode", None)
    if not stockCode:
        return None

    result = None
    try:
        from dartlab.gather.infra.http import runAsync
        from dartlab.gather.sources.price import fetch

        snapshot = runAsync(fetch(stockCode, market="KR"))
        if snapshot is not None:
            result = {
                "currentPrice": snapshot.current,
                "marketCap": snapshot.marketCap,
                "per": snapshot.per,
                "pbr": snapshot.pbr,
                "isStale": getattr(snapshot, "is_stale", False),
            }
    except (ImportError, OSError, RuntimeError, AttributeError):
        log.debug("price fetch 실패: %s", stockCode)

    if cache is not None:
        cache[_KEY] = result
    return result


def _getSeriesAndShares(company: Any) -> tuple[dict | None, int | None, str]:
    """company에서 annual series, shares, currency 추출."""
    try:
        ann = company._buildFinanceSeries(freq="Y")
        if ann is None:
            return None, None, getattr(company, "currency", "KRW") or "KRW"
        series = ann[0] if isinstance(ann, tuple) else ann
    except (ValueError, KeyError, AttributeError):
        return None, None, getattr(company, "currency", "KRW") or "KRW"

    shares = None
    profile = getattr(company, "profile", None)
    if profile:
        sharesVal = getattr(profile, "sharesOutstanding", None)
        if sharesVal:
            shares = int(sharesVal)

    if shares is None:
        price = _fetchPriceContext(company)
        if price and price.get("marketCap") and price.get("currentPrice"):
            mc = price["marketCap"]
            cp = price["currentPrice"]
            if mc > 0 and cp > 0:
                shares = int(mc / cp)

    currency = getattr(company, "currency", "KRW") or "KRW"
    return series, shares, currency


def _getSectorParams(company: Any):
    """company에서 sectorParams 추출."""
    try:
        return getattr(company, "sectorParams", None)
    except AttributeError:
        return None
