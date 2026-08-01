"""신용등급 산출 메인 파이프라인.

Layer 1 (metrics.py) → Layer 2 (scorecard) → Layer 3 (등급 결정)
→ Layer 4 (보고서 생성) 순서로 실행.
"""

from __future__ import annotations

from dartlab.credit._engineConfig import _CONFIG, _WEIGHTS
from dartlab.credit._engineFinancial import _evaluateFinancial
from dartlab.credit._engineNotch import _NOTCH_RULES
from dartlab.credit._enginePostAdjust import (
    _CREDIT_SCORE_LEGEND,
    _applyPostAdjustments,
    _applyTimeSeriesSmoothing,
    _blendOFS,
    _explainDivergence,
    _normalizeMetricsForOutput,
)
from dartlab.credit._engineScoring import (
    _calcHistoricalScores,
    _scoreBusinessStability,
    _scoreCashFlow,
    _scoreDisclosureRisk,
    _scoreReliability,
)
from dartlab.credit.features.sectorThresholds import getSectorLabel, getThresholds
from dartlab.credit.scoring.creditScorecard import (
    axisScore,
    cashFlowGrade,
    creditOutlook,
    gradeCategory,
    isInvestmentGrade,
    scoreMetric,
    weightedScore,
)
from dartlab.credit.scoring.metrics import calcAllMetrics

# ═══════════════════════════════════════════════════════════
# 유틸리티
# ═══════════════════════════════════════════════════════════


def _getSectorInfo(company):
    """company.sector에서 (Sector, IndustryGroup) 추출."""
    try:
        si = getattr(company, "sector", None)
        if si is not None:
            return si.sector, si.industryGroup
    except (AttributeError, ImportError):
        pass
    return None, None


def _isFinancial(company) -> bool:
    try:
        sector, _ = _getSectorInfo(company)
        if sector is not None:
            from dartlab.frame.sector import Sector

            return sector == Sector.FINANCIALS
    except (AttributeError, ImportError):
        pass
    return False


def _isHolding(company) -> bool:
    """지주사 판별 - 이름 + 재무 구조 복합 기준.

    1. 이름에 "지주"/"홀딩스"/"Holdings" 포함
    2. 관계기업투자자산/총자산 > holding_investment_ratio (재무 구조 기반)
    """
    name = getattr(company, "corpName", "") or ""
    if any(k in name for k in _CONFIG["holding_keywords"]):
        return True
    try:
        bs = company.select("BS", ["종속기업,관계기업및공동기업투자", "관계기업등지분관련투자자산", "자산총계"])
        if bs is not None and len(bs) > 0:
            from dartlab.core.utils.helpers import toDictBySnakeId

            parsed = toDictBySnakeId(bs)
            if parsed:
                data, periods = parsed
                invest = data.get("종속기업,관계기업및공동기업투자", {}) or data.get("관계기업등지분관련투자자산", {})
                ta = data.get("자산총계", {})
                for p in sorted(periods, reverse=True):
                    inv_val = invest.get(p)
                    ta_val = ta.get(p)
                    if inv_val and ta_val and ta_val > 0:
                        ratio = inv_val / ta_val
                        if ratio > _CONFIG["holding_investment_ratio"]:
                            return True
                        break
    except (TypeError, ValueError, KeyError, AttributeError):
        pass
    return False


def _isCyclical(sector) -> bool:
    if sector is None:
        return False
    try:
        from dartlab.frame.sector import Sector

        return sector in (Sector.ENERGY, Sector.MATERIALS)
    except ImportError:
        return False


def _isCaptiveFinance(totalBorrowing: float, ebitda: float | None, isFinancial: bool) -> bool:
    """캡티브 금융 감지 - D/EBITDA > 15."""
    if isFinancial or ebitda is None or ebitda <= 0 or totalBorrowing <= 0:
        return False
    return totalBorrowing / ebitda > 15


