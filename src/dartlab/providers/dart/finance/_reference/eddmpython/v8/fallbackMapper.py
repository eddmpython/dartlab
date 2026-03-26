"""Fallback 매퍼 - 미매핑 계정을 적절한 'other' 계정으로 분류

v8 ParquetMapper에서 매핑 실패 시 사용하는 fallback 로직.
재무제표 합계 정확성을 위해 미매핑 계정도 적절한 분류로 포함.
"""

from typing import Optional


class FallbackMapper:
    """미매핑 계정을 적절한 'other' 계정으로 분류"""

    # 재무상태표 (BS) fallback 규칙
    BS_FALLBACK = {
        # 자산 키워드
        "자산": "other_noncurrent_assets",  # 기본: 기타비유동자산
        "현금": "other_current_assets",
        "예금": "other_current_assets",
        "금융상품": "other_current_financial_assets",
        "금융자산": "other_current_financial_assets",
        "투자": "other_noncurrent_financial_assets",
        "투자자산": "other_noncurrent_financial_assets",
        "관계기업": "investments_in_associates",  # 지분법 투자
        "종속기업": "investments_in_subsidiaries",  # 종속기업 투자
        "공동기업": "investments_in_joint_ventures",  # 공동기업 투자
        "채권": "other_noncurrent_receivables",
        "미수": "other_current_receivables",
        "매출채권": "trade_and_other_current_receivables",
        "선급": "other_current_assets",
        "재고": "inventories",
        "유형자산": "property_plant_equipment",
        "무형자산": "intangible_assets",
        "영업권": "goodwill",
        "리스": "other_leased_assets",
        "보증금": "other_current_assets",
        # 부채 키워드
        "부채": "other_noncurrent_liabilities",  # 기본: 기타비유동부채
        "차입": "other_noncurrent_borrowings",
        "차입금": "other_noncurrent_borrowings",
        "사채": "bonds",
        "매입채무": "trade_and_other_current_payables",
        "미지급": "other_current_liabilities",
        "선수": "other_current_liabilities",
        "예수": "other_current_liabilities",
        "충당부채": "other_noncurrent_provisions",
        "퇴직급여": "retirement_benefit_liabilities",
        "리스부채": "lease_liabilities",
        "파생상품부채": "other_current_financial_liabilities",
        # 자본 키워드
        "자본": "other_equity_components",
        "자본금": "capital_stock",
        "잉여금": "other_reserves",
        "적립금": "other_reserves",
        "비지배": "noncontrolling_interests",
    }

    # 손익계산서 (IS) fallback 규칙
    IS_FALLBACK = {
        "매출": "revenue",
        "수익": "other_operating_income",
        "영업수익": "revenue",
        "원가": "cost_of_sales",
        "비용": "other_operating_expenses",
        "판매비": "selling_expenses",
        "관리비": "administrative_expenses",
        "영업이익": "operating_income",
        "영업외수익": "other_nonoperating_income",
        "영업외비용": "other_nonoperating_expenses",
        "금융수익": "finance_income",
        "금융비용": "finance_costs",
        "이자수익": "interest_income",
        "이자비용": "interest_expense",
        "배당": "dividend_income",
        "지분법": "share_of_profit_of_associates",
        "법인세": "income_tax_expense",
        "손익": "net_income",
        "순이익": "net_income",
        "이익": "other_income",
        "손실": "other_expenses",
        "손상차손": "impairment_loss",
        "감가상각": "depreciation",
        "상각": "amortization",
        "주당이익": "earnings_per_share",
    }

    # 현금흐름표 (CF) fallback 규칙
    CF_FALLBACK = {
        "영업활동": "cash_flows_from_operating_activities",
        "투자활동": "cash_flows_from_investing_activities",
        "재무활동": "cash_flows_from_financing_activities",
        "현금": "other_cash_flows",
        "이자": "interest_paid",
        "배당": "dividends_paid",
        "법인세": "income_taxes_paid",
        "자산": "other_adjustments",
        "부채": "other_adjustments",
        "취득": "purchase_of_property_plant_and_equipment",
        "처분": "disposal_of_tangible_assets",
        "증가": "other_adjustments",
        "감소": "other_adjustments",
        "차입": "proceeds_from_borrowings",
        "상환": "repayment_of_borrowings",
    }

    # 포괄손익계산서 (CIS) fallback 규칙
    CIS_FALLBACK = {
        "당기순이익": "net_income",
        "기타포괄손익": "other_comprehensive_income",
        "총포괄이익": "comprehensive_income",
        "재분류": "other_comprehensive_income",
        "평가": "other_comprehensive_income",
    }

    # 자본변동표 (SCE) fallback 규칙
    SCE_FALLBACK = {
        "기초": "equity_at_beginning_of_period",
        "기말": "equity_at_end_of_period",
        "자본": "other_changes_in_equity",
        "배당": "dividends",
        "순이익": "net_income",
        "포괄이익": "comprehensive_income",
        "자기주식": "treasury_stock_transactions",
    }

    def __init__(self):
        # 재무제표별 fallback 규칙
        self._rules = {
            1: self.BS_FALLBACK,  # BS
            2: self.IS_FALLBACK,  # IS
            4: self.CF_FALLBACK,  # CF
            8: self.SCE_FALLBACK,  # SCE
            # CIS는 IS와 동일
        }

    def getFallback(self, accountName: str, statementKind: Optional[int] = None) -> str:
        """미매핑 계정의 fallback snakeId 반환

        Args:
            accountName: 계정명
            statementKind: 재무제표종류 (1=BS, 2=IS, 4=CF, 8=SCE)

        Returns:
            fallback snakeId
        """
        if not accountName:
            return "other_accounts"

        # 재무제표별 규칙 선택
        if statementKind == 2:  # CIS도 IS 규칙 사용
            rules = self.IS_FALLBACK
        else:
            rules = self._rules.get(statementKind, {})

        if not rules:
            return "other_accounts"

        # 키워드 매칭 (우선순위 순서)
        for keyword, fallback in rules.items():
            if keyword in accountName:
                return fallback

        # 기본 fallback (재무제표별)
        if statementKind == 1:  # BS
            # 자산/부채/자본 구분
            if "자산" in accountName:
                if "유동" in accountName or "단기" in accountName:
                    return "other_current_assets"
                else:
                    return "other_noncurrent_assets"
            elif "부채" in accountName:
                if "유동" in accountName or "단기" in accountName:
                    return "other_current_liabilities"
                else:
                    return "other_noncurrent_liabilities"
            elif "자본" in accountName or "지분" in accountName:
                return "other_equity_components"
            else:
                # 키워드 없으면 기타비유동자산 (보수적)
                return "other_noncurrent_assets"

        elif statementKind == 2:  # IS
            if "수익" in accountName or "매출" in accountName:
                return "other_operating_income"
            elif "비용" in accountName or "원가" in accountName:
                return "other_operating_expenses"
            else:
                return "other_income"

        elif statementKind == 4:  # CF
            return "other_adjustments"

        elif statementKind == 8:  # SCE
            return "other_changes_in_equity"

        return "other_accounts"

    def getFallbackWithReason(self, accountName: str, statementKind: Optional[int] = None) -> tuple[str, str]:
        """Fallback과 이유 반환

        Returns:
            (fallback snakeId, reason)
        """
        fallback = self.getFallback(accountName, statementKind)

        # 이유 추출
        if statementKind == 1:
            if "자산" in accountName:
                if "유동" in accountName:
                    reason = "유동자산 키워드 → other_current_assets"
                else:
                    reason = "비유동자산 키워드 → other_noncurrent_assets"
            elif "부채" in accountName:
                if "유동" in accountName:
                    reason = "유동부채 키워드 → other_current_liabilities"
                else:
                    reason = "비유동부채 키워드 → other_noncurrent_liabilities"
            elif "자본" in accountName:
                reason = "자본 키워드 → other_equity_components"
            else:
                reason = "기본 BS fallback"
        elif statementKind == 2:
            if "수익" in accountName:
                reason = "수익 키워드 → other_operating_income"
            elif "비용" in accountName:
                reason = "비용 키워드 → other_operating_expenses"
            else:
                reason = "기본 IS fallback"
        elif statementKind == 4:
            reason = "CF fallback → other_adjustments"
        elif statementKind == 8:
            reason = "SCE fallback → other_changes_in_equity"
        else:
            reason = "기본 fallback"

        return (fallback, reason)
