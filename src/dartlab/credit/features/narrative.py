"""7축 신용분석 서사 생성 엔진.

지표값 + 업종 기준표 위치를 조합하여 신평사 수준의 해석 문장을 생성한다.
숫자 나열이 아니라, "왜 이 등급인가"를 읽을 수 있는 문장으로 설명한다.
"""

from __future__ import annotations

from dartlab.core.formatting import formatDecimal, formatKr
from dartlab.credit.features._narrativeAxes import (
    buildNarratives,
    narrateBusinessStability,
    narrateCapitalStructure,
    narrateCashFlow,
    narrateDisclosureRisk,
    narrateLiquidity,
    narrateReliability,
    narrateRepayment,
)
from dartlab.credit.features._narrativeBuilders import (
    _buildCausalChainParts,
    _buildCreditIntroSentence,
    _buildStrengthWeaknessSentences,
    _trendDebtEbitdaLine,
    _trendDebtRatioLine,
    _trendMultiYearStoryLine,
    _trendOpIncomeLine,
    _trendRevenueLine,
)
from dartlab.credit.features._narrativeSeverity import _severity
from dartlab.credit.features._narrativeTypes import AxisNarrative

__all_helpers__ = [
    "_buildCausalChainParts",
    "_buildCreditIntroSentence",
    "_buildStrengthWeaknessSentences",
    "_trendDebtEbitdaLine",
    "_trendDebtRatioLine",
    "_trendMultiYearStoryLine",
    "_trendOpIncomeLine",
    "_trendRevenueLine",
    "narrateBusinessStability",
    "narrateCapitalStructure",
    "narrateCashFlow",
    "narrateDisclosureRisk",
    "narrateLiquidity",
    "narrateReliability",
    "narrateRepayment",
]


def _fmt(v, suffix="", decimals=1) -> str:
    """고정 소수 + suffix (None → N/A)."""
    return formatDecimal(v, decimals=decimals, suffix=suffix, nullStr="N/A")


def _fmtTril(v) -> str:
    """금액을 조/억 단위로 변환 (원 접미사 포함)."""
    return formatKr(v, withWon=True, nullStr="N/A")


# ═══════════════════════════════════════════════════════════
# 축별 서사 생성
# ═══════════════════════════════════════════════════════════


def narrateProfile(profile: dict | None, segments: dict | None, rank: dict | None) -> str:
    """기업 개요 서사: 이 회사가 뭘 하는 회사인가.

    Capabilities:
        섹터 + 주요사업 + 부문 구성 (상위 3, share > 5%) + 업종 내 매출
        순위/사이즈 클래스 (대형/중형/소형) 를 " | " 구분 1 줄로 합성.
        credit 5-7 신용평가 섹션 도입부 표준 서사.

    Args:
        profile: 기업 프로필 dict (sector, products).
        segments: 부문 dict (segments list, totalRevenue).
        rank: 순위 dict (revenueRankInSector, revenueSectorTotal, sizeClass).

    Returns:
        str: " | " 구분 한 줄 서사. 데이터 부재 시 빈 문자열.

    Raises:
        없음.

    Example:
        >>> narrateProfile(profile={"sector": "반도체"}, segments={...},
        ...                rank={"sizeClass": "large", ...})
        '반도체 | 부문 구성: 메모리 65%(영업이익률 25%), 시스템LSI 30% | 업종 내 매출 1/15위 (대형)'

    Guide:
        - share > 5% 부문만 표기 (sub-segment noise 제거).
        - margin 결측 시 부문 share 만 표기.
        - rank 없으면 sector + segments 만.

    SeeAlso:
        - ``narrateTrend``: 전기 대비 추세
        - ``buildNarratives``: 7 축 서사 합성 (본 함수 포함)

    When:
        credit 신용평가 보고서 도입 1 줄 서사가 필요할 때.

    How:
        profile sector → segments share 계산 → rank size class → " | " join.

    Requires:
        ``profile`` (sector/products), ``segments`` (totalRevenue),
        ``rank`` (size) 중 하나 이상.

    AIContext:
        본 함수 결과는 그대로 신용평가 도입부 1 줄로 사용. 변형 금지.

    LLM Specifications:
        AntiPatterns:
            - margin/share 값 변형 인용. 원문 그대로.
            - 부문 4 개 이상 나열. 본 함수가 상위 3 만 반환.
        OutputSchema:
            ``str``.
        Prerequisites:
            profile + segments + rank 중 하나.
        Freshness:
            연간 (사업보고서 + 매출 ranking).
        Dataflow:
            profile sector → segments share 계산 → rank size class →
            " | " join.
        TargetMarkets: KR (DART), US (EDGAR Segment Reporting).
    """
    parts = []

    # 업종 + 주요제품
    if profile:
        sector = profile.get("sector", "")
        products = profile.get("products", "")
        if sector:
            parts.append(sector.replace("섹터: ", ""))
        if products:
            parts.append(products.replace("주요제품: ", "주요 사업: "))

    # 부문 구성
    if segments and segments.get("segments"):
        segs = segments["segments"]
        total = segments.get("totalRevenue", 0)
        if total > 0 and segs:
            segParts = []
            for s in segs[:3]:
                name = s.get("name", "")
                rev = s.get("revenue", 0)
                share = rev / total * 100 if total > 0 else 0
                if share > 5:
                    margin = s.get("opMargin")
                    marginStr = f"(영업이익률 {margin:.1f}%)" if margin is not None else ""
                    segParts.append(f"{name} {share:.0f}%{marginStr}")
            if segParts:
                parts.append("부문 구성: " + ", ".join(segParts))

    # 업종 내 순위
    if rank:
        sectorRank = rank.get("revenueRankInSector")
        sectorTotal = rank.get("revenueSectorTotal")
        sizeClass = rank.get("sizeClass", "")
        if sectorRank and sectorTotal:
            sizeKr = {"large": "대형", "mid": "중형", "small": "소형"}.get(sizeClass, "")
            parts.append(f"업종 내 매출 {sectorRank}/{sectorTotal}위 ({sizeKr})")

    return " | ".join(parts) if parts else ""


