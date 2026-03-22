"""
실험 ID: 001
실험명: scan 4축 대시보드 페이로드 설계

목적:
- scan 4축(governance/workforce/capital/debt) 결과를 InsightDashboard 호환
  payload(InsightResult 구조)로 변환 가능한지 검증
- insight 7영역과 합쳐 11영역 통합 payload 프로토타입 제작

가설:
1. scan 4축 DataFrame 1행에서 grade/summary/details/risks/opportunities를
   InsightResult와 동일한 dict 구조로 변환할 수 있다
2. 3개사 모두 11영역 payload 생성 가능하고 null 축 3개 이하
3. 통합 payload JSON 크기 10KB 이하

방법:
1. 삼성전자(005930), 현대차(005380), 카카오(035720) 3사
2. c.governance() ~ c.debt() 각 1행 DataFrame 추출
3. 각 축을 InsightResult 호환 dict로 변환하는 함수 작성
4. c.insights 7영역 payload와 합쳐 11영역 통합 dict 제작
5. payload 크기, null 비율, 등급 분포 측정

결과:
- 삼성전자: 11/11영역 유효, 4.0KB, null 0개
  insight 7영역: A/A/A/B/B/B/A, scan 4축: D/A/A/C
- 현대차: 11/11영역 유효, 3.2KB, null 0개
  insight 7영역: D/A/D/F/A/D/C, scan 4축: D/A/A/A
- 카카오: 11/11영역 유효, 3.6KB, null 0개
  insight 7영역: F/C/C/B/B/D/C, scan 4축: B/B/C/C
- 3사 모두 null 0개, JSON 3.2~4.0KB (10KB 이하 충족)
- insight.governance(재무 기반)와 scan_governance(report 기반)가 서로 다른 관점 제공
  삼성전자: insight B vs scan D (보수비율 28.4배, 사외이사 0%)

결론:
- 가설 1 채택: scan 4축 → InsightResult 변환 완전 가능
- 가설 2 채택: 3사 모두 11영역 유효 (null 0개)
- 가설 3 채택: JSON 3.2~4.0KB (10KB 이하)
- 감사의견 "적정의견" 문자열 매칭 버그 수정 필요 ("적정" 포함 여부로)
- insight.governance와 scan_governance는 겹치지만 관점이 다름 →
  UI에서 "재무 건전성 관점" vs "보고서 기반 관점"으로 구분 표시 가능
- 흡수 추천: scan payload 변환 함수를 engines/insight/ 또는 server/에 추가

실험일: 2026-03-20
"""

import json
import sys

import polars as pl

import dartlab


def governance_to_insight(row: dict) -> dict:
    """governance 1행 → InsightResult 호환 dict."""
    grade = row.get("등급", None)
    score = row.get("총점", None)
    if grade is None:
        return None

    details = []
    risks = []
    opportunities = []

    pct = row.get("지분율")
    if pct is not None:
        details.append(f"최대주주 지분율 {pct:.1f}%")
        if pct > 50:
            risks.append({"level": "warning", "category": "governance", "text": f"최대주주 과점 ({pct:.1f}%)"})
        elif pct < 20:
            risks.append({"level": "warning", "category": "governance", "text": f"최대주주 지분 낮음 ({pct:.1f}%)"})

    outside = row.get("사외이사비율")
    if outside is not None:
        details.append(f"사외이사 비율 {outside:.1f}%")
        if outside >= 40:
            opportunities.append({"level": "positive", "category": "governance", "text": f"사외이사 비율 우수 ({outside:.1f}%)"})
        elif outside == 0:
            risks.append({"level": "danger", "category": "governance", "text": "사외이사 없음"})

    pay = row.get("pay_ratio")
    if pay is not None:
        details.append(f"임원/직원 보수비율 {pay:.1f}배")
        if pay >= 10:
            risks.append({"level": "warning", "category": "governance", "text": f"보수비율 과다 ({pay:.1f}배)"})

    audit = row.get("감사의견")
    if audit is not None:
        details.append(f"감사의견: {audit}")
        if audit and "적정" not in audit:
            risks.append({"level": "danger", "category": "governance", "text": f"감사의견 비적정 ({audit})"})

    return {
        "grade": grade,
        "summary": f"지배구조 종합 {score:.0f}점 ({grade}등급)" if score else f"지배구조 {grade}등급",
        "details": details,
        "risks": risks,
        "opportunities": opportunities,
    }


