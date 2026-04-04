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
    """지주사 판별 — 이름 + 재무 구조 복합 기준.

    1. 이름에 "지주"/"홀딩스"/"Holdings" 포함
    2. 관계기업투자자산/총자산 > 40% (재무 구조 기반)
    """
    name = getattr(company, "corpName", "") or ""
    if any(k in name for k in ("지주", "홀딩스", "Holdings")):
        return True
    # 재무 구조 기반: 관계기업 투자자산 비중
    try:
        bs = company.select("BS", ["종속기업,관계기업및공동기업투자", "관계기업등지분관련투자자산", "자산총계"])
        if bs is not None and len(bs) > 0:
            from dartlab.analysis.financial._helpers import toDict

            parsed = toDict(bs)
            if parsed:
                data, periods = parsed
                invest = data.get("종속기업,관계기업및공동기업투자", {}) or data.get("관계기업등지분관련투자자산", {})
                ta = data.get("자산총계", {})
                # 최신 기간
                for p in sorted(periods, reverse=True):
                    inv_val = invest.get(p)
                    ta_val = ta.get(p)
                    if inv_val and ta_val and ta_val > 0:
                        ratio = inv_val / ta_val
                        if ratio > 0.5:
                            return True
                        break
    except (TypeError, ValueError, KeyError, AttributeError):
        pass
    return False


def _calcCHSAdjustment(company, baseScore: float) -> dict | None:
    """CHS 부도확률 모델로 기본 점수를 ±2 notch 범위 보정.

    주가 데이터 없으면 None (보정 스킵).
    """
    try:
        from dartlab.core.finance.chsModel import calcCHS

        priceData = company.gather("price") if hasattr(company, "gather") else None
        if priceData is None or len(priceData) < 20:
            return None

        bs = company.select("BS", ["자산총계", "부채총계", "현금및현금성자산"])
        is_ = company.select("IS", ["당기순이익"])
        from dartlab.analysis.financial._helpers import toDict

        bsParsed = toDict(bs)
        isParsed = toDict(is_)
        if not bsParsed or not isParsed:
            return None

        bsData, periods = bsParsed
        isData, _ = isParsed

        # 최신 기간
        p = sorted(periods, reverse=True)[0] if periods else None
        if not p:
            return None

        ta = (bsData.get("자산총계", {}) or {}).get(p)
        tl = (bsData.get("부채총계", {}) or {}).get(p)
        cash = (bsData.get("현금및현금성자산", {}) or {}).get(p)
        ni = (isData.get("당기순이익", {}) or {}).get(p)

        if not all(v is not None and v != 0 for v in [ta, tl]):
            return None

        # 주가 데이터에서 시가총액, 변동성, 수익률 추출
        prices = priceData.sort("date") if "date" in priceData.columns else priceData
        closeCol = "close" if "close" in prices.columns else "종가"
        if closeCol not in prices.columns:
            return None

        closes = prices[closeCol].drop_nulls().to_list()
        if len(closes) < 20:
            return None

        latestPrice = closes[-1]
        if latestPrice <= 0:
            return None

        # 주식수 추정: EPS 역산 (가장 신뢰)
        shares = None
        try:
            epsData = company.select("IS", ["기본주당이익", "당기순이익"])
            if epsData is not None:
                from dartlab.analysis.financial._helpers import toDict as _td

                epsParsed = _td(epsData)
                if epsParsed:
                    epsDict, epsPeriods = epsParsed
                    eps = (epsDict.get("기본주당이익", {}) or {}).get(epsPeriods[0] if epsPeriods else "")
                    niForEps = (epsDict.get("당기순이익", {}) or {}).get(epsPeriods[0] if epsPeriods else "")
                    if eps and abs(eps) > 0 and niForEps:
                        shares = abs(niForEps / eps)
        except (TypeError, ValueError, KeyError, AttributeError, ZeroDivisionError):
            pass

        # fallback: 자본/주가
        if not shares:
            eq = ta - tl if ta and tl else None
            shares = eq / latestPrice if eq and latestPrice > 0 else None
        if not shares or shares <= 0:
            return None

        marketCap = shares * latestPrice

        # 변동성 (연환산 일별 수익률 표준편차)
        returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes)) if closes[i - 1] != 0]
        if len(returns) < 10:
            return None
        mean_r = sum(returns) / len(returns)
        var_r = sum((r - mean_r) ** 2 for r in returns) / len(returns)
        sigma = (var_r**0.5) * (252**0.5)

        exret = (closes[-1] / closes[0] - 1) if closes[0] != 0 else 0

        chsResult = calcCHS(
            netIncome=ni,
            totalLiabilities=tl,
            cash=cash,
            totalAssets=ta,
            marketCap=marketCap,
            equityVolatility=sigma,
            excessReturn=exret,
            stockPrice=latestPrice,
        )

        if chsResult is None:
            return None

        # CHS PD → 점수 매핑 (0-100 스케일)
        chsPd = chsResult.probability
        if chsPd <= 0.001:
            chsScore = 3  # AAA 급
        elif chsPd <= 0.01:
            chsScore = 10  # AA 급
        elif chsPd <= 0.05:
            chsScore = 25  # A 급
        elif chsPd <= 0.1:
            chsScore = 40  # BBB 급
        elif chsPd <= 0.3:
            chsScore = 60  # BB 급
        else:
            chsScore = 80  # B 이하

        # PD 기반 비대칭 조정 — 안전 기업 상향, 위험 기업 하향
        diff = chsScore - baseScore
        if chsPd <= 0.001:  # 극안전 (AAA급 PD)
            adj = max(-5.0, diff * 0.3)
        elif chsPd <= 0.01:  # 투자적격 확실 — 상향만 허용
            adj = max(-3.0, min(0, diff * 0.2))
        elif chsPd > 0.10:  # 부실 신호 — 하향만
            adj = min(5.0, max(0, diff * 0.2))
        else:  # 중간 대역
            adj = max(min(diff * 0.15, 3.0), -3.0)
        # 안전장치: BB 이하(score>40)이면 CHS 상향 제한
        if baseScore > 40:
            adj = max(adj, -3.0)

        return {
            "adjustedScore": round(baseScore + adj, 2),
            "chsScore": chsScore,
            "chsPd": chsPd,
            "adjustment": round(adj, 2),
        }
    except (ImportError, TypeError, ValueError, KeyError, AttributeError, ZeroDivisionError):
        return None


