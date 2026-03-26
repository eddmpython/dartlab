"""재무 데이터 처리 헬퍼.

company.py에서 분리된 모듈-레벨 헬퍼.
_financeToDataFrame, _ratioSeriesToDataFrame 등이 핵심.
"""

from __future__ import annotations

from typing import Any

import polars as pl

_RATIO_CATEGORY_LABELS: dict[str, str] = {
    "profitability": "수익성",
    "stability": "안정성",
    "growth": "성장성",
    "efficiency": "효율성",
    "cashflow": "현금흐름",
    "composite": "복합지표",
    "absolute": "절대규모",
}

_RATIO_FIELD_LABELS: dict[str, str] = {
    "roe": "ROE (%)",
    "roa": "ROA (%)",
    "operatingMargin": "영업이익률 (%)",
    "netMargin": "순이익률 (%)",
    "grossMargin": "매출총이익률 (%)",
    "ebitdaMargin": "EBITDA마진 (%)",
    "costOfSalesRatio": "매출원가율 (%)",
    "sgaRatio": "판관비율 (%)",
    "debtRatio": "부채비율 (%)",
    "currentRatio": "유동비율 (%)",
    "quickRatio": "당좌비율 (%)",
    "equityRatio": "자기자본비율 (%)",
    "interestCoverage": "이자보상배율 (x)",
    "netDebtRatio": "순차입금비율 (%)",
    "noncurrentRatio": "비유동비율 (%)",
    "revenueGrowth": "매출 YoY (%)",
    "operatingProfitGrowth": "영업이익 YoY (%)",
    "netProfitGrowth": "순이익 YoY (%)",
    "assetGrowth": "자산 YoY (%)",
    "equityGrowthRate": "자본 YoY (%)",
    "totalAssetTurnover": "총자산회전율 (x)",
    "inventoryTurnover": "재고자산회전율 (x)",
    "receivablesTurnover": "매출채권회전율 (x)",
    "payablesTurnover": "매입채무회전율 (x)",
    "fcf": "FCF",
    "operatingCfMargin": "영업CF마진 (%)",
    "operatingCfToNetIncome": "영업CF/순이익 (%)",
    "capexRatio": "CAPEX비율 (%)",
    "dividendPayoutRatio": "배당성향 (%)",
    "revenue": "매출",
    "operatingProfit": "영업이익",
    "netProfit": "순이익",
    "totalAssets": "총자산",
    "totalEquity": "자본(지배)",
    "operatingCashflow": "영업현금흐름",
    "roic": "ROIC (%)",
    "dupontMargin": "DuPont 순이익률 (%)",
    "dupontTurnover": "DuPont 회전율 (x)",
    "dupontLeverage": "DuPont 레버리지 (x)",
    "debtToEbitda": "Debt/EBITDA (x)",
    "ccc": "현금전환주기 (일)",
    "dso": "매출채권회수기간 (일)",
    "dio": "재고보유기간 (일)",
    "dpo": "매입채무지급기간 (일)",
    "piotroskiFScore": "F-Score (0~9)",
    "altmanZScore": "Z-Score",
}


_RATIO_TEMPLATE_FIELDS: dict[str, tuple[str, ...]] = {
    "bank": (
        "roe",
        "roa",
        "equityRatio",
        "operatingProfitGrowth",
        "netProfitGrowth",
        "assetGrowth",
        "equityGrowthRate",
        "dividendPayoutRatio",
        "operatingProfit",
        "netProfit",
        "totalAssets",
        "totalEquity",
        "operatingCashflow",
    ),
    "insurance": (
        "roe",
        "roa",
        "equityRatio",
        "operatingProfitGrowth",
        "netProfitGrowth",
        "assetGrowth",
        "equityGrowthRate",
        "dividendPayoutRatio",
        "operatingProfit",
        "netProfit",
        "totalAssets",
        "totalEquity",
        "operatingCashflow",
    ),
    "diversified_financials": (
        "roe",
        "roa",
        "operatingMargin",
        "netMargin",
        "ebitdaMargin",
        "equityRatio",
        "revenueGrowth",
        "operatingProfitGrowth",
        "netProfitGrowth",
        "assetGrowth",
        "equityGrowthRate",
        "totalAssetTurnover",
        "dividendPayoutRatio",
        "revenue",
        "operatingProfit",
        "netProfit",
        "totalAssets",
        "totalEquity",
        "operatingCashflow",
    ),
}


