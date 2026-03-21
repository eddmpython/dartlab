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

keywordFinal = {
    # Numbered/format items
    "(2)조정": "other_adjustments",
    "(3)자산": "other_adjustments",
    "(4)운전자본": "other_adjustments",
    "(금융리스채권현재가치": "finance_lease_receivables",
    "(유동성)장기부채": "current_portion_of_noncurrent_liabilities",
    "(유동성금융리스": "finance_lease_receivables",
    "(유동성사책": "current_portion_of_noncurrent_liabilities",
    "(유통성금융": "finance_lease_receivables",
    "-조정": "other_adjustments",
    "-총포괄이익소계": "comprehensive_income",
    "1월1일(조정": "accumulated_effect_of_accounting_policy_change",
    "2018년1월1일": "accumulated_effect_of_accounting_policy_change",
    "2022년6월30일": "accumulated_effect_of_accounting_policy_change",
    "APDP이익": "other_income",
    "MIDP이익": "other_income",
    "C/S비": "other_expenses",
    "FVOCI": "gainslosses_on_valuation_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "FV_OCI": "gainslosses_on_valuation_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "IFRS회계기준": "accumulated_effect_of_accounting_policy_change",
    "IP판권": "other_intangible_assets",
    "K-IFRS": "accumulated_effect_of_accounting_policy_change",
    "K-IRFS": "accumulated_effect_of_accounting_policy_change",
    "NCIPut": "other_current_liabilities",
    "RCPS전환": "convertible_bonds",
    "entity00": "plan_assets",
    "Ⅰ.총포괄": "comprehensive_income",
    "Ⅳ.기타부채": "other_noncurrent_liabilities",
    "Ⅴ.기타부채": "other_noncurrent_liabilities",
    "Ⅷ.기타자산": "other_noncurrent_assets",
    "Ⅹ.기타자산": "other_noncurrent_assets",
    "⑵조정": "other_adjustments",
    "⑶자산및부채": "other_adjustments",
    "VI.조정": "other_adjustments",
    "VI.환울차이": "difference_by_changes_in_foreign_exchange_rates",
    "XI.당기순손익": "net_profit",
    "XII.반기총포괄": "comprehensive_income",
    "XIV.반기총포괄": "comprehensive_income",
    "XVIII.총포괄": "comprehensive_income",
    "XⅣ.총포괄": "comprehensive_income",
    "V.금융손익": "other_income",
    "IV.기타손익": "other_income",
    "II.창업투자": "longterm_financial_assets",
    "III.금융업부채": "other_current_liabilities",
    "III.금융업자산": "other_current_assets",
    "7.보통주발행": "increase_in_capital_stock",
    "7.선납세금": "prepaid_income_tax",
    "8.기타투자자산": "longterm_financial_assets",
    "8.장기금융상품의처분": "decrease_in_longterm_financial_instruments",
    # 가 관련
    "가맹비": "other_expenses",
    "가상자산": "other_intangible_assets",
    "가스": "utilities",
    "가타유동부채": "other_current_liabilities",
    "가타유동채권": "other_receivables",
    "가타채무": "other_payables",
    "간이공사비": "other_expenses",
    "감가상가누계": "accumulated_depreciation",
    "감가상삭누계": "accumulated_depreciation",
    "감자차손": "other_reserves",
    "강기금융상품": "longterm_financial_instruments",
    # 개발 관련
    "개발비오류수정": "gainslosses_on_prior_period_error_corrections",
    "개발비의차감": "other_adjustments",
    "개발비차감": "other_adjustments",
    "개설매출": "sales_of_finished_goods",
    "개설집기비품": "furniture_and_fixtures",
    "개정기준서도입": "accumulated_effect_of_accounting_policy_change",
    "거래일손익": "other_adjustments",
    # 건설 관련
    "건설가계정": "construction_in_progress",
    "건설자금이자": "interest_expenses",
    "건설장비의처분": "disposal_of_tangible_assets",
    # 경/계 관련
    "경상개발비": "usual_development_and_research_expenses",
    "계속기본희석": "eps",
    "계속기업기본주당": "eps",
    "계속기업영업": "operating_income",
    "계속기업이익": "profit_from_continuing_operations",
    "계속사업당기순익": "profit_from_continuing_operations",
    "계속사업반기": "profit_from_continuing_operations",
    "계속사업보통주": "eps",
    "계속사업분기": "profit_from_continuing_operations",
    "계속사영업": "operating_income",
    "계속영입": "profit_from_continuing_operations",
    "계속포괄이익": "comprehensive_income",
    "계손영업": "operating_income",
    "계악부채": "contract_liabilities",
    "계약매입": "contract_liabilities",
    "계약매출": "contract_assets",
    "계약보증": "other_expenses",
    "계약이행자산": "contract_assets",
    "계약해지": "other_expenses",
    "계열사전입": "gainslosses_in_subsidiaries",
    "계열사전출": "gainslosses_in_subsidiaries",
    "계정대체": "other_adjustments",
    "계측기의처분": "disposal_of_tangible_assets",
    # 고객 관련
    "고객관계가치": "other_intangible_assets",
    "고객적립금": "other_current_liabilities",
    "고객전립금": "other_current_liabilities",
    "고객충성제도": "other_current_liabilities",
    "고용지원금": "government_grants",
    "공공영업자산": "other_noncurrent_assets",
    "공구기구": "tools",
    "공구기와비품": "disposal_of_tangible_assets",
    "공구및기구": "disposal_of_tangible_assets",
    "공구와기구및비품": "disposal_of_tangible_assets",
    "공기구비품": "acquisition_of_tangible_assets",
    "공기구의증가": "acquisition_of_tangible_assets",
    # 공동 관련
    "공동기업손익": "gains_on_valuation_of_investments_in_joint_ventures",
    "공동기업유상감자": "disposal_of_investments_in_associates",
    "공동기업의기타포": "accumulated_other_comprehensive_income",
    "공동기업의순손익": "gains_on_valuation_of_investments_in_joint_ventures",
    "공동기업주식": "investments_in_associates",
    "공동지배기업": "investments_in_associates",
    "공동투자기업": "investments_in_associates",
    # 공사 관련
    "공사손실부채전입": "onerous_contracts_provisions",
    "공사손실부채환입": "onerous_contracts_provisions",
    "공사손실비": "onerous_contracts_provisions",
    "공사손실인식": "onerous_contracts_provisions",
    "공사손실추정": "onerous_contracts_provisions",
    "공사손실충당": "onerous_contracts_provisions",
    "공사손실환입": "onerous_contracts_provisions",
    "공사수입금": "other_current_liabilities",
    "공사원재료": "raw_materials",
    "금융리스채권의대금수령": "finance_lease_receivables",
    "금융리스채권의증가(감소)": "finance_lease_receivables",
    "금융리스채권현재가치할인차금": "finance_lease_receivables",
    "금융이익-기타": "other_income",
    "금융이익_기타": "other_income",
    # 기타 remaining
    "가.금융상품의감소": "decrease_in_shortterm_financial_instruments",
    "가.금융상품의증가": "increase_in_shortterm_financial_instruments",
    "가.조정": "other_adjustments",
    "2.리스채권의회수": "finance_lease_receivables",
    "3.금융리스채권": "finance_lease_receivables",
    "3.리스채권의회수": "finance_lease_receivables",
    "4.리스채권의회수": "finance_lease_receivables",
    "10.기타": "other_expenses",
    "12.기타": "other_expenses",
    "4.기타": "other_expenses",
    "7.기타": "other_expenses",
    "8.기타": "other_expenses",
    "9.기타": "other_expenses",
    "2.기타": "other_expenses",
    "1.기타이익": "other_income",
    "4.기타손익": "other_income",
    "2.장기금융상품": "longterm_financial_instruments",
    "3.장기금융상품": "longterm_financial_instruments",
    "결솜금처리": "other_adjustments",
}

autoMappingsFinal = {}
for acc in allUnmatched:
    for keyword, snakeId in keywordFinal.items():
        if keyword in acc and snakeId in sl._snakeToKor:
            autoMappingsFinal[acc] = snakeId
            break

print(f"Auto-mappable (final): {len(autoMappingsFinal)}")

if autoMappingsFinal:
    count = sl.learnBatch(autoMappingsFinal)
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
