"""scan 교차검증 고급 정보 추출 + 저장."""

import json

import polars as pl

import dartlab


def main():
    """11축 교차검증 → scan_insights JSON 저장."""
    gov = dartlab.scan("governance")
    cf = dartlab.scan("cashflow")
    prof = dartlab.scan("profitability")
    qual = dartlab.scan("quality")
    debt = dartlab.scan("debt")
    cap = dartlab.scan("capital")
    growth = dartlab.scan("growth")
    insider = dartlab.scan("insider")
    audit = dartlab.scan("audit")
    liq = dartlab.scan("liquidity")

    # 1. 빚내서 배당 (환원형 + 부채 고위험)
    capReturn = set(cap.filter(pl.col("분류") == "환원형")["종목코드"].to_list())
    debtHigh = set(debt.filter(pl.col("위험등급") == "고위험")["종목코드"].to_list())
    debtDividend = capReturn & debtHigh

    debtDividendList = []
    for c in debtDividend:
        d = debt.filter(pl.col("종목코드") == c)
        ca = cap.filter(pl.col("종목코드") == c)
        if d.is_empty() or ca.is_empty():
            continue
        dr = d.row(0, named=True)
        cr = ca.row(0, named=True)
        debtDividendList.append({
            "stockCode": c,
            "debtRatio": dr["부채비율"],
            "icr": dr["ICR"],
            "dps": cr["DPS"],
            "dividendYield": cr["배당수익률"],
        })
    debtDividendList.sort(key=lambda x: x.get("debtRatio") or 0, reverse=True)

    # 2. 비경상 이익 의심 (수익성 양호+ + 이익의 질 나쁨)
    profGood = set(prof.filter(pl.col("grade").is_in(["우수", "양호"]))["stockCode"].to_list())
    qualBad = set(qual.filter(pl.col("grade").is_in(["위험", "주의"]))["stockCode"].to_list())
    nonRecurring = profGood & qualBad

    nonRecurringList = []
    for c in nonRecurring:
        p = prof.filter(pl.col("stockCode") == c)
        q = qual.filter(pl.col("stockCode") == c)
        if p.is_empty() or q.is_empty():
            continue
        pr = p.row(0, named=True)
        qr = q.row(0, named=True)
        nonRecurringList.append({
            "stockCode": c,
            "opMargin": pr["opMargin"],
            "netMargin": pr["netMargin"],
            "roe": pr["roe"],
            "accrualRatio": qr["accrualRatio"],
            "cfToNi": qr["cfToNi"],
        })

    # 3. 레버리지 성장 (고성장 + 부채 고위험)
    growthHigh = set(growth.filter(pl.col("grade") == "고성장")["stockCode"].to_list())
    leverageGrowth = growthHigh & debtHigh

    leverageGrowthList = []
    for c in leverageGrowth:
        g = growth.filter(pl.col("stockCode") == c)
        d = debt.filter(pl.col("종목코드") == c)
        if g.is_empty() or d.is_empty():
            continue
        gr = g.row(0, named=True)
        dr = d.row(0, named=True)
        leverageGrowthList.append({
            "stockCode": c,
            "revenueCagr": gr["revenueCagr"],
            "growthPattern": gr["pattern"],
            "debtRatio": dr["부채비율"],
            "icr": dr["ICR"],
        })
    leverageGrowthList.sort(key=lambda x: x.get("debtRatio") or 0, reverse=True)

    # 4. 형식적 지배구조 (governance A + 현금위기/외부의존)
    govA = set(gov.filter(pl.col("등급") == "A")["종목코드"].to_list())
    cfCrisis = set(cf.filter(pl.col("pattern").is_in(["현금위기형", "외부의존형"]))["stockCode"].to_list())
    formalGov = govA & cfCrisis

    formalGovList = []
    for c in formalGov:
        g = gov.filter(pl.col("종목코드") == c)
        cff = cf.filter(pl.col("stockCode") == c)
        if g.is_empty() or cff.is_empty():
            continue
        gr = g.row(0, named=True)
        cr = cff.row(0, named=True)
        formalGovList.append({
            "stockCode": c,
            "govScore": gr["총점"],
            "cfPattern": cr["pattern"],
            "ocf": cr["ocf"],
            "fcf": cr["fcf"],
        })

    # 5. 감사 고위험
    auditRiskDf = audit.filter(pl.col("riskLevel").is_in(["고위험", "주의"]))
    auditRiskList = []
    for row in auditRiskDf.iter_rows(named=True):
        auditRiskList.append({
            "stockCode": row["stockCode"],
            "opinion": row["opinion"],
            "auditor": row["auditor"],
            "auditorChanged": row["auditorChanged"],
            "riskLevel": row["riskLevel"],
        })

    # 6. 경영권 위험
    insiderRiskDf = insider.filter(pl.col("stability").is_in(["경고", "위험"]))
    insiderRiskList = []
    for row in insiderRiskDf.iter_rows(named=True):
        insiderRiskList.append({
            "stockCode": row["stockCode"],
            "holderPct": row["holderPct"],
            "holderChange": row["holderChange"],
            "treasuryShares": row["treasuryShares"],
            "stability": row["stability"],
        })
    insiderRiskList.sort(key=lambda x: x.get("holderPct") or 999)

    # 7. 유동성 위험
    liqRiskDf = liq.filter(pl.col("grade") == "위험")
    liqRiskList = []
    for row in liqRiskDf.iter_rows(named=True):
        liqRiskList.append({
            "stockCode": row["stockCode"],
            "currentRatio": row["currentRatio"],
            "quickRatio": row["quickRatio"],
        })
    liqRiskList.sort(key=lambda x: x.get("currentRatio") or 999)

    # 8. 현금 부자 (현금축적형 + 수익성 우수)
    cfRich = set(cf.filter(pl.col("pattern") == "현금축적형")["stockCode"].to_list())
    profExcellent = set(prof.filter(pl.col("grade") == "우수")["stockCode"].to_list())
    cashRich = cfRich & profExcellent

    cashRichList = []
    for c in cashRich:
        p = prof.filter(pl.col("stockCode") == c)
        cff = cf.filter(pl.col("stockCode") == c)
        if p.is_empty() or cff.is_empty():
            continue
        pr = p.row(0, named=True)
        cr = cff.row(0, named=True)
        cashRichList.append({
            "stockCode": c,
            "opMargin": pr["opMargin"],
            "roe": pr["roe"],
            "ocf": cr["ocf"],
            "fcf": cr["fcf"],
        })

    # 9. 균형 우등생 (수익성 우수 + 이익의 질 우수 + 부채 안전 + 성장)
    profExcSet = set(prof.filter(pl.col("grade") == "우수")["stockCode"].to_list())
    qualExcSet = set(qual.filter(pl.col("grade").is_in(["우수", "양호"]))["stockCode"].to_list())
    debtSafe = set(debt.filter(pl.col("위험등급") == "안전")["종목코드"].to_list())
    growthPos = set(growth.filter(pl.col("grade").is_in(["고성장", "성장"]))["stockCode"].to_list())
    balanced = profExcSet & qualExcSet & debtSafe & growthPos

    balancedList = []
    for c in balanced:
        p = prof.filter(pl.col("stockCode") == c)
        g = growth.filter(pl.col("stockCode") == c)
        d = debt.filter(pl.col("종목코드") == c)
        q = qual.filter(pl.col("stockCode") == c)
        if p.is_empty() or g.is_empty() or d.is_empty() or q.is_empty():
            continue
        pr = p.row(0, named=True)
        gr = g.row(0, named=True)
        dr = d.row(0, named=True)
        qr = q.row(0, named=True)
        balancedList.append({
            "stockCode": c,
            "opMargin": pr["opMargin"],
            "roe": pr["roe"],
            "revenueCagr": gr["revenueCagr"],
            "debtRatio": dr["부채비율"],
            "icr": dr["ICR"],
            "accrualRatio": qr["accrualRatio"],
        })
    balancedList.sort(key=lambda x: x.get("roe") or 0, reverse=True)

    result = {
        "scanDate": "2026-03-30",
        "summary": {
            "debtDividend": len(debtDividendList),
            "nonRecurringProfit": len(nonRecurringList),
            "leverageGrowth": len(leverageGrowthList),
            "formalGovernance": len(formalGovList),
            "auditRisk": len(auditRiskList),
            "insiderRisk": len(insiderRiskList),
            "liquidityRisk": len(liqRiskList),
            "cashRich": len(cashRichList),
            "balanced": len(balancedList),
        },
        "debtDividend": debtDividendList,
        "nonRecurringProfit": nonRecurringList,
        "leverageGrowth": leverageGrowthList,
        "formalGovernance": formalGovList,
        "auditRisk": auditRiskList,
        "insiderRisk": insiderRiskList,
        "liquidityRisk": liqRiskList,
        "cashRich": cashRichList,
        "balanced": balancedList,
    }

    outPath = "data/audit/scan_insights_2026-03-30.json"
    with open(outPath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: {outPath}")
    for k, v in result["summary"].items():
        print(f"  {k}: {v}개")


if __name__ == "__main__":
    main()
