import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from core.dart.searchDart.finance.v7.synonymLearner import SynonymLearner

sl = SynonymLearner()

directMappings = {
    "⑶자산및부채의탕감": "changes_in_assets_and_liabilities_from_operating_activities",
    "⑵조정": "changes_in_assets_and_liabilities_from_operating_activities",
    "기타영업수입": "other_nonoperating_revenues",
    "잡수입": "other_nonoperating_revenues",
    "1.기타이익": "other_nonoperating_revenues",
    "이자율평가스왑": "shortterm_derivative_assets",
    "기타현금의감소": "other_cash_flows_from_operating_investing_financing_activities",
    "기타포관손익-공정가치지분상품의증가": "total_comprehensive_income",
    "확정계약이익": "other_nonoperating_revenues",
    "기타미확정부채": "other_current_liabilities",
    "영업활등으로인한자산및부채의증감": "changes_in_assets_and_liabilities_from_operating_activities",
    "염가매수선택권환입": "other_nonoperating_revenues",
    "단기매매차익의변환": "other_nonoperating_revenues",
    "단기매매차익": "other_nonoperating_revenues",
    "사업부문조정": "changes_in_assets_and_liabilities_from_operating_activities",
    "처분으로인한대체": "changes_in_assets_and_liabilities_from_operating_activities",
    "기타잡이익": "other_nonoperating_revenues",
    "집기기품": "tools_and_office_equipment",
    "난방비": "water_light_and_heating_expenses",
    "납후봉사비": "other_operating_expenses",
    "임원의보수": "salaries_and_wages",
    "채권조정이익": "other_nonoperating_revenues",
    "부산물평가손실": "other_nonoperating_expenses",
    "부산품평가손실": "other_nonoperating_expenses",
    "기타(자본직접인식거래)": "stockholders_equity",
    "기타손익의증감": "changes_in_assets_and_liabilities_from_operating_activities",
    "입목의처분": "cash_flows_from_investing",
    "기타유동재산": "other_current_assets",
    "개발비차감": "intangible_assets",
    "개발비의차감": "intangible_assets",
    "자본잉금": "capital_surplus",
    "인수대금의증가": "cash_flows_from_investing",
    "전기료": "water_light_and_heating_expenses",
    "판촉비": "advertising_expenses",
    "비현금조정소계": "changes_in_assets_and_liabilities_from_operating_activities",
    "파생상픔거래이익": "gains_on_valuations_of_derivatives",
    "기타비유동부": "other_noncurrent_liabilities",
    "복리후생비에대한조정": "changes_in_assets_and_liabilities_from_operating_activities",
    "기타단기금융상품감소": "decrease_in_shortterm_financial_instruments",
    "자본주식처분": "sale_of_treasury_stock",
    "기티유동부채": "other_current_liabilities",
    "미수법인제의감소(증가)": "changes_in_assets_and_liabilities_from_operating_activities",
    "투자자산수증이익": "other_nonoperating_revenues",
    "이자율평가손익": "shortterm_derivative_assets",
    "리스순투자의감": "cash_flows_from_investing",
    "리스순투자의감소": "cash_flows_from_investing",
    "사용자산": "leased_assets",
    "원전자본의변동": "stockholders_equity",
    "유전개발의처분": "cash_flows_from_investing",
    "용구수입": "other_nonoperating_revenues",
    "유동성장부채의감소": "current_portion_of_longterm_debt",
    "유실수": "property_plant_and_equipment",
    "기타비유동투자자산의감소": "cash_flows_from_investing",
    "기타기부금": "donations",
    "리스채권감소(증가)": "trade_and_other_current_receivables",
    "리스채권증가(감소)": "trade_and_other_current_receivables",
    "원인자부담금의수령": "other_nonoperating_revenues",
    "부당거래반환이익": "other_nonoperating_revenues",
    "기대신용손실": "expenses_of_allowance_for_doubtful_accounts",
    "등록면허세의환급": "other_nonoperating_revenues",
    "누적순이익": "net_profit",
    "원재료의증가": "raw_materialssubmaterials",
    "단기금융상품거래이익": "other_nonoperating_revenues",
    "파상상품평가손실": "losses_on_valuations_of_derivatives",
    "가.조정": "changes_in_assets_and_liabilities_from_operating_activities",
    "다.주임종단기채권의감소": "cash_flows_from_investing",
    "원재료매각이익": "other_nonoperating_revenues",
    "원자재처분손익": "other_nonoperating_gainslosses",
    "기타비유동금부채의증가": "other_noncurrent_liabilities",
    "유동충동부채": "other_current_liabilities",
    "장기대금의감소": "cash_flows_from_investing",
    "장기입금의증가": "other_noncurrent_liabilities",
    "-조정": "changes_in_assets_and_liabilities_from_operating_activities",
    "Ｍ＆Ａ인수대금": "cash_flows_from_investing",
    "분기총괄이익": "total_comprehensive_income",
    "유의적인영향력상실에따른재분류": "cash_flows_from_investing",
    "지배지분포괄순손익": "total_comprehensive_incomeowners_of_parent_equity",
    "파생거래수취": "cash_flows_from_investing",
    "기타비유동금즁자산의증가": "cash_flows_from_investing",
    "유동화채무(주15,20)": "cash_flows_from_financing_activities",
    "기타손(익)": "other_nonoperating_gainslosses",
    "기타자산의(증)감": "changes_in_assets_and_liabilities_from_operating_activities",
    "(유동성사책상환할증금)": "current_portion_of_longterm_debt",
    "유동성차채": "current_portion_of_longterm_debt",
    "지급어음의감소": "changes_in_assets_and_liabilities_from_operating_activities",
    "기타소득": "other_nonoperating_revenues",
    "설비장치": "property_plant_and_equipment",
    "가스": "water_light_and_heating_expenses",
    "파상생품평가손익": "gains_on_valuations_of_derivatives",
    "기타영업자산ㆍ부채의증감": "changes_in_assets_and_liabilities_from_operating_activities",
    "단기금용상품의감소": "decrease_in_shortterm_financial_instruments",
    "기타비유동금자산의감소(증가)": "cash_flows_from_investing",
    "기타비유종자산의순증감": "changes_in_assets_and_liabilities_from_operating_activities",
    "선수부채": "advance_from_lease",
    "유동부채계": "current_liabilities",
    "유동자산계": "current_assets",
    "기타이익조정": "changes_in_assets_and_liabilities_from_operating_activities",
    "보증수증이익": "other_nonoperating_revenues",
    "계정대체": "changes_in_assets_and_liabilities_from_operating_activities",
    "순운전자의변동": "changes_in_assets_and_liabilities_from_operating_activities",
    "기타김융부채(유동)의증가": "other_current_liabilities",
    "기타차이조정": "changes_in_assets_and_liabilities_from_operating_activities",
    "차량": "motor_vehicles",
    "기타자산항목": "other_current_assets",
    "차입원료": "raw_materialssubmaterials",
    "유가증권처분": "cash_flows_from_investing",
    "기타비투자자산의증가": "cash_flows_from_investing",
    "파생금자산의감소": "cash_flows_from_investing",
    "리스채권자산의감소": "trade_and_other_current_receivables",
    "기타현금의증가(감)": "other_cash_flows_from_operating_investing_financing_activities",
    "실험기구의처분": "decrease_in_tools_and_office_equipment",
    "기타당좌산의감소(증가)": "changes_in_assets_and_liabilities_from_operating_activities",
    "이익잉여": "retained_earnings",
    "기타자산의증가(증가)": "changes_in_assets_and_liabilities_from_operating_activities",
    "염가매수차이": "other_nonoperating_revenues",
    "엽엉외손익": "other_nonoperating_gainslosses",
    "재고평가손실(환입)": "inventory",
    "기타투자자산": "investment_assets",
    "금융이익_기타": "gains_on_disposition_of_other_financial_assets",
    "자본항목간대체": "stockholders_equity",
    "원화예금": "cash_and_cash_equivalents",
    "매출조정": "sales",
    "기타금부채의감소": "other_current_liabilities",
    "기타금부채의증가": "other_current_liabilities",
    "이조정": "changes_in_assets_and_liabilities_from_operating_activities",
    "기타매출": "sales",
    "기타자산(유동)의감소(증가)": "changes_in_assets_and_liabilities_from_operating_activities",
    "기타채의감소": "changes_in_assets_and_liabilities_from_operating_activities",
    "기타비유동채권감소(증가)": "changes_in_assets_and_liabilities_from_operating_activities",
    "기타영업손실": "other_operating_expenses",
    "재매입이익": "other_nonoperating_revenues",
    "재매입이익(자본)": "other_nonoperating_revenues",
    "기타제예금의감소": "cash_flows_from_investing",
    "장기근속포상금지급": "salaries_and_wages",
    "유입": "other_cash_flows_from_operating_investing_financing_activities",
    "유출": "other_cash_flows_from_operating_investing_financing_activities",
    "기타수채권의감소(증가)": "changes_in_assets_and_liabilities_from_operating_activities",
    "유리스채권": "trade_and_other_current_receivables",
    "유동장기부채의증가": "increase_in_current_portion_of_longterm_debt",
    "유동금융기관예치의증가": "cash_flows_from_investing",
    "분류변경": "changes_in_assets_and_liabilities_from_operating_activities",
    "변동대가조정": "changes_in_assets_and_liabilities_from_operating_activities",
}

# Validate all snakeIds
invalid = [(k, v) for k, v in directMappings.items() if v not in sl._snakeToKor]
if invalid:
    print(f"Invalid snakeIds ({len(invalid)}):")
    for k, v in invalid:
        print(f"  {k} -> {v}")
else:
    count = sl.learnBatch(directMappings)
    print(f"Learned: {count}")
    print(f"Total synonyms: {sl.synonymCount}")

    fs = sl._getFinanceSearch()
    codes = fs.getCorpList()["stock_code"].drop_nulls().to_list()
    full = 0
    dist = {}
    for code in codes:
        r = sl.analyzeCompany(code)
        if r.matchRate == 100.0:
            full += 1
        else:
            un = len(r.unmatched)
            dist[un] = dist.get(un, 0) + 1
    print(f"\n100% stocks: {full} / {len(codes)} ({full * 100 / len(codes):.1f}%)")
    for k in sorted(dist.keys()):
        if k <= 5:
            print(f"  {k} unmapped: {dist[k]} stocks")
    sixPlus = sum(v for k, v in dist.items() if k >= 6)
    if sixPlus:
        print(f"  6+ unmapped: {sixPlus} stocks")
