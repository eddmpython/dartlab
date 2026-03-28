# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DartLab -- Scan.

search, listing, scanAccount, scanRatio, and 11-axis market scan across 2,700+ companies.
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
    # find a company by name -- returns matching stock codes
    dartlab.search("삼성전자")
    return


@app.cell
def _(dartlab):
    # full listing of all available companies
    dartlab.listing()
    return


@app.cell
def _(dartlab):
    # available pre-computed ratio scans
    dartlab.scan("ratio")
    return


@app.cell
def _(dartlab):
    # rank all 2,700+ companies by ROE
    dartlab.scanRatio("roe")
    return


@app.cell
def _(dartlab):
    # scan a raw account across every company
    dartlab.scanAccount("매출액")
    return


@app.cell
def _(dartlab):
    # unified scan interface -- list available axes
    dartlab.scan.topics()
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
