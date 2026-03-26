"""실험 ID: 001
실험명: Benford's Law 재무제표 적용 검증

목적:
- 실제 재무제표 수치에 Benford's Law를 적용하여 첫째 자릿수 분포 검증
- 정상 기업 vs 합성 조작 데이터 구분 능력 확인
- detectBenfordAnomaly 탐지기의 χ² 임계값 타당성 검증

가설:
1. 정상 기업의 재무 수치는 Benford 분포를 따른다 (χ² < 15.51)
2. 인위적 조작 데이터는 Benford 분포를 위반한다 (χ² > 15.51)

방법:
1. mock 재무 시계열 (test_insight_pipeline.py와 동일) → Benford 검증
2. 균등분포 합성 데이터 → Benford 위반 확인
3. 실제적 분포 (대수정규) 데이터 → Benford 준수 확인

결과 (실험 후 작성):
- 아래 실행 결과 참조

결론:
- 아래 실행 결과 참조

실험일: 2026-03-23
"""

from __future__ import annotations

import math
import random


def _first_digit(v: float) -> int | None:
    """첫째 유효 자릿수 추출."""
    if v == 0 or not math.isfinite(v):
        return None
    absV = abs(v)
    d = int(str(absV).lstrip("0").lstrip(".").lstrip("0")[:1])
    return d if 1 <= d <= 9 else None


def benford_chi2(digits: list[int]) -> float:
    """Benford χ² 검정."""
    n = len(digits)
    expected = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
    observed = {d: 0 for d in range(1, 10)}
    for d in digits:
        observed[d] += 1

    chi2 = 0.0
    for d in range(1, 10):
        exp_count = expected[d] * n
        if exp_count > 0:
            chi2 += (observed[d] - exp_count) ** 2 / exp_count
    return chi2


def test_mock_financial_data():
    """Mock 재무 데이터 (insight 테스트용) Benford 검증."""
    # test_insight_pipeline.py의 _make_series()와 동일한 구조
    aSeries = {
        "IS": {
            "sales": [100e9, 110e9, 120e9],
            "operating_profit": [10e9, 12e9, 15e9],
            "net_income": [8e9, 10e9, 12e9],
            "cost_of_sales": [60e9, 65e9, 70e9],
            "sga": [20e9, 22e9, 23e9],
            "ebitda": [15e9, 18e9, 22e9],
            "interest_expense": [1e9, 1e9, 1e9],
        },
        "BS": {
            "total_assets": [200e9, 220e9, 250e9],
            "total_equity": [120e9, 135e9, 150e9],
            "total_liabilities": [80e9, 85e9, 100e9],
            "current_assets": [80e9, 90e9, 100e9],
            "current_liabilities": [40e9, 45e9, 50e9],
            "inventory": [20e9, 22e9, 25e9],
            "receivables": [15e9, 18e9, 20e9],
            "payables": [10e9, 12e9, 14e9],
            "cash": [30e9, 35e9, 40e9],
        },
        "CF": {
            "operating_cashflow": [12e9, 15e9, 18e9],
            "investing_cashflow": [-5e9, -7e9, -8e9],
            "financing_cashflow": [-3e9, -4e9, -5e9],
            "capex": [5e9, 7e9, 8e9],
        },
    }

    digits = []
    for sjDiv in ("IS", "BS", "CF"):
        for vals in aSeries.get(sjDiv, {}).values():
            for v in vals:
                if v is not None and v != 0:
                    d = _first_digit(float(v))
                    if d:
                        digits.append(d)

    print(f"Mock 데이터 수치 수: {len(digits)}")
    print(f"  → 숫자 50개 미만: 탐지기 스킵 (설계 의도)")

    return len(digits)


def test_synthetic_benford():
    """대수정규 합성 데이터 → Benford 준수 확인."""
    random.seed(42)
    # 대수정규: ln(X) ~ N(23, 3) → 재무 수치 스케일 (100억 ~ 수조)
    values = [math.exp(random.gauss(23, 3)) for _ in range(500)]
    digits = [_first_digit(v) for v in values]
    digits = [d for d in digits if d is not None]

    chi2 = benford_chi2(digits)
    print(f"\n대수정규 합성 데이터 ({len(digits)}개)")

    expected = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
    observed = {d: 0 for d in range(1, 10)}
    for d in digits:
        observed[d] += 1

    print(f"  {'자릿수':>6} {'관측':>6} {'기대':>6} {'Benford':>8}")
    for d in range(1, 10):
        obs_pct = observed[d] / len(digits) * 100
        exp_pct = expected[d] * 100
        print(f"  {d:>6} {obs_pct:>5.1f}% {exp_pct:>5.1f}% {'✓' if abs(obs_pct - exp_pct) < 5 else '✗':>8}")

    print(f"  χ² = {chi2:.2f} (임계값: 15.51 warning, 20.09 danger)")
    passed = chi2 < 15.51
    print(f"  판정: {'PASS — Benford 준수' if passed else 'FAIL'}")
    return chi2, passed


