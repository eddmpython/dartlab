"""scan 4축 → InsightResult 호환 페이로드 변환.

scan 엔진(governance/workforce/capital/debt) 결과를 InsightResult 와
동일한 dict 구조로 변환해 대시보드 4 축을 구성한다.
축 하나가 실패해도 나머지는 그대로 나온다 (축마다 격리).

사용법::

    from dartlab.scan.builders.kr.payload import (
        buildScanPayload, buildUnifiedPayload,
    )

    scan = buildScanPayload(company)
    unified = buildUnifiedPayload(company)
"""

from __future__ import annotations


def governanceToInsight(row: dict) -> dict | None:
    """governance scan 1 행 → InsightResult 호환 dict (대시보드 4 축의 1 축).

    Parameters
    ----------
    row : dict
        governance scan 결과 1행 (등급, 총점, 지분율, 사외이사비율, pay_ratio, 감사의견).

    Returns
    -------
    dict | None
        grade : str — 등급 (A~E)
        summary : str — 요약 문장
        details : list[str] — 세부 지표 문자열 목록
        risks : list[dict] — 위험 요인 (level, category, text)
        opportunities : list[dict] — 기회 요인 (level, category, text)
        등급 없으면 None.

    Raises
    ------
    없음 — row dict.get 기본값 처리.

    Examples
    --------
    >>> from dartlab.scan.builders.kr.payload import governanceToInsight
    >>> insight = governanceToInsight({"등급": "B", "총점": 75, "지분율": 35})
    >>> insight["grade"]
    'B'

    Capabilities:
        - governance scan 단일 row → 5 키 InsightResult dict 변환. 지분율 / 사외이사 / pay_ratio
          / 감사의견 임계 분기로 risks · opportunities 자동 생성. summary 한 줄 narrative.

    AIContext:
        ``buildScanPayload`` 호출 시 4 axis 중 첫 번째 변환. 4 축 대시보드에서 "지배구조" 카드
        본문을 채우는 source. AI 가 narrative 합성 시 details + risks·opportunities 텍스트를
        그대로 인용 가능.

    Guide:
        - 임계 정책: 최대주주 > 50 % (warning) · < 20 % (warning) · 사외이사 ≥ 40 % (positive) ·
          pay_ratio ≥ 10 (warning) · 감사의견 비적정 (danger). 정책 변경 시 본 함수 내부 분기 수정.
        - 등급 누락 row 는 None — 호출자 (`buildScanPayload`) 가 한 영역 skip 처리.

    When:
        Company / Story API 가 대시보드 페이로드 빌드 시 4 ToInsight 동시 호출. 단독 사용은
        prototype 디버깅 한정.

    How:
        row.get("등급") 가드 → 4 metric 분기 (지분율/사외이사/pay/감사) → details list 적재 +
        임계 위반 시 risks / opportunities append → 5 키 dict 반환.

    Requires:
        - scan governance axis 결과 row dict (`Scan("governance")` 산출의 한 행)

    SeeAlso:
        - :func:`workforceToInsight` · :func:`capitalToInsight` · :func:`debtToInsight` — 동료 변환
        - :func:`buildScanPayload` — 4 ToInsight 통합 호출
        - :func:`buildUnifiedPayload` . scan 4 축 대시보드 payload
    """
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


def workforceToInsight(row: dict) -> dict | None:
    """workforce scan 1 행 → InsightResult 호환 dict (대시보드 4 축의 1 축).

    Parameters
    ----------
    row : dict
        workforce scan 결과 1행 (직원수, 평균급여_만원, 직원당매출_억, 급여매출괴리, 남녀격차).

    Returns
    -------
    dict | None
        grade : str — 등급 (A~F, 직원당매출 기준)
        summary : str — 요약 문장
        details : list[str] — 세부 지표 문자열 목록
        risks : list[dict] — 위험 요인 (level, category, text)
        opportunities : list[dict] — 기회 요인 (level, category, text)
        직원수 없으면 None.

    Raises
    ------
    없음 — row dict.get 기본값 처리.

    Examples
    --------
    >>> from dartlab.scan.builders.kr.payload import workforceToInsight
    >>> insight = workforceToInsight({"직원수": 1000, "평균급여_만원": 5000, "직원당매출_억": 3.5})
    >>> insight["grade"]
    'B'

    Capabilities:
        - workforce scan 단일 row → 5 키 InsightResult. 직원당매출 / 급여매출괴리 / 남녀격차
          임계 분기로 risks · opportunities 자동 생성. 등급은 직원당매출 기준 5 단계 (A/B/C/D/F).

    AIContext:
        ``buildScanPayload`` 의 2 번째 변환. "인력/급여" 대시보드 카드 source. 직원당매출 5억 ≥
        positive · 1억 < warning · 급여매출괴리 > 10 %p · 남녀격차 > 40 % 임계 narrative.

    Guide:
        - 등급 기준은 직원당매출 1 metric. 다축 등급 합성 안 함 (단순성 우선).
        - 직원수 누락 row 는 None — 호출자가 한 영역 skip.

    When:
        Company / Story API 대시보드 빌드 시 4 ToInsight 동시 호출의 한 단계.

    How:
        row.get("직원수") 가드 → details 적재 → 4 metric 분기 (rev_per/burden/gender/grade) →
        5 키 dict 반환.

    Requires:
        - scan workforce axis 결과 row dict

    SeeAlso:
        - :func:`governanceToInsight` · :func:`capitalToInsight` · :func:`debtToInsight`
        - :func:`buildScanPayload` — 통합 호출
    """
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


