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

keywordMap6 = {
    # 단기금융상품 typos
    "단기금융삼품": "shortterm_financial_instruments",
    "단기금융상퓸": "shortterm_financial_instruments",
    "단기금융장품": "shortterm_financial_instruments",
    "단기금융자간": "shortterm_financial_instruments",
    "단기금융자사": "shortterm_financial_instruments",
    "단기금융자상품": "shortterm_financial_instruments",
    "단기금융증권": "shortterm_financial_instruments",
    "단기금융상품.": "shortterm_financial_instruments",
    "단기금융상품의납입": "increase_in_shortterm_financial_instruments",
    "단기금융상품의순증": "increase_in_shortterm_financial_instruments",
    "단기금융상품이처분": "decrease_in_shortterm_financial_instruments",
    "단기금융상품자산의감소": "decrease_in_shortterm_financial_instruments",
    "단기금융상품자산의증가": "increase_in_shortterm_financial_instruments",
    "단기금융상품해지": "decrease_in_shortterm_financial_instruments",
    "단기금융상품의장기": "increase_in_longterm_financial_instruments",
    "단기금융상품의？감소": "decrease_in_shortterm_financial_instruments",
    "단기금융상품의": "shortterm_financial_instruments",
    "단기금융기관예기금": "shortterm_financial_instruments",
    "단기금융리스채권": "finance_lease_receivables",
    "단기금융상품거래이익": "gains_on_transactions_of_derivatives",
    "단기금융상품부채": "other_current_liabilities",
    "단기금융상품평기손실": "losses_on_valuations_of_derivatives",
    "딘기금융상품": "shortterm_financial_instruments",
    "딘기매매증권": "shortterm_financial_instruments",
    "단기기타부채": "other_current_liabilities",
    "단기기타자산": "other_current_assets",
    "단기기타패권": "other_receivables",
    "단기대여": "shortterm_loans",
    "단기대역금": "shortterm_loans",
    "단기대요금": "shortterm_loans",
    "단기매여금": "shortterm_loans",
    "단기여대금": "shortterm_loans",
    "단기매도증권": "shortterm_availableforsale_financial_assets",
    "단기매매증궝": "shortterm_financial_instruments",
    "단기매매증증권": "shortterm_financial_instruments",
    "단기매매차익": "gains_on_transactions_of_derivatives",
    "단기매매평가": "gains_on_valuation_of_financial_assets_measured_at_fair_value_through_profit_or_loss",
    "단기부채": "shortterm_borrowings",
    "단기선급급": "advance_payments",
    "단기선급부가세": "other_current_assets",
    "단기종업원부채": "accrued_expenses",
    "단기지원금융": "shortterm_financial_instruments",
    "단기투자일임": "shortterm_financial_instruments",
    "단기투자자산감액": "impairment_losses_on_assets",
    "단기투자자산의납입": "increase_in_shortterm_financial_instruments",
    "단기투자자산증가": "increase_in_shortterm_financial_instruments",
    "단기손익지정": "designatedfinancial_assets_at_fv_through_profit",
    "단수주": "other_expenses",
    "단주주식대금": "other_expenses",
    "단주처리": "other_expenses",
    "단주처분": "other_expenses",
    "단체공납금": "other_expenses",
    # 당기손익 관련
    "당기손손실": "net_profit",
    "당기손이익": "net_profit",
    "당기이익": "net_profit",
    "당기이익(손실)": "net_profit",
    "당기수이익": "net_profit",
    "당기이손익": "net_profit",
    "당순이익": "net_profit",
    "당기(분기)순이익": "net_profit",
    "당기순손익의합계": "net_profit",
    "당기주당손익": "eps",
    "당기총포괄이익": "comprehensive_income",
    "당기투자자산평가": "gains_on_valuation_of_investments",
    "당기확정부채의재측정": "remeasurement_elements_of_defined_benefit_plans",
    "당기초(수정)": "accumulated_effect_of_accounting_policy_change",
    "당기매각": "noncurrent_asset_held_for_sale_or_disposal_group",
    "당기미청구공사": "shortterm_gross_amount_due_from_customers_for_contract_work",
    "당사의변동": "change_by_merger_and_acquisition",
    "당기손익-공정가치": "designatedfinancial_assets_at_fv_through_profit",
    "당기손익-금융상품": "designatedfinancial_assets_at_fv_through_profit",
    "당기손익금융상품": "designatedfinancial_assets_at_fv_through_profit",
    "당기손익금융자": "designatedfinancial_assets_at_fv_through_profit",
    "당기손익인식근융": "designatedfinancial_assets_at_fv_through_profit",
    "당기손익인식금유": "designatedfinancial_assets_at_fv_through_profit",
    "당기손익인식금융": "designatedfinancial_assets_at_fv_through_profit",
    "당기손익인식부채": "other_current_liabilities",
    "당기손익인식음융": "designatedfinancial_assets_at_fv_through_profit",
    "당기손익인식자산의감액": "impairment_losses_on_assets",
    "당기손익인식지분상품": "designatedfinancial_assets_at_fv_through_profit",
    "당기손익인식지정": "designatedfinancial_assets_at_fv_through_profit",
    "당기손익인식채무상품": "designatedfinancial_assets_at_fv_through_profit",
    "당기손익재분류": "accumulated_other_comprehensive_income",
    "당기손익측정유가증권": "designatedfinancial_assets_at_fv_through_profit",
    "당기손익으로재분": "accumulated_other_comprehensive_income",
    "당기손익에포함된": "accumulated_other_comprehensive_income",
    "당기에발생한": "accumulated_other_comprehensive_income",
    "당기손익－공정가치지분": "designatedfinancial_assets_at_fv_through_profit",
    # 대 관련
    "대급금": "other_current_assets",
    "대여재고": "inventory",
    "대여채권": "other_receivables",
    "대출금": "shortterm_loans",
    "대체와기타변동": "other_adjustments",
    # 리스 관련
    "리스거래해지": "other_income",
    "리스계약변경": "other_expenses",
    "리스계약손실": "other_expenses",
    "리스계약이익": "other_income",
    "리스계약손익": "other_income",
    "리스관련차익": "other_income",
    "리스변경손익": "other_income",
    "리스변경이익": "other_income",
    "리스변경효과": "other_adjustments",
    "리스변동효과": "other_adjustments",
    "리스보증손실": "other_expenses",
    "리스사용료": "other_expenses",
    "리스설비": "other_tangible_assets",
    "리스순투자": "finance_lease_receivables",
    "리스원금반환": "finance_lease_receivables",
    "리스유동채권": "finance_lease_receivables",
    "리스이자": "interest_income",
    "리스적용효과": "accumulated_effect_of_accounting_policy_change",
    "리스정산손실": "other_expenses",
    "리스정산이익": "other_income",
    "리스중단이익": "other_income",
    "리스중도해지": "other_income",
    "리스채권": "finance_lease_receivables",
    "리스채무": "lease_obligations",
    "리스처분손익": "other_income",
    "리스해지비": "other_expenses",
    "리스해지손실": "other_expenses",
    "리스해지손익": "other_income",
    "리스해지이익": "other_income",
    "리브부채": "lease_obligations",
    # 마/매 관련
    "마일리지": "other_current_liabilities",
    "만기유동증권": "longterm_held_to_maturity_investments",
    "매각비유동부채": "liabilities_included_in_disposal_groups_classified_as_held_for_sale",
    "매각비유동자산": "noncurrent_asset_held_for_sale_or_disposal_group",
    "매각에정자산": "noncurrent_asset_held_for_sale_or_disposal_group",
    "매도기능증권": "longterm_availableforsale_financial_assets",
    "매도유가증권": "longterm_availableforsale_financial_assets",
    "매도주가지수옵션": "current_derivative_assets",
    "매도청구권행사": "other_reserves",
    "매립장설비": "other_tangible_assets",
    "매매가능증권": "longterm_availableforsale_financial_assets",
    # 기타
    "도서및훈련": "other_expenses",
    "도급비": "outsourcing_expenses",
    "드라마제작": "other_noncurrent_assets",
    "등록면허세": "other_income",
    "라.장기금융상품": "longterm_financial_instruments",
    "렌탈매출": "rental_income",
    "렌탈자산": "other_tangible_assets",
    "로열티수익": "other_income",
    "공장이전": "other_income",
}

autoMappings6 = {}
for acc in allUnmatched:
    for keyword, snakeId in keywordMap6.items():
        if keyword in acc and snakeId in sl._snakeToKor:
            autoMappings6[acc] = snakeId
            break

print(f"Auto-mappable (round 6): {len(autoMappings6)}")

if autoMappings6:
    count = sl.learnBatch(autoMappings6)
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
