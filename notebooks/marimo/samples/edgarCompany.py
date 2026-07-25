# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""EDGAR 미국 상장기업 탐색. panel 중심 흐름.

공개 호출 계약만 쓴다. `dartlab.{engine}("{axis}", ...)` 와 engines skill 의 capabilityRefs 에
등재된 `Company.{method}` 뿐이다. 은퇴한 `show`와 비공개 메서드(topics · diff ·
disclosure · liveFilings · readFiling)는 계약이 아니므로 예제에 싣지 않는다. 티커를 넣으면
EDGAR 로, 6자리 숫자를 넣으면 DART 로 라우팅된다.

실행: marimo edit notebooks/marimo/samples/edgarCompany.py
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
    c.market  # US 이면 EDGAR 로 라우팅된다
    return


@app.cell
def _(c):
    # 공시를 항목 x 기간으로 눕힌 wide 격자 그 자체
    c.panel.shape
    return


@app.cell
def _(c):
    c.panel("IS")  # Income Statement
    return


@app.cell
def _(c):
    c.panel("BS")  # Balance Sheet
    return


@app.cell
def _(c):
    c.panel("CF")  # Cash Flow Statement
    return


@app.cell
def _(c):
    # 분기로 묶어 보기
    c.panel("IS", freq="Q")
    return


@app.cell
def _(c):
    # 격자에서 원하는 계정만 이름으로 골라내기
    c.select("IS", ["Revenue"], freq="Y")
    return


@app.cell
def _(c):
    # 공시 문서 목록 + 원문 링크
    c.filings()
    return


@app.cell
def _(c):
    # 종합평가
    c.analysis("financial", "종합평가")
    return


@app.cell
def _(c):
    c.credit("채무상환능력")
    return


if __name__ == "__main__":
    app.run()