def narrateTrend(history: list[dict]) -> str:
    """전기 대비 추세 해석 orchestrator: 핵심 지표 개선/악화 (Q3.1f split).

    Capabilities:
        metricsHistory 시계열에서 최신 vs 전기를 비교해 매출/영업이익/Debt-EBITDA/부채비율
        line 단위 추세 해석 4 종 + 다년 stroyLine 결합. 변화 없으면 "변동 제한적" 폴백.

    Args:
        history: ``evaluateCompany(detail=True).metricsHistory`` (최신 0 → 과거 순).

    Returns:
        str: 추세 해석 1 줄 (마침표 포함) 또는 빈 문자열.

    Raises:
        없음. history 2 개 미만이면 빈 문자열.

    Example:
        >>> narrateTrend(metricsHistory)
        '매출 12% 증가했다. 영업이익 23% 개선. ...'

    Guide:
        본 함수가 4 개 ``_trend*Line`` 서브 함수를 orchestrate. 빈 라인은 자동 skip.

    When:
        신용평가 보고서의 "전기 대비" 한 줄. credit detail 결과 narrative 에 자동 첨부.

    How:
        history[0] vs history[1] 비교 → 4 라인 산출 → 다년 storyLine 첨부 → " " join + 마침표.

    Requires:
        - metricsHistory list (>= 2)

    See Also:
        - ``dartlab.credit.features.narrative.narrateProfile`` : 도입 1 줄
        - ``dartlab.credit.features.narrative.buildOverallNarrative`` : 본 함수 사용자

    AIContext:
        AI 답변 "전기 대비" 1 줄 직접 인용 가능. 빈 문자열일 땐 "변동 제한적" 단서 명시.
    """
    if len(history) < 2:
        return ""

    h0, h1 = history[0], history[1]
    parts: list[str] = []
    for line in (
        _trendRevenueLine(h0, h1),
        _trendOpIncomeLine(h0, h1),
        _trendDebtEbitdaLine(h0, h1),
        _trendDebtRatioLine(h0, h1),
    ):
        if line:
            parts.append(line)

    if not parts:
        return "전기 대비 핵심 지표 변동이 제한적이다."

    storyLine = _trendMultiYearStoryLine(history)
    if storyLine:
        parts.append(storyLine)

    return " ".join(parts) + "."


