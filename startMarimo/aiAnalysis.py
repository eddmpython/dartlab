# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""AI 기업 분석 — LLM 기반 대화형 분석 예시.

실행: marimo edit startMarimo/aiAnalysis.py

사전 조건:
  - provider 설정 필요: dartlab setup (CLI에서 안내 확인)
  - 예: ollama pull llama3.2 && ollama serve  (무료 로컬)
  - 예: export OPENAI_API_KEY=sk-...          (OpenAI API)
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import dartlab
    import marimo as mo

    return dartlab, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## AI 분석

    `dartlab.ask("삼성전자 분석해줘")` — 호출하면 스트리밍 출력 + 전체 텍스트 반환.
    """)
    return


@app.cell
def _(dartlab):
    dartlab.ask('삼성전자 최근 매출액 및 영업이익 분석해줘')
    return


@app.cell
def _(dartlab):
    dartlab.ask('삼성전자 성격별 비용 분류도 알수있나')
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