def _isCaptiveByOFS(company, consolidatedBorrowing: float) -> bool:
    """별도재무제표 기반 캡티브 금융 감지.

    연결 차입금 / 별도 차입금 > 10이면 캡티브 금융자회사 존재.
    """
    if consolidatedBorrowing <= 0:
        return False
    try:
        from dartlab.credit.scoring.metrics import calcSeparateMetrics

        sep = calcSeparateMetrics(company)
        if sep is None:
            return False
        sepBorrowing = sep.get("totalBorrowing", 0) or 0
        if sepBorrowing <= 0:
            return consolidatedBorrowing > 1e12
        ratio = consolidatedBorrowing / sepBorrowing
        return ratio > 10
    except (ImportError, TypeError, ValueError, AttributeError):
        return False


# ═══════════════════════════════════════════════════════════
# 메인 진입점
# ═══════════════════════════════════════════════════════════


def evaluate(
    stockCode: str,
    *,
    detail: bool = False,
    basePeriod: str | None = None,
    overrides: dict | None = None,
) -> dict | None:
    """신용등급 산출 메인 진입점.

    Capabilities:
        stockCode 단일 입력으로 Company 객체 생성 후 ``evaluateCompany`` 위임. ``credit()``
        진입점이 stockCode 만으로 호출될 때 본 함수를 거친다.

    Args:
        stockCode: 6 자리 KR 종목코드 또는 EDGAR ticker.
        detail: ``True`` 면 7 축 상세 + 시계열 + narrative.
        basePeriod: 분석 기준 기간 (예 ``"2024"``). None 이면 최신.

    Returns:
        dict | None: ``evaluateCompany`` 결과 그대로.

    Raises:
        없음 - Company 인스턴스화 실패 시 None.

    Example:
        >>> from dartlab.credit.engine import evaluate
        >>> result = evaluate("005930")
        >>> result["grade"]
        'dCR-AA+'

    Guide:
        본 함수는 stockCode → Company 생성만 담당. 모든 로직은 ``evaluateCompany``.

    When:
        ``credit(stockCode)`` 가 본 함수 위임.

    How:
        ``dartlab.company.Company(stockCode)`` → ``evaluateCompany`` 위임.

    Requires:
        - L1 raw: DART/EDGAR 정기보고서 접근 가능

    See Also:
        - ``dartlab.credit.engine.evaluateCompany`` : 본 함수 위임 대상
        - ``dartlab.credit.credit`` : 사용자 진입점

    AIContext:
        AI 가 직접 호출하지 않는다 (``credit(stockCode)`` 권장).
    """
    from dartlab.company import Company

    company = Company(stockCode)
    return evaluateCompany(company, detail=detail, basePeriod=basePeriod, overrides=overrides)


