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

keywordMap8 = {
    # 자 관련
    "자산유동화": "longterm_borrowings",
    "자시주식": "treasury_stock",
    "자원개발": "longterm_financial_assets",
    "자입금의증가": "increase_in_shortterm_borrowings",
    "자지주식": "treasury_stock",
    "자회사매각": "gains_on_disposition_of_subsidiaries",
    "자회사의유상감자": "decrease_in_capital_stock",
    "자회사인수": "acquisition_of_interest_in_subsidiaries",
    "작물": "biological_assets",
    "잔여자산": "other_adjustments",
    "잔여재산": "other_adjustments",
    "잔환권대가": "other_reserves",
    "잡손실환입": "other_income",
    "잡수입": "other_income",
    "잡이익": "other_income",
    # 장기금융상품 typos
    "장가차임금": "longterm_borrowings",
    "장가치입금": "longterm_borrowings",
    "장기금웅부채": "other_noncurrent_liabilities",
    "장기금웅상품": "longterm_financial_instruments",
    "장기금융기관예침금": "longterm_financial_instruments",
    "장기금융리스": "finance_lease_receivables",
    "장기금융삼풍": "longterm_financial_instruments",
    "장기금융상품$": "longterm_financial_instruments",
    "장기금융상품감소": "decrease_in_longterm_financial_instruments",
    "장기금융상품부채": "other_noncurrent_liabilities",
    "장기금융상품의납입": "increase_in_longterm_financial_instruments",
    "장기금융상품의선수": "longterm_financial_instruments",
    "장기금융상품의증": "increase_in_longterm_financial_instruments",
    "장기금융상품의츼득": "increase_in_longterm_financial_instruments",
    "장기금융상품의평가": "gains_on_valuations_of_derivatives",
    "장기금융상품자산의감소": "decrease_in_longterm_financial_instruments",
    "장기금융상품자산의증가": "increase_in_longterm_financial_instruments",
    "장기금융상풍": "longterm_financial_instruments",
    "장기금융상픔": "longterm_financial_instruments",
    "장기금융자.": "longterm_financial_instruments",
    "장기금융품": "longterm_financial_instruments",
    "장기기타금융장산": "longterm_financial_assets",
    "장기기타수쉬채권": "lt_trade_and_other_receivables",
    "장기기타자산": "other_noncurrent_assets",
    "장기대금의감소": "decrease_in_other_noncurrent_payables",
    "장기만기채무증권": "longterm_held_to_maturity_investments",
    "장기미급금": "other_noncurrent_payables",
    "장기미수채권": "lt_trade_and_other_receivables",
    "장기보즘금": "longterm_guarantee",
    "장기선급용": "other_noncurrent_assets",
    "장기성예금": "longterm_financial_instruments",
    "장기연불거래": "other_noncurrent_liabilities",
    "장기예수부채": "longterm_guarantee_deposits_withhold",
    "장기예적금": "longterm_financial_instruments",
    "장기임차권": "other_noncurrent_assets",
    "장기입금의증가": "increase_in_longterm_borrowings",
    "장기종업원부채": "noncurrent_provisions_for_employee_benefits",
    "장기종업원채무": "noncurrent_provisions_for_employee_benefits",
    "장기차임금": "longterm_borrowings",
    "장기채권의감소": "lt_trade_and_other_receivables",
    "장기채무의감소": "decrease_in_other_noncurrent_liabilities",
    "장기채무조기상환": "repayments_of_bonds",
    "장기프로젝트": "other_noncurrent_assets",
    "장치장식비": "other_expenses",
    "장.단기투자자산": "longterm_financial_assets",
    "장·단기투자자산": "longterm_financial_assets",
    "장·단기기금융": "longterm_financial_instruments",
    "장ㆍ단기투자자산": "longterm_financial_assets",
    "장기근속포상금": "salaries",
    # 재 관련
    "재고감모": "impairment_losses_on_inventories",
    "재고평가손실": "impairment_losses_on_inventories",
    "재매입유가증권": "bonds_sold_under_repurchase_agreements",
    "재매입이익": "other_income",
    "재무제표재작성": "accumulated_effect_of_accounting_policy_change",
    "재무홛동으로인한": "cash_flows_from_financing_activities",
    "재산자산": "other_current_assets",
    "재측정요소": "remeasurement_elements_of_defined_benefit_plans",
    "재해보상비": "other_expenses",
    "재해손실": "other_expenses",
    "재해피해": "other_expenses",
    # 전 관련
    "전권대가": "other_reserves",
    "전기(전전기)": "accumulated_effect_of_accounting_policy_change",
    "전기개발비오류": "gainslosses_on_prior_period_error_corrections",
    "전기공급설비": "other_tangible_assets",
    "전기누적오류": "gainslosses_on_prior_period_error_corrections",
    "전기료": "utilities",
    "전기미실현": "accumulated_other_comprehensive_income",
    "전기손익수정": "gainslosses_on_prior_period_error_corrections",
    "전기순손실": "net_profit",
    "전기요류수정": "gainslosses_on_prior_period_error_corrections",
    "전기재감사": "gainslosses_on_prior_period_error_corrections",
    "전기재무제표수정": "gainslosses_on_prior_period_error_corrections",
    "전기조정금액": "accumulated_effect_of_accounting_policy_change",
    "전기해외사업": "gains_on_foreign_currency_translation",
    "전대리스": "finance_lease_receivables",
    "전속계약": "other_intangible_assets",
    "전시회참가비": "other_expenses",
    "전용회선료": "other_expenses",
    "전한권대가": "other_reserves",
    "전한권의행사": "conversion_rights",
    "전혼권대가": "other_reserves",
    "전화권대가": "other_reserves",
    "전화권의행사": "conversion_rights",
    "전화채권": "convertible_bonds",
    "전환(교환)": "other_reserves",
    "전환대가": "other_reserves",
    "전환사재": "convertible_bonds",
    "전환사체": "convertible_bonds",
    "전환상환우선": "convertible_bonds",
    "전환새채": "convertible_bonds",
    "전환손실": "other_expenses",
    "전환우선부채": "convertible_bonds",
    "전환의행사": "conversion_rights",
    "전환전대가": "other_reserves",
    "전환전채": "convertible_bonds",
    "전환증권": "convertible_bonds",
    "전환채권": "convertible_bonds",
    "전환채의상환": "repayments_of_bonds",
    "전환청구": "conversion_rights",
    # 정 관련
    "정기성예금": "longterm_financial_instruments",
    "정기예.적금": "longterm_financial_instruments",
    "정보구입비": "other_expenses",
    "정보보조금사용": "government_grants",
    "정보보조금상환": "government_grants",
    "정보사업": "other_income",
    "정부정산": "other_income",
    "정부조금": "government_grants",
    "정부지원보조금": "government_grants",
    "정부출연금": "government_grants",
    "정부협약보장금": "government_grants",
    # 제 관련
    "제1109호": "accumulated_effect_of_accounting_policy_change",
    "제3자지정콜옵션": "other_reserves",
    "제가입권": "membership",
    "제도의정산": "noncurrent_provisions_for_employee_benefits",
    "제세공과금": "taxes_and_dues",
    "제작비": "other_expenses",
    "제작지원수입": "other_income",
    "제품매출진행률": "sales_of_finished_goods",
    "제품보증비": "other_expenses",
    "제품재고액": "finished_goods",
    "제품평가손실(환입)": "impairment_losses_on_inventories",
    # 조 관련
    "조림": "biological_assets",
    "조사연구비": "research",
    "조인트벤처": "investments_in_associates",
    "조정.": "other_adjustments",
    "조정:": "other_adjustments",
    "조정과목": "other_adjustments",
    "조정반영후": "accumulated_effect_of_accounting_policy_change",
    "조정후기초": "accumulated_effect_of_accounting_policy_change",
    "조합분담금": "other_income",
    # 종속 관련
    "종소기업": "gainslosses_in_subsidiaries",
    "종속관계조인트벤처": "gainslosses_in_subsidiaries",
    "종속법인": "gainslosses_in_subsidiaries",
    "종속투자지분": "investments_in_subsidiaries",
    "종송기업": "gainslosses_in_subsidiaries",
    "종송회사": "gainslosses_in_subsidiaries",
    "종업원주식매수": "stock_options",
    # 주 관련
    "주.임.종": "stockholder_executive_employee_longterm_loans",
    "주권발행비": "other_reserves",
    "주기주식": "treasury_stock",
    "주석선택권": "stock_options",
    "주시매수선택권": "stock_options",
    "주식거래보상": "compensation_expenses_associated_with_stock_options",
    "주식교환": "other_reserves",
    "주식기준보상": "compensation_expenses_associated_with_stock_options",
    "주식매선택권소멸": "reversal_of_compensation_expenses_associated_with_stock_options",
    "주식매수권": "stock_options",
    "주식매수선권택": "exercise_of_stock_options",
    "주식매수선태권": "stock_options",
    "주식매수선택원": "stock_options",
    "주식매수선택의": "exercise_of_stock_options",
    "주식매수옵션": "stock_options",
    "주식매수청구권": "stock_options",
    "주식매입권": "stock_options",
    "주식매입대금": "treasury_stock",
    "주식매입서택권": "stock_options",
    "주식매입선택원": "stock_options",
    "주식발행초과금결손": "capital_surplus",
    "주식발행초과금으로": "capital_surplus",
    "주식발행초과금의이입": "capital_surplus",
    "주식병합": "change_in_capital_stock",
    "주식석택권": "stock_options",
    "주식선택군": "stock_options",
    "주식양수": "other_reserves",
    "주식의소각": "treasury_stock",
    "주식주식의처분": "sale_of_treasury_stock",
    "주식청약금": "other_reserves",
    "주식할인밸행": "other_reserves",
    "주임종단가채권": "stockholder_executive_employee_longterm_loans",
    "주임종단기채권감소": "decrease_in_shortterm_loans",
    "주임종단기채권의증가": "increase_in_shortterm_loans",
    "주임종단기채무": "other_payables",
    "주임종복지지원금": "other_expenses",
    "주임종장기채무": "other_noncurrent_liabilities",
    "주임종장단기채권": "stockholder_executive_employee_longterm_loans",
    # 중단/증 관련
    "중단손익": "discontinued_operating_incomeloss",
    "중단업업": "discontinued_operating_incomeloss",
    "중단영엽": "discontinued_operating_incomeloss",
    "중단포괄": "discontinued_operating_incomeloss",
    "중소기업의감자": "decrease_in_capital_stock",
    "증거금": "other_current_assets",
    "증권업": "other_current_assets",
    "증권평가손익": "gains_on_valuations_of_derivatives",
    # 지 관련
    "지급어음의감소": "decrease_in_trade_payables",
    "지급이자": "interest_expenses",
    "지급입차료": "other_expenses",
    "지급채무": "other_payables",
    "지기주식": "treasury_stock",
    "지배권처분": "gainslosses_in_subsidiaries",
    "지배기업과의자본거래": "other_reserves",
    "지배기업소유": "net_profitowners_of_parent_equity",
    "지배기업의사업부": "change_by_merger_and_acquisition",
    "지배기업의소유지분": "net_profitowners_of_parent_equity",
    "지배기업의수유주": "net_profitowners_of_parent_equity",
    "지배기업의지분변동": "gainslosses_in_subsidiaries",
    "지배기업주주지": "net_profitowners_of_parent_equity",
    "지배기업총포괄": "comprehensive_income",
    "지배력상실": "gainslosses_in_subsidiaries",
}

autoMappings8 = {}
for acc in allUnmatched:
    for keyword, snakeId in keywordMap8.items():
        if keyword in acc and snakeId in sl._snakeToKor:
            autoMappings8[acc] = snakeId
            break

print(f"Auto-mappable (round 8): {len(autoMappings8)}")

if autoMappings8:
    count = sl.learnBatch(autoMappings8)
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
