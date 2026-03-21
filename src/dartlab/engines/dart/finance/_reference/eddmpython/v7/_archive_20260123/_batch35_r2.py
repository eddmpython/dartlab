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

keywordMap = {
    # 지배 관련
    "지배력을상실": "gainslosses_in_subsidiaries",
    "지배력의변동이없는": "other_reserves",
    "지배력의획득": "cash_inflows_from_merger_and_acquisition",
    "지배력획득으로인한현급": "cash_inflows_from_merger_and_acquisition",
    "지배지분손실": "net_profitowners_of_parent_equity",
    "지배지분순이익": "net_profitowners_of_parent_equity",
    "지배지분에대한주당": "eps",
    "지배지분의감소": "net_profitowners_of_parent_equity",
    "지배지분의증가": "net_profitowners_of_parent_equity",
    "지배지분총포괄": "comprehensive_income",
    "지배지분포괄": "comprehensive_income",
    "지배회사보통주": "increase_in_capital_stock",
    "지배회사분": "net_profitowners_of_parent_equity",
    "지배회사의소유지분": "net_profitowners_of_parent_equity",
    "지배회사지분당기순": "net_profitowners_of_parent_equity",
    "지배회사지분에대한주당": "eps",
    "지배회사지분총포괄": "comprehensive_income",
    "지배회사총포괄": "comprehensive_income",
    "지분거래이익": "other_income",
    "지분매각": "disposal_of_investments_in_associates",
    "지분매도": "disposal_of_investments_in_associates",
    "지분변동등": "gainslosses_in_subsidiaries",
    "지분변동에의한": "gainslosses_in_subsidiaries",
    "지분변동으로인한": "gainslosses_in_subsidiaries",
    "지분상품투자평가": "gainslosses_on_valuation_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "지분옵션계약": "other_reserves",
    "지분의전환": "other_reserves",
    "지분적자본변동": "capital_change_in_equity_method",
    "지분증권(금융업)": "longterm_financial_assets",
    "지분증권의감소": "decrease_in_longterm_financial_instruments",
    "지분증권의매입": "increase_in_longterm_financial_instruments",
    "지붑법손실": "losses_on_valuation_of_investments_in_associates",
    "지븐법자본변동": "capital_change_in_equity_method",
    "지속관여": "other_noncurrent_assets",
    "지연이자": "interest_expenses",
    "지점청산": "change_by_merger_and_acquisition",
    "진행공사부채": "gross_amount_due_to_customers_for_contract_work",
    "진행중인DOCK": "construction_in_progress",
    "집기기품": "furniture_and_fixtures",
    "집합투자증권": "longterm_financial_assets",
    "징기금융상품": "longterm_financial_instruments",
    # 차 관련
    "차.개발비": "research_development",
    "차.장기금융상품": "longterm_financial_instruments",
    "차량": "vehicles",
    "차량운반의처분": "disposal_of_tangible_assets",
    "차량유지비": "other_expenses",
    "차입부채": "longterm_borrowings",
    "차입원료": "raw_materials",
    "차입재고": "inventory",
    "차입채무": "longterm_borrowings",
    "창업투자자": "longterm_financial_assets",
    # 채 관련
    "채권의처분": "decrease_in_longterm_financial_instruments",
    "채권재조정": "other_expenses",
    "채권조정이익": "other_income",
    "채권추심": "other_income",
    "채권할인차금": "other_receivables",
    "채무면제이익대체": "other_income",
    "채무보증환입": "other_income",
    "채무상품의증가": "increase_in_longterm_financial_instruments",
    "채무상품평가이익": "gains_on_valuations_of_derivatives",
    "채무조정": "other_expenses",
    "처리후자본": "other_reserves",
    "처분으로인한대체": "other_adjustments",
    "처분후자본": "other_reserves",
    "청구채권": "other_receivables",
    "청산": "change_by_merger_and_acquisition",
    "체무면제이익": "other_income",
    # 초 관련
    "초과전력매출환수부채": "other_current_liabilities",
    "초과청구계약": "gross_amount_due_to_customers_for_contract_work",
    "초인플레이션": "other_income",
    # 총포괄 관련
    "총포괄손": "comprehensive_income",
    "총포괄순이익": "comprehensive_income",
    "총포괄이익": "comprehensive_income",
    "총포손익소계": "comprehensive_income",
    "추가상장": "increase_in_capital_stock",
    "출연료수입": "other_income",
    "출자": "longterm_financial_assets",
    "충담부채": "longterm_provisions",
    "측정장치의처분": "disposal_of_tangible_assets",
    "츨자금의반환": "decrease_in_longterm_financial_instruments",
    "층당부채의증가": "longterm_provisions",
    "콜론의감소": "other_current_liabilities",
    "콜옵션": "other_reserves",
    # 타계정
    "타.투자자산의처분": "longterm_financial_assets",
    "타계정에서대체": "other_adjustments",
    "태양광발전설비": "acquisition_of_tangible_assets",
    "태양광설비": "disposal_of_tangible_assets",
    "토직연금": "plan_assets",
    "통신장비": "other_tangible_assets",
    "통하선도거래": "losses_on_transactions_of_derivatives",
    "통합스왑의정산": "swaptransaction",
    "통화선부채": "derivative_liabilities",
    "통화옵션부채": "derivative_liabilities",
    # 퇴직 관련
    "퇴직/연차": "provision_for_retirement_allowance",
    "퇴직금의납입": "plan_assets",
    "퇴직금의이관": "provision_for_retirement_allowance",
    "퇴직금의전입": "provision_for_retirement_allowance",
    "퇴직금의증가": "provision_for_retirement_allowance",
    "퇴직금의총지급": "provision_for_retirement_allowance",
    "퇴직금의？지급": "provision_for_retirement_allowance",
    "퇴직금지급의증가": "provision_for_retirement_allowance",
    "퇴직금차액": "provision_for_retirement_allowance",
    "퇴직운영자산": "plan_assets",
    "퇴직의이관": "provision_for_retirement_allowance",
    "퇴직전환금": "plan_assets",
    # 투자 관련
    "투기부동산": "disposal_of_tangible_assets",
    "투자계약금": "other_noncurrent_assets",
    "투자손실(주": "losses_on_valuation_of_investments_in_associates",
    "투자자산수증이익": "other_income",
    "투자자산의증감": "longterm_financial_assets",
    "투자자산의처분.": "gains_on_disposal_of_assets",
    "투자자산평가": "gains_on_valuation_of_investments",
    "투자조합출자": "increase_in_longterm_financial_instruments",
    "투자주식감액": "impairment_losses_on_assets",
    "투자주식관련투자액": "decrease_in_longterm_financial_instruments",
    "투자주식손익": "gains_on_valuation_of_investments",
    "투자증권의감소": "decrease_in_longterm_financial_instruments",
    "투자지분변동": "gainslosses_in_subsidiaries",
    "투자지분증권": "gainslosses_in_subsidiaries",
    "투자차액": "other_adjustments",
    "투자채권의처분": "decrease_in_longterm_financial_instruments",
    "투자평가": "gains_on_valuation_of_investments",
    "투자할동으로인한": "cash_flows_from_investing_activities",
    "특수관계자재무": "trade_payablesrelated_parties",
    "특약점개설담보금": "longterm_guarantee",
    # 파생 관련
    "파.개발비": "research_development",
    "파렛트렌탈자산": "disposal_of_tangible_assets",
    "파상상품": "current_derivative_assets",
    "파상생품": "current_derivative_assets",
    "파상품평가": "gains_on_valuations_of_derivatives",
    "파생거래수취": "gains_on_transactions_of_derivatives",
    "파생금상품": "losses_on_valuations_of_derivatives",
    "파생금자산": "current_derivative_assets",
    "파생부채의감소": "derivative_liabilities",
    "파생부채의결제": "derivative_liabilities",
    "파생삼품의결제": "current_derivative_assets",
    "파생상풍": "gains_on_valuations_of_derivatives",
    "파생상픔": "gains_on_transactions_of_derivatives",
    "파생생품": "current_derivative_assets",
    "파생자산상품": "current_derivative_assets",
    "파생팡품": "gains_on_valuations_of_derivatives",
    "파생평가손실": "losses_on_valuations_of_derivatives",
    # 판 관련
    "판권매출": "other_income",
    "판권의감소": "other_intangible_assets",
    "판권의처분": "gains_on_disposal_of_intangible_assets",
    "판권증가": "other_intangible_assets",
    "판매보증비": "other_expenses",
    "판매보증수리비": "other_expenses",
    "판매부대비": "other_expenses",
    "판매수리비": "other_expenses",
    "판매유지비": "other_expenses",
    "판배보증비": "other_expenses",
    "판촉비": "sales_promotions",
    "폐광지역개발": "other_expenses",
    "폐기물처분분담금": "other_expenses",
    "포괄사업의양수": "change_by_merger_and_acquisition",
    "포괄이익": "comprehensive_income",
    "포괄적손익누계": "accumulated_other_comprehensive_income",
    "포인트충당부체": "other_current_liabilities",
    "표시통화변동": "difference_by_changes_in_foreign_exchange_rates",
    "품질보증비환입": "other_income",
    "풋백옵션": "other_reserves",
    "풋옵션계약": "other_reserves",
    "풋옵션소멸": "other_reserves",
    "프로그램의증가": "other_noncurrent_assets",
    "피트니스수입": "other_income",
    # 하 관련
    "하.개발비": "research_development",
    "하역매출": "sales_of_finished_goods",
    "하자보수채무": "other_current_liabilities",
    "하자보수춛당부채": "longterm_provisions",
    "학술비": "other_expenses",
    "합계.": "other_adjustments",
    # 해외 관련
    "해외부가세대금급": "other_current_assets",
    "해외사업": "gains_on_foreign_currency_translation",
    "해외산업환손익": "gains_on_foreign_currency_translation",
    "해외선급부가세": "other_current_assets",
    "해외제품매출": "sales_of_finished_goods",
    "핸디카보통주": "treasury_stock",
    # 현금/현재가치
    "현금공탁금": "other_current_assets",
    "현금및현금성산": "cash_and_cash_equivalents",
    "현금및현금자산": "cash_and_cash_equivalents",
    "현금에서창출된": "cash_flows_from_operatings",
    "현금의환울": "difference_by_changes_in_foreign_exchange_rates",
    "현금출자": "increase_in_capital_stock",
    "현금활율변동": "difference_by_changes_in_foreign_exchange_rates",
    "현금흐름회피": "accumulated_other_comprehensive_income",
    "현대가치할인차금": "other_noncurrent_liabilities",
    "현물출자": "other_reserves",
    "현자기채할인차금": "other_receivables",
    "현재가지할인차금": "other_noncurrent_liabilities",
    "현재가차할인차금": "other_noncurrent_liabilities",
    "현재가치할인": "other_noncurrent_liabilities",
    # 화/확/환/회
    "화물수입": "other_current_liabilities",
    "화원권의처분": "decrease_in_membership",
    "확정거래평가": "gains_on_valuations_of_derivatives",
    "확정계약이익": "other_income",
    "확정계약평가": "gains_on_valuations_of_derivatives",
    "확정금여자산": "plan_assets",
    "확정기여제도": "noncurrent_provisions_for_employee_benefits",
    "확정기여형": "noncurrent_provisions_for_employee_benefits",
    "환가료": "other_expenses",
    "환경복구비": "other_expenses",
    "환경유지비": "other_expenses",
    "환률변동": "difference_by_changes_in_foreign_exchange_rates",
    "환매조건부채권": "bonds_sold_under_repurchase_agreements",
    "환매조권부채권": "bonds_sold_under_repurchase_agreements",
    "환부채의증가": "other_current_liabilities",
    "환율의변동효과": "difference_by_changes_in_foreign_exchange_rates",
    "환율차손": "losses_on_foreign_currency_transactions",
    "환율차익": "gains_on_foreign_currency_transactions",
    "회계기준변경": "accumulated_effect_of_accounting_policy_change",
    "회계번경누적효과": "accumulated_effect_of_accounting_policy_change",
    "회계정책": "accumulated_effect_of_accounting_policy_change",
    "회계처리소급": "accumulated_effect_of_accounting_policy_change",
    "회계추정의변경": "accumulated_effect_of_accounting_policy_change",
    "회사설립": "acquisition_of_interest_in_subsidiaries",
    "회사차(단기)": "shortterm_borrowings",
    "회생계획안": "decrease_in_capital_stock",
    "회생채권": "other_current_assets",
    "횐율변동": "difference_by_changes_in_foreign_exchange_rates",
    "후석적으로": "accumulated_other_comprehensive_income",
    "후속적으로": "accumulated_other_comprehensive_income",
    "후순위채의감소": "repayments_of_bonds",
    # 희석주당
    "희석주당반기순이긱": "diluted_eps",
    "희석주당보통주": "diluted_eps",
    "희석주당손손익": "diluted_eps",
    "희석주당손순익": "diluted_eps",
    "희석주당순손이익": "diluted_eps",
    "희석주당순손익": "diluted_eps",
    "희석주당중단": "diluted_eps",
    # 종속 관련
    "종속(관계)기업": "gainslosses_in_subsidiaries",
    "종속/공동기업": "gainslosses_in_subsidiaries",
    "지급어음의감소": "decrease_in_trade_payables",
    "전환의행사": "conversion_rights",
    "전환청구": "conversion_rights",
    "정부정산": "other_income",
    "제각채권의회수": "other_income",
    "제작지원수입": "other_income",
    "제품평가손실(환입)": "impairment_losses_on_inventories",
    "조합분담금": "other_income",
    "코스": "other_adjustments",
}

autoMappings = {}
for acc in allUnmatched:
    for keyword, snakeId in keywordMap.items():
        if keyword in acc and snakeId in sl._snakeToKor:
            autoMappings[acc] = snakeId
            break

print(f"Auto-mappable: {len(autoMappings)}")

if autoMappings:
    count = sl.learnBatch(autoMappings)
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
