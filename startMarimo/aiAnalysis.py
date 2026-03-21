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


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## AI 분석 기본

    `dartlab.ask(종목코드, 질문)` — 회사 데이터를 자동으로 수집하여 LLM에 전달합니다.
    별도 설정 없이도 재무제표, 공시, 비율 등을 종합하여 답변합니다.
    """)
    return


@app.cell
def _(dartlab):
    # 기본 분석 — 자동으로 provider 감지
    result = dartlab.ask("005930", "이 회사의 재무 건전성을 분석해줘")
    print(result)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Provider 지정
    """)
    return


@app.cell
def _(dartlab):
    # Ollama (로컬, 무료)
    # 사전: ollama pull llama3.2 && ollama serve
    result_ollama = dartlab.ask("005930", "배당 정책을 분석해줘", provider="ollama")
    print(result_ollama)
    return


@app.cell
def _(dartlab):
    # OpenAI API (API 키 필요)
    # 사전: export OPENAI_API_KEY=sk-...
    result_openai = dartlab.ask("005930", "밸류에이션을 분석해줘", provider="openai", model="gpt-4o")
    print(result_openai)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 스트리밍 모드
    """)
    return


@app.cell
def _(dartlab):
    # stream=True → 제너레이터 반환 (chunk 단위 출력)
    for chunk in dartlab.ask("005930", "수익성 추세를 분석해줘", stream=True):
        print(chunk, end="", flush=True)
    print()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 데이터 필터링 (include / exclude)
    """)
    return


@app.cell
def _(dartlab):
    # 특정 데이터만 포함
    result_focused = dartlab.ask(
        "005930",
        "재무상태표와 손익계산서만 보고 핵심 포인트를 알려줘",
        include=["BS", "IS"],
    )
    print(result_focused)
    return


@app.cell
def _(dartlab):
    # 특정 데이터 제외
    result_exclude = dartlab.ask(
        "005930",
        "전반적으로 분석해줘",
        exclude=["dividend", "segments"],
    )
    print(result_exclude)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
