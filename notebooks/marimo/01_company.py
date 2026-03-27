# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DartLab -- Company.

One stock code. The whole story.
sections, show, trace, diff, BS/IS/CF, ratios, EDGAR.
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App()


@app.cell
def _():
    import dartlab

    # one stock code creates the entire company map
    c = dartlab.Company("005930")  # Samsung Electronics
    c.corpName
    return c, dartlab


@app.cell
def _(c):
    # topic x period matrix -- the full company map at a glance
    c.sections
    return


@app.cell
def _(c):
    # all available topics for this company
    c.topics
    return


@app.cell
def _(c):
    # drill into a specific topic -- narrative text with period comparison
    c.show("businessOverview")
    return


@app.cell
def _(c):
    c.show("companyOverview")
    return


@app.cell
def _(c):
    # trace where data comes from -- docs, finance, or report
    c.trace("BS")
    return


@app.cell
def _(c):
    c.trace("businessOverview")
    return


@app.cell
def _(c):
    # diff across periods -- what changed between filings
    c.diff()
    return


@app.cell
def _(c):
    # diff on a single topic
    c.diff("businessOverview")
    return


@app.cell
def _(c):
    # income statement -- standalone quarterly, all periods
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
    apple.sections
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
