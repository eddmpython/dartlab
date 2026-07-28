"""credit/features/narrative 7 축 narrate 함수 분리.

credit/features/narrative.py 가 823 줄 god module 이라 7 축 서사 함수를 분리.
identity 보존을 위해 narrative.py 가 본 모듈에서 re-export 한다.

축별 narrate 함수:
- narrateRepayment: 채무상환능력 (이자보상배율 + Debt/EBITDA)
- narrateCapitalStructure: 자본구조 (부채비율 + 차입금의존도)
- narrateLiquidity: 유동성 (current/quick ratio)
- narrateCashFlow: 현금흐름 (OCF + FCF + CFO 안정성)
- narrateBusinessStability: 사업안정성 (매출 변동성)
- narrateReliability: 재무신뢰성 (감사의견 + 발생주의 비율)
- narrateDisclosureRisk: 공시리스크 (정정공시 + Beneish M-Score)

``_severity`` 임계표 본체는 `_narrativeSeverity` 로 옮겼다 (narrative.py 와 공유).
"""

from __future__ import annotations

from dartlab.core.formatting import formatDecimal, formatKr
from dartlab.credit.features._narrativeSeverity import _severity
from dartlab.credit.features._narrativeTypes import AxisNarrative


def _fmt(v, suffix="", decimals=1) -> str:
    """고정 소수 + suffix (None → N/A)."""
    return formatDecimal(v, decimals=decimals, suffix=suffix, nullStr="N/A")


def _fmtTril(v) -> str:
    """금액을 조/억 단위로 변환 (원 접미사 포함)."""
    return formatKr(v, withWon=True, nullStr="N/A")


def narrateLiquidity(latest: dict, axisScore: float | None) -> AxisNarrative:
    """축 3: 유동성 서사 — 유동비율 + 단기차입금 + 현금비율 + 모순 진단.

    Capabilities:
        유동비율/단기차입금/현금비율 3 지표를 결합해 단기 유동성 진단 + 모순
        탐지 (유동비율 좋은데 단기차입금 비중 높음 = 차환 리스크).

    Args:
        latest: 최신 분기 dict. 키: ``currentRatio`` (%), ``shortTermDebtRatio``
            (%), ``cashRatio`` (%).
        axisScore: 유동성 축 점수 (0~100). None 이면 평가 불가.

    Returns:
        AxisNarrative ``{axisName, summary, details, severity}``.

    Raises:
        없음.

    Example:
        >>> n = narrateLiquidity({"currentRatio": 250, "shortTermDebtRatio": 30,
        ...                       "cashRatio": 40}, axisScore=10)
        >>> n.severity
        'strong'

    Guide:
        유동비율 > 200 = 매우 우수, > 150 = 양호, > 100 = 적정, < 100 =
        부족. 모순 케이스 (CR>150 + STDR>50) 는 차환 의존도 큰 회사 — KR
        대기업 자주 등장 (단기 만기 회전).

    SeeAlso:
        - ``narrateCashFlow``: OCF 기반 유동성 보강 진단
        - ``narrateRepayment``: 이자보상 (유동성과 연계)

    When:
        유동성 축 narrative 가 필요할 때. ``buildNarratives`` 가 진입점.

    How:
        latest dict 의 3 지표 → 임계값 매핑 → details 라인 → 모순 진단 케이스 추가 → severity.

    Requires:
        latest dict 의 currentRatio 필수, 나머지 옵션.

    AIContext:
        단기차입금 비중 50%+ 회사는 신용경색 시 즉시 위험. summary 만 인용
        금지 — details 의 모순 진단 라인 함께 노출.

    LLM Specifications:
        AntiPatterns:
            - 유동비율만 보고 "유동성 우수" 결론 — STDR (단기차입금 비중)
              병행 확인 필수.
            - cashRatio 가 매우 높은 (50%+) 회사 — 안전이지만 자본배분
              비효율 (배당/투자 부진) 신호 가능.
        OutputSchema:
            AxisNarrative ``{axisName, summary, details, severity}``.
        Prerequisites:
            latest dict 에 currentRatio 보유.
        Freshness:
            latest = 최신 분기.
        Dataflow:
            currentRatio/STDR/cashRatio → 분기 룰 → 모순 탐지 → details →
            severity (axisScore).
        TargetMarkets: KR (DART), US (EDGAR — current ratio 표준 동일).
    """
    details = []
    sev = _severity(axisScore)

    cr = latest.get("currentRatio")
    if cr is not None:
        if cr > 200:
            details.append(f"유동비율 {_fmt(cr, '%', 0)}로 단기 유동성이 매우 우수하다.")
        elif cr > 150:
            details.append(f"유동비율 {_fmt(cr, '%', 0)}로 단기 유동성이 양호하다.")
        elif cr > 100:
            details.append(f"유동비율 {_fmt(cr, '%', 0)}로 단기 유동성이 적정하다.")
        else:
            details.append(f"유동비율 {_fmt(cr, '%', 0)}로 단기 유동성이 부족하다.")

    stdr = latest.get("shortTermDebtRatio")
    if stdr is not None and stdr > 50:
        details.append(f"단기차입금 비중 {_fmt(stdr, '%', 0)}로 차환 리스크가 존재한다.")

    cashR = latest.get("cashRatio")
    if cashR is not None and cashR > 30:
        details.append(f"현금비율 {_fmt(cashR, '%', 0)}로 즉시 동원 가능한 현금이 충분하다.")

    # 유동성 지표 모순 설명: 유동비율/현금비율은 좋은데 단기차입금비중이 높은 경우
    if cr is not None and cr > 150 and stdr is not None and stdr > 50:
        details.append(
            f"유동비율({_fmt(cr, '%', 0)})과 현금비율은 우수하나, "
            f"단기차입금 비중({_fmt(stdr, '%', 0)})이 높아 차환 시점의 유동성 관리가 필요하다. "
            f"현금 보유량이 충분하므로 실질적 차환 위험은 낮다."
        )

    summary = "유동성은 "
    if sev == "strong":
        summary += "매우 충분하다."
    elif sev == "adequate":
        summary += "적정 수준이다."
    elif sev == "weak":
        summary += "주의가 필요한 수준이다."
    else:
        summary += "부족하여 차환/유동성 위험이 높다."

    return AxisNarrative("유동성", summary, details, sev)


