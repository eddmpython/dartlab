"""실험 ID: 003
실험명: Taffler Z-Score + Altman Z''-Score (비제조업 변형) 검증

목적:
- Taffler(1983) UK 부도 예측 모델의 한국 시장 적합성 검증
- Altman Z''-Score(1995) 비제조업/신흥시장 변형의 금융업 포함 커버리지 확인
- 5개 모델(Z, Z'', O, X, Taffler) 종합 비교 및 앙상블 가능성 탐색

가설:
1. Taffler Z-Score는 영업이익/유동부채 비중이 커서 수익성 중심 평가
2. Z''-Score는 매출/총자산 항을 제거하여 금융업에서도 유효할 것
3. 5개 모델의 교집합(모두 위험 판정)이 단일 모델보다 정밀할 것

방법:
1. Taffler: T = 3.20 + 12.18×(OP/CL) + 2.50×(CA/TL) - 10.68×(CL/TA) + 0.029×(CR)
   T < 0 → 부도 위험, T > 0 → 안전 (원논문: Taffler 1983)
2. Z''-Score: Z'' = 6.56×(WC/TA) + 3.26×(RE/TA) + 6.72×(EBIT/TA) + 1.05×(BV_Equity/TL)
   Z'' > 2.60 → 안전, 1.10~2.60 → 회색, < 1.10 → 위험 (Altman 1995)
3. 20개 종목 5개 모델 종합 비교표

결과 (실험 후 작성):
- 20/20 종목 Taffler, Z''-Score 모두 산출 성공
- Taffler T-Score: 1.73 (S-Oil) ~ 24.35 (SK하이닉스) → **전 종목 안전 판정** (T>0)
  → Taffler 모델은 한국 시장에서 변별력 부족 (cutoff 재보정 필요)
- Z''-Score: 0.16 (대한항공) ~ 13.00 (LG)
  - 위험(<1.10): 대한항공, KB금융, 신한지주, 한화, 삼성증권, S-Oil, 삼성생명, 위메이드 (8개)
  - 회색(1.10~2.60): 현대차, LG전자, 넷마블 (3개)
  - 안전(>2.60): 삼성전자, SK하이닉스, NAVER, 셀트리온, LG 등 (9개)
- **금융업 커버리지**: Z-Score 전부 불가 → Z''-Score 전부 산출 (0.32~0.67, 모두 위험 구간)
- 위험 교차 분석 (비금융업): SK(Z+Z''), 한화(Z''+X) 2개 모델 동시 위험. 현대차, 위메이드 등 1개
- 5개 모델 종합: Z''-Score가 가장 균형 잡힌 변별력. Taffler는 과소 탐지

결론:
- **가설 1 부분 채택**: Taffler는 영업이익/유동부채 비중이 크지만, 한국 기업 대부분 양호→ 전원 안전
  → cutoff 0이 아닌 한국 시장 재보정 필요 (예: T<5 → 주의 등)
- **가설 2 채택**: Z''-Score가 매출/총자산 항 제거로 금융업 4개 모두 커버. Z-Score 대비 커버리지 확대
- **가설 3 부분 채택**: SK, 한화만 2개 모델 동시 위험. 교집합 종목이 적어 앙상블 효과 제한적
  → 교집합보다는 가중 투표 방식이 적절
- **엔진 흡수 권장**: Z''-Score는 금융업 커버리지 확대로 필수. Taffler는 cutoff 재보정 후 채택 검토

실험일: 2026-03-22
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab import Company
from dartlab.engines.common.finance.ratios import calcRatios


def calc_taffler(ratios) -> dict | None:
    """Taffler Z-Score (1983) UK 모델.

    T = 3.20 + 12.18×(OP/CL) + 2.50×(CA/TL) - 10.68×(CL/TA) + 0.029×(no-credit interval proxy)
    여기서 no-credit interval ≈ (CA - CL) / daily operating expense ≈ CR ratio proxy
    """
    ta = ratios.totalAssets
    cl = ratios.currentLiabilities
    ca = ratios.currentAssets
    tl = ratios.totalLiabilities
    op = ratios.operatingIncomeTTM

    if ta is None or ta <= 0 or tl is None or tl <= 0:
        return None

    a = (op or 0) / cl if cl and cl > 0 else 0
    b = (ca or 0) / tl
    c = (cl or 0) / ta
    # no-credit interval proxy: 유동비율 / 100
    d = ((ca or 0) / cl * 100) if cl and cl > 0 else 100

    t = 3.20 + 12.18 * a + 2.50 * b - 10.68 * c + 0.029 * d

    return {
        "t_score": round(t, 4),
        "zone": "안전" if t > 0 else "위험",
        "variables": {
            "OP/CL": round(a, 4),
            "CA/TL": round(b, 4),
            "CL/TA": round(c, 4),
            "NCI_proxy": round(d, 2),
        },
    }


def calc_altman_z_double_prime(ratios) -> dict | None:
    """Altman Z''-Score (1995) — 비제조업/신흥시장 변형.

    Z'' = 6.56×(WC/TA) + 3.26×(RE/TA) + 6.72×(EBIT/TA) + 1.05×(BV_Equity/TL)
    매출/총자산 항(E) 제거 → 금융업/서비스업 적용 가능
    """
    ta = ratios.totalAssets
    tl = ratios.totalLiabilities

    if ta is None or ta <= 0 or tl is None or tl <= 0:
        return None

    wc = (ratios.currentAssets or 0) - (ratios.currentLiabilities or 0)
    re = ratios.retainedEarnings or 0
    ebit = ratios.operatingIncomeTTM or 0
    eq = ratios.totalEquity or 0

    a = wc / ta
    b = re / ta
    c = ebit / ta
    d = eq / tl

    z = 6.56 * a + 3.26 * b + 6.72 * c + 1.05 * d

    if z > 2.60:
        zone = "안전"
    elif z > 1.10:
        zone = "회색"
    else:
        zone = "위험"

    return {
        "z_score": round(z, 4),
        "zone": zone,
        "variables": {
            "WC/TA": round(a, 4),
            "RE/TA": round(b, 4),
            "EBIT/TA": round(c, 4),
            "Eq/TL": round(d, 4),
        },
    }


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def calc_ohlson(ratios, series) -> float | None:
    """O-Score 간소 계산 (001에서 검증된 로직)."""
    ta = ratios.totalAssets
    if ta is None or ta <= 0:
        return None

    tl = ratios.totalLiabilities or 0
    ca = ratios.currentAssets or 0
    cl = ratios.currentLiabilities or 0
    ni = ratios.netIncomeTTM or 0
    ocf = ratios.operatingCashflowTTM or 0

    size = math.log(ta / 1e8) if ta > 0 else 0
    tlta = tl / ta
    wcta = (ca - cl) / ta
    clca = cl / ca if ca > 0 else 0
    oeneg = 1.0 if tl > ta else 0.0
    nita = ni / ta
    futl = ocf / tl if tl > 0 else 0

    np_series = series.get("IS", {}).get("net_profit", []) or series.get("IS", {}).get("net_income", [])
    intwo = 0.0
    if len(np_series) >= 2:
        last = [v for v in np_series[-2:] if v is not None]
        if len(last) == 2 and all(v < 0 for v in last):
            intwo = 1.0

    chin = 0.0
    if len(np_series) >= 2 and np_series[-1] is not None and np_series[-2] is not None:
        d = abs(np_series[-1]) + abs(np_series[-2])
        if d > 0:
            chin = (np_series[-1] - np_series[-2]) / d

    o = -1.32 - 0.407*size + 6.03*tlta - 1.43*wcta + 0.0757*clca - 1.72*oeneg - 2.37*nita - 1.83*futl + 0.285*intwo - 0.521*chin
    return round(o, 4)


def calc_zmijewski(ratios) -> float | None:
    ta = ratios.totalAssets
    if ta is None or ta <= 0:
        return None
    nita = (ratios.netIncomeTTM or 0) / ta
    tlta = (ratios.totalLiabilities or 0) / ta
    cacl = (ratios.currentAssets / ratios.currentLiabilities) if ratios.currentAssets and ratios.currentLiabilities and ratios.currentLiabilities > 0 else 1.0
    return round(-4.336 - 4.513*nita + 5.679*tlta + 0.004*cacl, 4)


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
    print("=" * 120)
    print("실험 003: Taffler Z-Score + Altman Z''-Score + 5개 모델 종합 비교")
    print("=" * 120)

    results = []
    for code, name in TEST_STOCKS:
        try:
            c = Company(code)
            build = c.finance.timeseries
            if not build:
                continue
            ts, periods = build
            ratios = calcRatios(ts)

            taffler = calc_taffler(ratios)
            zpp = calc_altman_z_double_prime(ratios)
            o = calc_ohlson(ratios, ts)
            x = calc_zmijewski(ratios)

            results.append({
                "name": name,
                "z": ratios.altmanZScore,
                "zpp": zpp["z_score"] if zpp else None,
                "zpp_zone": zpp["zone"] if zpp else "N/A",
                "o": o,
                "x": x,
                "t": taffler["t_score"] if taffler else None,
                "t_zone": taffler["zone"] if taffler else "N/A",
                "f": ratios.piotroskiFScore,
            })
            del c
        except Exception as e:
            print(f"  {name}: {e}")

    # ── 종합 비교표 ──
    zpp_label = "Z''-Score"
    zpp_zone_label = "Z''구간"
    print(f"\n{'종목':>12} {'Z-Score':>9} {zpp_label:>10} {zpp_zone_label:>6} {'O-Score':>9} {'X-Score':>9} {'Taffler':>9} {'T구간':>6} {'F-Score':>8}")
    print("-" * 120)

    for r in results:
        z = f"{r['z']:.2f}" if r["z"] is not None else "N/A"
        zpp = f"{r['zpp']:.2f}" if r["zpp"] is not None else "N/A"
        o = f"{r['o']:.2f}" if r["o"] is not None else "N/A"
        x = f"{r['x']:.2f}" if r["x"] is not None else "N/A"
        t = f"{r['t']:.2f}" if r["t"] is not None else "N/A"
        f = str(r["f"]) if r["f"] is not None else "N/A"
        print(f"  {r['name']:>10} {z:>9} {zpp:>10} {r['zpp_zone']:>6} {o:>9} {x:>9} {t:>9} {r['t_zone']:>6} {f:>8}")

    # ── 위험 판정 교차 분석 ──
    print("\n" + "=" * 120)
    print("위험 판정 교차 분석 (금융업 제외)")
    print("-" * 120)

    fin_names = {"KB금융", "신한지주", "삼성증권", "삼성생명"}
    non_fin = [r for r in results if r["name"] not in fin_names]

    for r in non_fin:
        danger_count = 0
        flags = []
        if r["z"] is not None and r["z"] < 1.81:
            danger_count += 1
            flags.append("Z")
        if r["zpp"] is not None and r["zpp"] < 1.10:
            danger_count += 1
            flags.append("Z''")
        if r["o"] is not None and r["o"] > 0.5:
            danger_count += 1
            flags.append("O")
        if r["x"] is not None and r["x"] > 0:
            danger_count += 1
            flags.append("X")
        if r["t"] is not None and r["t"] < 0:
            danger_count += 1
            flags.append("T")

        if danger_count > 0:
            print(f"  {r['name']:>10}: {danger_count}개 모델 위험 — {', '.join(flags)}")

    # ── Z vs Z'' 비교 (금융업 커버리지) ──
    print("\n" + "=" * 120)
    print("Z-Score vs Z''-Score 금융업 커버리지")
    print("-" * 120)
    for r in results:
        if r["name"] in fin_names:
            z = "불가" if r["z"] is None else f"{r['z']:.2f}"
            zpp = "불가" if r["zpp"] is None else f"{r['zpp']:.2f}"
            print(f"  {r['name']:>10}: Z={z:>8}  Z''={zpp:>8} ({r['zpp_zone']})")

    print(f"\n총 {len(results)}개 종목 5개 모델 비교 완료")
