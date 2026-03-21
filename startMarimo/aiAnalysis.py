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

    `dartlab.ask("삼성전자 분석해줘")` — 한 문장이면 끝. 종목명을 자동 추출하고
    재무제표, 공시, 비율 등을 종합하여 LLM이 답변합니다.
    기존 2인자 형식 `dartlab.ask("005930", "질문")` 도 호환됩니다.
    """)
    return


@app.cell
def _(dartlab):
    # 원스톱 분석 — 종목명을 텍스트에서 자동 추출
    result = dartlab.ask("삼성전자 재무건전성 분석해줘", stream=False)
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
    # stream=True가 기본값 → 제너레이터 반환 (chunk 단위 출력)
    for chunk in dartlab.ask("삼성전자 수익성 추세를 분석해줘"):
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