def narrateBorrowings(borrowingsDetail: list[dict] | None, latest: dict | None) -> str:
    """차입금 구성 분석: 만기/종류별 + 현금 대비.

    Capabilities:
        총차입금 + 단기/장기 비중 (금액 명시) + 현금/차입금 비율 기반 차환
        위험 평가 자연어 합성. 현금 ≥ 차입금 → 차환 여력 우수, 현금 < 차입금
        → 외부 조달 필요. _fmtTril 헬퍼로 조 단위 표기.

    Args:
        borrowingsDetail: 차입금 상세 (현재 미사용, 향후 만기별 분해 예정).
        latest: 최신 BS row (totalBorrowing, cash, netDebt,
            shortTermDebtRatio).

    Returns:
        str: 차입금 구조 + 차환 위험 평가 1~3 줄.

    Raises:
        없음.

    Example:
        >>> narrateBorrowings(None, {"totalBorrowing": 1e13, "cash": 5e12,
        ...                         "shortTermDebtRatio": 30})
        '총차입금 10.0 조. 단기 30%(3.0 조), 장기 70%(7.0 조). 현금(5.0 조)이 총차입금의 50%로 차환 시 외부 조달이 필요할 수 있다.'

    Guide:
        - 현금/차입 > 2 = 매우 낮은 차환 위험 (순현금 회사).
        - 1 < 현금/차입 < 2 = 차환 여력 보유.
        - 현금/차입 < 1 = 외부 조달 의존 (시장 환경 따라 위험).
        - 단기 비중 > 50% + 현금/차입 < 1 = 강한 차환 경고.

    SeeAlso:
        - ``narrateTrend``: 전기 대비 추세
        - ``calcDebtMaturity``: 만기 구조 (numerical)
        - ``calcLeverageTrend``: 부채 시계열

    When:
        신용평가 본문의 차입금 구조 + 차환 위험 1~3 줄.

    How:
        latest.totalBorrowing → 단기/장기 비중 → 현금/차입 비율 → 차환 위험 라벨 합성.

    Requires:
        latest dict (totalBorrowing 필수 + cash/netDebt + shortTermDebtRatio).

    AIContext:
        본 함수 결과 그대로 신용평가 본문에 삽입. 조 단위 표기 통일성 유지.

    LLM Specifications:
        AntiPatterns:
            - 차입금 0 회사에 본 함수 호출. 자동 "불필요" 메시지.
            - 단기 비중 단독 인용. 현금/차입 함께.
        OutputSchema:
            ``str``.
        Prerequisites:
            latest dict (BS).
        Freshness:
            분기.
        Dataflow:
            totalBorrowing → 단기/장기 비중 → 현금 대비 → 차환 위험 라벨.
        TargetMarkets: KR (DART), US (EDGAR Short/Long-Term Debt).
    """
    if latest is None:
        return ""

    totalBorrowing = latest.get("totalBorrowing")
    cashVal = latest.get("cash") if "cash" in (latest or {}) else None
    # cash가 latest에 없으면 history에서 추출 시도
    if cashVal is None:
        # netDebt = totalBorrowing - cash → cash = totalBorrowing - netDebt
        netDebt = latest.get("netDebt")
        if totalBorrowing and netDebt is not None:
            cashVal = totalBorrowing - netDebt

    if not totalBorrowing or totalBorrowing <= 0:
        return "차입금이 없거나 극소하여 부채 구성 분석이 불필요하다."

    parts = []
    parts.append(f"총차입금 {_fmtTril(totalBorrowing)}.")

    # 단기/장기 비중
    stRatio = latest.get("shortTermDebtRatio")
    if stRatio is not None:
        ltRatio = 100 - stRatio
        stAmt = totalBorrowing * stRatio / 100
        ltAmt = totalBorrowing * ltRatio / 100
        parts.append(f"단기 {stRatio:.0f}%({_fmtTril(stAmt)}), 장기 {ltRatio:.0f}%({_fmtTril(ltAmt)}).")

    # 현금 대비
    if cashVal and cashVal > 0:
        ratio = cashVal / totalBorrowing
        if ratio > 2:
            parts.append(f"현금 보유({_fmtTril(cashVal)})가 총차입금의 {ratio:.1f}배로 차환 위험이 매우 낮다.")
        elif ratio > 1:
            parts.append(f"현금({_fmtTril(cashVal)})이 총차입금을 상회하여 차환 여력이 있다.")
        else:
            parts.append(f"현금({_fmtTril(cashVal)})이 총차입금의 {ratio:.0%}로 차환 시 외부 조달이 필요할 수 있다.")

    return " ".join(parts)


