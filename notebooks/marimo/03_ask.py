# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DartLab -- Ask.

AI-powered company analysis.
Prerequisite: dartlab setup (CLI) to configure a provider.
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
    # check which AI providers are configured
    dartlab.setup()
    return


@app.cell
def _(dartlab):
    # ask without a stock code -- auto-detects the company from the question
    dartlab.ask("Analyze Samsung Electronics financial health")
    return


@app.cell
def _(dartlab):
    # ask with a stock code -- targeted question about a specific company
    dartlab.ask("005930", "What are the key risks?")
    return


@app.cell
def _(dartlab):
    dartlab.ask("005930", "How about dividend trends?")
    return


@app.cell
def _(dartlab):
    # works with EDGAR tickers too
    dartlab.ask("AAPL", "Compare Apple's margins to industry average")
    return


if __name__ == "__main__":
    app.run()
