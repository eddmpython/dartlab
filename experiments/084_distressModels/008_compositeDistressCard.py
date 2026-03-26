"""실험 ID: 008
실험명: 5축 복합 부실 스코어카드 — Phase 1~3 통합

목적:
- Phase 1(정량 모델) + Phase 2(감사 Red Flag) + Phase 3(시계열 패턴)을 통합한 복합 스코어카드
- 5개 축(정량 부실, 이익 품질, 감사 위험, 추세 악화, 우발부채)으로 종합 판단
- 엔진 흡수용 최종 프로토타입

가설:
1. 5축 통합이 004의 정량 전용 앙상블보다 위험 기업 식별에 우수할 것
2. 감사/추세/우발부채 축이 정량 모델이 놓치는 위험을 보완할 것
3. 금융업은 정량 축에서 고위험이지만, 감사/추세 축에서 안전하여 균형될 것

방법:
1. 5개 축 각 0~100점 (100=최위험):
   - Axis 1: 정량 부실 (Z'', O, X 정규화 가중평균)
   - Axis 2: 이익 품질 (Beneish M + Sloan Accrual + F-Score 역수)
   - Axis 3: 감사 위험 (비적정, 감사인 교체 빈도, 보수 급변, 내부통제)
   - Axis 4: 추세 악화 (연속적자, ICR<1, CF적자, 부채 상승)
   - Axis 5: 우발부채 (채무보증/자본, 소송 건수)
2. 종합 = 가중 평균 (정량 30%, 이익품질 15%, 감사 20%, 추세 25%, 우발부채 10%)
3. distressLevel 5단계

결과 (실험 후 작성):
- 20/20 종목 5축 복합 점수 산출 성공
- 종합 점수: 2.5 (LG, 최안전) ~ 45.2 (삼성증권, 최위험)
- 등급 분포: safe(10), watch(7), warning(3), danger(0), critical(0)
  - warning: KB금융(36.9), 신한지주(35.4), 삼성증권(45.2) — 모두 금융업
  - watch: 현대차, 위메이드, 대한항공, 한화, S-Oil, SK, 삼성생명
- 축별 위험 Top:
  - 정량: 삼성증권(60), 한화(57), 삼성생명(56) — 금융/고부채
  - 이익품질: 현대차(89), 삼성증권(89), 넷마블(89) — F-Score 1점
  - 감사: 삼성증권(70) — 비적정 의견 파싱 + 보수 급변 + 교체
  - 추세: 현대차(30), 위메이드(30), SK(30) — 연속적자/ICR<1
  - 우발부채: KB금융(30), 대한항공(30) — 다수 소송
- 004 대비: warning이 3개→3개 유지, watch가 2→7개로 세분화 향상

결론:
- **가설 1 채택**: 5축 통합이 004 정량 앙상블(safe/watch/warning/danger)보다 중간 구간(watch) 변별력 향상
- **가설 2 채택**: 감사축이 삼성증권(70점) 식별, 추세축이 위메이드/SK 식별 — 정량 모델 보완
- **가설 3 부분 채택**: 금융업이 정량(55~60)에서 높지만 추세(0~15)에서 낮아 종합 35~45 수준.
  다만 여전히 warning 3개 모두 금융업 → 금융업 정량 보정이 불완전
- **이익품질 축 재보정 필요**: F-Score 1점인 현대차/넷마블이 89점으로 과대. F-Score만으로는
  이익 품질 전체를 대표하지 못함 → Beneish/Sloan 산출률 개선 또는 가중치 하향
- **엔진 흡수 방향**: insight/distress.py에 5축 계산기 + distressLevel 구현.
  금융업 정량축 별도 가중치, 이익품질축 F-Score 가중치 하향

실험일: 2026-03-22
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab import Company
from dartlab.core.finance.ratios import calcRatios


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


# ── Axis 1: 정량 부실 (0~100) ──
def axis_quantitative(ratios, series: dict, is_fin: bool) -> float:
    ta = ratios.totalAssets
    if not ta or ta <= 0:
        return 50.0  # 데이터 부족 시 중립

    tl = ratios.totalLiabilities or 0
    ca = ratios.currentAssets or 0
    cl = ratios.currentLiabilities or 0
    ni = ratios.netIncomeTTM or 0
    ocf = ratios.operatingCashflowTTM or 0
    eq = ratios.totalEquity or 0
    re = ratios.retainedEarnings or 0
    ebit = ratios.operatingIncomeTTM or 0

    scores = []

    # O-Score → P(부도)
    np_s = series.get("IS", {}).get("net_profit", []) or series.get("IS", {}).get("net_income", [])
    intwo = 0.0
    if len(np_s) >= 2:
        last = [v for v in np_s[-2:] if v is not None]
        if len(last) == 2 and all(v < 0 for v in last):
            intwo = 1.0
    chin = 0.0
    if len(np_s) >= 2 and np_s[-1] is not None and np_s[-2] is not None:
        d = abs(np_s[-1]) + abs(np_s[-2])
        if d > 0:
            chin = (np_s[-1] - np_s[-2]) / d

    size = math.log(ta / 1e8) if ta > 0 else 0
    o = -1.32 - 0.407*size + 6.03*(tl/ta) - 1.43*((ca-cl)/ta) + 0.0757*(cl/ca if ca > 0 else 0) - 1.72*(1.0 if tl > ta else 0.0) - 2.37*(ni/ta) - 1.83*(ocf/tl if tl > 0 else 0) + 0.285*intwo - 0.521*chin
    p_o = 1 / (1 + math.exp(-o))
    scores.append(p_o * 100)

    # Z''-Score
    if tl > 0:
        wc = ca - cl
        zpp = 6.56*(wc/ta) + 3.26*(re/ta) + 6.72*(ebit/ta) + 1.05*(eq/tl)
        zpp_score = _clamp((2.60 - zpp) / (2.60 - 1.10) * 100)
        scores.append(zpp_score)

    # X-Score (비금융만)
    if not is_fin:
        nita = ni / ta
        tlta = tl / ta
        cacl = ca / cl if cl > 0 else 1.0
        x = -4.336 - 4.513*nita + 5.679*tlta + 0.004*cacl
        scores.append(normal_cdf(x) * 100)

    return sum(scores) / len(scores) if scores else 50.0


# ── Axis 2: 이익 품질 (0~100) ──
def axis_earnings_quality(ratios) -> float:
    scores = []

    # Beneish M-Score
    if ratios.beneishMScore is not None:
        m_score = _clamp((ratios.beneishMScore + 2.22) / 2 * 100)
        scores.append(m_score)

    # Sloan Accrual (> 10% 위험)
    if ratios.sloanAccrualRatio is not None:
        accrual_score = _clamp(ratios.sloanAccrualRatio / 20 * 100)  # 20%에서 100
        scores.append(accrual_score)

    # F-Score 역수 (0점=100위험, 9점=0위험)
    if ratios.piotroskiFScore is not None:
        f_score = _clamp((9 - ratios.piotroskiFScore) / 9 * 100)
        scores.append(f_score)

    return sum(scores) / len(scores) if scores else 50.0


# ── Axis 3: 감사 위험 (0~100) ──
def axis_audit_risk(code: str) -> float:
    score = 0.0
    count = 0

    try:
        from dartlab.providers.dart.docs.finance.audit.pipeline import audit
        result = audit(code)
        if result and result.opinionDf is not None:
            df = result.opinionDf
            # 비적정 의견
            if "opinion" in df.columns:
                for op in df["opinion"].to_list():
                    if op and "적정" not in str(op):
                        score += 50
                        count += 1
                        break
            # 감사인 교체
            if "auditor" in df.columns:
                auditors = df["auditor"].to_list()
                changes = sum(1 for i in range(1, len(auditors)) if auditors[i] and auditors[i-1] and auditors[i] != auditors[i-1])
                if changes >= 3:
                    score += 30
                elif changes >= 2:
                    score += 10
                count += 1

        if result and result.feeDf is not None and "actualFee" in result.feeDf.columns:
            fees = result.feeDf["actualFee"].to_list()
            for i in range(1, len(fees)):
                if fees[i] is not None and fees[i-1] is not None and fees[i-1] > 0:
                    chg = abs((fees[i] - fees[i-1]) / fees[i-1]) * 100
                    if chg > 50:
                        score += 20
                        break
                    elif chg > 30:
                        score += 10
                        break
            count += 1
    except Exception:
        pass

    try:
        from dartlab.providers.dart.docs.finance.internalControl.pipeline import internalControl
        ic = internalControl(code)
        if ic and ic.controlDf is not None and "hasWeakness" in ic.controlDf.columns:
            if any(w for w in ic.controlDf["hasWeakness"].to_list() if w):
                score += 40
            count += 1
    except Exception:
        pass

    return _clamp(score) if count > 0 else 0.0


# ── Axis 4: 추세 악화 (0~100) ──
def axis_trend(series: dict) -> float:
    score = 0.0

    # 순이익 연속적자
    np_s = series.get("IS", {}).get("net_profit", []) or series.get("IS", {}).get("net_income", [])
    streak = 0
    for v in reversed(np_s):
        if v is not None and v < 0:
            streak += 1
        else:
            break
    if streak >= 4:
        score += 40
    elif streak >= 3:
        score += 25
    elif streak >= 2:
        score += 10

    # 영업CF 연속적자
    ocf_s = series.get("CF", {}).get("operating_cashflow", [])
    cf_streak = 0
    for v in reversed(ocf_s):
        if v is not None and v < 0:
            cf_streak += 1
        else:
            break
    if cf_streak >= 3:
        score += 30
    elif cf_streak >= 2:
        score += 15

    # ICR<1 연속
    op = series.get("IS", {}).get("operating_profit", []) or series.get("IS", {}).get("operating_income", [])
    fc = series.get("IS", {}).get("finance_costs", []) or series.get("IS", {}).get("interest_expense", [])
    if op and fc:
        icr_streak = 0
        for i in range(len(op) - 1, -1, -1):
            if i < len(fc) and op[i] is not None and fc[i] is not None and fc[i] > 0:
                if op[i] / fc[i] < 1:
                    icr_streak += 1
                else:
                    break
            else:
                break
        if icr_streak >= 4:
            score += 30
        elif icr_streak >= 2:
            score += 15

    return _clamp(score)


# ── Axis 5: 우발부채 (0~100) ──
def axis_contingent(code: str, equity: float | None) -> float:
    score = 0.0
    try:
        from dartlab.providers.dart.docs.finance.contingentLiability.pipeline import contingentLiability
        cl = contingentLiability(code)
        if cl:
            if cl.lawsuitDf is not None:
                n = len(cl.lawsuitDf)
                if n > 20:
                    score += 30
                elif n > 5:
                    score += 15
                elif n > 0:
                    score += 5

            if cl.guaranteeDf is not None and "totalGuaranteeAmount" in cl.guaranteeDf.columns:
                amounts = cl.guaranteeDf["totalGuaranteeAmount"].to_list()
                total = sum(a for a in amounts if a is not None)
                if equity and equity > 0 and total > 0:
                    ratio = total / equity * 100
                    if ratio > 50:
                        score += 40
                    elif ratio > 20:
                        score += 20
                    elif ratio > 5:
                        score += 10
    except Exception:
        pass

    return _clamp(score)


def distress_level(score: float) -> str:
    if score < 15:
        return "safe"
    if score < 30:
        return "watch"
    if score < 50:
        return "warning"
    if score < 70:
        return "danger"
    return "critical"


TEST_STOCKS = [
    ("005930", "삼성전자"), ("000660", "SK하이닉스"), ("035420", "NAVER"),
    ("068270", "셀트리온"), ("003550", "LG"), ("005380", "현대차"),
    ("263750", "펄어비스"), ("112040", "위메이드"),
    ("105560", "KB금융"), ("055550", "신한지주"),
    ("003490", "대한항공"), ("000880", "한화"),
    ("016360", "삼성증권"), ("010950", "S-Oil"),
    ("041510", "에스엠"), ("251270", "넷마블"),
    ("009150", "삼성전기"), ("066570", "LG전자"),
    ("034730", "SK"), ("032830", "삼성생명"),
]

FIN_NAMES = {"KB금융", "신한지주", "삼성증권", "삼성생명"}
WEIGHTS = {"quant": 0.30, "quality": 0.15, "audit": 0.20, "trend": 0.25, "contingent": 0.10}


if __name__ == "__main__":
    print("=" * 130)
    print("실험 008: 5축 복합 부실 스코어카드")
    print("=" * 130)

    results = []
    for code, name in TEST_STOCKS:
        try:
            c = Company(code)
            build = c.finance.annual
            if not build:
                continue
            series, years = build

            # timeseries for ratios
            ts_build = c.finance.timeseries
            if not ts_build:
                continue
            ts, _ = ts_build
            ratios = calcRatios(ts)
            is_fin = name in FIN_NAMES

            a1 = axis_quantitative(ratios, ts, is_fin)
            a2 = axis_earnings_quality(ratios)
            a3 = axis_audit_risk(code)
            a4 = axis_trend(series)
            a5 = axis_contingent(code, ratios.totalEquity)

            composite = (
                WEIGHTS["quant"] * a1
                + WEIGHTS["quality"] * a2
                + WEIGHTS["audit"] * a3
                + WEIGHTS["trend"] * a4
                + WEIGHTS["contingent"] * a5
            )
            level = distress_level(composite)

            results.append({
                "name": name, "is_fin": is_fin,
                "a1": round(a1, 1), "a2": round(a2, 1),
                "a3": round(a3, 1), "a4": round(a4, 1), "a5": round(a5, 1),
                "composite": round(composite, 1), "level": level,
            })
            del c
        except Exception as e:
            print(f"  {name}: {e}")

    # ── 결과 ──
    print(f"\n{'종목':>12} {'종합':>6} {'등급':>8} {'정량':>6} {'이익Q':>6} {'감사':>6} {'추세':>6} {'우발':>6} {'금융':>4}")
    print("-" * 130)

    for r in sorted(results, key=lambda x: x["composite"], reverse=True):
        fin = "Y" if r["is_fin"] else ""
        print(f"  {r['name']:>10} {r['composite']:>6.1f} {r['level']:>8} "
              f"{r['a1']:>6.1f} {r['a2']:>6.1f} {r['a3']:>6.1f} {r['a4']:>6.1f} {r['a5']:>6.1f} {fin:>4}")

    # ── 004 앙상블과 비교 ──
    print("\n" + "=" * 130)
    print("등급 분포")
    print("-" * 130)
    from collections import Counter
    levels = Counter(r["level"] for r in results)
    for lv in ["critical", "danger", "warning", "watch", "safe"]:
        names = [r["name"] for r in results if r["level"] == lv]
        print(f"  {lv:>10}: {levels.get(lv, 0)}개 — {', '.join(names) if names else '-'}")

    # ── 축별 top 5 ──
    print("\n" + "=" * 130)
    print("축별 위험 Top 5")
    print("-" * 130)
    for axis_name, key in [("정량 부실", "a1"), ("이익 품질", "a2"), ("감사 위험", "a3"), ("추세 악화", "a4"), ("우발부채", "a5")]:
        top5 = sorted(results, key=lambda x: x[key], reverse=True)[:5]
        names = ", ".join(f"{r['name']}({r[key]:.0f})" for r in top5)
        print(f"  {axis_name:>10}: {names}")

    print(f"\n총 {len(results)}개 종목 5축 분석 완료")
