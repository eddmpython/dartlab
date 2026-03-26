"""EDINET finance pivot — raw XBRL parquet → 시계열 dict.

Axiora context priority 로직 적용:
1. 연결(Consolidated) 우선 — 연결 데이터가 있으면 개별(NonConsolidated) 무시
2. context_id에서 기간(year/quarter) + 시점(duration/instant) 파싱
3. 회계표준 감지 (J-GAAP / IFRS / US-GAAP)

출력 형식은 DART/EDGAR와 동일한 {sjDiv: {snakeId: [values...]}} dict.
"""

from __future__ import annotations

import re
from typing import Any, Optional

import polars as pl

from dartlab.providers.edinet.finance.mapper import EdinetMapper

# ── context_id 파싱 ──────────────────────────────────────────────

# EDINET context_id 패턴 예시:
# CurrentYearDuration
# CurrentYearDuration_ConsolidatedMember
# CurrentYearDuration_NonConsolidatedMember
# Prior1YearDuration_ConsolidatedMember
# CurrentYearInstant
# CurrentQuarter2Duration_ConsolidatedMember

_RE_PERIOD = re.compile(
    r"(?P<relative>Current|Prior\d+)"
    r"(?:Year|Quarter(?P<quarter>\d+)?)"
    r"(?P<temporal>Duration|Instant)",
    re.IGNORECASE,
)

_RE_CONSOLIDATED = re.compile(r"_(Consolidated|NonConsolidated)Member", re.IGNORECASE)


def _parseContext(contextId: str) -> dict[str, Any]:
    """context_id → {relative, quarter, temporal, consolidated} 파싱."""
    result: dict[str, Any] = {
        "relative": None,
        "quarter": None,
        "temporal": None,
        "consolidated": None,  # True=연결, False=개별, None=구분없음
    }
    if not contextId:
        return result

    m = _RE_PERIOD.search(contextId)
    if m:
        result["relative"] = m.group("relative").lower()
        result["quarter"] = int(m.group("quarter")) if m.group("quarter") else None
        result["temporal"] = m.group("temporal").lower()

    cm = _RE_CONSOLIDATED.search(contextId)
    if cm:
        result["consolidated"] = cm.group(1).lower() == "consolidated"

    return result


# ── 회계표준 감지 ────────────────────────────────────────────────


def detectAccountingStandard(elementIds: list[str]) -> str:
    """element_id prefix로 회계표준 감지.

    Returns: 'J-GAAP', 'IFRS', 'US-GAAP', 'unknown'
    """
    counts = {"jppfs": 0, "jpcrp": 0, "ifrs": 0, "usgaap": 0}
    for eid in elementIds:
        lower = eid.lower()
        if lower.startswith("jppfs_") or lower.startswith("jpcrp_"):
            counts["jppfs"] += 1
        elif lower.startswith("ifrs") or lower.startswith("ifrs-full_"):
            counts["ifrs"] += 1
        elif lower.startswith("us-gaap_") or lower.startswith("usgaap_"):
            counts["usgaap"] += 1

    total_jp = counts["jppfs"] + counts["jpcrp"]
    if counts["ifrs"] > total_jp and counts["ifrs"] > counts["usgaap"]:
        return "IFRS"
    if counts["usgaap"] > total_jp and counts["usgaap"] > counts["ifrs"]:
        return "US-GAAP"
    return "J-GAAP"


# ── 재무제표 분류 ────────────────────────────────────────────────

# J-GAAP element → 재무제표 유형 매핑
_STMT_KEYWORDS = {
    "BS": [
        "Assets",
        "Liabilities",
        "Equity",
        "NetAssets",
        "資産",
        "負債",
        "純資産",
        "資本",
    ],
    "IS": [
        "Revenue",
        "Sales",
        "OperatingIncome",
        "NetIncome",
        "Profit",
        "Loss",
        "売上",
        "営業利益",
        "当期純利益",
        "経常利益",
    ],
    "CF": [
        "CashFlow",
        "OperatingActivities",
        "InvestingActivities",
        "FinancingActivities",
        "営業活動",
        "投資活動",
        "財務活動",
    ],
}


def _classifyStatement(elementId: str, accountName: str) -> str | None:
    """element_id + account_name에서 재무제표 유형 추론."""
    combined = elementId + " " + accountName
    for sjDiv, keywords in _STMT_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in combined.lower():
                return sjDiv
    return None


# ── Context Priority — Axiora 방식 ──────────────────────────────


def _applyContextPriority(
    df: pl.DataFrame,
    preferConsolidated: bool = True,
) -> pl.DataFrame:
    """연결/개별 우선순위 적용.

    Axiora의 핵심 로직:
    - 같은 (element_id, period)에 연결과 개별이 모두 있으면 연결 우선
    - 연결만 있거나 개별만 있으면 그대로 사용
    - context_id에 연결/개별 구분이 없으면 연결로 간주

    Args:
        df: context_id 파싱 완료된 DataFrame.
        preferConsolidated: True면 연결 우선 (기본값).
    """
    if "consolidated" not in df.columns:
        return df

    # consolidated 컬럼이 전부 null이면 (구분 없는 경우) 그대로 반환
    if df["consolidated"].null_count() == len(df):
        return df

    # null은 연결로 간주 (단독 기업이 아닌 한 연결이 기본)
    df = df.with_columns(pl.col("consolidated").fill_null(preferConsolidated))

    # 우선순위: preferConsolidated면 True 우선 (0), 아니면 False 우선 (0)
    priority_val = preferConsolidated
    df = df.with_columns(pl.when(pl.col("consolidated") == priority_val).then(0).otherwise(1).alias("_csPriority"))

    # 같은 (element_id, period_key)에서 우선순위 높은 행만 남김
    df = (
        df.sort(["element_id", "period_key", "_csPriority"])
        .unique(subset=["element_id", "period_key"], keep="first")
        .drop("_csPriority")
    )

    return df


