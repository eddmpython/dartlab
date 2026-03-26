"""실험 ID: 007
실험명: CCC(Cash Conversion Cycle) 시계열 분석 — 운전자본 위기 선행지표

목적:
- DSO/DIO/DPO/CCC 연간 추이를 분석하여 운전자본 악화 패턴 감지
- CCC 연속 확대가 유동성 위기 선행지표로 작동하는지 검증
- 관리종목 자동 점검 로직(자본잠식률, 매출액 기준, 연속적자) 프로토타입

가설:
1. CCC 3기 연속 확대는 매출채권 수금 지연/재고 누적 신호
2. DSO > 90일 + DIO > 120일 조합은 운전자본 경색 고위험
3. 관리종목 기준(자본잠식>50%, 매출<50억, 4기 연속적자)은 DART 데이터로 자동 점검 가능

방법:
1. ratioSeries로 연도별 DSO/DIO/DPO/CCC 시계열 추출
2. CCC 연속 확대 패턴 탐지
3. 관리종목 기준 자동 점검 로직 구현

결과 (실험 후 작성):
- 20/20 종목 분석, CCC 산출 16개 (금융업 4개 N/A — 정상)
- CCC 3기+ 연속 확대: 8/20 종목 (40%)
  - SK하이닉스: 6기 확대 (CCC 222일, DIO 197일 — 반도체 재고 주기)
  - 한화: 6기 확대 (CCC 124일, DIO 125일)
  - 삼성전기: 5기 확대 (CCC 132일)
  - 삼성전자: 4기 확대 (CCC 163일, DIO 120일)
  - 현대차: 4기 확대 (CCC 48일)
- 이상값 발견:
  - LG: DSO 9,766일 → 지주회사 관계사 채권 특성 (일반 DSO 해석 부적절)
  - 셀트리온: DIO 987일 → 바이오 장기 재고 특성
  - SK: DSO 1,174일 → 지주회사 특성
  - 위메이드: DSO 216일 → 게임업 라이선스 수금 구조
- 관리종목 기준: 20개 대형주 중 해당 없음 (정상)
- 금융업(KB금융, 신한지주, 삼성증권, 삼성생명): DSO/DIO/CCC 전부 N/A → 업종 특성 정상

결론:
- **가설 1 부분 채택**: CCC 3기+ 확대 8/20으로 흔함. 단순 확대보다 업종별 수준 대비 이탈 필요
- **가설 2 부분 채택**: DSO>90일 6개, DIO>120일 4개 탐지. 그러나 지주회사/바이오는 제외 필요
- **가설 3 채택**: 관리종목 3대 기준(자본잠식/매출/연속적자) 자동 점검 로직 작동 확인
- **업종 보정 필수 발견**: 지주회사 DSO, 바이오 DIO, 반도체 CCC는 업종 특성 →
  sector 벤치마크 대비 이탈로 판단해야 함
- **엔진 흡수 방향**: anomaly.py에 detectCCCDeterioration() 추가.
  업종별 벤치마크 연동 필요 (insight/benchmark.py 활용)

실험일: 2026-03-22
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab import Company
from dartlab.core.finance.ratios import calcRatios


def analyze_ccc_trend(series: dict, years: list) -> dict:
    """CCC 시계열 분석."""
    result = {
        "dso_series": [], "dio_series": [], "dpo_series": [], "ccc_series": [],
        "ccc_expanding": 0,  # 연속 확대 최대 기수
        "dso_max": None, "dio_max": None,
        "patterns": [],
    }

    rev = series.get("IS", {}).get("sales", []) or series.get("IS", {}).get("revenue", [])
    rec = series.get("BS", {}).get("trade_and_other_receivables", [])
    inv = series.get("BS", {}).get("inventories", [])
    pay = series.get("BS", {}).get("trade_and_other_payables", [])
    cogs = series.get("IS", {}).get("cost_of_sales", [])

    n = min(len(rev), len(years))
    for i in range(n):
        r = rev[i] if i < len(rev) else None
        re = rec[i] if i < len(rec) else None
        iv = inv[i] if i < len(inv) else None
        pa = pay[i] if i < len(pay) else None
        co = cogs[i] if i < len(cogs) else None

        dso = (re / r * 365) if r and r > 0 and re else None
        cos = co or r
        dio = (iv / cos * 365) if cos and cos > 0 and iv else None
        dpo = (pa / cos * 365) if cos and cos > 0 and pa else None
        ccc = (dso + dio - dpo) if dso is not None and dio is not None and dpo is not None else None

        result["dso_series"].append(round(dso, 1) if dso else None)
        result["dio_series"].append(round(dio, 1) if dio else None)
        result["dpo_series"].append(round(dpo, 1) if dpo else None)
        result["ccc_series"].append(round(ccc, 1) if ccc else None)

    # CCC 연속 확대 탐지
    ccc = result["ccc_series"]
    max_streak = 0
    streak = 0
    for i in range(1, len(ccc)):
        if ccc[i] is not None and ccc[i-1] is not None and ccc[i] > ccc[i-1]:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    result["ccc_expanding"] = max_streak

    if max_streak >= 3:
        result["patterns"].append(f"CCC {max_streak}기 연속 확대")

    # DSO/DIO 위험 수준
    dso_vals = [v for v in result["dso_series"] if v is not None]
    dio_vals = [v for v in result["dio_series"] if v is not None]
    if dso_vals:
        result["dso_max"] = max(dso_vals)
        if result["dso_max"] > 90:
            result["patterns"].append(f"DSO {result['dso_max']:.0f}일 (>90일 경고)")
    if dio_vals:
        result["dio_max"] = max(dio_vals)
        if result["dio_max"] > 120:
            result["patterns"].append(f"DIO {result['dio_max']:.0f}일 (>120일 경고)")

    return result


def check_listing_criteria(series: dict, name: str) -> list[str]:
    """관리종목 기준 자동 점검."""
    alerts = []

    # 1. 자본잠식률 > 50%
    cap = series.get("BS", {}).get("issued_capital", []) or series.get("BS", {}).get("capital_stock", [])
    eq = series.get("BS", {}).get("total_stockholders_equity", []) or series.get("BS", {}).get("owners_of_parent_equity", [])
    if cap and eq and cap[-1] is not None and eq[-1] is not None and cap[-1] > 0:
        erosion = (cap[-1] - eq[-1]) / cap[-1] * 100
        if erosion > 50:
            alerts.append(f"자본잠식률 {erosion:.1f}% (>50% 관리종목)")
        elif erosion > 0:
            alerts.append(f"부분 자본잠식 {erosion:.1f}%")

    # 2. 매출액 < 50억 (코스피 기준)
    rev = series.get("IS", {}).get("sales", []) or series.get("IS", {}).get("revenue", [])
    if rev and rev[-1] is not None:
        rev_billion = rev[-1] / 1e8  # 억원
        if rev_billion < 50:
            alerts.append(f"매출 {rev_billion:.0f}억 (<50억 관리종목)")

    # 3. 4기 연속 적자
    np_s = series.get("IS", {}).get("net_profit", []) or series.get("IS", {}).get("net_income", [])
    if len(np_s) >= 4:
        last4 = [v for v in np_s[-4:] if v is not None]
        if len(last4) == 4 and all(v < 0 for v in last4):
            alerts.append("4기 연속 순적자 (관리종목)")

    return alerts


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
    print("=" * 110)
    print("실험 007: CCC 시계열 + 관리종목 자동 점검")
    print("=" * 110)

    results = []
    for code, name in TEST_STOCKS:
        try:
            c = Company(code)
            build = c.finance.annual
            if not build:
                continue
            series, years = build

            ccc_result = analyze_ccc_trend(series, years)
            listing_alerts = check_listing_criteria(series, name)

            results.append({
                "name": name,
                "years": len(years),
                "ccc_latest": ccc_result["ccc_series"][-1] if ccc_result["ccc_series"] else None,
                "ccc_expanding": ccc_result["ccc_expanding"],
                "dso_max": ccc_result["dso_max"],
                "dio_max": ccc_result["dio_max"],
                "patterns": ccc_result["patterns"],
                "listing_alerts": listing_alerts,
            })
            del c
        except Exception as e:
            print(f"  {name}: {e}")

    # ── CCC 결과 ──
    print(f"\n{'종목':>12} {'CCC최신':>8} {'연속확대':>8} {'DSO최대':>8} {'DIO최대':>8} {'패턴'}")
    print("-" * 110)

    for r in sorted(results, key=lambda x: x["ccc_expanding"], reverse=True):
        ccc = f"{r['ccc_latest']:.0f}" if r["ccc_latest"] is not None else "N/A"
        dso = f"{r['dso_max']:.0f}" if r["dso_max"] is not None else "N/A"
        dio = f"{r['dio_max']:.0f}" if r["dio_max"] is not None else "N/A"
        patterns = ", ".join(r["patterns"]) if r["patterns"] else ""
        print(f"  {r['name']:>10} {ccc:>8} {r['ccc_expanding']:>8} {dso:>8} {dio:>8}  {patterns}")

    # ── 관리종목 점검 ──
    print("\n" + "=" * 110)
    print("관리종목 기준 자동 점검")
    print("-" * 110)
    alerted = [r for r in results if r["listing_alerts"]]
    if alerted:
        for r in alerted:
            for a in r["listing_alerts"]:
                print(f"  {r['name']:>10}: {a}")
    else:
        print("  관리종목 기준 해당 없음 (20개 대형주)")

    # ── 통계 ──
    print("\n" + "=" * 110)
    ccc_vals = [r["ccc_latest"] for r in results if r["ccc_latest"] is not None]
    if ccc_vals:
        print(f"  CCC 평균: {sum(ccc_vals)/len(ccc_vals):.0f}일, 중앙값: {sorted(ccc_vals)[len(ccc_vals)//2]:.0f}일")
        print(f"  CCC 범위: {min(ccc_vals):.0f}~{max(ccc_vals):.0f}일")
    expanding = sum(1 for r in results if r["ccc_expanding"] >= 3)
    print(f"  CCC 3기+ 확대: {expanding}/{len(results)}개 종목")

    print(f"\n총 {len(results)}개 종목 분석 완료")
