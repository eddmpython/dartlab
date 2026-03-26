"""LLM 답변 숫자 검증 — finance 엔진 실제 값과 대조.

LLM이 생성한 답변에서 재무 수치를 추출하고,
Company.finance 실제 값과 비교하여 불일치를 감지한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from dartlab.ai.context.company_adapter import get_headline_ratios


@dataclass
class NumberClaim:
    """LLM 답변에서 추출한 숫자 주장."""

    label: str  # "매출액", "ROE" 등
    value: float  # 정규화된 숫자 (백만원 단위 또는 %)
    unit: str  # "억", "조", "%" 등
    raw_text: str  # 원문


@dataclass
class Mismatch:
    """실제 값과의 불일치."""

    label: str
    claimed: float
    actual: float
    diff_pct: float  # 차이율 (%)
    unit: str


@dataclass
class ValidationResult:
    """검증 결과."""

    claims: list[NumberClaim] = field(default_factory=list)
    mismatches: list[Mismatch] = field(default_factory=list)


# 한국어 재무 용어 → snakeId 매핑
_LABEL_PATTERNS: dict[str, str] = {
    # 손익계산서
    "매출액": "sales",
    "매출": "sales",
    "영업이익": "operating_profit",
    "당기순이익": "net_profit",
    "순이익": "net_profit",
    "매출원가": "cost_of_sales",
    "매출총이익": "gross_profit",
    "판관비": "selling_and_admin",
    "판매관리비": "selling_and_admin",
    "법인세비용": "income_tax_expense",
    "세전이익": "profit_before_tax",
    # 재무상태표
    "자산총계": "total_assets",
    "총자산": "total_assets",
    "부채총계": "total_liabilities",
    "자본총계": "owners_of_parent_equity",
    "유동자산": "current_assets",
    "유동부채": "current_liabilities",
    "재고자산": "inventories",
    "매출채권": "trade_and_other_receivables",
    "매입채무": "trade_and_other_payables",
    "차입금": "short_term_borrowings",
    "이익잉여금": "retained_earnings",
    "유형자산": "tangible_assets",
    # 현금흐름표
    "영업활동CF": "operating_cashflow",
    "영업활동현금흐름": "operating_cashflow",
    "투자활동CF": "investing_cashflow",
    "재무활동CF": "cash_flows_from_financing_activities",
    "현금성자산": "cash_and_cash_equivalents",
}

# 비율 용어 매핑
_RATIO_PATTERNS: dict[str, str] = {
    # 수익성
    "ROE": "roe",
    "ROA": "roa",
    "ROIC": "roic",
    "영업이익률": "operatingMargin",
    "순이익률": "netMargin",
    "매출총이익률": "grossMargin",
    "EBITDA마진": "ebitdaMargin",
    # 안정성
    "부채비율": "debtRatio",
    "유동비율": "currentRatio",
    "당좌비율": "quickRatio",
    "자기자본비율": "equityRatio",
    "이자보상배율": "interestCoverage",
    "순차입금비율": "netDebtRatio",
    # 효율성·활동성
    "총자산회전율": "totalAssetTurnover",
    "매출성장률": "salesGrowth",
    "영업이익성장률": "operatingProfitGrowth",
    # 현금흐름
    "영업CF마진": "operatingCashflowMargin",
    "CAPEX비율": "capexRatio",
    # 밸류에이션·복합
    "배당성향": "dividendPayoutRatio",
    "Piotroski": "piotroskiFScore",
    "피오트로스키": "piotroskiFScore",
    "Altman": "altmanZScore",
    "CCC": "cashConversionCycle",
}

# 숫자 추출 패턴: "매출 1,234억", "매출액 약 30조", "ROE 15.2%"
_NUM_PATTERN = re.compile(
    r"(?P<label>[가-힣A-Z]{2,10})\s*"
    r"(?:약\s*)?(?:[\-−])?(?P<number>[\d,]+(?:\.\d+)?)\s*"
    r"(?P<unit>조|억|만|백만|%|원)"
)

# 단위 → 배수 (백만원 기준)
_UNIT_MULTIPLIER: dict[str, float] = {
    "조": 1e6,  # 1조 = 1,000,000백만
    "억": 1e2,  # 1억 = 100백만
    "만": 1e-2,  # 1만 = 0.01백만
    "백만": 1.0,
    "원": 1e-6,
}


def extract_numbers(text: str) -> list[NumberClaim]:
    """LLM 답변에서 재무 수치 추출."""
    claims = []
    for m in _NUM_PATTERN.finditer(text):
        label = m.group("label").strip()
        num_str = m.group("number").replace(",", "")
        unit = m.group("unit")

        try:
            value = float(num_str)
        except ValueError:
            continue

        # 음수 처리
        prefix = text[max(0, m.start() - 2) : m.start()]
        if "−" in prefix or "-" in prefix:
            value = -value

        claims.append(
            NumberClaim(
                label=label,
                value=value,
                unit=unit,
                raw_text=m.group(0),
            )
        )
    return claims


def validate_claims(claims: list[NumberClaim], company: Any) -> ValidationResult:
    """추출된 숫자를 finance 엔진 실제 값과 대조."""
    result = ValidationResult(claims=claims)

    if not claims:
        return result

    # finance annual series 가져오기
    annual = getattr(company, "annual", None)
    ratios = get_headline_ratios(company)
    if annual is None and ratios is None:
        return result

    series = {}
    if annual is not None:
        raw_series, years = annual
        # 최신 연도 값만 사용
        for sj, sj_data in raw_series.items():
            for snake_id, vals in sj_data.items():
                if vals:
                    latest = next((v for v in reversed(vals) if v is not None), None)
                    if latest is not None:
                        series[snake_id] = latest

    for claim in claims:
        if claim.unit == "%":
            # 비율 검증
            snake_id = _RATIO_PATTERNS.get(claim.label)
            if snake_id and ratios and hasattr(ratios, snake_id):
                actual = getattr(ratios, snake_id)
                if actual is not None:
                    diff_pct = abs(claim.value - actual) / max(abs(actual), 0.01) * 100
                    if diff_pct > 10:
                        result.mismatches.append(
                            Mismatch(
                                label=claim.label,
                                claimed=claim.value,
                                actual=actual,
                                diff_pct=diff_pct,
                                unit="%",
                            )
                        )
        else:
            # 금액 검증 (백만원 기준)
            snake_id = _LABEL_PATTERNS.get(claim.label)
            if snake_id and snake_id in series:
                actual = series[snake_id]  # 백만원 단위
                multiplier = _UNIT_MULTIPLIER.get(claim.unit, 1.0)
                claimed_in_millions = claim.value * multiplier

                if abs(actual) > 0:
                    diff_pct = abs(claimed_in_millions - actual) / abs(actual) * 100
                    if diff_pct > 10:
                        result.mismatches.append(
                            Mismatch(
                                label=claim.label,
                                claimed=claimed_in_millions,
                                actual=actual,
                                diff_pct=diff_pct,
                                unit=claim.unit,
                            )
                        )

    return result


def cross_validate_context(company: Any) -> list[str]:
    """context 내부 수치 일관성 검증.

    IS 정합: 매출 - 매출원가 ≈ 매출총이익
    CF 정합: 영업CF + 투자CF + 재무CF ≈ 현금변동

    Returns:
        경고 메시지 리스트 (비어있으면 정합)
    """
    warnings: list[str] = []
    annual = getattr(company, "annual", None)
    if annual is None:
        return warnings

    raw_series, _years = annual

    def _latest(sj: str, key: str) -> float | None:
        vals = raw_series.get(sj, {}).get(key)
        if not vals:
            return None
        return next((v for v in reversed(vals) if v is not None), None)

    # IS 정합: 매출 - 매출원가 ≈ 매출총이익
    sales = _latest("IS", "sales")
    cogs = _latest("IS", "cost_of_sales")
    gp = _latest("IS", "gross_profit")
    if sales is not None and cogs is not None and gp is not None:
        expected_gp = sales - cogs
        if abs(gp) > 0:
            diff = abs(expected_gp - gp) / abs(gp) * 100
            if diff > 5:
                warnings.append(
                    f"IS 정합 경고: 매출({sales:,.0f}) - 매출원가({cogs:,.0f}) = "
                    f"{expected_gp:,.0f} ≠ 매출총이익({gp:,.0f}), 차이 {diff:.1f}%"
                )

    # CF 정합: 영업CF + 투자CF + 재무CF ≈ 현금변동
    ocf = _latest("CF", "operating_cashflow")
    icf = _latest("CF", "investing_cashflow")
    fcf = _latest("CF", "cash_flows_from_financing_activities")
    if ocf is not None and icf is not None and fcf is not None:
        total_cf = ocf + icf + fcf
        # 현금변동이 0이 아닌 경우만 의미있는 검증
        if abs(total_cf) > 1:
            # 개별 CF 합이 0에 가까우면 정상 (증감이 거의 없는 경우)
            # 여기서는 각 CF의 절대값 합 대비 편차를 본다
            scale = max(abs(ocf), abs(icf), abs(fcf), 1)
            if abs(total_cf) / scale > 0.5:
                # 큰 순현금 변동이 있으면 환율효과 등 누락 가능 → 참고 경고
                warnings.append(
                    f"CF 참고: 영업CF({ocf:,.0f}) + 투자CF({icf:,.0f}) + "
                    f"재무CF({fcf:,.0f}) = {total_cf:,.0f} (환율효과 등 미포함 가능)"
                )

    return warnings


def validate_structured(structured: dict, expected_facts: list[dict]) -> dict:
    """Structured 응답의 metrics에서 직접 name/value 매칭.

    Args:
            structured: {"metrics": [{"name": "sales", "value": 1234}], ...}
            expected_facts: [{"metric": "sales", "value": 1234}]

    Returns:
            {"metrics_found": N, "numeric_facts": N, "matched": N, "coverage": float}
    """
    metrics = structured.get("metrics", [])
    numeric_facts = [f for f in expected_facts if isinstance(f.get("value"), (int, float))]

    matched = 0
    for fact in numeric_facts:
        expected_val = fact["value"]
        expected_name = fact.get("metric", "")

        for m in metrics:
            if m.get("name") == expected_name:
                actual_val = m.get("value")
                if actual_val is not None and expected_val != 0:
                    if abs(actual_val - expected_val) / abs(expected_val) < 0.15:
                        matched += 1
                        break

    return {
        "metrics_found": len(metrics),
        "numeric_facts": len(numeric_facts),
        "matched": matched,
        "coverage": round(matched / max(len(numeric_facts), 1) * 100, 1),
    }
