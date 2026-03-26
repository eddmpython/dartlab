"""공급망 리스크 스코어링.

추출된 공급망 관계에서 집중도, 관계자 거래 비중 등을 평가한다.
"""

from __future__ import annotations

from dartlab.analysis.strategy.supply.types import SupplyChainResult, SupplyLink


def score_supply_risk(
    customers: list[SupplyLink],
    suppliers: list[SupplyLink],
    related_parties: list[SupplyLink],
) -> tuple[float, float, list[str]]:
    """공급망 리스크 점수 계산.

    Args:
        customers: 고객 목록.
        suppliers: 공급사 목록.
        related_parties: 관계자 목록.

    Returns:
        (concentration_hhi, risk_score, risk_factors) 튜플.
    """
    risk_factors: list[str] = []
    risk_score = 0.0

    total_links = len(customers) + len(suppliers)

    # 1. 고객 집중도 (30점)
    if len(customers) == 0:
        concentration = 0.0
        risk_factors.append("고객 정보 미공시")
        risk_score += 15  # 정보 부족 리스크
    elif len(customers) == 1:
        concentration = 1.0
        risk_score += 30
        risk_factors.append(f"단일 고객 의존: {customers[0].target}")
    elif len(customers) <= 3:
        concentration = 1.0 / len(customers)
        risk_score += 20
        risk_factors.append(f"고객 집중 ({len(customers)}개사)")
    else:
        concentration = 1.0 / len(customers)
        risk_score += 5

    # 2. 공급사 집중도 (30점)
    if len(suppliers) == 0:
        risk_factors.append("공급사 정보 미공시")
        risk_score += 10
    elif len(suppliers) == 1:
        risk_score += 30
        risk_factors.append(f"단일 공급사 의존: {suppliers[0].target}")
    elif len(suppliers) <= 3:
        risk_score += 15
        risk_factors.append(f"공급사 집중 ({len(suppliers)}개사)")
    else:
        risk_score += 5

    # 3. 관계자거래 비중 (20점)
    if related_parties:
        rp_ratio = len(related_parties) / max(total_links, 1)
        if rp_ratio > 0.5:
            risk_score += 20
            risk_factors.append(f"관계자거래 비중 높음 ({len(related_parties)}건)")
        elif rp_ratio > 0.2:
            risk_score += 10
            risk_factors.append(f"관계자거래 {len(related_parties)}건")

    # 4. 정보 투명도 (20점)
    if total_links == 0:
        risk_score += 20
        risk_factors.append("공급망 정보 전무")
    elif total_links < 3:
        risk_score += 10
        risk_factors.append("공급망 공시 불충분")

    risk_score = min(risk_score, 100)

    return concentration, risk_score, risk_factors


def analyze_supply_chain(company: object) -> SupplyChainResult | None:
    """단일 기업의 공급망 분석.

    Args:
        company: dartlab Company 객체.

    Returns:
        SupplyChainResult 또는 None.
    """
    from dartlab.analysis.strategy.supply.extractor import extract_supply_links

    stock_code = getattr(company, "stockCode", "")
    corp_name = getattr(company, "corpName", None)
    market = getattr(company, "market", "KR")

    customers, suppliers, related_parties = extract_supply_links(company)

    # 기업명 → 종목코드 매칭 시도
    try:
        from dartlab.analysis.strategy.supply.mapper import resolve_links

        customers = resolve_links(customers, market=market)
        suppliers = resolve_links(suppliers, market=market)
    except ImportError:
        pass

    concentration, risk_score, risk_factors = score_supply_risk(
        customers,
        suppliers,
        related_parties,
    )

    return SupplyChainResult(
        stockCode=stock_code,
        corpName=corp_name,
        customers=customers,
        suppliers=suppliers,
        relatedParties=related_parties,
        concentration=round(concentration, 4),
        riskScore=round(risk_score, 1),
        riskFactors=risk_factors,
    )
