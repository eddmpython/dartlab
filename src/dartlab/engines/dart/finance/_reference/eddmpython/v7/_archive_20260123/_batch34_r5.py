import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from core.dart.searchDart.finance.v7.synonymLearner import SynonymLearner

sl = SynonymLearner()
fs = sl._getFinanceSearch()
corpDf = fs.getCorpList()
codes = corpDf["stock_code"].drop_nulls().to_list()

allUnmatched = set()
alreadyLearned = set(sl._synonyms.keys())
for code in codes:
    try:
        r = sl.analyzeCompany(code)
        for acc in r.unmatched:
            if acc not in alreadyLearned:
                allUnmatched.add(acc)
    except:
        pass

print(f"Remaining: {len(allUnmatched)}")

keywordMap5 = {
    "공정가치측정지분상품평가": "gainslosses_on_valuation_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "공정가치측정금융상품": "designatedfinancial_assets_at_fv_through_profit",
    "공정가치측정금웅": "designatedfinancial_assets_at_fv_through_profit",
    "공정가치측정융자산": "designatedfinancial_assets_at_fv_through_profit",
    "공정가치평가": "gains_on_valuations_of_derivatives",
    "공정가치이익": "gains_on_valuations_of_derivatives",
    "공정가치채무상품": "designatedfinancial_assets_at_fv_through_profit",
    "공정가치로측정": "designatedfinancial_assets_at_fv_through_profit",
    "공정가치위험회피": "gains_on_derivatives_for_hedge",
    "공정가치금용": "designatedfinancial_assets_at_fv_through_profit",
    "공정가치금유": "designatedfinancial_assets_at_fv_through_profit",
    "공정가치측정": "designatedfinancial_assets_at_fv_through_profit",
    "관계사": "gainslosses_in_subsidiaries",
    "관계업": "gainslosses_in_subsidiaries",
    "관계이업": "gainslosses_in_subsidiaries",
    "관계법인": "gainslosses_in_subsidiaries",
    "관련기업": "gainslosses_in_subsidiaries",
    "관계및공동기업": "gainslosses_in_subsidiaries",
    "관계기투자": "investments_in_associates",
    "관게기업": "investments_in_associates",
    "관계(공동)기업": "gainslosses_in_subsidiaries",
    "금융보증": "guarantee_contracts_provisions",
    "금융지급보증": "guarantee_contracts_provisions",
    "금융리스지산": "finance_lease_receivables",
    "금융리스해지": "other_expenses",
    "금융계약보증": "guarantee_contracts_provisions",
    "금융상품거래손실": "losses_on_transactions_of_derivatives",
    "금융상품거래이익": "gains_on_transactions_of_derivatives",
    "금융상품처분": "gains_on_disposal_of_assets",
    "금융상품투자": "longterm_financial_assets",
    "금융상품평가": "gains_on_valuations_of_derivatives",
    "금융상평가": "gains_on_valuations_of_derivatives",
    "금융순손": "other_expenses",
    "금융이익": "other_income",
    "금융채권": "other_receivables",
    "금융투자": "longterm_financial_assets",
    "금융평가": "gains_on_valuations_of_derivatives",
    "금리스왑": "swaptransaction",
    "금웅보증": "guarantee_contracts_provisions",
    "금융기관계치금": "other_current_liabilities",
    "기타금융부채": "other_current_liabilities",
    "기타금융부재": "other_noncurrent_liabilities",
    "기타금융부태": "other_noncurrent_liabilities",
    "기타금융자사": "other_noncurrent_assets",
    "기타금융자의": "other_noncurrent_assets",
    "기타금융상품의감소": "decrease_in_shortterm_financial_instruments",
    "기타금융상품평가": "gains_on_valuations_of_derivatives",
    "기타금융업투자": "gains_on_valuation_of_investments",
    "공연투자자산": "other_noncurrent_assets",
    "공장이전보상": "other_income",
    "공채의감소": "decrease_in_longterm_financial_instruments",
    "관광수탁금": "other_current_liabilities",
    "관광진흥개발기금": "other_expenses",
    "관리보수": "salaries",
    "관리운용순익": "other_income",
    "관세금": "other_expenses",
    "교환권청산": "other_reserves",
    "교환권파생부채": "derivative_liabilities",
    "구조조정": "other_expenses",
    "국공채": "government_and_public_bonds",
    "국고부조금": "government_grants",
    "국고조금": "government_grants",
    "국고출연금": "government_grants",
    "국보고조금": "government_grants",
    "국민연금": "plan_assets",
    "국면연금": "plan_assets",
    "기술료": "other_expenses",
    "기술이전료": "other_income",
    "기술가치": "other_intangible_assets",
    "기술적가치": "other_intangible_assets",
    "기업결합": "change_by_merger_and_acquisition",
    "기준서제1109호": "accumulated_effect_of_accounting_policy_change",
    "기초(재작성)": "accumulated_effect_of_accounting_policy_change",
    "기초수정": "accumulated_effect_of_accounting_policy_change",
    "기초오류수정": "gainslosses_on_prior_period_error_corrections",
    "기초현금자산": "cash_and_cash_equivalents",
    "기초재품재고": "finished_goods",
    "기초제품재고": "finished_goods",
    "기말재고액": "finished_goods",
    "기말제품재고": "finished_goods",
    "기말의현금": "cash_and_cash_equivalents",
    "기본주당계속사업": "eps",
    "기본주당중단": "eps",
    "기본주당지배": "eps",
    "기본주당손": "eps",
    "기본및희석주당": "eps",
    "기본주및희석": "eps",
    "기본희석주당": "eps",
    "기순이익": "net_profit",
    "기능통화": "difference_by_changes_in_foreign_exchange_rates",
    "기대신용손실": "allowance_for_bad_debts",
    "기부금조정": "other_adjustments",
    "기타거래사항": "other_reserves",
    "기타고정부채": "other_noncurrent_liabilities",
    "금형의증가": "acquisition_of_tangible_assets",
    "급료와임금": "salaries",
    "국내제품매출": "sales_of_finished_goods",
    # Additional patterns
    "지배회사이익": "net_profitowners_of_parent_equity",
    "희석주당": "diluted_eps",
    "사채상환": "repayments_of_bonds",
    "사채의상환": "repayments_of_bonds",
    "사채의발행": "issuance_of_bonds",
    "전환사채": "convertible_bonds",
    "신주인수권부": "bonds_with_warrants",
    "전환권": "conversion_rights",
    "신주인수권": "stock_warrants",
    "매출원가": "cost_of_sales",
    "매출총이익": "gross_profit",
    "영업이익": "operating_income",
    "법인세비용": "income_taxes_expenses",
    "법인세차감": "income_before_income_taxes",
    "이자수익": "interest_income",
    "이자비용": "interest_expenses",
    "배당수익": "dividend_income",
    "배당금수익": "dividend_income",
    "임대수익": "rental_income",
    "임대료수익": "rental_income",
    "로열티수익": "other_income",
    "수수료수익": "commission_income",
    "수수료비용": "commission_expenses",
    "대손상각비": "allowance_for_bad_debts",
    "대손충당금": "allowance_for_bad_debts",
    "재고자산평가": "impairment_losses_on_inventories",
    "감가상각비": "depreciation",
    "무형자산상각": "amortization",
    "유형자산처분": "gains_on_disposal_of_tangible_assets",
    "유형자산폐기": "losses_on_disposal_of_tangible_assets",
    "유형자산취득": "acquisition_of_tangible_assets",
    "무형자산취득": "acquisition_of_intangible_assets",
    "무형자산처분": "gains_on_disposal_of_intangible_assets",
    "자기주식취득": "acquisition_of_treasury_stock",
    "자기주식처분": "sale_of_treasury_stock",
    "배당금지급": "dividends_paid",
    "배당금의지급": "dividends_paid",
    "지급보증": "assets_guarantee_contracts",
    "종속기업투자": "investments_in_subsidiaries",
    "종속기업처분": "gains_on_disposition_of_subsidiaries",
    "영업권손상": "impairment_losses_on_goodwill",
    "주당순이익": "eps",
    "주당이익": "eps",
    "주당손실": "eps",
    "기초현금": "cash_and_cash_equivalents",
    "기말현금": "cash_and_cash_equivalents",
    "현금성자산": "cash_and_cash_equivalents",
    "매도가능금융": "longterm_availableforsale_financial_assets",
    "장기매도가능": "longterm_availableforsale_financial_assets",
    "단기매도가능": "shortterm_availableforsale_financial_assets",
    "만기보유": "longterm_held_to_maturity_investments",
    "확정급여": "noncurrent_provisions_for_employee_benefits",
    "퇴직급여": "provision_for_retirement_allowance",
    "충당부채": "longterm_provisions",
    "충당금": "longterm_provisions",
    "손상차손": "impairment_losses_on_assets",
    "손상환입": "recovery_of_impairment_losses_on_assets",
    "외화환산": "gains_on_foreign_currency_translation",
    "외환차익": "gains_on_foreign_currency_transactions",
    "외환차손": "losses_on_foreign_currency_transactions",
    "외화환산이익": "gains_on_foreign_currency_translation",
    "외화환산손실": "losses_on_foreign_currency_translation",
    "파생상품평가이익": "gains_on_valuations_of_derivatives",
    "파생상품평가손실": "losses_on_valuations_of_derivatives",
    "파생상품거래이익": "gains_on_transactions_of_derivatives",
    "파생상품거래손실": "losses_on_transactions_of_derivatives",
    "파생상품": "current_derivative_assets",
    "지분법이익": "gains_on_valuation_of_investments_in_associates",
    "지분법손실": "losses_on_valuation_of_investments_in_associates",
    "지분법": "capital_change_in_equity_method",
    "연결범위": "gainslosses_in_subsidiaries",
    "연결대상": "gainslosses_in_subsidiaries",
    "연결조정": "gainslosses_in_subsidiaries",
    "연결변동": "gainslosses_in_subsidiaries",
    "연결이익": "net_profitowners_of_parent_equity",
    "이익잉여금": "retained_earnings",
    "미처분이익잉여금": "retained_earnings",
    "미처리결손금": "retained_earnings",
    "임의적립금": "voluntary_reserves",
    "이익준비금": "legal_reserves",
    "자본잉여금": "capital_surplus",
    "주식발행초과금": "paid_in_capital_in_excess_of_par_value",
    "자본조정": "other_reserves",
    "토지재평가": "assets_revaluations_reserves2001_years",
    "재평가잉여금": "assets_revaluations_reserves2001_years",
    "소수주주지분": "noncontrolling_interests_equity",
    "소수주주": "noncontrolling_interests_equity",
}

autoMappings5 = {}
for acc in allUnmatched:
    for keyword, snakeId in keywordMap5.items():
        if keyword in acc and snakeId in sl._snakeToKor:
            autoMappings5[acc] = snakeId
            break

print(f"Auto-mappable (round 5): {len(autoMappings5)}")

if autoMappings5:
    count = sl.learnBatch(autoMappings5)
    print(f"Learned: {count}")
    print(f"Total synonyms: {sl.synonymCount}")

done = 0
dist = {}
for code in codes:
    try:
        r = sl.analyzeCompany(code)
        if r.unmatchedCount == 0:
            done += 1
        else:
            bucket = min(r.unmatchedCount, 6)
            dist[bucket] = dist.get(bucket, 0) + 1
    except:
        pass

print(f"\n100% stocks: {done} / {len(codes)} ({done / len(codes) * 100:.1f}%)")
for k in sorted(dist.keys()):
    label = f"{k}+" if k == 6 else str(k)
    print(f"  {label} unmapped: {dist[k]} stocks")
