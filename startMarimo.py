# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo", "polars"]
# ///
"""dartlab sections 탐색 노트북.

실행: marimo edit startMarimo.py
"""

import marimo

__generated_with = "0.12.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import dartlab

    # 종목코드 또는 이름으로 Company 생성
    c = dartlab.Company("005930")  # 삼성전자
    return c, dartlab


# ── sections: 회사 전체 맵 ─────────────────────────────────────
@app.cell
def _(c):
    # topic × period 수평화 DataFrame
    # blockType으로 text/table 구분, textNodeType으로 heading/body 구분
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
    # BS → finance source (숫자 authoritative)
    c.show("BS")
    return


@app.cell
def _(c):
    # 서술형 topic → 블록 목차
    c.show("companyOverview")
    return


@app.cell
def _(c):
    # 블록 번호 지정 → 실제 데이터
    c.show("companyOverview", 0)
    return


# ── trace: 출처 확인 ─────────────────────────────────────────
@app.cell
def _(c):
    # 어떤 source(docs/finance/report)가 채택됐는지
    c.trace("BS")
    return


# ── diff: 텍스트 변화 감지 ───────────────────────────────────
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


# ── 재무제표 / 비율 ──────────────────────────────────────────
@app.cell
def _(c):
    c.BS  # 재무상태표
    return


@app.cell
def _(c):
    c.ratios  # 47개 재무비율
    return


# ── EDGAR (미국) ─────────────────────────────────────────────
@app.cell
def _(dartlab):
    # 동일한 인터페이스, 다른 데이터 소스
    us = dartlab.Company("AAPL")
    us.sections
    return (us,)


@app.cell
def _(us):
    us.show("10-K::item1Business")
    return


if __name__ == "__main__":
    app.run()
