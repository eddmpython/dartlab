# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""EDGAR 미국 상장기업 탐색 — sections 중심 흐름.

실행: marimo edit startMarimo/edgarCompany.py
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import dartlab

    c = dartlab.Company("AAPL")  # Apple
    c.corpName
    return (c,)


@app.cell
def _(c):
    # topic × period 수평화 DataFrame
    c.sections
    return


@app.cell
def _(c):
    # 이 회사의 topic 목록
    c.topics
    return


@app.cell
def _(c):
    # 10-K riskFactors → 서술형 블록
    c.show("riskFactors")
    return


@app.cell
def _(c):
    # 재무제표 topic
    c.show("IS")
    return


@app.cell
def _(c):
    c.BS  # Balance Sheet
    return


@app.cell
def _(c):
    c.IS  # Income Statement
    return


@app.cell
def _(c):
    c.CF  # Cash Flow Statement
    return


@app.cell
def _(c):
    c.ratios  # 재무비율 시계열
    return


@app.cell
def _(c):
    # 특정 기간 비교 (항목 × 기간)
    c.show("IS", period=["2024Q4", "2023Q4"])
    return


@app.cell
def _(c):
    c.trace("riskFactors")
    return


@app.cell
def _(c):
    # 전체 topic별 텍스트 변경률
    c.diff()
    return


@app.cell
def _(c):
    # 종합평가
    c.analysis("financial", "종합평가")
    return


@app.cell
def _(c):
    c.filings()
    return


if __name__ == "__main__":
    app.run()
