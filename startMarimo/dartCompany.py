import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import dartlab
    c = dartlab.Company("005930")
    return (c,)


@app.cell
def _(c):
    # 회사명 확인
    c.corpName
    return


@app.cell
def _(c):
    # 사업보고서 전체 맵
    c.sections
    return


@app.cell
def _(c):
    # topic으로 topic의 구조를 다시 확인 가능함
    c.show("companyOverview")
    return


@app.cell
def _(c):
    # topic으로 topic의 blockOrder를 통해 표형식 데이터는 다시 수평구조로 concat 
    c.show("companyOverview",1)
    return


@app.cell
def _(c):
    c.show("companyHistory",5)
    return


@app.cell
def _(c):
    # report 데이터 조회
    c.show('dividend',8)
    return


@app.cell
def _(c):
    # IS, CIS, BS, CF, SCE 등 시계열 조회
    c.show("IS")
    return


@app.cell
def _(c):
    # 데이터 소스 추적
    c.trace("stockTotal")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
