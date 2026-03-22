"""EDINET XBRL element → DART canonical snakeId 매핑.

매핑 파이프라인 (DART 7단계 패턴):
1. prefix 제거 (jpcrp_, jppfs_, jpigp_, jpdei_, ifrs-full_, jpcrp_cor: 등)
2. ID_SYNONYMS (영문 XBRL element 동의어 통합)
3. ACCOUNT_NAME_SYNONYMS (일본어 계정명 동의어 통합)
4. CORE_MAP (핵심 계정 오버라이드, DART/EDGAR 공유 snakeId)
5. accountMappings.json (학습 결과 누적)
6. 전각/공백 정규화 후 재조회
7. 미매핑 → None

데이터 출처:
- edinet-mcp taxonomy.yaml (161 fields, 233 element variants)
  https://github.com/ajtgjmdjp/edinet-mcp
- DART/EDGAR 기존 snakeId 체계
- 실험 002 (DART↔EDINET 매핑 분석)
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Optional

_DATA_DIR = Path(__file__).parent / "mapperData"

# ── 1. Prefix 제거 ──

_PREFIXES = (
    "jpcrp_cor:",
    "jppfs_cor:",
    "jpigp_cor:",
    "jpdei_cor:",
    "jpcrp-esr_cor:",
    "jpcrp-sbr_cor:",
    "jpctl_cor:",
    "jplvh_cor:",
    "jpcrp_",
    "jppfs_",
    "jpigp_",
    "jpdei_",
    "ifrs-full_",
    "ifrs-full:",
    "ifrs_",
    "us-gaap_",
    "us-gaap:",
    "jpmfs_",
    "jpbps_",
)


def _removePrefix(elementId: str) -> str:
    lower = elementId.lower()
    for prefix in _PREFIXES:
        if lower.startswith(prefix):
            return elementId[len(prefix) :]
    return elementId


# ── 2. ID_SYNONYMS (영문 XBRL element 동의어 → 정규화) ──
# edinet-mcp taxonomy.yaml 기반 — 3중 회계기준(J-GAAP/IFRS/US-GAAP) 변형 통합

ID_SYNONYMS: dict[str, str] = {
    # ─ Revenue ─
    "Revenues": "Revenue",
    "NetSales": "Revenue",
    "SalesRevenueNet": "Revenue",
    "SalesRevenues": "Revenue",
    "TotalNetRevenues": "Revenue",
    "OperatingRevenues": "Revenue",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "Revenue",
    "NetSalesAndOperatingRevenue": "Revenue",
    # ─ Operating Income ─
    "OperatingIncomeLoss": "OperatingIncome",
    "OperatingProfit": "OperatingIncome",
    "OperatingProfitLoss": "OperatingIncome",
    # ─ Net Income ─
    "NetIncomeLoss": "ProfitLoss",
    "ProfitForThePeriod": "ProfitLoss",
    # ─ Net Income (Parent) ─
    "ProfitLossAttributableToOwnersOfParent": "NetIncomeParent",
    "ProfitAttributableToOwnersOfParent": "NetIncomeParent",
    # ─ Net Income (Non-controlling) ─
    "ProfitLossAttributableToNonControllingInterests": "NetIncomeMinority",
    # ─ Income Before Tax ─
    "IncomeBeforeIncomeTaxes": "IncomeBeforeTax",
    "ProfitBeforeTax": "IncomeBeforeTax",
    "ProfitLossBeforeTax": "IncomeBeforeTax",
    # ─ Income Taxes ─
    "IncomeTaxExpense": "IncomeTaxes",
    # ─ Deferred Income Tax ─
    "IncomeTaxesDeferred": "DeferredIncomeTax",
    "DeferredIncomeTaxExpense": "DeferredIncomeTax",
    # ─ Depreciation ─
    "DepreciationAndAmortization": "Depreciation",
    "DepreciationAndAmortizationOperatingExpenses": "Depreciation",
    # ─ EPS ─
    "BasicEarningsPerShare": "BasicEPS",
    "BasicEarningsLossPerShare": "BasicEPS",
    "DilutedEarningsPerShare": "DilutedEPS",
    "DilutedEarningsLossPerShare": "DilutedEPS",
    # ─ Equity in Earnings ─
    "ShareOfProfitLossOfInvestmentsAccountedForUsingEquityMethod": "EquityInEarnings",
    "EquityInEarningsOfAffiliates": "EquityInEarnings",
    # ─ Fixed Asset Gains/Losses ─
    "GainOnSaleOfPropertyPlantAndEquipment": "GainOnSaleOfFixedAssets",
    "GainOnSaleOfNoncurrentAssets": "GainOnSaleOfFixedAssets",
    "LossOnSaleOfPropertyPlantAndEquipment": "LossOnSaleOfFixedAssets",
    "LossOnSaleOfNoncurrentAssets": "LossOnSaleOfFixedAssets",
    "LossOnDisposalOfPropertyPlantAndEquipment": "LossOnDisposalOfFixedAssets",
    "LossOnRetirementOfNoncurrentAssets": "LossOnDisposalOfFixedAssets",
    # ─ Total Assets ─
    "Assets": "TotalAssets",
    # ─ PPE ─
    "PropertyPlantAndEquipment": "PPE",
    "PropertyPlantAndEquipmentNet": "PPE",
    # ─ Buildings ─
    "BuildingsNet": "Buildings",
    # ─ Structures ─
    "StructuresNet": "Structures",
    # ─ Machinery ─
    "MachineryAndEquipment": "Machinery",
    "MachineryEquipmentAndVehicles": "Machinery",
    "MachineryAndEquipmentNet": "Machinery",
    # ─ Vehicles ─
    "VehiclesNet": "Vehicles",
    # ─ Tools/Furniture ─
    "ToolsFurnitureAndFixtures": "ToolsFurnitureFixtures",
    "ToolsFurnitureAndFixturesNet": "ToolsFurnitureFixtures",
    # ─ Leased Assets / Right of Use ─
    "RightOfUseAssets": "LeasedAssets",
    # ─ Cash ─
    "CashAndCashEquivalents": "CashAndEquivalents",
    "CashAndDeposits": "CashAndDeposits",
    # ─ Receivables ─
    "NotesAndAccountsReceivableTrade": "TradeReceivables",
    "AccountsReceivableTrade": "AccountsReceivable",
    "TradeReceivables": "AccountsReceivable",
    # ─ Payables ─
    "NotesAndAccountsPayableTrade": "TradePayables",
    "AccountsPayableTrade": "AccountsPayable",
    "TradePayables": "AccountsPayable",
    # ─ Inventories ─
    "MerchandiseAndFinishedGoods": "Inventories",
    # ─ Raw Materials ─
    "RawMaterialsAndSupplies": "RawMaterials",
    # ─ Investment Securities ─
    "InvestmentSecurities": "InvestmentSecurities",
    # ─ Affiliates ─
    "InvestmentsInAffiliates": "InvestmentsInAffiliates",
    "SharesOfSubsidiariesAndAffiliates": "InvestmentsInAffiliates",
    # ─ Guarantee Deposits ─
    "SecurityDeposits": "GuaranteeDeposits",
    # ─ Retirement Benefit Asset ─
    "RetirementBenefitAsset": "RetirementBenefitAsset",
    "NetDefinedBenefitAsset": "RetirementBenefitAsset",
    # ─ Provision for Bonuses ─
    "AccruedBonuses": "ProvisionForBonuses",
    # ─ Accounts Payable Other ─
    "OtherAccountsPayable": "AccountsPayableOther",
    # ─ Advances Received ─
    "ContractLiabilities": "AdvancesReceived",
    # ─ Retirement Benefit Liability ─
    "ProvisionForRetirementBenefits": "RetirementBenefitLiability",
    # ─ Asset Retirement Obligations ─
    "ProvisionForAssetRetirementObligations": "AssetRetirementObligations",
    # ─ Provisions Noncurrent ─
    "ProvisionForLoss": "ProvisionsNoncurrent",
    # ─ Total Equity variants ─
    "NetAssets": "TotalEquity",
    "Equity": "TotalEquity",
    "TotalEquity": "TotalEquity",
    "StockholdersEquity": "TotalEquity",
    # ─ Equity Parent ─
    "EquityAttributableToOwnersOfParent": "EquityParent",
    # ─ Total L&E ─
    "LiabilitiesAndEquity": "TotalLiabilitiesAndNetAssets",
    # ─ Total Liabilities ─
    "Liabilities": "TotalLiabilities",
    # ─ AOCI detail ─
    "NetUnrealizedGainsLossesOnAvailableForSaleSecurities": "ValuationDifferenceSecurities",
    "NetDeferredGainsLossesOnHedges": "DeferredHedgeGainsLosses",
    # ─ Subscription Rights ─
    "StockAcquisitionRights": "SubscriptionRightsToShares",
    # ─ Ordinary Income (J-GAAP 고유) ─
    "OrdinaryIncomeLoss": "OrdinaryIncome",
    "OrdinaryIncome": "OrdinaryIncome",
    # ─ Extraordinary (J-GAAP 고유) ─
    "ExtraordinaryIncome": "ExtraordinaryIncome",
    "ExtraordinaryLoss": "ExtraordinaryLoss",
    # ─ Cash Flow ─
    "CashFlowsFromOperatingActivities": "OperatingCF",
    "CashFlowsFromUsedInOperatingActivities": "OperatingCF",
    "NetCashProvidedByUsedInOperatingActivities": "OperatingCF",
    "CashFlowsFromInvestingActivities": "InvestingCF",
    "CashFlowsFromUsedInInvestingActivities": "InvestingCF",
    "NetCashProvidedByUsedInInvestingActivities": "InvestingCF",
    "CashFlowsFromFinancingActivities": "FinancingCF",
    "CashFlowsFromUsedInFinancingActivities": "FinancingCF",
    "NetCashProvidedByUsedInFinancingActivities": "FinancingCF",
    # ─ FX Effect on Cash ─
    "EffectOfExchangeRateChangeOnCashAndCashEquivalents": "FxEffectOnCash",
    "EffectOfExchangeRateChangesOnCashAndCashEquivalents": "FxEffectOnCash",
    # ─ Cash at End ─
    "CashAndCashEquivalentsAtEndOfPeriod": "CashEnd",
    # ─ CF detail synonyms ─
    "DepreciationAndAmortizationOpeCF": "DepreciationCF",
    "ImpairmentLossOpeCF": "ImpairmentLossCF",
    "AmortizationOfGoodwillOpeCF": "AmortizationOfGoodwillCF",
    "ShareOfProfitLossOfInvestmentsAccountedForUsingEquityMethodOpeCF": "EquityInEarningsCF",
    "DividendsReceivedInvCF": "DividendsReceivedCF",
    "DividendsReceivedOpeCF": "DividendsReceivedCF",
    "IncreaseDecreaseInRetirementBenefitLiability": "ChangeInRetirementBenefitLiability",
    "IncreaseDecreaseInNetDefinedBenefitLiability": "ChangeInRetirementBenefitLiability",
    "InterestExpensesPaid": "InterestPaid",
    "PurchaseOfSharesOfSubsidiaries": "PurchaseOfSubsidiariesStock",
    "PurchaseOfSharesOfSubsidiariesAndAffiliates": "PurchaseOfSubsidiariesStock",
    "ProceedsFromSaleOfSharesOfSubsidiaries": "ProceedsFromSaleOfSubsidiariesStock",
    "ProceedsFromSaleOfSharesOfSubsidiariesAndAffiliates": "ProceedsFromSaleOfSubsidiariesStock",
    "ProceedsFromCollectionOfLoansReceivable": "CollectionOfLoansReceivable",
    "ProceedsFromLongTermLoansPayable": "ProceedsFromBorrowings",
    "ProceedsFromShortTermLoansPayable": "ProceedsFromBorrowings",
    "RepaymentsOfLongTermLoansPayable": "RepaymentOfBorrowings",
    "RepaymentsOfShortTermLoansPayable": "RepaymentOfBorrowings",
    "RepaymentsOfLeaseLiabilities": "RepaymentOfLeaseLiabilities",
}

# ── 3. ACCOUNT_NAME_SYNONYMS (일본어 계정명 동의어) ──

ACCOUNT_NAME_SYNONYMS: dict[str, str] = {
    # ── IS ──
    # 매출
    "売上高": "売上高",
    "営業収益": "売上高",
    "売上収益": "売上高",
    "経常収益": "売上高",
    "事業収益": "売上高",
    # 매출원가
    "売上原価": "売上原価",
    # 매출총이익
    "売上総利益": "売上総利益",
    # 판관비
    "販売費及び一般管理費": "販売費及び一般管理費",
    "販売費及び一般管理費合計": "販売費及び一般管理費",
    # 영업이익
    "営業利益": "営業利益",
    "営業利益又は営業損失": "営業利益",
    "営業利益（△は営業損失）": "営業利益",
    # 영업외수익/비용
    "営業外収益": "営業外収益",
    "営業外費用": "営業外費用",
    # 경상이익 (J-GAAP 고유)
    "経常利益": "経常利益",
    "経常利益又は経常損失": "経常利益",
    "経常利益（△は経常損失）": "経常利益",
    # 특별이익/손실
    "特別利益": "特別利益",
    "特別損失": "特別損失",
    # 세전이익
    "税引前当期純利益": "税引前当期純利益",
    "税金等調整前当期純利益": "税引前当期純利益",
    # 법인세
    "法人税等": "法人税等",
    "法人税、住民税及び事業税": "法人税等",
    "法人税等合計": "法人税等",
    "法人税等調整額": "法人税等調整額",
    # 당기순이익
    "当期純利益": "当期純利益",
    "当期純利益又は当期純損失": "当期純利益",
    "親会社株主に帰属する当期純利益": "親会社帰属当期純利益",
    "親会社株主に帰属する当期純利益又は親会社株主に帰属する当期純損失": "親会社帰属当期純利益",
    "非支配株主に帰属する当期純利益": "非支配株主帰属当期純利益",
    # 포괄이익
    "包括利益": "包括利益",
    "その他の包括利益合計額": "その他の包括利益",
    # 감가상각비
    "減価償却費": "減価償却費",
    # 감손
    "減損損失": "減損損失",
    # 연구개발비
    "研究開発費": "研究開発費",
    # 지분법
    "持分法による投資損益": "持分法による投資損益",
    "持分法による投資利益": "持分法による投資損益",
    # EPS
    "１株当たり当期純利益": "1株当たり当期純利益",
    "1株当たり当期純利益": "1株当たり当期純利益",
    "潜在株式調整後１株当たり当期純利益": "希薄化後1株当たり当期純利益",
    "潜在株式調整後1株当たり当期純利益": "希薄化後1株当たり当期純利益",
    # BPS
    "１株当たり純資産額": "1株当たり純資産",
    "1株当たり純資産額": "1株当たり純資産",
    # 배당
    "１株当たり配当額": "1株当たり配当額",
    "1株当たり配当額": "1株当たり配当額",
    # 이자수익/비용
    "受取利息": "受取利息",
    "受取配当金": "受取配当金",
    "支払利息": "支払利息",
    # 환차손익
    "為替差益": "為替差益",
    "為替差損": "為替差損",
    # 고정자산 처분손익
    "固定資産売却益": "固定資産売却益",
    "固定資産売却損": "固定資産売却損",
    "固定資産除却損": "固定資産除却損",
    # SGA 내역
    "人件費": "人件費",
    "広告宣伝費": "広告宣伝費",
    "地代家賃": "地代家賃",
    "旅費交通費": "旅費交通費",
    "通信費": "通信費",
    "水道光熱費": "水道光熱費",
    "消耗品費": "消耗品費",
    # 퇴직급여
    "退職給付費用": "退職給付費用",
    # 기타수익/비용
    "その他の収益": "その他の収益",
    "その他の費用": "その他の費用",
    # のれん상각
    "のれん償却額": "のれん償却額",
    # ── BS ──
    # 유동자산/부채
    "流動資産": "流動資産",
    "流動資産合計": "流動資産",
    "流動負債": "流動負債",
    "流動負債合計": "流動負債",
    "固定資産": "固定資産",
    "固定資産合計": "固定資産",
    "固定負債": "固定負債",
    "固定負債合計": "固定負債",
    # 총자산
    "総資産額": "総資産",
    "資産合計": "総資産",
    "資産の部合計": "総資産",
    # 순자산
    "純資産額": "純資産",
    "純資産合計": "純資産",
    "純資産の部合計": "純資産",
    # 부채합계
    "負債合計": "負債合計",
    "負債の部合計": "負債合計",
    # 부채순자산합계
    "負債純資産合計": "負債純資産合計",
    "負債及び純資産合計": "負債純資産合計",
    # 현금
    "現金及び預金": "現金及び預金",
    "現金及び現金同等物": "現金及び現金同等物",
    # 매출채권
    "売掛金": "売掛金",
    "受取手形及び売掛金": "受取手形及び売掛金",
    # 매입채무
    "買掛金": "買掛金",
    "支払手形及び買掛金": "支払手形及び買掛金",
    # 재고
    "棚卸資産": "棚卸資産",
    "たな卸資産": "棚卸資産",
    "商品": "商品",
    "製品": "製品",
    "仕掛品": "仕掛品",
    "原材料": "原材料",
    "原材料及び貯蔵品": "原材料",
    "貯蔵品": "貯蔵品",
    # 유가증권
    "有価証券": "有価証券",
    # 전도금/선급비용
    "前払費用": "前払費用",
    "仮払金": "仮払金",
    # 대손충당금
    "貸倒引当金": "貸倒引当金",
    # 유형자산
    "有形固定資産": "有形固定資産",
    "有形固定資産合計": "有形固定資産",
    # PPE 내역
    "建物": "建物",
    "建物及び構築物": "建物",
    "構築物": "構築物",
    "機械装置": "機械装置",
    "機械装置及び運搬具": "機械装置",
    "車両運搬具": "車両運搬具",
    "工具器具備品": "工具器具備品",
    "工具、器具及び備品": "工具器具備品",
    "土地": "土地",
    "建設仮勘定": "建設仮勘定",
    "リース資産": "リース資産",
    "使用権資産": "リース資産",
    # 무형자산
    "無形固定資産": "無形固定資産",
    "無形固定資産合計": "無形固定資産",
    "のれん": "のれん",
    "ソフトウェア": "ソフトウェア",
    "特許権": "特許権",
    "商標権": "商標権",
    # 투자 기타 자산
    "投資その他の資産": "投資その他の資産",
    "投資有価証券": "投資有価証券",
    "関係会社株式": "関係会社株式",
    "敷金及び保証金": "敷金及び保証金",
    "長期貸付金": "長期貸付金",
    "長期前払費用": "長期前払費用",
    "繰延税金資産": "繰延税金資産",
    "退職給付に係る資産": "退職給付に係る資産",
    "投資不動産": "投資不動産",
    "契約資産": "契約資産",
    # 자기자본
    "自己資本": "自己資本",
    "株主資本合計": "自己資本",
    "株主資本": "株主資本",
    # 자본금
    "資本金": "資本金",
    # 자본잉여금
    "資本剰余金": "資本剰余金",
    # 이익잉여금
    "利益剰余金": "利益剰余金",
    "利益剰余金合計": "利益剰余金",
    # 자기주식
    "自己株式": "自己株式",
    # AOCI
    "その他の包括利益累計額": "その他の包括利益累計額",
    "その他有価証券評価差額金": "その他有価証券評価差額金",
    "為替換算調整勘定": "為替換算調整勘定",
    "退職給付に係る調整累計額": "退職給付に係る調整累計額",
    "繰延ヘッジ損益": "繰延ヘッジ損益",
    # 신주예약권
    "新株予約権": "新株予約権",
    # 비지배지분
    "非支配株主持分": "非支配株主持分",
    "少数株主持分": "非支配株主持分",
    # 친회사 귀속 지분
    "親会社の所有者に帰属する持分": "親会社の所有者に帰属する持分",
    # 차입금
    "短期借入金": "短期借入金",
    "長期借入金": "長期借入金",
    "社債": "社債",
    # 미지급비용
    "未払費用": "未払費用",
    "未払法人税等": "未払法人税等",
    "未払金": "未払金",
    # 충당금
    "賞与引当金": "賞与引当金",
    "1年内返済予定の長期借入金": "1年内返済予定の長期借入金",
    "前受金": "前受金",
    "仮受金": "仮受金",
    "退職給付引当金": "退職給付引当金",
    "退職給付に係る負債": "退職給付引当金",
    "リース債務": "リース債務",
    "資産除去債務": "資産除去債務",
    "繰延税金負債": "繰延税金負債",
    # ── CF ──
    "営業活動によるキャッシュ・フロー": "営業CF",
    "投資活動によるキャッシュ・フロー": "投資CF",
    "財務活動によるキャッシュ・フロー": "財務CF",
    "現金及び現金同等物に係る換算差額": "為替換算差額CF",
    "現金及び現金同等物の増減額": "現金増減額",
    "現金及び現金同等物の期首残高": "現金期首残高",
    "現金及び現金同等物の期末残高": "現金期末残高",
    # CF 내역
    "貸倒引当金の増減額": "貸倒引当金の増減額",
    "配当金の受取額": "配当金の受取額",
    "退職給付に係る負債の増減額": "退職給付に係る負債の増減額",
    "引当金の増減額": "引当金の増減額",
    "売上債権の増減額": "売上債権の増減額",
    "棚卸資産の増減額": "棚卸資産の増減額",
    "仕入債務の増減額": "仕入債務の増減額",
    "利息及び配当金の受取額": "利息及び配当金の受取額",
    "利息の支払額": "利息の支払額",
    "法人税等の支払額": "法人税等の支払額",
    "有形固定資産の取得による支出": "有形固定資産の取得による支出",
    "有形固定資産の売却による収入": "有形固定資産の売却による収入",
    "投資有価証券の取得による支出": "投資有価証券の取得による支出",
    "投資有価証券の売却による収入": "投資有価証券の売却による収入",
    "子会社株式の取得による支出": "子会社株式の取得による支出",
    "子会社株式の売却による収入": "子会社株式の売却による収入",
    "貸付けによる支出": "貸付けによる支出",
    "貸付金の回収による収入": "貸付金の回収による収入",
    "連結の範囲の変更を伴う子会社株式の取得による支出": "連結範囲変更子会社取得支出",
    "借入れによる収入": "借入れによる収入",
    "借入金の返済による支出": "借入金の返済による支出",
    "社債の発行による収入": "社債発行収入",
    "社債の償還による支出": "社債償還支出",
    "配当金の支払額": "配当金の支払額",
    "無形固定資産の取得による支出": "無形固定資産の取得による支出",
    "リース債務の返済による支出": "リース債務の返済による支出",
    "短期借入金の純増減額": "短期借入金の純増減額",
    "株式の発行による収入": "株式発行収入",
    "自己株式の取得による支出": "自己株式の取得による支出",
}

# ── 4. CORE_MAP (핵심 계정 → snakeId 오버라이드) ──
# edinet-mcp taxonomy.yaml 161개 필드 전량 반영
# DART/EDGAR 기존 snakeId와 최대한 일치

CORE_MAP: dict[str, str] = {
    # ═══════════════════════════════════════════
    # IS — Income Statement (42개)
    # ═══════════════════════════════════════════
    # 매출
    "売上高": "revenue",
    "Revenue": "revenue",
    # 매출원가
    "売上原価": "cost_of_sales",
    "CostOfSales": "cost_of_sales",
    # 매출총이익
    "売上総利益": "gross_profit",
    "GrossProfit": "gross_profit",
    # 판관비
    "販売費及び一般管理費": "selling_and_administrative_expenses",
    "SellingGeneralAndAdministrativeExpenses": "selling_and_administrative_expenses",
    # SGA 내역
    "人件費": "personnel_expenses",
    "PersonnelExpenses": "personnel_expenses",
    "SalariesAndWages": "personnel_expenses",
    "広告宣伝費": "advertising_expenses",
    "AdvertisingExpenses": "advertising_expenses",
    "地代家賃": "rent_expenses",
    "RentExpenses": "rent_expenses",
    "旅費交通費": "travel_expenses",
    "TravelAndTransportationExpenses": "travel_expenses",
    "通信費": "communication_expenses",
    "CommunicationExpenses": "communication_expenses",
    "水道光熱費": "utilities_expenses",
    "UtilitiesExpenses": "utilities_expenses",
    "消耗品費": "supplies_expenses",
    "SuppliesExpenses": "supplies_expenses",
    # 영업이익
    "営業利益": "operating_profit",
    "OperatingIncome": "operating_profit",
    # 영업외수익/비용
    "営業外収益": "non_operating_income",
    "NonOperatingIncome": "non_operating_income",
    "営業外費用": "non_operating_expenses",
    "NonOperatingExpenses": "non_operating_expenses",
    # 이자수익/비용
    "受取利息": "interest_income",
    "InterestIncome": "interest_income",
    "受取配当金": "dividend_income",
    "DividendIncome": "dividend_income",
    "支払利息": "interest_expense",
    "InterestExpense": "interest_expense",
    # 환차손익
    "為替差益": "fx_gain",
    "ForeignExchangeGain": "fx_gain",
    "為替差損": "fx_loss",
    "ForeignExchangeLoss": "fx_loss",
    # 경상이익 (J-GAAP 고유)
    "経常利益": "ordinary_income",
    "OrdinaryIncome": "ordinary_income",
    # 특별이익/손실 (J-GAAP 고유)
    "特別利益": "extraordinary_income",
    "ExtraordinaryIncome": "extraordinary_income",
    "特別損失": "extraordinary_loss",
    "ExtraordinaryLoss": "extraordinary_loss",
    # 감손
    "減損損失": "impairment_loss",
    "ImpairmentLoss": "impairment_loss",
    # 세전이익
    "税引前当期純利益": "income_before_tax",
    "IncomeBeforeTax": "income_before_tax",
    # 법인세
    "法人税等": "income_taxes",
    "IncomeTaxes": "income_taxes",
    # 법인세등조정액
    "法人税等調整額": "deferred_income_taxes",
    "DeferredIncomeTax": "deferred_income_taxes",
    # 당기순이익
    "当期純利益": "net_profit",
    "ProfitLoss": "net_profit",
    # 친회사 귀속 당기순이익
    "親会社帰属当期純利益": "net_profit_parent",
    "NetIncomeParent": "net_profit_parent",
    # 비지배지분 귀속 당기순이익
    "非支配株主帰属当期純利益": "net_profit_minority",
    "NetIncomeMinority": "net_profit_minority",
    # 포괄이익
    "包括利益": "comprehensive_income",
    "ComprehensiveIncome": "comprehensive_income",
    # 감가상각비
    "減価償却費": "depreciation",
    "Depreciation": "depreciation",
    # のれん상각
    "のれん償却額": "amortization_of_goodwill",
    "AmortizationOfGoodwill": "amortization_of_goodwill",
    # 지분법
    "持分法による投資損益": "equity_in_earnings",
    "EquityInEarnings": "equity_in_earnings",
    # 고정자산 처분손익
    "固定資産売却益": "gain_on_sale_of_fixed_assets",
    "GainOnSaleOfFixedAssets": "gain_on_sale_of_fixed_assets",
    "固定資産売却損": "loss_on_sale_of_fixed_assets",
    "LossOnSaleOfFixedAssets": "loss_on_sale_of_fixed_assets",
    "固定資産除却損": "loss_on_disposal_of_fixed_assets",
    "LossOnDisposalOfFixedAssets": "loss_on_disposal_of_fixed_assets",
    # 연구개발비
    "研究開発費": "rd_expenses",
    "ResearchAndDevelopmentExpenses": "rd_expenses",
    # 퇴직급여비용
    "退職給付費用": "retirement_benefit_expense",
    "RetirementBenefitExpenses": "retirement_benefit_expense",
    # 기타수익/비용
    "その他の収益": "other_income",
    "OtherIncome": "other_income",
    "その他の費用": "other_expenses",
    "OtherExpenses": "other_expenses",
    # EPS
    "1株当たり当期純利益": "basic_earnings_per_share",
    "BasicEPS": "basic_earnings_per_share",
    "希薄化後1株当たり当期純利益": "diluted_earnings_per_share",
    "DilutedEPS": "diluted_earnings_per_share",
    # BPS / DPS
    "1株当たり純資産": "book_value_per_share",
    "1株当たり配当額": "dividend_per_share",
    # ═══════════════════════════════════════════
    # BS — Balance Sheet (79개)
    # ═══════════════════════════════════════════
    # 유동자산
    "流動資産": "current_assets",
    "CurrentAssets": "current_assets",
    # 현금
    "現金及び預金": "cash_and_deposits",
    "CashAndDeposits": "cash_and_deposits",
    "現金及び現金同等物": "cash_and_cash_equivalents",
    "CashAndEquivalents": "cash_and_cash_equivalents",
    # 매출채권
    "受取手形及び売掛金": "trade_and_other_receivables",
    "TradeReceivables": "trade_and_other_receivables",
    "売掛金": "trade_receivables",
    "AccountsReceivable": "trade_receivables",
    # 대손충당금
    "貸倒引当金": "allowance_for_doubtful_accounts",
    "AllowanceForDoubtfulAccounts": "allowance_for_doubtful_accounts",
    # 재고자산
    "棚卸資産": "inventories",
    "Inventories": "inventories",
    # 재고 내역
    "商品": "merchandise",
    "Merchandise": "merchandise",
    "製品": "finished_goods",
    "FinishedGoods": "finished_goods",
    "仕掛品": "work_in_process",
    "WorkInProcess": "work_in_process",
    "原材料": "raw_materials",
    "RawMaterials": "raw_materials",
    "貯蔵品": "supplies_inventory",
    "Supplies": "supplies_inventory",
    # 유가증권
    "有価証券": "short_term_securities",
    "ShortTermInvestmentSecurities": "short_term_securities",
    # 선급비용
    "前払費用": "prepaid_expenses",
    "PrepaidExpenses": "prepaid_expenses",
    # 기타유동자산
    "その他の流動資産": "other_current_assets",
    "OtherCurrentAssets": "other_current_assets",
    "仮払金": "advance_payments",
    "AdvancePayments": "advance_payments",
    # 고정자산
    "固定資産": "noncurrent_assets",
    "NoncurrentAssets": "noncurrent_assets",
    "NonCurrentAssets": "noncurrent_assets",
    # 유형자산
    "有形固定資産": "tangible_assets",
    "PPE": "tangible_assets",
    # PPE 내역
    "建物": "buildings",
    "Buildings": "buildings",
    "構築物": "structures",
    "Structures": "structures",
    "機械装置": "machinery_and_equipment",
    "Machinery": "machinery_and_equipment",
    "車両運搬具": "vehicles",
    "Vehicles": "vehicles",
    "工具器具備品": "tools_furniture_and_fixtures",
    "ToolsFurnitureFixtures": "tools_furniture_and_fixtures",
    "土地": "land",
    "Land": "land",
    "建設仮勘定": "construction_in_progress",
    "ConstructionInProgress": "construction_in_progress",
    "リース資産": "leased_assets",
    "LeasedAssets": "leased_assets",
    # 무형자산
    "無形固定資産": "intangible_assets",
    "IntangibleAssets": "intangible_assets",
    "ソフトウェア": "software",
    "Software": "software",
    "特許権": "patent_rights",
    "PatentRights": "patent_rights",
    "商標権": "trademark_rights",
    "TrademarkRights": "trademark_rights",
    "のれん": "goodwill",
    "Goodwill": "goodwill",
    # 투자기타자산
    "投資その他の資産": "investments_and_other",
    "InvestmentsAndOtherAssets": "investments_and_other",
    "投資有価証券": "investment_securities",
    "InvestmentSecurities": "investment_securities",
    "関係会社株式": "investments_in_subsidiaries",
    "InvestmentsInAffiliates": "investments_in_subsidiaries",
    "敷金及び保証金": "guarantee_deposits",
    "GuaranteeDeposits": "guarantee_deposits",
    "長期貸付金": "long_term_loans_receivable",
    "LongTermLoansReceivable": "long_term_loans_receivable",
    "長期前払費用": "long_term_prepaid_expenses",
    "LongTermPrepaidExpenses": "long_term_prepaid_expenses",
    "繰延税金資産": "deferred_tax_assets",
    "DeferredTaxAssets": "deferred_tax_assets",
    "退職給付に係る資産": "retirement_benefit_asset",
    "RetirementBenefitAsset": "retirement_benefit_asset",
    "投資不動産": "investment_property",
    "InvestmentProperty": "investment_property",
    "契約資産": "contract_assets",
    "ContractAssets": "contract_assets",
    # 총자산
    "総資産": "total_assets",
    "TotalAssets": "total_assets",
    # 유동부채
    "流動負債": "current_liabilities",
    "CurrentLiabilities": "current_liabilities",
    "短期借入金": "shortterm_borrowings",
    "ShortTermLoansPayable": "shortterm_borrowings",
    "支払手形及び買掛金": "trade_and_other_payables",
    "TradePayables": "trade_and_other_payables",
    "買掛金": "trade_payables",
    "AccountsPayable": "trade_payables",
    "未払費用": "accrued_expenses",
    "AccruedExpenses": "accrued_expenses",
    "未払法人税等": "income_taxes_payable",
    "IncomeTaxesPayable": "income_taxes_payable",
    "未払金": "accounts_payable_other",
    "AccountsPayableOther": "accounts_payable_other",
    "賞与引当金": "provision_for_bonuses",
    "ProvisionForBonuses": "provision_for_bonuses",
    "1年内返済予定の長期借入金": "current_portion_lt_loans",
    "CurrentPortionOfLongTermLoansPayable": "current_portion_lt_loans",
    "前受金": "advances_received",
    "AdvancesReceived": "advances_received",
    "仮受金": "suspense_receipt",
    "SuspenseReceipt": "suspense_receipt",
    "その他の流動負債": "other_current_liabilities",
    "OtherCurrentLiabilities": "other_current_liabilities",
    "引当金（流動）": "provisions_current",
    "ProvisionsCurrent": "provisions_current",
    # 고정부채
    "固定負債": "noncurrent_liabilities",
    "NoncurrentLiabilities": "noncurrent_liabilities",
    "NonCurrentLiabilities": "noncurrent_liabilities",
    "長期借入金": "longterm_borrowings",
    "LongTermLoansPayable": "longterm_borrowings",
    "社債": "debentures",
    "BondsPayable": "debentures",
    "退職給付引当金": "retirement_benefit_liability",
    "RetirementBenefitLiability": "retirement_benefit_liability",
    "リース債務": "lease_liabilities",
    "LeaseLiabilities": "lease_liabilities",
    "資産除去債務": "asset_retirement_obligations",
    "AssetRetirementObligations": "asset_retirement_obligations",
    "繰延税金負債": "deferred_tax_liabilities",
    "DeferredTaxLiabilities": "deferred_tax_liabilities",
    "引当金（固定）": "provisions_noncurrent",
    "ProvisionsNoncurrent": "provisions_noncurrent",
    "その他の固定負債": "other_noncurrent_liabilities",
    "OtherNoncurrentLiabilities": "other_noncurrent_liabilities",
    # 부채합계
    "負債合計": "total_liabilities",
    "TotalLiabilities": "total_liabilities",
    # 주주자본
    "株主資本": "shareholders_equity",
    "ShareholdersEquity": "shareholders_equity",
    "資本金": "paidin_capital",
    "CapitalStock": "paidin_capital",
    "資本剰余金": "capital_surplus",
    "CapitalSurplus": "capital_surplus",
    "利益剰余金": "retained_earnings",
    "RetainedEarnings": "retained_earnings",
    "自己株式": "treasury_stock",
    "TreasuryShares": "treasury_stock",
    # AOCI
    "その他の包括利益累計額": "aoci",
    "AccumulatedOtherComprehensiveIncome": "aoci",
    "その他の包括利益": "other_comprehensive_income",
    "その他有価証券評価差額金": "valuation_difference_securities",
    "ValuationDifferenceSecurities": "valuation_difference_securities",
    "ValuationDifferenceOnAvailableForSaleSecurities": "valuation_difference_securities",
    "為替換算調整勘定": "foreign_currency_translation_adjustment",
    "ForeignCurrencyTranslationAdjustment": "foreign_currency_translation_adjustment",
    "退職給付に係る調整累計額": "remeasurements_of_defined_benefit_plans",
    "RemeasurementsOfDefinedBenefitPlans": "remeasurements_of_defined_benefit_plans",
    "繰延ヘッジ損益": "deferred_hedge_gains_losses",
    "DeferredHedgeGainsLosses": "deferred_hedge_gains_losses",
    # 신주예약권
    "新株予約権": "subscription_rights_to_shares",
    "SubscriptionRightsToShares": "subscription_rights_to_shares",
    # 비지배지분
    "非支配株主持分": "noncontrolling_interests_equity",
    "NonControllingInterests": "noncontrolling_interests_equity",
    # 자기자본 (주주귀속)
    "自己資本": "owners_of_parent_equity",
    "親会社の所有者に帰属する持分": "owners_of_parent_equity",
    "EquityParent": "owners_of_parent_equity",
    # 순자산
    "純資産": "net_assets",
    "TotalEquity": "net_assets",
    # 부채순자산합계
    "負債純資産合計": "total_liabilities_and_net_assets",
    "TotalLiabilitiesAndNetAssets": "total_liabilities_and_net_assets",
    # ═══════════════════════════════════════════
    # CF — Cash Flow (40개)
    # ═══════════════════════════════════════════
    "営業CF": "operating_cashflow",
    "OperatingCF": "operating_cashflow",
    "投資CF": "investing_cashflow",
    "InvestingCF": "investing_cashflow",
    "財務CF": "cash_flows_from_financing_activities",
    "FinancingCF": "cash_flows_from_financing_activities",
    # FX Effect
    "為替換算差額CF": "fx_effect_on_cash",
    "FxEffectOnCash": "fx_effect_on_cash",
    # 현금 증감
    "現金増減額": "net_change_in_cash",
    "NetIncreaseDecreaseInCashAndCashEquivalents": "net_change_in_cash",
    "現金期首残高": "cash_beginning",
    "CashAndCashEquivalentsAtBeginningOfPeriod": "cash_beginning",
    "現金期末残高": "cash_end",
    "CashEnd": "cash_end",
    # CF 내역 (Operating)
    "DepreciationCF": "depreciation_cf",
    "ImpairmentLossCF": "impairment_loss_cf",
    "貸倒引当金の増減額": "allowance_for_doubtful_accounts_change",
    "IncreaseDecreaseInAllowanceForDoubtfulAccounts": "allowance_for_doubtful_accounts_change",
    "AmortizationOfGoodwillCF": "amortization_of_goodwill_cf",
    "EquityInEarningsCF": "equity_in_earnings_cf",
    "配当金の受取額": "dividends_received_cf",
    "DividendsReceivedCF": "dividends_received_cf",
    "退職給付に係る負債の増減額": "change_in_retirement_benefit_liability",
    "ChangeInRetirementBenefitLiability": "change_in_retirement_benefit_liability",
    "引当金の増減額": "change_in_provisions",
    "IncreaseDecreaseInProvision": "change_in_provisions",
    "売上債権の増減額": "change_in_receivables",
    "IncreaseDecreaseInNotesAndAccountsReceivable": "change_in_receivables",
    "棚卸資産の増減額": "change_in_inventories",
    "IncreaseDecreaseInInventories": "change_in_inventories",
    "仕入債務の増減額": "change_in_payables",
    "IncreaseDecreaseInNotesAndAccountsPayable": "change_in_payables",
    "利息及び配当金の受取額": "interest_and_dividends_received",
    "InterestAndDividendsReceived": "interest_and_dividends_received",
    "利息の支払額": "interest_paid_cf",
    "InterestPaid": "interest_paid_cf",
    "法人税等の支払額": "income_taxes_paid",
    "IncomeTaxesPaid": "income_taxes_paid",
    # CF 내역 (Investing)
    "有形固定資産の取得による支出": "purchase_ppe",
    "PurchaseOfPropertyPlantAndEquipment": "purchase_ppe",
    "有形固定資産の売却による収入": "proceeds_from_sale_of_ppe",
    "ProceedsFromSaleOfPropertyPlantAndEquipment": "proceeds_from_sale_of_ppe",
    "投資有価証券の取得による支出": "purchase_investments",
    "PurchaseOfInvestmentSecurities": "purchase_investments",
    "投資有価証券の売却による収入": "proceeds_from_sale_of_investments",
    "ProceedsFromSaleOfInvestmentSecurities": "proceeds_from_sale_of_investments",
    "子会社株式の取得による支出": "purchase_of_subsidiaries_stock",
    "PurchaseOfSubsidiariesStock": "purchase_of_subsidiaries_stock",
    "子会社株式の売却による収入": "proceeds_from_sale_of_subsidiaries_stock",
    "ProceedsFromSaleOfSubsidiariesStock": "proceeds_from_sale_of_subsidiaries_stock",
    "貸付けによる支出": "payments_of_loans_receivable",
    "PaymentsOfLoansReceivable": "payments_of_loans_receivable",
    "貸付金の回収による収入": "collection_of_loans_receivable",
    "CollectionOfLoansReceivable": "collection_of_loans_receivable",
    "連結範囲変更子会社取得支出": "purchase_of_subsidiaries_change_in_scope",
    "PurchaseOfSharesOfSubsidiariesResultingInChangeInScopeOfConsolidation": "purchase_of_subsidiaries_change_in_scope",
    "無形固定資産の取得による支出": "purchase_intangible_assets",
    "PurchaseOfIntangibleAssets": "purchase_intangible_assets",
    # CF 내역 (Financing)
    "借入れによる収入": "proceeds_from_borrowings",
    "ProceedsFromBorrowings": "proceeds_from_borrowings",
    "借入金の返済による支出": "repayment_of_borrowings",
    "RepaymentOfBorrowings": "repayment_of_borrowings",
    "社債発行収入": "bond_issuance",
    "ProceedsFromIssuanceOfBonds": "bond_issuance",
    "社債償還支出": "bond_redemption",
    "RedemptionOfBonds": "bond_redemption",
    "配当金の支払額": "dividends_paid",
    "DividendsPaid": "dividends_paid",
    "リース債務の返済による支出": "repayment_of_lease_liabilities",
    "RepaymentOfLeaseLiabilities": "repayment_of_lease_liabilities",
    "短期借入金の純増減額": "net_change_short_term_loans",
    "NetIncreaseDecreaseInShortTermLoansPayable": "net_change_short_term_loans",
    "株式発行収入": "proceeds_from_issuance_of_shares",
    "ProceedsFromIssuanceOfShares": "proceeds_from_issuance_of_shares",
    "自己株式の取得による支出": "purchase_treasury_shares",
    "PurchaseOfTreasuryShares": "purchase_treasury_shares",
}

# ── 전각 → 반각 정규화 ──

_FULLWIDTH_OFFSET = 0xFEE0  # '！' - '!'


def _normalizeWidth(text: str) -> str:
    """전각 영숫자/기호 → 반각, 전각 스페이스 → 반각."""
    result: list[str] = []
    for ch in text:
        cp = ord(ch)
        if 0xFF01 <= cp <= 0xFF5E:  # ！～～
            result.append(chr(cp - _FULLWIDTH_OFFSET))
        elif cp == 0x3000:  # 전각 스페이스
            result.append(" ")
        else:
            result.append(ch)
    return "".join(result)


_WHITESPACE_RE = re.compile(r"\s+")
_PAREN_RE = re.compile(r"[（(][^）)]*[）)]")


def _normalizeText(text: str) -> str:
    """전각→반각 + 공백 정규화 + 앞뒤 공백 제거."""
    text = _normalizeWidth(text)
    text = _WHITESPACE_RE.sub("", text)
    return text.strip()


def _removeParentheses(text: str) -> str:
    """괄호 및 괄호 내용 제거."""
    return _PAREN_RE.sub("", text).strip()


# ── 매퍼 클래스 ──


class EdinetMapper:
    """EDINET 계정 매퍼 (thread-safe singleton 패턴)."""

    _mappings: Optional[dict[str, str]] = None
    _lock = threading.Lock()

    @classmethod
    def _ensureLoaded(cls) -> None:
        if cls._mappings is not None:
            return
        with cls._lock:
            if cls._mappings is not None:
                return
            cls._loadData()

    @classmethod
    def _loadData(cls) -> None:
        path = _DATA_DIR / "accountMappings.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                cls._mappings = json.load(f)
        else:
            cls._mappings = {}

    @classmethod
    def map(
        cls,
        elementId: str,
        accountName: str = "",
    ) -> str | None:
        """XBRL element ID + 일본어 계정명 → snakeId 매핑.

        Args:
            elementId: XBRL 요소 ID (예: "jpcrp_cor:Revenue").
            accountName: 일본어 계정명 (예: "売上高").

        Returns:
            snakeId 또는 None (미매핑).
        """
        cls._ensureLoaded()

        # 1. prefix 제거
        cleanId = _removePrefix(elementId)

        # 2. ID_SYNONYMS
        cleanId = ID_SYNONYMS.get(cleanId, cleanId)

        # 3. ACCOUNT_NAME_SYNONYMS
        normalizedName = accountName
        if accountName:
            normalizedName = ACCOUNT_NAME_SYNONYMS.get(accountName, accountName)

        # 4. CORE_MAP (영문 element 우선, 일본어 계정명 fallback)
        if cleanId in CORE_MAP:
            return CORE_MAP[cleanId]
        if normalizedName and normalizedName in CORE_MAP:
            return CORE_MAP[normalizedName]

        # 5. accountMappings.json
        assert cls._mappings is not None
        if normalizedName and normalizedName in cls._mappings:
            return cls._mappings[normalizedName]
        if cleanId in cls._mappings:
            return cls._mappings[cleanId]

        # 6. 전각/공백 정규화 후 재조회
        if accountName:
            normalized = _normalizeText(accountName)
            if normalized in CORE_MAP:
                return CORE_MAP[normalized]
            if normalized in cls._mappings:
                return cls._mappings[normalized]

            # 괄호 제거 후 재조회
            noParen = _removeParentheses(normalized)
            if noParen and noParen != normalized:
                if noParen in CORE_MAP:
                    return CORE_MAP[noParen]
                if noParen in cls._mappings:
                    return cls._mappings[noParen]

        # 7. 미매핑
        return None

    @classmethod
    def mappingRate(cls, elements: list[tuple[str, str]]) -> dict[str, float]:
        """매핑률 측정.

        Args:
            elements: [(elementId, accountName), ...] 리스트.

        Returns:
            {"total": N, "mapped": M, "rate": M/N} dict.
        """
        total = len(elements)
        if total == 0:
            return {"total": 0, "mapped": 0, "rate": 0.0}

        mapped = sum(1 for eid, name in elements if cls.map(eid, name) is not None)
        return {
            "total": total,
            "mapped": mapped,
            "rate": round(mapped / total, 4),
        }
