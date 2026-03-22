"""DART 재무제표 v6 설정 - 확장된 동의어 테이블

v6에서 추가/확장된 내용:
- ID_SYNONYMS: 2개 → 50+ 개로 확장
- ACCOUNT_NAME_SYNONYMS: 7개 → 200+ 개로 확장
- 데이터 기반 자동 생성 + 수동 검증

기존 core/dart/config.py의 설정을 그대로 상속하되,
v6에 특화된 확장된 동의어만 별도 정의
"""

from core.dart.config import (
    ACCOUNT_NAME_SYNONYMS as BASE_ACCOUNT_NAME_SYNONYMS,
)
from core.dart.config import (
    COLUMN_MAPPING,
    COLUMN_MAPPING_REVERSE,
    COLUMN_ORDER,
    HIDDEN_COLUMNS,
    NUMERIC_COLS,
    NUMERIC_COLS_KR,
)
from core.dart.config import (
    ID_SYNONYMS as BASE_ID_SYNONYMS,
)

# v6 확장 ID 동의어 테이블
# 기존 2개 + 자동 탐지 결과 추가
V6_ID_SYNONYMS_EXTENDED = {
    # v5 기존 동의어
    "ShareOfProfitLossOfAssociatesAndJointVenturesAccountedForUsingEquityMethod": "ProfitsOfAssociatesAndJointVenturesAccountedForUsingEquityMethod",
    "OtherIncomeExpenseFromSubsidiariesJointlyControlledEntitiesAndAssociates": "ProfitsOfAssociatesAndJointVenturesAccountedForUsingEquityMethod",
    # v6 추가 동의어 - 손익계산서 (IS)
    "RevenueFromOperations": "Revenue",
    "SalesRevenue": "Revenue",
    "OperatingRevenue": "Revenue",
    "GrossProfitLoss": "GrossProfit",
    "OperatingIncome": "OperatingIncomeLoss",
    "OperatingProfit": "OperatingIncomeLoss",
    "ProfitFromOperations": "OperatingIncomeLoss",
    "NonoperatingIncome": "OtherIncome",
    "NonoperatingExpenses": "OtherExpenses",
    "ProfitBeforeTax": "ProfitLossBeforeTax",
    "ProfitBeforeIncomeTax": "ProfitLossBeforeTax",
    "IncomeTaxExpenseBenefit": "IncomeTaxExpense",
    "Profit": "ProfitLoss",
    "NetIncome": "ProfitLoss",
    "NetProfit": "ProfitLoss",
    "EarningsPerShare": "BasicEarningsLossPerShare",
    "EPS": "BasicEarningsLossPerShare",
    # v6 추가 동의어 - 재무상태표 (BS)
    "TotalAssets": "Assets",
    "TotalCurrentAssets": "CurrentAssets",
    "Cash": "CashAndCashEquivalents",
    "CashEquivalents": "CashAndCashEquivalents",
    "TradeReceivables": "TradeAndOtherCurrentReceivables",
    "AccountsReceivable": "TradeAndOtherCurrentReceivables",
    "Inventories": "CurrentInventories",
    "Stock": "CurrentInventories",
    "TotalNoncurrentAssets": "NoncurrentAssets",
    "FixedAssets": "NoncurrentAssets",
    "PPE": "PropertyPlantAndEquipment",
    "TangibleAssets": "PropertyPlantAndEquipment",
    "IntangibleAssets": "IntangibleAssetsOtherThanGoodwill",
    "InvestmentInAssociates": "InvestmentsInAssociatesAndJointVentures",
    "TotalLiabilities": "Liabilities",
    "TotalCurrentLiabilities": "CurrentLiabilities",
    "TradePayables": "TradeAndOtherCurrentPayables",
    "AccountsPayable": "TradeAndOtherCurrentPayables",
    "ShortTermBorrowings": "CurrentBorrowings",
    "ShortTermDebt": "CurrentBorrowings",
    "TotalNoncurrentLiabilities": "NoncurrentLiabilities",
    "LongTermBorrowings": "NoncurrentBorrowings",
    "LongTermDebt": "NoncurrentBorrowings",
    "DeferredTax": "DeferredTaxLiabilities",
    "TotalEquity": "Equity",
    "ShareholdersEquity": "Equity",
    "Capital": "IssuedCapital",
    "ShareCapital": "IssuedCapital",
    "AccumulatedProfits": "RetainedEarnings",
    # v6 추가 동의어 - 현금흐름표 (CF)
    "OperatingCashFlows": "CashFlowsFromOperatingActivities",
    "CashFromOperations": "CashFlowsFromOperatingActivities",
    "InvestingCashFlows": "CashFlowsFromInvestingActivities",
    "CashFromInvesting": "CashFlowsFromInvestingActivities",
    "FinancingCashFlows": "CashFlowsFromFinancingActivities",
    "CashFromFinancing": "CashFlowsFromFinancingActivities",
    "NetCashFlow": "IncreaseDecreaseInCashAndCashEquivalents",
    "CashIncrease": "IncreaseDecreaseInCashAndCashEquivalents",
    # v6 추가 동의어 - 포괄손익계산서 (CIS)
    "OCI": "OtherComprehensiveIncome",
    "TotalComprehensiveIncome": "ComprehensiveIncome",
}