def narrateCashFlow(
    latest: dict,
    axisScore: float | None,
    metrics: dict,
    *,
    captive: bool = False,
) -> AxisNarrative:
    """축 4: 현금흐름 서사 생성.

    Capabilities:
        OCF/매출 비율, FCF 추이, 현금흐름 패턴 (+/-/-) 을 해석해 현금 창출력 + 투자 부담 narrative
        생성. captive=True (캡티브 금융 복합기업) 면 자동차/할부금융 특수 해석 분기.

    OCF/매출, FCF 추이, 현금흐름 패턴(+/-/-)을 해석하여
    현금 창출력과 투자 부담에 대한 서사를 생성한다.

    Parameters
    ----------
    latest : dict
        최신 분기 지표. 주요 키: ``ocfToSales`` (%),
        ``fcf`` (원), ``ocf`` (원).
    axisScore : float | None
        현금흐름 축 점수 (점). None이면 평가 불가.
    metrics : dict
        전체 메트릭스 딕셔너리 (추이 분석용).
    captive : bool
        캡티브 금융 복합기업 여부.

    Returns
    -------
    AxisNarrative
        axisName : str — 축 이름 (``"현금흐름"``)
        summary : str — 한 줄 요약 문장
        details : list[str] — 세부 해석 문장 목록
        severity : str — 심각도 (``"strong"`` / ``"moderate"`` / ``"weak"`` / ``"critical"``)

    Raises:
        없음.

    Example:
        >>> from dartlab.credit.features._narrativeAxes import narrateCashFlow
        >>> n = narrateCashFlow({"ocfToSales": 18, "ocf": 1e12, "fcf": 5e11}, 20, metrics)
        >>> n.severity
        'strong'

    Guide:
        OCF/매출 > 15 = 우수, > 5 = 양호, < 0 = 영업현금유출. captive 회사는 OCF 부호 해석 주의.

    When:
        현금흐름 축 narrative 가 필요할 때. ``buildNarratives`` 진입점.

    How:
        latest OCF/매출 → 임계값 매핑 → metrics 시계열 → FCF 추이 + 패턴 → details / severity.

    Requires:
        - latest 의 ocfToSales/ocf 필수
        - metrics 시계열 (추이 분석용)

    See Also:
        - ``dartlab.credit.features._narrativeAxes.narrateLiquidity`` : 유동성 보강
        - ``dartlab.credit.features._narrativeAxes.buildNarratives`` : 본 함수 사용자

    AIContext:
        OCF 단독 인용 금지 — FCF / 패턴 / captive 단서까지 함께. 음수 OCF 는 "영업현금유출"
        명시.
    """
    details = []
    sev = _severity(axisScore)

    os = latest.get("ocfToSales")
    if os is not None:
        if os > 100:
            # 지주사 등: 매출 < OCF (배당수입/지분법이 OCF에 포함)
            details.append(
                f"OCF/매출 {_fmt(os, '%')}로 자체 매출 대비 현금흐름이 매우 크다. "
                f"이는 자회사 배당수입 등 영업외 현금이 포함된 것으로 판단된다."
            )
        elif os > 15:
            details.append(f"OCF/매출 {_fmt(os, '%')}로 매출 대비 현금 창출력이 우수하다.")
        elif os > 5:
            details.append(f"OCF/매출 {_fmt(os, '%')}로 현금 창출이 양호하다.")
        elif os > 0:
            details.append(f"OCF/매출 {_fmt(os, '%')}로 현금 창출이 제한적이다.")
        else:
            details.append(f"OCF/매출 {_fmt(os, '%')}로 영업에서 현금이 유출되고 있다.")

    fcf = latest.get("fcf")
    if fcf is not None:
        if fcf > 0:
            details.append("투자 이후에도 잉여현금흐름(FCF)이 양수로 자체 성장 여력이 있다.")
        else:
            details.append("투자 부담으로 잉여현금흐름(FCF)이 음수이다.")

    # OCF 추세
    history = metrics.get("history", [])
    if len(history) >= 3:
        ocfs = [h.get("ocf") for h in history[:3]]
        if all(o is not None and o > 0 for o in ocfs):
            details.append("영업현금흐름이 3기 연속 양수로 안정적이다.")

    # 캡티브 맥락: OCF 음수는 금융자회사 대출 유출 포함 가능
    if captive:
        ocfVal = latest.get("ocf")
        if ocfVal is not None and ocfVal < 0:
            details.append(
                "참고: OCF가 음수인 것은 연결 기준으로 금융자회사의 대출 원금 유출이 포함되기 때문이다. "
                "제조 모회사 단독으로는 OCF가 정상 범위일 수 있다."
            )

    summary = "현금흐름 창출 능력은 "
    if sev == "strong":
        summary += "우수하다."
    elif sev == "adequate":
        summary += "양호하다."
    elif sev == "weak":
        summary += "보통 수준이다."
    else:
        summary += "취약하여 외부 조달 의존도가 높다."

    return AxisNarrative("현금흐름", summary, details, sev)


