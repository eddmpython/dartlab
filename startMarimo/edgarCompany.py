import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import dartlab
    c = dartlab.Company("AAPL")
    return (c,)


@app.cell
def _(c):
    c.corpName
    return


@app.cell
def _(c):
    c.index
    return


@app.cell
def _(c):
    c.show("riskFactors")
    return


@app.cell
def _(c):
    c.show("IS")
    return


@app.cell
def _(c):
    c.ratios
    return


@app.cell
def _(c):
    c.filings()
    return


@app.cell
def _(c):
    c.trace("riskFactors")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