# ── 메인 피벗 ────────────────────────────────────────────────────


def buildTimeseries(
    financeDf: pl.DataFrame,
    preferConsolidated: bool = True,
) -> tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]:
    """finance parquet → 시계열 dict.

    Args:
        financeDf: finance parquet (element_id, account_name, context_id, value, unit).
        preferConsolidated: 연결 우선 여부 (기본 True).

    Returns:
        (series, periods) 튜플.
        series = {"BS": {"total_assets": [v1, v2, ...], ...}, "IS": {...}, "CF": {...}}
        periods = ["prior2", "prior1", "current"] 등
    """
    if financeDf.is_empty():
        return {}, []

    mapper = EdinetMapper

    # 1. context_id 파싱
    rows: list[dict[str, Any]] = []
    for row in financeDf.iter_rows(named=True):
        elementId = row.get("element_id", "")
        accountName = row.get("account_name", "")
        contextId = row.get("context_id", "")
        value = row.get("value")

        if value is None:
            continue

        # 숫자 변환
        try:
            numVal = float(value)
        except (ValueError, TypeError):
            continue

        ctx = _parseContext(contextId)
        if ctx["relative"] is None:
            continue

        # snakeId 매핑
        snakeId = mapper.map(elementId, accountName)
        if snakeId is None:
            continue

        # 재무제표 분류
        sjDiv = _classifyStatement(elementId, accountName)
        if sjDiv is None:
            continue

        # period 키 생성
        periodKey = ctx["relative"]
        if ctx["quarter"]:
            periodKey += f"Q{ctx['quarter']}"
        if ctx["temporal"] == "instant":
            periodKey += "End"

        rows.append(
            {
                "element_id": elementId,
                "snakeId": snakeId,
                "sjDiv": sjDiv,
                "period_key": periodKey,
                "temporal": ctx["temporal"],
                "consolidated": ctx["consolidated"],
                "value": numVal,
            }
        )

    if not rows:
        return {}, []

    df = pl.DataFrame(rows)

    # 2. Context Priority 적용 (Axiora 방식)
    df = _applyContextPriority(df, preferConsolidated=preferConsolidated)

    # 3. 기간 정렬
    # prior2 < prior1 < current 순서
    periodOrder = {
        "prior2": 0,
        "prior2End": 0,
        "prior1": 1,
        "prior1End": 1,
        "current": 2,
        "currentEnd": 2,
        "prior2Q1": 0,
        "prior2Q2": 0,
        "prior2Q3": 0,
        "prior1Q1": 1,
        "prior1Q2": 1,
        "prior1Q3": 1,
        "currentQ1": 2,
        "currentQ2": 2,
        "currentQ3": 2,
    }

    # BS는 instant, IS/CF는 duration
    bsDf = df.filter(pl.col("sjDiv") == "BS")
    flowDf = df.filter(pl.col("sjDiv").is_in(["IS", "CF"]))

    # BS: instant만, IS/CF: duration만
    bsDf = bsDf.filter(pl.col("temporal") == "instant")
    flowDf = flowDf.filter(pl.col("temporal") == "duration")

    # period 순서 결정
    allPeriods = sorted(
        set(bsDf["period_key"].unique().to_list() + flowDf["period_key"].unique().to_list()),
        key=lambda p: periodOrder.get(p, 99),
    )

    if not allPeriods:
        return {}, []

    # 4. 피벗: sjDiv × snakeId × period → value
    series: dict[str, dict[str, list[Optional[float]]]] = {}

    for sjDiv, subDf in [
        ("BS", bsDf),
        ("IS", flowDf.filter(pl.col("sjDiv") == "IS")),
        ("CF", flowDf.filter(pl.col("sjDiv") == "CF")),
    ]:
        if subDf.is_empty():
            continue

        snakeIds = subDf["snakeId"].unique().sort().to_list()
        sjSeries: dict[str, list[Optional[float]]] = {}

        for sid in snakeIds:
            sidDf = subDf.filter(pl.col("snakeId") == sid)
            vals: list[Optional[float]] = []
            for period in allPeriods:
                pRows = sidDf.filter(pl.col("period_key") == period)
                if len(pRows) > 0:
                    vals.append(pRows["value"][0])
                else:
                    vals.append(None)
            if any(v is not None for v in vals):
                sjSeries[sid] = vals

        if sjSeries:
            series[sjDiv] = sjSeries

    return series, allPeriods


def getAccountingStandard(financeDf: pl.DataFrame) -> str:
    """finance parquet에서 회계표준 감지."""
    if financeDf.is_empty():
        return "unknown"
    elementIds = financeDf["element_id"].unique().to_list()
    return detectAccountingStandard(elementIds)


def getConsolidationInfo(financeDf: pl.DataFrame) -> dict[str, int]:
    """finance parquet의 연결/개별 데이터 분포 확인.

    Returns:
        {"consolidated": N, "nonConsolidated": M, "unknown": K}
    """
    counts = {"consolidated": 0, "nonConsolidated": 0, "unknown": 0}
    for ctx in financeDf["context_id"].unique().to_list():
        parsed = _parseContext(ctx)
        if parsed["consolidated"] is True:
            counts["consolidated"] += 1
        elif parsed["consolidated"] is False:
            counts["nonConsolidated"] += 1
        else:
            counts["unknown"] += 1
    return counts