def evaluateCompany(
    company,
    *,
    detail: bool = False,
    basePeriod: str | None = None,
    overrides: dict | None = None,
) -> dict | None:
    """Company → dCR 신용등급 (3-Track 분기 + CHS·Notch 보정).

    Capabilities:
        Company 의 업종/기업유형으로 Track A/B/C 분기 → 7 (또는 5) 축 가중평균
        → CHS PD 보정 → Notch 7 룰 (재무약화/사업위험/지배구조 등) → dCR 등급
        (AAA ~ D, 20 단계). credit engine 의 단일 진입점.

    Args:
        company: DartCompany 또는 EdgarCompany 인스턴스.
        detail: ``True`` 면 metricsHistory + businessStability + narratives
            포함 (보고서 생성용). ``False`` 면 grade + score 만.
        basePeriod: 분석 기준 기간 (예 ``"2024"``). ``None`` 이면 최신.

    Returns:
        dict | None: 다음 키 (BS/IS/CF 누락 시 ``None``):
            - ``grade`` (str): dCR 등급 (예 ``"dCR-AA+"``)
            - ``gradeRaw`` (str): 등급 코드
            - ``gradeDescription``/``gradeCategory`` (str)
            - ``investmentGrade`` (bool): 투자적격 여부
            - ``score`` (float): 위험 점수 (0~100, 0=최우량)
            - ``healthScore`` (float): 100 - score
            - ``currentScore`` (float): 시계열 안정화 전
            - ``pdEstimate`` (float): 부도확률 (%)
            - ``eCR`` (str|None): 현금흐름등급 (Track B 는 None)
            - ``outlook`` (str): 전망 ("안정적"/"긍정적"/"부정적")
            - ``sector``/``captiveFinance``/``holding`` (str/bool)
            - ``latestPeriod`` (str)
            - ``chsAdjustment``/``notchAdjustment`` (dict|None)
            - ``divergenceExplanation`` (list[str])
            - ``methodologyVersion`` (str)
            - ``axes`` (list[dict]): 비금융 7 축 점수 또는 금융 비채점 회계 프록시 진단
            - ``metricsHistory`` (detail=True): 기간별 시계열
            - ``narratives`` (detail=True): 서사 dict

    Raises:
        없음.

    Example:
        >>> from dartlab.credit.engine import evaluateCompany
        >>> r = evaluateCompany(Company("005930"))
        >>> r["grade"], r["outlook"]
        ('dCR-AA+', '안정적')

    Guide:
        3-Track 분류:
        - Track A (일반): 7 축 (repayment/leverage/liquidity/cashFlow/
          businessStability/reliability/disclosureRisk)
        - Track B (금융): 유형별 규제지표 calibration 전까지 accounting proxy
          ``diagnostic_only``. grade/PD/outlook 비발행
        - Track C (지주): 7 축 + 가중치 차별화 + 별도재무 블렌딩

    When:
        Company 객체 단위 신용 분석이 필요할 때. ``Company.credit`` / ``creditCompany`` 본 함수
        위임.

    How:
        ``_getSectorInfo`` / ``_isFinancial`` 분기. 비금융은 ``calcAllMetrics`` 축별 metric →
        가중평균 → CHS/Notch → 20 단계 grade. 금융은 공통기간 회계 프록시와 coverage gap만 반환.

    See Also:
        - ``credit`` (top-level): stockCode 진입점
        - ``calcAllMetrics``: 축별 metric 산출 (본 함수 호출)
        - ``computeChsProbability``: CHS PD 보정
        - ``_calcNotchAdjustment``: Notch 7 룰

    Requires:
        Company.finance (BS/IS/CF) + 종가 (CHS) + 업종 룩업.

    AIContext:
        ``grade`` + ``outlook`` 만 인용 금지 - divergenceExplanation 과 notch
        / CHS adjustment 도 함께 노출해 등급 변동 근거 투명화. invest
        decision 은 grade + score + 시계열 모두 검토.

    LLM Specifications:
        AntiPatterns:
            - Track B 금융사의 ``grade``/``pdEstimate``/``eCR`` None을 누락 오류로
              해석 금지. 유형별 규제지표 calibration 전 의도적 비발행이다.
            - basePeriod 미지정 시 최신이 partial quarter 인 경우 자동
              skip (R25-1) - currentScore 와 score 차이 발생 가능, 정상.
        OutputSchema:
            상기 22 키 dict. detail=True 시 metricsHistory + narratives 추가.
        Prerequisites:
            Company.finance + sectorThresholds 로드 + 종가 cache (CHS 입력).
        Freshness:
            finance = 최신 분기. CHS = 종가 cache 동기화.
        Dataflow:
            company → _getSectorInfo → Track 분기 → calcAllMetrics →
            가중평균 → calcCHS → notch 7 룰 → mapTo20Grade → dict.
        TargetMarkets: KR (DART) 만. US (EDGAR) 는 KR(WICS) calibration 미검증이라
            등급 미산출(None) - US calibration 은 Slice2 (_usDefaultThresholds).
    """
    # ⛔ 시장 가드 - 등급표·임계값은 KR(WICS 업종·한국 회계) calibration 전용.
    # US(EDGAR) 회사를 그대로 태우면 sectorThresholds 가 sector=None→_defaultThresholds(KR)
    # 를 US-GAAP 숫자에 먹여 non-None *가짜 등급* 을 낸다(확신 오정렬). _revenueSelect 의
    # 정직 None 과 대칭화 - 비-KR 시장은 등급 미산출(None). US calibration = Slice2.
    # KR 하위시장(KOSPI/KOSDAQ/KONEX)·미지정·비-str(mock)은 KR 로 통과 - US/JP 등 외화회계만 차단.
    _market = getattr(company, "market", "KR")
    if isinstance(_market, str) and _market.strip().upper() not in ("", "KR", "KOSPI", "KOSDAQ", "KONEX"):
        return None

    from dartlab.synth.overrides import validateOverrides

    requestedOverrides = validateOverrides(overrides, engine="credit")

    sector, industryGroup = _getSectorInfo(company)
    isFinancialCo = _isFinancial(company)

    if isFinancialCo:
        financialResult = _evaluateFinancial(
            company,
            detail=detail,
            basePeriod=basePeriod,
            sector=sector,
            industryGroup=industryGroup,
        )
        if financialResult is not None and requestedOverrides:
            financialResult["appliedOverrides"] = {}
            financialResult["ignoredOverrides"] = {
                key: "금융회사 Track B에는 일반기업 override calibration이 없습니다." for key in requestedOverrides
            }
        return financialResult

    metrics = calcAllMetrics(company, basePeriod=basePeriod)
    if metrics is None or not metrics.get("history"):
        return None

    _CORE_METRIC_KEYS = ("ebitda", "ocf", "netIncome", "interestExpense")
    history = metrics["history"]
    latest = history[0]
    if all(latest.get(k) is None for k in _CORE_METRIC_KEYS) and len(history) > 1:
        for row in history[1:]:
            if any(row.get(k) is not None for k in _CORE_METRIC_KEYS):
                latest = row
                break
    latest = dict(latest)
    appliedOverrides, ignoredOverrides, scenarioAdjustments = _applyCreditOverrides(latest, requestedOverrides)
    holding = _isHolding(company)
    captive = _isCaptiveFinance(latest.get("totalBorrowing") or 0, latest.get("ebitda"), isFinancialCo)
    if not captive and not isFinancialCo:
        captive = _isCaptiveByOFS(company, latest.get("totalBorrowing") or 0)
    cyclical = _isCyclical(sector)

    if captive:
        from dartlab.credit.features.sectorThresholds import _airlineThresholds

        thresholds = _airlineThresholds()
        sectorLabel = f"{getSectorLabel(sector)} (캡티브금융조정)"
    elif holding:
        from dartlab.credit.features.sectorThresholds import _holdingThresholds

        thresholds = _holdingThresholds()
        sectorLabel = f"{getSectorLabel(sector)} (지주사조정)"
    else:
        thresholds = getThresholds(sector, industryGroup)
        sectorLabel = getSectorLabel(sector)

    def _entry(name: str, value, threshold: dict) -> dict:
        return {
            "name": name,
            "value": value,
            "score": scoreMetric(value, threshold),
        }

    _focfVal = latest.get("focfToDebt")
    if latest.get("fcf") is not None and (latest.get("fcf") or 0) < 0:
        _focfEntry = {"name": "FOCF/Debt", "value": _focfVal, "score": None}
    else:
        _focfEntry = _entry("FOCF/Debt", _focfVal, thresholds["focf_to_debt"])

    axis1_scores = [
        _entry("FFO/총차입금", latest.get("ffoToDebt"), thresholds["ffo_to_debt"]),
        _entry("Debt/EBITDA", latest.get("debtToEbitda"), thresholds["debt_to_ebitda"]),
        _focfEntry,
        _entry("EBITDA/이자비용", latest.get("ebitdaInterestCoverage"), thresholds["ebitda_interest_coverage"]),
    ]
    axis1 = axisScore(axis1_scores)

    axis2_scores = [
        _entry("부채비율", latest.get("debtRatio"), thresholds["debt_ratio"]),
        _entry("차입금의존도", latest.get("borrowingDependency"), thresholds["borrowing_dependency"]),
        _entry("순차입금/EBITDA", latest.get("netDebtToEbitda"), thresholds["net_debt_to_ebitda"]),
    ]
    axis2 = axisScore(axis2_scores)

    _needsOFS = holding or captive
    sepMetrics = None
    if _needsOFS and axis1 is not None:
        from dartlab.credit.scoring.metrics import calcSeparateMetrics

        sepMetrics = calcSeparateMetrics(company)
        if sepMetrics is not None:
            sep_axis1_scores = [
                _entry("별도D/EBITDA", sepMetrics.get("separateDebtToEbitda"), thresholds["debt_to_ebitda"]),
            ]
            sep1 = axisScore(sep_axis1_scores)
            axis1 = _blendOFS(axis1, sep1)

            sep_axis2_scores = [
                _entry("별도부채비율", sepMetrics.get("separateDebtRatio"), thresholds["debt_ratio"]),
                _entry("별도차입금의존도", sepMetrics.get("separateBorrowingDep"), thresholds["borrowing_dependency"]),
            ]
            sep2 = axisScore(sep_axis2_scores)
            axis2 = _blendOFS(axis2, sep2)

    compThresh = _CONFIG["axis1_compress_threshold"]
    compRatio = _CONFIG["axis1_compress_ratio"]
    if (captive or holding or cyclical) and axis1 is not None and axis1 > compThresh:
        excess = axis1 - compThresh
        axis1 = round(compThresh + excess * compRatio, 2)

    axis3_scores = [
        _entry("유동비율", latest.get("currentRatio"), thresholds["current_ratio"]),
        _entry("현금비율", latest.get("cashRatio"), thresholds["cash_ratio"]),
        _entry("단기차입금비중", latest.get("shortTermDebtRatio"), thresholds["short_term_debt_ratio"]),
    ]
    axis3 = axisScore(axis3_scores)

    axis4_scores = _scoreCashFlow(latest, metrics)
    axis4 = axisScore(axis4_scores)

    if _needsOFS and sepMetrics is not None and axis4 is not None:
        sepOcfScore = scoreMetric(
            sepMetrics.get("separateOcfToSales"), thresholds.get("ocf_to_sales", thresholds.get("cash_ratio", {}))
        )
        sepOcfDebt = scoreMetric(sepMetrics.get("separateOcfToDebt"), thresholds.get("focf_to_debt", {}))
        sepCfScores = [(s, 1) for s in [sepOcfScore, sepOcfDebt] if s is not None]
        if sepCfScores:
            sepAxis4 = sum(s for s, _ in sepCfScores) / len(sepCfScores)
            axis4 = round(axis4 * 0.5 + sepAxis4 * 0.5, 2)

    biz = metrics.get("businessStability", {})
    axis5_scores = _scoreBusinessStability(biz)
    axis5 = axisScore(axis5_scores)

    rel = metrics.get("reliability", {})
    audit = metrics.get("auditOpinion")
    axis6_scores = _scoreReliability(rel, audit)
    axis6 = axisScore(axis6_scores)

    dr = metrics.get("disclosureRisk")
    axis7_scores = _scoreDisclosureRisk(dr)
    axis7 = axisScore(axis7_scores)

    if captive or cyclical:
        w = _WEIGHTS["captive"]
    elif holding:
        w = _WEIGHTS["holding"]
    else:
        w = _WEIGHTS["default"]

    axes = [
        {"name": "채무상환능력", "score": axis1, "weight": w[0], "metrics": axis1_scores},
        {"name": "자본구조", "score": axis2, "weight": w[1], "metrics": axis2_scores},
        {"name": "유동성", "score": axis3, "weight": w[2], "metrics": axis3_scores},
        {"name": "현금흐름", "score": axis4, "weight": w[3], "metrics": axis4_scores},
        {"name": "사업안정성", "score": axis5, "weight": w[4], "metrics": axis5_scores},
        {"name": "재무신뢰성", "score": axis6, "weight": w[5], "metrics": axis6_scores},
        {"name": "공시리스크", "score": axis7, "weight": w[6], "metrics": axis7_scores},
    ]

    for a in axes:
        score = a.get("score")
        weight = a.get("weight", 0)
        a["contribution"] = round(score * weight, 2) if score is not None else None

    currentScore = weightedScore([{"score": a["score"], "weight": a["weight"]} for a in axes])

    historicalScores = _calcHistoricalScores(metrics, thresholds)
    overall = _applyTimeSeriesSmoothing(currentScore, historicalScores)

    grade, gradeDesc, pdEstimate, overall, chsResult, notchAdj, divExpl = _applyPostAdjustments(
        company, overall, latest, metrics, axes, captive, holding, sepMetrics
    )

    eCR = cashFlowGrade(
        latest.get("ocfToSales"),
        latest.get("fcf") is not None and (latest.get("fcf") or 0) > 0,
        latest.get("ocfToDebt"),
        all(h.get("ocf") is not None and (h.get("ocf") or 0) > 0 for h in metrics["history"][:3])
        if len(metrics["history"]) >= 3
        else None,
    )

    allScores = [currentScore] + historicalScores
    outlook = creditOutlook(allScores)

    result = {
        "grade": f"dCR-{grade}",
        "gradeRaw": grade,
        "gradeDescription": gradeDesc,
        "gradeCategory": gradeCategory(grade),
        "investmentGrade": isInvestmentGrade(grade),
        "score": overall,
        "healthScore": round(100 - overall, 2),
        "currentScore": currentScore,
        "pdEstimate": pdEstimate,
        "eCR": eCR,
        "outlook": outlook,
        "sector": sectorLabel,
        "captiveFinance": captive,
        "holding": holding,
        "latestPeriod": latest.get("period"),
        "chsAdjustment": chsResult,
        "notchAdjustment": notchAdj if notchAdj["totalNotch"] != 0 else None,
        "divergenceExplanation": divExpl,
        "methodologyVersion": "v4.0",
        "_scoreMeaning": _CREDIT_SCORE_LEGEND,
        "axes": [
            {
                "name": a["name"],
                "score": a["score"],
                "weight": round(a["weight"] * 100),
                "contribution": a.get("contribution"),
                "metrics": _normalizeMetricsForOutput(a["metrics"]),
            }
            for a in axes
        ],
    }

    if requestedOverrides:
        result["appliedOverrides"] = appliedOverrides
        result["ignoredOverrides"] = ignoredOverrides
        result["scenarioMetrics"] = latest
        result["scenarioAdjustments"] = scenarioAdjustments

    if detail:
        result["metricsHistory"] = metrics["history"]
        result["businessStability"] = metrics.get("businessStability")
        result["reliability"] = metrics.get("reliability")
        result["disclosureRisk"] = metrics.get("disclosureRisk")
        result["auditOpinion"] = metrics.get("auditOpinion")
        result["auditOpinionEvidence"] = metrics.get("auditOpinionEvidence")
        result["borrowingsDetail"] = metrics.get("borrowingsDetail")
        result["provisionsDetail"] = metrics.get("provisionsDetail")

        result["profile"] = metrics.get("profile")
        result["segmentComposition"] = metrics.get("segmentComposition")
        result["rank"] = metrics.get("rank")
        result["separateMetrics"] = sepMetrics

        from dartlab.credit.features.narrative import (
            buildNarratives,
            buildOverallNarrative,
            narrateBorrowings,
            narrateCausalChain,
            narrateProfile,
            narrateTrend,
        )

        narratives = buildNarratives(result, captive=captive, holding=holding, separateMetrics=sepMetrics)

        profileNarrative = narrateProfile(
            metrics.get("profile"), metrics.get("segmentComposition"), metrics.get("rank")
        )
        trendNarrative = narrateTrend(metrics["history"])
        borrowingsNarrative = narrateBorrowings(
            metrics.get("borrowingsDetail"), metrics["history"][0] if metrics["history"] else None
        )

        causalChain = narrateCausalChain(metrics["history"][0] if metrics["history"] else {}, result)

        result["narratives"] = {
            "overall": buildOverallNarrative(
                result, narratives, captive=captive, holding=holding, separateMetrics=sepMetrics
            ),
            "causalChain": causalChain,
            "profile": profileNarrative,
            "trend": trendNarrative,
            "borrowings": borrowingsNarrative,
            "axes": [
                {
                    "axis": n.axisName,
                    "summary": n.summary,
                    "details": n.details,
                    "severity": n.severity,
                }
                for n in narratives
            ],
        }

    return result


