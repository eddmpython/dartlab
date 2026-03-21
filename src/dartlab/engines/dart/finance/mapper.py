"""계정명 → snakeId 매핑.

eddmpython v6+v8 매핑 파이프라인:
1. account_id prefix 제거 → normalizedId
2. ID_SYNONYMS 로 영문 ID 동의어 통합
3. ACCOUNT_NAME_SYNONYMS 로 한글명 동의어 통합
4. accountMappings.json 조회 (한글명 우선 → 영문ID)
5. 공백 제거 후 재조회
6. 괄호+공백 제거 후 재조회
7. 미매핑 → None

snakeId는 standardAccounts.json에 정의된 것을 그대로 사용.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from dartlab.engines.common.finance.ordering import levelMap as _commonLevelMap
from dartlab.engines.common.finance.ordering import sortOrder as _commonSortOrder

_DATA_DIR = Path(__file__).parent / "mapperData"

_PREFIX_RE = re.compile(r"^(?:ifrs-full_|ifrs_|dart_|ifrs-smes_)")
_PAREN_RE = re.compile(r"\([^)]*\)")

ID_SYNONYMS: dict[str, str] = {
    "ShareOfProfitLossOfAssociatesAndJointVenturesAccountedForUsingEquityMethod": "ProfitsOfAssociatesAndJointVenturesAccountedForUsingEquityMethod",
    "OtherIncomeExpenseFromSubsidiariesJointlyControlledEntitiesAndAssociates": "ProfitsOfAssociatesAndJointVenturesAccountedForUsingEquityMethod",
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
    "OperatingCashFlows": "CashFlowsFromOperatingActivities",
    "CashFromOperations": "CashFlowsFromOperatingActivities",
    "InvestingCashFlows": "CashFlowsFromInvestingActivities",
    "CashFromInvesting": "CashFlowsFromInvestingActivities",
    "FinancingCashFlows": "CashFlowsFromFinancingActivities",
    "CashFromFinancing": "CashFlowsFromFinancingActivities",
    "NetCashFlow": "IncreaseDecreaseInCashAndCashEquivalents",
    "CashIncrease": "IncreaseDecreaseInCashAndCashEquivalents",
    "OCI": "OtherComprehensiveIncome",
    "TotalComprehensiveIncome": "ComprehensiveIncome",
}

ACCOUNT_NAME_SYNONYMS: dict[str, str] = {
    "영업이익(손실)": "영업이익",
    "당기순이익(손실)": "당기순이익",
    "법인세비용차감전순이익(손실)": "법인세비용차감전순이익",
    "매출총이익(손실)": "매출총이익",
    "기본주당이익(손실)": "기본주당이익",
    "희석주당이익(손실)": "희석주당이익",
    "총포괄손익": "총포괄이익",
    "매출": "매출액",
    "수익": "매출액",
    "매출액합계": "매출액",
    "영업수익": "매출액",
    "상품매출": "매출액",
    "제품매출": "매출액",
    "용역매출": "매출액",
    "매출원가합계": "매출원가",
    "제조원가": "매출원가",
    "상품매출원가": "매출원가",
    "판매관리비": "판매비와관리비",
    "판관비": "판매비와관리비",
    "판매비": "판매비와관리비",
    "관리비": "판매비와관리비",
    "판매비및관리비": "판매비와관리비",
    "판매및관리비": "판매비와관리비",
    "매출총손익": "매출총이익",
    "영업손익": "영업이익",
    "당기순손익": "당기순이익",
    "순이익": "당기순이익",
    "순손익": "당기순이익",
    "법인세차감전순이익": "법인세비용차감전순이익",
    "세전이익": "법인세비용차감전순이익",
    "법인세비용차감전이익": "법인세비용차감전순이익",
    "기타영업외수익": "기타수익",
    "영업외수익": "기타수익",
    "기타영업외비용": "기타비용",
    "영업외비용": "기타비용",
    "이자수익": "금융수익",
    "이자비용": "금융비용",
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
    "무형자산합계": "무형자산",
    "영업권및무형자산": "무형자산",
    "관계기업투자": "관계기업및공동기업투자",
    "관계회사투자": "관계기업및공동기업투자",
    "유동부채합계": "유동부채",
    "비유동부채합계": "비유동부채",
    "고정부채": "비유동부채",
    "부채합계": "부채총계",
    "총부채": "부채총계",
    "매입채무": "매입채무및기타채무",
    "단기매입채무": "매입채무및기타채무",
    "단기빌림": "단기차입금",
    "유동성장기부채": "단기차입금",
    "장기빌림": "장기차입금",
    "이연법인세": "이연법인세부채",
    "자본합계": "자본총계",
    "총자본": "자본총계",
    "보통주자본금": "자본금",
    "우선주자본금": "자본금",
    "이익잉여금합계": "이익잉여금",
    "미처분이익잉여금": "이익잉여금",
    "기타포괄손익누계액": "기타자본구성요소",
    "영업활동으로인한현금흐름": "영업활동현금흐름",
    "영업활동현금흐름합계": "영업활동현금흐름",
    "영업에서창출된현금흐름": "영업활동현금흐름",
    "투자활동으로인한현금흐름": "투자활동현금흐름",
    "투자활동현금흐름합계": "투자활동현금흐름",
    "재무활동으로인한현금흐름": "재무활동현금흐름",
    "재무활동현금흐름합계": "재무활동현금흐름",
    "현금증가": "현금및현금성자산증감",
    "현금감소": "현금및현금성자산증감",
    "기타포괄이익": "기타포괄손익",
    "포괄손익": "총포괄이익",
    "주당이익": "기본주당이익",
    "주당순이익": "기본주당이익",
    "EPS": "기본주당이익",
    "희석EPS": "희석주당이익",
    "법인세": "법인세비용",
    "법인세등": "법인세비용",
    "당기법인세": "법인세비용",
    "지분법이익": "지분법손익",
    "지분법평가손익": "지분법손익",
    "유형자산감가상각비": "감가상각비",
    "무형자산상각비": "감가상각비",
    "대손비용": "대손상각비",
    "현금배당": "배당금",
    "주식배당": "배당금",
    "매출 액": "매출액",
    "영업 이익": "영업이익",
    "당기 순이익": "당기순이익",
    "자산 총계": "자산총계",
    "부채 총계": "부채총계",
    "자본 총계": "자본총계",
}


def _stripPrefix(accountId: str) -> str:
    return _PREFIX_RE.sub("", accountId)


class AccountMapper:
    """계정명 매핑기 (eddmpython v6+v8 파이프라인).

    v6: account_id prefix 제거 + ID_SYNONYMS/ACCOUNT_NAME_SYNONYMS 정규화
    v8: 정규화된 한글명/영문ID → accountMappings.json → standardAccounts snakeId
    """

    _instance: Optional[AccountMapper] = None
    _mappings: Optional[dict[str, str]] = None
    _stdAccountsRaw: Optional[dict[str, dict]] = None
    _noHyphenIndex: Optional[dict[str, str]] = None  # lazy 빌드

    @classmethod
    def get(cls) -> AccountMapper:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def release(cls) -> None:
        """메모리 해제. 다음 get() 호출 시 자동 재로드."""
        cls._instance = None
        cls._mappings = None
        cls._stdAccountsRaw = None
        cls._noHyphenIndex = None

    def __init__(self):
        if AccountMapper._mappings is None:
            path = _DATA_DIR / "accountMappings.json"
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            AccountMapper._mappings = data["mappings"]
            AccountMapper._stdAccountsRaw = data.get("standardAccounts", {})

    @property
    def _stdAccounts(self) -> dict[str, dict]:
        if AccountMapper._stdAccountsRaw is None:
            return {}
        return AccountMapper._stdAccountsRaw

    def _getNoHyphenIndex(self) -> dict[str, str]:
        """하이픈 제거 역인덱스 — 첫 접근 시 lazy 빌드."""
        if AccountMapper._noHyphenIndex is None:
            idx: dict[str, str] = {}
            for key, snakeId in self._mappings.items():
                stripped = key.replace("-", "").replace("–", "").replace("—", "")
                if stripped != key and stripped not in self._mappings:
                    idx[stripped] = snakeId
            AccountMapper._noHyphenIndex = idx
        return AccountMapper._noHyphenIndex

    def map(self, accountId: str, accountNm: str) -> Optional[str]:
        """account_id + account_nm → snakeId.

        v8 방식: 한글명 우선 조회 → 영문ID 조회 → 공백제거 → 괄호제거 fallback.
        accountMappings.json의 snakeId(= standardAccounts 기준)를 그대로 반환.

        Returns:
                snakeId 또는 None (미매핑).
        """
        stripped = _stripPrefix(accountId) if accountId else ""
        normalizedId = ID_SYNONYMS.get(stripped, stripped)

        normalizedNm = ACCOUNT_NAME_SYNONYMS.get(accountNm, accountNm) if accountNm else ""

        if normalizedNm and normalizedNm in self._mappings:
            return self._mappings[normalizedNm]

        if normalizedId and normalizedId in self._mappings:
            return self._mappings[normalizedId]

        if normalizedNm:
            noSpace = normalizedNm.replace(" ", "")
            if noSpace != normalizedNm and noSpace in self._mappings:
                return self._mappings[noSpace]

            noParen = _PAREN_RE.sub("", noSpace)
            if noParen != noSpace and noParen in self._mappings:
                return self._mappings[noParen]

            # 하이픈/대시 정규화 fallback (실험 081-001: 미매핑 98.5%가 하이픈 차이)
            # 양방향: 입력에서 하이픈 제거 → 사전 조회, 사전에서 하이픈 제거 → 역인덱스 조회
            noHyphen = noSpace.replace("-", "").replace("–", "").replace("—", "")
            if noHyphen in self._mappings:
                return self._mappings[noHyphen]
            nhIdx = self._getNoHyphenIndex()
            if noHyphen in nhIdx:
                return nhIdx[noHyphen]

        return None

    def labelMap(self) -> dict[str, str]:
        """snakeId → 대표 한글명 매핑 (캐싱).

        우선순위:
        1. standardAccounts의 korName (정본)
        2. accountMappings.json에서 한글명 중 가장 짧은 것
        """
        if hasattr(self, "_labelMap"):
            return self._labelMap

        result: dict[str, str] = {}

        if self._stdAccounts:
            for snakeId, meta in self._stdAccounts.items():
                result[snakeId] = meta["korName"]

        if self._mappings:
            reverse: dict[str, list[str]] = {}
            for name, snakeId in self._mappings.items():
                if any("\uac00" <= ch <= "\ud7a3" for ch in name):
                    reverse.setdefault(snakeId, []).append(name)
            for snakeId, names in reverse.items():
                if snakeId not in result:
                    result[snakeId] = min(names, key=len)

        self._labelMap = result
        return result

    def sortOrder(self, sjDiv: str) -> dict[str, int]:
        """sj_div별 snakeId → 표시 순서 (common/finance/ordering 위임)."""
        return _commonSortOrder(sjDiv)

    def levelMap(self, sjDiv: str) -> dict[str, int]:
        """sj_div별 snakeId → 들여쓰기 레벨 (common/finance/ordering 위임)."""
        return _commonLevelMap(sjDiv)
