"""기업명 → 종목코드/ticker 매칭.

추출된 기업명을 kindList(KR) 또는 EDGAR ticker(US)에 매칭한다.
"""

from __future__ import annotations


def match_company_name(
    name: str,
    *,
    market: str = "KR",
) -> dict | None:
    """기업명을 종목코드/ticker에 매칭.

    Args:
        name: 추출된 기업명.
        market: "KR" 또는 "US".

    Returns:
        {"stockCode": str, "corpName": str} 또는 None.
    """
    if market == "KR":
        return _match_kr(name)
    return _match_us(name)


def _match_kr(name: str) -> dict | None:
    """한국 기업명 → KRX 종목코드."""
    try:
        from dartlab.gather.listing import fuzzySearch, nameToCode

        # 정확 매칭
        code = nameToCode(name)
        if code:
            return {"stockCode": code, "corpName": name}

        # fuzzy 매칭
        results = fuzzySearch(name)
        if results is not None and hasattr(results, "height") and results.height > 0:
            first = results.row(0, named=True)
            return {
                "stockCode": first.get("종목코드", ""),
                "corpName": first.get("회사명", name),
            }
    except (ImportError, ValueError, KeyError):
        pass

    return None


def _match_us(name: str) -> dict | None:
    """미국 기업명 → ticker (EDGAR)."""
    try:
        from dartlab.providers.edgar.company import Company as EdgarCompany

        results = EdgarCompany.search(name)
        if results is not None and hasattr(results, "height") and results.height > 0:
            first = results.row(0, named=True)
            return {
                "stockCode": first.get("ticker", ""),
                "corpName": first.get("title", name),
            }
    except (ImportError, ValueError, KeyError):
        pass

    return None


def resolve_links(
    links: list,
    *,
    market: str = "KR",
) -> list:
    """SupplyLink 리스트의 target을 종목코드로 해석.

    매칭 성공하면 confidence를 0.1 올린다.
    """
    for link in links:
        match = match_company_name(link.target, market=market)
        if match:
            link.target = f"{match['corpName']} ({match['stockCode']})"
            link.confidence = min(link.confidence + 0.1, 1.0)
    return links
