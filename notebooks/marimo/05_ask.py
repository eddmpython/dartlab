# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DartLab -- Ask (AI Analysis).

ask() -- natural language questions about any company.
Engine computes, LLM explains. No code knowledge required.

Provider setup:
  - oauth-codex (recommended): dartlab setup oauth-codex
  - gemini (free): dartlab setup gemini
  - groq (free): dartlab setup groq
  - openai: dartlab setup openai
  - ollama (local): dartlab setup ollama
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
    dartlab.setup()
    return


@app.cell
def _(dartlab):
    # streams in real-time, returns full text
    answer = dartlab.ask("삼성전자 재무건전성 분석해줘")
    return


if __name__ == "__main__":
    app.run()
