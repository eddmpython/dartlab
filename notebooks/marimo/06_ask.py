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

    dartlab.setup()
    return (dartlab,)


@app.cell
def _(dartlab):
    dartlab.ask("삼성전자 재무건전성 분석해줘")
    return


if __name__ == "__main__":
    app.run()
