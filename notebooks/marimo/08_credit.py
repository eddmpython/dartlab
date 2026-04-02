import marimo

__generated_with = "0.13.0"
app = marimo.App(width="medium")


@app.cell
def _():
    """dartlab 신용평가 엔진 — dCR 독립 등급 체계."""
    import dartlab

    c = dartlab.Company("005930")
    return c, dartlab


@app.cell
def _(c):
    """기본 등급 조회."""
    cr = c.credit()
    print(f"등급: {cr['grade']}")
    print(f"건전도: {cr['healthScore']}/100")
    print(f"부도확률: {cr['pdEstimate']}%")
    print(f"전망: {cr['outlook']}")
    return (cr,)


@app.cell
def _(c):
    """상세 분석 — 7축 서사."""
    cr = c.credit(detail=True)
    for n in cr["narratives"]["axes"]:
        print(f"[{n['severity']}] {n['axis']}: {n['summary']}")
    return


@app.cell
def _(c):
    """지표 시계열."""
    cr = c.credit(detail=True)
    for h in cr["metricsHistory"][:3]:
        print(
            f"{h['period']}: "
            f"ICR={h.get('ebitdaInterestCoverage', '-')} "
            f"D/E={h.get('debtRatio', '-')}% "
            f"OCF/Sales={h.get('ocfToSales', '-')}%"
        )
    return


@app.cell
def _(dartlab):
    """다른 기업 비교."""
    for code, name in [("000660", "SK하이닉스"), ("035420", "NAVER"), ("003550", "LG")]:
        cc = dartlab.Company(code)
        r = cc.credit()
        if r:
            print(f"{name}: {r['grade']} 건전도 {r['healthScore']}/100 PD {r['pdEstimate']}%")
    return


if __name__ == "__main__":
    app.run()
