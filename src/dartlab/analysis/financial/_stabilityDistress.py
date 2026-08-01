"""stability.py 부실 진단 calc 분리 — Altman Z'' + 계열 중복 없는 앙상블.

분리 이유: stability.py의 Altman 시계열과 다중 모델 투표를 별도 모듈로 빼서
stability.py 의 facade 책임 (레버리지/이자보상/만기/플래그) 만 유지.

BC: stability 모듈에서 두 함수 모두 import 가능 (re-export).
"""

from __future__ import annotations

from dartlab.analysis.financial.companyContext import getRatios
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import (
    MAX_RATIO_YEARS,
    annualColsFromPeriods,
    toDictBySnakeId,
)

_MAX_YEARS = MAX_RATIO_YEARS


def _distressUnavailable(reasonCode: str, *, missingInputs: list[str] | None = None) -> dict:
    """Altman Z''를 발행할 수 없는 경로의 공통 계약."""
    return {
        "status": "unavailable",
        "available": False,
        "reasonCode": reasonCode,
        "missingInputs": missingInputs or [],
        "history": [],
        "latestScore": None,
        "zone": "판별 불가",
        "diagnosticMeta": {
            "model": "Z''-Score",
            "variant": "zpp",
            "thresholds": {"distressBelow": 1.1, "safeAbove": 2.6},
            "financeBasis": "annual_consolidated",
            "selectedPeriod": None,
            "periodPolicy": "latest_common_complete_annual",
            "ebitSource": "operating_profit_proxy",
            "pointInTime": False,
            "precision": None,
            "typeIError": None,
            "reference": "Altman Z'' nonfinancial model",
        },
    }


