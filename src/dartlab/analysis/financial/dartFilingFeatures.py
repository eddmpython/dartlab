"""DART filing evidence를 provider-neutral 재무 feature envelope로 변환한다."""

from __future__ import annotations

import calendar
import json
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from typing import Any

import polars as pl

from dartlab.providers.dart.finance.frameTimeseries import buildTimeseriesFromFrame

DART_FINANCIAL_FEATURE_NORMALIZATION_HASH = sha256(b"dartlab.dart-quarterly-financial-state-adapter.v1").hexdigest()

_QUARTER_BY_REPORT = {"1분기": 1, "2분기": 2, "3분기": 3, "4분기": 4}
_EVIDENCE_COLUMNS = (
    "rcept_no",
    "__sourceBsnsYear",
    "bsns_year",
    "reprt_nm",
    "sj_div",
    "fs_div",
    "account_id",
    "account_nm",
    "thstrm_amount",
    "thstrm_add_amount",
    "currency",
)


@dataclass(frozen=True)
class DartFinancialFeatureMapping:
    """DART 정규화 값과 공용 feature 의미의 결합."""

    variableId: str
    fieldName: str
    evidenceRole: str
    timing: str
    transformId: str
    lower: float | None
    upper: float | None


DART_FINANCIAL_FEATURE_MAPPINGS: tuple[DartFinancialFeatureMapping, ...] = (
    DartFinancialFeatureMapping(
        "financial.revenue",
        "revenue",
        "deterministicDerived",
        "flow",
        "standalone-quarter-flow-v1",
        0.0,
        None,
    ),
    DartFinancialFeatureMapping(
        "financial.operatingMargin",
        "operatingMargin",
        "deterministicDerived",
        "ratio",
        "operating-profit-div-revenue-v1",
        -1.0,
        1.0,
    ),
    DartFinancialFeatureMapping(
        "financial.cash",
        "cash",
        "observed",
        "stock",
        "latest-filing-instant-v1",
        0.0,
        None,
    ),
    DartFinancialFeatureMapping(
        "financial.debt",
        "debt",
        "deterministicDerived",
        "stock",
        "interest-bearing-debt-components-v1",
        0.0,
        None,
    ),
    DartFinancialFeatureMapping(
        "financial.receivables",
        "receivables",
        "observed",
        "stock",
        "latest-filing-instant-v1",
        0.0,
        None,
    ),
    DartFinancialFeatureMapping(
        "financial.inventories",
        "inventories",
        "observed",
        "stock",
        "latest-filing-instant-v1",
        0.0,
        None,
    ),
    DartFinancialFeatureMapping(
        "financial.payables",
        "payables",
        "observed",
        "stock",
        "latest-filing-instant-v1",
        0.0,
        None,
    ),
    DartFinancialFeatureMapping(
        "financial.ppe",
        "ppe",
        "observed",
        "stock",
        "latest-filing-instant-v1",
        0.0,
        None,
    ),
    DartFinancialFeatureMapping(
        "financial.otherNetAssets",
        "otherNetAssets",
        "deterministicDerived",
        "stock",
        "balance-residual-other-net-assets-v1",
        None,
        None,
    ),
    DartFinancialFeatureMapping(
        "financial.equity",
        "equity",
        "observed",
        "stock",
        "latest-filing-instant-v1",
        None,
        None,
    ),
)


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise ValueError(f"invalid {label}: {value}")
    try:
        date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    except ValueError as error:
        raise ValueError(f"invalid {label}: {value}") from error
    return text


def _canonicalHash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def _periodKey(period: str) -> tuple[int, int]:
    year, separator, quarter = str(period).partition("-Q")
    if not separator or not year.isdigit() or quarter not in {"1", "2", "3", "4"}:
        raise ValueError(f"invalid DART fiscal period: {period}")
    return int(year), int(quarter)


def _fiscalEventAt(period: str, fiscalYearEndMonth: int) -> str:
    year, quarter = _periodKey(period)
    monthOffset = (4 - quarter) * 3
    absoluteMonth = year * 12 + fiscalYearEndMonth - 1 - monthOffset
    eventYear, zeroBasedMonth = divmod(absoluteMonth, 12)
    eventMonth = zeroBasedMonth + 1
    eventDay = calendar.monthrange(eventYear, eventMonth)[1]
    return f"{eventYear:04d}{eventMonth:02d}{eventDay:02d}"


