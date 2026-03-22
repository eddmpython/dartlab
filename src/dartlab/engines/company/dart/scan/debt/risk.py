"""이자보상배율(ICR) + 단기비중 교차 → 부채 위험등급."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.engines.company.dart.scan._helpers import parse_num

# ── 영업이익 ──

OP_IDS = {
    "ProfitLossFromOperatingActivities",
    "profitLossFromOperatingActivities",
    "ifrs-full_ProfitLossFromOperatingActivities",
    "dart_OperatingIncomeLoss",
}
OP_NMS = {"영업이익", "영업이익(손실)"}


# ── 이자비용 ──

INTEREST_IDS = {
    "FinanceCosts",
    "financeCosts",
    "ifrs-full_FinanceCosts",
    "InterestExpense",
    "interestExpense",
}
INTEREST_NMS = {"이자비용", "금융비용", "금융원가", "이자비용(수익)"}


def scan_icr() -> dict[str, float]:
    """finance IS → {종목코드: ICR}.

    ICR = 영업이익 / 이자비용.  이자비용이 0이면 제외.
    """
    from dartlab.core.dataLoader import _dataDir

    finance_dir = Path(_dataDir("finance"))
    parquet_files = sorted(finance_dir.glob("*.parquet"))

    result: dict[str, float] = {}
    for pf in parquet_files:
        code = pf.stem
        try:
            is_df = (
                pl.scan_parquet(str(pf))
                .filter(
                    pl.col("sj_div").is_in(["IS", "CIS"])
                    & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
                )
                .collect()
            )
        except (pl.exceptions.PolarsError, OSError):
            continue
        if is_df.is_empty() or "account_id" not in is_df.columns:
            continue
        if is_df.is_empty():
            continue
        cfs = is_df.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else is_df

        years = sorted(target["bsns_year"].unique().to_list(), reverse=True)
        if not years:
            continue
        latest = target.filter(pl.col("bsns_year") == years[0])

        op_income = None
        interest = None
        for row in latest.iter_rows(named=True):
            aid = row.get("account_id", "")
            anm = row.get("account_nm", "")
            val = parse_num(row.get("thstrm_amount"))
            if val is None:
                continue
            if (aid in OP_IDS or anm in OP_NMS) and op_income is None:
                op_income = val
            elif (aid in INTEREST_IDS or anm in INTEREST_NMS) and interest is None:
                interest = abs(val) if val != 0 else None

        if op_income is not None and interest and interest > 0:
            result[code] = round(op_income / interest, 2)

    return result


def classify_risk(icr: float | None, short_ratio: float | None) -> str:
    """ICR × 단기비중 → 위험등급.

    - 고위험: 단기비중 ≥ 50% AND ICR < 1
    - 주의:   단기비중 ≥ 50% OR ICR < 1
    - 관찰:   ICR < 3
    - 안전:   그 외
    """
    sr = short_ratio if short_ratio is not None else 0
    if icr is None:
        return "주의" if sr >= 50 else "관찰"
    if sr >= 50 and icr < 1:
        return "고위험"
    if sr >= 50 or icr < 1:
        return "주의"
    if icr < 3:
        return "관찰"
    return "안전"
