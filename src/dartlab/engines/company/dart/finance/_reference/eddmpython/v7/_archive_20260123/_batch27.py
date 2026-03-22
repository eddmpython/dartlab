import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from core.dart.searchDart.finance.v7.synonymLearner import SynonymLearner

sl = SynonymLearner()
print(f"학습 전 동의어: {sl.synonymCount}")

mappings = {
    # 빈도 4
    "금융보증비용(손실)": "increasedecrease_in_financial_guarantee_provisions",
    # 빈도 3
    "그밖의기타장기충당부채의증가(감소)": "longterm_provisions",
    "복구충당부채의지급": "provisions_for_restoration_costs",
    "기타포괄손익-공정가치측정금융자산처분이익조정": "gains_on_disposal_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "단기금융상품평가이익(금융수익)": "gains_in_financial_assets_measured_at_fair_value_through_profit_or_loss",
    # 빈도 2
    "당기손익으로재분류되지는않을지분법적용대상인관계기업과공동기업의기타포괄손익의지분과관련된법인세": "income_taxes",
    "영업활동으로인한자산.부채의변동": "changes_in_assets_and_liabilities_from_operating_activities",
    "통화선물거래손실": "losses_on_futures_transactions",
    "1.투자활동으로인한현금흐름": "cash_flows_from_investing_activities",
    "임대료수입": "leasehold_deposits_received",
    "당기손익인식지정금융자산의감소(증가)": "financial_assets_at_fv_through_profit",
    "토지취득": "increase_in_land",
    "건물취득": "increase_in_buildings_and_structures",
    "현금및현금성자산에의한환율변동효과": "difference_by_changes_in_foreign_exchange_rates",
    "선수금증가": "advance_from_customers",
    "세후금액": "income_taxes",
    "당기손익-공정가치의무측정금융자산처분": "gains_on_disposal_of_financial_assets_measured_at_fair_value_through_profit_or_loss",
    "사용권자산상각비에대한조정": "depreciation_of_leasedrightofuse_assets",
    "무상증자비용발생": "capital_increase_decrease_without_consideration",
    "전환사채할인발행차금": "discount_on_bonds",
    # 빈도 1 - 복구/충당 관련
    "금융보증채무의증가": "increasedecrease_in_financial_guarantee_provisions",
    "복구충당부채전입액": "provisions_for_provisions_for_restoration_costs",
    "복구충당부채환입액": "reversion_of_provisions_for_restoration_costs",
    # 빈도 1 - 공정가치 관련
    "공정가치측정지분상품평가손익(세후기타포괄손익)": "gainslosses_on_valuation_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "공정가치측정지분상품처분손익(세후기타포괄손익)": "gains_on_disposal_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "기타포괄손익-공정가치측적지분상품처분손익": "gains_on_disposal_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "기타포괄손익-공정가치측정지분상품제거에따른변동": "gains_on_disposal_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "기타포괄손익-공정가치측정지분상품제거": "gains_on_disposal_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "기타포괄손익-공정가지측정금융자산": "financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "당기손익-공정가치측정금융자산투자수익수취": "gains_in_financial_assets_measured_at_fair_value_through_profit_or_loss",
    "당기손익-공정가치측정금융자산투자수익감소": "gains_in_financial_assets_measured_at_fair_value_through_profit_or_loss",
    "당기손익-공정가치금유자산의증가": "financial_assets_measured_at_fair_value_through_profit_or_loss",
    # 빈도 1 - 감가상각/사용권 관련
    "사용권자산감가상각비에대한조정": "depreciation_of_leasedrightofuse_assets",
    "감가상각비(사용권자산)": "depreciation_of_leasedrightofuse_assets",
    # 빈도 1 - 종속/관계/공동기업 관련
    "관계기업의당기순손익에대한지분변동": "other_comprehensive_income_of_associates_etc",
    "관계기업의당기순이익(손실)에대한지분": "other_comprehensive_income_of_associates_etc",
    "관계기업주식의매각": "gains_on_disposition_of_investments",
    "종속기업투자취득시순현금유출": "investments_in_subsidiaries",
    "종속기업인수선급금": "investments_in_subsidiaries",
    "공동기업투자주식의처분（관계기업투자주식）": "gains_on_disposition_of_investments",
    "비연결종속기업투자주식평가손익": "gainslosses_in_subsidiaries",
    "비연결종속기업투자주식취득순현금유출": "investments_in_subsidiaries",
    "비연결종속기업투자주식": "investments_in_subsidiaries",
    "비연결종속기업투자주식취득": "investments_in_subsidiaries",
    "비연결종속기업투식": "investments_in_subsidiaries",
    "지분법손익(손실": "gains_on_valuation_of_equity_method_securitiesequity_method_note",
    # 빈도 1 - 영업활동/투자활동/재무활동 관련
    "영업자산및부채의변동": "changes_in_assets_and_liabilities_from_operating_activities",
    "영업양수도로인한현금증감": "cash_inflows_by_merger_and_acquisition",
    "영업양도로인한현금증감": "cash_outflows_by_merger_and_acquisition",
    "영업양도로인한현금감소": "cash_outflows_by_merger_and_acquisition",
    # 빈도 1 - 매각예정/중단영업
    "매각예정자산처분미수금의감소": "gains_on_disposal_of_held_for_sale_or_disposal_group",
    "매각예정처분자산집단으로의대체": "noncurrent_asset_held_for_sale_or_disposal_group",
    "중단사업의해외사업장순투자의위험회피손익대체": "noncurrent_asset_held_for_sale_or_disposal_group",
    "중단영업에포함된현금및현금성자산": "noncurrent_asset_held_for_sale_or_disposal_group",
    "지배기업소유주지분중단영업당기순이익": "noncurrent_asset_held_for_sale_or_disposal_group",
    "지배기업소유주지분계속영업당기순이익": "profit_per_share_from_continuing_operations",
    # 빈도 1 - 배출권/온실가스
    "온실가스배출권평가이익": "emission_right",
    # 빈도 1 - 토지/건물/부동산
    "투자부동산취득이익": "gains_on_investment_in_properties",
    # 빈도 1 - 전환사채/상환
    "전환사채의전환(신주발행비)": "discount_on_bonds",
    "상환전환우선주증가": "longterm_preferred_stock_of_redemption",
    "상환의무부채이익": "gains_on_redemption_of_bonds",
    "상환의무부채의증가": "longterm_preferred_stock_of_redemption",
    # 빈도 1 - 주당순이익
    "보통주분기기본및희석주당이": "earnings_per_share",
    "우선주분기기본및희석주당이": "dilution_earnings_per_share",
    # 빈도 1 - 매출채권/기타채권
    "매출채권및기타채권의(증가)감소": "trade_and_other_receivables",
    # 빈도 1 - 법인세/이연
    "장기미지급법인세": "income_taxes",
    "이연부채의증가(감소)": "deferred_tax_liabilities",
    "기타자본조정법인세율변동효과": "deferred_taxes_change",
    # 빈도 1 - 기타
    "상각후원가유가증권의처분": "gains_on_disposition_of_investments",
    "상각후원가측정금융자산중도회수이익": "gains_on_disposition_of_investments",
    "상각후원가축정금융자산의취득": "gains_on_disposition_of_investments",
    "기타회원권처분이익": "gains_on_disposition_of_investments",
    "회원권의발행": "gains_on_disposition_of_investments",
    "채무보증수수료": "assets_guarantee_contracts",
    "기타대출평가및처분손실": "losses_on_disposition_of_investments",
    "통화선도": "future_transaction",
    "분할자본조정": "change_by_merger_and_acquisition",
    "감자차손보존": "capital_increase_decrease_without_consideration",
    "감차손보전": "capital_increase_decrease_without_consideration",
    "연결범위변동에의한증가": "change_by_merger_and_acquisition",
    "주식선택권의비지배지분대체": "exercise_of_stock_options",
    "장기미지급금감소": "longterm_other_payables",
    "기타금융부채의취득(처분)": "financial_liabilities_measured_at_fair_value_through_profit_or_loss",
    "기타포괄손익-공정가치측정금융자산신용위험평가손실": "gainslosses_on_valuation_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "주식의포괄적교환등": "change_by_merger_and_acquisition",
    "기능통화변경": "difference_by_changes_in_foreign_exchange_rates",
    "자본에직접인식된주주와의거래등:": "change_by_merger_and_acquisition",
    "사업양도에의한기타자본잉여금변동": "cash_outflows_by_merger_and_acquisition",
    "기타유동산잔의증가": "decreaseincrease_in_other_assets",
    "지배기억의소유주에귀속될당기순이익(손실)": "earnings_per_share",
    "임직원대출상환": "decreaseincrease_in_loans_and_receivables",
    "미지급(배당금)": "dividends",
    "수입연체료": "interest_on_loans_and_receivables",
    "주종장기대여금의증가": "decreaseincrease_in_loans_and_receivables",
    "기타조정": "changes_in_assets_and_liabilities_from_operating_activities",
    "기타매출액": "sales",
    "(2)비현금비용조정": "addition_of_expenses_of_noncash_transactions",
    "기타상품매출원가": "cost_of_goods_sold",
    "기타상품매출": "sales",
    "가스매출원가": "cost_of_goods_sold",
    "호텔매출액": "sales",
    "레저매출원가": "cost_of_goods_sold",
    "선수금증가": "advance_from_customers",
}

# snakeId 유효성 검증
validMappings = {}
invalidMappings = {}
for korName, snakeId in mappings.items():
    if snakeId in sl._snakeToKor:
        validMappings[korName] = snakeId
    else:
        invalidMappings[korName] = snakeId

print(f"유효한 매핑: {len(validMappings)}개")
print(f"무효한 매핑: {len(invalidMappings)}개")
if invalidMappings:
    print("무효 목록:")
    for k, v in invalidMappings.items():
        print(f"  {k} -> {v}")

# 학습 실행
count = sl.learnBatch(validMappings)
print(f"\n학습 완료: {count}개")
print(f"학습 후 동의어: {sl.synonymCount}")
