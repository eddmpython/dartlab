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

keywordMap7 = {
    # 비지배 관련 (typos)
    "비재배주주": "noncontrolling_interests_equity",
    "비재배지분": "noncontrolling_interests_equity",
    "비재비지분": "noncontrolling_interests_equity",
    "비지배기준": "noncontrolling_interests_equity",
    "비지배부문": "noncontrolling_interests_equity",
    "비지배부채": "noncontrolling_interests_equity",
    "비지배비분": "noncontrolling_interests_equity",
    "비지배소유주": "noncontrolling_interests_equity",
    "비지배주분": "noncontrolling_interests_equity",
    "비지배주주": "noncontrolling_interests_equity",
    "비지배지": "noncontrolling_interests_equity",
    "비지배회사": "noncontrolling_interests_equity",
    "비지분부채": "noncontrolling_interests_equity",
    "소주주주지분": "noncontrolling_interests_equity",
    # 비유동 관련
    "비유동금융리스": "finance_lease_receivables",
    "비유동금융상품": "longterm_financial_instruments",
    "비유동리스": "lease_obligations",
    "비유동미청구": "longterm_gross_amount_due_from_customers_for_contract_work",
    "비유동반품권": "returnrefund_assets",
    "비유동부채계": "total_noncurrent_liabilities",
    "비유동부채의증가": "increase_in_other_noncurrent_liabilities",
    "비유동부채현재가치": "other_noncurrent_liabilities",
    "비유동성기타부채": "other_noncurrent_liabilities",
    "비유동성예수부채": "other_noncurrent_liabilities",
    "비유동성전환금융": "other_noncurrent_liabilities",
    "비유동성차입부채": "longterm_borrowings",
    "비유동성투자자산": "longterm_financial_assets",
    "비유동자산계": "total_noncurrent_assets",
    "비유동장기금융": "longterm_financial_instruments",
    "비유동채권의감소": "lt_trade_and_other_receivables",
    "비유동충동부채": "other_noncurrent_liabilities",
    "비유동파생자산": "noncurrent_derivative_assets",
    "비금융유동부채": "other_current_liabilities",
    "비금융유동자산": "other_current_assets",
    # 비품 관련
    "비품매각": "disposal_of_tangible_assets",
    "비품의폐기": "disposal_of_tangible_assets",
    "비현금조정": "other_adjustments",
    # 분 관련
    "분기총이익": "comprehensive_income",
    "분기총포괄": "comprehensive_income",
    "분류변경": "other_adjustments",
    "분배금의지급": "dividends_paid",
    "분배예정부채": "other_current_liabilities",
    "분할결정": "change_by_merger_and_acquisition",
    "분할등으로인한": "change_by_merger_and_acquisition",
    "분할양도차익": "other_reserves",
    "분할에따른": "change_by_merger_and_acquisition",
    "분할으로인한": "change_by_merger_and_acquisition",
    "불균증감자": "change_in_capital_stock",
    # 사 관련
    "사.장기금융상품": "longterm_financial_instruments",
    "사내근로사업": "noncurrent_provisions_for_employee_benefits",
    "사내복지근로": "noncurrent_provisions_for_employee_benefits",
    "사모투자": "longterm_financial_assets",
    "사무실관리비": "other_expenses",
    "사업가치평": "other_intangible_assets",
    "사업결합": "change_by_merger_and_acquisition",
    "사업결으로인한": "change_by_merger_and_acquisition",
    "사업결함으로인한": "change_by_merger_and_acquisition",
    "사업권자산": "other_intangible_assets",
    "사업부매각": "gains_on_disposition_of_subsidiaries",
    "사업부문매각": "gains_on_disposition_of_subsidiaries",
    "사업부문분할": "change_by_merger_and_acquisition",
    "사업부문양도": "gains_on_disposition_of_subsidiaries",
    "사업부문자산": "gains_on_disposal_of_assets",
    "사업부문조정": "other_adjustments",
    "사업부문처분": "gains_on_disposition_of_subsidiaries",
    "사업부분매각": "gains_on_disposition_of_subsidiaries",
    "사업부분의양수": "change_by_merger_and_acquisition",
    "사업양도": "gains_on_disposition_of_subsidiaries",
    "사업의결합": "change_by_merger_and_acquisition",
    "사업의양수도": "change_by_merger_and_acquisition",
    "사업인수대가": "acquisition_of_interest_in_subsidiaries",
    "사업처분": "gains_on_disposition_of_subsidiaries",
    "사엉양수": "change_by_merger_and_acquisition",
    "사엽결합": "change_by_merger_and_acquisition",
    "사외운용자산": "plan_assets",
    "사외자산의적립": "plan_assets",
    "사외적입자산": "plan_assets",
    "사외정립자산": "plan_assets",
    "사위적립자산": "plan_assets",
    "사회적립자산": "plan_assets",
    "사재의증가": "increase_in_longterm_financial_instruments",
    "사후처리비": "other_expenses",
    "사용권(금융리스)": "finance_lease_receivables",
    "사용권부채": "lease_obligations",
    "사용자기여금": "plan_assets",
    "사용자산": "other_tangible_assets",
    # 산업재산권/상각
    "산업재산권": "other_intangible_assets",
    "산업합리화": "other_noncurrent_liabilities",
    "산종자본증권": "other_reserves",
    "상각누계액": "accumulated_amortisation",
    "상각후채무증권": "longterm_held_to_maturity_investments",
    "상여금의지급": "salaries",
    "상여부채": "accrued_expenses",
    "상장으로인한": "other_reserves",
    "상표권": "other_intangible_assets",
    "상품권의감소": "other_current_liabilities",
    "상품판매비": "other_expenses",
    "상품폐기손실": "impairment_losses_on_inventories",
    "상환전환우선": "convertible_bonds",
    "상환전환종류주식": "other_reserves",
    "새로운기준서도입": "accumulated_effect_of_accounting_policy_change",
    # 선급 관련
    "선급공사비": "advance_payments",
    "선급급": "advance_payments",
    "선급부가가치세": "other_current_assets",
    "선급비요": "prepaid_expenses",
    "선급세금": "prepaid_income_tax",
    "선급제세": "prepaid_income_tax",
    "선급주세": "prepaid_income_tax",
    "선급통관료": "other_current_assets",
    "선납지방소득세": "prepaid_income_tax",
    "선박장비품": "other_tangible_assets",
    "선수부채": "advance_received",
    "설립자본": "capital_stock",
    "설변손실보상": "other_income",
    "설비장치": "other_tangible_assets",
    # 성과/세 관련
    "성과급": "salaries",
    "성과보수": "salaries",
    "세금과공과": "taxes_and_dues",
    "세무조사": "other_expenses",
    "세울변동효과": "income_taxes_expenses",
    "세전이익": "income_before_income_taxes",
    "소급적용": "accumulated_effect_of_accounting_policy_change",
    "소급조정": "accumulated_effect_of_accounting_policy_change",
    "소모품비": "other_expenses",
    "소비자보상비": "other_expenses",
    "소송": "other_expenses",
    "소유자의미배분": "other_reserves",
    "소유주분배": "dividends_paid",
    "소유주에의한": "other_reserves",
    "소유주와거래": "other_reserves",
    "소유주와의거래": "other_reserves",
    "소유주지분변동": "other_reserves",
    "손실보상금": "other_expenses",
    "손실충담부채": "longterm_provisions",
    "송무비": "other_expenses",
    "수목": "biological_assets",
    "수이긴식기준변경": "accumulated_effect_of_accounting_policy_change",
    "수입보증": "other_income",
    "수입입대료": "rental_income",
    "수입장려금": "other_income",
    "수입제세": "other_current_assets",
    "수정사항": "accumulated_effect_of_accounting_policy_change",
    "수정후기초": "accumulated_effect_of_accounting_policy_change",
    "수정후당기초": "accumulated_effect_of_accounting_policy_change",
    "수정후반기초": "accumulated_effect_of_accounting_policy_change",
    "수정후분기초": "accumulated_effect_of_accounting_policy_change",
    "수주활동비": "other_expenses",
    "수출경비": "other_expenses",
    "수출제품매출": "sales_of_finished_goods",
    "수탁금": "other_current_liabilities",
    "수탁대리점": "other_current_liabilities",
    "숙식비": "other_expenses",
    "순금융손": "other_expenses",
    "순운전자": "other_adjustments",
    "순이익의귀속": "net_profit",
    "순확정금여": "noncurrent_provisions_for_employee_benefits",
    "순확정급영": "noncurrent_provisions_for_employee_benefits",
    "순확정급유": "noncurrent_provisions_for_employee_benefits",
    "순확정부채": "noncurrent_provisions_for_employee_benefits",
    "스톡옵션": "stock_options",
    "스톱옵션": "stock_options",
    # 시설 관련
    "시설공사의처분": "disposal_of_tangible_assets",
    "시설물의처분": "disposal_of_tangible_assets",
    "시설분담금": "other_income",
    "시설사용권": "membership",
    "시설장비": "other_tangible_assets",
    "시설장치의양도": "disposal_of_tangible_assets",
    "시설장치의취둑": "acquisition_of_tangible_assets",
    "시설장치의폐기": "disposal_of_tangible_assets",
    "시스템매출": "sales_of_finished_goods",
    "시외적립자산": "plan_assets",
    "시절장치": "other_tangible_assets",
    "시추설비": "other_tangible_assets",
    "시험기구": "tools",
    "시험분석비": "research",
    "시험연구비": "research",
    "시험재료": "research",
    "시혐연구용기기": "disposal_of_tangible_assets",
    "식음료": "other_expenses",
    # 신 관련
    "신규투자": "longterm_financial_assets",
    "신기술조합": "longterm_financial_assets",
    "신본자본증권": "other_reserves",
    "신수인수권": "stock_warrants",
    "신용조사": "other_income",
    "신용조회": "other_income",
    "신용평가": "other_income",
    "신인수권": "stock_warrants",
    "신종자본등": "other_reserves",
    "신종자본의전환": "other_reserves",
    "신주발행비환급": "other_reserves",
    "신주발행에따른": "other_reserves",
    "신주발행으로인한": "increase_in_capital_stock",
    "신주신수권": "stock_warrants",
    "신주의발생단주": "other_expenses",
    "신주의발행비지급": "other_reserves",
    "신주인사권": "stock_warrants",
    "신주인수대금": "other_reserves",
    "신주인수증권": "stock_warrants",
    "신주인숸소각": "stock_warrants",
    "신주청약증거금": "other_reserves",
    "신주청양증거금": "other_reserves",
    "신탁계정": "other_noncurrent_assets",
    "신탁계좌": "other_noncurrent_assets",
    "신탁자산": "other_noncurrent_assets",
    "실험기구": "tools",
    "아이스크림사업부": "gains_on_disposition_of_subsidiaries",
    "아자의지급": "interest_expenses",
    "아지율스왑": "swaptransaction",
    "암호화자산": "other_intangible_assets",
    "액면분할": "change_in_capital_stock",
    "양수채권": "other_receivables",
    "어음채권금융": "other_receivables",
    "여객운송수입": "sales_of_finished_goods",
    "여행수탁금": "other_current_liabilities",
    "연걸범위변동": "gainslosses_in_subsidiaries",
}

autoMappings7 = {}
for acc in allUnmatched:
    for keyword, snakeId in keywordMap7.items():
        if keyword in acc and snakeId in sl._snakeToKor:
            autoMappings7[acc] = snakeId
            break

print(f"Auto-mappable (round 7): {len(autoMappings7)}")

if autoMappings7:
    count = sl.learnBatch(autoMappings7)
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
