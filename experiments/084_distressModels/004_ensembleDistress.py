"""실험 ID: 004
실험명: 앙상블 부실 점수 — 다중 모델 가중 투표 프로토타입

목적:
- 001~003에서 검증된 5개 부도 예측 모델을 정규화하여 단일 부실 점수로 통합
- 가중 투표 방식의 앙상블 프로토타입 구축
- distressLevel (safe/watch/warning/danger/critical) 5단계 분류 기준 도출

가설:
1. 정규화된 앙상블 점수가 개별 모델보다 안정적인 순위 배열을 제공할 것
2. F-Score(이익 품질)와 Beneish M-Score(조작 의심)를 앙상블에 포함하면 정보량 증가
3. 금융업/비금융업 분리 앙상블이 단일 앙상블보다 적절할 것

방법:
1. 각 모델을 0~1 정규화 (0=안전, 1=위험)
   - Z-Score: max(0, min(1, (2.99 - z) / (2.99 - 1.81)))
   - Z''-Score: max(0, min(1, (2.60 - z) / (2.60 - 1.10)))
   - O-Score: 1 / (1 + e^(-O))  (원래 P(부도))
   - X-Score: Φ(X)
   - Taffler: max(0, min(1, (5 - T) / 10))  (한국 재보정)
   - Beneish: max(0, min(1, (M + 2.22) / 2))  (> -2.22 위험)
   - Piotroski: max(0, min(1, (9 - F) / 9))  (0점=최위험)
2. 가중 평균 (Z'':0.20, O:0.25, X:0.15, Taffler:0.10, Beneish:0.15, Piotroski:0.15)
3. 5단계 분류: <0.15 safe, <0.30 watch, <0.50 warning, <0.70 danger, ≥0.70 critical

결과 (실험 후 작성):
- 20/20 종목 앙상블 부실 점수 산출 성공
- 앙상블 범위: 0.020 (삼성전자) ~ 0.586 (삼성증권)
- 등급 분포:
  - safe (8개): 삼성전자, SK하이닉스, NAVER, 셀트리온, LG, 펄어비스, 에스엠, 삼성전기
  - watch (2개): 넷마블, LG전자
  - warning (7개): 현대차, 위메이드, 대한항공, 한화, S-Oil, SK, 삼성생명
  - danger (3개): KB금융, 신한지주, 삼성증권
  - critical (0개)
- 금융업 평균: 0.540 vs 비금융업 평균: 0.195 → 업종 특성 반영됨
- 개별 모델에서 과잉탐지(Springate 80%)나 과소탐지(Taffler 0%)였던 것이 앙상블에서 균형
- Beneish M-Score는 대한항공만 산출 → 대부분 종목에서 가중치 재배분

결론:
- **가설 1 채택**: 앙상블 순위가 직관적. 대형 우량주 하위, 고부채/적자 이력 상위 배열
- **가설 2 부분 채택**: Beneish 산출률이 낮아(1/20) 정보 기여 제한적. F-Score는 보조 효과
- **가설 3 채택**: 금융업 평균 0.54 vs 비금융 0.20 → Z-Score 제외(is_financial=True)가
  과소 보정하므로, 금융업 전용 cutoff 또는 업종별 백분위 정규화 필요
- **5단계 분류 기준**: safe<0.15, watch<0.30, warning<0.50, danger<0.70, critical≥0.70
  현재 cutoff가 합리적이나, 금융업은 별도 기준 검토 필요
- **엔진 흡수 방향**: engines/insight/distress.py에 앙상블 계산기 구현.
  detector.py 금융업 감지와 연동하여 업종별 가중치/cutoff 분리

실험일: 2026-03-22
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab import Company
from dartlab.engines.common.finance.ratios import calcRatios


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def normalize_scores(*, z=None, zpp=None, o=None, x=None, t=None, m=None, f=None, is_financial=False):
    """각 모델 점수를 0~1로 정규화 (0=안전, 1=위험)."""
    scores = {}
    weights = {}

    # Z-Score (비금융만)
    if z is not None and not is_financial:
        scores["Z"] = _clamp((2.99 - z) / (2.99 - 1.81))
        weights["Z"] = 0.15

    # Z''-Score
    if zpp is not None:
        scores["Z''"] = _clamp((2.60 - zpp) / (2.60 - 1.10))
        weights["Z''"] = 0.20

    # O-Score → P(bankruptcy)
    if o is not None:
        scores["O"] = _clamp(1 / (1 + math.exp(-o)))
        weights["O"] = 0.25

    # X-Score → Φ(X)
    if x is not None:
        scores["X"] = _clamp(normal_cdf(x))
        weights["X"] = 0.15

    # Taffler (한국 재보정: T<5 → 주의)
    if t is not None:
        scores["T"] = _clamp((5 - t) / 10)
        weights["T"] = 0.10

    # Beneish M-Score
    if m is not None:
        scores["M"] = _clamp((m + 2.22) / 2)
        weights["M"] = 0.15

    # Piotroski F-Score (0=최위험, 9=최안전)
    if f is not None:
        scores["F"] = _clamp((9 - f) / 9)
        weights["F"] = 0.10 if "M" in scores else 0.15

    return scores, weights


def ensemble_score(scores: dict, weights: dict) -> float | None:
    """가중 평균 앙상블 점수."""
    if not scores:
        return None
    total_w = sum(weights[k] for k in scores)
    if total_w == 0:
        return None
    return sum(scores[k] * weights[k] for k in scores) / total_w


def distress_level(score: float | None) -> str:
    if score is None:
        return "N/A"
    if score < 0.15:
        return "safe"
    if score < 0.30:
        return "watch"
    if score < 0.50:
        return "warning"
    if score < 0.70:
        return "danger"
    return "critical"


# ── 모델 계산 함수들 (001-003에서 검증) ──

def calc_ohlson(ratios, series):
    ta = ratios.totalAssets
    if not ta or ta <= 0:
        return None
    tl = ratios.totalLiabilities or 0
    ca = ratios.currentAssets or 0
    cl = ratios.currentLiabilities or 0
    ni = ratios.netIncomeTTM or 0
    ocf = ratios.operatingCashflowTTM or 0
    size = math.log(ta / 1e8) if ta > 0 else 0
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
    o = -1.32 - 0.407*size + 6.03*(tl/ta) - 1.43*((ca-cl)/ta) + 0.0757*(cl/ca if ca>0 else 0) - 1.72*(1.0 if tl>ta else 0.0) - 2.37*(ni/ta) - 1.83*(ocf/tl if tl>0 else 0) + 0.285*intwo - 0.521*chin
    return round(o, 4)


def calc_zmijewski(ratios):
    ta = ratios.totalAssets
    if not ta or ta <= 0:
        return None
    nita = (ratios.netIncomeTTM or 0) / ta
    tlta = (ratios.totalLiabilities or 0) / ta
    cacl = (ratios.currentAssets / ratios.currentLiabilities) if ratios.currentAssets and ratios.currentLiabilities and ratios.currentLiabilities > 0 else 1.0
    return round(-4.336 - 4.513*nita + 5.679*tlta + 0.004*cacl, 4)


def calc_zpp(ratios):
    ta = ratios.totalAssets
    tl = ratios.totalLiabilities
    if not ta or ta <= 0 or not tl or tl <= 0:
        return None
    wc = (ratios.currentAssets or 0) - (ratios.currentLiabilities or 0)
    z = 6.56*(wc/ta) + 3.26*((ratios.retainedEarnings or 0)/ta) + 6.72*((ratios.operatingIncomeTTM or 0)/ta) + 1.05*((ratios.totalEquity or 0)/tl)
    return round(z, 4)


def calc_taffler(ratios):
    ta = ratios.totalAssets
    cl = ratios.currentLiabilities
    tl = ratios.totalLiabilities
    if not ta or ta <= 0 or not tl or tl <= 0:
        return None
    a = (ratios.operatingIncomeTTM or 0) / cl if cl and cl > 0 else 0
    b = (ratios.currentAssets or 0) / tl
    c = (cl or 0) / ta
    d = ((ratios.currentAssets or 0) / cl * 100) if cl and cl > 0 else 100
    return round(3.20 + 12.18*a + 2.50*b - 10.68*c + 0.029*d, 4)


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


if __name__ == "__main__":
    print("=" * 110)
    print("실험 004: 앙상블 부실 점수 — 다중 모델 가중 투표")
    print("=" * 110)

    results = []
    for code, name in TEST_STOCKS:
        try:
            c = Company(code)
            build = c.finance.timeseries
            if not build:
                continue
            ts, _ = build
            ratios = calcRatios(ts)
            is_fin = name in FIN_NAMES

            z = ratios.altmanZScore
            zpp = calc_zpp(ratios)
            o = calc_ohlson(ratios, ts)
            x = calc_zmijewski(ratios)
            t = calc_taffler(ratios)
            m = ratios.beneishMScore
            f = ratios.piotroskiFScore

            scores, weights = normalize_scores(z=z, zpp=zpp, o=o, x=x, t=t, m=m, f=f, is_financial=is_fin)
            ens = ensemble_score(scores, weights)
            level = distress_level(ens)

            results.append({
                "name": name, "is_fin": is_fin,
                "z": z, "zpp": zpp, "o": o, "x": x, "t": t, "m": m, "f": f,
                "scores": scores, "ensemble": ens, "level": level,
            })
            del c
        except Exception as e:
            print(f"  {name}: {e}")

    # ── 결과 출력 ──
    print(f"\n{'종목':>12} {'앙상블':>8} {'등급':>8} {'Z':>6} {'Z\"\"':>6} {'O':>6} {'X':>6} {'T':>6} {'M':>6} {'F':>6} {'금융':>4}")
    print("-" * 110)

    for r in sorted(results, key=lambda x: x["ensemble"] or 0, reverse=True):
        ens = f"{r['ensemble']:.3f}" if r['ensemble'] is not None else "N/A"
        sc = r["scores"]
        def _fmt(k):
            return f"{sc[k]:.2f}" if k in sc else "  - "
        fin = "Y" if r["is_fin"] else ""
        print(f"  {r['name']:>10} {ens:>8} {r['level']:>8} {_fmt('Z'):>6} {_fmt('Z\"\"'):>6} {_fmt('O'):>6} {_fmt('X'):>6} {_fmt('T'):>6} {_fmt('M'):>6} {_fmt('F'):>6} {fin:>4}")

    # ── 등급 분포 ──
    print("\n" + "=" * 110)
    print("등급 분포")
    print("-" * 110)
    from collections import Counter
    level_counts = Counter(r["level"] for r in results)
    for lv in ["critical", "danger", "warning", "watch", "safe"]:
        cnt = level_counts.get(lv, 0)
        names = [r["name"] for r in results if r["level"] == lv]
        print(f"  {lv:>10}: {cnt}개 — {', '.join(names) if names else '-'}")

    # ── 금융업 vs 비금융업 ──
    print("\n" + "=" * 110)
    print("금융업 vs 비금융업 앙상블 비교")
    print("-" * 110)
    fin_r = [r for r in results if r["is_fin"] and r["ensemble"] is not None]
    nfin_r = [r for r in results if not r["is_fin"] and r["ensemble"] is not None]
    if fin_r:
        print(f"  금융업 평균: {sum(r['ensemble'] for r in fin_r)/len(fin_r):.3f}")
    if nfin_r:
        print(f"  비금융업 평균: {sum(r['ensemble'] for r in nfin_r)/len(nfin_r):.3f}")

    print(f"\n총 {len(results)}개 종목 앙상블 분석 완료")
