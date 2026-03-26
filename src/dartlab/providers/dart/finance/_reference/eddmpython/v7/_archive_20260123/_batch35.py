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
    # 리스 관련
    "리스채권현금회수": "finance_lease_receivables",
    "리스해지의손익": "other_income",
    "리스해지이익의조정": "other_adjustments",
    # 매도/매매/매수
    "매도주가지수옵션": "current_derivative_assets",
    "매매증권평가": "gains_on_valuation_of_financial_assets_measured_at_fair_value_through_profit_or_loss",
    "매수선택권의행사": "exercise_of_stock_options",
    "매수주가지수옵션": "current_derivative_assets",
    "매수청구권": "other_reserves",
    "매점수입": "other_income",
    "매출조정": "other_adjustments",
    "매립장설비": "other_tangible_assets",
    # 무 관련
    "명칭사용료": "other_expenses",
    "무상감자": "decrease_in_capital_stock",
    "무상사용권": "membership",
    "무상주": "increase_in_capital_stock",
    "무상증가": "increase_in_capital_stock",
    "무형자사의처분": "gains_on_disposal_of_intangible_assets",
    "무형자신의처분": "gains_on_disposal_of_intangible_assets",
    "무형잔산의처분": "gains_on_disposal_of_intangible_assets",
    # 미 관련
    "미교부주식": "other_reserves",
    "미분배자산": "other_noncurrent_assets",
    "미사용정부지원금": "government_grants",
    "미성공사": "work_in_process",
    "미수대매금": "other_receivables",
    "미수법인": "prepaid_income_tax",
    "미수부가세": "other_current_assets",
    "미수수의감소": "other_receivables",
    "미수이익": "accrued_income",
    "미수이자": "accrued_income",
    "미실현외화": "gains_on_foreign_currency_translation",
    "미완성애니메이션": "work_in_process",
    "미완성프로그램": "work_in_process",
    "미인수주식": "other_reserves",
    "미지금의감소": "decrease_in_other_payables",
    "미지급내국환": "other_current_liabilities",
    "미청구공사부채": "gross_amount_due_to_customers_for_contract_work",
    "미청구공사의증가(갑소)": "shortterm_gross_amount_due_from_customers_for_contract_work",
    "미청구수입": "other_receivables",
    "미확정회생채권": "other_current_assets",
    "미회수내국환": "other_receivables",
    "민원대행": "other_income",
    # 바/반 관련
    "바.장기금융상품": "longterm_financial_instruments",
    "반기당기총포괄": "comprehensive_income",
    "반기손손실": "net_profit",
    "반기손순": "net_profit",
    "반기손이익": "net_profit",
    "반기총총포괄": "comprehensive_income",
    "반품가능자산": "returnrefund_assets",
    "반품권": "returnrefund_assets",
    "반품상품회수권": "returnrefund_assets",
    "반품제고회수권": "returnrefund_assets",
    "반품제품회수권": "returnrefund_assets",
    "반품청구권": "returnrefund_assets",
    "반품추정변동대가": "other_expenses",
    "반품추정비": "other_expenses",
    "반품회수권": "returnrefund_assets",
    "반품회수자산": "returnrefund_assets",
    "반화제품회수권": "returnrefund_assets",
    "반환상품": "returnrefund_inventories",
    "반환제품": "returnrefund_inventories",
    # 발행/방송/배
    "발행어음": "other_current_liabilities",
    "방송장비": "other_tangible_assets",
    "방송채널의처분": "gains_on_disposal_of_intangible_assets",
    "방송프로그램수입": "other_income",
    "배댱금의지급": "dividends_paid",
    "배상금의수령": "other_income",
    # 법/변
    "법률비": "other_expenses",
    "법인설립": "acquisition_of_interest_in_subsidiaries",
    "법인신규설립": "acquisition_of_interest_in_subsidiaries",
    "법입세납부": "payments_of_income_taxes",
    "벱인세납부": "payments_of_income_taxes",
    "변동대가조정": "other_adjustments",
    "별도전환": "other_reserves",
    "병원매출": "sales_of_finished_goods",
    # 보 관련
    "보상금의수령": "other_income",
    "보상금이익": "other_income",
    "보상비조정": "other_adjustments",
    "보상자산의정산": "other_adjustments",
    "보즘금의증가": "increase_in_longterm_guarantee",
    "보증계약": "guarantee_contracts_provisions",
    "보증료": "other_expenses",
    "보증료조정": "other_adjustments",
    "보증부채": "guarantee_contracts_provisions",
    "보증손실환입": "other_income",
    "보증수증이익": "other_income",
    "보증의무": "guarantee_contracts_provisions",
    "보증채무": "guarantee_contracts_provisions",
    "보증평가손실": "other_expenses",
    "보통주감소": "decrease_in_capital_stock",
    "보통주증가": "increase_in_capital_stock",
    "복구공사이익": "other_income",
    "복리후생비": "other_adjustments",
    "복합금융상품": "other_reserves",
    "봉사활동비": "other_expenses",
    # 부 관련
    "부가가치세": "other_current_assets",
    "부가세대급급의감소": "other_current_assets",
    "부가세대급의감소": "other_current_assets",
    "부가세에수금": "withholdings",
    "부가세예수의증가": "withholdings",
    "부당거래반환": "other_income",
    "부도어음": "other_receivables",
    "부동산평가이익": "gains_on_valuation_of_investments",
    "부산물평가손실": "impairment_losses_on_inventories",
    "부산품평가손실": "impairment_losses_on_inventories",
    "부의영업권의증가": "goodwill",
    "부의영업권의환입": "recovery_of_impairment_losses_on_goodwill",
    "부의영업권즉시인식": "other_income",
    "부의자본법자본변동": "negative_capital_change_in_equity_method",
    "부의지본법자본변동": "negative_capital_change_in_equity_method",
    "부재료의감소": "change_in_inventory_of_finished_goods_and_work_in_process",
    "부품비": "other_expenses",
    # 분기 관련
    "분기손순익": "net_profit",
    "분기순손익": "net_profit",
    "분기총괄이익": "comprehensive_income",
    "분기총손실": "comprehensive_income",
    # 연구/연차/영업
    "연구비품의처분": "disposal_of_tangible_assets",
    "연구설비의처분": "disposal_of_tangible_assets",
    "연구용자산의증가": "acquisition_of_tangible_assets",
    "연구자금정산이익": "other_income",
    "연동범위": "gainslosses_in_subsidiaries",
    "연별범위변동": "gainslosses_in_subsidiaries",
    "연차보상부채": "accrued_expenses",
    "연차부채전입": "accrued_expenses",
    "연차수당및장기근속": "salaries",
    "열공급설비": "other_tangible_assets",
    "염가매수": "other_income",
    "엽엉외손익": "other_income",
    "영농교육비": "other_expenses",
    "영업경비": "selling_and_administrative_expenses",
    "영업관련자산": "other_adjustments",
    "영업권감액": "impairment_losses_on_goodwill",
    "영업권상각": "amortization",
    "영업권의증가(감소)": "goodwill",
    "영업권재측정": "goodwill",
    "영업권측정오류수정": "gainslosses_on_prior_period_error_corrections",
    "영업권획득": "goodwill",
    "영업보조금": "government_grants",
    "영업부문의양도": "gains_on_disposition_of_subsidiaries",
    "영업순손익": "operating_income",
    "영업양도": "gains_on_disposition_of_subsidiaries",
    "영업에서창춛": "cash_flows_from_operatings",
    "영업외비": "other_expenses",
    "영업외이익": "other_income",
    "영업의양수": "change_by_merger_and_acquisition",
    "영업자산부채변동": "other_adjustments",
    "영업자산의포괄적": "gains_on_disposition_of_subsidiaries",
    "영업할동으로인한": "other_adjustments",
    "영업활등으로인한": "other_adjustments",
    "영엽외손익": "other_income",
    "영화판권": "other_intangible_assets",
    # 예/오 관련
    "예상공사손실": "onerous_contracts_provisions",
    "예상공사이익": "other_income",
    "예수부가가치세": "withholdings",
    "예수원천세": "withholdings",
    "예수제세": "withholdings",
    "예치보조금": "government_grants",
    "오류수정금액": "gainslosses_on_prior_period_error_corrections",
    "오류수정에따른": "gainslosses_on_prior_period_error_corrections",
    "오류수정으로인한": "gainslosses_on_prior_period_error_corrections",
    "옵션거래손실": "losses_on_transactions_of_derivatives",
    "옵션평가이": "gains_on_valuations_of_derivatives",
    # 완/외 관련
    "완성영화": "other_noncurrent_assets",
    "외부주주지분": "noncontrolling_interests_equity",
    "외수부가세": "withholdings",
    "외주정비비": "other_expenses",
    "외화관련": "gains_on_foreign_currency_transactions",
    "외화예금": "cash_and_cash_equivalents",
    "외화차산": "other_current_assets",
    "외화차손": "losses_on_foreign_currency_transactions",
    "외화평가": "gains_on_foreign_currency_translation",
    "외화표시": "difference_by_changes_in_foreign_exchange_rates",
    "외화화산손익": "gains_on_foreign_currency_translation",
    "외화환찬차이": "difference_by_changes_in_foreign_exchange_rates",
    # 용/운 관련
    "용구수입": "other_income",
    "용지의감소": "other_tangible_assets",
    "운전자분의변동": "other_adjustments",
    "운전항목의변동": "other_adjustments",
    "운휴중인자산": "other_tangible_assets",
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
