# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DartLab -- Scan.

scan() -- one function for all cross-market analysis.
13 axes, 2,700+ companies.
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import dartlab

    return (dartlab,)


@app.cell
def _(dartlab):
    # find a company by name
    dartlab.search("삼성전자")
    return


@app.cell
def _(dartlab):
    # full listing of all available companies
    dartlab.listing()
    return


@app.cell
def _(dartlab):
    # step 1: guide -- all axes + usage
    dartlab.scan()
    return


@app.cell
def _(dartlab):
    # step 2: item list for an axis
    dartlab.scan("ratio")
    return


@app.cell
def _(dartlab):
    # step 3: execute -- rank all companies by ROE
    dartlab.scan("ratio", "roe")
    return


@app.cell
def _(dartlab):
    # scan a raw account across every company
    dartlab.scan("account", "매출액")
    return


@app.cell
def _(dartlab):
    # governance scan -- full market
    dartlab.scan("governance")
    return


@app.cell
def _(dartlab):
    # cashflow pattern classification (OCF/ICF/FCF + 8 patterns)
    dartlab.scan("cashflow")
    return


@app.cell
def _(dartlab):
    # audit risk flags (opinion, auditor changes, risk score)
    dartlab.scan("audit")
    return


@app.cell
def _(dartlab):
    # insider ownership changes (largest shareholder, treasury stock)
    dartlab.scan("insider")
    return


if __name__ == "__main__":
    app.run()
