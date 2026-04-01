# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DartLab -- Analysis.

c.analysis() -- 14-axis financial analysis.
c.insights -- 7-area grades at a glance.
c.forecast() / c.valuation() -- forward-looking estimates.
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import dartlab

    c = dartlab.Company("005930")
    return c, dartlab


@app.cell
def _(c):
    # guide -- see all 14 axes
    c.analysis()
    return


@app.cell
def _(c):
    c.analysis("financial", "수익구조")
    return


@app.cell
def _(c):
    c.analysis("financial", "현금흐름")
    return


@app.cell
def _(c):
    c.analysis("financial", "안정성")
    return


@app.cell
def _(c):
    # 7-area grades
    c.insights
    return


@app.cell
def _(c):
    c.forecast()
    return


@app.cell
def _(c):
    c.valuation()
    return


@app.cell
def _(c):
    c.audit()
    return


@app.cell
def _(dartlab):
    # root functions -- no Company needed
    dartlab.insights("005930")
    return


@app.cell
def _(dartlab):
    dartlab.forecast("005930")
    return


if __name__ == "__main__":
    app.run()
