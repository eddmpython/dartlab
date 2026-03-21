"""그룹사 건전성 분석 — 네트워크 × 재무비율 교차.

그룹별 건전성 요약, 약한 고리 식별, 순환출자 리스크 점수.

Example::

    from dartlab.engines.dart.scan.network.health import groupHealth
    summary, weakLinks = groupHealth()
"""

from __future__ import annotations

import polars as pl


def groupHealth(*, verbose: bool = True) -> tuple[pl.DataFrame, pl.DataFrame]:
    """그룹사 건전성 분석.

    Returns:
        (summary, weakLinks) 튜플.
        summary: 그룹별 건전성 요약 DataFrame (group, members, roe_median, ...).
        weakLinks: 약한 고리 종목 DataFrame (ROE<0 AND 부채비율>150).
    """
    from dartlab.engines.dart.scan.network import build_graph
    from dartlab.engines.rank.screen import _ensureMarketRatios

    if verbose:
        print("[dartlab] 그룹 건전성 분석 중...")

    data = build_graph(verbose=False)
    code_to_group = data["code_to_group"]

    df = _ensureMarketRatios(verbose=verbose)

    # 그룹 매핑
    groupCol = [code_to_group.get(code, "독립") for code in df["stockCode"].to_list()]
    df = df.with_columns(pl.Series("group", groupCol))

    # 그룹별 건전성 요약
    summary = (
        df.filter(pl.col("group") != "독립")
        .group_by("group")
        .agg(
            [
                pl.len().alias("members"),
                pl.col("roe").median().alias("roe_median"),
                pl.col("debtRatio").median().alias("debtRatio_median"),
                pl.col("operatingMargin").median().alias("om_median"),
                pl.col("currentRatio").median().alias("cr_median"),
                pl.col("totalAssets").sum().alias("totalAssets_sum"),
                ((pl.col("roe") < 0) & (pl.col("debtRatio") > 150)).sum().alias("weakLinks"),
                (pl.col("roe") < 0).sum().alias("lossMembers"),
            ]
        )
        .sort("members", descending=True)
    )

    # 건전성 등급
    grades = []
    for row in summary.iter_rows(named=True):
        roe = row["roe_median"] or 0
        debt = row["debtRatio_median"] or 0
        if roe > 5 and debt < 100:
            grades.append("A")
        elif roe > 0 and debt < 200:
            grades.append("B")
        elif roe > 0:
            grades.append("C")
        else:
            grades.append("D")
    summary = summary.with_columns(pl.Series("grade", grades))

    # 약한 고리
    weakLinks = (
        df.filter((pl.col("group") != "독립") & (pl.col("roe") < 0) & (pl.col("debtRatio") > 150))
        .select(
            [
                "stockCode",
                "corpName",
                "group",
                "sector",
                "roe",
                "debtRatio",
                "operatingMargin",
                "currentRatio",
            ]
        )
        .sort(["group", "roe"])
    )

    if verbose:
        print(f"  [health] {summary.shape[0]}그룹, {weakLinks.shape[0]}개 약한 고리")

    return summary, weakLinks
