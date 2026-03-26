import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from core.dart.searchDart.finance.v7.synonymLearner import SynonymLearner

sl = SynonymLearner()
fs = sl._getFinanceSearch()
corpDf = fs.getCorpList()
codes = corpDf["stock_code"].drop_nulls().to_list()

allUnmatched = set()
for code in codes:
    try:
        r = sl.analyzeCompany(code)
        if r and 1 <= r.unmatchedCount <= 10:
            for acc in r.unmatched:
                allUnmatched.add(acc)
    except:
        pass

print(f"1-10 unmapped 고유 계정: {len(allUnmatched)}개")

keywordMap = {
    "창출": "cash_flows_from_operatings",
    "현금유입": "cash_flows_from_operatings",
    "현금유출": "cash_flows_from_operatings",
    "현금흐름": "cash_flows_from_operatings",
    "당기순이익": "net_income",
    "당기순손": "net_income",
    "분기순이익": "net_income",
    "분기순손": "net_income",
    "반기순이익": "net_income",
    "반기순손": "net_income",
    "당기순익": "net_income",
    "자산부채": "changes_in_assets_and_liabilities_from_operating_activities",
    "운전자본": "changes_in_assets_and_liabilities_from_operating_activities",
    "기초자본": "capital_stock",
    "기말자본": "capital_stock",
    "조정전": "retained_earnings",
    "조정후": "retained_earnings",
    "수정후": "retained_earnings",
    "재작성": "retained_earnings",
    "정책변경": "retained_earnings",
    "IFRS": "retained_earnings",
    "소유주": "total_stockholders_equity",
    "자본항목": "other_reserves",
    "관리비": "sga",
    "판매비": "sga",
    "판관비": "sga",
    "복리후생": "sga",
    "인건비": "sga",
    "물류비": "sga",
    "매출": "sales",
    "연결": "gainslosses_in_subsidiaries",
    "예금": "cash_and_cash_equivalents",
    "적립금": "retained_earnings",
    "준비금": "retained_earnings",
    "결손금": "retained_earnings",
    "상환": "decrease_in_longtermborrowings",
    "발행": "bonds",
    "지급": "other_payables",
    "수취": "other_receivables",
    "귀속": "net_income",
    "주주": "total_stockholders_equity",
    "비현금": "addition_of_expenses_of_noncash_transactions",
}

alreadyLearned = set(sl._synonyms.keys())
autoMappings = {}
for acc in allUnmatched:
    if acc in alreadyLearned:
        continue
    for keyword, snakeId in keywordMap.items():
        if keyword in acc and snakeId in sl._snakeToKor:
            autoMappings[acc] = snakeId
            break

print(f"자동매핑 후보: {len(autoMappings)}개")
count = sl.learnBatch(autoMappings)
print(f"학습: {count}개")
print(f"동의어: {sl.synonymCount}")
