# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DartLab -- Ask (AI).

ask() -- natural language analysis with LLM.
Setup: dartlab setup gemini / openai / ollama
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
    dartlab.ask('최근 매출액이 많이 오른 기업들 상위 10개 뽑아줘')
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