def capitalToInsight(row: dict) -> dict | None:
    """capital 1행 → InsightResult 호환 dict.

    Parameters
    ----------
    row : dict
        capital scan 결과 1행 (분류, 배당여부, DPS, 배당수익률, 자사주보유, 최근증자, 모순형).

    Returns
    -------
    dict | None
        grade : str — 등급 (A/C/D, 환원형/중립/희석형 매핑)
        summary : str — 요약 문장
        details : list[str] — 세부 지표 문자열 목록
        risks : list[dict] — 위험 요인 (level, category, text)
        opportunities : list[dict] — 기회 요인 (level, category, text)
        분류 없으면 None.

    Raises
    ------
    없음 — row dict.get 기본값 처리.

    Examples
    --------
    >>> from dartlab.scan.builders.kr.payload import capitalToInsight
    >>> insight = capitalToInsight({"분류": "환원형", "배당여부": True, "DPS": 1000, "배당수익률": 3.5})
    >>> insight["grade"]
    'A'

    Capabilities:
        - capital scan 단일 row → 5 키 InsightResult. 분류 (환원형/중립/희석형) → grade 매핑
          + 배당수익률 / 자사주취득 / 최근증자 / 모순형 임계 분기로 risks · opportunities.

    AIContext:
        ``buildScanPayload`` 의 3 번째 변환. "주주환원" 카드 source. 배당수익률 ≥ 3 % positive ·
        자사주 취득 positive · 최근증자 / 모순형 warning narrative.

    Guide:
        - "모순형" = 같은 시기에 배당과 증자를 동시 → 자본정책 일관성 결여 신호.
        - 분류 누락 row 는 None.

    When:
        Company / Story API 대시보드 빌드 시 4 ToInsight 동시 호출.

    How:
        row.get("분류") 가드 → details 적재 → 배당/자사주/증자/모순 분기 → grade_map 매핑
        → 5 키 dict.

    Requires:
        - scan capital axis 결과 row dict

    SeeAlso:
        - :func:`governanceToInsight` · :func:`workforceToInsight` · :func:`debtToInsight`
        - :func:`buildScanPayload`
    """
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


def debtToInsight(row: dict) -> dict | None:
    """debt scan 1 행 → InsightResult 호환 dict (대시보드 4 축의 1 축).

    Parameters
    ----------
    row : dict
        debt scan 결과 1행 (위험등급, 부채비율, ICR, 사채잔액, 단기비중).

    Returns
    -------
    dict | None
        grade : str — 등급 (A/B/C/F, 위험등급 매핑)
        summary : str — 요약 문장
        details : list[str] — 세부 지표 문자열 목록
        risks : list[dict] — 위험 요인 (level, category, text)
        opportunities : list[dict] — 기회 요인 (level, category, text)
        위험등급 없으면 None.

    Raises
    ------
    없음 — row dict.get 기본값 처리.

    Examples
    --------
    >>> from dartlab.scan.builders.kr.payload import debtToInsight
    >>> insight = debtToInsight({"위험등급": "안전", "부채비율": 80, "ICR": 6.5})
    >>> insight["grade"]
    'A'

    Capabilities:
        - debt scan 단일 row → 5 키 InsightResult. 부채비율 / ICR / 사채잔액 / 단기비중 임계
          분기로 risks · opportunities. grade 는 위험등급 4 단계 매핑.

    AIContext:
        ``buildScanPayload`` 의 4 번째 (마지막) 변환. "부채구조" 카드 source. 부채비율 > 200 %
        danger · ICR < 1 danger · ICR ≥ 5 positive · 단기비중 과다 warning narrative.

    Guide:
        - 위험등급 정책 (안전/주의/위험/심각) 은 scan debt risk 모듈이 정의 — 본 함수는 매핑만.
        - 위험등급 누락 row 는 None.

    When:
        Company / Story API 대시보드 빌드 시 4 ToInsight 동시 호출.

    How:
        row.get("위험등급") 가드 → details 적재 → 4 metric 분기 → grade_map 매핑 → 5 키 dict.

    Requires:
        - scan debt axis 결과 row dict

    SeeAlso:
        - :func:`governanceToInsight` · :func:`workforceToInsight` · :func:`capitalToInsight`
        - :func:`buildScanPayload`
    """
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
    "governance": governanceToInsight,
    "workforce": workforceToInsight,
    "capital": capitalToInsight,
    "debt": debtToInsight,
}