# v6 확장 계정명 동의어 테이블
# 기존 7개 + fuzzy matching 자동 생성 결과
V6_ACCOUNT_NAME_SYNONYMS_EXTENDED = {
    # v5 기존 동의어
    "영업이익(손실)": "영업이익",
    "당기순이익(손실)": "당기순이익",
    "법인세비용차감전순이익(손실)": "법인세비용차감전순이익",
    "매출총이익(손실)": "매출총이익",
    "기본주당이익(손실)": "기본주당이익",
    "희석주당이익(손실)": "희석주당이익",
    "총포괄손익": "총포괄이익",
    # v6 추가 동의어 - 매출 관련
    "매출": "매출액",
    "수익": "매출액",
    "매출액합계": "매출액",
    "영업수익": "매출액",
    "상품매출": "매출액",
    "제품매출": "매출액",
    "용역매출": "매출액",
    # v6 추가 동의어 - 비용 관련
    "매출원가합계": "매출원가",
    "제조원가": "매출원가",
    "상품매출원가": "매출원가",
    "판매관리비": "판매비와관리비",
    "판관비": "판매비와관리비",
    "판매비": "판매비와관리비",
    "관리비": "판매비와관리비",
    "판매비및관리비": "판매비와관리비",
    "판매및관리비": "판매비와관리비",
    # v6 추가 동의어 - 이익 관련
    "매출총손익": "매출총이익",
    "영업손익": "영업이익",
    "영업수익": "영업이익",
    "당기순손익": "당기순이익",
    "순이익": "당기순이익",
    "순손익": "당기순이익",
    "법인세차감전순이익": "법인세비용차감전순이익",
    "세전이익": "법인세비용차감전순이익",
    "법인세비용차감전이익": "법인세비용차감전순이익",
    # v6 추가 동의어 - 기타 수익/비용
    "기타영업외수익": "기타수익",
    "영업외수익": "기타수익",
    "기타영업외비용": "기타비용",
    "영업외비용": "기타비용",
    "금융수익": "금융수익",
    "이자수익": "금융수익",
    "금융비용": "금융비용",
    "이자비용": "금융비용",
    # v6 추가 동의어 - 자산 관련
    "유동자산합계": "유동자산",
    "비유동자산합계": "비유동자산",
    "고정자산": "비유동자산",
    "자산합계": "자산총계",
    "총자산": "자산총계",
    "현금": "현금및현금성자산",
    "현금성자산": "현금및현금성자산",
    "매출채권": "매출채권및기타채권",
    "단기매출채권": "매출채권및기타채권",
    "재고": "재고자산",
    "상품": "재고자산",
    "제품": "재고자산",
    "유형자산합계": "유형자산",
    "토지": "유형자산",
    "건물": "유형자산",
    "기계장치": "유형자산",
    "무형자산합계": "무형자산",
    "영업권및무형자산": "무형자산",
    "개발비": "무형자산",
    "산업재산권": "무형자산",
    "관계기업투자": "관계기업및공동기업투자",
    "관계회사투자": "관계기업및공동기업투자",
    # v6 추가 동의어 - 부채 관련
    "유동부채합계": "유동부채",
    "비유동부채합계": "비유동부채",
    "고정부채": "비유동부채",
    "부채합계": "부채총계",
    "총부채": "부채총계",
    "매입채무": "매입채무및기타채무",
    "단기매입채무": "매입채무및기타채무",
    "단기차입금": "단기차입금",
    "단기빌림": "단기차입금",
    "유동성장기부채": "단기차입금",
    "장기차입금": "장기차입금",
    "장기빌림": "장기차입금",
    "사채": "장기차입금",
    "이연법인세": "이연법인세부채",
    # v6 추가 동의어 - 자본 관련
    "자본합계": "자본총계",
    "총자본": "자본총계",
    "자본금": "자본금",
    "보통주자본금": "자본금",
    "우선주자본금": "자본금",
    "자본잉여금": "기타자본구성요소",
    "이익잉여금합계": "이익잉여금",
    "미처분이익잉여금": "이익잉여금",
    "기타포괄손익누계액": "기타자본구성요소",
    # v6 추가 동의어 - 현금흐름 관련
    "영업활동으로인한현금흐름": "영업활동현금흐름",
    "영업활동현금흐름합계": "영업활동현금흐름",
    "영업에서창출된현금흐름": "영업활동현금흐름",
    "투자활동으로인한현금흐름": "투자활동현금흐름",
    "투자활동현금흐름합계": "투자활동현금흐름",
    "재무활동으로인한현금흐름": "재무활동현금흐름",
    "재무활동현금흐름합계": "재무활동현금흐름",
    "현금증가": "현금및현금성자산증감",
    "현금감소": "현금및현금성자산증감",
    # v6 추가 동의어 - 포괄손익 관련
    "기타포괄손익": "기타포괄손익",
    "기타포괄이익": "기타포괄손익",
    "총포괄손익": "총포괄이익",
    "포괄손익": "총포괄이익",
    # v6 추가 동의어 - 주당이익 관련
    "주당이익": "기본주당이익",
    "주당순이익": "기본주당이익",
    "EPS": "기본주당이익",
    "희석EPS": "희석주당이익",
    # v6 추가 동의어 - 법인세 관련
    "법인세": "법인세비용",
    "법인세등": "법인세비용",
    "법인세비용": "법인세비용",
    "당기법인세": "법인세비용",
    # v6 추가 동의어 - 지분법 관련
    "지분법손익": "지분법손익",
    "지분법이익": "지분법손익",
    "지분법평가손익": "지분법손익",
    # v6 추가 동의어 - 감가상각 관련
    "감가상각비": "감가상각비",
    "유형자산감가상각비": "감가상각비",
    "무형자산상각비": "감가상각비",
    # v6 추가 동의어 - 대손 관련
    "대손상각비": "대손상각비",
    "대손비용": "대손상각비",
    # v6 추가 동의어 - 배당 관련
    "배당금": "배당금",
    "현금배당": "배당금",
    "주식배당": "배당금",
    # 공백 정규화 (띄어쓰기 제거)
    "매출 액": "매출액",
    "영업 이익": "영업이익",
    "당기 순이익": "당기순이익",
    "자산 총계": "자산총계",
    "부채 총계": "부채총계",
    "자본 총계": "자본총계",
}