def narrateBusinessStability(biz: dict, axisScore: float | None) -> AxisNarrative:
    """축 5: 사업 안정성 서사 — 매출 변동계수 + 규모 + 사업 다각화 (HHI).

    Capabilities:
        매출 변동계수 (3~5 년 CV) + 매출 규모 + 세그먼트 HHI (Herfindahl)
        를 결합해 사업 안정성 진단. 신평사의 "Business Risk" 축 직접 매핑.

    Args:
        biz: 사업 안정성 dict. 키:
            - ``revenueCV`` (%): 매출 변동계수 (3~5 년)
            - ``latestRevenue`` (원): 최신 매출
            - ``segmentHHI`` (점): Herfindahl 사업 집중도 (0~10000)
        axisScore: 사업안정성 축 점수 (0~100). None 이면 평가 불가.

    Returns:
        AxisNarrative ``{axisName, summary, details, severity}``.

    Raises:
        없음.

    Example:
        >>> n = narrateBusinessStability(
        ...     {"revenueCV": 8, "latestRevenue": 15e12, "segmentHHI": 2000},
        ...     axisScore=15)
        >>> n.severity
        'strong'

    Guide:
        revenueCV < 10% = 매우 안정 (utility/통신 등), 10~20% = 적정, >20% =
        변동 큼 (시클리컬). HHI < 1500 = 다각화, > 4000 = 집중 (단일 사업).
        매출 10조원+ = 대형주 안정성 보너스.

    SeeAlso:
        - ``narrateRepayment``: 부채 상환능력 (사업 안정성과 보완)
        - ``credit.engine.evaluateCompany``: 본 함수 호출

    When:
        사업안정성 축 narrative 가 필요할 때. ``buildNarratives`` 진입점.

    How:
        biz dict 의 3 지표 → 임계 매핑 → details → severity (axisScore 기반).

    Requires:
        biz dict 의 revenueCV 필수, latestRevenue/segmentHHI 옵션.

    AIContext:
        시클리컬 (조선/철강/화학) 회사의 revenueCV 30%+ 는 정상 — 무조건
        "변동성 크다" 부정 인용 금지. 업종 맥락 함께 노출.

    LLM Specifications:
        AntiPatterns:
            - HHI 만으로 다각화 평가 — 다각화가 신용에 항상 + 가 아님 (관련
              없는 사업 다각화는 비효율).
            - 매출 규모 1 조원 미만 회사를 "소형" 으로 negative 인용 — 우량
              중소기업도 안정 가능.
        OutputSchema:
            AxisNarrative ``{axisName, summary, details, severity}``.
        Prerequisites:
            biz 에 revenueCV 보유 + 매출 시계열 ≥ 3 년 (CV 계산 기반).
        Freshness:
            biz = 최신 분기 + 3~5 년 시계열.
        Dataflow:
            biz dict → revenueCV/규모/HHI 룰 → details → severity.
        TargetMarkets: KR (사업부문 dart 공시 기반), US (segment reporting).
    """
    details = []
    sev = _severity(axisScore)

    revCV = biz.get("revenueCV")
    if revCV is not None:
        if revCV < 10:
            details.append(f"매출 변동계수 {_fmt(revCV, '%')}로 매출이 매우 안정적이다.")
        elif revCV < 20:
            details.append(f"매출 변동계수 {_fmt(revCV, '%')}로 적정한 안정성을 보인다.")
        else:
            details.append(f"매출 변동계수 {_fmt(revCV, '%')}로 실적 변동성이 크다.")

    latestRev = biz.get("latestRevenue")
    if latestRev is not None:
        revTril = latestRev / 1e12
        if revTril > 10:
            details.append(f"매출 규모 {revTril:.0f}조원으로 대형 기업의 사업 안정성을 보유한다.")
        elif revTril > 1:
            details.append(f"매출 규모 {revTril:.1f}조원 수준이다.")

    hhi = biz.get("segmentHHI")
    if hhi is not None:
        if hhi < 1500:
            details.append("사업 부문이 분산되어 다각화 효과가 있다.")
        elif hhi > 5000:
            details.append("사업이 단일 부문에 집중되어 있어 분산 효과가 제한적이다.")

    summary = "사업 안정성은 "
    if sev == "strong":
        summary += "매우 높다."
    elif sev == "adequate":
        summary += "양호한 수준이다."
    else:
        summary += "변동성이 존재한다."

    return AxisNarrative("사업안정성", summary, details, sev)


