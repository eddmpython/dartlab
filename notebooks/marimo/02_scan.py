# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DartLab -- Scan.

search, listing, scanAccount, scanRatio across 2,700+ companies.
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
    dartlab.scanRatioList()
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


if __name__ == "__main__":
    app.run()
