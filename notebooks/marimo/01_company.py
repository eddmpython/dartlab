# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import dartlab

    c = dartlab.Company("005930")
    c.corpName
    return (c,)


@app.cell
def _(c):
    # 전체 공시 수평화 격자 (항목 × 기간), tag=True 모든 태그 포함
    c.panel(tag=False)
    return


@app.cell
def _(c):
    # 항목명 행 검색 (raw 공시)
    c.panel("수주")
    return


@app.cell
def _(c):
    # 항목명 행 검색 (raw 공시)
    c.panel("재고자산",tag=False)
    return


@app.cell
def _(c):
    # native 손익 — 사업보고서 항목 그대로, XBRL+옛 통합 (2013~)
    c.panel("is", freq="year")
    return


@app.cell
def _(c):
    # finance 손익 — XBRL 정규화 숫자
    c.panel("IS", freq="year")
    return


@app.cell
def _(c):
    c.panel("CF", freq="year")
    return


@app.cell
def _(c):
    # native 비율 — 5표 항목으로 계산 (깊은 history)
    c.panel("ratios")
    return


@app.cell
def _(c):
    # finance 비율
    c.panel("RATIOS")
    return


@app.cell
def _(c):
    # 한 값이 어느 공시에서 왔는지 되짚기 (filings 는 계약이 아니다)
    c.trace("영업이익")
    return


@app.cell
def _(c):
    # 본문 전체 검색
    c.panel.search("사업보고서",tag=False)
    return


if __name__ == "__main__":
    app.run()
