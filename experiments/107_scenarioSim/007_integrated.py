"""107-007 — P1+P2+P3 통합 8개 기업 재검증.

004: 마진 비율 블렌딩 (이익 편차 -29% → -4.4%)
005: 분기 재예측 (Q1 시점 연간 착지 오차 2.1%)
006: DCF 3년 체인 (역전 해소)

이 3가지를 모두 적용하여 003의 8개 기업을 재검증.
003 대비 개선 측정.

사용법::

    uv run python -X utf8 experiments/107_scenarioSim/007_integrated.py
"""

from __future__ import annotations

import gc
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

_ROOT = Path(__file__).resolve().parent
_RESULT_FILE = _ROOT / "integrated_results.json"

COMPANIES = [
    {"code": "005930", "name": "삼성전자",  "growth": [15.0, 10.0, 7.0], "histW": 0.5},
    {"code": "000660", "name": "SK하이닉스", "growth": [30.0, 20.0, 12.0], "histW": 0.5},
    {"code": "005380", "name": "현대차",    "growth": [8.0, 5.0, 3.0], "histW": 0.5},
    {"code": "035420", "name": "NAVER",    "growth": [12.0, 10.0, 8.0], "histW": 0.5},
    {"code": "068270", "name": "셀트리온",   "growth": [20.0, 15.0, 10.0], "histW": 0.5},
    {"code": "004020", "name": "현대제철",   "growth": [-5.0, -2.0, 1.0], "histW": 0.3},
    {"code": "030200", "name": "KT",       "growth": [3.0, 2.0, 2.0], "histW": 0.5},
    {"code": "034730", "name": "SK",       "growth": [10.0, 7.0, 5.0], "histW": 0.5},
]


def _qvals(is_df, sid: str, year: str) -> list[float]:
    row = is_df.filter(is_df["snakeId"] == sid)
    if row.height == 0:
        return []
    vals = []
    for q in range(1, 5):
        col = f"{year}Q{q}"
        if col in row.columns:
            v = row[col].to_list()[0]
            vals.append(float(v) if v is not None else 0)
    return vals if len(vals) == 4 else []


def _seasonality(is_df, sid: str, years: list[str]) -> list[float]:
    all_w = []
    for y in years:
        qv = _qvals(is_df, sid, y)
        if len(qv) == 4:
            t = sum(abs(v) for v in qv)
            if t > 0:
                all_w.append([abs(v)/t for v in qv])
    if not all_w:
        return [0.25]*4
    n = len(all_w)
    avg = [sum(w[q] for w in all_w)/n for q in range(4)]
    s = sum(avg)
    return [w/s for w in avg] if s > 0 else [0.25]*4


def _judge(actual, bull, base, bear, tol=0.05):
    if base == 0:
        return "unknown"
    dev = (actual - base) / abs(base)
    if abs(dev) <= tol:
        return "on_track"
    elif actual >= bull:
        return "outperform"
    elif actual <= bear:
        return "underperform_severe"
    elif dev > 0:
        return "outperform_mild"
    else:
        return "underperform"


def _reforecast(qTargets, actuals, trendFactor=0.0):
    nA = len(actuals)
    ytdA = sum(actuals)
    ytdT = sum(qTargets[:nA])
    remaining = sum(qTargets[nA:])
    return ytdA + remaining  # 단순 방식 (005에서 추세보다 안정적 확인)


def _scenarioDCF(projections, wacc_pct, netDebt=0, shares=1):
    wacc = wacc_pct / 100
    if wacc <= 0.02:
        wacc = 0.07
    pvFcf = sum(p.fcf / (1 + wacc) ** (i + 1) for i, p in enumerate(projections))
    lastP = projections[-1]
    normFcf = lastP.ocf - lastP.depreciation
    if normFcf <= 0:
        normFcf = lastP.ocf * 0.3
    tv = normFcf * 1.02 / (wacc - 0.02)
    pvTv = tv / (1 + wacc) ** len(projections)
    ev = pvFcf + pvTv
    eq = ev - netDebt
    return int(eq / shares) if shares > 0 else 0


