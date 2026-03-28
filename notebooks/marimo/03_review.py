# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DartLab -- Review.

analysis() computes 14-axis financial analysis.
c.review() consumes it and assembles a structured report.
c.reviewer() adds AI interpretation on top.
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import dartlab

    c = dartlab.Company("005930")  # Samsung Electronics
    return (c,)


@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md("## Review -- structured report from analysis")
    return (mo,)


@app.cell
def _(c):
    # full review -- all 14 sections
    c.review()
    return


@app.cell
def _(c):
    # single section
    c.review("수익구조")
    return


@app.cell
def _(c):
    c.review("수익성")
    return


@app.cell
def _(c):
    c.review("현금흐름")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Reviewer -- review + AI interpretation

    "
        "Requires: `pip install dartlab[llm]` + `dartlab setup`
    """)
    return


@app.cell
def _(c):
    # AI interprets each section
    c.reviewer()
    return


@app.cell
def _(c):
    # single section with AI
    c.reviewer("수익구조")
    return


@app.cell
def _(c):
    # domain-specific guidance for AI
    c.reviewer(guide="Evaluate from a semiconductor cycle perspective")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Custom layout
    """)
    return


@app.cell
def _(c):
    from dartlab.review import ReviewLayout

    ly = ReviewLayout(indentBody=8, gapAfterH2=2)
    c.review("수익구조", layout=ly)
    return


if __name__ == "__main__":
    app.run()