def workforce_to_insight(row: dict) -> dict:
    """workforce 1행 → InsightResult 호환 dict."""
    emp = row.get("직원수")
    if emp is None:
        return None

    details = []
    risks = []
    opportunities = []

    details.append(f"직원수 {emp:,.0f}명")

    salary = row.get("평균급여_만원")
    if salary is not None:
        details.append(f"평균급여 {salary:,.0f}만원")

    rev_per = row.get("직원당매출_억")
    if rev_per is not None:
        details.append(f"직원당 매출 {rev_per:.1f}억")
        if rev_per >= 5:
            opportunities.append({"level": "positive", "category": "workforce", "text": f"직원당 매출 우수 ({rev_per:.1f}억)"})
        elif rev_per < 1:
            risks.append({"level": "warning", "category": "workforce", "text": f"직원당 매출 저조 ({rev_per:.1f}억)"})

    burden = row.get("인건비부담")
    if burden is not None:
        details.append(f"인건비부담 {burden:+.1f}%p")
        if burden > 10:
            risks.append({"level": "warning", "category": "workforce", "text": f"인건비 부담 증가 ({burden:+.1f}%p)"})

    gender = row.get("남녀격차")
    if gender is not None and gender > 40:
        risks.append({"level": "warning", "category": "workforce", "text": f"남녀 급여격차 {gender:.1f}%"})

    # 등급은 직원당매출 기준 간이 산출
    if rev_per is not None:
        if rev_per >= 5:
            grade = "A"
        elif rev_per >= 3:
            grade = "B"
        elif rev_per >= 1.5:
            grade = "C"
        elif rev_per >= 0.5:
            grade = "D"
        else:
            grade = "F"
    else:
        grade = "C"

    return {
        "grade": grade,
        "summary": f"직원 {emp:,.0f}명, 직원당 매출 {rev_per:.1f}억" if rev_per else f"직원 {emp:,.0f}명",
        "details": details,
        "risks": risks,
        "opportunities": opportunities,
    }


def capital_to_insight(row: dict) -> dict:
    """capital 1행 → InsightResult 호환 dict."""
    cls = row.get("분류")
    if cls is None:
        return None

    details = []
    risks = []
    opportunities = []

    details.append(f"주주환원 분류: {cls}")

    div = row.get("배당여부")
    if div:
        dps = row.get("DPS")
        yld = row.get("배당수익률")
        if dps is not None:
            details.append(f"DPS {dps:,.0f}원")
        if yld is not None:
            details.append(f"배당수익률 {yld:.1f}%")
            if yld >= 3:
                opportunities.append({"level": "positive", "category": "capital", "text": f"배당수익률 우수 ({yld:.1f}%)"})

    treasury = row.get("자사주보유")
    if treasury:
        details.append("자사주 보유")
        if row.get("자사주취득"):
            opportunities.append({"level": "positive", "category": "capital", "text": "당기 자사주 취득"})

    recent = row.get("최근증자")
    if recent:
        risks.append({"level": "warning", "category": "capital", "text": "최근 증자 이력"})

    contradict = row.get("모순형")
    if contradict:
        risks.append({"level": "warning", "category": "capital", "text": "모순형 (배당+증자 동시)"})

    grade_map = {"환원형": "A", "중립": "C", "희석형": "D"}
    grade = grade_map.get(cls, "C")

    return {
        "grade": grade,
        "summary": f"주주환원: {cls}",
        "details": details,
        "risks": risks,
        "opportunities": opportunities,
    }


def debt_to_insight(row: dict) -> dict:
    """debt 1행 → InsightResult 호환 dict."""
    risk_level = row.get("위험등급")
    if risk_level is None:
        return None

    details = []
    risks = []
    opportunities = []

    ratio = row.get("부채비율")
    if ratio is not None:
        details.append(f"부채비율 {ratio:.1f}%")
        if ratio > 200:
            risks.append({"level": "danger", "category": "debt", "text": f"부채비율 과다 ({ratio:.1f}%)"})

    icr = row.get("ICR")
    if icr is not None:
        details.append(f"ICR {icr:.1f}배")
        if icr < 1:
            risks.append({"level": "danger", "category": "debt", "text": f"ICR 1배 미만 ({icr:.1f})"})
        elif icr >= 5:
            opportunities.append({"level": "positive", "category": "debt", "text": f"ICR 양호 ({icr:.1f}배)"})

    bond = row.get("사채잔액")
    if bond is not None and bond > 0:
        details.append(f"사채잔액 {bond:,.0f}")
        short_pct = row.get("단기비중")
        if short_pct is not None and short_pct >= 50:
            risks.append({"level": "warning", "category": "debt", "text": f"단기사채 비중 {short_pct:.1f}%"})

    grade_map = {"안전": "A", "관찰": "B", "주의": "C", "고위험": "F"}
    grade = grade_map.get(risk_level, "C")

    return {
        "grade": grade,
        "summary": f"부채 위험등급: {risk_level}",
        "details": details,
        "risks": risks,
        "opportunities": opportunities,
    }


