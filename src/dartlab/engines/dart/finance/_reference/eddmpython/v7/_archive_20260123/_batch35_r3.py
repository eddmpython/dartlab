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
    "리스채권": "lease_receivables",
    "리스정산": "gains_on_disposals_of_tangible_assets",
    "리스변동": "other_noncurrent_liabilities",
    "리스해지": "other_income",
    "금융리스채권": "lease_receivables",
    "파생생품": "derivative_assets",
    "파상상품": "derivative_liabilities",
    "선급세금": "prepaid_expenses",
    "선납세금": "prepaid_expenses",
    "총포괄이익(손실)합계": "total_comprehensive_income",
    "총포괄이익계": "total_comprehensive_income",
    "총포괄손익계": "total_comprehensive_income",
    "분기총포괄이익계": "total_comprehensive_income",
    "반기총포괄이익계": "total_comprehensive_income",
    "총포괄손": "total_comprehensive_income",
    "분기총손실": "net_profit",
    "분기총이익": "net_profit",
    "유동성부채": "current_portion_of_noncurrent_liabilities",
    "유동장기채무": "current_portion_of_noncurrent_liabilities",
    "타계정대체": "other_adjustments",
    "타계정으로대체": "other_adjustments",
    "투자주식": "investments_in_subsidiaries",
    "기타보종금": "other_deposits",
    "기타비유동부채증가": "other_noncurrent_liabilities",
    "기타비유동부채의순증가": "other_noncurrent_liabilities",
    "기타의비유동부채": "other_noncurrent_liabilities",
    "기타의부채": "other_current_liabilities",
    "기타비유동비금융부": "other_noncurrent_liabilities",
    "기타금융손익": "other_finance_income",
    "자본거래이익": "other_income",
    "자산,부채의변동": "changes_in_assets_and_liabilities",
    "자산및부채의증가": "changes_in_assets_and_liabilities",
    "자산및부채의탕감": "changes_in_assets_and_liabilities",
    "공구기구": "tools",
    "용지의증가": "tangible_assets",
    "퇴직금전입액": "retirement_benefits",
    "연차수당": "salaries",
    "제수당": "salaries",
    "포상비": "other_selling_and_administrative_expenses",
    "사원모집비": "other_selling_and_administrative_expenses",
    "홍보비": "advertising_expenses",
    "외주비": "outsourcing_expenses",
    "채굴권": "intangible_assets",
    "배상금": "other_income",
    "보상금이익": "other_income",
    "제각채권의회수": "other_income",
    "잡수입": "other_income",
    "기타영업수입": "other_income",
    "법정준비금": "legal_reserve",
    "법적적림금": "legal_reserve",
    "법정적립금": "legal_reserve",
    "선급제세": "prepaid_expenses",
    "기타현금흐름": "other_cash_flows_from_operating_activities",
    "납입액": "paid_in_capital",
    "자사주소각": "treasury_stock",
    "유평자산평가": "tangible_assets",
    "초인플레이션": "other_comprehensive_income",
    "결솜금처리액": "retained_earnings",
    "코스": "other_income",
    "MIDP이익": "other_income",
    "APDP이익": "other_income",
    "영업외손익": "other_non_operating_income",
    "기타영업외손익": "other_non_operating_income",
    "유동성예수부채": "current_portion_of_noncurrent_liabilities",
    "유동성전환부채": "current_portion_of_noncurrent_liabilities",
    "유동성전환금융상품": "current_portion_of_noncurrent_liabilities",
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