def _filingSchedule(
    filings: pl.DataFrame,
    *,
    fiscalYearEndMonth: int,
) -> pl.DataFrame:
    rows: list[dict[str, str]] = []
    for filing in filings.iter_rows(named=True):
        rawYear = str(filing["bsns_year"])
        report = str(filing["reprt_nm"])
        firstReceipt = _dateText(str(filing["__firstReceipt"])[:8], "rcept_no")
        quarter = _QUARTER_BY_REPORT.get(report)
        if not rawYear.isdigit() or quarter is None:
            raise ValueError("DART filing의 사업연도 또는 보고서 분기가 유효하지 않습니다")
        candidates = tuple(
            (
                cycleYear,
                _fiscalEventAt(f"{cycleYear}-Q{quarter}", fiscalYearEndMonth),
            )
            for cycleYear in (int(rawYear), int(rawYear) + 1)
        )
        eligible = tuple(item for item in candidates if item[1] <= firstReceipt)
        if not eligible:
            # 현재 상장 snapshot의 결산월은 과거 결산월 변경 전 filing과 다를 수 있다.
            # 그 행을 현재 결산월로 재라벨링하지 않고 제외한 뒤 최신 coherent window를 찾는다.
            continue
        cycleYear, eventAt = max(eligible, key=lambda item: item[1])
        rows.append(
            {
                "bsns_year": rawYear,
                "reprt_nm": report,
                "fs_div": str(filing["fs_div"]),
                "__cycleYear": str(cycleYear),
                "__eventAt": eventAt,
            }
        )
    if not rows:
        raise ValueError("DART filing 접수일에서 실제 회계 분기말을 복원할 수 없습니다")
    return pl.DataFrame(rows)


def _latestWholeFilings(
    frame: pl.DataFrame,
    *,
    knownAt: str,
    validAt: str | None,
    fiscalYearEndMonth: int,
) -> pl.DataFrame:
    required = {
        "rcept_no",
        "bsns_year",
        "reprt_nm",
        "sj_div",
        "account_id",
        "account_nm",
        "thstrm_amount",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"DART finance source schema missing: {', '.join(sorted(missing))}")
    normalized = frame.with_columns(
        pl.col("rcept_no").cast(pl.Utf8),
        pl.col("bsns_year").cast(pl.Utf8),
        pl.col("reprt_nm").cast(pl.Utf8),
        (pl.col("fs_div").cast(pl.Utf8) if "fs_div" in frame.columns else pl.lit("UNKNOWN").alias("fs_div")),
    )
    normalized = normalized.filter(
        pl.col("rcept_no").str.slice(0, 8).str.contains(r"^\d{8}$")
        & (pl.col("rcept_no").str.slice(0, 8) <= knownAt)
        & pl.col("reprt_nm").is_in(tuple(_QUARTER_BY_REPORT))
    )
    if normalized.is_empty():
        raise ValueError("knownAt 이전 DART finance filing이 없습니다")
    filingKeys = ["bsns_year", "reprt_nm", "fs_div"]
    filings = normalized.group_by(filingKeys).agg(
        pl.col("rcept_no").min().alias("__firstReceipt"),
        pl.col("rcept_no").max().alias("__latestReceipt"),
    )
    schedule = _filingSchedule(filings, fiscalYearEndMonth=fiscalYearEndMonth)
    selected = (
        normalized.join(filings.select(filingKeys + ["__latestReceipt"]), on=filingKeys, how="inner")
        .join(schedule, on=filingKeys, how="inner")
        .filter(pl.col("rcept_no") == pl.col("__latestReceipt"))
        .with_columns(
            pl.col("bsns_year").alias("__sourceBsnsYear"),
            pl.col("__cycleYear").alias("bsns_year"),
        )
        .drop("__latestReceipt", "__cycleYear")
    )
    if validAt is not None:
        selected = selected.filter(pl.col("__eventAt") <= validAt)
    if selected.is_empty():
        raise ValueError("validAt 이전 DART finance filing이 없습니다")
    return selected