def narrateReliability(
    rel: dict,
    auditOpinion: str | None,
    axisScore: float | None,
    *,
    captive: bool = False,
) -> AxisNarrative:
    """축 6: 재무 신뢰성.

    Capabilities:
        Beneish M-Score + Piotroski F-Score + 감사의견을 결합해 재무제표 신뢰성 narrative 생성.
        captive=True (캡티브 금융) 일 때 F-Score 왜곡 단서 자동 추가.

    Args:
        rel: 신뢰성 dict. 키 beneishMScore / piotroskiFScore.
        auditOpinion: 감사의견 문자열 (예: "적정" / "한정" / "부적정").
        axisScore: 신뢰성 축 점수 (0~100).
        captive: 캡티브 금융 복합기업 여부.

    Returns:
        AxisNarrative ``{axisName, summary, details, severity}``.

    Raises:
        없음.

    Example:
        >>> narrateReliability({"beneishMScore": -2.8, "piotroskiFScore": 8}, "적정", 18)

    Guide:
        M-Score < -2.22 = 조작 가능성 낮음. F-Score >= 7 = 강건. 감사의견 "한정"/"부적정" 시
        severity 직접 영향. captive 회사는 F-Score 보수적으로 해석.

    When:
        재무신뢰성 축 narrative 가 필요할 때. ``buildNarratives`` 진입점.

    How:
        beneishMScore/piotroskiFScore/auditOpinion 매핑 → captive 보정 → severity 결합.

    Requires:
        - rel dict 의 beneishMScore/piotroskiFScore (optional)
        - auditOpinion 문자열 (optional)

    See Also:
        - ``dartlab.credit.features._narrativeAxes.buildNarratives`` : 본 함수 사용자

    AIContext:
        F-Score 단독 인용 금지 — M-Score / 감사의견 결합. 감사의견 "한정" 이상은 답변에 명시.
    """
    details = []
    sev = _severity(axisScore)

    m = rel.get("beneishMScore")
    if m is not None:
        if m < -2.22:
            details.append("Beneish M-Score 기준 이익 조작 가능성이 낮다.")
        elif m > -1.78:
            details.append("Beneish M-Score가 조작 가능성 구간에 해당하여 주의가 필요하다.")

    f = rel.get("piotroskiFScore")
    if f is not None:
        if f >= 7:
            details.append(f"Piotroski F-Score {f}/9로 재무 펀더멘탈이 강건하다.")
        elif f <= 3:
            details.append(f"Piotroski F-Score {f}/9로 재무 펀더멘탈이 취약하다.")
            if captive:
                details.append(
                    "다만, 캡티브 금융 연결 효과로 OCF/유동비율 등이 왜곡되어 "
                    "F-Score가 실제 모회사 체력보다 낮게 산출될 수 있다."
                )

    if auditOpinion:
        if "적정" in auditOpinion and "부적정" not in auditOpinion and "한정" not in auditOpinion:
            details.append("감사의견은 적정으로 재무제표 신뢰성에 문제가 없다.")
        elif "한정" in auditOpinion:
            details.append("감사의견이 한정으로 재무제표 일부 항목에 대한 신뢰성 우려가 있다.")
        elif "부적정" in auditOpinion or "의견거절" in auditOpinion:
            details.append("감사의견이 비적정으로 재무제표 전반의 신뢰성에 심각한 문제가 있다.")

    summary = "재무 신뢰성은 "
    if sev == "strong":
        summary += "우수하다."
    elif sev == "adequate":
        summary += "양호하다."
    else:
        summary += "주의가 필요하다."

    return AxisNarrative("재무신뢰성", summary, details, sev)