def narrateCausalChain(latest: dict, result: dict) -> str:
    """6막 인과 연결: dartlab 핵심 사상을 credit에 적용.

    Capabilities:
        매출 → 이익 → 현금 → 안정성 → 등급 인과 체인을 한 줄로 합성. 지주사 (holding=True) /
        영업적자 등 특수 케이스 별도 분기. dartlab "앞이 뒤의 원인" 사상의 credit 본문 적용.

    매출 → 이익 → 현금 → 안정성 → 등급의 인과 체인.
    앞이 뒤의 원인이다.

    지주사/영업적자 등 특수 케이스를 별도 처리한다.

    Args:
        latest: 최신 metricsHistory row.
        result: ``evaluateCompany`` 결과 (grade, holding 등).

    Returns:
        str: 인과 요약 1 줄.

    Raises:
        없음.

    Example:
        >>> narrateCausalChain(metricsHistory[0], creditResult)
        '인과 요약: 매출 300조원 → 영업이익 60조원 (20%) → OCF 80조원 → 순현금 → dCR-AA+.'

    Guide:
        지주사는 자체 매출보다 자회사 배당 OCF 가 핵심. 별도 분기 처리.

    When:
        보고서의 한 줄 인과 요약. 보고서 도입/결론에 모두 적용 가능.

    How:
        result.holding 분기 → 지주사: 매출+배당+순현금 / 일반: 매출 → 이익 → 현금 → 안정성 →
        등급 합성.

    Requires:
        - latest dict + result dict (``evaluateCompany`` 산출)

    See Also:
        - ``dartlab.credit.features.narrative.buildOverallNarrative`` : 본 함수 사용자

    AIContext:
        AI 답변에 한 줄 인과 요약 직접 인용 가능. holding=True 회사는 별도 분기 결과 사용.
    """
    parts = []
    grade = result.get("grade", "?")
    isHolding = result.get("holding", False)

    rev = latest.get("revenue")
    oi = latest.get("operatingIncome")
    ebitda = latest.get("ebitda")
    ocf = latest.get("ocf")
    netDebt = latest.get("netDebt")
    debtRatio = latest.get("debtRatio")

    # 지주사 특수 경로: 매출이 작고 OCF가 배당/지분법 중심
    if isHolding and rev and ocf and ocf > rev * 0.5:
        parts.append(f"지주사로서 자체 매출 {_fmtTril(rev)}")
        if ocf > 0:
            parts.append(f"자회사 배당 등으로 OCF {_fmtTril(ocf)} 확보")
        if netDebt is not None and netDebt <= 0:
            parts.append("순현금 포지션으로 재무 안정성이 높다.")
        elif debtRatio is not None:
            parts.append(f"부채비율 {debtRatio:.0f}%.")
        if parts:
            chain = ", ".join(parts)
            return f"인과 요약: {chain} 종합 {grade}."
        return ""

    # 일반 기업 경로
    # 1막→2막: 매출 → 이익
    if rev and rev > 0:
        parts.append(f"매출 {_fmtTril(rev)}")
        if oi is not None:
            margin = oi / rev * 100
            if oi < 0:
                parts.append(f"영업적자(이익률 {margin:.0f}%)로 본업 수익성이 부진하나")
            elif margin > 15:
                parts.append(f"영업이익률 {margin:.0f}%로 수익성이 높아")
            elif margin > 5:
                parts.append(f"영업이익률 {margin:.0f}%로")
            else:
                parts.append(f"영업이익률 {margin:.0f}%에 불과하여")

    # 2막→3막: 이익 → 현금
    if ocf is not None:
        if ebitda is not None and ebitda > 0 and ocf > 0:
            if ocf > ebitda:
                parts.append(f"EBITDA {_fmtTril(ebitda)} 이상의 현금(OCF {_fmtTril(ocf)})을 창출하고")
            else:
                parts.append(f"OCF {_fmtTril(ocf)}를 창출하며")
        elif ocf > 0:
            parts.append(f"OCF {_fmtTril(ocf)}를 확보하고")
        else:
            parts.append("영업에서 현금이 유출되어")

    # 3막→4막: 현금 → 안정성
    if netDebt is not None:
        if netDebt <= 0:
            parts.append("순현금 포지션을 유지한다.")
        elif debtRatio is not None and debtRatio < 100:
            parts.append(f"부채비율 {debtRatio:.0f}%로 안정적이다.")
        elif debtRatio is not None:
            parts.append(f"부채비율 {debtRatio:.0f}%로 레버리지 부담이 있다.")

    # 결론
    if parts:
        chain = " → ".join(parts[:2]) + ", " + " → ".join(parts[2:]) if len(parts) > 2 else " → ".join(parts)
        return f"인과 요약: {chain} 종합 {grade}."

    return ""


