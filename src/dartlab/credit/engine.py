"""신용등급 산출 메인 파이프라인.

Layer 1 (metrics.py) → Layer 2 (scorecard) → Layer 3 (등급 결정)
→ Layer 4 (보고서 생성) 순서로 실행.
"""

from __future__ import annotations

from dartlab.credit.metrics import calcAllMetrics
from dartlab.credit.scorecard import (
    axisScore,
    cashFlowGrade,
    creditOutlook,
    gradeCategory,
    isInvestmentGrade,
    mapTo20Grade,
    scoreMetric,
    weightedScore,
)
from dartlab.credit.thresholds import getSectorLabel, getThresholds


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
            from dartlab.core.sector.types import Sector

            return sector == Sector.FINANCIALS
    except (AttributeError, ImportError):
        pass
    return False


def _isHolding(company) -> bool:
    name = getattr(company, "corpName", "") or ""
    return any(k in name for k in ("지주", "홀딩스", "Holdings"))


def _isCaptiveFinance(totalBorrowing: float, ebitda: float | None, isFinancial: bool) -> bool:
    if isFinancial or ebitda is None or ebitda <= 0 or totalBorrowing <= 0:
        return False
    return totalBorrowing / ebitda > 15


def _isCyclical(sector) -> bool:
    if sector is None:
        return False
    try:
        from dartlab.core.sector.types import Sector

        return sector in (Sector.ENERGY, Sector.MATERIALS)
    except ImportError:
        return False


# ═══════════════════════════════════════════════════════════


def evaluate(stockCode: str, *, detail: bool = False, basePeriod: str | None = None) -> dict | None:
    """신용등급 산출 메인 진입점."""
    from dartlab import Company

    company = Company(stockCode)
    return evaluateCompany(company, detail=detail, basePeriod=basePeriod)


