# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""review 블록 조립 예제.

실행: marimo edit notebooks/marimo/sampleReview.py
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import dartlab
    from dartlab.review import blocks, Review

    c = dartlab.Company("005930")
    return c, dartlab, blocks, Review


@app.cell
def _(c, blocks):
    # 블록 사전 — 16개 분석 블록
    b = blocks(c)
    print(list(b.keys()))
    return (b,)


@app.cell
def _(b, Review):
    # 자유 조립 — 원하는 블록만 골라서
    Review([
        b["segmentComposition"],
        b["growth"],
        b["concentration"],
    ])
    return


@app.cell
def _(b, c, Review):
    # 블록 + 원시 데이터 혼합
    Review([
        b["segmentTrend"],
        c.select("IS", ["매출액"]),
    ])
    return


@app.cell
def _(c):
    # reviewer — AI 종합의견 (AI 설정 필요: dartlab setup gemini 등)
    # guide로 분석 관점 지정 가능
    c.reviewer("수익구조", guide="반도체 사이클 관점에서 평가해줘")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
