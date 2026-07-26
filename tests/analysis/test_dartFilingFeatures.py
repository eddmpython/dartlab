"""DART quarterly financial feature compiler contract tests."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO

import polars as pl
import pytest

from dartlab.analysis.financial.dartFilingFeatures import buildDartFinancialFeatureInput
from dartlab.analysis.financial.dataAssets import dartFinancialFeatures
from dartlab.dataHub.feature.query import featureObservationSetFromValue

pytestmark = pytest.mark.unit

_BALANCE_ACCOUNTS = (
    ("ifrs-full_CashAndCashEquivalents", "현금및현금성자산", 20.0),
    ("ifrs-full_TradeAndOtherCurrentReceivables", "매출채권 및 기타유동채권", 30.0),
    ("ifrs-full_Inventories", "재고자산", 40.0),
    ("ifrs-full_TradeAndOtherCurrentPayables", "매입채무 및 기타유동채무", 25.0),
    ("ifrs-full_PropertyPlantAndEquipment", "유형자산", 50.0),
    ("dart_ShortTermBorrowings", "단기차입금", 10.0),
    ("dart_LongTermBorrowings", "장기차입금", 15.0),
    ("ifrs-full_Assets", "자산총계", 200.0),
    ("ifrs-full_Liabilities", "부채총계", 80.0),
    ("ifrs-full_Equity", "자본총계", 120.0),
)


def _row(
    *,
    receipt: str,
    year: str,
    report: str,
    statement: str,
    accountId: str,
    accountName: str,
    amount: float,
    cumulative: float | None = None,
) -> dict[str, str | None]:
    return {
        "rcept_no": receipt,
        "reprt_code": "11011",
        "bsns_year": year,
        "corp_code": "00126380",
        "sj_div": statement,
        "account_id": accountId,
        "account_nm": accountName,
        "thstrm_amount": str(amount),
        "thstrm_add_amount": str(cumulative) if cumulative is not None else None,
        "currency": "KRW",
        "fs_div": "CFS",
        "stock_code": "005930",
        "reprt_nm": report,
    }


def _finance(*, amendedQ4: bool = False) -> pl.DataFrame:
    reports = (
        ("1분기", "20240515000001", 100.0, 10.0),
        ("2분기", "20240814000001", 210.0, 21.0),
        ("3분기", "20241114000001", 330.0, 33.0),
        ("4분기", "20250315000001", 460.0, 46.0),
    )
    rows: list[dict[str, str | None]] = []
    for report, receipt, revenue, operating in reports:
        rows.extend(
            (
                _row(
                    receipt=receipt,
                    year="2024",
                    report=report,
                    statement="IS",
                    accountId="ifrs-full_Revenue",
                    accountName="매출액",
                    amount=revenue,
                    cumulative=revenue,
                ),
                _row(
                    receipt=receipt,
                    year="2024",
                    report=report,
                    statement="IS",
                    accountId="dart_OperatingIncomeLoss",
                    accountName="영업이익",
                    amount=operating,
                    cumulative=operating,
                ),
            )
        )
        rows.extend(
            _row(
                receipt=receipt,
                year="2024",
                report=report,
                statement="BS",
                accountId=accountId,
                accountName=accountName,
                amount=value,
            )
            for accountId, accountName, value in _BALANCE_ACCOUNTS
        )
    if amendedQ4:
        amendmentReceipt = "20250401000001"
        amendment = [row for row in rows if row["reprt_nm"] == "4분기"]
        for row in amendment:
            replacement = dict(row)
            replacement["rcept_no"] = amendmentReceipt
            if replacement["account_id"] == "ifrs-full_Revenue":
                replacement["thstrm_amount"] = "500"
                replacement["thstrm_add_amount"] = "500"
            rows.append(replacement)
    return pl.DataFrame(rows)


def _marchYearEndFinance() -> pl.DataFrame:
    finance = _finance()
    schedule = {
        "1분기": ("2024", "20240814000001"),
        "2분기": ("2024", "20241114000001"),
        "3분기": ("2025", "20250214000001"),
        "4분기": ("2025", "20250615000001"),
    }
    return finance.with_columns(
        pl.col("reprt_nm")
        .replace_strict({report: year for report, (year, _receipt) in schedule.items()})
        .alias("bsns_year"),
        pl.col("reprt_nm")
        .replace_strict({report: receipt for report, (_year, receipt) in schedule.items()})
        .alias("rcept_no"),
    )


def testCompilesValidatedQuarterlyEnvelopeFromPinnedFrame() -> None:
    envelope = buildDartFinancialFeatureInput(
        _finance(),
        entityId="KR:005930",
        knownAt="20250320",
        fiscalYearEndMonth=12,
    )
    dataset = featureObservationSetFromValue(envelope)

    assert dataset is not None
    assert len(dataset.registry.specs) == 10
    assert len(dataset.observations) == 10
    bySignal = {item.signalId: item for item in dataset.observations}
    assert bySignal["financial.revenue"].value == 130.0
    assert bySignal["financial.operatingMargin"].value == pytest.approx(13.0 / 130.0)
    assert bySignal["financial.debt"].value == 25.0
    assert bySignal["financial.otherNetAssets"].value == 30.0
    assert bySignal["financial.revenue"].eventAt == "20241231"
    assert bySignal["financial.revenue"].availableAt == "20250315"


def testKnownAtSelectsLatestWholeFilingWithoutRevisionLeakage() -> None:
    finance = _finance(amendedQ4=True)
    before = buildDartFinancialFeatureInput(
        finance,
        entityId="KR:005930",
        knownAt="20250320",
        fiscalYearEndMonth=12,
    )
    after = buildDartFinancialFeatureInput(
        finance,
        entityId="KR:005930",
        knownAt="20250402",
        fiscalYearEndMonth=12,
    )
    beforeRevenue = next(item for item in before["observations"] if item["signalId"] == "financial.revenue")
    afterRevenue = next(item for item in after["observations"] if item["signalId"] == "financial.revenue")

    assert beforeRevenue["value"] == 130.0
    assert afterRevenue["value"] == 170.0
    assert beforeRevenue["availableAt"] == "20250315"
    assert afterRevenue["availableAt"] == "20250401"
    assert beforeRevenue["revisionId"] != afterRevenue["revisionId"]


def testFiscalYearEndMonthControlsExactEventDate() -> None:
    envelope = buildDartFinancialFeatureInput(
        _marchYearEndFinance(),
        entityId="KR:005930",
        knownAt="20250620",
        fiscalYearEndMonth=3,
    )
    revenue = next(item for item in envelope["observations"] if item["signalId"] == "financial.revenue")

    assert revenue["value"] == 130.0
    assert revenue["eventAt"] == "20250331"
    assert revenue["availableAt"] == "20250615"


def testHistoricalFilingFromPriorFiscalCalendarDoesNotBlockLatestWindow() -> None:
    historical = (
        _finance()
        .filter(pl.col("reprt_nm") == "4분기")
        .with_columns(
            pl.lit("2016").alias("bsns_year"),
            pl.lit("20160629000284").alias("rcept_no"),
        )
    )
    envelope = buildDartFinancialFeatureInput(
        pl.concat((historical, _finance()), how="vertical_relaxed"),
        entityId="KR:005930",
        knownAt="20250320",
        fiscalYearEndMonth=12,
    )
    revenue = next(item for item in envelope["observations"] if item["signalId"] == "financial.revenue")

    assert revenue["value"] == 130.0
    assert revenue["eventAt"] == "20241231"


def testRejectsIncompleteFourQuarterFlowWindow() -> None:
    finance = _finance().filter(pl.col("reprt_nm") != "2분기")

    with pytest.raises(ValueError, match="연속된 4개 분기"):
        buildDartFinancialFeatureInput(
            finance,
            entityId="KR:005930",
            knownAt="20250320",
            fiscalYearEndMonth=12,
        )


def testDataAssetReadsOnlyIntegrityBoundPayload() -> None:
    buffer = BytesIO()
    _finance().write_parquet(buffer)
    payload = buffer.getvalue()

    envelope = dartFinancialFeatures(
        subject="KR:005930",
        sourceEntityId="005930",
        sourcePayload=payload,
        sourceIntegrityDigest=sha256(payload).hexdigest(),
        knownAt="20250320",
        fiscalYearEndMonth="12",
    )

    assert len(envelope["observations"]) == 10


def testDataAssetRejectsPayloadDigestOrIdentityMismatch() -> None:
    buffer = BytesIO()
    _finance().write_parquet(buffer)
    payload = buffer.getvalue()

    with pytest.raises(ValueError, match="integrity"):
        dartFinancialFeatures(
            subject="KR:005930",
            sourceEntityId="005930",
            sourcePayload=payload,
            sourceIntegrityDigest="0" * 64,
            knownAt="20250320",
            fiscalYearEndMonth=12,
        )
    with pytest.raises(ValueError, match="일치하는 6자리 영숫자"):
        dartFinancialFeatures(
            subject="KR:000660",
            sourceEntityId="005930",
            sourcePayload=payload,
            sourceIntegrityDigest=sha256(payload).hexdigest(),
            knownAt="20250320",
            fiscalYearEndMonth=12,
        )


def testDataAssetAcceptsSixCharacterAlphanumericKrTicker() -> None:
    finance = _finance().with_columns(pl.lit("0001A0").alias("stock_code"))
    buffer = BytesIO()
    finance.write_parquet(buffer)
    payload = buffer.getvalue()

    envelope = dartFinancialFeatures(
        subject="KR:0001a0",
        sourceEntityId="0001A0",
        sourcePayload=payload,
        sourceIntegrityDigest=sha256(payload).hexdigest(),
        knownAt="20250320",
        fiscalYearEndMonth=12,
    )

    assert {item["entityId"] for item in envelope["observations"]} == {"KR:0001A0"}


def testDataAssetRejectsNonAsciiAlphanumericKrTicker() -> None:
    buffer = BytesIO()
    _finance().write_parquet(buffer)
    payload = buffer.getvalue()

    with pytest.raises(ValueError, match="6자리 영숫자"):
        dartFinancialFeatures(
            subject="KR:000가00",
            sourceEntityId="000가00",
            sourcePayload=payload,
            sourceIntegrityDigest=sha256(payload).hexdigest(),
            knownAt="20250320",
            fiscalYearEndMonth=12,
        )


def testRequestedMeasuresAreHonoredAndUnknownOnesFailClosed() -> None:
    """요청한 measure 만 반환한다. EDGAR owner 와 같은 pushdown 계약이다."""

    from dartlab.analysis.financial.dartFilingFeatures import (
        DART_FINANCIAL_FEATURE_MAPPINGS,
        buildDartFinancialFeatureInput,
    )

    frame = _finance()
    full = buildDartFinancialFeatureInput(
        frame,
        entityId="KR:005930",
        knownAt="20250320",
        fiscalYearEndMonth=12,
    )
    narrowed = buildDartFinancialFeatureInput(
        frame,
        entityId="KR:005930",
        knownAt="20250320",
        fiscalYearEndMonth=12,
        measures=("financial.revenue",),
    )

    fullIds = {item["signalId"] for item in full["observations"]}
    narrowedIds = {item["signalId"] for item in narrowed["observations"]}
    assert narrowedIds == {"financial.revenue"}
    assert narrowedIds < fullIds
    # 선언 순서는 그대로라 observation 순서가 결정적이다.
    declared = [item.variableId for item in DART_FINANCIAL_FEATURE_MAPPINGS]
    emitted = [item["signalId"] for item in full["observations"]]
    assert emitted == [item for item in declared if item in fullIds]

    with pytest.raises(ValueError, match="지원되지 않습니다"):
        buildDartFinancialFeatureInput(
            frame,
            entityId="KR:005930",
            knownAt="20250320",
            fiscalYearEndMonth=12,
            measures=("financial.unknown",),
        )
    with pytest.raises(ValueError, match="중복"):
        buildDartFinancialFeatureInput(
            frame,
            entityId="KR:005930",
            knownAt="20250320",
            fiscalYearEndMonth=12,
            measures=("financial.revenue", "financial.revenue"),
        )