def narrateDisclosureRisk(dr: dict | None, axisScore: float | None) -> AxisNarrative:
    """축 7: 공시 리스크.

    Capabilities:
        scan 단계에서 검출된 만성 우발부채 / 리스크 키워드 (횡령·배임·과징금) 수를 narrative
        로 변환. dr=None 이면 "신호 없음" 폴백 (strong).

    Args:
        dr: 공시 리스크 dict (chronicYears / riskKeyword). None 허용.
        axisScore: 공시리스크 축 점수 (0~100).

    Returns:
        AxisNarrative ``{axisName, summary, details, severity}``.

    Raises:
        없음.

    Example:
        >>> narrateDisclosureRisk({"chronicYears": 3, "riskKeyword": 2}, 35)

    Guide:
        chronicYears >= 3 = 만성. riskKeyword > 0 = 답변에 키워드 종류 단서 명시 권장.

    When:
        공시리스크 축 narrative 가 필요할 때. ``buildNarratives`` 진입점.

    How:
        chronicYears / riskKeyword 카운트 → 임계 매핑 → details → severity.

    Requires:
        - L1.5 scan 의 공시 리스크 신호 (optional dr)

    See Also:
        - ``dartlab.credit.features._narrativeAxes.buildNarratives`` : 본 함수 사용자

    AIContext:
        키워드 검출은 자동 — 답변 시 "공시 리스크 N 건 감지" 같이 수량만 명시, 단정 ("횡령
        있음") 금지.
    """
    details = []
    sev = _severity(axisScore)

    if dr is None:
        return AxisNarrative(
            "공시리스크", "공시 리스크 신호가 감지되지 않았다.", ["scan 데이터 범위 내 특이 신호 없음."], "strong"
        )

    chronic = dr.get("chronicYears") or dr.get("chronic_years", 0)
    if chronic >= 3:
        details.append(f"우발부채가 {chronic}년 연속 증가하여 만성화 징후가 있다.")
    elif chronic >= 1:
        details.append("우발부채가 증가 추세이나 아직 만성 수준은 아니다.")

    risk = dr.get("riskKeyword") or dr.get("risk_keyword", 0)
    if risk > 0:
        details.append(f"리스크 키워드(횡령/배임/과징금 등)가 {risk}건 감지되었다.")

    if not details:
        details.append("특이한 공시 리스크 신호는 감지되지 않았다.")

    summary = "공시 리스크는 "
    if sev == "strong":
        summary += "낮은 수준이다."
    elif sev == "adequate":
        summary += "양호하다."
    else:
        summary += "모니터링이 필요하다."

    return AxisNarrative("공시리스크", summary, details, sev)


