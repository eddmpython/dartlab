"""인건비 효율 지표 — 인건비율, 1인당 부가가치."""

from __future__ import annotations

from dartlab.scan._helpers import scan_finance_parquets
from dartlab.scan.workforce.scanner import scan_employee, scan_total_payroll

REVENUE_IDS = {
    "Revenue",
    "Revenues",
    "revenue",
    "revenues",
    "ifrs-full_Revenue",
    "dart_Revenue",
    "RevenueFromContractsWithCustomers",
}
REVENUE_NMS = {"매출액", "수익(매출액)", "영업수익", "매출", "순영업수익"}

OP_IDS = {
    "dart_OperatingIncomeLoss",
    "ifrs-full_ProfitLossFromOperatingActivities",
    "OperatingIncomeLoss",
}
OP_NMS = {"영업이익", "영업이익(손실)", "영업손익"}


def _revenueMap() -> dict[str, float]:
    """전종목 매출(원) → {종목코드: 매출}."""
    return scan_finance_parquets("IS", REVENUE_IDS, REVENUE_NMS)


def _opIncomeMap() -> dict[str, float]:
    """전종목 영업이익(원) → {종목코드: 영업이익}."""
    return scan_finance_parquets("IS", OP_IDS, OP_NMS)


def scan_labor_ratio() -> dict[str, float]:
    """총급여/매출 → {종목코드: 인건비율(%)}.

    인건비율이 높을수록 매출 중 인건비 비중이 크다.
    """
    payrollMap = scan_total_payroll()
    revMap = _revenueMap()

    result: dict[str, float] = {}
    for code, payroll in payrollMap.items():
        rev = revMap.get(code)
        if rev and rev > 0:
            ratio = payroll / rev * 100
            if 0 < ratio < 500:
                result[code] = round(ratio, 1)
    return result


def scan_value_added() -> dict[str, float]:
    """(영업이익+총급여)/직원수 → {종목코드: 1인당부가가치(억)}.

    부가가치 = 영업이익 + 인건비.  직원 1명이 만들어내는 가치.
    """
    payrollMap = scan_total_payroll()
    opMap = _opIncomeMap()
    empMap = scan_employee()

    result: dict[str, float] = {}
    for code, payroll in payrollMap.items():
        opIncome = opMap.get(code)
        empInfo = empMap.get(code)
        if opIncome is None or empInfo is None:
            continue
        headcount = empInfo.get("직원수", 0)
        if headcount and headcount > 0:
            valueAdded = (opIncome + payroll) / headcount / 1e8
            result[code] = round(valueAdded, 1)
    return result
