# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""종합 기업분석 리포트 — Research Engine.

종목코드 하나로 세계 수준의 equity research를 생성한다.
Piotroski F-Score, DuPont, Magic Formula, Lynch, QMJ 등
정량 스코어링 + 투자논거 합성 + 밸류에이션 + 리스크 분석을 한 화면에.

실행: marimo edit notebooks/marimo/research.py
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")

with app.setup:
    import dartlab


@app.cell
def _():
    r = dartlab.research("005930")
    r
    return (r,)


@app.cell
def _(r):
    r.toDict()
    return


if __name__ == "__main__":
    app.run()