@memoizedCalc
def calcDistressScore(company, *, basePeriod: str | None = None) -> dict | None:
    """Altman Z'' 시계열 + 4 변수 분해 — 비금융사 부실위험 판별.

    Capabilities:
        비금융사에 같은 Z'' 모형을 적용한다. 현재 시가총액을 과거 전 기간에 붙이거나
        시총 결손 때문에 Z/Z''를 바꾸지 않는다. 필수 계정 결손은 0으로 대체하지 않는다.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``history`` (list[dict]): 연도별 원천 + 4 X 변수 + score/zone
            - ``latestScore`` (float): 최신 Z-Score
            - ``zone`` (str): "안전"/"회색"/"위험"/"판별 불가"
            - ``diagnosticMeta`` (dict): 진단 메타

    Raises:
        없음.

    Example:
        >>> r = calcDistressScore(Company("005930"))
        >>> r["latestScore"], r["zone"]
        (3.2, '안전')

    Guide:
        Z'' 임계: >2.6 안전, 1.1~2.6 회색, <1.1 위험. 점수는 부도확률이 아니다.

    When:
        부실 위험 정량 진단, 신용 평가 보조 시점.

    How:
        연간 연결 BS/IS → 4 X 변수 → Z'' = 6.56X1 + 3.26X2 + 6.72X3 + 1.05X4.

    SeeAlso:
        - ``analyzeHealth``: Z-Score 포함 종합 건전성
        - ``calcDistressEnsemble``: 적용 가능한 독립 부실모형의 합성
        - ``dartlab.synth.distress.chsModel.calcCHS``: 현대 표준 (Campbell 2008)
        - Altman, E. (1968) "Financial Ratios, Discriminant Analysis"

    Requires:
        BS (자산총계, 유동자산/부채, 이익잉여금, 부채총계, 자본총계) + IS (영업이익 proxy).

    AIContext:
        Z-Score 절대값 + zone + history 추세 함께 인용. 단년도 위험 진입은
        일회성 (M&A/적자) 가능, 2 년 연속 distress zone 가 진짜 신호.
        금융업에는 적용하지 않는다. EBIT 대신 영업이익 proxy를 쓴다는 provenance를 확인한다.

    LLM Specifications:
        AntiPatterns:
            - Z-Score 1.5 단년도 → "부도 임박" 단정 — 2~3 년 연속 distress
              zone 확인 필수.
            - 금융업/계정 결손 회사에 점수 강제 산출.
        OutputSchema:
            ``{status: str, history: list[dict], latestScore: float | None, zone: str,
            diagnosticMeta: dict}``.
        Prerequisites:
            연간 BS/IS 시계열.
        Freshness:
            BS/IS 연간 공시.
        Dataflow:
            BS/IS → 자산/WC/RE/영업이익/장부자본/부채 → Z'' → zone 분류.
        TargetMarkets: KR (DART), US (EDGAR), 비금융사 한정.
    """
    from dartlab.analysis.financial._capitalCashflow import _isFinancialCompany

    if _isFinancialCompany(company):
        return _distressUnavailable("financial_company_unsupported")

    bsResult = company.select(
        "BS",
        [
            "자산총계",
            "유동자산",
            "유동부채",
            "부채총계",
            "자본총계",
            "이익잉여금",
            "미처분이익잉여금(결손금)",
        ],
    )
    isResult = company.select("IS", ["영업이익"])

    bsParsed = toDictBySnakeId(bsResult)
    isParsed = toDictBySnakeId(isResult)
    if bsParsed is None or isParsed is None:
        missingStatements = []
        if bsParsed is None:
            missingStatements.append("BS")
        if isParsed is None:
            missingStatements.append("IS")
        return _distressUnavailable("financial_statements_unavailable", missingInputs=missingStatements)

    bsData, bsPeriods = bsParsed
    isData, isPeriods = isParsed

    taRow = bsData.get("total_assets", {})
    caRow = bsData.get("current_assets", {})
    clRow = bsData.get("current_liabilities", {})
    tlRow = bsData.get("total_liabilities", {})
    eqRow = bsData.get("total_stockholders_equity", {})
    from dartlab.core.utils.helpers import mergeRows

    reRow = mergeRows(bsData.get("retained_earnings"), bsData.get("unappropriated_retained_earnings_deficit"))
    opRow = isData.get("operating_profit", {})

    bsAnnualCols = annualColsFromPeriods(bsPeriods, basePeriod, _MAX_YEARS)
    isAnnualCols = set(annualColsFromPeriods(isPeriods, basePeriod, _MAX_YEARS))
    # BS는 stock 계정이라 당해 Q1만 있어도 연도 alias가 생기지만, IS flow는 4개 분기가
    # 모두 있어야 연간값이 된다. 두 statement에 공통으로 존재하는 완결 연도만 쓴다.
    yCols = [period for period in bsAnnualCols if period in isAnnualCols]
    if not yCols:
        return _distressUnavailable("common_annual_period_unavailable")
    history = []
    for col in yCols:
        a = taRow.get(col)
        ca = caRow.get(col)
        cl = clRow.get(col)
        tl = tlRow.get(col)
        eq = eqRow.get(col)
        re = reRow.get(col)
        ebit = opRow.get(col)

        values = {
            "totalAssets": a,
            "currentAssets": ca,
            "currentLiabilities": cl,
            "retainedEarnings": re,
            "ebitProxy": ebit,
            "bookEquity": eq,
            "totalLiabilities": tl,
        }
        missing = [key for key, value in values.items() if value is None]
        valid_denominators = a is not None and a > 0 and tl is not None and tl > 0
        if missing or not valid_denominators:
            history.append(
                {
                    "period": col,
                    "zScore": None,
                    "zModel": "Z''-Score",
                    "zone": None,
                    "missingInputs": missing or ["nonpositive_denominator"],
                }
            )
            continue

        assert ca is not None and cl is not None and re is not None and ebit is not None and eq is not None
        wc = ca - cl
        x1Raw = wc / a
        x2Raw = re / a
        x3Raw = ebit / a
        x4Raw = eq / tl
        zScore = round(6.56 * x1Raw + 3.26 * x2Raw + 6.72 * x3Raw + 1.05 * x4Raw, 2)
        x1 = round(x1Raw, 6)
        x2 = round(x2Raw, 6)
        x3 = round(x3Raw, 6)
        x4 = round(x4Raw, 6)
        if zScore > 2.6:
            zone = "안전"
        elif zScore >= 1.1:
            zone = "회색"
        else:
            zone = "위험"

        history.append(
            {
                "period": col,
                "totalAssets": a,
                "workingCapital": wc,
                "retainedEarnings": re,
                "ebit": ebit,
                "totalDebt": tl,
                "bookEquity": eq,
                "x1_wcTa": x1,
                "x2_reTa": x2,
                "x3_ebitTa": x3,
                "x4_bveTl": x4,
                "zScore": zScore,
                "zModel": "Z''-Score",
                "zone": zone,
                "missingInputs": [],
            }
        )

    latest = history[0]
    available = latest.get("zScore") is not None
    result: dict = {
        "status": "ok" if available else "unavailable",
        "available": available,
        "reasonCode": None if available else "missing_required_inputs",
        "missingInputs": latest.get("missingInputs") or [],
        "history": history,
        "latestScore": latest.get("zScore"),
        "zone": latest.get("zone") or "판별 불가",
        "diagnosticMeta": {
            "model": "Z''-Score",
            "variant": "zpp",
            "thresholds": {"distressBelow": 1.1, "safeAbove": 2.6},
            "financeBasis": "annual_consolidated",
            "selectedPeriod": latest.get("period"),
            "periodPolicy": "latest_common_complete_annual",
            "ebitSource": "operating_profit_proxy",
            "pointInTime": False,
            "precision": None,
            "typeIError": None,
            "reference": "Altman Z'' nonfinancial model",
        },
    }

    # notes enrichment — 충당부채 (위험/회색 구간일 때 의미)
    from dartlab.analysis.financial.companyContext import fetchNotesDetail

    if available and result["zone"] in {"위험", "회색"}:
        notesDetail = fetchNotesDetail(company, ["provisions"])
        if notesDetail:
            result["notesDetail"] = notesDetail

    return result


