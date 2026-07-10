# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DART 한국 상장기업 탐색. panel 중심 흐름.

공개 호출 계약만 쓴다. `dartlab.{engine}("{axis}", ...)` 와 engines skill 의 capabilityRefs 에
등재된 `Company.{method}` 뿐이다. 내부 메서드(show · topics · diff · notes · filings · sector)는
계약이 아니므로 예제에 싣지 않는다.

실행: marimo edit notebooks/marimo/samples/dartCompany.py
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App()


@app.cell
def _():
    import dartlab

    c = dartlab.Company("005930")  # 삼성전자
    c.corpName
    return (c,)


@app.cell
def _(c):
    # 공시를 항목 x 기간으로 눕힌 wide 격자 그 자체
    c.panel.shape
    return


@app.cell
def _(c):
    # 손익계산서 (숫자 authoritative source 주입)
    c.panel("IS")
    return


@app.cell
def _(c):
    c.panel("BS")  # 재무상태표
    return


@app.cell
def _(c):
    c.panel("CF")  # 현금흐름표
    return


@app.cell
def _(c):
    c.panel("ratios")  # 재무비율 시계열
    return


@app.cell
def _(c):
    # 연간으로 묶어 보기
    c.panel("IS", freq="Y")
    return


@app.cell
def _(c):
    # 연결이 기본값. 별도 재무제표는 scope 로 지정
    c.panel("BS", scope="separate")
    return


@app.cell
def _(c):
    # 격자에서 원하는 계정만 이름으로 골라내기
    c.select("IS", ["매출액", "영업이익"], freq="Y")
    return


@app.cell
def _(c):
    # 주석 본문 검색 (섹션명 또는 canonicalKey 행)
    c.panel("재고")
    return


@app.cell
def _(c):
    # 이 topic 데이터가 어느 출처에서 왔는지 되짚기
    c.trace("IS")
    return


@app.cell
def _(c):
    # 산업 위치 (업종, 공정 단계, 동종사)
    c.industry()
    return


@app.cell
def _(c):
    c.analysis("financial", "종합평가")
    return


@app.cell
def _(c):
    c.credit("채무상환능력")
    return


if __name__ == "__main__":
    app.run()
