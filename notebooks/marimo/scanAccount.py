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

with app.setup:
    import polars as pl

    from dartlab import scanAccount


@app.cell
def _():
    # 전종목 매출 분기별 시계열 (기본=분기, 최신 먼저)
    df = scanAccount("매출액")
    df
    return (df,)


@app.cell
def _(df):
    # 삼성전자 매출 확인
    df.filter(pl.col("corpName").str.contains("삼성전자"))
    return


@app.cell
def _():
    # 연간 매출 시계열
    scanAccount("매출액", annual=True)
    return


@app.cell
def _():
    # 영업이익 분기별
    scanAccount("영업이익")
    return


@app.cell
def _():
    # 자산총계 (BS 계정)
    scanAccount("자산총계")
    return


@app.cell
def _():
    # 영문 snakeId도 사용 가능
    scanAccount("operating_profit", annual=True)
    return


@app.cell
def _():
    # 별도재무제표(OFS) 우선
    scanAccount("매출액", fsPref="OFS", annual=True)
    return


@app.cell
def _(df):
    # 최근 분기 매출 상위 10개
    latest = [c for c in df.columns if c not in ("stockCode", "corpName")][0]
    df.filter(pl.col(latest).is_not_null()).sort(latest, descending=True).head(10)
    return


@app.cell
def _(df):
    # 직전 분기 대비 매출 성장률
    cols = [c for c in df.columns if c not in ("stockCode", "corpName")]
    cur, prev = cols[0], cols[1]
    growth = df.filter(
        pl.col(cur).is_not_null() & pl.col(prev).is_not_null()
    ).with_columns(
        ((pl.col(cur) - pl.col(prev)) / pl.col(prev).abs() * 100)
        .round(2)
        .alias("growth_pct")
    )
    growth.select("stockCode", "corpName", prev, cur, "growth_pct").sort(
        "growth_pct", descending=True
    ).head(10)
    return


if __name__ == "__main__":
    app.run()
