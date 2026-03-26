"""실험 ID: 005
실험명: 감사 Red Flag — 감사인 교체, 감사보수 변동, 핵심감사사항(KAM) 분석

목적:
- PCAOB/IAASB 기준 감사 Red Flag를 DART 데이터로 자동 탐지 가능한지 검증
- 감사인 교체 패턴, 감사보수 급변, KAM 수 변화를 시계열로 분석
- 감사의견 비적정, 계속기업 의문 등 핵심 위험 신호 탐지

가설:
1. audit pipeline의 opinionDf로 감사인 교체 패턴을 시계열 추적 가능
2. feeDf로 감사보수 전년 대비 급변(±30% 이상)을 감지할 수 있음
3. 대형 우량 기업은 감사의견 '적정' 유지, 특이사항 기업에서 Red Flag 발견 가능

방법:
1. 20개 종목의 audit pipeline 결과 수집
2. 감사인 교체 횟수 및 패턴 분석
3. 감사보수 YoY 변화율 계산
4. KAM 유무 및 내용 변화 추적
5. internalControl pipeline의 hasWeakness 교차 확인

결과 (실험 후 작성):
- 16/20 종목 분석 (4개 docs 데이터 미보유: 펄어비스, 위메이드, 에스엠, 넷마블)
- 감사의견 데이터: 15/16 종목 보유, 최대 12년 시계열 (삼성증권)
- **감사인 교체**: 11/16 종목에서 교체 이력, 2회 교체가 8개 (빅4 순환)
  - 삼성전자: 삼일→안진→삼정, SK하이닉스: 삼정→삼일→삼정, NAVER: 삼정→삼일→한영
  - 빅4(삼일/삼정/안진/한영) 순환이 대부분 — 정상적 주기적 교체로 판단
- **감사보수 급변**: 셀트리온(+76.2%, -99.8%), 삼성증권(+45.3%), 삼성생명(+40.7%)
  - 셀트리온 -99.8%는 파싱 오류 의심 (실제보수 급감 비현실적)
- **비적정 감사의견**: 삼성증권 1건 — 내부회계관리제도 검토의견이 감사의견으로 파싱됨 (오분류)
- **소송**: KB금융(90건), 대한항공(42건), 신한지주/한화(8건) — 금융업·항공업 특성
- **KAM**: 15/16 종목 보유, 정상적으로 핵심감사사항 기록
- **내부통제 취약점**: 0건 (20개 대형주에서 발견 안 됨 — 정상)
- Red Flag 기업: 10/16 (62%) — 대부분 감사인 교체(빅4 순환)로 인한 것

결론:
- **가설 1 채택**: opinionDf로 감사인 교체 패턴 시계열 추적 가능. 빅4 순환 vs 이상 교체 구분 필요
- **가설 2 부분 채택**: feeDf로 보수 변동 감지 가능하나, 파싱 오류(셀트리온 -99.8%) 보정 필요
- **가설 3 부분 채택**: 대형 우량주는 대부분 적정 의견. 삼성증권 "비적정"은 파서 오분류
- **발견된 이슈**:
  1. 빅4 순환 교체(2~3회)는 정상 → Red Flag 기준을 "짧은 주기 교체(2년 이내)" 또는
     "비빅4 교체"로 세분화 필요
  2. 감사보수 파싱 품질 검증 필요 (셀트리온 -99.8% 비현실적)
  3. 감사의견 vs 내부통제 의견 구분 로직 개선 필요
  4. 금융업 소송 건수는 업종 특성 → 업종별 정규화 필요
- **엔진 흡수 방향**: grading.py governance에 감사인 교체 빈도, 보수 급변 반영 추가

실험일: 2026-03-22
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.providers.dart.docs.finance.audit.pipeline import audit
from dartlab.providers.dart.docs.finance.contingentLiability.pipeline import contingentLiability
from dartlab.providers.dart.docs.finance.internalControl.pipeline import internalControl

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


def analyze_audit_red_flags(code: str, name: str) -> dict:
    """감사 Red Flag 종합 분석."""
    result = {
        "code": code, "name": name,
        "audit_years": 0, "opinions": [],
        "auditor_changes": 0, "auditors": [],
        "fee_changes": [], "fee_data": [],
        "kam_count": 0, "kam_years": [],
        "non_clean": False, "going_concern": False,
        "ic_weakness": False, "ic_data": [],
        "contingent_total": 0, "lawsuit_count": 0,
        "red_flags": [],
    }

    # ── 감사의견 ──
    audit_result = audit(code)
    if audit_result and audit_result.opinionDf is not None:
        df = audit_result.opinionDf
        result["audit_years"] = len(df)

        if "opinion" in df.columns:
            opinions = df["opinion"].to_list()
            result["opinions"] = opinions
            for op in opinions:
                if op and "적정" not in str(op):
                    result["non_clean"] = True
                    result["red_flags"].append(f"비적정 감사의견: {op}")
                if op and ("계속기업" in str(op) or "going concern" in str(op).lower()):
                    result["going_concern"] = True
                    result["red_flags"].append("계속기업 의문 언급")

        if "auditor" in df.columns:
            auditors = df["auditor"].to_list()
            result["auditors"] = auditors
            # 감사인 교체 횟수
            changes = 0
            for i in range(1, len(auditors)):
                if auditors[i] and auditors[i-1] and auditors[i] != auditors[i-1]:
                    changes += 1
            result["auditor_changes"] = changes
            if changes >= 2:
                result["red_flags"].append(f"감사인 {changes}회 교체 (빈번)")

        if "keyAuditMatters" in df.columns:
            kams = df["keyAuditMatters"].to_list()
            kam_years = [(i, k) for i, k in enumerate(kams) if k and str(k).strip()]
            result["kam_count"] = len(kam_years)
            result["kam_years"] = kam_years

    # ── 감사보수 ──
    if audit_result and audit_result.feeDf is not None:
        fee_df = audit_result.feeDf
        if "actualFee" in fee_df.columns:
            fees = fee_df["actualFee"].to_list()
            result["fee_data"] = fees
            for i in range(1, len(fees)):
                if fees[i] is not None and fees[i-1] is not None and fees[i-1] > 0:
                    change = ((fees[i] - fees[i-1]) / fees[i-1]) * 100
                    result["fee_changes"].append(round(change, 1))
                    if abs(change) > 30:
                        result["red_flags"].append(f"감사보수 급변 {change:+.1f}%")

    # ── 내부통제 ──
    ic_result = internalControl(code)
    if ic_result and ic_result.controlDf is not None:
        ic_df = ic_result.controlDf
        result["ic_data"] = ic_df.to_dicts() if len(ic_df) > 0 else []
        if "hasWeakness" in ic_df.columns:
            weaknesses = ic_df["hasWeakness"].to_list()
            if any(w for w in weaknesses if w):
                result["ic_weakness"] = True
                result["red_flags"].append("내부통제 중요한 취약점 보유")

    # ── 우발부채 ──
    cl_result = contingentLiability(code)
    if cl_result:
        if cl_result.guaranteeDf is not None and len(cl_result.guaranteeDf) > 0:
            if "totalGuaranteeAmount" in cl_result.guaranteeDf.columns:
                amounts = cl_result.guaranteeDf["totalGuaranteeAmount"].to_list()
                result["contingent_total"] = sum(a for a in amounts if a is not None)
        if cl_result.lawsuitDf is not None:
            result["lawsuit_count"] = len(cl_result.lawsuitDf)
            if result["lawsuit_count"] > 5:
                result["red_flags"].append(f"소송 {result['lawsuit_count']}건 (다수)")

    return result


if __name__ == "__main__":
    print("=" * 110)
    print("실험 005: 감사 Red Flag — 감사인 교체, 감사보수, KAM, 내부통제, 우발부채")
    print("=" * 110)

    all_results = []
    for code, name in TEST_STOCKS:
        try:
            r = analyze_audit_red_flags(code, name)
            all_results.append(r)
        except Exception as e:
            print(f"  {name}({code}): 에러 — {e}")

    # ── 감사의견 요약 ──
    print(f"\n{'종목':>12} {'연도수':>6} {'감사인교체':>8} {'비적정':>6} {'IC취약':>6} {'소송수':>6} {'KAM':>4} {'Red Flags':>6}")
    print("-" * 110)

    for r in all_results:
        non_clean = "Y" if r["non_clean"] else ""
        ic = "Y" if r["ic_weakness"] else ""
        print(
            f"  {r['name']:>10} {r['audit_years']:>6} {r['auditor_changes']:>8} "
            f"{non_clean:>6} {ic:>6} {r['lawsuit_count']:>6} {r['kam_count']:>4} {len(r['red_flags']):>6}"
        )

    # ── 감사인 목록 ──
    print("\n" + "=" * 110)
    print("감사인 시계열")
    print("-" * 110)
    for r in all_results:
        if r["auditors"]:
            unique = []
            for a in r["auditors"]:
                if a and (not unique or unique[-1] != a):
                    unique.append(a)
            print(f"  {r['name']:>10}: {' → '.join(str(a) for a in unique)}")

    # ── 감사보수 변동 ──
    print("\n" + "=" * 110)
    print("감사보수 YoY 변화율 (%)")
    print("-" * 110)
    for r in all_results:
        if r["fee_changes"]:
            changes_str = ", ".join(f"{c:+.1f}%" for c in r["fee_changes"])
            big = any(abs(c) > 30 for c in r["fee_changes"])
            flag = " ← 급변!" if big else ""
            print(f"  {r['name']:>10}: {changes_str}{flag}")

    # ── Red Flag 종합 ──
    print("\n" + "=" * 110)
    print("Red Flag 종합 (발견된 기업)")
    print("-" * 110)
    flagged = [r for r in all_results if r["red_flags"]]
    if flagged:
        for r in flagged:
            print(f"  {r['name']:>10}:")
            for flag in r["red_flags"]:
                print(f"    - {flag}")
    else:
        print("  Red Flag 발견 없음")

    # ── 통계 ──
    print("\n" + "=" * 110)
    print("통계 요약")
    print("-" * 110)
    total = len(all_results)
    has_audit = sum(1 for r in all_results if r["audit_years"] > 0)
    has_change = sum(1 for r in all_results if r["auditor_changes"] > 0)
    has_fee = sum(1 for r in all_results if r["fee_changes"])
    has_kam = sum(1 for r in all_results if r["kam_count"] > 0)
    has_ic = sum(1 for r in all_results if r["ic_data"])
    has_cl = sum(1 for r in all_results if r["lawsuit_count"] > 0)

    print(f"  총 종목: {total}")
    print(f"  감사의견 데이터 보유: {has_audit}/{total}")
    print(f"  감사인 교체 이력: {has_change}/{total}")
    print(f"  감사보수 데이터: {has_fee}/{total}")
    print(f"  KAM 데이터: {has_kam}/{total}")
    print(f"  내부통제 데이터: {has_ic}/{total}")
    print(f"  소송 데이터: {has_cl}/{total}")
    print(f"  Red Flag 기업: {len(flagged)}/{total}")