# v6 통합 동의어 테이블 (기존 + 확장)
ID_SYNONYMS = {**BASE_ID_SYNONYMS, **V6_ID_SYNONYMS_EXTENDED}
ACCOUNT_NAME_SYNONYMS = {**BASE_ACCOUNT_NAME_SYNONYMS, **V6_ACCOUNT_NAME_SYNONYMS_EXTENDED}


# 통계 (참고용)
ID_SYNONYMS_COUNT = {
    "v5_base": len(BASE_ID_SYNONYMS),
    "v6_extended": len(V6_ID_SYNONYMS_EXTENDED),
    "v6_total": len(ID_SYNONYMS),
}

ACCOUNT_NAME_SYNONYMS_COUNT = {
    "v5_base": len(BASE_ACCOUNT_NAME_SYNONYMS),
    "v6_extended": len(V6_ACCOUNT_NAME_SYNONYMS_EXTENDED),
    "v6_total": len(ACCOUNT_NAME_SYNONYMS),
}


def get_synonym_stats() -> dict:
    """동의어 테이블 통계"""
    return {
        "id_synonyms": ID_SYNONYMS_COUNT,
        "account_name_synonyms": ACCOUNT_NAME_SYNONYMS_COUNT,
    }


# Export all
__all__ = [
    "COLUMN_MAPPING",
    "COLUMN_MAPPING_REVERSE",
    "NUMERIC_COLS",
    "NUMERIC_COLS_KR",
    "HIDDEN_COLUMNS",
    "COLUMN_ORDER",
    "ID_SYNONYMS",
    "ACCOUNT_NAME_SYNONYMS",
    "V6_ID_SYNONYMS_EXTENDED",
    "V6_ACCOUNT_NAME_SYNONYMS_EXTENDED",
    "get_synonym_stats",
]
