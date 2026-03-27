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

    c = dartlab.Company("005930")  # Samsung Electronics
    c.corpName
    return c, dartlab


@app.cell
def _(c):
    # topic x period company map
    c.sections
    return


@app.cell
def _(c):
    c.topics
    return


@app.cell
def _(c):
    c.show("businessOverview")
    return


@app.cell
def _(c):
    c.show("companyOverview")
    return


@app.cell
def _(c):
    c.trace("BS")
    return


@app.cell
def _(c):
    c.trace("businessOverview")
    return


@app.cell
def _(c):
    c.diff()
    return


@app.cell
def _(c):
    c.diff("businessOverview")
    return


@app.cell
def _(c):
    c.IS
    return


@app.cell
def _(c):
    c.BS
    return


@app.cell
def _(c):
    c.CF
    return


@app.cell
def _(c):
    c.ratios
    return


@app.cell
def _(dartlab):
    # EDGAR -- same API, US companies
    apple = dartlab.Company("AAPL")
    apple.sections
    return (apple,)


@app.cell
def _(apple):
    apple.IS
    return


@app.cell
def _(apple):
    apple.show("10-K::item1ARiskFactors")
    return


if __name__ == "__main__":
    app.run()
