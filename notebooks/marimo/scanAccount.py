# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""전종목 단일 계정 시계열 배치 추출 — scanAccount.

실행: marimo edit notebooks/marimo/scanAccount.py
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App()


@app.cell
def _():
    from dartlab.engines.company.dart.finance import scanAccount

    # 전종목 매출(sales) 연간 시계열
    df = scanAccount("sales")
    df
    return (df, scanAccount)


@app.cell
def _(df):
    import polars as pl

    # 삼성전자 매출 확인
    df.filter(pl.col("stockCode") == "005930")
    return


@app.cell
def _(scanAccount):
    # BS 계정: 총자산
    scanAccount("total_assets", sjDiv="BS")
    return


@app.cell
def _(scanAccount):
    # 별도재무제표(OFS) 우선으로 매출 추출
    scanAccount("sales", fsPref="OFS")
    return


@app.cell
def _(df):
    import polars as pl

    # 2024년 매출 상위 10개 종목
    df.filter(pl.col("2024").is_not_null()).sort("2024", descending=True).head(10)
    return


@app.cell
def _(df):
    import polars as pl

    # YoY 매출 성장률 계산 (2023→2024)
    growth = df.filter(
        pl.col("2023").is_not_null() & pl.col("2024").is_not_null()
    ).with_columns(
        ((pl.col("2024") - pl.col("2023")) / pl.col("2023").abs() * 100)
        .round(2)
        .alias("growth_pct")
    )
    growth.select("stockCode", "2023", "2024", "growth_pct").sort(
        "growth_pct", descending=True
    ).head(10)
    return


if __name__ == "__main__":
    app.run()