SCAN_CONVERTERS = {
    "governance": governance_to_insight,
    "workforce": workforce_to_insight,
    "capital": capital_to_insight,
    "debt": debt_to_insight,
}


def build_scan_payload(company) -> dict:
    """scan 4축 → InsightResult 호환 dict들."""
    result = {}
    for axis, converter in SCAN_CONVERTERS.items():
        try:
            df = getattr(company, axis)()
            if df is not None and len(df) > 0:
                row = df.row(0, named=True)
                insight = converter(row)
                result[axis] = insight
            else:
                result[axis] = None
        except Exception as e:
            print(f"  {axis} 실패: {e}")
            result[axis] = None
    return result


def build_unified_payload(company) -> dict:
    """insight 7영역 + scan 4축 = 11영역 통합 payload."""
    # insight 7영역
    try:
        insights = company.insights
        insight_areas = {}
        if insights and hasattr(insights, "grades"):
            for area_name in ["performance", "profitability", "health", "cashflow",
                              "governance", "risk", "opportunity"]:
                area = getattr(insights, area_name, None)
                if area:
                    insight_areas[area_name] = {
                        "grade": area.grade,
                        "summary": area.summary,
                        "details": area.details,
                        "risks": [{"level": r.level, "category": r.category, "text": r.text} for r in area.risks],
                        "opportunities": [{"level": o.level, "category": o.category, "text": o.text} for o in area.opportunities],
                    }
    except Exception as e:
        print(f"  insights 실패: {e}")
        insight_areas = {}

    # scan 4축
    scan_areas = build_scan_payload(company)

    # 통합 (insight.governance와 scan.governance가 겹침 → scan을 scan_governance로)
    unified = {}
    unified.update(insight_areas)
    for axis, data in scan_areas.items():
        key = f"scan_{axis}" if axis in insight_areas else axis
        unified[key] = data

    return unified


if __name__ == "__main__":
    test_codes = [
        ("005930", "삼성전자"),
        ("005380", "현대차"),
        ("035720", "카카오"),
    ]

    all_results = {}

    for code, name in test_codes:
        print(f"\n{'='*60}")
        print(f"{name} ({code})")
        print(f"{'='*60}")

        c = dartlab.Company(code)

        # scan 4축 개별 확인
        print("\n[scan 4축 개별]")
        scan_payload = build_scan_payload(c)
        for axis, data in scan_payload.items():
            if data is None:
                print(f"  {axis}: null")
            else:
                print(f"  {axis}: {data['grade']}등급 — {data['summary']}")
                if data["details"]:
                    for d in data["details"]:
                        print(f"    · {d}")
                if data["risks"]:
                    for r in data["risks"]:
                        print(f"    ⚠ {r['text']}")
                if data["opportunities"]:
                    for o in data["opportunities"]:
                        print(f"    ✓ {o['text']}")

        # 통합 payload
        print("\n[통합 11영역 payload]")
        unified = build_unified_payload(c)
        null_count = sum(1 for v in unified.values() if v is None)
        total_areas = len(unified)
        valid_areas = total_areas - null_count

        for key, data in unified.items():
            if data is None:
                print(f"  {key}: null")
            else:
                print(f"  {key}: {data['grade']}등급")

        # JSON 크기
        json_str = json.dumps(unified, ensure_ascii=False, default=str)
        json_kb = len(json_str.encode("utf-8")) / 1024

        print(f"\n[통계]")
        print(f"  총 영역: {total_areas}")
        print(f"  유효 영역: {valid_areas}")
        print(f"  null 영역: {null_count}")
        print(f"  JSON 크기: {json_kb:.1f}KB")

        all_results[name] = {
            "total": total_areas,
            "valid": valid_areas,
            "null": null_count,
            "json_kb": json_kb,
            "grades": {k: v["grade"] if v else None for k, v in unified.items()},
        }

    # 종합
    print(f"\n{'='*60}")
    print("종합 결과")
    print(f"{'='*60}")
    for name, r in all_results.items():
        print(f"  {name}: {r['valid']}/{r['total']}영역 유효, {r['json_kb']:.1f}KB, null {r['null']}개")
        grades = {k: v for k, v in r["grades"].items() if v}
        print(f"    등급: {grades}")
