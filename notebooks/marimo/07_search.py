# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab[vector]", "marimo"]
# ///
"""DartLab -- Search (alpha).

공시 원문 시맨틱 검색.
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import dartlab

    dartlab.search("유상증자 결정", topK=5)
    return (dartlab,)


@app.cell
def _(dartlab):
    dartlab.search("대표이사 변경", corp="005930", topK=5)
    return


@app.cell
def _(dartlab):
    dartlab.search("회사가 돈을 빌렸다", topK=5)
    return


@app.cell
def _(dartlab):
    dartlab.search("전환사채 발행", start="20260101", topK=5)
    return


if __name__ == "__main__":
    app.run()
