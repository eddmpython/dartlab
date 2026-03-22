"""공급망 관계 추출.

sections의 segments(부문정보), rawMaterial(원재료),
relatedPartyTransaction(관계자거래) topic에서
고객/공급사 관계를 규칙 기반으로 추출한다.
"""

from __future__ import annotations

import re

from dartlab.engines.supply.types import SupplyLink

# 기업명 패턴 — 한글 2자 이상 또는 영문 대문자 시작 2자 이상
_COMPANY_PATTERN = re.compile(
    r"(?:"
    r"[가-힣]{2,}(?:전자|화학|물산|건설|생명|증권|은행|보험|제약|반도체|에너지|텔레콤|모바일|[주]주?[))]?)"
    r"|"
    r"[A-Z][A-Za-z]{1,}(?:\s+[A-Z][A-Za-z]+)*"
    r")"
)

# 공급/고객 관계 키워드
_CUSTOMER_KEYWORDS = [
    "매출처",
    "주요 고객",
    "주요고객",
    "판매처",
    "매출 상위",
    "customer",
    "client",
    "buyer",
    "revenue from",
]

_SUPPLIER_KEYWORDS = [
    "원재료",
    "주요 공급",
    "주요공급",
    "공급사",
    "공급업체",
    "구매처",
    "매입처",
    "원자재",
    "supplier",
    "vendor",
    "raw material",
]

# 공급망 관련 topic
_SUPPLY_TOPICS = frozenset(
    {
        "segments",
        "rawMaterial",
        "relatedPartyTransaction",
        "majorContract",
        "salesByProduct",
        "salesByRegion",
        # EDGAR
        "10-K::item1Business",
        "10-K::item7MDA",
    }
)


def extract_supply_links(
    company: object,
) -> tuple[list[SupplyLink], list[SupplyLink], list[SupplyLink]]:
    """sections에서 고객/공급사/관계자 관계를 추출.

    Args:
        company: dartlab Company 객체.

    Returns:
        (customers, suppliers, related_parties) 튜플.
    """
    customers: list[SupplyLink] = []
    suppliers: list[SupplyLink] = []
    related_parties: list[SupplyLink] = []

    stock_code = getattr(company, "stockCode", "")
    sections = getattr(company, "sections", None)
    if sections is None:
        return customers, suppliers, related_parties

    has_topic = "topic" in sections.columns
    if not has_topic:
        return customers, suppliers, related_parties

    # 기간 컬럼 찾기
    periods = [
        c
        for c in sections.columns
        if c not in ("topic", "chapter", "blockType", "textNodeType", "sourceBlockOrder")
        and re.fullmatch(r"\d{4}(Q[1-4])?", c)
    ]
    if not periods:
        return customers, suppliers, related_parties

    latest_period = periods[0]

    # 관련 topic만 필터
    for row in sections.iter_rows(named=True):
        topic = row.get("topic", "")
        text = str(row.get(latest_period) or "")
        if not text or len(text) < 10:
            continue

        evidence = f"{topic} ({latest_period})"

        # 관계자거래
        if "relatedParty" in topic.lower() or "related" in topic.lower():
            names = _extract_company_names(text)
            for name in names:
                related_parties.append(
                    SupplyLink(
                        source=stock_code,
                        target=name,
                        relation="related_party",
                        evidence=evidence,
                        confidence=0.7,
                    )
                )

        # 고객 추출
        if any(kw in text for kw in _CUSTOMER_KEYWORDS) or "segment" in topic.lower():
            names = _extract_company_names(text)
            for name in names:
                customers.append(
                    SupplyLink(
                        source=stock_code,
                        target=name,
                        relation="customer",
                        evidence=evidence,
                        confidence=0.6,
                    )
                )

        # 공급사 추출
        if any(kw in text for kw in _SUPPLIER_KEYWORDS) or "rawMaterial" in topic:
            names = _extract_company_names(text)
            for name in names:
                suppliers.append(
                    SupplyLink(
                        source=stock_code,
                        target=name,
                        relation="supplier",
                        evidence=evidence,
                        confidence=0.6,
                    )
                )

    # 중복 제거
    customers = _dedupe_links(customers)
    suppliers = _dedupe_links(suppliers)
    related_parties = _dedupe_links(related_parties)

    return customers, suppliers, related_parties


def _extract_company_names(text: str) -> list[str]:
    """텍스트에서 기업명 후보를 추출."""
    matches = _COMPANY_PATTERN.findall(text)
    # 일반 명사 제외
    exclude = {
        "해당",
        "없음",
        "합계",
        "소계",
        "기타",
        "전체",
        "관련",
        "증가",
        "감소",
        "이하",
        "이상",
        "미만",
        "대비",
    }
    return [m.strip() for m in matches if m.strip() not in exclude and len(m.strip()) >= 2]


def _dedupe_links(links: list[SupplyLink]) -> list[SupplyLink]:
    """target 기준 중복 제거 (confidence가 높은 것 유지)."""
    seen: dict[str, SupplyLink] = {}
    for link in links:
        key = link.target
        if key not in seen or link.confidence > seen[key].confidence:
            seen[key] = link
    return list(seen.values())