def _valueAt(
    series: dict[str, dict[str, list[float | None]]],
    statement: str,
    aliases: tuple[str, ...],
    index: int,
) -> float | None:
    valuesByAccount = series.get(statement, {})
    for alias in aliases:
        values = valuesByAccount.get(alias)
        if values is not None and index < len(values):
            value = values[index]
            if value is not None:
                return float(value)
    return None


def _alignedFlowWindow(
    series: dict[str, dict[str, list[float | None]]],
    periods: list[str],
) -> tuple[str, int, float, float, tuple[str, ...]]:
    candidates: list[tuple[int, int, str, int, float, float]] = []
    for index, period in enumerate(periods):
        revenue = _valueAt(series, "IS", ("sales", "revenue", "net_sales"), index)
        operating = _valueAt(
            series,
            "IS",
            ("operating_profit", "profit_from_operating_activities"),
            index,
        )
        if revenue is None or revenue <= 0 or operating is None:
            continue
        year, quarter = _periodKey(period)
        candidates.append((year, quarter, period, index, revenue, operating))
    byOrdinal = {item[0] * 4 + item[1]: item for item in candidates}
    for latestOrdinal in sorted(byOrdinal, reverse=True):
        window = tuple(byOrdinal.get(latestOrdinal - offset) for offset in range(3, -1, -1))
        if any(item is None for item in window):
            continue
        latest = byOrdinal[latestOrdinal]
        history = tuple(str(item[2]) for item in window if item is not None)
        return str(latest[2]), int(latest[3]), float(latest[4]), float(latest[5]), history
    raise ValueError("연속된 4개 분기의 DART 매출과 영업이익이 필요합니다")


def _financialValues(
    series: dict[str, dict[str, list[float | None]]],
    index: int,
    *,
    revenue: float,
    operatingProfit: float,
) -> dict[str, float]:
    values: dict[str, float] = {
        "revenue": revenue,
        "operatingMargin": operatingProfit / revenue,
    }
    cash = _valueAt(series, "BS", ("cash_and_cash_equivalents",), index)
    receivables = _valueAt(
        series,
        "BS",
        ("trade_and_other_receivables", "trade_receivables", "receivables"),
        index,
    )
    inventories = _valueAt(series, "BS", ("inventories",), index)
    payables = _valueAt(
        series,
        "BS",
        ("trade_and_other_payables", "trade_payables", "payables"),
        index,
    )
    ppe = _valueAt(series, "BS", ("tangible_assets", "property_plant_and_equipment"), index)
    equity = _valueAt(
        series,
        "BS",
        ("total_stockholders_equity", "total_equity", "owners_of_parent_equity"),
        index,
    )
    totalAssets = _valueAt(series, "BS", ("total_assets",), index)
    totalLiabilities = _valueAt(series, "BS", ("total_liabilities",), index)
    if totalAssets is not None and totalLiabilities is not None and equity is not None:
        tolerance = max(1.0, abs(equity) * 1e-8)
        if abs(totalAssets - totalLiabilities - equity) > tolerance:
            raise ValueError("DART consolidated balance identity가 닫히지 않습니다")
    direct = {
        "cash": cash,
        "receivables": receivables,
        "inventories": inventories,
        "payables": payables,
        "ppe": ppe,
        "equity": equity,
    }
    values.update({key: value for key, value in direct.items() if value is not None})

    shortDebt = _valueAt(series, "BS", ("shortterm_borrowings", "short_term_borrowings"), index)
    longDebt = _valueAt(series, "BS", ("longterm_borrowings", "long_term_borrowings"), index)
    currentTerm = _valueAt(series, "BS", ("current_portion_of_longterm_liabilities",), index)
    bonds = _valueAt(series, "BS", ("debentures", "bonds_payable"), index)
    if shortDebt is not None and (longDebt is not None or bonds is not None):
        debt = sum(value for value in (shortDebt, longDebt, currentTerm, bonds) if value is not None)
        values["debt"] = debt
    else:
        debt = None

    if (
        totalAssets is not None
        and totalLiabilities is not None
        and cash is not None
        and receivables is not None
        and inventories is not None
        and payables is not None
        and ppe is not None
        and debt is not None
    ):
        otherAssets = totalAssets - cash - receivables - inventories - ppe
        otherLiabilities = totalLiabilities - payables - debt
        values["otherNetAssets"] = otherAssets - otherLiabilities
    return values


