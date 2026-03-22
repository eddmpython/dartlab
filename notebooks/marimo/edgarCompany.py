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


# ── Company 생성 ──────────────────────────────────────────────
@app.cell
def _():
    import dartlab

    c = dartlab.Company("AAPL")  # Apple
    c.corpName
    return (c,)


# ── sections: 회사 전체 맵 ────────────────────────────────────
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


# ── show: topic 열기 ──────────────────────────────────────────
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


# ── 재무제표 ──────────────────────────────────────────────────
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


# ── trace / diff ──────────────────────────────────────────────
@app.cell
def _(c):
    c.trace("riskFactors")
    return


@app.cell
def _(c):
    # 전체 topic별 텍스트 변경률
    c.diff()
    return


# ── 분석 엔진 ─────────────────────────────────────────────────
@app.cell
def _(c):
    # 섹터 분류
    c.sector
    return


@app.cell
def _(c):
    # 인사이트 등급 (7영역)
    c.insights
    return


# ── 보고서 목록 ───────────────────────────────────────────────
@app.cell
def _(c):
    c.filings()
    return


if __name__ == "__main__":
    app.run()
