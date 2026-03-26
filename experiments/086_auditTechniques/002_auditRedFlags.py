"""실험 ID: 002
실험명: 감사 Red Flag 탐지기 검증

목적:
- detectAuditRedFlags 탐지기의 6개 항목 개별/종합 동작 검증
- 합성 감사 데이터 프로필별 탐지 정확도 확인
- PCAOB/ISA/SOX 기준 매핑 적합성 검증

가설:
1. 정상 기업 프로필 → Red Flag 0건
2. 감사인 빈번 교체 → danger 탐지
3. 계속기업+내부통제 취약 → danger 2건
4. Big4→비Big4 교체 → warning 1건

방법:
1. 5개 합성 프로필 생성 (정상, 빈번교체, 계속기업위험, Big4이탈, 종합위험)
2. detectAuditRedFlags 개별 호출 → 탐지 결과 검증
3. severity/category 정확성 확인

결과 (실험 후 작성):
- 아래 실행 결과 참조

결론:
- 아래 실행 결과 참조

실험일: 2026-03-23
"""

from __future__ import annotations


def make_profiles() -> dict:
    """5개 합성 감사 프로필."""
    from dartlab.analysis.financial.insight.types import AuditDataForAnomaly

    return {
        "정상 기업": AuditDataForAnomaly(
            auditors=["삼일PwC회계법인", "삼일PwC회계법인", "삼일PwC회계법인", "삼일PwC회계법인"],
            opinions=["적정", "적정", "적정", "적정"],
            fees=[200.0, 210.0, 220.0, 230.0],
            kamCounts=[2, 2, 3, 3],
            hasGoingConcern=False,
            hasInternalControlWeakness=False,
        ),
        "빈번 교체": AuditDataForAnomaly(
            auditors=["삼일PwC회계법인", "삼정KPMG회계법인", "한영EY회계법인", "대주회계법인"],
            opinions=["적정", "적정", "적정", "적정"],
            fees=[200.0, 180.0, 150.0, 120.0],
            kamCounts=[2, 3, 3, 4],
            hasGoingConcern=False,
            hasInternalControlWeakness=False,
        ),
        "계속기업 위험": AuditDataForAnomaly(
            auditors=["안진Deloitte회계법인", "안진Deloitte회계법인", "안진Deloitte회계법인"],
            opinions=["적정", "적정", "한정"],
            fees=[300.0, 310.0, 450.0],
            kamCounts=[2, 3, 6],
            hasGoingConcern=True,
            hasInternalControlWeakness=True,
        ),
        "Big4 이탈": AuditDataForAnomaly(
            auditors=["삼정KPMG회계법인", "삼정KPMG회계법인", "삼정KPMG회계법인", "대주회계법인"],
            opinions=["적정", "적정", "적정", "적정"],
            fees=[250.0, 260.0, 270.0, 150.0],
            kamCounts=[2, 2, 2, 2],
            hasGoingConcern=False,
            hasInternalControlWeakness=False,
        ),
        "종합 위험": AuditDataForAnomaly(
            auditors=["한영EY회계법인", "대주회계법인", "신한회계법인"],
            opinions=["적정", "한정", "의견거절"],
            fees=[200.0, 100.0, 80.0],
            kamCounts=[2, 5, 8],
            hasGoingConcern=True,
            hasInternalControlWeakness=True,
        ),
    }


def test_all_profiles():
    """모든 프로필 탐지 결과 검증."""
    from dartlab.analysis.financial.insight.anomaly import detectAuditRedFlags

    profiles = make_profiles()

    results = {}
    for name, data in profiles.items():
        anomalies = detectAuditRedFlags(data)
        results[name] = anomalies

        print(f"\n{'─' * 50}")
        print(f"프로필: {name}")
        print(f"  감사인: {data.auditors}")
        print(f"  의견: {data.opinions}")
        print(f"  계속기업: {data.hasGoingConcern}, 내부통제 취약: {data.hasInternalControlWeakness}")
        print(f"  탐지 결과: {len(anomalies)}건")
        for a in anomalies:
            print(f"    [{a.severity:>7}] {a.category}: {a.text}")

    return results


def verify_expectations(results: dict):
    """기대값 검증."""
    print("\n" + "=" * 50)
    print("검증:")

    checks = []

    # 정상 기업 → 0건
    n = len(results["정상 기업"])
    ok = n == 0
    checks.append(ok)
    print(f"  1. 정상 기업 → {n}건: {'PASS' if ok else 'FAIL (expected 0)'}")

    # 빈번 교체 → danger (3회 교체)
    r = results["빈번 교체"]
    has_frequent = any(a.severity == "danger" and "교체" in a.text for a in r)
    checks.append(has_frequent)
    print(f"  2. 빈번 교체 → danger 교체 탐지: {'PASS' if has_frequent else 'FAIL'}")

    # 계속기업 위험 → goingConcern danger + 내부통제 danger + 비적정 danger
    r = results["계속기업 위험"]
    has_gc = any("계속기업" in a.text for a in r)
    has_ic = any("내부" in a.text for a in r)
    has_opinion = any("비적정" in a.text or "한정" in a.text for a in r)
    checks.extend([has_gc, has_ic])
    print(f"  3. 계속기업 → GC탐지: {'PASS' if has_gc else 'FAIL'}, IC탐지: {'PASS' if has_ic else 'FAIL'}")

    # Big4 이탈 → warning
    r = results["Big4 이탈"]
    has_big4 = any(a.severity == "warning" and "Big4" in a.text for a in r)
    checks.append(has_big4)
    print(f"  4. Big4 이탈 → warning: {'PASS' if has_big4 else 'FAIL'}")

    # 종합 위험 → 4건+
    r = results["종합 위험"]
    n = len(r)
    ok = n >= 4
    checks.append(ok)
    print(f"  5. 종합 위험 → {n}건 (≥4): {'PASS' if ok else 'FAIL'}")

    return all(checks)


def test_none_input():
    """auditData=None → 0건."""
    from dartlab.analysis.financial.insight.anomaly import detectAuditRedFlags

    result = detectAuditRedFlags(None)
    ok = len(result) == 0
    print(f"\n  None 입력 → {len(result)}건: {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    print("=" * 60)
    print("086-002: 감사 Red Flag 탐지기 검증")
    print("=" * 60)

    results = test_all_profiles()
    pass1 = verify_expectations(results)
    pass2 = test_none_input()

    print("\n" + "=" * 60)
    print(f"종합: {'ALL PASS' if pass1 and pass2 else 'SOME FAIL'}")
