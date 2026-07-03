"""Estimate statements view : the library-owned display contract for the E-3표.

The sealed proforma ledger (account x quantile x FY, values only) is the immutable record.
This module owns EVERYTHING a surface needs to render those estimates aligned to the actual
statement time series: the canonical row key (the statements display contract shared with the
actuals pipeline), Korean/English labels, statement grouping, and sort order. Surfaces do no
mapping; they match ``rowKey`` and render (SSOT 원칙: 가공·정렬 지식은 라이브러리, 표면은 소비만).

The view is regenerated every cycle (like scorecard.json) and published next to the ledger:
``expectations/estimateStatements.parquet``. It is a derived view, not a second history:
the append-only truth stays in ``proforma_{yyyy}.parquet``.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.simulate.expectationLedger import ledgerDir, readProforma

# (statement, proforma account) -> (canonical rowKey, kr, en, sortOrder)
# rowKey = 재무제표 표시 계약의 정본 키. 근사 매핑(예: interest_expense ~= 금융비용)은 넣지 않는다.
_CANON: tuple[tuple[str, str, str, str, str, int], ...] = (
    ("IS", "revenue", "revenue", "매출액", "Revenue", 10),
    ("IS", "cogs", "costOfSales", "매출원가", "COGS", 20),
    ("IS", "gross_profit", "grossProfit", "매출총이익", "Gross profit", 30),
    ("IS", "sga", "sga", "판매관리비", "SG&A", 40),
    ("IS", "operating_income", "operatingIncome", "영업이익", "Operating income", 50),
    ("IS", "tax", "incomeTax", "법인세비용", "Income tax", 60),
    ("IS", "net_income", "netIncome", "당기순이익", "Net income", 70),
    ("BS", "total_assets", "assets", "자산총계", "Assets", 10),
    ("BS", "current_assets", "currentAssets", "유동자산", "Current assets", 20),
    ("BS", "cash", "cash", "현금성자산", "Cash", 30),
    ("BS", "inventories", "inventories", "재고자산", "Inventories", 40),
    ("BS", "receivables", "receivables", "매출채권", "Receivables", 50),
    ("BS", "total_liabilities", "liabilities", "부채총계", "Liabilities", 60),
    ("BS", "current_liabilities", "currentLiabilities", "유동부채", "Current liab", 70),
    ("BS", "total_equity", "equity", "자본총계", "Equity", 80),
    ("BS", "retained_earnings", "retainedEarnings", "이익잉여금", "Retained earnings", 90),
    ("CF", "ocf", "cfOperating", "영업활동현금흐름", "Operating CF", 10),
    ("CF", "financing_cf", "cfFinancing", "재무활동현금흐름", "Financing CF", 20),
)

VIEW_FILENAME = "estimateStatements.parquet"


def buildEstimateStatements(*, baseDir: Path | None = None) -> pl.DataFrame | None:
    """Build the aligned estimate-statements view from the sealed proforma ledger.

    Returns:
        pl.DataFrame(code, targetPeriod, periodKind("FY"|"Q"), quantile, statement, rowKey,
        labelKr, labelEn, sortOrder, value(원), parentId, issuedAt, issuedLive). live 발행분만,
        canonical 매핑이 있는 계정만. Ledger 미발간이면 None. periodKind 분류는 뷰(라이브러리)
        소유다: 표면이 targetPeriod 문자열을 파싱하지 않는다.
    """
    pf = readProforma(baseDir=baseDir)
    if pf is None or pf.height == 0:
        return None
    canon = pl.DataFrame(
        [
            {"statement": s, "account": a, "rowKey": k, "labelKr": kr, "labelEn": en, "sortOrder": o}
            for s, a, k, kr, en, o in _CANON
        ]
    )
    return (
        pf.filter(pl.col("issuedLive"))
        .join(canon, on=["statement", "account"], how="inner")
        .with_columns(
            pl.when(pl.col("targetPeriod").str.starts_with("FY"))
            .then(pl.lit("FY"))
            .otherwise(pl.lit("Q"))
            .alias("periodKind")
        )
        .select(
            "code",
            "targetPeriod",
            "periodKind",
            "quantile",
            "statement",
            "rowKey",
            "labelKr",
            "labelEn",
            "sortOrder",
            "value",
            "parentId",
            "issuedAt",
            "issuedLive",
        )
        .sort(["code", "targetPeriod", "statement", "sortOrder", "quantile"])
    )


def writeEstimateStatements(*, baseDir: Path | None = None) -> Path | None:
    """Regenerate the view file next to the ledger (cycle publish step)."""
    df = buildEstimateStatements(baseDir=baseDir)
    if df is None:
        return None
    out = ledgerDir(baseDir) / VIEW_FILENAME
    tmp = out.with_suffix(".parquet.tmp")
    df.write_parquet(tmp)
    tmp.replace(out)
    return out
