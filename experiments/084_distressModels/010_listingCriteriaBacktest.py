"""실험 ID: 010
실험명: 관리종목 기준 역추적 — 실제 위기 기업 backtesting

목적:
- Phase 1-3에서 구축한 부실 모델이 실제 위기 기업을 사전 포착할 수 있었는지 검증
- 관리종목/상장폐지/워크아웃 이력이 있는 기업에 모델 적용
- 반대로 대형 안전주에서 false positive가 없는지 확인

가설:
1. 실제 위기 기업은 O-Score, Z''-Score, 앙상블 점수에서 danger/warning 판정을 받을 것
2. 대형 우량주(삼성전자, SK하이닉스)는 safe 판정을 받을 것
3. 복합 스코어카드(008) 5축 점수가 단일 모델보다 정확한 변별력을 보일 것

방법:
1. 위험군: 실제 위기 이력 기업 (상폐/관리종목/워크아웃) 중 DART 데이터 보유 기업
2. 안전군: Phase 1-3에서 safe로 판정된 대형주
3. 각 기업에 O-Score, Z''-Score, 앙상블, 시계열 패턴 적용
4. 위험군/안전군 분리도(separation) 평가

결과 (실험 후 작성):
- 16/16 종목 분석 완료 (위험군 8, 안전군 8)
- **위험군** (평균 앙상블 0.220):
  - danger 3/8: 다우데이타(0.538, 부채913%), 기업은행(0.520, 부채1272%), CJ(0.508)
  - safe 5/8: GS(0.004), 효성(0.008), 현대건설(0.005), 포스코인터(0.119), 롯데케미칼(0.055)
  - 롯데케미칼: safe이나 순적자 3기 연속 패턴 보유
- **안전군** (평균 앙상블 0.081):
  - safe 7/8: 삼성전자(0.000), SK하이닉스(0.000), NAVER(0.001), 현대차(0.109), LG(0.000), LG전자(0.024), 셀트리온(0.001)
  - danger 1/8: 한화(0.513, 부채516%) — **false positive**
- 분리도: 위험군 0.220 vs 안전군 0.081 — 방향 일치하나 격차 작음
- **false positive**: 한화(안전군→danger), 기업은행(금융업 부채 구조적)
- **false negative**: 롯데케미칼(순적자 3기이나 safe), GS/효성(위기 이력이나 safe)

결론:
- **가설 1 부분 채택**: 위험군 danger 3/8(38%). 다우데이타·CJ는 정확 포착.
  그러나 기업은행 danger는 금융업 부채비율 구조적 왜곡 (false positive)
- **가설 2 채택**: 안전군 7/8이 safe (88%). 삼성전자·SK하이닉스 P(부도)=0.0%.
  한화 예외는 방산/화학 복합 지주 특성 → 업종 보정 필요
- **가설 3 부분 기각**: 간이 2모델 앙상블(O+Z'')은 분리도 0.220 vs 0.081로 약함.
  008의 5축 스코어카드가 더 정밀하나, 이번 종목과 동일 대상이 아니므로 직접 비교 불가
- **핵심 한계**:
  1. 위험군 종목 선정이 "과거 워크아웃 계열사" 수준으로, 현재 재무는 이미 회복된 기업 다수
  2. 실제 관리종목/상폐 기업은 DART 데이터가 비공개되어 테스트 불가
  3. 금융업·지주회사 부채비율 왜곡 → 업종별 cutoff 분리 필수
- **엔진 흡수 방향**: 앙상블에 업종 보정(금융업 부채비율 제외, 지주회사 DSO 제외) 적용.
  detector.py 금융업 감지 → 모델별 자동 cutoff 선택

실험일: 2026-03-22
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import math

from dartlab import Company


# ── O-Score 계산 (001에서 가져옴) ──
def calc_ohlson_o_score(series: dict) -> dict | None:
    """Ohlson O-Score 간이 계산."""
    bs = series.get("BS", {})
    is_ = series.get("IS", {})

    ta = bs.get("total_assets", [])
    tl = bs.get("total_liabilities", [])
    wc_ca = bs.get("current_assets", [])
    wc_cl = bs.get("current_liabilities", [])
    ni = is_.get("net_profit", []) or is_.get("net_income", [])
    rev = is_.get("sales", []) or is_.get("revenue", [])

    if not ta or not tl or not ni:
        return None

    ta_v = ta[-1]
    tl_v = tl[-1]
    if not ta_v or ta_v <= 0:
        return None

    ni_v = ni[-1] if ni else 0
    ca_v = wc_ca[-1] if wc_ca else 0
    cl_v = wc_cl[-1] if wc_cl else 0

    size = math.log(ta_v / 1e6) if ta_v > 0 else 0  # 백만원 단위
    tlta = (tl_v or 0) / ta_v
    wcta = ((ca_v or 0) - (cl_v or 0)) / ta_v
    clca = (cl_v or 0) / (ca_v or 1)
    oeneg = 1 if (tl_v or 0) > ta_v else 0
    nita = (ni_v or 0) / ta_v
    futl = 0  # FFO 간이 대체
    intwo = 1 if ni_v and ni_v < 0 and len(ni) >= 2 and ni[-2] and ni[-2] < 0 else 0

    # CHIN: 순이익 변화
    chin = 0
    if len(ni) >= 2 and ni[-1] is not None and ni[-2] is not None:
        denom = abs(ni[-1]) + abs(ni[-2])
        if denom > 0:
            chin = (ni[-1] - ni[-2]) / denom

    o = (-1.32 - 0.407 * size + 6.03 * tlta - 1.43 * wcta
         + 0.0757 * clca - 1.72 * oeneg - 2.37 * nita
         - 1.83 * futl + 0.285 * intwo - 0.521 * chin)

    p = 1 / (1 + math.exp(-o))
    return {"o_score": round(o, 4), "p_bankruptcy": round(p * 100, 2)}


# ── Z''-Score 계산 (003에서 가져옴) ──
def calc_altman_zpp(series: dict) -> float | None:
    """Altman Z''-Score (비제조업/신흥시장 변형)."""
    bs = series.get("BS", {})
    is_ = series.get("IS", {})

    ta = bs.get("total_assets", [])
    if not ta or not ta[-1] or ta[-1] <= 0:
        return None
    ta_v = ta[-1]

    ca = bs.get("current_assets", [])
    cl = bs.get("current_liabilities", [])
    re = bs.get("retained_earnings", [])
    eq = bs.get("total_stockholders_equity", []) or bs.get("owners_of_parent_equity", [])
    tl = bs.get("total_liabilities", [])
    op = is_.get("operating_profit", []) or is_.get("operating_income", [])

    wc = ((ca[-1] if ca and ca[-1] else 0) - (cl[-1] if cl and cl[-1] else 0))
    re_v = re[-1] if re and re[-1] else 0
    ebit = op[-1] if op and op[-1] else 0
    eq_v = eq[-1] if eq and eq[-1] else 0
    tl_v = tl[-1] if tl and tl[-1] else 1

    zpp = 6.56 * (wc / ta_v) + 3.26 * (re_v / ta_v) + 6.72 * (ebit / ta_v) + 1.05 * (eq_v / tl_v)
    return round(zpp, 4)


# ── 앙상블 점수 (004 간이 버전) ──
def calc_ensemble_simple(o_result: dict | None, zpp: float | None) -> float | None:
    """O-Score + Z''-Score 간이 앙상블."""
    scores = []
    if o_result:
        # O-Score: P(bankruptcy) > 50% → 1.0, 0% → 0.0
        scores.append(min(o_result["p_bankruptcy"] / 50, 1.0))
    if zpp is not None:
        # Z'': < 1.1 → 1.0, > 2.6 → 0.0
        if zpp < 1.1:
            scores.append(1.0)
        elif zpp > 2.6:
            scores.append(0.0)
        else:
            scores.append(round(1 - (zpp - 1.1) / 1.5, 2))
    if not scores:
        return None
    return round(sum(scores) / len(scores), 3)


# ── 시계열 악화 패턴 (006 간이) ──
def detect_trend_patterns(series: dict) -> list[str]:
    """주요 시계열 악화 패턴 간이 탐지."""
    patterns = []
    is_ = series.get("IS", {})
    bs = series.get("BS", {})

    # 연속 적자
    ni = is_.get("net_profit", []) or is_.get("net_income", [])
    if len(ni) >= 3:
        streak = 0
        for v in reversed(ni):
            if v is not None and v < 0:
                streak += 1
            else:
                break
        if streak >= 2:
            patterns.append(f"순적자 {streak}기 연속")

    # 자본잠식
    cap = bs.get("issued_capital", []) or bs.get("capital_stock", [])
    eq = bs.get("total_stockholders_equity", []) or bs.get("owners_of_parent_equity", [])
    if cap and eq and cap[-1] and eq[-1] and cap[-1] > 0:
        erosion = (cap[-1] - eq[-1]) / cap[-1] * 100
        if erosion > 50:
            patterns.append(f"자본잠식 {erosion:.0f}%")
        elif erosion > 0:
            patterns.append(f"부분잠식 {erosion:.0f}%")

    # 부채비율 > 200%
    tl = bs.get("total_liabilities", [])
    if tl and eq and tl[-1] and eq[-1] and eq[-1] > 0:
        dr = tl[-1] / eq[-1] * 100
        if dr > 200:
            patterns.append(f"부채비율 {dr:.0f}%")

    return patterns


# ── 테스트 종목 ──
# 위험군: 과거 관리종목/워크아웃/재무 위기 이력 기업
RISK_STOCKS = [
    ("032190", "다우데이타"),     # 관리종목 경험
    ("078930", "GS"),           # 재무구조 변동
    ("004800", "효성"),         # 워크아웃 계열사
    ("024110", "기업은행"),     # 금융업 기준
    ("000720", "현대건설"),     # 건설업 변동성
    ("047050", "포스코인터내셔널"),  # 대우인터 전신
    ("001040", "CJ"),          # 지주 구조
    ("011170", "롯데케미칼"),   # 화학업 사이클
]

# 안전군: Phase 1-3 safe 판정 대형주
SAFE_STOCKS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("035420", "NAVER"),
    ("005380", "현대차"),
    ("003550", "LG"),
    ("066570", "LG전자"),
    ("000880", "한화"),
    ("068270", "셀트리온"),
]


def analyze_stock(code: str, name: str, group: str) -> dict | None:
    """단일 종목 분석."""
    try:
        c = Company(code)
        build = c.finance.annual
        if not build:
            print(f"  {name}: 연간 데이터 없음")
            del c
            return None

        series, years = build
        o_result = calc_ohlson_o_score(series)
        zpp = calc_altman_zpp(series)
        ensemble = calc_ensemble_simple(o_result, zpp)
        patterns = detect_trend_patterns(series)

        # 등급 판정
        if ensemble is not None:
            if ensemble >= 0.70:
                level = "critical"
            elif ensemble >= 0.50:
                level = "danger"
            elif ensemble >= 0.30:
                level = "warning"
            elif ensemble >= 0.15:
                level = "watch"
            else:
                level = "safe"
        else:
            level = "N/A"

        result = {
            "name": name,
            "group": group,
            "years": len(years),
            "o_score": o_result["o_score"] if o_result else None,
            "p_bankruptcy": o_result["p_bankruptcy"] if o_result else None,
            "zpp": zpp,
            "ensemble": ensemble,
            "level": level,
            "patterns": patterns,
        }
        del c
        return result
    except Exception as e:
        print(f"  {name}: {e}")
        return None


if __name__ == "__main__":
    print("=" * 110)
    print("실험 010: 관리종목 기준 역추적 — backtesting")
    print("=" * 110)

    all_results = []

    # 위험군
    print("\n[위험군 분석]")
    for code, name in RISK_STOCKS:
        result = analyze_stock(code, name, "RISK")
        if result:
            all_results.append(result)

    # 안전군
    print("\n[안전군 분석]")
    for code, name in SAFE_STOCKS:
        result = analyze_stock(code, name, "SAFE")
        if result:
            all_results.append(result)

    # ── 결과 ──
    zpp_label = "Z''"
    print(f"\n{'그룹':>6} {'종목':>12} {'O-Score':>8} {'P(부도)':>8} {zpp_label:>8} {'앙상블':>8} {'등급':>8} {'패턴'}")
    print("-" * 110)

    for r in all_results:
        o = f"{r['o_score']:.2f}" if r["o_score"] is not None else "N/A"
        p = f"{r['p_bankruptcy']:.1f}%" if r["p_bankruptcy"] is not None else "N/A"
        z = f"{r['zpp']:.2f}" if r["zpp"] is not None else "N/A"
        e = f"{r['ensemble']:.3f}" if r["ensemble"] is not None else "N/A"
        pat = ", ".join(r["patterns"]) if r["patterns"] else ""
        print(f"  {r['group']:>4} {r['name']:>10} {o:>8} {p:>8} {z:>8} {e:>8} {r['level']:>8}  {pat}")

    # ── 분리도 통계 ──
    print("\n" + "=" * 110)
    print("그룹별 통계")
    print("-" * 110)
    for grp in ["RISK", "SAFE"]:
        grp_r = [r for r in all_results if r["group"] == grp]
        if not grp_r:
            continue
        ensembles = [r["ensemble"] for r in grp_r if r["ensemble"] is not None]
        if ensembles:
            avg = sum(ensembles) / len(ensembles)
            levels = [r["level"] for r in grp_r]
            print(f"  {grp}: 평균 앙상블 {avg:.3f}, 등급 분포: {', '.join(levels)}")
            danger_plus = sum(1 for l in levels if l in ("danger", "critical"))
            safe_plus = sum(1 for l in levels if l in ("safe", "watch"))
            print(f"        danger+: {danger_plus}/{len(grp_r)}, safe/watch: {safe_plus}/{len(grp_r)}")

    # ── 패턴 보유 기업 ──
    print("\n" + "=" * 110)
    print("시계열 악화 패턴 보유 기업")
    print("-" * 110)
    for r in all_results:
        if r["patterns"]:
            print(f"  [{r['group']}] {r['name']:>10}: {', '.join(r['patterns'])}")

    print(f"\n총 {len(all_results)}개 종목 backtesting 완료")
