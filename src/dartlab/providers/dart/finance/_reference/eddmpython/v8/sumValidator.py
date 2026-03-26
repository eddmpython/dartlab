"""재무제표 합계 검증 시스템

미매핑 계정을 'other' 계정으로 fallback 매핑한 후
재무제표 공식이 정확한지 검증합니다.

검증 항목:
1. BS: 자산총계 = 부채총계 + 자본총계
2. BS: 유동자산 + 비유동자산 = 자산총계
3. IS: 매출총이익 = 매출액 - 매출원가
4. IS: 당기순이익 = 법인세비용차감전순이익 - 법인세비용
5. CF: 영업 + 투자 + 재무 = 현금증감
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

import polars as pl


@dataclass
class ValidationResult:
    """검증 결과"""

    formula: str
    expected: Optional[float]
    actual: Optional[float]
    diffPct: Optional[float]
    isValid: bool
    message: str


class SumValidator:
    """재무제표 합계 검증기"""

    def __init__(self, tolerance: float = 0.01):
        """
        Args:
            tolerance: 허용 오차 비율 (기본 1% = 0.01)
        """
        self.tolerance = tolerance

    def validateBalanceSheet(self, data: Dict[str, Optional[float]], period: str = None) -> List[ValidationResult]:
        """재무상태표 검증

        Args:
            data: {snakeId: amount} 딕셔너리
            period: 검증 기간 (로그용)

        Returns:
            검증 결과 리스트
        """
        results = []

        # 1. 자산 = 부채 + 자본
        assets = data.get("total_assets")
        liabilities = data.get("total_liabilities")
        # Check both total_equity and total_stockholders_equity
        equity = data.get("total_equity") or data.get("total_stockholders_equity") or data.get("stockholders_equity")

        if assets is not None and liabilities is not None and equity is not None:
            expected = liabilities + equity
            diffPct = abs((assets - expected) / assets * 100) if assets != 0 else (100 if expected != 0 else 0)
            isValid = diffPct <= (self.tolerance * 100)

            results.append(
                ValidationResult(
                    formula="total_assets = total_liabilities + total_equity",
                    expected=expected,
                    actual=assets,
                    diffPct=diffPct,
                    isValid=isValid,
                    message=f"자산총계 균형: {diffPct:.2f}% 오차" if not isValid else "OK",
                )
            )

        # 2. 자산총계 = 유동자산 + 비유동자산
        currentAssets = data.get("current_assets")
        noncurrentAssets = data.get("noncurrent_assets") or data.get("non_current_assets")

        if assets is not None and currentAssets is not None and noncurrentAssets is not None:
            expected = currentAssets + noncurrentAssets
            diffPct = abs((assets - expected) / assets * 100) if assets != 0 else (100 if expected != 0 else 0)
            isValid = diffPct <= (self.tolerance * 100)

            results.append(
                ValidationResult(
                    formula="total_assets = current_assets + noncurrent_assets",
                    expected=expected,
                    actual=assets,
                    diffPct=diffPct,
                    isValid=isValid,
                    message=f"자산 분류 합계: {diffPct:.2f}% 오차" if not isValid else "OK",
                )
            )

        # 3. 부채총계 = 유동부채 + 비유동부채
        currentLiabilities = data.get("current_liabilities")
        noncurrentLiabilities = data.get("noncurrent_liabilities") or data.get("non_current_liabilities")

        if liabilities is not None and currentLiabilities is not None and noncurrentLiabilities is not None:
            expected = currentLiabilities + noncurrentLiabilities
            diffPct = (
                abs((liabilities - expected) / liabilities * 100) if liabilities != 0 else (100 if expected != 0 else 0)
            )
            isValid = diffPct <= (self.tolerance * 100)

            results.append(
                ValidationResult(
                    formula="total_liabilities = current_liabilities + noncurrent_liabilities",
                    expected=expected,
                    actual=liabilities,
                    diffPct=diffPct,
                    isValid=isValid,
                    message=f"부채 분류 합계: {diffPct:.2f}% 오차" if not isValid else "OK",
                )
            )

        return results

    def validateIncomeStatement(self, data: Dict[str, Optional[float]], period: str = None) -> List[ValidationResult]:
        """손익계산서 검증

        Args:
            data: {snakeId: amount} 딕셔너리
            period: 검증 기간 (로그용)

        Returns:
            검증 결과 리스트
        """
        results = []

        # 1. 매출총이익 = 매출액 - 매출원가
        revenue = data.get("revenue")
        costOfSales = data.get("cost_of_sales")
        grossProfit = data.get("gross_profit")

        if revenue is not None and costOfSales is not None and grossProfit is not None:
            expected = revenue - costOfSales
            diffPct = (
                abs((grossProfit - expected) / grossProfit * 100) if grossProfit != 0 else (100 if expected != 0 else 0)
            )
            isValid = diffPct <= (self.tolerance * 100)

            results.append(
                ValidationResult(
                    formula="gross_profit = revenue - cost_of_sales",
                    expected=expected,
                    actual=grossProfit,
                    diffPct=diffPct,
                    isValid=isValid,
                    message=f"매출총이익 공식: {diffPct:.2f}% 오차" if not isValid else "OK",
                )
            )

        # 2. 당기순이익 = 법인세비용차감전순이익 - 법인세비용
        profitBeforeTax = data.get("profit_before_tax")
        taxExpense = data.get("income_tax_expense")
        netIncome = data.get("net_income") or data.get("net_profit")

        if profitBeforeTax is not None and taxExpense is not None and netIncome is not None:
            expected = profitBeforeTax - taxExpense
            diffPct = abs((netIncome - expected) / netIncome * 100) if netIncome != 0 else (100 if expected != 0 else 0)
            isValid = diffPct <= (self.tolerance * 100)

            results.append(
                ValidationResult(
                    formula="net_income = profit_before_tax - tax_expense",
                    expected=expected,
                    actual=netIncome,
                    diffPct=diffPct,
                    isValid=isValid,
                    message=f"당기순이익 공식: {diffPct:.2f}% 오차" if not isValid else "OK",
                )
            )

        return results

    def validateCashFlow(self, data: Dict[str, Optional[float]], period: str = None) -> List[ValidationResult]:
        """현금흐름표 검증

        Args:
            data: {snakeId: amount} 딕셔너리
            period: 검증 기간 (로그용)

        Returns:
            검증 결과 리스트
        """
        results = []

        # 영업 + 투자 + 재무 = 현금증감
        operating = data.get("cash_flows_from_operating_activities")
        investing = data.get("cash_flows_from_investing_activities")
        financing = data.get("cash_flows_from_financing_activities")
        netChange = data.get("increase_decrease_in_cash_and_cash_equivalents") or data.get(
            "increasedecrease_in_cash_and_cash_equivalents"
        )

        if operating is not None and investing is not None and financing is not None and netChange is not None:
            expected = operating + investing + financing
            diffPct = abs((netChange - expected) / netChange * 100) if netChange != 0 else (100 if expected != 0 else 0)
            isValid = diffPct <= (self.tolerance * 100)

            results.append(
                ValidationResult(
                    formula="net_change = operating + investing + financing",
                    expected=expected,
                    actual=netChange,
                    diffPct=diffPct,
                    isValid=isValid,
                    message=f"현금흐름 합계: {diffPct:.2f}% 오차" if not isValid else "OK",
                )
            )

        return results

    def aggregateBySnakeId(self, df: pl.DataFrame, period: str) -> Dict[str, float]:
        """snakeId별 합계 계산

        같은 snakeId가 여러 행에 있을 수 있으므로 합산
        (예: 'other_current_assets'에 여러 미매핑 계정이 fallback)

        Args:
            df: 재무 데이터 (single period)
            period: 기간 컬럼명

        Returns:
            {snakeId: total_amount}
        """
        if period not in df.columns:
            return {}

        # Group by snakeId and sum
        aggregated = df.group_by("snakeId").agg(pl.col(period).sum().alias("total"))

        result = {}
        for row in aggregated.iter_rows(named=True):
            snakeId = row["snakeId"]
            total = row["total"]
            if snakeId and total is not None:
                result[snakeId] = total

        return result

    def validateCompany(
        self, stockCode: str, period: str, bsData: Dict[str, float], isData: Dict[str, float], cfData: Dict[str, float]
    ) -> Dict[str, List[ValidationResult]]:
        """회사별 전체 검증

        Args:
            stockCode: 종목코드
            period: 기간
            bsData: BS 데이터 {snakeId: amount}
            isData: IS 데이터 {snakeId: amount}
            cfData: CF 데이터 {snakeId: amount}

        Returns:
            {statement: [ValidationResult]}
        """
        return {
            "BS": self.validateBalanceSheet(bsData, period),
            "IS": self.validateIncomeStatement(isData, period),
            "CF": self.validateCashFlow(cfData, period),
        }

    def printValidationReport(self, stockCode: str, period: str, results: Dict[str, List[ValidationResult]]):
        """검증 결과 출력

        Args:
            stockCode: 종목코드
            period: 기간
            results: 검증 결과
        """
        print(f"\n{'=' * 90}")
        print(f"재무제표 합계 검증: {stockCode} - {period}")
        print(f"{'=' * 90}\n")

        totalChecks = 0
        passedChecks = 0

        for statement, validations in results.items():
            if not validations:
                continue

            print(f"{statement}:")
            for v in validations:
                totalChecks += 1
                status = "✅" if v.isValid else "❌"
                if v.isValid:
                    passedChecks += 1

                print(f"  {status} {v.formula}")
                if v.expected is not None and v.actual is not None:
                    print(f"     예상: {v.expected:,.0f} | 실제: {v.actual:,.0f} | 오차: {v.diffPct:.2f}%")
                print(f"     {v.message}")
            print()

        successRate = (passedChecks / totalChecks * 100) if totalChecks > 0 else 0
        print(f"검증 통과율: {passedChecks}/{totalChecks} ({successRate:.1f}%)")
        print(f"{'=' * 90}\n")
