# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DART 한국 상장기업 탐색 — sections 중심 흐름.

실행: marimo edit startMarimo/dartCompany.py
"""

import marimo

__generated_with = "0.20.4"
app = marimo.App()


@app.cell
def _():
    import dartlab

    c = dartlab.Company("005930")  # 삼성전자
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
    # 서술형 topic → 블록 목차
    c.show("companyOverview")
    return


@app.cell
def _(c):
    # 블록 번호 지정 → 실제 데이터
    c.show("companyOverview", 3)
    return


@app.cell
def _(c):
    # 재무제표 topic → finance source (숫자 authoritative)
    c.show("IS")
    return


@app.cell
def _(c):
    # report 데이터 조회
    c.show("dividend", 13)
    return


@app.cell
def _(c):
    # 어떤 source(docs/finance/report)가 채택됐는지
    c.trace("stockTotal")
    return


@app.cell
def _(c):
    # 전체 topic별 변경률
    c.diff()
    return


@app.cell
def _(c):
    # 특정 topic 기간별 이력
    c.diff("businessOverview")
    return


@app.cell
def _(c):
    c.BS  # 재무상태표
    return


@app.cell
def _(c):
    c.ratios  # 재무비율
    return


@app.cell
def _(c):
    # 세로 뷰 — 특정 기간 비교 (기간 × 항목)
    c.show("IS", period=["2024Q4", "2023Q4"])
    return


if __name__ == "__main__":
    app.run()