def buildOverallNarrative(
    result: dict,
    narratives: list[AxisNarrative],
    *,
    captive: bool = False,
    holding: bool = False,
    separateMetrics: dict | None = None,
) -> str:
    """등급 근거 종합 서사: 인과 체인 통합.

    Capabilities:
        7 축 narrative + 인과 체인 + 강점/약점 + captive/holding 구조 단서를 합성한 등급 근거
        종합 문단 1 단락 반환. credit 보고서 결론부 그대로 사용 가능.

    각 축별 서사(AxisNarrative)를 종합하여 매출→이익→현금→안정성→등급의
    인과 체인이 한 문단에 드러나는 종합 서사를 생성한다.

    Parameters
    ----------
    result : dict
        신용분석 결과. 주요 키: ``grade`` (str), ``score`` (점),
        ``metricsHistory`` (list[dict]).
    narratives : list[AxisNarrative]
        축별 서사 리스트 (narrateRepayment, narrateCapitalStructure 등의 반환값).
    captive : bool
        캡티브 금융 복합기업 여부. True이면 금융자회사 관련
        구조적 참고 문구를 추가한다.
    holding : bool
        지주사 여부. True이면 지분법손익 비중이 큰 구조적 특성
        관련 문구를 추가한다.
    separateMetrics : dict | None
        별도 재무제표 기반 지표.

    Returns
    -------
    str
        등급 근거 종합 서사 문단. 인과 체인(매출→이익→현금→안정성)을
        하나의 흐름으로 연결한 문장이며, 강점·약점·구조적 참고가 포함된다.

    Raises:
        없음. narratives 비면 grade 인용만 가능.

    Example:
        >>> from dartlab.credit.features.narrative import buildOverallNarrative
        >>> text = buildOverallNarrative(creditResult, narratives)

    Guide:
        UI / Story 6 막 결론, 보고서 결론부에 단일 문단으로 그대로 첨부 가능.

    When:
        보고서 / 답변의 등급 근거 결론 문단이 필요할 때.

    How:
        result.grade/score + narratives strong/weak 분류 → 인과 chain → 도입 sentence + 강약점
        sentences + captive/holding 단서 → " " join.

    Requires:
        - ``evaluateCompany(detail=True)`` 산출 result + narratives 리스트

    See Also:
        - ``dartlab.credit.features._narrativeAxes.buildNarratives`` : narratives 산출
        - ``dartlab.credit.features.narrative.narrateCausalChain`` : 인과 체인

    AIContext:
        AI 답변의 신용평가 결론 한 문단 그대로 인용. 답변 길이 조정 시 strength/weakness 라인만
        발췌도 가능.
    """
    grade = result.get("grade", "?")
    score = result.get("score", 0)

    strengths = [n for n in narratives if n.severity == "strong"]
    weaknesses = [n for n in narratives if n.severity in ("weak", "critical")]

    parts: list[str] = []
    chainParts = _buildCausalChainParts(result)
    parts.append(_buildCreditIntroSentence(grade, score, chainParts))
    parts.extend(_buildStrengthWeaknessSentences(strengths, weaknesses))
    if result.get("captiveFinance"):
        parts.append("캡티브 금융 복합기업으로 연결 재무제표의 구조적 왜곡이 존재한다.")
    if result.get("holding"):
        parts.append("지주사 구조로 지분법손익이 실적에 영향을 미친다.")
    return " ".join(parts)