def _applyCreditOverrides(
    latest: dict,
    requested: dict,
) -> tuple[dict, dict[str, str], dict[str, dict[str, float]]]:
    """검증된 신용 override를 실제 점수 입력에 적용한다.

    명시 override는 stress preset 뒤에 적용한다. 계산에 쓰이지 않는 키는
    적용된 것처럼 기록하지 않고 ``ignoredOverrides``에 이유를 남긴다.
    """
    if not requested:
        return {}, {}, {}

    applied: dict = {}
    ignored: dict[str, str] = {}
    adjustments: dict[str, dict[str, float]] = {}

    stress = requested.get("scenarioStress")
    stressFactors = {
        "mild": {
            "debtRatio": 1.10,
            "ebitdaInterestCoverage": 0.85,
            "currentRatio": 0.90,
            "ocfToDebt": 0.85,
            "focfToDebt": 0.80,
        },
        "moderate": {
            "debtRatio": 1.25,
            "ebitdaInterestCoverage": 0.65,
            "currentRatio": 0.75,
            "ocfToDebt": 0.65,
            "focfToDebt": 0.50,
        },
        "severe": {
            "debtRatio": 1.50,
            "ebitdaInterestCoverage": 0.40,
            "currentRatio": 0.55,
            "ocfToDebt": 0.35,
            "focfToDebt": 0.20,
        },
    }
    if stress is not None:
        factors = stressFactors.get(stress) if isinstance(stress, str) else None
        if factors is None:
            ignored["scenarioStress"] = "mild, moderate, severe 중 하나여야 합니다."
        else:
            for metric, factor in factors.items():
                before = latest.get(metric)
                if isinstance(before, bool) or not isinstance(before, (int, float)):
                    continue
                after = round(float(before) * factor, 6)
                latest[metric] = after
                adjustments[metric] = {"before": float(before), "after": after}
            if adjustments:
                applied["scenarioStress"] = stress
            else:
                ignored["scenarioStress"] = "stress를 적용할 관측 지표가 없습니다."

    keyMap = {
        "debtRatio": "debtRatio",
        "interestCoverage": "ebitdaInterestCoverage",
        "currentRatio": "currentRatio",
        "ocfToDebt": "ocfToDebt",
        "fcfToDebt": "focfToDebt",
    }
    for publicKey, metricKey in keyMap.items():
        if publicKey not in requested:
            continue
        value = requested[publicKey]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            ignored[publicKey] = "숫자 값이어야 합니다."
            continue
        before = latest.get(metricKey)
        latest[metricKey] = float(value)
        applied[publicKey] = value
        if isinstance(before, (int, float)) and not isinstance(before, bool):
            adjustments[metricKey] = {"before": float(before), "after": float(value)}

    if "quickRatio" in requested:
        ignored["quickRatio"] = "현재 dCR 유동성 축에는 검증된 당좌비율 calibration이 없습니다."

    return applied, ignored, adjustments
