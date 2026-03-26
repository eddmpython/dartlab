"""실험 ID: 003
실험명: 매출 품질 탐지기 검증

목적:
- detectRevenueQuality 탐지기의 3개 신호 검증
- OCF/Revenue 비율 추세, 매출채권 증가율 vs 매출 증가율 비교
- Dechow & Dichev (2002) 기반 매출 품질 판정 정확도 확인

가설:
1. 건전 기업 (OCF/Rev 양호, 매출채권 정상) → anomaly 0건
2. OCF/Rev < 0 → danger 탐지
3. OCF/Rev 연속 하락 → warning 탐지
4. 매출채권 증가율 > 매출 × 1.5 (3기 연속) → warning 탐지

방법:
1. 4개 합성 재무 시계열 생성 (건전, OCF적자, 추세악화, 매출채권이상)
2. detectRevenueQuality 개별 호출 → 결과 검증

결과 (실험 후 작성):
- 아래 실행 결과 참조

결론:
- 아래 실행 결과 참조

실험일: 2026-03-23
"""

from __future__ import annotations


def make_profiles():
    """4개 합성 프로필."""
    return {
        "건전 기업": {
            "IS": {"sales": [100e9, 110e9, 120e9, 130e9]},
            "CF": {"operating_cashflow": [15e9, 18e9, 20e9, 22e9]},
            "BS": {"trade_and_other_receivables": [10e9, 11e9, 12e9, 13e9]},
        },
        "OCF 적자": {
            "IS": {"sales": [100e9, 110e9, 120e9, 130e9]},
            "CF": {"operating_cashflow": [15e9, 10e9, 5e9, -3e9]},
            "BS": {"trade_and_other_receivables": [10e9, 11e9, 12e9, 13e9]},
        },
        "OCF/Rev 연속 하락": {
            "IS": {"sales": [100e9, 110e9, 120e9, 130e9, 140e9]},
            "CF": {"operating_cashflow": [20e9, 18e9, 15e9, 10e9, 5e9]},
            "BS": {"trade_and_other_receivables": [10e9, 11e9, 12e9, 13e9, 14e9]},
        },
        "매출채권 이상 증가": {
            "IS": {"sales": [100e9, 105e9, 110e9, 115e9, 120e9]},
            "CF": {"operating_cashflow": [15e9, 16e9, 17e9, 18e9, 19e9]},
            "BS": {"trade_and_other_receivables": [10e9, 13e9, 18e9, 26e9, 38e9]},
        },
    }


def test_all():
    from dartlab.analysis.financial.insight.anomaly import detectRevenueQuality

    profiles = make_profiles()

    results = {}
    for name, series in profiles.items():
        anomalies = detectRevenueQuality(series)
        results[name] = anomalies

        print(f"\n{'─' * 50}")
        print(f"프로필: {name}")

        revs = series["IS"]["sales"]
        cfs = series["CF"]["operating_cashflow"]
        ratios = [cf / rv if rv > 0 else None for rv, cf in zip(revs, cfs)]
        print(f"  매출: {[f'{v/1e9:.0f}B' for v in revs]}")
        print(f"  OCF:  {[f'{v/1e9:.0f}B' for v in cfs]}")
        print(f"  OCF/Rev: {[f'{r:.1%}' if r else 'N/A' for r in ratios]}")

        ars = series["BS"]["trade_and_other_receivables"]
        print(f"  매출채권: {[f'{v/1e9:.0f}B' for v in ars]}")

        print(f"  탐지: {len(anomalies)}건")
        for a in anomalies:
            print(f"    [{a.severity:>7}] {a.text}")

    return results


def verify(results: dict):
    print("\n" + "=" * 50)
    print("검증:")

    checks = []

    # 건전 기업 → 0건
    n = len(results["건전 기업"])
    ok = n == 0
    checks.append(ok)
    print(f"  1. 건전 기업 → {n}건: {'PASS' if ok else 'FAIL'}")

    # OCF 적자 → danger
    r = results["OCF 적자"]
    has_danger = any(a.severity == "danger" and "OCF" in a.text for a in r)
    checks.append(has_danger)
    print(f"  2. OCF 적자 → danger: {'PASS' if has_danger else 'FAIL'}")

    # OCF/Rev 연속 하락 → warning
    r = results["OCF/Rev 연속 하락"]
    has_decline = any("연속 하락" in a.text for a in r)
    checks.append(has_decline)
    print(f"  3. OCF/Rev 연속 하락 → warning: {'PASS' if has_decline else 'FAIL'}")

    # 매출채권 이상 → warning
    r = results["매출채권 이상 증가"]
    has_ar = any("매출채권" in a.text for a in r)
    checks.append(has_ar)
    print(f"  4. 매출채권 이상 → warning: {'PASS' if has_ar else 'FAIL'}")

    return all(checks)


if __name__ == "__main__":
    print("=" * 60)
    print("086-003: 매출 품질 탐지기 검증")
    print("=" * 60)

    results = test_all()
    all_pass = verify(results)

    print("\n" + "=" * 60)
    print(f"종합: {'ALL PASS' if all_pass else 'SOME FAIL'}")
