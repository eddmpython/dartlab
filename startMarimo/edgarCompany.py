# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""EDGAR 미국 상장기업 탐색 — sections 중심 흐름.

실행: marimo edit startMarimo/edgarCompany.py
"""

import marimo

__generated_with = "0.20.4"
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


# ── trace: 출처 확인 ──────────────────────────────────────────
@app.cell
def _(c):
    c.trace("riskFactors")
    return


# ── diff: 텍스트 변화 감지 ────────────────────────────────────
@app.cell
def _(c):
    c.diff()
    return


# ── 재무제표 / 비율 ──────────────────────────────────────────
@app.cell
def _(c):
    c.BS
    return


@app.cell
def _(c):
    c.ratios
    return


# ── 특정 기간 비교 ────────────────────────────────────────────
@app.cell
def _(c):
    # 특정 기간 비교 (항목 × 기간)
    c.show("IS", period=["2024Q4", "2023Q4"])
    return


# ── 보고서 목록 ──────────────────────────────────────────────
@app.cell
def _(c):
    c.filings()
    return


if __name__ == "__main__":
    app.run()
