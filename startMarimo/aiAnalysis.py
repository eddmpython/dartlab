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
app = marimo.App()


@app.cell
def _():
    import dartlab

    c = dartlab.Company("005930")  # 삼성전자
    c.corpName
    return (c,)


# ── 원스톱 ask ──────────────────────────────────────────────────
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 원스톱 AI 분석

    `dartlab.ask("삼성전자 분석해줘")` — 한 문장이면 끝.
    종목명을 자동 추출하고, 재무제표·공시·비율 등을 종합하여 LLM이 스트리밍으로 답변합니다.
    """)
    return


@app.cell
def _(dartlab):
    # 원스톱 — 종목명을 텍스트에서 자동 추출, 스트리밍 기본
    for chunk in dartlab.ask("삼성전자 재무건전성 분석해줘"):
        print(chunk, end="", flush=True)
    print()
    return


# ── 분석 패턴 (pattern) ────────────────────────────────────────
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 분석 패턴

    `pattern`으로 분석 프레임워크를 지정할 수 있습니다.
    - `"financial"` — 수익성·안정성·성장성 종합
    - `"risk"` — 리스크 요인 집중
    - `"valuation"` — 밸류에이션 분석
    - `"dividend"` — 배당 정책 분석
    """)
    return


@app.cell
def _(dartlab):
    # 밸류에이션 패턴으로 분석
    for chunk in dartlab.ask("삼성전자 저평가인지 분석해줘", pattern="valuation"):
        print(chunk, end="", flush=True)
    print()
    return


@app.cell
def _(dartlab):
    # 리스크 패턴
    for chunk in dartlab.ask("삼성전자 리스크 요인을 분석해줘", pattern="risk"):
        print(chunk, end="", flush=True)
    print()
    return


# ── Company에서 직접 질문 ──────────────────────────────────────
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Company 직접 질문

    `c.ask("질문")`으로 이미 로드된 Company에 바로 질문할 수 있습니다.
    종목 지정이 필요 없어 편리합니다.
    """)
    return


@app.cell
def _(c):
    # Company에서 바로 질문 — 스트리밍 기본
    for chunk in c.ask("배당 정책을 분석해줘"):
        print(chunk, end="", flush=True)
    print()
    return


# ── Provider 지정 ──────────────────────────────────────────────
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Provider 지정

    `provider`로 LLM 백엔드를 선택합니다.
    - `"ollama"` — 로컬 무료 (사전: `ollama pull llama3.2 && ollama serve`)
    - `"openai"` — OpenAI API (사전: `export OPENAI_API_KEY=sk-...`)
    - `"claude"` — Anthropic Claude
    """)
    return


@app.cell
def _(dartlab):
    # Ollama (로컬, 무료)
    for chunk in dartlab.ask("삼성전자 부채 구조를 분석해줘", provider="ollama"):
        print(chunk, end="", flush=True)
    print()
    return


@app.cell
def _(dartlab):
    # OpenAI API
    for chunk in dartlab.ask("SK하이닉스 밸류에이션을 분석해줘", provider="openai", model="gpt-4o"):
        print(chunk, end="", flush=True)
    print()
    return


# ── 데이터 필터링 ──────────────────────────────────────────────
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 데이터 필터링

    `include` / `exclude`로 LLM에 전달할 데이터를 제어합니다.
    """)
    return


@app.cell
def _(dartlab):
    # 특정 데이터만 포함
    for chunk in dartlab.ask(
        "삼성전자 재무상태표와 손익계산서만 보고 핵심 포인트를 알려줘",
        include=["BS", "IS"],
    ):
        print(chunk, end="", flush=True)
    print()
    return


@app.cell
def _(dartlab):
    # 특정 데이터 제외
    for chunk in dartlab.ask(
        "삼성전자를 전반적으로 분석해줘",
        exclude=["dividend", "segments"],
    ):
        print(chunk, end="", flush=True)
    print()
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
