# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""시장 전체 스캔 — scanAccount + scanRatio.

2,700+ 종목의 계정·비율을 한 번에 조회한다.

실행: marimo edit notebooks/marimo/marketScan.py
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App()

with app.setup:
    import polars as pl

    import dartlab


# ── scanAccount: 단일 계정 전종목 시계열 ──


@app.cell
def _():
    # 전종목 매출 분기별 시계열
    df = dartlab.scanAccount("매출액")
    df
    return (df,)


@app.cell
def _(df):
    # 삼성전자 매출 확인
    df.filter(pl.col("corpName").str.contains("삼성전자"))
    return


@app.cell
def _():
    # 연간 영업이익
    dartlab.scanAccount("영업이익", annual=True)
    return


# ── scanRatio: 재무비율 전종목 시계열 ──


@app.cell
def _():
    # 사용 가능한 비율 목록
    dartlab.scanRatioList()
    return


@app.cell
def _():
    # 전종목 ROE 분기별
    roe = dartlab.scanRatio("roe")
    roe
    return (roe,)


@app.cell
def _(roe):
    # 최근 분기 ROE 상위 20개
    latest = [c for c in roe.columns if c not in ("stockCode", "corpName")][0]
    roe.filter(pl.col(latest).is_not_null()).sort(latest, descending=True).head(20)
    return


if __name__ == "__main__":
    app.run()
