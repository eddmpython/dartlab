"""EDGAR XBRL Notes — TextBlock 태그 추출.

SEC XBRL companyfacts에서 TextBlock 형태의 주석(Notes) 태그를 추출한다.
AccountingPoliciesTextBlock, RevenueRecognitionTextBlock 등.

사용법::

    c = Company("AAPL")
    c.docs.notes()                      # 전체 TextBlock 목록
    c.docs.notes("AccountingPolicies")  # 특정 주석 검색
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

# 주요 TextBlock 태그 → 읽기 쉬운 label
_NOTE_LABELS: dict[str, str] = {
    "AccountingPoliciesTextBlock": "Accounting Policies",
    "RevenueRecognitionPolicyTextBlock": "Revenue Recognition",
    "SignificantAccountingPoliciesTextBlock": "Significant Accounting Policies",
    "IncomeTaxDisclosureTextBlock": "Income Taxes",
    "DebtDisclosureTextBlock": "Debt",
    "LeasesOfLesseeDisclosureTextBlock": "Leases",
    "CommitmentsAndContingenciesDisclosureTextBlock": "Commitments & Contingencies",
    "FairValueDisclosuresTextBlock": "Fair Value",
    "SegmentReportingDisclosureTextBlock": "Segment Reporting",
    "StockholdersEquityNoteDisclosureTextBlock": "Stockholders Equity",
    "GoodwillAndIntangibleAssetsDisclosureTextBlock": "Goodwill & Intangibles",
    "PropertyPlantAndEquipmentDisclosureTextBlock": "Property Plant & Equipment",
    "InventoryDisclosureTextBlock": "Inventory",
    "CompensationAndRetirementDisclosureTextBlock": "Compensation & Retirement",
    "EarningsPerShareTextBlock": "Earnings Per Share",
    "ShareBasedCompensationOptionAndIncentivePlansPolicy": "Stock-Based Compensation",
    "FinancialInstrumentsDisclosureTextBlock": "Financial Instruments",
    "RelatedPartyTransactionsDisclosureTextBlock": "Related Party Transactions",
    "SubsequentEventsTextBlock": "Subsequent Events",
    "BusinessCombinationDisclosureTextBlock": "Business Combinations",
}


def notes(
    cik: str,
    query: str | None = None,
    *,
    edgarDir: Path | None = None,
) -> pl.DataFrame | None:
    """SEC XBRL TextBlock 태그 추출.

    Args:
        cik: SEC CIK 번호.
        query: 검색어 (None이면 전체 TextBlock 목록).
        edgarDir: EDGAR 데이터 디렉토리.

    Returns:
        DataFrame with columns: tag, label, period, text (truncated), chars
    """
    if edgarDir is None:
        from dartlab.core.dataLoader import _dataDir

        edgarDir = _dataDir("edgar")

    path = edgarDir / f"{cik}.parquet"
    if not path.exists():
        return None

    df = pl.read_parquet(path)
    if df.is_empty():
        return None

    # TextBlock 태그만 필터
    df = df.filter(pl.col("tag").str.contains("TextBlock"))

    if query:
        df = df.filter(pl.col("tag").str.to_lowercase().str.contains(query.lower()))

    if df.is_empty():
        return None

    # label 매핑
    tags = df["tag"].unique().to_list()
    tagToLabel: dict[str, str] = {}
    for tag in tags:
        tagToLabel[tag] = _NOTE_LABELS.get(tag, _tagToLabel(tag))

    # 최신 기간 기준 정리
    result_cols = ["tag", "val", "fy", "fp", "form", "filed"]
    available = [c for c in result_cols if c in df.columns]
    result = df.select(available)

    if "fy" in result.columns:
        result = result.sort("fy", descending=True)

    result = result.with_columns(
        pl.col("tag").replace_strict(tagToLabel, default=pl.col("tag")).alias("label"),
    )

    # val 텍스트 길이 + 미리보기
    if "val" in result.columns:
        result = result.with_columns(
            pl.col("val").cast(pl.Utf8).str.len_chars().alias("chars"),
            pl.col("val").cast(pl.Utf8).str.slice(0, 200).alias("preview"),
        )

    return result


def _tagToLabel(tag: str) -> str:
    """TextBlock 태그명 → 읽기 쉬운 label. 'AccountingPoliciesTextBlock' → 'Accounting Policies'."""
    import re

    label = tag.replace("TextBlock", "").replace("DisclosureText", "")
    label = re.sub(r"([a-z])([A-Z])", r"\1 \2", label)
    label = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", label)
    return label.strip()