def _financeToDataFrame(
    series: dict[str, dict[str, list]],
    years: list[str],
    sjDiv: str,
) -> pl.DataFrame | None:
    """finance 연도별 시계열 → 한글 계정명 × 연도 컬럼 DataFrame."""
    stmtData = series.get(sjDiv)
    if not stmtData:
        return None

    from dartlab.providers.dart.finance.mapper import AccountMapper

    mapper = AccountMapper.get()
    labels = mapper.labelMap()
    order = mapper.sortOrder(sjDiv)
    levels = mapper.levelMap(sjDiv)

    rows = []
    for snakeId, values in stmtData.items():
        label = labels.get(snakeId, snakeId)
        level = levels.get(snakeId, 2)
        sortKey = order.get(snakeId, 9999)
        row = {"snakeId": snakeId, "계정명": label, "_level": level, "_sort": sortKey}
        for i, y in enumerate(years):
            row[y] = values[i] if i < len(values) else None
        rows.append(row)

    if not rows:
        return None

    rows.sort(key=lambda r: r["_sort"])
    df = pl.DataFrame(rows)
    df = df.drop(["_level", "_sort"])
    # 기간 컬럼을 최신 먼저 역순으로 정렬
    periodCols = [c for c in df.columns if c not in ("snakeId", "계정명")]
    df = df.select(["snakeId", "계정명"] + periodCols[::-1])
    return df


def _ratioTemplateKeyForIndustryGroup(industryGroup: Any) -> str | None:
    if industryGroup is None:
        return None

    try:
        from dartlab.analysis.comparative.sector.types import IndustryGroup
    except ImportError:
        return None

    mapping = {
        IndustryGroup.BANK: "bank",
        IndustryGroup.INSURANCE: "insurance",
        IndustryGroup.DIVERSIFIED_FINANCIALS: "diversified_financials",
    }
    return mapping.get(industryGroup)


def _ratioArchetypeOverrideForIndustryGroup(industryGroup: Any) -> str | None:
    if industryGroup is None:
        return None

    try:
        from dartlab.analysis.comparative.sector.types import IndustryGroup
    except ImportError:
        return None

    mapping = {
        IndustryGroup.BANK: "bank",
        IndustryGroup.INSURANCE: "insurance",
        IndustryGroup.DIVERSIFIED_FINANCIALS: "securities",
    }
    return mapping.get(industryGroup)


def _ratioResultHasHeadlineSignal(result: Any) -> bool:
    if result is None:
        return False

    headlineFields = (
        "roe",
        "roa",
        "operatingMargin",
        "netMargin",
        "debtRatio",
        "currentRatio",
        "equityRatio",
        "revenueTTM",
        "netIncomeTTM",
    )
    return any(getattr(result, fieldName, None) is not None for fieldName in headlineFields)


def _shouldFallbackToAnnualRatios(result: Any, archetypeOverride: str | None) -> bool:
    if result is None:
        return True

    if archetypeOverride in {"bank", "insurance", "securities"}:
        profitabilityFields = ("roe", "roa", "operatingMargin", "netMargin")
        return not any(getattr(result, fieldName, None) is not None for fieldName in profitabilityFields)

    return not _ratioResultHasHeadlineSignal(result)


def _ratioSeriesToDataFrame(
    series: dict[str, dict[str, list[Any | None]]],
    years: list[str],
    fieldNames: tuple[str, ...] | None = None,
) -> pl.DataFrame | None:
    """재무비율 연도별 시계열 → 분류/항목 × 연도 컬럼 DataFrame."""
    ratioData = series.get("RATIO")
    if not ratioData:
        return None

    from dartlab.core.finance.ratios import RATIO_CATEGORIES

    fieldFilter = set(fieldNames) if fieldNames is not None else None
    rows: list[dict[str, Any]] = []
    for category, fields in RATIO_CATEGORIES:
        for fieldName in fields:
            if fieldFilter is not None and fieldName not in fieldFilter:
                continue
            values = ratioData.get(fieldName)
            if not values or not any(v is not None for v in values):
                continue
            row = {
                "분류": _RATIO_CATEGORY_LABELS.get(category, category),
                "항목": _RATIO_FIELD_LABELS.get(fieldName, fieldName),
                "_field": fieldName,
            }
            for idx, year in enumerate(years):
                row[str(year)] = values[idx] if idx < len(values) else None
            rows.append(row)

    if not rows:
        return None

    df = pl.DataFrame(rows)
    return df.drop("_field")