def _isCaptiveFinance(totalBorrowing: float, ebitda: float | None, isFinancial: bool) -> bool:
    """캡티브 금융 감지 — D/EBITDA > 15."""
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
        from dartlab.credit.metrics import calcSeparateMetrics

        sep = calcSeparateMetrics(company)
        if sep is None:
            return False
        sepBorrowing = sep.get("totalBorrowing", 0) or 0
        if sepBorrowing <= 0:
            # 별도 차입금 0이면 전부 자회사 차입금
            return consolidatedBorrowing > 1e12  # 1조 이상이면 의미 있음
        ratio = consolidatedBorrowing / sepBorrowing
        return ratio > 10
    except (ImportError, TypeError, ValueError, AttributeError):
        return False


_PUBLIC_CORPS = {"한국전력", "한국가스공사", "한국수력원자력", "한국도로공사", "한국토지주택공사"}


def _calcNotchAdjustment(
    company,
    grade: str,
    score: float,
    latest: dict,
    metrics: dict,
    holding: bool,
    captive: bool,
    sepMetrics: dict | None,
) -> dict:
    """v3 Notch Adjustment — 기업 특성 기반 등급 보정.

    정량 점수만으로는 반영 불가능한 요소를 notch 단위로 보정:
    - 기업 규모/시장 지위
    - 공기업/규제 보호
    - 캡티브 금융 별도 부채 양호
    - 지주사 별도 부채 양호
    - CAPEX 집약 OCF 양수

    총 ±5 notch cap. score 15 이하(AA 이상)에는 미적용 (퇴행 방지).
    """
    # AA 이상(score<=10)은 조정 불필요 (퇴행 방지)
    if score <= 10:
        return {"totalNotch": 0, "reasons": []}

    notches: list[tuple[int, str]] = []
    corpName = getattr(company, "corpName", "") or ""

    # 1. 기업 규모 (매출 기준)
    revenue = latest.get("revenue") or 0
    if revenue > 50e12:  # 50조+
        notches.append((3, f"대형기업 (매출 {revenue / 1e12:.0f}조)"))
    elif revenue > 10e12:  # 10조+
        notches.append((1, f"중대형기업 (매출 {revenue / 1e12:.0f}조)"))

    # 2. 공기업/정부 보호
    if any(k in corpName for k in _PUBLIC_CORPS) or "한국전력" in corpName:
        notches.append((3, "공기업 (정부 보증/규제 보호)"))

    # 3. 캡티브 금융 — 별도 D/EBITDA가 양호하면 상향
    if captive and sepMetrics:
        sepDE = sepMetrics.get("separateDebtToEbitda")
        if sepDE is not None and sepDE < 3:
            notches.append((2, f"캡티브금융 별도 D/EBITDA {sepDE:.1f}x (양호)"))

    # 4. 지주사 — 별도 부채비율이 양호하면 상향
    if holding and sepMetrics:
        sepDR = sepMetrics.get("separateDebtRatio")
        if sepDR is not None and sepDR < 100:
            notches.append((2, f"지주사 별도 부채비율 {sepDR:.0f}% (양호)"))

    # 5. CAPEX 집약 but OCF 양수 (투자 중이지만 현금은 도는 기업)
    ocf = latest.get("ocf") or 0
    fcf = latest.get("fcf") or 0
    if ocf > 0 and fcf < 0 and abs(fcf) > 0:  # OCF+, FCF- = CAPEX 집약
        notches.append((1, "CAPEX집약 OCF양수 (투자 사이클)"))

    # ── 정성 대리 신호 (정량 데이터에서 추출) ──

    # 6. 시가총액 TOP 50 = 시장이 인정한 시장 지위/암묵적 지원
    try:
        priceData = company.gather("price") if hasattr(company, "gather") else None
        if priceData is not None and len(priceData) > 0:
            # EPS 역산 shares
            epsResult = company.select("IS", ["기본주당이익", "당기순이익"])
            from dartlab.analysis.financial._helpers import toDict as _tdNotch

            epsParsed = _tdNotch(epsResult)
            if epsParsed:
                ed, ep = epsParsed
                eps = (ed.get("기본주당이익", {}) or {}).get(ep[0] if ep else "")
                niE = (ed.get("당기순이익", {}) or {}).get(ep[0] if ep else "")
                closeCol = "close" if "close" in priceData.columns else "종가"
                if eps and abs(eps) > 0 and niE and closeCol in priceData.columns:
                    shares = abs(niE / eps)
                    latestClose = priceData[closeCol].drop_nulls().to_list()[-1]
                    mktCap = shares * latestClose
                    if mktCap > 30e12:  # 시가총액 30조+ (TOP ~30)
                        notches.append((3, f"시가총액 {mktCap / 1e12:.0f}조 (시장 지위)"))
                    elif mktCap > 10e12:  # 10조+
                        notches.append((1, f"시가총액 {mktCap / 1e12:.0f}조"))
    except (TypeError, ValueError, KeyError, AttributeError, IndexError, ZeroDivisionError):
        pass

    # 7. 장기 상장 + 연속 흑자 = 경영 역량 대리
    histLen = len(metrics.get("history", []))
    if histLen >= 5:
        niHistory = [h.get("operatingIncome") for h in metrics["history"][:5]]
        allPositive = all(v is not None and v > 0 for v in niHistory)
        if allPositive:
            notches.append((1, f"연속 {histLen}기 영업흑자 (경영 안정성)"))

    # 총 notch 합산 (상한 7 — 정성 대리 3개 추가)
    totalNotch = min(sum(n for n, _ in notches), 7)

    # A 범위(10 < score <= 19): 과보정 방지, 최대 4 notch
    if score <= 19:
        totalNotch = min(totalNotch, 4)

    reasons = [r for _, r in notches]
    return {"totalNotch": totalNotch, "reasons": reasons}


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
    """Company 객체로 신용등급 산출.

    기업 유형에 따라 3-Track 분기:
    - Track A: 일반기업 (기존 7축)
    - Track B: 금융업 (5축 전용)
    - Track C: 지주사 (7축 + 가중치 차별화)
    """
    sector, industryGroup = _getSectorInfo(company)
    isFinancialCo = _isFinancial(company)

    # ── Track B: 금융업 전용 평가 ──
    if isFinancialCo:
        return _evaluateFinancial(company, detail=detail, basePeriod=basePeriod, sector=sector)

    metrics = calcAllMetrics(company, basePeriod=basePeriod)
    if metrics is None or not metrics.get("history"):
        return None

    latest = metrics["history"][0]
    holding = _isHolding(company)
    captive = _isCaptiveFinance(
        latest.get("totalBorrowing") or 0,
        latest.get("ebitda"),
        isFinancialCo,
    )
    # OFS 기반 캡티브 보강 (D/EBITDA < 15이어도 연결/별도 차입금 비율로 감지)
    if not captive and not isFinancialCo:
        captive = _isCaptiveByOFS(company, latest.get("totalBorrowing") or 0)
    cyclical = _isCyclical(sector)

    # 기준표 선택 (캡티브 > 지주 > 업종별 > 기본)
    if captive:
        from dartlab.core.finance.sectorThresholds import _airlineThresholds

        thresholds = _airlineThresholds()
        sectorLabel = f"{getSectorLabel(sector)} (캡티브금융조정)"
    elif holding:
        from dartlab.core.finance.sectorThresholds import _holdingThresholds

        thresholds = _holdingThresholds()
        sectorLabel = f"{getSectorLabel(sector)} (지주사조정)"
    else:
        thresholds = getThresholds(sector, industryGroup)
        sectorLabel = getSectorLabel(sector)

    # ── 축 1: 채무상환능력 ──
    # FOCF/Debt: FCF가 음수(CAPEX > OCF)면 구조적으로 나쁜 값 → 스킵
    focfScore = scoreMetric(latest.get("focfToDebt"), thresholds["focf_to_debt"])
    if latest.get("fcf") is not None and (latest.get("fcf") or 0) < 0:
        focfScore = None  # FCF 음수 기업은 FOCF/Debt 무의미 — 다른 지표로 평가

    axis1_scores = [
        ("FFO/총차입금", scoreMetric(latest.get("ffoToDebt"), thresholds["ffo_to_debt"])),
        ("Debt/EBITDA", scoreMetric(latest.get("debtToEbitda"), thresholds["debt_to_ebitda"])),
        ("FOCF/Debt", focfScore),
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

    # ── 별도재무제표 블렌딩 (지주/캡티브만) ──
    _needsOFS = holding or captive
    sepMetrics = None
    if _needsOFS and axis1 is not None:
        from dartlab.credit.metrics import calcSeparateMetrics

        sepMetrics = calcSeparateMetrics(company)
        if sepMetrics is not None:
            # 축1: 별도 D/EBITDA 블렌딩
            sep_axis1_scores = [
                ("별도D/EBITDA", scoreMetric(sepMetrics.get("separateDebtToEbitda"), thresholds["debt_to_ebitda"])),
            ]
            sep1 = axisScore(sep_axis1_scores)
            if sep1 is not None and axis1 is not None:
                # 동적 블렌딩: 별도가 10점+ 양호하면 별도 비중 65%
                if sep1 < axis1 - 10:
                    axis1 = round(axis1 * 0.35 + sep1 * 0.65, 2)
                else:
                    axis1 = round(axis1 * 0.5 + sep1 * 0.5, 2)

            # 축2: 별도 부채비율 블렌딩
            sep_axis2_scores = [
                ("별도부채비율", scoreMetric(sepMetrics.get("separateDebtRatio"), thresholds["debt_ratio"])),
                (
                    "별도차입금의존도",
                    scoreMetric(sepMetrics.get("separateBorrowingDep"), thresholds["borrowing_dependency"]),
                ),
            ]
            sep2 = axisScore(sep_axis2_scores)
            if sep2 is not None and axis2 is not None:
                if sep2 < axis2 - 10:
                    axis2 = round(axis2 * 0.35 + sep2 * 0.65, 2)
                else:
                    axis2 = round(axis2 * 0.5 + sep2 * 0.5, 2)

    # ── Phase 4: 캡티브/지주/사이클 축1 압축 (20 초과분 40% 감쇄) ──
    if (captive or holding or cyclical) and axis1 is not None and axis1 > 20:
        excess = axis1 - 20
        axis1 = round(20 + excess * 0.6, 2)

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

    # #1: 축4에도 별도 OCF 블렌딩 (캡티브/지주/자본집약)
    if _needsOFS and sepMetrics is not None and axis4 is not None:
        sepOcfScore = scoreMetric(
            sepMetrics.get("separateOcfToSales"), thresholds.get("ocf_to_sales", thresholds.get("cash_ratio", {}))
        )
        sepOcfDebt = scoreMetric(sepMetrics.get("separateOcfToDebt"), thresholds.get("focf_to_debt", {}))
        sepCfScores = [(s, 1) for s in [sepOcfScore, sepOcfDebt] if s is not None]
        if sepCfScores:
            sepAxis4 = sum(s for s, _ in sepCfScores) / len(sepCfScores)
            axis4 = round(axis4 * 0.5 + sepAxis4 * 0.5, 2)

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
    # isFinancialCo는 이미 Track B로 분기됨 (여기 도달 안 함)
    if captive or cyclical:
        w = [0.30, 0.15, 0.15, 0.15, 0.10, 0.10, 0.05]
    elif holding:
        # 지주사: 채무상환능력↓ 자본구조↑ 사업안정성↑ (연결 D/EBITDA 왜곡 보정)
        w = [0.15, 0.25, 0.15, 0.15, 0.15, 0.10, 0.05]
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

    # ── CHS 부도확률 보정 (±2 notch) ──
    chsResult = _calcCHSAdjustment(company, overall)
    if chsResult is not None:
        overall = chsResult["adjustedScore"]

    grade, gradeDesc, pdEstimate = mapTo20Grade(overall)

    # ── v3 Notch Adjustment (기업 특성 기반 등급 보정) ──
    notchAdj = _calcNotchAdjustment(
        company,
        grade,
        overall,
        latest,
        metrics,
        holding,
        captive,
        sepMetrics,
    )
    if notchAdj["totalNotch"] != 0:
        from dartlab.core.finance.creditScorecard import notchGrade as _notchGrade

        # notchGrade: +면 idx 증가(하향). 상향하려면 -notch
        grade = _notchGrade(grade, -notchAdj["totalNotch"])
        # 보정 후 등급에 맞는 PD 재계산
        from dartlab.core.finance.creditScorecard import estimatePD

        pdEstimate = estimatePD(grade)
        gradeDesc = gradeCategory(grade) + " (notch 조정)"

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
        "chsAdjustment": chsResult,
        "notchAdjustment": notchAdj if notchAdj["totalNotch"] != 0 else None,
        "methodologyVersion": "v3.0",
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


# ═══════════════════════════════════════════════════════════
# Track B: 금융업 전용 평가
# ═══════════════════════════════════════════════════════════


def _evaluateFinancial(
    company,
    *,
    detail: bool = False,
    basePeriod: str | None = None,
    sector=None,
) -> dict | None:
    """금융업(은행/보험/증권) 전용 5축 평가.

    D/EBITDA, FFO/Debt를 사용하지 않고
    자본비율, ROA, NIM, 충당금 비율로 평가.
    """
    from dartlab.credit.metrics import calcFinancialMetrics

    metrics = calcFinancialMetrics(company, basePeriod=basePeriod)
    if metrics is None or not metrics.get("history"):
        return None

    from dartlab.core.finance.sectorThresholds import financialTrackBThresholds

    thresholds = financialTrackBThresholds()
    latest = metrics["history"][0]

    # ── 축1: 자본적정성 ──
    ax1 = [
        ("자기자본비율", scoreMetric(latest.get("equityRatio"), thresholds["equity_ratio"])),
    ]
    s1 = axisScore(ax1)

    # ── 축2: 수익성 ──
    ax2 = [
        ("ROA", scoreMetric(latest.get("roa"), thresholds["roa"])),
        ("NIM대리", scoreMetric(latest.get("nimProxy"), thresholds["nim_proxy"])),
    ]
    s2 = axisScore(ax2)

    # ── 축3: 자산건전성 ──
    ax3 = [
        ("충당금비율", scoreMetric(latest.get("provisionRatio"), thresholds["provision_ratio"])),
    ]
    s3 = axisScore(ax3)
    if s3 is None:
        s3 = 25.0  # #4: 데이터 없으면 중립 (0=최우량도 100=최위험도 아님)

    # ── 축4: 유동성 ──
    ax4 = [
        ("현금/자산", scoreMetric(latest.get("cashToAsset"), thresholds["cash_to_asset"])),
        ("유동비율", scoreMetric(latest.get("currentRatio"), thresholds["current_ratio"])),
    ]
    s4 = axisScore(ax4)
    if s4 is None:
        s4 = 25.0  # #4: 유동성도 데이터 없으면 중립

    # ── 축5: 사업안정성 ──
    biz = metrics.get("businessStability", {})
    ax5 = []
    revCV = biz.get("revenueCV")
    if revCV is not None:
        ax5.append(("영업안정성", min(revCV, 100)))
    totalAssets = biz.get("totalAssets")
    if totalAssets and totalAssets > 50e12:
        ax5.append(("규모", 0.0))  # 대형 금융지주 = 최소 위험
    elif totalAssets and totalAssets > 10e12:
        ax5.append(("규모", 15.0))
    else:
        ax5.append(("규모", 35.0))
    s5 = axisScore(ax5) if ax5 else 25.0

    # ── 가중평균 ──
    # 금융지주: 자본 35% + 수익 35% + 자산건전 15% + 사업안정 15% + 유동 0%
    # 유동성 완전 제거: 은행 현금/자산 비율은 무의미 (예수금 유동성, 중앙은행 보증)
    w = [0.35, 0.35, 0.15, 0.00, 0.15]
    axes = [
        {"name": "자본적정성", "score": s1, "weight": w[0], "metrics": ax1},
        {"name": "수익성", "score": s2, "weight": w[1], "metrics": ax2},
        {"name": "자산건전성", "score": s3, "weight": w[2], "metrics": ax3},
        {"name": "유동성", "score": s4, "weight": w[3], "metrics": ax4},
        {"name": "사업안정성", "score": s5, "weight": w[4], "metrics": ax5},
    ]

    currentScore = weightedScore([{"score": a["score"], "weight": a["weight"]} for a in axes])

    # 시계열 안정화 (간이 — 과거 ROA/자본비율 추세)
    historicalScores = []
    for h in metrics["history"][1:3]:
        scores = []
        er = scoreMetric(h.get("equityRatio"), thresholds["equity_ratio"])
        roa = scoreMetric(h.get("roa"), thresholds["roa"])
        if er is not None:
            scores.append(er)
        if roa is not None:
            scores.append(roa)
        if scores:
            historicalScores.append(sum(scores) / len(scores))

    if len(historicalScores) >= 2:
        overall = currentScore * 0.60 + historicalScores[0] * 0.25 + historicalScores[1] * 0.15
    elif len(historicalScores) == 1:
        overall = currentScore * 0.70 + historicalScores[0] * 0.30
    else:
        overall = currentScore
    overall = round(overall, 2)

    # CHS 보정
    chsResult = _calcCHSAdjustment(company, overall)
    if chsResult is not None:
        overall = chsResult["adjustedScore"]

    grade, gradeDesc, pdEstimate = mapTo20Grade(overall)

    sectorLabel = f"{getSectorLabel(sector)} (Track B 금융전용)"

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
        "eCR": None,
        "outlook": creditOutlook([currentScore] + historicalScores),
        "sector": sectorLabel,
        "captiveFinance": False,
        "holding": False,
        "latestPeriod": latest.get("period"),
        "chsAdjustment": chsResult,
        "methodologyVersion": "v2.0-TrackB",
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

    return result
