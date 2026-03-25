# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""전종목 재무비율 시계열 배치 추출 — scanRatio.

실행: marimo edit notebooks/marimo/scanRatio.py
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App()

with app.setup:
    import polars as pl

    from dartlab import scanRatio, scanRatioList


@app.cell
def _():
    # 사용 가능한 비율 목록
    scanRatioList()
    return


@app.cell
def _():
    # 전종목 ROE 분기별 시계열 (기본=분기, 최신 먼저)
    roe = scanRatio("roe")
    roe
    return (roe,)


@app.cell
def _(roe):
    # 삼성전자 ROE 확인
    roe.filter(pl.col("corpName") == "삼성전자")
    return


@app.cell
def _():
    # 연간 ROE
    scanRatio("roe", annual=True)
    return


@app.cell
def _(roe):
    # 최근 분기 ROE 상위 20개
    latest = [c for c in roe.columns if c not in ("stockCode", "corpName")][0]
    roe.filter(pl.col(latest).is_not_null()).sort(latest, descending=True).head(20)
    return (latest,)


@app.cell
def _(latest, roe):
    # 최근 분기 ROE 분포 통계
    roe.select(pl.col(latest).drop_nulls()).describe()
    return


@app.cell
def _():
    # 영업이익률 분기별
    margin = scanRatio("operatingMargin")
    margin
    return (margin,)


@app.cell
def _(latest, margin):
    # 영업이익률 20% 이상 우량 기업 (최근 분기)
    margin.filter(pl.col(latest) >= 20).sort(latest, descending=True).head(20)
    return


@app.cell
def _():
    # 부채비율 분기별
    debt = scanRatio("debtRatio")
    debt
    return (debt,)


@app.cell
def _(debt, latest):
    # 부채비율 50% 이하 건전 기업 (최근 분기)
    debt.filter(
        pl.col(latest).is_not_null() & (pl.col(latest) <= 50)
    ).sort(latest).head(20)
    return


@app.cell
def _():
    # 매출 성장률 연간
    growth = scanRatio("revenueGrowth", annual=True)
    growth
    return (growth,)


@app.cell
def _(growth, latest):
    # 최근 연간 매출 성장률 상위 20개
    growth.filter(pl.col(latest).is_not_null()).sort(latest, descending=True).head(20)
    return


@app.cell
def _(latest, margin, roe):
    # 멀티팩터: ROE 15%+ & 영업이익률 10%+ (최근 분기)
    good = roe.filter(
        pl.col(latest).is_not_null() & (pl.col(latest) >= 15)
    ).select("stockCode", "corpName", pl.col(latest).alias("ROE"))

    mLatest = [c for c in margin.columns if c not in ("stockCode", "corpName")][0]
    goodMargin = margin.filter(
        pl.col(mLatest).is_not_null() & (pl.col(mLatest) >= 10)
    ).select("stockCode", pl.col(mLatest).alias("영업이익률"))

    good.join(goodMargin, on="stockCode").sort("ROE", descending=True)
    return


if __name__ == "__main__":
    app.run()