def _analyzeOne(comp: dict) -> dict | None:
    from dartlab import Company
    from dartlab.core.finance.proforma import build_proforma, extract_historical_ratios

    code = comp["code"]
    try:
        c = Company(code)
        ts = c.finance.timeseries
        fullSeries = ts[0] if isinstance(ts, tuple) else ts
        periods = ts[1] if isinstance(ts, tuple) else []
        is_df = c.IS

        cutIdx = periods.index("2023-Q4") + 1
        series = {stmt: {k: v[:cutIdx] for k, v in fullSeries[stmt].items()} for stmt in ["IS", "BS", "CF"]}

        ratios = extract_historical_ratios(series)
        rev23 = sum(_qvals(is_df, "sales", "2023"))
        gp23 = sum(_qvals(is_df, "gross_profit", "2023"))
        baseGM = gp23 / rev23 * 100 if rev23 else ratios.gross_margin

        # P1: 블렌딩
        hw = comp["histW"]
        blendedGM = baseGM * (1 - hw) + ratios.gross_margin * hw

        # 3년 ProForma (P3)
        growthPath = comp["growth"]
        bullPath = [g * 1.5 if g > 0 else g * 0.5 for g in growthPath]
        bearPath = [g * 0.3 if g > 0 else g * 1.5 for g in growthPath]

        pfResults = {}
        for scName, path, gmAdj in [
            ("bull", bullPath, blendedGM + 2),
            ("base", growthPath, blendedGM),
            ("bear", bearPath, blendedGM - 2),
        ]:
            try:
                pf = build_proforma(series, revenue_growth_path=path, scenario_name=scName, overrides={"gross_margin": gmAdj})
                if pf.projections:
                    pfResults[scName] = pf
            except (KeyError, ValueError, ZeroDivisionError, TypeError):
                pass

        if "base" not in pfResults:
            del c; gc.collect()
            return None

        # 실적
        rev24Q = _qvals(is_df, "sales", "2024")
        oi24Q = _qvals(is_df, "operating_profit", "2024")
        if not rev24Q or not oi24Q:
            del c; gc.collect()
            return None

        # 계절성 + 분기 목표
        revW = _seasonality(is_df, "sales", ["2021", "2022", "2023"])
        oiW = _seasonality(is_df, "operating_profit", ["2021", "2022", "2023"])

        qTargets = {}
        for sc in ["bull", "base", "bear"]:
            pf = pfResults.get(sc)
            if not pf:
                continue
            p = pf.projections[0]
            qTargets[sc] = {"rev": [p.revenue * w for w in revW], "oi": [p.operating_income * w for w in oiW]}

        # 분기 판정
        judgments = []
        for q in range(4):
            revPath = _judge(
                rev24Q[q],
                qTargets.get("bull", {}).get("rev", [0]*4)[q],
                qTargets["base"]["rev"][q],
                qTargets.get("bear", {}).get("rev", [0]*4)[q],
            )
            oiPath = _judge(
                oi24Q[q],
                qTargets.get("bull", {}).get("oi", [0]*4)[q],
                qTargets["base"]["oi"][q],
                qTargets.get("bear", {}).get("oi", [0]*4)[q],
            )
            judgments.append({"q": f"Q{q+1}", "revPath": revPath, "oiPath": oiPath})

        # P2: 분기 재예측 (Q1~Q3 시점)
        reforecasts = []
        for q in range(1, 4):
            rf = _reforecast(qTargets["base"]["rev"], rev24Q[:q])
            reforecasts.append({"atQ": q, "revForecast": round(rf / 1e12, 1)})

        # DCF (P3: 3년 체인)
        dcfValues = {}
        for sc in ["bull", "base", "bear"]:
            pf = pfResults.get(sc)
            if not pf or len(pf.projections) < 2:
                continue
            p1 = pf.projections[0]
            netDebt = (p1.short_term_debt + p1.long_term_debt) - p1.cash
            shares = 5969782550 if code == "005930" else 1  # 삼성만 정확, 나머지 EV로
            dcfValues[sc] = _scenarioDCF(pf.projections, pf.wacc, netDebt=netDebt, shares=shares)

        # 연간 요약
        baseP = pfResults["base"].projections[0]
        actualRev = sum(rev24Q)
        actualOI = sum(oi24Q)

        result = {
            "code": code,
            "name": comp["name"],
            "baseRev_조": round(baseP.revenue / 1e12, 1),
            "actualRev_조": round(actualRev / 1e12, 1),
            "revDev": round((actualRev - baseP.revenue) / abs(baseP.revenue) * 100, 1),
            "baseOI_조": round(baseP.operating_income / 1e12, 1),
            "actualOI_조": round(actualOI / 1e12, 1),
            "oiDev": round((actualOI - baseP.operating_income) / abs(baseP.operating_income) * 100 if baseP.operating_income else 0, 1),
            "judgments": judgments,
            "reforecasts": reforecasts,
            "dcf": dcfValues if code == "005930" else {},
        }

        del c; gc.collect()
        return result

    except Exception as e:
        print(f"    [ERR] {code}: {e}")
        gc.collect()
        return None


