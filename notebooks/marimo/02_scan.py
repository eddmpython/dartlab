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
    dartlab.search("삼성전자")
    return


@app.cell
def _(dartlab):
    dartlab.listing()
    return


@app.cell
def _(dartlab):
    dartlab.scanRatioList()
    return


@app.cell
def _(dartlab):
    dartlab.scanRatio("roe")
    return


@app.cell
def _(dartlab):
    dartlab.scanAccount("매출액")
    return


if __name__ == "__main__":
    app.run()
