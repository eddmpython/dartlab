import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")

from core.dart.searchDart.finance.v7.synonymLearner import SynonymLearner

sl = SynonymLearner()
fs = sl._getFinanceSearch()
corpDf = fs.getCorpList()
codes = corpDf["stock_code"].drop_nulls().to_list()

allUnmatched = set()
for code in codes:
    try:
        r = sl.analyzeCompany(code)
        if r and 1 <= r.unmatchedCount <= 5:
            for acc in r.unmatched:
                allUnmatched.add(acc)
    except:
        pass

print(f"미매핑 계정: {len(allUnmatched)}개")

keywordMap = {
    "차입금": "borrowings",
    "장기차입": "longterm_borrowings",
    "단기차입": "shortterm_borrowings",
    "유동성장기": "current_portion_of_longterm_debt",
    "사채": "bonds",
    "감가상각": "depreciationcash_flow",
    "상각비": "depreciationcash_flow",
    "법인세": "income_taxes",
    "배당": "dividends",
    "이자수익": "interest_income",
    "이자비용": "interest_expenses",
    "매출채권": "trade_and_other_receivables",
    "매입채무": "trade_and_other_payables",
    "재고자산": "inventories",
    "유형자산": "tangible_assets",
    "무형자산": "intangible_assets",
    "투자부동산": "investment_in_properties",
    "보증금": "longterm_gurarantee",
    "선급금": "advance_payments",
    "선수금": "advance_from_customers",
    "미지급금": "other_payables",
    "미수금": "other_receivables",
    "대여금": "shortterm_loans",
    "리스부채": "lease_obligations",
    "사용권자산": "leasedrightofuse_assets",
    "리스자산": "leasedrightofuse_assets",
    "충당부채": "longterm_provisions",
    "충당금": "longterm_provisions",
    "퇴직급여": "defined_benefit_liabilities",
    "확정급여": "defined_benefit_liabilities",
    "주식선택권": "stock_options",
    "주식매수선택권": "stock_options",
    "주식보상": "stock_options",
    "자기주식": "treasury_stock",
    "종속기업": "investments_in_subsidiaries",
    "관계기업": "investments_in_associates",
    "지분법": "gains_on_valuation_of_equity_method_securitiesequity_method_note",
    "파생상품": "shortterm_derivative_assets",
    "파생금융": "shortterm_derivative_assets",
    "전환사채": "longterm_borrowings",
    "전환권": "consideration_for_conversion_rights",
    "신주인수권": "stock_warrants_conversion_rights",
    "해외사업환산": "reserve_of_exchange_differences_on_translation",
    "환율변동": "difference_by_changes_in_foreign_exchange_rates",
    "외화환산": "losses_on_foreign_currency_translation",
    "합병": "change_by_merger_and_acquisition",
    "영업양수": "cash_inflows_by_merger_and_acquisition",
    "이익잉여금": "retained_earnings",
    "자본잉여금": "other_capital_surplus",
    "정부보조금": "government_grants_deferred_income",
    "국고보조금": "government_grants_deferred_income",
    "연구개발": "usual_development_and_research_expenses",
    "복구충당": "provisions_for_restoration_costs",
    "공정가치측정금융자산": "financial_assets_measured_at_fair_value_through_profit_or_loss",
    "기타포괄손익-공정가치": "financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "기타포괄손익공정가치": "financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "매도가능": "financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "중단영업": "discontinued_operating_incomeloss",
    "계속영업": "profit_from_continuing_operations",
    "임대보증금": "leasehold_deposits_received",
    "매각예정": "noncurrent_asset_held_for_sale_or_disposal_group",
    "영업활동": "cash_flows_from_operating_activities",
    "투자활동": "cash_flows_from_investing_activities",
    "재무활동": "cash_flows_from_financing_activities",
    "현금성자산": "cash_and_cash_equivalents",
    "예치금": "other_due_from_banks",
    "비지배지분": "noncontrolling_interests_equity",
    "재평가": "revaluation_surplus",
    "토지": "land",
    "건물": "buildings",
    "차량운반구": "motor_vehicles",
    "기계장치": "machinery_and_equipment",
}

autoMappings = {}
alreadyLearned = set(sl._synonyms.keys())

for acc in allUnmatched:
    if acc in alreadyLearned:
        continue
    for keyword, snakeId in keywordMap.items():
        if keyword in acc and snakeId in sl._snakeToKor:
            autoMappings[acc] = snakeId
            break

print(f"자동 매핑 후보: {len(autoMappings)}개")

count = sl.learnBatch(autoMappings)
print(f"학습: {count}개")
print(f"동의어: {sl.synonymCount}")