# ═══════════════════════════════════════════════════════════
# 통합
# ═══════════════════════════════════════════════════════════


def buildNarratives(
    result: dict,
    *,
    captive: bool = False,
    holding: bool = False,
    separateMetrics: dict | None = None,
) -> list[AxisNarrative]:
    """engine.py evaluateCompany 결과에서 7축 전체 서사 생성.

    Capabilities:
        ``evaluateCompany`` 결과 dict 를 받아 7 축 (채무상환/자본구조/유동성/현금흐름/사업안정성/
        재무신뢰성/공시리스크) narrative 리스트 산출. detail=True 결과의 ``narratives`` 키에
        그대로 들어가는 단일 진입점.

    Parameters
    ----------
    captive : bool
        캡티브 금융 복합기업 여부. True이면 연결 재무 왜곡 맥락 문장을 추가한다.
    holding : bool
        지주사 여부. (현재 축별 서사에서 직접 사용하지 않으나 향후 확장용.)
    separateMetrics : dict | None
        별도 재무제표 지표. captive일 때 연결/별도 대비 참고 문장에 사용한다.

    Returns:
        list[AxisNarrative] (7 개) — 각 ``{axisName, summary, details, severity}``.

    Raises:
        없음 — 입력 result 누락 키는 빈 dict 폴백.

    Example:
        >>> from dartlab.credit.features._narrativeAxes import buildNarratives
        >>> narratives = buildNarratives(creditResult, captive=False)
        >>> narratives[0].summary

    Guide:
        UI / Story 6 막의 narrative 줄거리 데이터. 각 narrative 의 details 라인이 답변에 직접
        인용 가능한 한국어 문장.

    When:
        ``evaluateCompany(detail=True)`` 가 본 함수 호출. AI 답변 narrative 라인 직접 인용 시.

    How:
        result.axes / metricsHistory / businessStability / reliability 등 추출 → 7 축
        narrate* 호출 → list 반환.

    Requires:
        - result dict (``evaluateCompany`` 산출, axes / metricsHistory 키 보유)

    See Also:
        - ``dartlab.credit.features._narrativeAxes.narrateLiquidity`` 외 6 축 narrate
        - ``dartlab.credit.engine.evaluateCompany`` : 본 함수 사용자

    AIContext:
        AI 가 신용 narrative 답변 생성 시 본 결과의 ``details`` 직접 인용. severity 별 색상 /
        강조 가능 — 답변에 severity 단서도 함께.
    """
    axes = result.get("axes", [])
    latest = {}
    metricsHistory = result.get("metricsHistory", [])
    if metricsHistory:
        latest = metricsHistory[0]

    biz = result.get("businessStability", {})
    rel = result.get("reliability", {})
    audit = result.get("auditOpinion")
    dr = result.get("disclosureRisk")
    sector = result.get("sector", "")

    def _axisScore(name):
        for a in axes:
            if a.get("name") == name:
                return a.get("score")
        return None

    return [
        narrateRepayment(
            latest,
            _axisScore("채무상환능력"),
            sector,
            captive=captive,
            separateMetrics=separateMetrics,
        ),
        narrateCapitalStructure(
            latest,
            _axisScore("자본구조"),
            captive=captive,
            separateMetrics=separateMetrics,
        ),
        narrateLiquidity(latest, _axisScore("유동성")),
        narrateCashFlow(
            latest,
            _axisScore("현금흐름"),
            {"history": metricsHistory},
            captive=captive,
        ),
        narrateBusinessStability(biz or {}, _axisScore("사업안정성")),
        narrateReliability(rel or {}, audit, _axisScore("재무신뢰성"), captive=captive),
        narrateDisclosureRisk(dr, _axisScore("공시리스크")),
    ]


__all__ = [
    "narrateBusinessStability",
    "narrateCapitalStructure",
    "narrateCashFlow",
    "narrateDisclosureRisk",
    "narrateLiquidity",
    "narrateReliability",
    "narrateRepayment",
]


# ── narrateRepayment + narrateCapitalStructure → _narrativeAxesA.py 분리 ──

from dartlab.credit.features._narrativeAxesA import (  # noqa: E402, F401
    narrateCapitalStructure,
    narrateRepayment,
)