def evaluateCompany(company, *, detail: bool = False, basePeriod: str | None = None) -> dict | None:
    """Company 객체로 신용등급 산출."""
    metrics = calcAllMetrics(company, basePeriod=basePeriod)
    if metrics is None or not metrics.get("history"):
        return None

    latest = metrics["history"][0]
    sector, industryGroup = _getSectorInfo(company)
    isFinancialCo = _isFinancial(company)
    holding = _isHolding(company)
    captive = _isCaptiveFinance(
        latest.get("totalBorrowing") or 0,
        latest.get("ebitda"),
        isFinancialCo,
    )
    cyclical = _isCyclical(sector)

    # 캡티브 금융이면 유틸리티 기준 적용
    if captive:
        from dartlab.core.sector.types import Sector

        thresholds = getThresholds(Sector.UTILITIES, None)
        sectorLabel = f"{getSectorLabel(sector)} (캡티브금융조정)"
    else:
        thresholds = getThresholds(sector, industryGroup)
        sectorLabel = getSectorLabel(sector)

    # ── 축 1: 채무상환능력 ──
    axis1_scores = [
        ("FFO/총차입금", scoreMetric(latest.get("ffoToDebt"), thresholds["ffo_to_debt"])),
        ("Debt/EBITDA", scoreMetric(latest.get("debtToEbitda"), thresholds["debt_to_ebitda"])),
        ("FOCF/Debt", scoreMetric(latest.get("focfToDebt"), thresholds["focf_to_debt"])),
        ("EBITDA/이자비용", scoreMetric(latest.get("ebitdaInterestCoverage"), thresholds["ebitda_interest_coverage"])),
    ]
    axis1 = axisScore(axis1_scores)

    # ── 축 2: 자본 구조 ──
    axis2_scores = [
        ("부채비율", scoreMetric(latest.get("debtRatio"), thresholds["debt_ratio"])),
        ("차입금의존도", scoreMetric(latest.get("borrowingDependency"), thresholds["borrowing_dependency"])),
        ("순차입금/EBITDA", scoreMetric(latest.get("netDebtToEbitda"), thresholds["net_debt_to_ebitda"])),
    ]
    axis2 = axisScore(axis2_scores)

    # ── 축 3: 유동성 ──
    axis3_scores = [
        ("유동비율", scoreMetric(latest.get("currentRatio"), thresholds["current_ratio"])),
        ("현금비율", scoreMetric(latest.get("cashRatio"), thresholds["cash_ratio"])),
        ("단기차입금비중", scoreMetric(latest.get("shortTermDebtRatio"), thresholds["short_term_debt_ratio"])),
    ]
    axis3 = axisScore(axis3_scores)

    # ── 축 4: 현금흐름 ──
    axis4_scores = _scoreCashFlow(latest, metrics)
    axis4 = axisScore(axis4_scores)

    # ── 축 5: 사업 안정성 ──
    biz = metrics.get("businessStability", {})
    axis5_scores = _scoreBusinessStability(biz)
    axis5 = axisScore(axis5_scores)

    # ── 축 6: 재무 신뢰성 ──
    rel = metrics.get("reliability", {})
    audit = metrics.get("auditOpinion")
    axis6_scores = _scoreReliability(rel, audit)
    axis6 = axisScore(axis6_scores)

    # ── 축 7: 공시 리스크 ──
    dr = metrics.get("disclosureRisk")
    axis7_scores = _scoreDisclosureRisk(dr)
    axis7 = axisScore(axis7_scores)

    # ── 가중평균 ──
    if isFinancialCo:
        w = [0.25, 0.20, 0.15, 0.15, 0.10, 0.10, 0.05]
    elif captive or cyclical:
        w = [0.30, 0.15, 0.15, 0.15, 0.10, 0.10, 0.05]
    elif holding:
        w = [0.25, 0.20, 0.15, 0.15, 0.10, 0.10, 0.05]
    else:
        w = [0.25, 0.20, 0.15, 0.15, 0.10, 0.10, 0.05]

    axes = [
        {"name": "채무상환능력", "score": axis1, "weight": w[0], "metrics": axis1_scores},
        {"name": "자본구조", "score": axis2, "weight": w[1], "metrics": axis2_scores},
        {"name": "유동성", "score": axis3, "weight": w[2], "metrics": axis3_scores},
        {"name": "현금흐름", "score": axis4, "weight": w[3], "metrics": axis4_scores},
        {"name": "사업안정성", "score": axis5, "weight": w[4], "metrics": axis5_scores},
        {"name": "재무신뢰성", "score": axis6, "weight": w[5], "metrics": axis6_scores},
        {"name": "공시리스크", "score": axis7, "weight": w[6], "metrics": axis7_scores},
    ]

    currentScore = weightedScore([{"score": a["score"], "weight": a["weight"]} for a in axes])

    # ── 시계열 안정화 (3개년 가중이동평균) ──
    historicalScores = _calcHistoricalScores(metrics, thresholds)
    if len(historicalScores) >= 2:
        overall = currentScore * 0.60 + historicalScores[0] * 0.25 + historicalScores[1] * 0.15
    elif len(historicalScores) == 1:
        overall = currentScore * 0.70 + historicalScores[0] * 0.30
    else:
        overall = currentScore
    overall = round(overall, 2)

    grade, gradeDesc, pdEstimate = mapTo20Grade(overall)

    # ── eCR ──
    eCR = cashFlowGrade(
        latest.get("ocfToSales"),
        latest.get("fcf") is not None and (latest.get("fcf") or 0) > 0,
        latest.get("ocfToDebt"),
        all(h.get("ocf") is not None and (h.get("ocf") or 0) > 0 for h in metrics["history"][:3])
        if len(metrics["history"]) >= 3
        else None,
    )

    # ── Outlook ──
    allScores = [currentScore] + historicalScores
    outlook = creditOutlook(allScores)

    # ── 결과 조립 ──
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
        "methodologyVersion": "v1.0",
        "axes": [
            {
                "name": a["name"],
                "score": a["score"],
                "weight": round(a["weight"] * 100),
                "metrics": [{"name": n, "score": s} for n, s in a["metrics"] if s is not None],
            }
            for a in axes
        ],
    }

    if detail:
        result["metricsHistory"] = metrics["history"]
        result["businessStability"] = metrics.get("businessStability")
        result["reliability"] = metrics.get("reliability")
        result["disclosureRisk"] = metrics.get("disclosureRisk")
        result["auditOpinion"] = metrics.get("auditOpinion")
        result["borrowingsDetail"] = metrics.get("borrowingsDetail")
        result["provisionsDetail"] = metrics.get("provisionsDetail")

        # 신규: 프로필 + 부문 구성 + 순위
        result["profile"] = metrics.get("profile")
        result["segmentComposition"] = metrics.get("segmentComposition")
        result["rank"] = metrics.get("rank")

        # 서사 생성 — AI가 소비할 로데이터 + 해석
        from dartlab.credit.narrative import (
            buildNarratives,
            buildOverallNarrative,
            narrateBorrowings,
            narrateCausalChain,
            narrateProfile,
            narrateTrend,
        )

        narratives = buildNarratives(result)

        # 추가 서사
        profileNarrative = narrateProfile(
            metrics.get("profile"),
            metrics.get("segmentComposition"),
            metrics.get("rank"),
        )
        trendNarrative = narrateTrend(metrics["history"])
        borrowingsNarrative = narrateBorrowings(
            metrics.get("borrowingsDetail"),
            metrics["history"][0] if metrics["history"] else None,
        )

        # 6막 인과 연결
        causalChain = narrateCausalChain(
            metrics["history"][0] if metrics["history"] else {},
            result,
        )

        result["narratives"] = {
            "overall": buildOverallNarrative(result, narratives),
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


# ═══════════════════════════════════════════════════════════
# 축별 스코어링 헬퍼
# ═══════════════════════════════════════════════════════════


def _scoreCashFlow(latest: dict, metrics: dict) -> list[tuple[str, float | None]]:
    """축 4: 현금흐름 점수."""
    scores = []

    ocfSales = latest.get("ocfToSales")
    if ocfSales is not None:
        if ocfSales > 20:
            scores.append(("OCF/매출", 0.0))
        elif ocfSales > 10:
            scores.append(("OCF/매출", 10.0))
        elif ocfSales > 5:
            scores.append(("OCF/매출", 20.0))
        elif ocfSales > 0:
            scores.append(("OCF/매출", 35.0))
        else:
            scores.append(("OCF/매출", min(70, 50 + abs(ocfSales))))

    fcfSales = latest.get("fcfToSales")
    if fcfSales is not None:
        if fcfSales > 10:
            scores.append(("FCF/매출", 0.0))
        elif fcfSales > 0:
            scores.append(("FCF/매출", 15.0))
        else:
            scores.append(("FCF/매출", min(60, 35 + abs(fcfSales))))

    # OCF 추세 (3기 연속 양수이면 안정)
    ocfs = [h.get("ocf") for h in metrics["history"][:3]]
    validOcfs = [o for o in ocfs if o is not None]
    if len(validOcfs) >= 3:
        if all(o > 0 for o in validOcfs):
            scores.append(("OCF추세", 0.0))
        elif validOcfs[0] is not None and validOcfs[0] < 0:
            scores.append(("OCF추세", 50.0))
        else:
            scores.append(("OCF추세", 20.0))

    return scores


def _scoreBusinessStability(biz: dict) -> list[tuple[str, float | None]]:
    """축 5: 사업 안정성 점수."""
    scores = []

    revCV = biz.get("revenueCV")
    if revCV is not None:
        if revCV < 5:
            scores.append(("매출안정성", 0.0))
        elif revCV < 15:
            scores.append(("매출안정성", (revCV - 5) * 2))
        elif revCV < 30:
            scores.append(("매출안정성", 20 + (revCV - 15) * 1.5))
        else:
            scores.append(("매출안정성", min(55, 42.5 + (revCV - 30) * 0.5)))

    opCV = biz.get("opMarginCV")
    if opCV is not None:
        if opCV < 10:
            scores.append(("이익안정성", 0.0))
        elif opCV < 30:
            scores.append(("이익안정성", (opCV - 10)))
        elif opCV < 60:
            scores.append(("이익안정성", 20 + (opCV - 30) * 0.5))
        else:
            scores.append(("이익안정성", min(50, 35)))

    latestRev = biz.get("latestRevenue")
    if latestRev is not None:
        revTril = latestRev / 1e12
        if revTril > 50:
            scores.append(("규모", 0.0))
        elif revTril > 10:
            scores.append(("규모", 5.0))
        elif revTril > 1:
            scores.append(("규모", 15.0))
        elif revTril > 0.1:
            scores.append(("규모", 30.0))
        else:
            scores.append(("규모", 45.0))

    hhi = biz.get("segmentHHI")
    if hhi is not None:
        if hhi < 1500:
            scores.append(("부문다각화", 0.0))
        elif hhi < 2500:
            scores.append(("부문다각화", 15.0))
        elif hhi < 5000:
            scores.append(("부문다각화", 30.0))
        else:
            scores.append(("부문다각화", 40.0))

    return scores


def _scoreReliability(rel: dict, auditOpinion: str | None) -> list[tuple[str, float | None]]:
    """축 6: 재무 신뢰성 점수."""
    scores = []

    # Beneish M-Score
    m = rel.get("beneishMScore")
    if m is not None:
        if m < -2.22:
            scores.append(("Beneish M", 0.0))
        elif m < -1.78:
            scores.append(("Beneish M", 20.0))
        else:
            scores.append(("Beneish M", 45.0))

    # Piotroski F-Score
    f = rel.get("piotroskiFScore")
    if f is not None:
        if f >= 7:
            scores.append(("Piotroski F", 0.0))
        elif f >= 5:
            scores.append(("Piotroski F", 10.0))
        elif f >= 3:
            scores.append(("Piotroski F", 25.0))
        else:
            scores.append(("Piotroski F", 45.0))

    # 감사의견
    if auditOpinion is not None:
        if "적정" in auditOpinion and "한정" not in auditOpinion and "부적정" not in auditOpinion:
            scores.append(("감사의견", 0.0))
        elif "한정" in auditOpinion:
            scores.append(("감사의견", 50.0))
        elif "부적정" in auditOpinion or "의견거절" in auditOpinion:
            scores.append(("감사의견", 90.0))

    return scores


def _scoreDisclosureRisk(dr: dict | None) -> list[tuple[str, float | None]]:
    """축 7: 공시 리스크 점수."""
    if dr is None:
        return []

    scores = []

    chronic = dr.get("chronicYears") or dr.get("chronic_years", 0)
    if chronic >= 3:
        scores.append(("우발부채만성", 60.0))
    elif chronic >= 1:
        scores.append(("우발부채만성", 25.0))
    else:
        scores.append(("우발부채만성", 0.0))

    risk = dr.get("riskKeyword") or dr.get("risk_keyword", 0)
    if risk > 0:
        scores.append(("리스크키워드", min(70, 30 + risk * 10)))
    else:
        scores.append(("리스크키워드", 0.0))

    return scores


def _calcHistoricalScores(metrics: dict, thresholds: dict) -> list[float]:
    """과거 기간 간이 점수 (시계열 안정화용)."""
    scores = []
    for h in metrics["history"][1:3]:
        pScores = []
        for key, tKey in [
            ("ffoToDebt", "ffo_to_debt"),
            ("debtToEbitda", "debt_to_ebitda"),
            ("ebitdaInterestCoverage", "ebitda_interest_coverage"),
            ("debtRatio", "debt_ratio"),
            ("currentRatio", "current_ratio"),
        ]:
            s = scoreMetric(h.get(key), thresholds[tKey])
            if s is not None:
                pScores.append(s)
        if pScores:
            scores.append(round(sum(pScores) / len(pScores), 2))
    return scores