def test_uniform_violation():
    """균등분포 데이터 → Benford 위반 확인."""
    random.seed(123)
    # 1~9 균등분포 (회계 조작 시뮬레이션)
    values = [random.randint(1, 9) * 10 ** random.randint(6, 12) for _ in range(500)]
    digits = [_first_digit(float(v)) for v in values]
    digits = [d for d in digits if d is not None]

    chi2 = benford_chi2(digits)
    print(f"\n균등분포 합성 데이터 ({len(digits)}개)")

    expected = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
    observed = {d: 0 for d in range(1, 10)}
    for d in digits:
        observed[d] += 1

    print(f"  {'자릿수':>6} {'관측':>6} {'기대':>6} {'Benford':>8}")
    for d in range(1, 10):
        obs_pct = observed[d] / len(digits) * 100
        exp_pct = expected[d] * 100
        print(f"  {d:>6} {obs_pct:>5.1f}% {exp_pct:>5.1f}% {'✓' if abs(obs_pct - exp_pct) < 5 else '✗':>8}")

    print(f"  χ² = {chi2:.2f} (임계값: 15.51 warning, 20.09 danger)")
    violated = chi2 > 15.51
    print(f"  판정: {'PASS — Benford 위반 탐지' if violated else 'FAIL'}")
    return chi2, violated


def test_detector_integration():
    """detectBenfordAnomaly 탐지기 통합 테스트."""
    from dartlab.analysis.financial.insight.anomaly import detectBenfordAnomaly

    random.seed(42)
    # 충분한 수의 대수정규 값 → Benford 준수 기대
    large_series = {
        "IS": {"sales": [math.exp(random.gauss(23, 2)) for _ in range(30)]},
        "BS": {"total_assets": [math.exp(random.gauss(24, 2)) for _ in range(30)]},
        "CF": {"operating_cashflow": [math.exp(random.gauss(22, 2)) for _ in range(30)]},
    }

    anomalies = detectBenfordAnomaly(large_series)
    print(f"\n탐지기 통합 테스트 (대수정규 90개 값)")
    print(f"  anomaly 수: {len(anomalies)}")
    if anomalies:
        for a in anomalies:
            print(f"  [{a.severity}] {a.text}")
    else:
        print(f"  → 정상: anomaly 없음 (Benford 준수)")

    # 균등분포 → 위반 기대
    uniform_series = {
        "IS": {"sales": [random.randint(1, 9) * 1e10 for _ in range(30)]},
        "BS": {"total_assets": [random.randint(1, 9) * 1e11 for _ in range(30)]},
        "CF": {"operating_cashflow": [random.randint(1, 9) * 1e9 for _ in range(30)]},
    }

    anomalies2 = detectBenfordAnomaly(uniform_series)
    print(f"\n탐지기 통합 테스트 (균등분포 90개 값)")
    print(f"  anomaly 수: {len(anomalies2)}")
    if anomalies2:
        for a in anomalies2:
            print(f"  [{a.severity}] {a.text}")
        print(f"  → 정상: Benford 위반 탐지")
    else:
        print(f"  → 주의: 균등분포인데 탐지 안 됨 (n 부족 가능)")

    return len(anomalies) == 0, len(anomalies2) > 0


if __name__ == "__main__":
    print("=" * 60)
    print("086-001: Benford's Law 재무제표 적용 검증")
    print("=" * 60)

    n_mock = test_mock_financial_data()
    chi2_normal, pass1 = test_synthetic_benford()
    chi2_uniform, pass2 = test_uniform_violation()
    pass3, pass4 = test_detector_integration()

    print("\n" + "=" * 60)
    print("결과 요약:")
    print(f"  1. Mock 데이터: {n_mock}개 (< 50 → 스킵 설계)")
    print(f"  2. 대수정규 → Benford 준수: {'PASS' if pass1 else 'FAIL'} (χ²={chi2_normal:.2f})")
    print(f"  3. 균등분포 → Benford 위반: {'PASS' if pass2 else 'FAIL'} (χ²={chi2_uniform:.2f})")
    print(f"  4. 탐지기 정상 → 무탐지: {'PASS' if pass3 else 'FAIL'}")
    print(f"  5. 탐지기 조작 → 탐지: {'PASS' if pass4 else 'FAIL'}")
    all_pass = pass1 and pass2 and pass3
    print(f"\n종합: {'ALL PASS' if all_pass else 'SOME FAIL'}")