def main():
    print("=" * 70)
    print("107-007 통합 검증 (P1+P2+P3)")
    print("=" * 70)

    results = []
    for i, comp in enumerate(COMPANIES):
        print(f"\n[{i+1}/{len(COMPANIES)}] {comp['name']} ({comp['code']})")
        r = _analyzeOne(comp)
        if r:
            results.append(r)
            print(f"  매출: {r['baseRev_조']}조 vs {r['actualRev_조']}조 ({r['revDev']:+.1f}%)")
            print(f"  이익: {r['baseOI_조']}조 vs {r['actualOI_조']}조 ({r['oiDev']:+.1f}%)")
        else:
            print(f"  분석 실패")

    # ── 요약 ──
    n = len(results)
    print(f"\n{'='*70}")
    print(f"003 vs 007 비교 ({n}개 기업)")
    print(f"{'='*70}")

    # 003 결과 (하드코딩 — 003에서 측정된 값)
    prev = {
        "005930": {"revDev": 1.0, "oiDev": -29.0},
        "000660": {"revDev": 55.4, "oiDev": 292.6},
        "005380": {"revDev": -0.3, "oiDev": 22.5},
        "035420": {"revDev": -0.9, "oiDev": 119.5},
        "068270": {"revDev": 36.2, "oiDev": -41.8},
        "004020": {"revDev": -5.7, "oiDev": -85.9},
        "030200": {"revDev": -2.7, "oiDev": -72.9},
        "034730": {"revDev": -13.3, "oiDev": -57.5},
    }

    print(f"\n  {'기업':10s} | {'매출003':>8s} {'매출007':>8s} | {'이익003':>8s} {'이익007':>8s} | {'이익개선':>6s}")
    print(f"  {'-'*65}")
    totalOiImproved = 0
    for r in results:
        p = prev.get(r["code"], {})
        oiPrev = p.get("oiDev", 0)
        oiNow = r["oiDev"]
        improved = abs(oiNow) < abs(oiPrev)
        if improved:
            totalOiImproved += 1
        print(f"  {r['name']:10s} | {p.get('revDev', 0):>+7.1f}% {r['revDev']:>+7.1f}% | {oiPrev:>+7.1f}% {oiNow:>+7.1f}% | {'✅' if improved else '❌'}")

    # 정확도
    revOk = sum(1 for r in results if abs(r["revDev"]) <= 10)
    oiOk = sum(1 for r in results if abs(r["oiDev"]) <= 30)
    prevOiOk = sum(1 for code, p in prev.items() if abs(p["oiDev"]) <= 30)

    print(f"\n  매출 ±10%: {revOk}/{n} (003: 5/8)")
    print(f"  이익 ±30%: {oiOk}/{n} (003: {prevOiOk}/8)")
    print(f"  이익 개선: {totalOiImproved}/{n}")

    # P2: 재예측 정확도
    print(f"\n  --- 분기 재예측 정확도 (매출, Q3 시점) ---")
    for r in results:
        rf = [x for x in r.get("reforecasts", []) if x["atQ"] == 3]
        if rf:
            rfRev = rf[0]["revForecast"]
            err = abs(rfRev - r["actualRev_조"]) / r["actualRev_조"] * 100
            print(f"  {r['name']:10s}: Q3 착지 {rfRev}조 vs 실제 {r['actualRev_조']}조 (오차 {err:.1f}%)")

    # 저장
    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump({"date": datetime.now().strftime("%Y-%m-%d"), "results": results}, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {_RESULT_FILE}")

    gc.collect()


from datetime import datetime

if __name__ == "__main__":
    main()
