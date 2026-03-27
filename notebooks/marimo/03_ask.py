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
    dartlab.setup()
    return


@app.cell
def _(dartlab):
    dartlab.ask("Analyze Samsung Electronics financial health")
    return


@app.cell
def _(dartlab):
    dartlab.ask("005930", "What are the key risks?")
    return


@app.cell
def _(dartlab):
    dartlab.ask("005930", "How about dividend trends?")
    return


@app.cell
def _(dartlab):
    dartlab.ask("AAPL", "Compare Apple's margins to industry average")
    return


if __name__ == "__main__":
    app.run()
