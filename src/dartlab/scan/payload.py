"""scan 4축 → InsightResult 호환 페이로드 변환.

scan 엔진(governance/workforce/capital/debt) 결과를 insight 7영역과
동일한 dict 구조로 변환하여 11영역 통합 대시보드를 구성한다.
075-001 실험으로 검증 (3사 11/11영역 유효, 3.2~4.0KB, null 0개).

사용법::

    from dartlab.scan.payload import (
        build_scan_payload, build_unified_payload,
    )

    scan = build_scan_payload(company)
    unified = build_unified_payload(company)
"""

from __future__ import annotations


def governance_to_insight(row: dict) -> dict | None:
    """governance 1행 → InsightResult 호환 dict."""
    grade = row.get("등급")
    score = row.get("총점")
    if grade is None:
        return None

    details: list[str] = []
    risks: list[dict] = []
    opportunities: list[dict] = []

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
            opportunities.append(
                {"level": "positive", "category": "governance", "text": f"사외이사 비율 우수 ({outside:.1f}%)"}
            )
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


def workforce_to_insight(row: dict) -> dict | None:
    """workforce 1행 → InsightResult 호환 dict."""
    emp = row.get("직원수")
    if emp is None:
        return None

    details: list[str] = []
    risks: list[dict] = []
    opportunities: list[dict] = []

    details.append(f"직원수 {emp:,.0f}명")

    salary = row.get("평균급여_만원")
    if salary is not None:
        details.append(f"평균급여 {salary:,.0f}만원")

    rev_per = row.get("직원당매출_억")
    if rev_per is not None:
        details.append(f"직원당 매출 {rev_per:.1f}억")
        if rev_per >= 5:
            opportunities.append(
                {"level": "positive", "category": "workforce", "text": f"직원당 매출 우수 ({rev_per:.1f}억)"}
            )
        elif rev_per < 1:
            risks.append({"level": "warning", "category": "workforce", "text": f"직원당 매출 저조 ({rev_per:.1f}억)"})

    burden = row.get("급여매출괴리")
    if burden is not None:
        details.append(f"급여매출괴리 {burden:+.1f}%p")
        if burden > 10:
            risks.append({"level": "warning", "category": "workforce", "text": f"급여-매출 괴리 ({burden:+.1f}%p)"})

    gender = row.get("남녀격차")
    if gender is not None and gender > 40:
        risks.append({"level": "warning", "category": "workforce", "text": f"남녀 급여격차 {gender:.1f}%"})

    # 등급: 직원당매출 기준 간이 산출
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


def capital_to_insight(row: dict) -> dict | None:
    """capital 1행 → InsightResult 호환 dict."""
    cls = row.get("분류")
    if cls is None:
        return None

    details: list[str] = []
    risks: list[dict] = []
    opportunities: list[dict] = []

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
                opportunities.append(
                    {"level": "positive", "category": "capital", "text": f"배당수익률 우수 ({yld:.1f}%)"}
                )

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


def debt_to_insight(row: dict) -> dict | None:
    """debt 1행 → InsightResult 호환 dict."""
    risk_level = row.get("위험등급")
    if risk_level is None:
        return None

    details: list[str] = []
    risks: list[dict] = []
    opportunities: list[dict] = []

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


_SCAN_CONVERTERS = {
    "governance": governance_to_insight,
    "workforce": workforce_to_insight,
    "capital": capital_to_insight,
    "debt": debt_to_insight,
}


def build_scan_payload(company) -> dict[str, dict | None]:
    """scan 4축 → InsightResult 호환 dict들.

    Args:
        company: dartlab.Company 인스턴스.

    Returns:
        {governance: {...}, workforce: {...}, capital: {...}, debt: {...}}
    """
    result: dict[str, dict | None] = {}
    for axis, converter in _SCAN_CONVERTERS.items():
        method = getattr(company, axis, None)
        if method is None:
            result[axis] = None
            continue
        try:
            df = method()
            if df is not None and len(df) > 0:
                row = df.row(0, named=True)
                result[axis] = converter(row)
            else:
                result[axis] = None
        except (AttributeError, FileNotFoundError, KeyError, RuntimeError, ValueError):
            result[axis] = None
    return result


def build_unified_payload(company) -> dict[str, dict | None]:
    """insight 7영역 + scan 4축 = 11영역 통합 payload.

    Args:
        company: dartlab.Company 인스턴스.

    Returns:
        {performance, profitability, ..., scan_governance, workforce, capital, debt}
    """
    # insight 7영역
    insight_areas: dict[str, dict] = {}
    try:
        insights = company.insights
        if insights and hasattr(insights, "grades"):
            for area_name in (
                "performance",
                "profitability",
                "health",
                "cashflow",
                "governance",
                "risk",
                "opportunity",
            ):
                area = getattr(insights, area_name, None)
                if area:
                    insight_areas[area_name] = {
                        "grade": area.grade,
                        "summary": area.summary,
                        "details": area.details,
                        "risks": [{"level": r.level, "category": r.category, "text": r.text} for r in area.risks],
                        "opportunities": [
                            {"level": o.level, "category": o.category, "text": o.text} for o in area.opportunities
                        ],
                    }
    except (AttributeError, FileNotFoundError, KeyError, RuntimeError, ValueError):
        pass

    # scan 4축
    scan_areas = build_scan_payload(company)

    # 통합 (insight.governance와 scan.governance 충돌 → scan_governance)
    unified: dict[str, dict | None] = {}
    unified.update(insight_areas)
    for axis, data in scan_areas.items():
        key = f"scan_{axis}" if axis in insight_areas else axis
        unified[key] = data

    return unified
