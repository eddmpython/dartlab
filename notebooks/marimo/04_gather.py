# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DartLab -- Gather.

gather() -- one function for all external market data.
Price, flow, macro, news -- all as Polars DataFrames.
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App()


@app.cell
def _():
    import dartlab

    return (dartlab,)


@app.cell
def _(dartlab):
    # guide -- all axes
    dartlab.gather()
    return


@app.cell
def _(dartlab):
    # KR stock -- 1-year OHLCV
    dartlab.gather("price", "005930")
    return


@app.cell
def _(dartlab):
    # custom date range
    dartlab.gather("price", "005930", start="2020-01-01")
    return


@app.cell
def _(dartlab):
    # US stock
    dartlab.gather("price", "AAPL", market="US")
    return


@app.cell
def _(dartlab):
    # supply/demand flow (KR only)
    dartlab.gather("flow", "005930")
    return


@app.cell
def _(dartlab):
    # KR macro indicators (12 key series)
    dartlab.gather("macro")
    return


@app.cell
def _(dartlab):
    # US macro indicators (25 key series)
    dartlab.gather("macro", market="US")
    return


@app.cell
def _(dartlab):
    # single indicator
    dartlab.gather("macro", "CPI")
    return


@app.cell
def _(dartlab):
    dartlab.gather("macro", "FEDFUNDS")
    return


@app.cell
def _(dartlab):
    # Google News RSS
    dartlab.gather("news", "삼성전자")
    return


@app.cell
def _(dartlab):
    # company bound
    c = dartlab.Company("005930")
    c.gather("price")
    return


if __name__ == "__main__":
    app.run()