# ── 부실 앙상블 ──


@memoizedCalc
def calcDistressEnsemble(company, *, basePeriod: str | None = None) -> dict | None:
    """적용 가능한 부실예측 모델 앙상블 — 다수결 투표.

    Capabilities:
        Altman 계열은 Z''를 우선하고 없을 때만 Z를 사용해 한 표로 집계한다.
        Ohlson O, Springate S, Zmijewski X 중 산출 가능한 모델과 함께
        verdict (safe/warning/danger)를 집계해 종합 등급과 일치도를 낸다.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``models`` (list[dict]): 모델별 (model, score, verdict, threshold)
            - ``ensemble`` (str): "안전"|"주의"|"위험"
            - ``agreement`` (float): 다수파 일치도 (%)
            - ``dangerCount``/``safeCount``/``total`` (int): 카운트

    Raises:
        없음.

    Example:
        >>> r = calcDistressEnsemble(Company("005930"))
        >>> r["ensemble"], r["agreement"]
        ('안전', 100.0)

    Guide:
        - agreement < 60% = 모델 간 불일치 → 단일 모델 결과 신뢰 어려움.
        - 다수결 "위험" + agreement > 80% = 다수 모델이 같은 방향을 가리키는 신호.
        - Ohlson O / Zmijewski X = logit 모델로 확률 (%) 출력, Altman = z-score.

    When:
        부실 위험 다중 모델 교차검증, 단일 모델 편향 제거 시점.

    How:
        getRatios의 적용 가능 모델 score → 계열당 한 표 → 다수결 + agreement 계산.

    SeeAlso:
        - ``calcDistressScore``: Altman Z 단독 시계열
        - ``credit.features.chsFeatures``: CHS (Campbell-Hilscher-Szilagyi)
        - ``calcLeverageTrend``: 부실 모델의 입력 (부채/자본/EBIT)

    Requires:
        IS + BS. Altman Z는 시가총액이 있을 때만 Z''의 대체 후보가 된다.

    AIContext:
        ensemble + agreement + 모델별 verdict 함께 인용. Altman Z와 Z''는
        서로 독립된 증거가 아니다. 한 모델만 "위험" 이고 나머지 safe 면
        해당 모델 한정 신호 (예: Ohlson 은 자본잠식·과거 적자에 민감).

    LLM Specifications:
        AntiPatterns:
            - 모델 1 개 결과 단독 인용 — 앙상블 다수결 인용 (편향 제거).
            - agreement 60% 미만에 강한 단정 — 모델 간 불일치 명시.
        OutputSchema:
            ``{models: list, ensemble: str, agreement: float, dangerCount: int,
              safeCount: int, total: int}``.
        Prerequisites:
            IS + BS. 원본 Altman Z를 쓸 때는 같은 기간 시가총액.
        Freshness:
            분기 (시가총액 일간 갱신, 회계 분기).
        Dataflow:
            getRatios → 적용 모델 score → 계열별 verdict → 다수결 → ensemble +
            agreement.
        TargetMarkets: KR/US. 금융업의 Altman 결과는 해석에서 제외한다.
    """
    ratios = getRatios(company)
    if ratios is None:
        return None

    models = []
    from dartlab.analysis.financial._capitalCashflow import _isFinancialCompany

    isFinancial = _isFinancialCompany(company)

    # Altman은 같은 위험 가설을 측정하는 한 계열이다. 범용 비금융 Z''를 우선하고
    # Z''가 없을 때만 제조업 원본 Z를 한 표로 쓴다.
    zpp = ratios.altmanZppScore
    if not isFinancial and zpp is not None:
        if zpp > 2.60:
            verdict = "safe"
        elif zpp >= 1.10:
            verdict = "warning"
        else:
            verdict = "danger"
        models.append(
            {
                "model": "Altman Z''-Score",
                "score": zpp,
                "verdict": verdict,
                "threshold": "안전 >2.60 / 회색 1.10~2.60 / 위험 <1.10",
            }
        )
    elif not isFinancial:
        z = ratios.altmanZScore
        if z is not None:
            if z > 2.99:
                verdict = "safe"
            elif z >= 1.81:
                verdict = "warning"
            else:
                verdict = "danger"
            models.append(
                {
                    "model": "Altman Z-Score",
                    "score": z,
                    "verdict": verdict,
                    "threshold": "안전 >2.99 / 회색 1.81~2.99 / 위험 <1.81",
                }
            )

    # Ohlson O-Score: P(default) < 10% safe, 10~50% warning, >50% danger
    oProb = ratios.ohlsonProbability
    if oProb is not None:
        if oProb < 10:
            verdict = "safe"
        elif oProb < 50:
            verdict = "warning"
        else:
            verdict = "danger"
        models.append(
            {
                "model": "Ohlson O-Score",
                "score": ratios.ohlsonOScore,
                "probability": oProb,
                "verdict": verdict,
                "threshold": "안전 <10% / 경고 10~50% / 위험 >50%",
            }
        )

    # Springate S-Score: >0.862 safe, else danger
    ss = ratios.springateSScore
    if ss is not None:
        verdict = "safe" if ss > 0.862 else "danger"
        models.append(
            {"model": "Springate S-Score", "score": ss, "verdict": verdict, "threshold": "안전 >0.862 / 위험 <0.862"}
        )

    # Zmijewski X-Score: <0 safe, else danger
    xz = ratios.zmijewskiXScore
    if xz is not None:
        verdict = "safe" if xz < 0 else "danger"
        models.append({"model": "Zmijewski X-Score", "score": xz, "verdict": verdict, "threshold": "안전 <0 / 위험 >0"})

    if not models:
        return None

    # 다수결
    dangerCount = sum(1 for m in models if m["verdict"] == "danger")
    safeCount = sum(1 for m in models if m["verdict"] == "safe")
    total = len(models)

    if dangerCount > total / 2:
        ensemble = "위험"
    elif safeCount > total / 2:
        ensemble = "안전"
    else:
        ensemble = "주의"

    agreement = max(dangerCount, safeCount) / total * 100

    return {
        "models": models,
        "ensemble": ensemble,
        "agreement": round(agreement, 1),
        "dangerCount": dangerCount,
        "safeCount": safeCount,
        "total": total,
    }
