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
    # 제공 데이터 전체
    c.index
    return


@app.cell
def _(c):
    # topic으로 상세한데이터 확인
    c.show("companyOverview")
    return


@app.cell
def _(c):
    c.show("companyHistory")
    return


@app.cell
def _(c):
    # report 데이터 조회
    c.show('nonAuditContract')
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
