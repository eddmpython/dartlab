"""실험 ID: 006
실험명: 시계열 악화 패턴 탐지 — 연속 적자, CF 악화, 부채 누적

목적:
- 단일 시점 스냅샷이 아닌 시계열 연속 악화 패턴이 부실 선행지표로 작동하는지 검증
- 금감원 관리종목 기준(영업손실 4기 연속 등)과 연계 가능한 패턴 탐지

가설:
1. 3기 연속 악화 추세(적자, CF 음수, 부채 상승)가 단일 시점보다 강력한 부실 신호
2. 이자보상배율(ICR) < 1 연속은 채무 상환 능력 위험의 직접적 지표
3. 대형 우량주에서는 연속 악화 패턴이 드물고, 위험군에서 집중될 것

방법:
1. 연간 시계열에서 연속 패턴 탐지 (5개 카테고리):
   - 연속 순적자 (net_profit < 0)
   - 연속 영업CF 적자 (operating_cashflow < 0)
   - 부채비율 연속 상승 (3기+)
   - 유동비율 연속 하락 (3기+)
   - 이자보상배율 < 1 연속 (2기+)
2. 20개 종목에서 패턴 발생 빈도 및 심각도 분석

결과 (실험 후 작성):
- 20/20 종목, 총 38건 악화 패턴 탐지
- danger 패턴 보유 기업 4개:
  - 위메이드: 순이익 5기 연속적자, ICR<1 5기+4기 연속 (가장 위험)
  - SK: ICR<1 7기 연속 (이자보상 만성 불량)
  - 펄어비스: ICR<1 4기 연속
  - KB금융: ICR<1 3기 연속 (금융업 특성)
- 패턴 유형별 빈도:
  1. 유동비율 연속하락: 12건 (가장 흔함, 10개 종목)
  2. ICR<1 연속: 9건 (8개 종목 — 가장 위험한 신호)
  3. 부채비율 연속상승: 7건 (6개 종목)
  4. 순이익 연속적자: 6건 (5개 종목)
  5. 영업CF 연속적자: 4건 (3개 종목)
- 안전 기업 (패턴 0건): 삼성전자, LG, 한화, LG전자 (4개)
- 앙상블 004 결과와 교차: 위메이드(warning), SK(warning) 일치

결론:
- **가설 1 채택**: 연속 악화 패턴이 단일 시점보다 풍부한 정보. 위메이드는 5기 연속적자+ICR<1로 최위험
- **가설 2 채택**: ICR<1 연속이 가장 직접적 위험 신호. SK 7기 연속은 만성적 이자 부담
- **가설 3 채택**: 삼성전자/LG 등 대형 우량주는 패턴 0건. 위메이드/넷마블 등에서 집중
- **금융업 보정 필요**: KB금융 ICR<1은 금융업 이자수익 구조 특성 → 별도 처리 필요
- **엔진 흡수 방향**: anomaly.py에 detectTrendDeterioration() 추가.
  severity 기준: 4기+ danger, 3기 warning, 2기 info

실험일: 2026-03-22
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab import Company
from dartlab.core.finance.ratios import calcRatios, calcRatioSeries


def detect_consecutive_negative(values: list, label: str) -> list[dict]:
    """연속 음수 패턴 탐지."""
    patterns = []
    streak = 0
    start = -1
    for i, v in enumerate(values):
        if v is not None and v < 0:
            if streak == 0:
                start = i
            streak += 1
        else:
            if streak >= 2:
                patterns.append({
                    "type": label,
                    "streak": streak,
                    "start": start,
                    "end": i - 1,
                    "severity": "danger" if streak >= 4 else "warning" if streak >= 3 else "info",
                })
            streak = 0
    if streak >= 2:
        patterns.append({
            "type": label,
            "streak": streak,
            "start": start,
            "end": len(values) - 1,
            "severity": "danger" if streak >= 4 else "warning" if streak >= 3 else "info",
        })
    return patterns


def detect_consecutive_rising(values: list, label: str, min_streak: int = 3) -> list[dict]:
    """연속 상승 패턴 탐지."""
    patterns = []
    streak = 0
    start = -1
    for i in range(1, len(values)):
        if values[i] is not None and values[i-1] is not None and values[i] > values[i-1]:
            if streak == 0:
                start = i - 1
            streak += 1
        else:
            if streak >= min_streak:
                patterns.append({
                    "type": label,
                    "streak": streak,
                    "start": start,
                    "end": i - 1,
                    "severity": "warning" if streak >= 4 else "info",
                })
            streak = 0
    if streak >= min_streak:
        patterns.append({
            "type": label,
            "streak": streak,
            "start": start,
            "end": len(values) - 1,
            "severity": "warning" if streak >= 4 else "info",
        })
    return patterns


def detect_consecutive_falling(values: list, label: str, min_streak: int = 3) -> list[dict]:
    """연속 하락 패턴 탐지."""
    patterns = []
    streak = 0
    start = -1
    for i in range(1, len(values)):
        if values[i] is not None and values[i-1] is not None and values[i] < values[i-1]:
            if streak == 0:
                start = i - 1
            streak += 1
        else:
            if streak >= min_streak:
                patterns.append({
                    "type": label,
                    "streak": streak,
                    "start": start,
                    "end": i - 1,
                    "severity": "warning" if streak >= 4 else "info",
                })
            streak = 0
    if streak >= min_streak:
        patterns.append({
            "type": label,
            "streak": streak,
            "start": start,
            "end": len(values) - 1,
            "severity": "warning" if streak >= 4 else "info",
        })
    return patterns


def detect_icr_below_one(icr_values: list) -> list[dict]:
    """이자보상배율 < 1 연속 패턴."""
    patterns = []
    streak = 0
    start = -1
    for i, v in enumerate(icr_values):
        if v is not None and v < 1:
            if streak == 0:
                start = i
            streak += 1
        else:
            if streak >= 2:
                patterns.append({
                    "type": "ICR<1 연속",
                    "streak": streak,
                    "start": start,
                    "end": i - 1,
                    "severity": "danger" if streak >= 3 else "warning",
                })
            streak = 0
    if streak >= 2:
        patterns.append({
            "type": "ICR<1 연속",
            "streak": streak,
            "start": start,
            "end": len(icr_values) - 1,
            "severity": "danger" if streak >= 3 else "warning",
        })
    return patterns


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
    print("실험 006: 시계열 악화 패턴 탐지")
    print("=" * 110)

    all_results = []

    for code, name in TEST_STOCKS:
        try:
            c = Company(code)
            build = c.finance.annual
            if not build:
                print(f"  {name}: 연간 시계열 없음")
                continue

            series, years = build
            all_patterns = []

            # 순이익 연속 적자
            np_series = series.get("IS", {}).get("net_profit", []) or series.get("IS", {}).get("net_income", [])
            if np_series:
                all_patterns.extend(detect_consecutive_negative(np_series, "순이익 연속적자"))

            # 영업CF 연속 적자
            ocf_series = series.get("CF", {}).get("operating_cashflow", [])
            if ocf_series:
                all_patterns.extend(detect_consecutive_negative(ocf_series, "영업CF 연속적자"))

            # 부채비율 연속 상승
            tl = series.get("BS", {}).get("total_liabilities", [])
            te = series.get("BS", {}).get("total_stockholders_equity", []) or series.get("BS", {}).get("owners_of_parent_equity", [])
            if tl and te:
                debt_ratios = []
                for i in range(len(tl)):
                    if i < len(te) and tl[i] is not None and te[i] is not None and te[i] > 0:
                        debt_ratios.append(tl[i] / te[i] * 100)
                    else:
                        debt_ratios.append(None)
                all_patterns.extend(detect_consecutive_rising(debt_ratios, "부채비율 연속상승"))

            # 유동비율 연속 하락
            ca = series.get("BS", {}).get("current_assets", [])
            cl = series.get("BS", {}).get("current_liabilities", [])
            if ca and cl:
                current_ratios = []
                for i in range(len(ca)):
                    if i < len(cl) and ca[i] is not None and cl[i] is not None and cl[i] > 0:
                        current_ratios.append(ca[i] / cl[i] * 100)
                    else:
                        current_ratios.append(None)
                all_patterns.extend(detect_consecutive_falling(current_ratios, "유동비율 연속하락"))

            # 이자보상배율 < 1 연속
            op = series.get("IS", {}).get("operating_profit", []) or series.get("IS", {}).get("operating_income", [])
            fc = series.get("IS", {}).get("finance_costs", []) or series.get("IS", {}).get("interest_expense", [])
            if op and fc:
                icr_vals = []
                for i in range(len(op)):
                    if i < len(fc) and op[i] is not None and fc[i] is not None and fc[i] > 0:
                        icr_vals.append(op[i] / fc[i])
                    else:
                        icr_vals.append(None)
                all_patterns.extend(detect_icr_below_one(icr_vals))

            all_results.append({
                "name": name,
                "years": len(years),
                "patterns": all_patterns,
                "danger_count": sum(1 for p in all_patterns if p["severity"] == "danger"),
                "warning_count": sum(1 for p in all_patterns if p["severity"] == "warning"),
            })
            del c
        except Exception as e:
            print(f"  {name}: {e}")

    # ── 결과 출력 ──
    print(f"\n{'종목':>12} {'연도수':>6} {'패턴수':>6} {'danger':>8} {'warning':>8} {'패턴 상세'}")
    print("-" * 110)

    for r in sorted(all_results, key=lambda x: x["danger_count"] * 10 + x["warning_count"], reverse=True):
        pattern_str = ""
        if r["patterns"]:
            details = [f"{p['type']}({p['streak']}기)" for p in r["patterns"]]
            pattern_str = ", ".join(details)
        print(f"  {r['name']:>10} {r['years']:>6} {len(r['patterns']):>6} {r['danger_count']:>8} {r['warning_count']:>8}  {pattern_str}")

    # ── 패턴 유형별 통계 ──
    print("\n" + "=" * 110)
    print("패턴 유형별 발생 빈도")
    print("-" * 110)
    from collections import Counter
    type_counts = Counter()
    for r in all_results:
        for p in r["patterns"]:
            type_counts[p["type"]] += 1
    for t, cnt in type_counts.most_common():
        companies = [r["name"] for r in all_results if any(p["type"] == t for p in r["patterns"])]
        print(f"  {t:>20}: {cnt}건 — {', '.join(companies)}")

    # ── 위험 기업 ──
    print("\n" + "=" * 110)
    print("위험 기업 (danger 패턴 보유)")
    print("-" * 110)
    dangerous = [r for r in all_results if r["danger_count"] > 0]
    if dangerous:
        for r in dangerous:
            danger_patterns = [p for p in r["patterns"] if p["severity"] == "danger"]
            for p in danger_patterns:
                print(f"  {r['name']:>10}: {p['type']} {p['streak']}기 연속")
    else:
        print("  danger 패턴 없음")

    print(f"\n총 {len(all_results)}개 종목, 패턴 {sum(len(r['patterns']) for r in all_results)}건 탐지")
