import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from core.dart.searchDart.finance.v7.synonymLearner import SynonymLearner

sl = SynonymLearner()
fs = sl._getFinanceSearch()
codes = fs.getCorpList()["stock_code"].drop_nulls().to_list()

allUnmatched = set()
alreadyLearned = set(sl._synonyms.keys())
for code in codes:
    r = sl.analyzeCompany(code)
    for acc in r.unmatched:
        if acc not in alreadyLearned:
            allUnmatched.add(acc)

print(f"Remaining: {len(allUnmatched)}")

keywordMap = {
    # 기타 패턴
    "기타단기성자산": "other_current_assets",
    "기타비유동자산의감소": "other_noncurrent_assets",
    "기타비유동자산의증가": "other_noncurrent_assets",
    "기타비유동자산의처분": "other_noncurrent_assets",
    "기타유동자산의감소": "other_current_assets",
    "기타유동자산의증가": "other_current_assets",
    "기타유동부채의감소": "other_current_liabilities",
    "기타유동부채의증가": "other_current_liabilities",
    "기타부채의처분": "other_current_liabilities",
    "기타부채의증가": "other_current_liabilities",
    "기타채권의감소": "other_receivables",
    "기타채권의증가": "other_receivables",
    "기타채무의감소": "other_payables",
    "기타채무의증가": "other_payables",
    "기타포괄손익의대체": "other_comprehensive_income",
    "기타조정": "other_adjustments",
    "기타영업활동": "other_cash_flows_from_operating_activities",
    # 유동성 패턴
    "유동성금융리스": "current_portion_of_noncurrent_liabilities",
    "유동성장기": "current_portion_of_noncurrent_liabilities",
    "유동금융리스": "lease_liabilities",
    # 자본/자산 패턴
    "자기추식": "treasury_stock",
    "자기주식처분": "gains_on_disposals_of_treasury_stock",
    "자산수증": "other_income",
    "자산양도": "gains_on_disposals_of_tangible_assets",
    "자산취득": "tangible_assets",
    # 리스 잔여 패턴
    "리스채권": "lease_receivables",
    # 파생 오타 패턴
    "파생삼품": "derivative_assets",
    "파생상픔": "derivative_assets",
    "파생부채": "derivative_liabilities",
    # 총포괄 패턴
    "총포괄순이익": "total_comprehensive_income",
    "총포괄이익": "total_comprehensive_income",
    # 단기 패턴
    "단기매매": "short_term_trading_securities",
    "단기금웅": "short_term_financial_instruments",
    "단가치입금": "deposits",
    # 퇴직 패턴
    "퇴직금": "retirement_benefits",
    "퇴직/연차": "retirement_benefits",
    # 금융리스 패턴
    "금융리스채권": "lease_receivables",
    "금융상품거래": "other_finance_income",
    # 전환/전기 패턴
    "전환의행사": "paid_in_capital",
    "전한권의행사": "paid_in_capital",
    "전화권의행사": "paid_in_capital",
    "전기공급": "tangible_assets",
    "전기료": "utilities_expenses",
    # 시설 패턴
    "시추설비": "tangible_assets",
    "시설장치": "tangible_assets",
    "시설장비": "tangible_assets",
    "시험기구": "tangible_assets",
    "시설분담금": "other_noncurrent_assets",
    # 장기금융리스
    "장기금융리스": "lease_liabilities",
    "장기채무": "noncurrent_borrowings",
    # 영업 패턴
    "영업활등": "changes_in_assets_and_liabilities",
    "영업자산": "changes_in_assets_and_liabilities",
    "영엽외손익": "other_non_operating_income",
    "영업관련자산": "changes_in_assets_and_liabilities",
    # 임목/임차
    "임원의보수": "salaries",
    "임목": "biological_assets",
    "임차자산개량권": "intangible_assets",
    # 보상/보증
    "보상자산": "other_current_assets",
    "보상비": "other_selling_and_administrative_expenses",
    "보즘금": "other_deposits",
    "보증수증": "other_income",
    # 매도/매수 옵션
    "매립장설비": "tangible_assets",
    "매도주가지수옵션": "derivative_assets",
    "매수주가지수옵션": "derivative_assets",
    # 위탁
    "위탁대리점": "other_current_assets",
    "위험회피활동": "other_cash_flows_from_operating_activities",
    # 희석주당 오타
    "희석주당": "diluted_earnings_per_share",
    # 비유동/비현금
    "비현금조정": "other_adjustments",
    "비유동파생": "derivative_assets",
    "비유동자산계": "noncurrent_assets",
    "비유동부채계": "noncurrent_liabilities",
    # 타계정
    "타계정": "other_adjustments",
    # 채권/채무
    "채무보증": "other_income",
    "채권추심": "other_income",
    "채권조정": "other_income",
    # 공구/공사
    "공사자재": "inventories",
    "공장이전보상금": "other_income",
    "공동기업유상감자": "investments_in_associates",
    # 지속적관여
    "지속적관여자산": "other_current_assets",
    "지분매각": "gains_on_disposals_of_investments",
    "지분매도": "gains_on_disposals_of_investments",
    "지배회사총포괄": "total_comprehensive_income",
    # 이자율 패턴
    "이자율평가": "derivative_assets",
    "이자율스평가": "derivative_assets",
    "이행보증": "other_noncurrent_liabilities",
    "이익조정": "other_adjustments",
    # 기타 ASCII/특수
    "조정": "other_adjustments",
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
    else:
        break
sixPlus = sum(v for k, v in dist.items() if k >= 6)
if sixPlus:
    print(f"  6+ unmapped: {sixPlus} stocks")
