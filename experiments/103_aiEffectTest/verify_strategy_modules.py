import json
import sys

import dartlab

# 검증 대상 종목
STOCKS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("005380", "현대자동차"),
]

def check_result(name, result):
    """결과 품질 체크"""
    if result is None:
        return {"status": "NONE", "periods": 0, "keys": []}
    if isinstance(result, list):
        return {"status": "OK" if result else "EMPTY", "count": len(result), "sample": result[:2] if result else []}
    if isinstance(result, dict):
        history = result.get("history", [])
        periods = [h.get("period", "") for h in history]
        keys = list(history[0].keys()) if history else []
        # 첫 번째 항목의 None이 아닌 필드 수
        non_none = 0
        if history:
            non_none = sum(1 for v in history[0].values() if v is not None)
        return {
            "status": "OK" if history else "EMPTY",
            "periods": len(history),
            "period_range": f"{periods[-1]}~{periods[0]}" if periods else "",
            "keys": keys,
            "non_none_fields": non_none,
            "total_fields": len(keys),
        }
    return {"status": "UNKNOWN", "type": str(type(result))}

def test_stock(code, name):
    print(f"\n{'='*80}")
    print(f"  {name} ({code})")
    print(f"{'='*80}")

    c = dartlab.Company(code)

    # ── 기존 모듈 (기준선) ──
    print(f"\n--- 기존 모듈 (기준선) ---")
    from dartlab.analysis.financial.revenue import calcRevenueGrowth
    from dartlab.analysis.financial.capital import calcDebtTimeline
    from dartlab.analysis.financial.cashflow import calcCashFlowOverview
    from dartlab.analysis.financial.asset import calcWorkingCapital

    for fn_name, fn in [
        ("revenue.calcRevenueGrowth", calcRevenueGrowth),
        ("capital.calcDebtTimeline", calcDebtTimeline),
        ("cashflow.calcCashFlowOverview", calcCashFlowOverview),
        ("asset.calcWorkingCapital", calcWorkingCapital),
    ]:
        try:
            result = fn(c)
            info = check_result(fn_name, result)
            print(f"  {fn_name}: {info['status']} | periods={info.get('periods','-')} | range={info.get('period_range','-')} | fields={info.get('non_none_fields','-')}/{info.get('total_fields','-')}")
        except Exception as e:
            print(f"  {fn_name}: ERROR - {e}")

    # ── 신규 모듈 1: earningsQuality ──
    print(f"\n--- earningsQuality ---")
    from dartlab.analysis.financial.earningsQuality import (
        calcAccrualAnalysis, calcEarningsPersistence, calcBeneishTimeline, calcEarningsQualityFlags
    )
    for fn_name, fn in [
        ("calcAccrualAnalysis", calcAccrualAnalysis),
        ("calcEarningsPersistence", calcEarningsPersistence),
        ("calcBeneishTimeline", calcBeneishTimeline),
    ]:
        try:
            result = fn(c)
            info = check_result(fn_name, result)
            print(f"  {fn_name}: {info['status']} | periods={info.get('periods','-')} | range={info.get('period_range','-')} | fields={info.get('non_none_fields','-')}/{info.get('total_fields','-')}")
            if info.get('status') == 'OK' and result and result.get('history'):
                h0 = result['history'][0]
                print(f"    latest: {json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in h0.items()}, ensure_ascii=False)}")
        except Exception as e:
            print(f"  {fn_name}: ERROR - {e}")

    try:
        flags = calcEarningsQualityFlags(c)
        print(f"  flags: {flags}")
    except Exception as e:
        print(f"  flags: ERROR - {e}")

    # ── 신규 모듈 2: costStructure ──
    print(f"\n--- costStructure ---")
    from dartlab.analysis.financial.costStructure import (
        calcCostBreakdown, calcOperatingLeverage, calcBreakevenEstimate, calcCostStructureFlags
    )
    for fn_name, fn in [
        ("calcCostBreakdown", calcCostBreakdown),
        ("calcOperatingLeverage", calcOperatingLeverage),
        ("calcBreakevenEstimate", calcBreakevenEstimate),
    ]:
        try:
            result = fn(c)
            info = check_result(fn_name, result)
            print(f"  {fn_name}: {info['status']} | periods={info.get('periods','-')} | range={info.get('period_range','-')} | fields={info.get('non_none_fields','-')}/{info.get('total_fields','-')}")
            if info.get('status') == 'OK' and result and result.get('history'):
                h0 = result['history'][0]
                print(f"    latest: {json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in h0.items()}, ensure_ascii=False)}")
        except Exception as e:
            print(f"  {fn_name}: ERROR - {e}")

    try:
        flags = calcCostStructureFlags(c)
        print(f"  flags: {flags}")
    except Exception as e:
        print(f"  flags: ERROR - {e}")

    # ── 신규 모듈 3: capitalAllocation ──
    print(f"\n--- capitalAllocation ---")
    from dartlab.analysis.financial.capitalAllocation import (
        calcDividendPolicy, calcShareholderReturn, calcReinvestment, calcFcfUsage, calcCapitalAllocationFlags
    )
    for fn_name, fn in [
        ("calcDividendPolicy", calcDividendPolicy),
        ("calcShareholderReturn", calcShareholderReturn),
        ("calcReinvestment", calcReinvestment),
        ("calcFcfUsage", calcFcfUsage),
    ]:
        try:
            result = fn(c)
            info = check_result(fn_name, result)
            print(f"  {fn_name}: {info['status']} | periods={info.get('periods','-')} | range={info.get('period_range','-')} | fields={info.get('non_none_fields','-')}/{info.get('total_fields','-')}")
            if info.get('status') == 'OK' and result and result.get('history'):
                h0 = result['history'][0]
                print(f"    latest: {json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in h0.items()}, ensure_ascii=False)}")
        except Exception as e:
            print(f"  {fn_name}: ERROR - {e}")

    try:
        flags = calcCapitalAllocationFlags(c)
        print(f"  flags: {flags}")
    except Exception as e:
        print(f"  flags: ERROR - {e}")

    # ── 신규 모듈 4: investmentAnalysis ──
    print(f"\n--- investmentAnalysis ---")
    from dartlab.analysis.financial.investmentAnalysis import (
        calcRoicTimeline, calcInvestmentIntensity, calcEvaTimeline, calcInvestmentFlags
    )
    for fn_name, fn in [
        ("calcRoicTimeline", calcRoicTimeline),
        ("calcInvestmentIntensity", calcInvestmentIntensity),
        ("calcEvaTimeline", calcEvaTimeline),
    ]:
        try:
            result = fn(c)
            info = check_result(fn_name, result)
            print(f"  {fn_name}: {info['status']} | periods={info.get('periods','-')} | range={info.get('period_range','-')} | fields={info.get('non_none_fields','-')}/{info.get('total_fields','-')}")
            if info.get('status') == 'OK' and result and result.get('history'):
                h0 = result['history'][0]
                print(f"    latest: {json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in h0.items()}, ensure_ascii=False)}")
        except Exception as e:
            print(f"  {fn_name}: ERROR - {e}")

    try:
        flags = calcInvestmentFlags(c)
        print(f"  flags: {flags}")
    except Exception as e:
        print(f"  flags: ERROR - {e}")

    # ── 신규 모듈 5: crossStatement ──
    print(f"\n--- crossStatement ---")
    from dartlab.analysis.financial.crossStatement import (
        calcIsCfDivergence, calcIsBsDivergence, calcAnomalyScore, calcCrossStatementFlags
    )
    for fn_name, fn in [
        ("calcIsCfDivergence", calcIsCfDivergence),
        ("calcIsBsDivergence", calcIsBsDivergence),
        ("calcAnomalyScore", calcAnomalyScore),
    ]:
        try:
            result = fn(c)
            info = check_result(fn_name, result)
            print(f"  {fn_name}: {info['status']} | periods={info.get('periods','-')} | range={info.get('period_range','-')} | fields={info.get('non_none_fields','-')}/{info.get('total_fields','-')}")
            if info.get('status') == 'OK' and result and result.get('history'):
                h0 = result['history'][0]
                print(f"    latest: {json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in h0.items()}, ensure_ascii=False)}")
        except Exception as e:
            print(f"  {fn_name}: ERROR - {e}")

    try:
        flags = calcCrossStatementFlags(c)
        print(f"  flags: {flags}")
    except Exception as e:
        print(f"  flags: ERROR - {e}")

    # ── 신규 모듈 6: taxAnalysis ──
    print(f"\n--- taxAnalysis ---")
    from dartlab.analysis.financial.taxAnalysis import (
        calcEffectiveTaxRate, calcTaxCashConversion, calcDeferredTax, calcTaxFlags
    )
    for fn_name, fn in [
        ("calcEffectiveTaxRate", calcEffectiveTaxRate),
        ("calcTaxCashConversion", calcTaxCashConversion),
        ("calcDeferredTax", calcDeferredTax),
    ]:
        try:
            result = fn(c)
            info = check_result(fn_name, result)
            print(f"  {fn_name}: {info['status']} | periods={info.get('periods','-')} | range={info.get('period_range','-')} | fields={info.get('non_none_fields','-')}/{info.get('total_fields','-')}")
            if info.get('status') == 'OK' and result and result.get('history'):
                h0 = result['history'][0]
                print(f"    latest: {json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in h0.items()}, ensure_ascii=False)}")
        except Exception as e:
            print(f"  {fn_name}: ERROR - {e}")

    try:
        flags = calcTaxFlags(c)
        print(f"  flags: {flags}")
    except Exception as e:
        print(f"  flags: ERROR - {e}")

    # ── scorecard 확장 검증 ──
    print(f"\n--- scorecard (8영역) ---")
    from dartlab.analysis.financial.scorecard import calcScorecard, calcPiotroskiDetail, calcSummaryFlags

    sc = calcScorecard(c)
    if sc:
        print(f"  areas: {len(sc['items'])}개")
        for item in sc['items']:
            print(f"    {item['area']}: {item['grade']}")
    else:
        print(f"  scorecard: NONE")

    pio = calcPiotroskiDetail(c)
    if pio:
        print(f"  Piotroski: {pio['total']}/9 ({pio['interpretation']})")

    flags = calcSummaryFlags(c)
    print(f"  summaryFlags: {len(flags)}개")
    for f in flags[:5]:
        print(f"    - {f}")
    if len(flags) > 5:
        print(f"    ... +{len(flags)-5}개 더")

    del c

# 종목별 순차 실행 (메모리 안전)
for code, name in STOCKS:
    test_stock(code, name)
    import gc
    gc.collect()

print("\n\n===== 검증 완료 =====")
