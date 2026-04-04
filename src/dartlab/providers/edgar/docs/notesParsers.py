"""EDGAR Notes 카테고리별 파서 — XBRL 수치 태그에서 구조화 DataFrame 추출.

DART의 12개 notes 카테고리에 대응:
inventory, borrowings, tangibleAsset, intangibleAsset, receivables,
provisions, eps, segments, costByNature, lease, affiliates, investmentProperty
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

# DART notes 카테고리 → XBRL 태그 패턴 매핑
_CATEGORY_TAGS: dict[str, list[str]] = {
    "inventory": [
        "InventoryFinishedGoods",
        "InventoryWorkInProcess",
        "InventoryRawMaterials",
        "InventoryNet",
        "InventoryGross",
        "InventoryAdjustments",
        "InventoryValuationReserves",
    ],
    "borrowings": [
        "LongTermDebt",
        "LongTermDebtNoncurrent",
        "LongTermDebtCurrent",
        "ShortTermBorrowings",
        "LinesOfCreditCurrent",
        "CommercialPaper",
        "NotesPayable",
        "SecuredDebt",
        "UnsecuredDebt",
    ],
    "tangibleAsset": [
        "PropertyPlantAndEquipmentGross",
        "PropertyPlantAndEquipmentNet",
        "AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment",
        "Land",
        "BuildingsAndImprovementsGross",
        "MachineryAndEquipmentGross",
        "ConstructionInProgressGross",
        "LeaseholdImprovementsGross",
    ],
    "intangibleAsset": [
        "Goodwill",
        "IntangibleAssetsNetExcludingGoodwill",
        "FiniteLivedIntangibleAssetsGross",
        "FiniteLivedIntangibleAssetsAccumulatedAmortization",
        "FiniteLivedIntangibleAssetsNet",
        "IndefiniteLivedIntangibleAssetsExcludingGoodwill",
        "CapitalizedComputerSoftwareGross",
        "CapitalizedComputerSoftwareNet",
    ],
    "receivables": [
        "AccountsReceivableNetCurrent",
        "AccountsReceivableGrossCurrent",
        "AllowanceForDoubtfulAccountsReceivableCurrent",
        "NotesReceivableNet",
        "ReceivablesNetCurrent",
    ],
    "provisions": [
        "ProductWarrantyAccrual",
        "LossContingencyAccrualAtCarryingValue",
        "RestructuringReserve",
        "EnvironmentalLossContingencyStatementOfFinancialPositionAccrual",
        "LitigationReserve",
        "AccruedLiabilitiesCurrent",
    ],
    "eps": [
        "EarningsPerShareBasic",
        "EarningsPerShareDiluted",
        "WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "AntidilutiveSecuritiesExcludedFromComputationOfEarningsPerShareAmount",
    ],
    "segments": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SegmentReportingInformationOperatingIncomeLoss",
        "SegmentReportingInformationRevenue",
    ],
    "costByNature": [
        "CostOfGoodsAndServicesSold",
        "SellingGeneralAndAdministrativeExpense",
        "ResearchAndDevelopmentExpense",
        "DepreciationAndAmortization",
        "LaborAndRelatedExpense",
        "AdvertisingExpense",
    ],
    "lease": [
        "OperatingLeaseRightOfUseAsset",
        "OperatingLeaseLiability",
        "FinanceLeaseRightOfUseAsset",
        "FinanceLeaseLiability",
        "OperatingLeasePayments",
        "OperatingLeaseCost",
    ],
    "affiliates": [
        "InvestmentsInAffiliatesSubsidiariesAssociatesAndJointVentures",
        "EquityMethodInvestments",
        "EquityMethodInvestmentRealizedGainLossOnDisposal",
        "IncomeLossFromEquityMethodInvestments",
        "EquityMethodInvestmentDividendsOrDistributions",
        "EquityMethodInvestmentOwnershipPercentage",
        "PaymentsToAcquireEquityMethodInvestments",
        "PaymentsToAcquireBusinessesAndInterestInAffiliates",
        "EquityMethodInvestmentOtherThanTemporaryImpairment",
    ],
    "investmentProperty": [
        "RealEstateInvestmentPropertyNet",
        "RealEstateInvestmentPropertyAtCost",
        "RealEstateInvestmentPropertyAccumulatedDepreciation",
        "RealEstateInvestmentPropertyAtFairValue",
        "RealEstateHeldsale",
    ],
}

# DART 카테고리 → 한국어 표시명
CATEGORY_LABELS: dict[str, str] = {
    "inventory": "재고자산",
    "borrowings": "차입금",
    "tangibleAsset": "유형자산",
    "intangibleAsset": "무형자산",
    "receivables": "매출채권",
    "provisions": "충당부채",
    "eps": "주당이익",
    "segments": "부문정보",
    "costByNature": "비용성격별분류",
    "lease": "리스",
    "affiliates": "관계기업",
    "investmentProperty": "투자부동산",
}


def availableCategories() -> list[str]:
    """사용 가능한 notes 카테고리 목록."""
    return list(_CATEGORY_TAGS.keys())


def extractAllNoteCategories(
    cik: str,
    *,
    edgarDir: Path | None = None,
) -> dict[str, pl.DataFrame]:
    """한 번의 parquet 로드로 모든 카테고리를 추출. 12번 I/O → 1번."""
    if edgarDir is None:
        from dartlab.providers.edgar.report import edgarFinancePath
        edgarDir = edgarFinancePath("_").parent

    path = edgarDir / f"{cik}.parquet"
    if not path.exists():
        return {}

    try:
        # 모든 카테고리의 태그를 합산
        allTags: list[str] = []
        tagToCat: dict[str, str] = {}
        for cat, tags in _CATEGORY_TAGS.items():
            allTags.extend(tags)
            for t in tags:
                tagToCat[t] = cat

        df = pl.scan_parquet(path).filter(
            pl.col("tag").is_in(allTags)
            & pl.col("unit").str.contains("(?i)USD|shares|pure")
            & pl.col("form").is_in(["10-K", "20-F"])
        ).select("tag", "label", "fy", "val", "filed").collect()

        if df.is_empty():
            return {}

        df = df.sort("filed", descending=True).unique(subset=["tag", "fy"], keep="first")

        result: dict[str, pl.DataFrame] = {}
        for cat in _CATEGORY_TAGS:
            catTags = _CATEGORY_TAGS[cat]
            catDf = df.filter(pl.col("tag").is_in(catTags))
            if catDf.is_empty():
                continue
            pivoted = catDf.pivot(on="fy", index=["tag", "label"], values="val")
            yearCols = sorted([c for c in pivoted.columns if c not in ("tag", "label")])
            if yearCols:
                result[cat] = pivoted.select(["tag", "label"] + yearCols)

        return result
    except (pl.exceptions.ComputeError, pl.exceptions.SchemaError, OSError):
        return {}


def extractNoteCategory(
    cik: str,
    category: str,
    *,
    edgarDir: Path | None = None,
) -> pl.DataFrame | None:
    """카테고리별 XBRL 수치 태그 추출 → 구조화 DataFrame.

    Returns: tag, label, period(fy), value 컬럼.
    연도별로 피벗된 형태 (tag × fy).
    """
    if category not in _CATEGORY_TAGS:
        return None

    if edgarDir is None:
        from dartlab.providers.edgar.report import edgarFinancePath
        edgarDir = edgarFinancePath("_").parent  # finance 디렉토리

    path = edgarDir / f"{cik}.parquet"
    if not path.exists():
        return None

    tagList = _CATEGORY_TAGS[category]

    try:
        df = pl.scan_parquet(path).filter(
            pl.col("tag").is_in(tagList)
            & pl.col("unit").str.contains("(?i)USD|shares|pure")
            & pl.col("form").is_in(["10-K", "20-F"])
        ).select("tag", "label", "fy", "val", "filed").collect()

        if df.is_empty():
            return None

        # 연도별 최신값 (같은 fy에서 가장 최근 filed 기준)
        df = df.sort("filed", descending=True).unique(subset=["tag", "fy"], keep="first")

        # 피벗: tag × fy → value
        pivoted = df.pivot(
            on="fy",
            index=["tag", "label"],
            values="val",
        )

        # 연도 컬럼 정렬
        yearCols = sorted(
            [c for c in pivoted.columns if c not in ("tag", "label")],
        )
        return pivoted.select(["tag", "label"] + yearCols)

    except (pl.exceptions.ComputeError, pl.exceptions.SchemaError, OSError):
        return None
