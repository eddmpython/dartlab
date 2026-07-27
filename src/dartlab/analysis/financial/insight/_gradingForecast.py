"""analysis/financial/insight/grading 예측/공시 그룹 분리.

grading.py 가 1094 줄 god module 이라 예측/불확실성/핵심이익/공시 4 함수 분리.
identity 보존을 위해 grading.py 가 본 모듈에서 re-export 한다.

함수:
- analyzePredictability — 매출 변동성 → 예측 가능성
- analyzeUncertainty — 동종업종 분산 → 불확실성
- analyzeCoreEarnings — 일회성 제거 후 핵심 이익 품질
- disclosureGapFlags — 공시 누락/지연 플래그
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dartlab.analysis.financial.insight._gradingScales import (
    _predictabilityGrade,
    _scoreToGrade,
    _uncertaintyGrade,
)
from dartlab.analysis.financial.insight.detector import detectIncompleteYear
from dartlab.analysis.financial.insight.types import Flag, InsightResult
from dartlab.core.utils.extract import getAnnualValues, getLatest

if TYPE_CHECKING:
    from dartlab.company import Company


def analyzePredictability(
    aSeries: dict,
    aYears: list[str],
    isFinancial: bool = False,
) -> InsightResult:
    """사업 예측가능성 분석 (0~10점 → A~F).

    Capabilities:
        - 매출/영업이익 CV + 연속성장 횟수 + 흑자 비율 4 룰 → 0~10 점 합산 → grade.

    Parameters
    ----------
    aSeries : dict
        연간 재무 시계열.
    aYears : list[str]
        연간 기간 라벨 리스트.
    isFinancial : bool
        금융업 여부. True이면 매출 대신 영업이익 사용.

    Returns
    -------
    InsightResult
        grade : str — 'A'~'F' 등급
        summary : str — 예측가능성 점수/10 + 수준
        details : list[str] — 매출 CV, 영업이익 CV, 연속성장, 흑자 비율 등 (점)

    Guide:
        Buffett ‘moat’ 사상의 정량 근사. 변동성 낮고 매년 성장하는 사업 우대.

    When:
        analyzeFinancial 의 'predictability' 키 산출 단계.

    How:
        statistics.stdev/mean 으로 CV 산출 + reversed loop 로 streak 카운트.

    Requires:
        aSeries IS (sales/operating_profit/net_profit) 연간 ≥ 3 년.

    Raises:
        없음 (statistics 내부 ValueError 가능성은 데이터 부족 분기로 차단).

    Example:
        >>> analyzePredictability(aSeries, aYears)
        InsightResult(grade='A', summary='예측가능성 8.2/10 — 매우 높음')

    See Also:
        - analyzeUncertainty: 대칭 (Morningstar 불확실성)
        - analyzeCoreEarnings: 이익 품질

    AIContext:
        ‘예측 가능 사업’ 컨텍스트는 가치주/장기보유 답변 톤으로 인용.
    """
    import statistics

    revVals = getAnnualValues(aSeries, "IS", "sales")
    opVals = getAnnualValues(aSeries, "IS", "operating_profit")
    niVals = getAnnualValues(aSeries, "IS", "net_profit")

    if isFinancial:
        revVals = opVals

    validRev = [v for v in revVals if v is not None]
    validOp = [v for v in opVals if v is not None]
    validNi = [v for v in niVals if v is not None]

    if len(validRev) < 3:
        return InsightResult("N", "예측가능성 데이터 부족")

    details: list[str] = []
    score = 0.0

    # 매출 CV (낮을수록 예측 가능)
    revMean = statistics.mean(validRev)
    revCv = statistics.stdev(validRev) / abs(revMean) if revMean != 0 else 1.0
    revScore = max(0, 2.5 - revCv * 2.5)
    score += revScore
    details.append(f"매출 CV {revCv:.2f} ({revScore:.1f}/2.5)")

    # 영업이익 CV
    if len(validOp) >= 3:
        opMean = statistics.mean(validOp)
        opCv = statistics.stdev(validOp) / abs(opMean) if opMean != 0 else 1.0
        opScore = max(0, 2.5 - opCv * 2.5)
        score += opScore
        details.append(f"영업이익 CV {opCv:.2f} ({opScore:.1f}/2.5)")

    # 연속 성장 (매출 YoY > 0 횟수)
    growthCount = sum(1 for i in range(1, len(validRev)) if validRev[i] > validRev[i - 1])
    maxGrowth = max(1, len(validRev) - 1)
    growthScore = (growthCount / maxGrowth) * 2.5
    score += growthScore
    details.append(f"연속성장 {growthCount}/{maxGrowth}년 ({growthScore:.1f}/2.5)")

    # 무적자 (순이익 > 0 비율)
    if len(validNi) >= 3:
        profitCount = sum(1 for v in validNi if v > 0)
        profitScore = (profitCount / len(validNi)) * 2.5
        score += profitScore
        details.append(f"흑자 {profitCount}/{len(validNi)}년 ({profitScore:.1f}/2.5)")

    score = min(10, score)
    grade = _predictabilityGrade(score)
    summary = f"예측가능성 {score:.1f}/10 — " + (
        "매우 높음" if score >= 7 else "높음" if score >= 5 else "보통" if score >= 3 else "낮음"
    )
    return InsightResult(grade, summary, details)


def analyzeUncertainty(
    aSeries: dict,
    aYears: list[str],
    isFinancial: bool = False,
) -> InsightResult:
    """불확실성 등급 분석 (Morningstar 방식 5단계).

    Capabilities:
        - 매출 CV + DOL + D/E + 영업 CV 4 축 → 100 점 환산 → Low~Extreme 등급 +
          Fair Value 밴드 (±15~55%).

    Parameters
    ----------
    aSeries : dict
        연간 재무 시계열.
    aYears : list[str]
        연간 기간 라벨 리스트.
    isFinancial : bool
        금융업 여부. True이면 매출 대신 영업이익 사용.

    Returns
    -------
    InsightResult
        grade : str — 'A'~'F' 등급 (낮은 불확실성 = 좋은 등급)
        summary : str — 불확실성 등급 + Fair Value 밴드
        details : list[str] — 매출CV, DOL, D/E, 영업CV, 종합점수/100

    Guide:
        Morningstar 5 단계 (Low/Medium/High/Very High/Extreme) Fair Value 밴드 직접 매핑.

    When:
        analyzeFinancial 의 'uncertainty' 키. predictability 와 쌍으로 호출.

    How:
        4 축 별 점수 (≤25 점) → totalScore → 임계 분기 → grade + 밴드.

    Requires:
        aSeries IS (sales, operating_profit) 연간 ≥ 5 년 + BS (TL/Equity).

    Raises:
        없음.

    Example:
        >>> analyzeUncertainty(aSeries, aYears)
        InsightResult(grade='B', summary='불확실성 Medium — Fair Value 밴드 ±25%')

    See Also:
        - analyzePredictability: 대칭 (변동 작음 가산)
        - quant.calcFairValueBand: 정량 밴드 입력

    AIContext:
        Fair Value 밴드 폭은 valuation 답변에서 ‘적정주가 ±N%’ 표현으로 인용.
    """
    import statistics

    revVals = getAnnualValues(aSeries, "IS", "sales")
    opVals = getAnnualValues(aSeries, "IS", "operating_profit")

    if isFinancial:
        revVals = opVals

    validRev = [v for v in revVals if v is not None]
    validOp = [v for v in opVals if v is not None]

    if len(validRev) < 5 or len(validOp) < 5:
        return InsightResult("N", "불확실성 데이터 부족")

    details: list[str] = []

    # 매출 CV
    revMean = statistics.mean(validRev)
    revCv = statistics.stdev(validRev) / abs(revMean) if revMean != 0 else 1.0

    # DOL (영업레버리지)
    dolList = []
    minLen = min(len(validRev), len(validOp))
    for i in range(1, minLen):
        if validRev[i - 1] != 0 and validOp[i - 1] != 0:
            sChg = (validRev[i] - validRev[i - 1]) / abs(validRev[i - 1])
            oChg = (validOp[i] - validOp[i - 1]) / abs(validOp[i - 1])
            if abs(sChg) > 0.01:
                dolList.append(abs(oChg / sChg))
    dol = statistics.median(dolList) if dolList else 2.0

    # D/E
    tl = getLatest(aSeries, "BS", "total_liabilities")
    eq = getLatest(aSeries, "BS", "total_stockholders_equity")
    deRatio = tl / eq if tl is not None and eq and eq > 0 else 0.0

    # 영업이익 CV
    opMean = statistics.mean(validOp)
    opCv = statistics.stdev(validOp) / abs(opMean) if opMean != 0 else 1.0

    # 종합 점수 (각 최대 25점)
    revScore = min(25, revCv / 0.5 * 25)
    dolScore = min(25, (dol - 1) / 9 * 25)
    deScore = min(25, deRatio / 3 * 25)
    opScore = min(25, opCv / 1.0 * 25)
    totalScore = revScore + dolScore + deScore + opScore

    if totalScore < 20:
        rating, margin = "Low", "±15%"
    elif totalScore < 35:
        rating, margin = "Medium", "±25%"
    elif totalScore < 50:
        rating, margin = "High", "±35%"
    elif totalScore < 70:
        rating, margin = "Very High", "±45%"
    else:
        rating, margin = "Extreme", "±55%"

    details.append(f"매출CV {revCv:.2f}, DOL {dol:.1f}, D/E {deRatio:.1f}, 영업CV {opCv:.2f}")
    details.append(f"종합 {totalScore:.1f}/100 → {rating} (Fair Value 밴드 {margin})")

    grade = _uncertaintyGrade(rating)
    summary = f"불확실성 {rating} — Fair Value 밴드 {margin}"
    return InsightResult(grade, summary, details)


def analyzeCoreEarnings(
    aSeries: dict,
    aYears: list[str],
    isFinancial: bool = False,
) -> InsightResult:
    """핵심이익 품질 분석 (비경상 항목 분리).

    Capabilities:
        - 실효세율 → Core Earnings (영업이익×(1-세율)) 산출 → Core CV vs Reported CV
          비교 + 괴리 분석.

    Parameters
    ----------
    aSeries : dict
        연간 재무 시계열.
    aYears : list[str]
        연간 기간 라벨 리스트.
    isFinancial : bool
        금융업 여부.

    Returns
    -------
    InsightResult
        grade : str — 'A'~'F' 등급
        summary : str — 이익 품질 요약
        details : list[str] — Core CV vs Reported CV, 안정성, 괴리 등

    Guide:
        영업외/일회성 손익이 보고이익을 왜곡하는지 검증. Reported = Core 이면 클린.

    When:
        analyzeFinancial 의 'coreEarnings' 키. uncertainty/predictability 와 동행 호출.

    How:
        세금/PBT 평균 → 실효세율 → Core 시계열 → CV 비교 + 최신 괴리 계산.

    Requires:
        aSeries IS (operating_profit/net_profit/income_taxes/profit_before_tax) ≥ 3 년.

    Raises:
        없음.

    Example:
        >>> analyzeCoreEarnings(aSeries, aYears)
        InsightResult(grade='A', summary='이익 품질 우수', ...)

    See Also:
        - analyzePredictability: 매출/영업이익 변동성
        - calcEarningsMomentum: Sloan accrual 분해

    AIContext:
        Reported >> Core 괴리는 ‘일회성 이익 비중 큼’ 컨텍스트로 인용 — 추세 판단 시 Core 우선.
    """
    import statistics

    opVals = getAnnualValues(aSeries, "IS", "operating_profit")
    niVals = getAnnualValues(aSeries, "IS", "net_profit")
    taxVals = getAnnualValues(aSeries, "IS", "income_taxes")
    pbtVals = getAnnualValues(aSeries, "IS", "profit_before_tax")

    validOp = [v for v in opVals if v is not None]
    validNi = [v for v in niVals if v is not None]
    validTax = [v for v in taxVals if v is not None]
    validPbt = [v for v in pbtVals if v is not None]

    if len(validOp) < 3 or len(validNi) < 3:
        return InsightResult("N", "핵심이익 데이터 부족")

    details: list[str] = []
    score = 0

    # 실효세율 추정
    if validTax and validPbt:
        taxRates = []
        for t, p in zip(validTax, validPbt):
            if p > 0 and t is not None:
                taxRates.append(t / p)
        effectiveTax = statistics.mean(taxRates) if taxRates else 0.22
    else:
        effectiveTax = 0.22

    # Core Earnings = 영업이익 × (1-세율)
    coreVals = [v * (1 - effectiveTax) for v in validOp]

    # CV 비교: Core vs Reported
    coreMean = statistics.mean(coreVals) if coreVals else 0
    reportedMean = statistics.mean(validNi) if validNi else 0
    coreCv = statistics.stdev(coreVals) / abs(coreMean) if coreMean != 0 and len(coreVals) >= 2 else 999
    reportedCv = statistics.stdev(validNi) / abs(reportedMean) if reportedMean != 0 and len(validNi) >= 2 else 999

    details.append(f"Core CV {coreCv:.2f} vs Reported CV {reportedCv:.2f}")

    # CV 개선 여부
    if coreCv < reportedCv:
        improvement = (1 - coreCv / reportedCv) * 100 if reportedCv > 0 else 0
        details.append(f"핵심이익이 변동성 {improvement:.0f}% 개선")
        score += 2
    else:
        details.append("비경상 항목 영향 미미")

    # 핵심이익 안정성 (Core CV 절대 수준)
    if coreCv < 0.2:
        details.append("핵심이익 매우 안정")
        score += 3
    elif coreCv < 0.4:
        details.append("핵심이익 안정")
        score += 2
    elif coreCv < 0.7:
        details.append("핵심이익 보통")
        score += 1
    else:
        details.append("핵심이익 변동 큼")

    # 핵심이익 대비 보고이익 괴리 (최신연도)
    if coreVals and validNi:
        latestCore = coreVals[-1]
        latestReported = validNi[-1]
        if latestCore != 0:
            gap = (latestReported - latestCore) / abs(latestCore) * 100
            if abs(gap) > 30:
                details.append(f"보고이익 vs 핵심이익 괴리 {gap:+.0f}%")
                if gap < -30:
                    score -= 1  # 비경상 손실
            elif abs(gap) < 10:
                details.append("보고이익 ≈ 핵심이익")
                score += 1

    grade = _scoreToGrade(score, 6)
    summary = "이익 품질 " + ("우수" if score >= 5 else "양호" if score >= 3 else "보통" if score >= 1 else "주의")
    return InsightResult(grade, summary, details)


def disclosureGapFlags(
    company: "Company | None",
    healthGrade: str | None = None,
) -> list[Flag]:
    """공시 텍스트 변화 vs 재무 지표 불일치 탐지.

    Capabilities:
        - diff 기반 공시 서술 변화 + 재무 건전성 등급 교차 → 텍스트-숫자 불일치 Flag.

    diff 기반으로 리스크 서술 급증/감소를 감지하고, 재무 건전성 등급과 교차 비교하여
    '서술형 리스크 급증 vs 재무 안정' 또는 '재무 악화 vs 서술형 은폐' 불일치를 찾는다.

    Parameters
    ----------
    company : Company | None
        기업 객체. None이면 빈 리스트 반환.
    healthGrade : str | None
        재무건전성 등급 ('A'~'F'). 교차 비교에 사용.

    Returns
    -------
    list[Flag]
        level : str — 'warning'
        category : str — 'disclosure_gap'
        text : str — 불일치 설명

    Guide:
        텍스트 톤 변화가 숫자보다 선행할 수 있다는 가정. ‘은폐’ 가설 신호로 활용.

    When:
        analyzeFinancial 후반 — risk 보강 단계에서 호출.

    How:
        disclosureDelta._safeDiffResult 로 entries 추출 → riskTopics 매칭 → healthGrade 교차.

    Requires:
        company.fetchDisclosure 의 diff 결과 + healthGrade 사전 산출.

    Raises:
        없음.

    Example:
        >>> disclosureGapFlags(company, "A")
        [Flag('warning', 'disclosure_gap', '서술형 리스크 급증 vs 재무 안정')]

    See Also:
        - analyzeFinancial: 상위 호출자
        - disclosureDelta: diff 산출 유틸

    AIContext:
        ‘공시 톤 vs 재무 숫자 괴리’ 표현은 가설성 신호로 인용 — 단정 금지.
    """
    if company is None:
        return []

    from dartlab.analysis.financial.disclosureDelta import _safeDiffResult

    diffResult = _safeDiffResult(company)
    if diffResult is None or not diffResult.entries:
        return []

    # 리스크 관련 topic 식별
    riskTopics = {
        "riskManagement",
        "riskFactor",
        "goingConcern",
        "audit",
        "contingentLiability",
        "litigation",
        "internalControl",
    }
    riskChanges = [e for e in diffResult.entries if e.topic in riskTopics and e.status == "changed"]

    flags: list[Flag] = []

    if riskChanges and healthGrade in ("A", "B"):
        topics = ", ".join(sorted({e.topic for e in riskChanges}))
        flags.append(
            Flag(
                level="warning",
                category="disclosure_gap",
                text=f"리스크 서술 변화({topics}) vs 재무 안정({healthGrade}) — 불일치 확인 필요",
            )
        )

    if not riskChanges and healthGrade in ("D", "F"):
        flags.append(
            Flag(
                level="warning",
                category="disclosure_gap",
                text=f"재무 악화({healthGrade}) vs 리스크 서술 무변동 — 공시 충실도 점검 필요",
            )
        )

    return flags


__all__ = [
    "analyzeCoreEarnings",
    "analyzePredictability",
    "analyzeUncertainty",
    "disclosureGapFlags",
]
