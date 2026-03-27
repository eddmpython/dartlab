# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DART 기업분석 보고서 — c.review() 집중 탐색.

실행: marimo edit notebooks/marimo/dartReview.py
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
    # 전체 분석 보고서 — rich 텍스트 + DataFrame 교차
    c = dartlab.Company("005930")  # 삼성전자
    # c.reviewer() # AI 전체 

    # 특정 항목만
    c.review("수익구조")
    return (c,)


@app.cell
def _(c):
    # 특정 항목만
    c.review("자금조달")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
