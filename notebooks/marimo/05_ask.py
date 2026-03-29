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
    import marimo as mo

    import dartlab

    return dartlab, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## AI Analysis -- `dartlab.ask()`

    | Provider | Auth | Cost | Setup |
    |----------|------|------|-------|
    | `oauth-codex` | ChatGPT subscription | Included | `dartlab setup oauth-codex` |
    | `gemini` | API key | Free tier | `dartlab setup gemini` |
    | `groq` | API key | Free tier | `dartlab setup groq` |
    | `openai` | API key | Pay-per-token | `dartlab setup openai` |
    | `ollama` | Local install | Free | `dartlab setup ollama` |

    `oauth-codex` is recommended -- no API keys needed with a ChatGPT subscription.
    """)
    return


@app.cell
def _(dartlab):
    # basic -- streams to stdout, returns full text
    dartlab.ask("삼성전자 재무건전성 분석해줘")
    return


@app.cell
def _(dartlab):
    # provider override
    dartlab.ask("삼성전자 수익성 추세", provider="gemini")
    return


@app.cell
def _(dartlab):
    # data filtering
    dartlab.ask("삼성전자 핵심 포인트", include=["BS", "IS"])
    return


@app.cell
def _(dartlab):
    # analysis pattern
    dartlab.ask("삼성전자 분석", pattern="financial")
    return


@app.cell
def _(dartlab):
    # agent mode -- LLM generates dartlab code for deeper analysis
    dartlab.chat("005930", "배당 추세를 분석하고 이상 징후를 찾아줘")
    return


@app.cell
def _(dartlab):
    # company bound
    c = dartlab.Company("005930")
    c.ask("영업이익률 추세 분석해줘")
    return


@app.cell
def _(dartlab):
    # US stock (EDGAR)
    dartlab.ask("AAPL revenue trend analysis")
    return


if __name__ == "__main__":
    app.run()