def _currency(frame: pl.DataFrame) -> str:
    if "currency" not in frame.columns:
        raise ValueError("DART finance source에 currency가 없습니다")
    currencies = tuple(
        sorted({str(value).strip().upper() for value in frame["currency"].drop_nulls().to_list() if str(value).strip()})
    )
    if len(currencies) != 1:
        raise ValueError("DART finance filing의 reporting currency가 하나로 정렬되지 않습니다")
    return currencies[0]


def _featureSpecs(currency: str) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "variableId": item.variableId,
            "signalId": item.variableId,
            "providerId": "dart",
            "datasetId": "quarterly-financial",
            "unit": "ratio" if item.timing == "ratio" else currency,
            "role": "observedFeature",
            "evidenceRole": item.evidenceRole,
            "frequency": "quarter",
            "timing": item.timing,
            "transformId": item.transformId,
            "maxStalenessDays": 400,
            "lower": item.lower,
            "upper": item.upper,
        }
        for item in DART_FINANCIAL_FEATURE_MAPPINGS
    )


def _evidencePayload(
    frame: pl.DataFrame,
    *,
    historyPeriods: tuple[str, ...],
    values: dict[str, float],
    fiscalThrough: str,
    currency: str,
    fiscalYearEndMonth: int,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    periods = set(historyPeriods)
    relevant = frame.with_columns(
        (
            pl.col("bsns_year").cast(pl.Utf8)
            + pl.lit("-Q")
            + pl.col("reprt_nm").replace_strict(_QUARTER_BY_REPORT, default=None).cast(pl.Utf8)
        ).alias("__period")
    ).filter(pl.col("__period").is_in(tuple(periods)))
    columns = [column for column in _EVIDENCE_COLUMNS if column in relevant.columns]
    sortColumns = [
        column for column in ("rcept_no", "sj_div", "fs_div", "account_id", "account_nm") if column in columns
    ]
    evidence = relevant.select(columns).sort(sortColumns).to_dicts()
    sourceRefs = tuple(
        f"dart:{receipt}" for receipt in sorted({str(value) for value in relevant["rcept_no"].drop_nulls().to_list()})
    )
    return (
        {
            "schemaVersion": "dart-quarterly-financial-evidence-v1",
            "fiscalThrough": fiscalThrough,
            "reportingCurrency": currency,
            "fiscalYearEndMonth": fiscalYearEndMonth,
            "frequency": "quarter",
            "values": values,
            "evidence": evidence,
            "normalizationRuleHash": DART_FINANCIAL_FEATURE_NORMALIZATION_HASH,
        },
        sourceRefs,
    )


def buildDartFinancialFeatureInput(
    finance: pl.DataFrame,
    *,
    entityId: str,
    knownAt: str,
    validAt: str | None = None,
    fiscalYearEndMonth: int,
) -> dict[str, Any]:
    """DART finance 원장을 cutoff-stable quarterly feature envelope로 만든다.

    Args:
        finance: 한 회사의 검증된 DART finance 원천 행.
        entityId: ``KR:6자리 영숫자 종목코드`` 형태의 canonical identity.
        knownAt: 허용할 접수 지식 시점.
        validAt: 선택할 수 있는 마지막 회계 사건 시점.
        fiscalYearEndMonth: 해당 회사의 회계연도 말 월.

    Returns:
        Data Workbench가 검증할 ``feature-observation-input-v1`` mapping.

    Raises:
        ValueError: Entity, 시간, 원천, 통화 또는 연속 분기 상태가 잘못된 경우.

    Example:
        ``buildDartFinancialFeatureInput(frame, entityId="KR:005930", knownAt="20250520", fiscalYearEndMonth=12)``.
    """

    market, separator, code = str(entityId).partition(":")
    if (
        separator != ":"
        or market != "KR"
        or len(code) != 6
        or not code.isascii()
        or not code.isalnum()
        or code != code.upper()
    ):
        raise ValueError("DART feature entityId는 KR:6자리 영숫자 종목코드 형식이어야 합니다")
    cutoff = _dateText(knownAt, "knownAt")
    valid = _dateText(validAt, "validAt") if validAt is not None else None
    if not isinstance(fiscalYearEndMonth, int) or not 1 <= fiscalYearEndMonth <= 12:
        raise ValueError("fiscalYearEndMonth는 1부터 12 사이 정수여야 합니다")
    selected = _latestWholeFilings(
        finance,
        knownAt=cutoff,
        validAt=valid,
        fiscalYearEndMonth=fiscalYearEndMonth,
    )
    timeseries = buildTimeseriesFromFrame(selected, stockCode=code)
    if timeseries is None:
        raise ValueError("DART finance filing을 분기 시계열로 정규화할 수 없습니다")
    series, periods = timeseries
    fiscalPeriod, index, revenue, operatingProfit, history = _alignedFlowWindow(series, periods)
    fiscalThrough = _fiscalEventAt(fiscalPeriod, fiscalYearEndMonth)
    values = _financialValues(
        series,
        index,
        revenue=revenue,
        operatingProfit=operatingProfit,
    )
    currency = _currency(selected)
    evidencePayload, sourceRefs = _evidencePayload(
        selected,
        historyPeriods=history,
        values=values,
        fiscalThrough=fiscalThrough,
        currency=currency,
        fiscalYearEndMonth=fiscalYearEndMonth,
    )
    evidenceHash = _canonicalHash(evidencePayload)
    relevantReceipts = (
        selected.with_columns(
            (
                pl.col("bsns_year").cast(pl.Utf8)
                + pl.lit("-Q")
                + pl.col("reprt_nm").replace_strict(_QUARTER_BY_REPORT, default=None).cast(pl.Utf8)
            ).alias("__period")
        )
        .filter(pl.col("__period").is_in(history))["rcept_no"]
        .drop_nulls()
    )
    availableAt = max(_dateText(str(value)[:8], "rcept_no") for value in relevantReceipts.to_list())
    vintage = {
        "artifactKind": "dartCompiledFinancialEvidence",
        "provider": "dart",
        "artifactId": f"{entityId}:{fiscalThrough}:{evidenceHash}",
        "artifactHash": evidenceHash,
        "payloadHash": evidenceHash,
        "knowledgeAsOf": availableAt,
        "availableAt": availableAt,
        "revisionPolicy": "latestRetained",
        "coverage": "periodOnly",
        "fiscalThrough": fiscalThrough,
        "contractHash": DART_FINANCIAL_FEATURE_NORMALIZATION_HASH,
        "sourceRefs": sourceRefs,
    }
    observations = tuple(
        {
            "providerId": "dart",
            "datasetId": "quarterly-financial",
            "entityId": entityId,
            "signalId": item.variableId,
            "value": float(values[item.fieldName]),
            "unit": "ratio" if item.timing == "ratio" else currency,
            "frequency": "quarter",
            "timing": item.timing,
            "transformId": item.transformId,
            "evidenceRole": item.evidenceRole,
            "eventAt": fiscalThrough,
            "availableAt": availableAt,
            "knowledgeAsOf": availableAt,
            "availabilityPrecision": "date",
            "revisionId": evidenceHash,
            "vintage": vintage,
            "normalizationRuleHash": DART_FINANCIAL_FEATURE_NORMALIZATION_HASH,
        }
        for item in DART_FINANCIAL_FEATURE_MAPPINGS
        if item.fieldName in values
    )
    return {
        "schemaVersion": "feature-observation-input-v1",
        "specs": _featureSpecs(currency),
        "observations": observations,
    }


__all__ = [
    "DART_FINANCIAL_FEATURE_MAPPINGS",
    "DART_FINANCIAL_FEATURE_NORMALIZATION_HASH",
    "DartFinancialFeatureMapping",
    "buildDartFinancialFeatureInput",
]
