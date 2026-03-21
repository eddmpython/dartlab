import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from core.dart.searchDart.finance.v7.synonymLearner import SynonymLearner

sl = SynonymLearner()
print(f"학습 전 동의어: {sl.synonymCount}")

mappings = {
    # 빈도 5 - 전환상환우선주
    "전환상환우선주의발행": "increase_in_preferred_stock_of_redemption",
    # 빈도 4 - 종속기업청산, 차입금
    "종속기업의청산": "gains_on_disposition_of_subsidiaries",
    "단기차입부채": "borrowings",
    "유동차입금": "shortterm_borrowings",
    # 빈도 3
    "기타순손익": "other_nonoperating_income",
    "공정가치금융자산의처분": "gains_on_disposal_of_financial_assets_measured_at_fair_value_through_profit_or_loss",
    "단기차입금및유동성장기부채": "current_portion_of_longterm_debt",
    "중단영업손익": "discontinued_operating_incomeloss",
    "차입금및사채": "borrowings",
    # 빈도 2
    "단기차입금등": "shortterm_borrowings",
    "이자부차입금": "borrowings",
    "유동종업원급여충당부채의증가(감소)": "others_shortterm_employee_benefits_liabilitiesbonuses_etc",
    "건물관리비": "sga",
    "회원권처분": "gains_on_disposition_of_investments",
    "기타변동에따른증가(감소),사용권자산": "leasedrightofuse_assets",
    # 빈도 1
    "합병법인세납부": "income_taxes_paid",
    "주식매입권행사로인한증가(감소),자본": "exercise_of_stock_options",
    "재보험계약자산부채": "reinsurance_assets",
    "자본에직접인식된거래합계": "total_stockholders_equity",
    "감가상각비및무형자산상각비": "depreciation_and_amortization",
    "우선주기본/희석주당이익": "dilution_earnings_per_share",
    "전환사채상환할증금": "yield_to_maturity_premium_on_bonds",
    "미디어제작비용": "cost_of_sales",
    "현금창출단위(CGU)처분으로인한순현금흐름": "gains_on_disposition_of_property_and_equipment",
    "예금잔액": "cash_and_cash_equivalents",
    "소모품비조정": "supplies",
    "비지배지분부채평가손실": "noncontrolling_interests_equity",
    "유동성리스금융부채": "lease_obligations",
    "조기상환청구": "repayment_of_longterm_borrowings",
    "유동성차입금": "current_portion_of_longterm_borrowings",
    "장기성차입부채의상환": "repayment_of_longterm_borrowings",
    "설립자본금": "capital_stock",
    "주식기준보상거래로인한현금흐름": "reserve_of_sharebased_payments",
    "법인세효": "income_tax_expense",
    "주식매입선택권의인식": "share_options",
    "차입금및유동성사채": "borrowings",
    "단기차입금외화환산손실": "foreign_exchange_losses",
    "주식발핼초과금": "paidin_capital_in_excess_of_par_value",
    "주식보상비인식": "stock_options",
    "해외사업장환산손익": "reserve_of_exchange_differences_on_translation",
    "투자부동산감가상각비,판관비": "depreciation_of_investment_properties",
    "차입금등": "borrowings",
    "주식매수선택권발행": "stock_options",
    "그밖의기타단기충당부채의증가(감소)": "longterm_provisions",
    "종속ㆍ관계기업투자주식관련비용": "gainslosses_in_subsidiaries_joint_ventures_associates",
    "금율리스부채의상환": "repayment_of_lease_liabilities",
    "리스자산부채의상환": "repayment_of_lease_liabilities",
    "(12)미지급법인세": "income_tax_payable",
    "자산유동화채무의감소": "securitized_assets",
    "차량리스료": "lease_obligations",
    "리스부채(비유동)의감소(증가)": "repayment_of_lease_liabilities",
    "금융부채": "financial_liabilities_measured_at_fair_value_through_profit_or_loss",
    "리스부채감소에따른현금유출": "repayment_of_lease_liabilities",
    "유동성장기미지금금의상환": "current_portion_of_longterm_debt",
    "비과세소득으로인한효과": "income_tax_expense",
    "사용권자산감소": "decrease_in_leasedrightofuse_assets",
    "임대자산감가상각비": "depreciation_of_investment_properties",
    "관련법인세": "income_tax_expense",
    "경상연구개발비(감가상가비)": "research_and_development_costs",
    "주식매수선태권소멸": "stock_options",
}

# snakeId 유효성 검증
validMappings = {k: v for k, v in mappings.items() if v in sl._snakeToKor}
invalidMappings = {k: v for k, v in mappings.items() if v not in sl._snakeToKor}

print(f"유효한 매핑: {len(validMappings)}개")
if invalidMappings:
    print(f"무효한 매핑: {len(invalidMappings)}개")
    for k, v in invalidMappings.items():
        print(f"  {k} -> {v}")

count = sl.learnBatch(validMappings)
print(f"\n학습 완료: {count}개")
print(f"학습 후 동의어: {sl.synonymCount}")
