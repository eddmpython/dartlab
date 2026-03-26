"""실험 ID: 002
실험명: Zmijewski X-Score — 3변수 부도 예측 프로빗 모델

목적:
- Zmijewski(1984) X-Score를 DART 데이터로 계산
- 3변수 간결 모델의 한국 시장 유효성 확인
- O-Score, Z-Score와 삼중 비교

가설:
1. X-Score 3변수(ROA, 부채비율, 유동비율)는 모두 이미 ratios.py에서 계산 중이므로 즉시 적용 가능
2. 간결한 3변수 모델이 9변수 O-Score와 유사한 분류력을 보일 것
3. 금융업의 높은 부채비율이 X-Score를 왜곡할 수 있음

방법:
1. X = -4.336 - 4.513×(NI/TA) + 5.679×(TL/TA) + 0.004×(CA/CL)
   (원논문: Zmijewski 1984, probit 모델)
2. P(bankruptcy) = Φ(X) — 표준정규 누적분포
3. 20개 종목 동일 세트, O-Score/Z-Score와 비교

결과 (실험 후 작성):
- 20/20 종목 X-Score 계산 성공, Springate S-Score도 동시 산출
- X-Score 범위: -3.92 (LG, 최안전) ~ 0.88 (신한지주, 최위험)
- X-Score P(부도)>50%: 신한지주(81%), KB금융(81%), 삼성증권(78%), 삼성생명(77%), 한화(65%)
  → 금융업 4개 + 고부채 한화가 모두 위험 판정
- Springate S-Score<0.862 위험: 16/20종목 → **과잉 탐지** (안전: 삼성전기, 에스엠, 삼성전자, SK하이닉스만)
- Z-Score<1.81 위험: 현대차, SK (2개만)
- 금융업 X-Score 평균: 0.82 vs 비금융업 -2.09 → **금융업 부채비율 왜곡 확인**
- 스피어만 순위: X-Score와 O-Score 방향 일치 (금융업 상위, 대형 제조업 하위)

결론:
- **가설 1 채택**: 3변수 모두 ratios.py에서 이미 계산되는 값. 즉시 추가 가능
- **가설 2 부분 채택**: X-Score는 O-Score와 유사한 순위 배열. 다만 3변수라 세밀도 부족
- **가설 3 채택**: 금융업 X-Score 평균 0.82 vs 비금융 -2.09 → **업종 보정 필수**
- Springate S-Score는 한국 시장에서 cutoff 0.862가 너무 높아 과잉 탐지 (80% 위험 판정)
  → 한국 적용 시 cutoff 하향 조정 필요 (0.3~0.5 범위 재보정 권장)
- **엔진 흡수 시**: X-Score는 금융업 감지(detector.py)와 연동하여 업종별 cutoff 분리 필요

실험일: 2026-03-22
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab import Company
from dartlab.core.finance.ratios import calcRatios


def normal_cdf(x: float) -> float:
    """표준정규 누적분포 근사 (math.erf 기반)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def calc_zmijewski_x_score(ratios) -> dict | None:
    """Zmijewski X-Score 계산.

    X = -4.336 - 4.513×(NI/TA) + 5.679×(TL/TA) + 0.004×(CA/CL)
    """
    ta = ratios.totalAssets
    tl = ratios.totalLiabilities
    ni = ratios.netIncomeTTM
    ca = ratios.currentAssets
    cl = ratios.currentLiabilities

    if ta is None or ta <= 0:
        return None

    nita = (ni or 0) / ta
    tlta = (tl or 0) / ta
    cacl = (ca / cl) if ca and cl and cl > 0 else 1.0

    x = -4.336 - 4.513 * nita + 5.679 * tlta + 0.004 * cacl
    p = normal_cdf(x) * 100

    return {
        "x_score": round(x, 4),
        "p_bankruptcy": round(p, 2),
        "variables": {
            "NITA": round(nita, 4),
            "TLTA": round(tlta, 4),
            "CACL": round(cacl, 4),
        },
    }