def _sceToDataFrame(
    series: dict[str, dict[str, list]],
    years: list[str],
) -> pl.DataFrame | None:
    """SCE 연도별 시계열 → 항목 × 연도 컬럼 DataFrame."""
    from dartlab.providers.dart.finance.sceMapper import CAUSE_LABELS, DETAIL_LABELS

    stmtData = series.get("SCE")
    if not stmtData:
        return None

    rows = []
    for item, values in stmtData.items():
        cause, _, detail = item.partition("__")
        causeKr = CAUSE_LABELS.get(cause)
        if causeKr is None:
            baseCause, _, suffix = cause.partition("_")
            baseKr = CAUSE_LABELS.get(baseCause, baseCause)
            suffixKr = suffix.replace("_", " ") if suffix else ""
            causeKr = f"{baseKr}({suffixKr})" if suffixKr else baseKr
        detailKr = DETAIL_LABELS.get(detail, detail) if detail else ""
        label = f"{causeKr} / {detailKr}" if detailKr else causeKr
        row = {
            "계정명": label,
            "_cause": cause,
            "_detail": detail,
            "_sort": item,
        }
        for i, y in enumerate(years):
            row[y] = values[i] if i < len(values) else None
        rows.append(row)

    if not rows:
        return None

    rows.sort(key=lambda r: (r["_cause"], r["_detail"], r["_sort"]))
    df = pl.DataFrame(rows)
    return df.drop(["_cause", "_detail", "_sort"])


def _buildCisSeries(df: pl.DataFrame, periods: list[str], formatPeriod) -> dict[str, list[Any | None]]:
    """CIS DataFrame에서 snakeId → 기간별 값 시리즈 추출 (공통 헬퍼)."""
    from dartlab.providers.dart.finance.mapper import AccountMapper

    periodIdx = {p: i for i, p in enumerate(periods)}
    mapper = AccountMapper.get()
    qSeries: dict[str, list[Any | None]] = {}

    _QUARTER_MAP = {"1분기": 1, "2분기": 2, "3분기": 3, "4분기": 4}
    _accIds = df["account_id"].to_list()
    _accNms = df["account_nm"].to_list()
    _bsnsYears = df["bsns_year"].to_list() if "bsns_year" in df.columns else [None] * df.height
    _reprtNms = df["reprt_nm"].to_list() if "reprt_nm" in df.columns else [None] * df.height
    _amounts = df["_normalized_amount"].to_list() if "_normalized_amount" in df.columns else [None] * df.height

    for i in range(df.height):
        accountId = _accIds[i] or ""
        accountNm = _accNms[i] or ""
        snakeId = mapper.map(accountId, accountNm)
        if snakeId is None:
            continue

        pKey = formatPeriod(_bsnsYears[i] or "", _QUARTER_MAP.get(_reprtNms[i] or "", 0))
        idx = periodIdx.get(pKey)
        if idx is None:
            continue

        if snakeId not in qSeries:
            qSeries[snakeId] = [None] * len(periods)
        if qSeries[snakeId][idx] is None:
            qSeries[snakeId][idx] = _amounts[i]

    return qSeries


def _financeCisAnnual(stockCode: str, fsDivPref: str = "CFS") -> tuple[dict[str, dict[str, list]], list[str]] | None:
    """finance 원본에서 CIS 연도별 시계열 생성."""
    from dartlab.core.finance.period import extractYear, formatPeriod
    from dartlab.providers.dart.finance.pivot import _loadAndNormalize

    result = _loadAndNormalize(stockCode, fsDivPref)
    if result is None:
        return None

    df, periods = result
    df = df.filter(pl.col("sj_div") == "CIS")
    if df.is_empty():
        return None

    qSeries = _buildCisSeries(df, periods, formatPeriod)

    yearSet: dict[str, list[int]] = {}
    for i, p in enumerate(periods):
        yearSet.setdefault(extractYear(p), []).append(i)

    years = sorted(yearSet.keys())
    annualSeries: dict[str, list[Any | None]] = {}
    for snakeId, vals in qSeries.items():
        annualVals: list[Any | None] = [None] * len(years)
        for yIdx, year in enumerate(years):
            qVals = [vals[qi] for qi in yearSet[year] if qi < len(vals) and vals[qi] is not None]
            annualVals[yIdx] = sum(qVals) if qVals else None
        annualSeries[snakeId] = annualVals

    return {"CIS": annualSeries}, years


def _financeCisQuarterly(stockCode: str, fsDivPref: str = "CFS") -> tuple[dict[str, dict[str, list]], list[str]] | None:
    """finance 원본에서 CIS 분기별 시계열 생성 (연간 합산 없이)."""
    from dartlab.core.finance.period import formatPeriod
    from dartlab.providers.dart.finance.pivot import _loadAndNormalize

    result = _loadAndNormalize(stockCode, fsDivPref)
    if result is None:
        return None

    df, periods = result
    df = df.filter(pl.col("sj_div") == "CIS")
    if df.is_empty():
        return None

    qSeries = _buildCisSeries(df, periods, formatPeriod)

    return {"CIS": qSeries}, periods
