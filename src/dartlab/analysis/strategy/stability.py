"""2-3 안정성 분석 -- 레버리지, 이자보상, 부실 판별, 부채 만기, 앙상블."""

from __future__ import annotations

from dartlab.analysis.strategy._helpers import (
    buildTimeline,
    getRatios,
    getRatioSeries,
    toDict,
)


def calcLeverageTrend(company) -> dict | None:
    """부채비율, 차입금의존도 시계열."""
    result = getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    debtRatio = buildTimeline(data, "debtRatio", years)
    netDebtRatio = buildTimeline(data, "netDebtRatio", years)
    equityRatio = buildTimeline(data, "equityRatio", years)

    if not debtRatio:
        return None

    return {
        "debtRatio": debtRatio,
        "netDebtRatio": netDebtRatio,
        "equityRatio": equityRatio,
    }


def calcCoverageTrend(company) -> dict | None:
    """이자보상배율 시계열."""
    result = getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    coverage = buildTimeline(data, "interestCoverage", years)

    if not coverage:
        return None

    return {"interestCoverage": coverage}


def calcDistressScore(company) -> dict | None:
    """Altman Z-Score 시계열 + 종합 등급."""
    result = getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    zScore = buildTimeline(data, "altmanZScore", years)

    if not zScore:
        return None

    latest = next((v["value"] for v in reversed(zScore) if v["value"] is not None), None)
    if latest is None:
        zone = "판별 불가"
    elif latest > 2.99:
        zone = "안전 구간"
    elif latest > 1.81:
        zone = "회색 구간"
    else:
        zone = "위험 구간"

    return {"altmanZScore": zScore, "latestScore": latest, "zone": zone}


def calcDistressEnsemble(company) -> dict | None:
    """4개 부실예측 모델 앙상블 -- 다수결 투표.

    Altman Z-Score, Ohlson O-Score, Springate S-Score, Zmijewski X-Score
    각 모델의 판정(safe/warning/danger)을 집계하여 종합 등급 산출.
    """
    ratios = getRatios(company)
    if ratios is None:
        return None

    models = []

    # Altman Z-Score: >2.99 safe, 1.81~2.99 gray, <1.81 danger
    z = ratios.altmanZScore
    if z is not None:
        if z > 2.99:
            verdict = "safe"
        elif z > 1.81:
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

    # Altman Z'' (비제조/신흥): >2.60 safe, 1.10~2.60 gray, <1.10 danger
    zpp = ratios.altmanZppScore
    if zpp is not None:
        if zpp > 2.60:
            verdict = "safe"
        elif zpp > 1.10:
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


def calcDebtMaturity(company) -> dict | None:
    """부채 만기 구조 분석.

    단기/장기 차입금 비율, 차환 리스크 지표.
    """
    bsResult = company.select(
        "BS",
        [
            "단기차입금",
            "장기차입금",
            "사채",
            "차입부채",
            "발행사채",
            "유동금융부채",
            "장기금융부채",
            "유동부채",
            "비유동부채",
            "부채총계",
        ],
    )
    parsed = toDict(bsResult, maxPeriods=5)
    if parsed is None:
        return None

    data, periods = parsed
    # 일반 제조업
    stRow = data.get("단기차입금", {})
    ltRow = data.get("장기차입금", {})
    bondsRow = data.get("사채", {})
    # 금융업
    borrowRow = data.get("차입부채", {})
    issuedBondRow = data.get("발행사채", {})
    # 바이오 등
    curFinRow = data.get("유동금융부채", {})
    ltFinRow = data.get("장기금융부채", {})

    clRow = data.get("유동부채", {})
    nclRow = data.get("비유동부채", {})
    tlRow = data.get("부채총계", {})

    # 연도 컬럼만
    annualPeriods = sorted([p for p in periods if "Q" not in p])
    if not annualPeriods:
        annualPeriods = sorted([p for p in periods if p.endswith("Q4")])
    annualPeriods = annualPeriods[-5:]

    # OCF for 차환능력 평가
    cfResult = company.select("CF", ["영업활동현금흐름"])
    cfParsed = toDict(cfResult, maxPeriods=5) if cfResult else None
    cfData = cfParsed[0] if cfParsed else {}
    ocfRow = cfData.get("영업활동현금흐름", {})

    history = []
    for col in reversed(annualPeriods):
        # 차입금: 업종별 계정 대응
        st = stRow.get(col) or 0
        lt = ltRow.get(col) or 0
        bonds = bondsRow.get(col) or 0
        totalBorrowing = st + lt + bonds

        # 금융업 fallback
        if totalBorrowing == 0:
            borrow = borrowRow.get(col) or 0
            issued = issuedBondRow.get(col) or 0
            totalBorrowing = borrow + issued
            st = borrow  # 금융업 차입부채를 단기로 근사
            lt = issued

        # 바이오 등 fallback
        if totalBorrowing == 0:
            curFin = curFinRow.get(col) or 0
            ltFin = ltFinRow.get(col) or 0
            totalBorrowing = curFin + ltFin
            st = curFin
            lt = ltFin

        cl = clRow.get(col) or 0
        tl = tlRow.get(col) or 0
        ocf = ocfRow.get(col)

        shortTermRatio = round(st / totalBorrowing * 100, 2) if totalBorrowing > 0 else None
        currentToTotal = round(cl / tl * 100, 2) if tl > 0 else None

        # 단기차입금/OCF = 차환능력 (낮을수록 안전)
        refinancingRisk = None
        if ocf is not None and ocf > 0 and st > 0:
            refinancingRisk = round(st / ocf, 2)

        history.append(
            {
                "period": col,
                "shortTermBorrowing": st,
                "longTermBorrowing": lt,
                "bonds": bonds,
                "totalBorrowing": totalBorrowing,
                "shortTermRatio": shortTermRatio,
                "currentToTotalDebt": currentToTotal,
                "refinancingRisk": refinancingRisk,
            }
        )

    return {"history": history} if history else None


def calcStabilityFlags(company) -> list[str]:
    """안정성 경고/기회 플래그."""
    flags: list[str] = []
    result = getRatioSeries(company)
    if result is None:
        return flags

    data, _years = result

    # 부채비율
    dr = data.get("RATIO", {}).get("debtRatio", [])
    latestDr = next((v for v in reversed(dr) if v is not None), None)
    if latestDr is not None:
        if latestDr > 200:
            flags.append(f"부채비율 {latestDr:.0f}% -- 재무 위험")
        elif latestDr < 50:
            flags.append(f"부채비율 {latestDr:.0f}% -- 매우 안정")

    # 이자보상배율
    ic = data.get("RATIO", {}).get("interestCoverage", [])
    latestIc = next((v for v in reversed(ic) if v is not None), None)
    if latestIc is not None:
        if latestIc < 1:
            flags.append(f"이자보상배율 {latestIc:.1f}배 -- 이자 지급 불능 위험")
        elif latestIc < 3:
            flags.append(f"이자보상배율 {latestIc:.1f}배 -- 이자 부담 과다")

    # Altman Z-Score
    z = data.get("RATIO", {}).get("altmanZScore", [])
    latestZ = next((v for v in reversed(z) if v is not None), None)
    if latestZ is not None and latestZ < 1.81:
        flags.append(f"Altman Z-Score {latestZ:.2f} -- 부실 위험 구간")

    return flags