def calc_springate_s_score(ratios) -> dict | None:
    """Springate S-Score (1978) — 비교용으로 포함.

    S = 1.03×(WC/TA) + 3.07×(EBIT/TA) + 0.66×(EBT/CL) + 0.4×(Sales/TA)
    S < 0.862 → 부도 위험
    """
    ta = ratios.totalAssets
    if ta is None or ta <= 0:
        return None

    wc = (ratios.currentAssets or 0) - (ratios.currentLiabilities or 0)
    ebit = ratios.operatingIncomeTTM or 0
    ebt = ratios.profitBeforeTax if ratios.profitBeforeTax is not None else (ratios.netIncomeTTM or 0)
    cl = ratios.currentLiabilities
    rev = ratios.revenueTTM or 0

    a = wc / ta
    b = ebit / ta
    c = ebt / cl if cl and cl > 0 else 0
    d = rev / ta

    s = 1.03 * a + 3.07 * b + 0.66 * c + 0.4 * d

    return {
        "s_score": round(s, 4),
        "bankrupt": s < 0.862,
        "variables": {"WC/TA": round(a, 4), "EBIT/TA": round(b, 4), "EBT/CL": round(c, 4), "Sales/TA": round(d, 4)},
    }


# ── 동일 테스트 종목 ──
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


if __name__ == "__main__":
    print("=" * 100)
    print("실험 002: Zmijewski X-Score + Springate S-Score 비교")
    print("=" * 100)

    results = []

    for code, name in TEST_STOCKS:
        try:
            c = Company(code)
            build = c.finance.timeseries
            if not build:
                print(f"  {name}({code}): skip")
                continue

            ts, periods = build
            ratios = calcRatios(ts)

            x_result = calc_zmijewski_x_score(ratios)
            s_result = calc_springate_s_score(ratios)

            if x_result is None:
                continue

            results.append({
                "code": code,
                "name": name,
                "x_score": x_result["x_score"],
                "x_p": x_result["p_bankruptcy"],
                "s_score": s_result["s_score"] if s_result else None,
                "s_bankrupt": s_result["bankrupt"] if s_result else None,
                "z_score": ratios.altmanZScore,
                "f_score": ratios.piotroskiFScore,
                "o_score": None,  # 001에서 계산됨, 여기선 비교 참조만
            })
            del c
        except Exception as e:
            print(f"  {name}({code}): 에러 — {e}")

    # ── 결과 출력 ──
    print(f"\n{'종목':>12} {'X-Score':>10} {'P(부도)%':>10} {'S-Score':>10} {'S위험':>6} {'Z-Score':>10} {'F-Score':>8}")
    print("-" * 100)

    for r in sorted(results, key=lambda x: x["x_score"], reverse=True):
        z = f"{r['z_score']:.2f}" if r["z_score"] is not None else "N/A"
        s = f"{r['s_score']:.4f}" if r["s_score"] is not None else "N/A"
        sb = "위험" if r["s_bankrupt"] else "안전" if r["s_bankrupt"] is not None else "N/A"
        f = str(r["f_score"]) if r["f_score"] is not None else "N/A"
        print(f"  {r['name']:>10} {r['x_score']:>10.4f} {r['x_p']:>9.2f}% {s:>10} {sb:>6} {z:>10} {f:>8}")

    # ── 위험군 비교 ──
    print("\n" + "=" * 100)
    print("모델별 위험 판정 비교")
    print("-" * 100)

    x_danger = {r["name"] for r in results if r["x_p"] > 50}
    s_danger = {r["name"] for r in results if r["s_bankrupt"]}
    z_vals = [r for r in results if r["z_score"] is not None]
    z_danger = {r["name"] for r in z_vals if r["z_score"] < 1.81}

    print(f"  X-Score P>50%: {x_danger or '없음'}")
    print(f"  Springate <0.862: {s_danger or '없음'}")
    print(f"  Z-Score <1.81: {z_danger or '없음'}")

    # 금융업 vs 비금융업 분포
    fin_names = {"KB금융", "신한지주", "삼성증권", "삼성생명"}
    fin = [r for r in results if r["name"] in fin_names]
    non_fin = [r for r in results if r["name"] not in fin_names]

    if fin:
        avg_fin = sum(r["x_score"] for r in fin) / len(fin)
        avg_non = sum(r["x_score"] for r in non_fin) / len(non_fin) if non_fin else 0
        print(f"\n  금융업 X-Score 평균: {avg_fin:.4f}")
        print(f"  비금융업 X-Score 평균: {avg_non:.4f}")
        print(f"  → 금융업 부채비율 효과로 X-Score {'상향' if avg_fin > avg_non else '하향'} 왜곡")

    print(f"\n총 {len(results)}개 종목 분석 완료")
