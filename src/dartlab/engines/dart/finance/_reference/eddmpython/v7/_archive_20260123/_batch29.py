import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from core.dart.searchDart.finance.v7.synonymLearner import SynonymLearner

sl = SynonymLearner()
print(f"학습 전 동의어: {sl.synonymCount}")

mappings = {
    # === 빈도 2-3 ===
    "생산용생물자산의취득": "tangible_assets",
    "전환상환우선주부채상환할증금": "yield_to_maturity_premium_on_bonds",
    "실용신안권": "intangible_assets",
    "단기제품보증충당부채의증가(감소)": "longterm_provisions",
    "사업결합으로인한순현금유출": "cash_outflows_by_merger_and_acquisition",
    "(3)운전자본의조정": "changes_in_assets_and_liabilities_from_operating_activities",
    # === 공정가치/포괄손익 관련 ===
    "공정가치측정지분상품처분에따른이익잉여금대체": "gains_on_disposal_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "지분법적용대상관계기업의기타포괄손익에대한지분": "other_comprehensive_income_of_associates_etc",
    "기타포괄손익-공정가치금융자산의재측정요소": "gainslosses_on_valuation_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "기타포괄손익-공정가치금융자산의처분": "gains_on_disposal_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "기타포괄손익-공정가치측정금융자산평가손익재분류(세후기타포괄손익)": "gainslosses_on_valuation_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "기타손익-공정가치측정금융자산의취득": "financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "기타포괄손익_공정가치측정지분상품": "gainslosses_on_valuation_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    "당기손익인식금융자산의처분이익": "gains_on_disposal_of_financial_assets_measured_at_fair_value_through_profit_or_loss",
    "당기손익인식지정금융자산": "financial_assets_at_fv_through_profit",
    "당기손익인식자산의처분": "gains_on_disposal_of_financial_assets_measured_at_fair_value_through_profit_or_loss",
    "매도가능금융증권평가": "gainslosses_on_valuation_of_financial_assets_measured_at_fair_value_through_other_comprehensive_income",
    # === 중단/계속영업 ===
    "당기중단사업총포괄손익": "discontinued_operating_incomeloss",
    "당기계속사업총포괄손익": "profit_from_continuing_operations",
    "총기타포괄이익": "other_comprehensive_income",
    # === 종속/관계기업 ===
    "종속기업유상증자": "investments_in_subsidiaries",
    "종속회사의주식매입선택권": "share_options",
    "종속회사배당": "dividends",
    "종속회사설립": "investments_in_subsidiaries",
    "종속기업투자현금흐름": "investments_in_subsidiaries",
    "종속기업흡수합병으로인한현금유출": "cash_outflows_by_merger_and_acquisition",
    "종속기업주식처분이익(손실)": "gains_on_disposition_of_subsidiaries",
    "종속기업에대한투자자산의추가취득": "investments_in_subsidiaries",
    "종속기업투자주식의추가취득": "investments_in_subsidiaries",
    "종속기업투자처분(보유현금성자산차감후)": "gains_on_disposition_of_subsidiaries",
    "종속기업지분법자본변동": "gainslosses_in_subsidiaries",
    "종속기업/관계기업/공동기업투자손실": "gainslosses_in_subsidiaries_joint_ventures_associates",
    "관계기업에대하투자자산": "investments_in_associates",
    "관기업주식처분이익(손실)": "gains_on_disposition_of_investments",
    "관계회사등투자손익": "gainslosses_in_subsidiaries_joint_ventures_associates",
    "지분법순이익(손실)": "gains_on_valuation_of_equity_method_securitiesequity_method_note",
    "지분법투자주식처분": "gains_on_disposition_of_equity_method_securities",
    "지분법이익잉여금조정": "retained_earnings",
    "지분법소급적용": "retained_earnings",
    # === 주식선택권/주식기준보상 ===
    "주식선택권행사비용": "exercise_of_stock_options",
    "주식선택권행사": "exercise_of_stock_options",
    "주식기준보상소멸이익": "stock_options",
    "주식매수선택권이연법인세효과": "stock_options",
    "주식매주선택권의부여": "stock_options",
    "주식매선택권": "stock_options",
    "미행사주식선택권": "stock_options",
    "주식발행초과금의자본전입": "paidin_capital_in_excess_of_par_value",
    # === 차입금/상환 관련 ===
    "유동성장기치입금의상환": "current_portion_of_longterm_debt",
    "유동상장기치입금의상환": "current_portion_of_longterm_debt",
    "유동성장기차입급의상환": "current_portion_of_longterm_debt",
    "유돋성장기부채의상환": "current_portion_of_longterm_debt",
    "유동성자익부채의상환": "current_portion_of_longterm_debt",
    "장기사채의감소": "decrease_in_longtermborrowings",
    "공급자금융약정차입금의상환": "decrease_in_longtermborrowings",
    "단기차입금및기타금융부채": "shortterm_borrowings",
    "상환부채의증가": "longterm_preferred_stock_of_redemption",
    # === 리스/사용권자산 ===
    "리스부채의수취": "lease_obligations",
    "유동성장기임대보증금의증가": "increase_in_leasehold_deposits_received",
    "유동성장기임대보증금": "leasehold_deposits_received",
    # === 합병/분할 ===
    "흡수합병으로인한변동": "change_by_merger_and_acquisition",
    "합병으로인한자금유출": "cash_outflows_by_merger_and_acquisition",
    "합병으로인한취득": "cash_outflows_by_merger_and_acquisition",
    "상장합병비용": "cash_outflows_by_merger_and_acquisition",
    "사업결합으로인한현금흐름의유입": "cash_inflows_by_merger_and_acquisition",
    # === 연결 ===
    "연결범위변동으로인한증가액": "gainslosses_in_subsidiaries",
    "연결실체변동으로인한증가": "gainslosses_in_subsidiaries",
    "연결범위변동으로인한순감소": "gainslosses_in_subsidiaries",
    # === 법인세 ===
    "당기손익으로재분류되지않는세후기타포괄손익의법인세": "income_taxes",
    "자기주식처분손실법인세효과": "income_taxes",
    # === 자본금/잉여금 ===
    "기타불입자본이입액": "other_capital_surplus",
    "기타불입자본의이입": "other_capital_surplus",
    "자본준비금감액및이익잉여금전입": "retained_earnings",
    "자본잉여금의자본금전입": "capital_stock",
    "설립증자": "paid_in_capital_increase",
    "우리사주": "treasury_stock",
    "유상증자로인한지분율변동": "paid_in_capital_increase",
    "무상수증": "other_capital_surplus",
    "무상증자관련비용": "capital_increase_decrease_without_consideration",
    "자산수증": "other_capital_surplus",
    # === 감가상각/투자부동산 ===
    "감가상각누계액(투자부동산-건물)": "investment_in_properties",
    "투자부동산취득세환급": "investment_in_properties",
    # === 배출권 ===
    "배출자산": "emission_right_assets",
    # === 유형자산 ===
    "유형자산재평가손익": "tangible_assets",
    "유형자산매각미수금회수": "disposal_of_tangible_assets",
    "유형자산처분미수금의감소": "disposal_of_tangible_assets",
    "유형자산위취득": "tangible_assets",
    "시설물이용권의처분": "gains_on_disposition_of_investments",
    # === 파생상품 ===
    "통화선도자산의정산": "future_transaction",
    "파생금융상품부채": "shortterm_derivative_liabilities",
    "파생금융상품자산": "shortterm_derivative_assets",
    "파생상품(전환권)": "shortterm_derivative_assets",
    "전환권재분류": "consideration_for_conversion_rights",
    "신주인수권대가등의변동": "stock_warrants_conversion_rights",
    # === 전환사채 ===
    "전환사채재매입": "longterm_borrowings",
    "전환사채자본전입": "longterm_borrowings",
    "전환사채발생": "longterm_borrowings",
    "전환사채주식발행비용": "longterm_borrowings",
    # === 보증금 ===
    "임대보증금및예치보증금의증가": "increase_in_leasehold_deposits_received",
    "기타보증금의지급": "longterm_gurarantee",
    "보증금지급": "longterm_gurarantee",
    # === 충당부채 ===
    "복구충당부채의상환": "provisions_for_restoration_costs",
    "판보충전입액": "longterm_provisions",
    "판매보증충담금전입액": "longterm_provisions",
    "금융보증비용(환입）": "increasedecrease_in_financial_guarantee_provisions",
    # === 정부보조금 ===
    "정부보조금(유형자산)의수령": "government_grants_deferred_income",
    "정부보조금(무형자산)의수령": "government_grants_deferred_income",
    "국고보조금자산의증가": "government_grants_deferred_income",
    # === 기타 금융 ===
    "비유동기타금융부채의증가": "other_longterm_financial_liabilities",
    "유동기타금융부채의증가": "other_current_financial_liabilities",
    "기타비유동금융부채의순증가(감소)": "other_longterm_financial_liabilities",
    "기타비유동부채의상환": "other_noncurrent_liabilities",
    "기타비유동금융자산처분손실": "losses_on_disposition_of_investments",
    "비지배지분부채금융비용": "noncontrolling_interests_equity",
    "대출채권관련이익": "gains_on_disposition_of_investments",
    "대출채권관련손실": "losses_on_disposition_of_investments",
    "금융수수료조정": "interest_expenses",
    "금융수수료": "interest_expenses",
    "금융업영업수익": "sales",
    "비금융기타채무": "other_current_liabilities",
    # === 기타 ===
    "입회금의감소": "longterm_gurarantee",
    "입회금의증가": "longterm_gurarantee",
    "장기기타수취채권의증감": "lt_trade_and_other_receivables",
    "IFRS1115호효과": "retained_earnings",
    "미수이자수익": "interest_income",
    "기술료수입": "other_nonoperating_income",
    "(기초자본[수정후])": "capital_stock",
    "금융상품대손상각비(대손충당금환입)": "expenses_of_allowance_for_doubtful_accounts",
    "유상증자로인한자본감소": "paid_in_capital_increase",
    "보유현금": "cash_and_cash_equivalents",
    "4.재고자산": "inventories",
    "기타수수료": "sga",
    "소모공구비": "sga",
    "금융기관예치금의불입": "interest_on_deposits_to_bank",
    "금융기관예치금의수령": "interest_on_deposits_to_bank",
    "공모사채분담금환입": "other_nonoperating_income",
    "기타비유동부채금융부채의증가": "other_longterm_financial_liabilities",
    "일반사무위탁수수료": "sga",
    "인쇄": "sga",
    "복구비의지출": "provisions_for_restoration_costs",
    "유동당기손익인식금융자산[개요]": "financial_assets_at_fv_through_profit",
    "선급공사비": "advance_paymentsconstruction_outside_processing_expenses",
    "매각예정비유동자산분류": "noncurrent_asset_held_for_sale_or_disposal_group",
    "해외사업환산이익의이익잉여금대체": "retained_earnings",
    "해외사업환산외환차익": "reserve_of_exchange_differences_on_translation",
    "제3자배정콜옵션관련기초조정": "stock_warrants_conversion_rights",
    "장기금융상품평가이익": "longterm_financial_instruments",
    "단기투자증권처분이익": "gains_on_disposal_of_financial_assets_measured_at_fair_value_through_profit_or_loss",
    "보통주기본,희석주당이익(손실)": "earnings_per_share",
    "우선주기본,희석주당이익(손실)": "dilution_earnings_per_share",
    "기타(토지취득금액조정)": "land",
}

# snakeId 유효성 검증
validMappings = {k: v for k, v in mappings.items() if v in sl._snakeToKor}
invalidMappings = {k: v for k, v in mappings.items() if v not in sl._snakeToKor}

print(f"유효: {len(validMappings)}개, 무효: {len(invalidMappings)}개")
if invalidMappings:
    for k, v in invalidMappings.items():
        print(f"  {k} -> {v}")

count = sl.learnBatch(validMappings)
print(f"\n학습: {count}개")
print(f"동의어: {sl.synonymCount}")
