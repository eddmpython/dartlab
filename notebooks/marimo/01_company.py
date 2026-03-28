# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DartLab -- Company.

One stock code. The whole story.
7 things to remember: index, show, select, trace, diff, review, analysis.
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import dartlab

    # one stock code creates the entire company map
    c = dartlab.Company("005930")  # Samsung Electronics
    return c, dartlab


@app.cell
def _(c):
    # 1. index -- what's available
    c.index
    return


@app.cell
def _(c):
    # 2. show -- see the data
    c.show("businessOverview")
    return


@app.cell
def _(c):
    c.show("companyOverview")
    return


@app.cell
def _(c):
    # 3. select -- extract specific rows/columns
    c.select("IS", ["revenue", "operatingIncome"])
    return


@app.cell
def _(c):
    # 4. trace -- where did it come from
    c.trace("BS")
    return


@app.cell
def _(c):
    c.trace("businessOverview")
    return


@app.cell
def _(c):
    # 5. diff -- what changed between filings
    c.diff()
    return


@app.cell
def _(c):
    c.diff("businessOverview")
    return


@app.cell
def _(c):
    # finance shortcuts -- income statement
    c.IS
    return


@app.cell
def _(c):
    # balance sheet
    c.BS
    return


@app.cell
def _(c):
    # cash flow statement
    c.CF
    return


@app.cell
def _(c):
    # financial ratios -- profitability, stability, valuation
    c.ratios
    return


@app.cell
def _(dartlab):
    # same API works for US companies via SEC EDGAR
    apple = dartlab.Company("AAPL")
    apple.index
    return (apple,)


@app.cell
def _(apple):
    apple.IS
    return


@app.cell
def _(apple):
    # EDGAR 10-K filing -- risk factors section
    apple.show("10-K::item1ARiskFactors")
    return


if __name__ == "__main__":
    app.run()
