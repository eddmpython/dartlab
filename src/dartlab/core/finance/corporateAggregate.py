"""기업집계 매크로 지표 — scan finance.parquet 기반 bottom-up 집계.

순수 집계 함수. Polars DataFrame 입력 → 매크로 지표 출력.
core/ 계층 소속 — macro/corporate에서 소비.

Bloomberg/FactSet에서나 가능한 전종목 재무제표 → 매크로 지표 집계를
dartlab scan 데이터로 무료 제공.
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl


# ══════════════════════════════════════
# 데이터 구조
# ══════════════════════════════════════


@dataclass(frozen=True)
class EarningsCycleResult:
    """전종목 이익 사이클."""

    periods: list[str]
    totalOperatingIncome: list[float]  # 기간별 영업이익 합계
    yoyChanges: list[float | None]  # YoY 변화율 (%)
    currentDirection: str  # "expanding" | "stable" | "contracting"
    currentLabel: str
    companyCount: int
    description: str


@dataclass(frozen=True)
class PonziRatioResult:
    """Minsky Ponzi 비율 (ICR<1 기업 비중)."""

    periods: list[str]
    ratios: list[float]  # 기간별 ICR<1 비중 (0-1)
    currentRatio: float
    trend: str  # "rising" | "stable" | "falling"
    trendLabel: str  # "상승" | "안정" | "하락"
    description: str


@dataclass(frozen=True)
class LeverageCycleResult:
    """전종목 레버리지 사이클."""

    periods: list[str]
    medianDebtRatio: list[float]  # 기간별 부채비율 중간값 (%)
    currentLevel: float
    trend: str  # "rising" | "stable" | "falling"
    trendLabel: str
    description: str


# ══════════════════════════════════════
# 내부 헬퍼
# ══════════════════════════════════════

# 계정명 패턴 (DART scan finance.parquet 기준)
_OP_INCOME_NAMES = {"영업이익", "영업이익(손실)", "영업이익 (손실)", "Ⅳ. 영업이익", "Ⅴ.영업이익(손실)", "V. 영업이익"}
_NET_INCOME_NAMES = {"당기순이익", "당기순이익(손실)"}
_TOTAL_DEBT_NAMES = {"부채총계"}
_TOTAL_EQUITY_NAMES = {"자본총계"}
_INTEREST_EXPENSE_PATTERNS = ["이자비용", "금융비용", "금융원가"]


def _extract_annual_consolidated(df: pl.DataFrame) -> pl.DataFrame:
    """연결재무제표 + 4분기(연간) 데이터만 추출."""
    return df.filter((pl.col("fs_nm") == "연결재무제표") & (pl.col("reprt_nm") == "4분기"))


def _sum_account(
    annual: pl.DataFrame,
    sj_div: str,
    account_names: set[str],
) -> pl.DataFrame:
    """특정 계정의 기간별 합계."""
    filtered = annual.filter((pl.col("sj_div") == sj_div) & (pl.col("account_nm").is_in(account_names)))
    # thstrm_amount가 당기 금액
    return (
        filtered.group_by("bsns_year")
        .agg(
            pl.col("thstrm_amount").cast(pl.Float64, strict=False).sum().alias("total"),
            pl.col("stockCode").n_unique().alias("count"),
        )
        .sort("bsns_year")
    )


def _median_ratio(
    annual: pl.DataFrame,
    numer_names: set[str],
    denom_names: set[str],
    sj_div: str = "BS",
) -> pl.DataFrame:
    """특정 비율의 기간별 중간값."""
    numer = annual.filter((pl.col("sj_div") == sj_div) & (pl.col("account_nm").is_in(numer_names))).select(
        "bsns_year", "stockCode", pl.col("thstrm_amount").cast(pl.Float64, strict=False).alias("numer")
    )

    denom = annual.filter((pl.col("sj_div") == sj_div) & (pl.col("account_nm").is_in(denom_names))).select(
        "bsns_year", "stockCode", pl.col("thstrm_amount").cast(pl.Float64, strict=False).alias("denom")
    )

    joined = numer.join(denom, on=["bsns_year", "stockCode"], how="inner")
    joined = joined.filter(pl.col("denom").abs() > 0)
    joined = joined.with_columns((pl.col("numer") / pl.col("denom") * 100).alias("ratio"))

    return joined.group_by("bsns_year").agg(pl.col("ratio").median().alias("median_ratio")).sort("bsns_year")


# ══════════════════════════════════════
# 공개 함수
# ══════════════════════════════════════


def aggregateEarningsCycle(financeDf: pl.DataFrame) -> EarningsCycleResult:
    """전종목 영업이익 합계 YoY → 이익 사이클.

    Args:
        financeDf: scan/finance.parquet 전체 DataFrame
    """
    annual = _extract_annual_consolidated(financeDf)
    result = _sum_account(annual, "IS", _OP_INCOME_NAMES)

    if len(result) < 2:
        return EarningsCycleResult([], [], [], "stable", "데이터부족", 0, "연간 영업이익 데이터 부족")

    periods = result.get_column("bsns_year").to_list()
    totals = result.get_column("total").to_list()
    counts = result.get_column("count").to_list()

    # YoY
    yoys: list[float | None] = [None]
    for i in range(1, len(totals)):
        if totals[i - 1] and abs(totals[i - 1]) > 0:
            yoys.append(round(((totals[i] - totals[i - 1]) / abs(totals[i - 1])) * 100, 1))
        else:
            yoys.append(None)

    # 방향
    last_yoy = yoys[-1]
    if last_yoy is not None and last_yoy > 5:
        direction, label = "expanding", "이익확장"
    elif last_yoy is not None and last_yoy < -5:
        direction, label = "contracting", "이익수축"
    else:
        direction, label = "stable", "안정"

    return EarningsCycleResult(
        periods=periods,
        totalOperatingIncome=[round(t / 1e8, 0) if t else 0 for t in totals],  # 억원 단위
        yoyChanges=yoys,
        currentDirection=direction,
        currentLabel=label,
        companyCount=counts[-1] if counts else 0,
        description=f"전종목 영업이익 {label} (YoY {last_yoy:+.1f}%, {counts[-1] if counts else 0}개사)"
        if last_yoy
        else "데이터 부족",
    )


def ponziRatio(financeDf: pl.DataFrame) -> PonziRatioResult:
    """ICR<1 기업 비중 추이 → Minsky Ponzi 비율.

    ICR(이자보상배율) = 영업이익 / 이자비용.
    ICR < 1 = 영업이익으로 이자도 못 갚는 기업.
    """
    annual = _extract_annual_consolidated(financeDf)

    # 영업이익
    op = annual.filter((pl.col("sj_div") == "IS") & (pl.col("account_nm").is_in(_OP_INCOME_NAMES))).select(
        "bsns_year", "stockCode", pl.col("thstrm_amount").cast(pl.Float64, strict=False).alias("op_income")
    )

    # 이자비용 — account_nm에 "이자비용" 또는 "금융비용" 포함
    interest = annual.filter(
        (pl.col("sj_div") == "IS") & pl.col("account_nm").str.contains("이자비용|금융비용|금융원가")
    ).select("bsns_year", "stockCode", pl.col("thstrm_amount").cast(pl.Float64, strict=False).abs().alias("interest"))

    # 종목별 ICR
    joined = op.join(interest, on=["bsns_year", "stockCode"], how="inner")
    joined = joined.filter(pl.col("interest") > 0)
    joined = joined.with_columns((pl.col("op_income") / pl.col("interest")).alias("icr"))

    # 기간별 ICR<1 비중
    by_year = (
        joined.group_by("bsns_year")
        .agg(
            (pl.col("icr") < 1).sum().alias("ponzi_count"),
            pl.len().alias("total"),
        )
        .sort("bsns_year")
    )

    if len(by_year) == 0:
        return PonziRatioResult([], [], 0, "stable", "데이터부족", "이자비용 데이터 부족")

    periods = by_year.get_column("bsns_year").to_list()
    ponzi_counts = by_year.get_column("ponzi_count").to_list()
    totals = by_year.get_column("total").to_list()
    ratios = [round(p / t, 3) if t > 0 else 0 for p, t in zip(ponzi_counts, totals)]

    current = ratios[-1]
    if len(ratios) >= 2:
        if ratios[-1] > ratios[-2] + 0.02:
            trend, trend_label = "rising", "상승"
        elif ratios[-1] < ratios[-2] - 0.02:
            trend, trend_label = "falling", "하락"
        else:
            trend, trend_label = "stable", "안정"
    else:
        trend, trend_label = "stable", "안정"

    return PonziRatioResult(
        periods=periods,
        ratios=ratios,
        currentRatio=current,
        trend=trend,
        trendLabel=trend_label,
        description=f"ICR<1 비중 {current:.1%} ({trend_label}) — {ponzi_counts[-1]}/{totals[-1]}개사",
    )


def leverageCycle(financeDf: pl.DataFrame) -> LeverageCycleResult:
    """전종목 부채비율 중간값 추이."""
    annual = _extract_annual_consolidated(financeDf)
    result = _median_ratio(annual, _TOTAL_DEBT_NAMES, _TOTAL_EQUITY_NAMES, "BS")

    if len(result) < 2:
        return LeverageCycleResult([], [], 0, "stable", "데이터부족", "부채비율 데이터 부족")

    periods = result.get_column("bsns_year").to_list()
    medians = [round(v, 1) if v is not None else 0 for v in result.get_column("median_ratio").to_list()]

    current = medians[-1]
    if len(medians) >= 2:
        if medians[-1] > medians[-2] + 2:
            trend, label = "rising", "상승"
        elif medians[-1] < medians[-2] - 2:
            trend, label = "falling", "하락"
        else:
            trend, label = "stable", "안정"
    else:
        trend, label = "stable", "안정"

    return LeverageCycleResult(
        periods=periods,
        medianDebtRatio=medians,
        currentLevel=current,
        trend=trend,
        trendLabel=label,
        description=f"전종목 부채비율 중간값 {current:.1f}% ({label})",
    )