def buildScanPayload(company) -> dict[str, dict | None]:
    """scan 4 축 → InsightResult 호환 dict 4 개 통합 (governance/workforce/capital/debt).

    Parameters
    ----------
    company : Company
        dartlab.Company 인스턴스.

    Returns
    -------
    dict[str, dict | None]
        governance : dict | None — 지배구조 insight (grade/summary/details/risks/opportunities)
        workforce : dict | None — 인력 insight
        capital : dict | None — 주주환원 insight
        debt : dict | None — 부채구조 insight

    Raises
    ------
    없음 — 각 axis 호출 실패 (AttributeError·FileNotFoundError·RuntimeError) 는 내부 흡수 → None.

    Examples
    --------
    >>> from dartlab.scan.builders.kr.payload import buildScanPayload
    >>> import dartlab
    >>> c = dartlab.Company("005930")
    >>> payload = buildScanPayload(c)
    >>> payload["governance"]["grade"] if payload["governance"] else "n/a"

    Capabilities:
        - 4 ToInsight 함수 (``governanceToInsight`` · ``workforceToInsight`` · ``capitalToInsight``
          · ``debtToInsight``) 통합 호출. ``_SCAN_CONVERTERS`` dispatch table 로 axis → converter
          매핑.
        - 각 axis 호출 실패는 isolation — 한 axis 가 fail 해도 다른 3 axis 는 정상 반환.

    AIContext:
        Server API (Company 페이로드 엔드포인트) 가 호출하는 메인 진입점.
        ``buildUnifiedPayload`` 가 본 함수를 그대로 위임한다.

    Guide:
        - company 가 axis method 없으면 silent None (NotImplemented 대신 빈 슬롯).
        - 4 axis 모두 실패 시 모든 키가 None 인 dict — API 응답 빈 카드 4 개.

    When:
        Story / Insight builder 가 대시보드 / 1 사 종합 분석 빌드 시.

    How:
        ``_SCAN_CONVERTERS.items()`` iterate → ``getattr(company, axis)()`` → ``df.row(0, named=True)``
        → converter 호출 → result dict 적재. 매 axis try/except 격리.

    Requires:
        - ``Company.{governance, workforce, capital, debt}`` 메서드 (DataFrame 반환)
        - 각 ToInsight 함수

    SeeAlso:
        - :func:`governanceToInsight` · :func:`workforceToInsight` · :func:`capitalToInsight` ·
          :func:`debtToInsight`
        - :func:`buildUnifiedPayload` . 본 함수를 그대로 위임하는 대시보드 진입점
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


def buildUnifiedPayload(company) -> dict[str, dict | None]:
    """scan 4 축 대시보드 payload. 현재는 ``buildScanPayload`` 와 같은 것을 돌려준다.

    예전에는 여기서 ``Company.insights`` 의 7 영역을 함께 붙여 11 영역을 만들었다. 그 accessor
    는 사라졌는데 호출부가 `except (AttributeError, ...)` 로 통째로 삼키고 있어서, 7 영역이
    조용히 0 개가 된 채로 남았다. 문서는 11 키를 약속하는데 실제로는 4 키만 나왔고 그 사실이
    어디에도 드러나지 않았다. 죽은 가지를 걷어내고 실제로 주는 것만 적는다.

    같은 능력이 필요하면 계약 호출로 얻는다. 재무 분석 영역은 ``c.analysis("financial", 축)``
    이고 축 목록은 ``dartlab.analysis("financial")`` 로 본다.

    Parameters
    ----------
    company : Company
        dartlab.Company 인스턴스.

    Returns
    -------
    dict[str, dict | None]
        governance : dict | None. 지배구조
        workforce : dict | None. 인력
        capital : dict | None. 주주환원
        debt : dict | None. 부채구조

    Raises
    ------
    없음. scan 축 호출 실패는 축마다 격리되어 None 으로 떨어진다.

    Examples
    --------
    >>> from dartlab.scan.builders.kr.payload import buildUnifiedPayload
    >>> import dartlab
    >>> c = dartlab.Company("005930")
    >>> payload = buildUnifiedPayload(c)
    >>> set(payload.keys()) == {"governance", "workforce", "capital", "debt"}
    True

    Capabilities:
        - scan 4 축 (governance / workforce / capital / debt) 을 InsightResult 호환 dict 로 통합.
        - 축 하나가 실패해도 나머지 3 축은 정상 반환 (키는 항상 4 개).

    AIContext:
        Server API 대시보드 엔드포인트 (e.g. ``/api/company/{code}/payload``) 의 메인 출력.
        프론트 대시보드가 카드를 그릴 source.

    Guide:
        - 축이 None 이어도 dict 키는 항상 4 개 (front-end 안전성).
        - 이름은 옛 통합 시절 것이 남아 있다. 호출부 호환 때문에 유지한다.

    When:
        Server API 페이로드 빌드 시. Story builder 에서 다영역 비교 narrative 추출 시.

    How:
        ``buildScanPayload`` 위임.

    Requires:
        - ``Company.{governance, workforce, capital, debt}`` 메서드
        - :func:`buildScanPayload`

    SeeAlso:
        - :func:`buildScanPayload`. scan 4 axis 통합
        - :mod:`dartlab.providers.dart.company`. 본 함수 호출자
    """
    return buildScanPayload(company)
