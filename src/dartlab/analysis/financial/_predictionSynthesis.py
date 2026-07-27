"""analysis/financial/predictionSignals 종합 + flags 함수 분리.

predictionSignals.py 가 2430 줄 god module 이라 다중 신호 종합 + flag 산출 분리.
identity 보존을 위해 predictionSignals.py 가 본 모듈에서 re-export 한다.

함수:
- calcPredictionSynthesis — 5 신호 단순 평균 앙상블 (Green & Armstrong 2015)
- calcPredictionFlags — 위험/기회 플래그 산출
"""

from __future__ import annotations

import logging
import math

from dartlab.analysis.financial._predictionProbability import _DIRECTION_SCORES, _clamp
from dartlab.core.memory import memoizedCalc

log = logging.getLogger(__name__)


def _lazy(name):
    """Lazy lookup — predictionSignals 본체 import 회피 (순환 방지)."""
    import importlib

    return getattr(importlib.import_module("dartlab.analysis.financial.predictionSignals"), name)


def calcEarningsMomentum(*args, **kwargs) -> dict | None:
    """predictionSignals.calcEarningsMomentum lazy proxy — 본체로 위임.

    Requires:
        predictionSignals 본체 모듈 import 가능.

    Raises:
        없음 — 본체 위임.

    Example:
        >>> calcEarningsMomentum(company)["momentum"]
        0.18
    """
    return _lazy("calcEarningsMomentum")(*args, **kwargs)


def calcPeerPrediction(*args, **kwargs) -> dict | None:
    """predictionSignals.calcPeerPrediction lazy proxy — 본체로 위임.

    Requires:
        predictionSignals 본체 import.

    Raises:
        없음.

    Example:
        >>> calcPeerPrediction(company)["peerScore"]
        0.62
    """
    return _lazy("calcPeerPrediction")(*args, **kwargs)


def calcStructuralBreak(*args, **kwargs) -> dict | None:
    """predictionSignals.calcStructuralBreak lazy proxy — 본체로 위임.

    Requires:
        predictionSignals 본체 import.

    Raises:
        없음.

    Example:
        >>> calcStructuralBreak(company)["isBreak"]
        True
    """
    return _lazy("calcStructuralBreak")(*args, **kwargs)


def calcMacroSensitivity(*args, **kwargs) -> dict | None:
    """predictionSignals.calcMacroSensitivity lazy proxy — 본체로 위임.

    Requires:
        predictionSignals 본체 import.

    Raises:
        없음.

    Example:
        >>> calcMacroSensitivity(company)["score"]
        0.4
    """
    return _lazy("calcMacroSensitivity")(*args, **kwargs)


def calcMacroRegression(*args, **kwargs) -> dict | None:
    """predictionSignals.calcMacroRegression lazy proxy — 본체로 위임.

    Requires:
        predictionSignals 본체 import.

    Raises:
        없음.

    Example:
        >>> calcMacroRegression(company)["coefficients"]
        {...}
    """
    return _lazy("calcMacroRegression")(*args, **kwargs)


def calcEventImpact(*args, **kwargs) -> dict | None:
    """predictionSignals.calcEventImpact lazy proxy — 본체로 위임.

    Requires:
        predictionSignals 본체 import.

    Raises:
        없음.

    Example:
        >>> calcEventImpact(company)["impact"]
        0.5
    """
    return _lazy("calcEventImpact")(*args, **kwargs)


def calcDisclosureDelta(*args, **kwargs) -> dict | None:
    """predictionSignals.calcDisclosureDelta lazy proxy — 본체로 위임.

    Requires:
        predictionSignals 본체 import.

    Raises:
        없음.

    Example:
        >>> calcDisclosureDelta(company)["delta"]
        0.3
    """
    return _lazy("calcDisclosureDelta")(*args, **kwargs)


def calcInventoryDivergence(*args, **kwargs) -> dict | None:
    """predictionSignals.calcInventoryDivergence lazy proxy — 본체로 위임.

    Requires:
        predictionSignals 본체 import.

    Raises:
        없음.

    Example:
        >>> calcInventoryDivergence(company)["divergence"]
        -0.2
    """
    return _lazy("calcInventoryDivergence")(*args, **kwargs)


def calcAnnouncementTiming(*args, **kwargs) -> dict | None:
    """predictionSignals.calcAnnouncementTiming lazy proxy — 본체로 위임.

    Requires:
        predictionSignals 본체 import.

    Raises:
        없음.

    Example:
        >>> calcAnnouncementTiming(company)["score"]
        0.1
    """
    return _lazy("calcAnnouncementTiming")(*args, **kwargs)


def calcSupplyChainSignal(*args, **kwargs) -> dict | None:
    """predictionSignals.calcSupplyChainSignal lazy proxy — 본체로 위임.

    Requires:
        predictionSignals 본체 import.

    Raises:
        없음.

    Example:
        >>> calcSupplyChainSignal(company)["score"]
        0.0
    """
    return _lazy("calcSupplyChainSignal")(*args, **kwargs)


def calcConsensusDirection(*args, **kwargs) -> dict | None:
    """predictionSignals.calcConsensusDirection lazy proxy — 본체로 위임.

    Requires:
        predictionSignals 본체 import.

    Raises:
        없음.

    Example:
        >>> calcConsensusDirection(company)["direction"]
        'up'
    """
    return _lazy("calcConsensusDirection")(*args, **kwargs)


def calcFlowDirection(*args, **kwargs) -> dict | None:
    """predictionSignals.calcFlowDirection lazy proxy — 본체로 위임.

    Requires:
        predictionSignals 본체 import.

    Raises:
        없음.

    Example:
        >>> calcFlowDirection(company)["direction"]
        'inflow'
    """
    return _lazy("calcFlowDirection")(*args, **kwargs)


def calcRevenueDirection(*args, **kwargs) -> dict | None:
    """predictionSignals.calcRevenueDirection lazy proxy — 본체로 위임.

    Requires:
        predictionSignals 본체 import.

    Raises:
        없음.

    Example:
        >>> calcRevenueDirection(company)["direction"]
        'up'
    """
    return _lazy("calcRevenueDirection")(*args, **kwargs)


@memoizedCalc
def calcPredictionSynthesis(company, *, basePeriod: str | None = None) -> dict | None:
    """다중 신호 종합 — 5개 신호의 단순 평균 앙상블.

    학술 근거: 32편 논문, 97개 비교에서 단순 평균이 최적 (Green & Armstrong 2015).

    Returns
    -------
    dict
        signals : dict — 신호별 상세 (direction, strength, 개별 지표)
        consensus : str — 종합 합의 ("bullish" | "bearish" | "neutral")
        directionScore : float — 방향 점수 (-1.0 ~ +1.0)
        agreementScore : float — 신호 합의도 (0.0 ~ 1.0)
        confidence : str — 신뢰도 ("high" | "medium" | "low")
        nSignals : int — 유효 신호 수
        revenuePrediction : dict | None — 매출 방향 예측 (direction, confidence, streak, expectedAccuracy(%))
        aiContext : dict — AI 소비용 요약 (directionBias, keyDrivers, keyRisks)

    Capabilities:
        - 13 sub-신호 (earnings momentum/peer/structural/macro 등) 단순 평균 → consensus + direction
        - agreementScore 로 신호 합의도 측정 + confidence 분류

    Guide:
        Green-Armstrong 2015 단순 평균이 32 편 논문 97 비교에서 최적. 가중평균 < 평균.

    When:
        analysis 예측 종합 + AI 미래 방향 답변.

    How:
        13 sub-calc 호출 → direction score 평균 → agreement + confidence.

    Requires:
        company + 13 sub-calc 가용 (대부분 best-effort).

    Raises:
        없음 — sub-calc None 일 때 skip.

    Example:
        >>> calcPredictionSynthesis(company)["consensus"]
        'bullish'

    See Also:
        - calcPredictionFlags : 위험/기회 플래그
        - predictionSignals : sub-신호 본체

    AIContext:
        "이 종목 방향 종합 예측" 답변 시 consensus + directionScore + keyDrivers 인용.
    """
    # 각 calc 독립 호출 (company._cache로 중복 방지는 호출자 레벨)
    momentum = calcEarningsMomentum(company, basePeriod=basePeriod)
    peer = calcPeerPrediction(company, basePeriod=basePeriod)
    structural = calcStructuralBreak(company, basePeriod=basePeriod)
    macro = calcMacroSensitivity(company, basePeriod=basePeriod)
    macroReg = calcMacroRegression(company, basePeriod=basePeriod)
    eventImp = calcEventImpact(company, basePeriod=basePeriod)
    disclosure = calcDisclosureDelta(company, basePeriod=basePeriod)
    inventory = calcInventoryDivergence(company, basePeriod=basePeriod)
    timing = calcAnnouncementTiming(company, basePeriod=basePeriod)
    supplyChain = calcSupplyChainSignal(company, basePeriod=basePeriod)

    signals = {}
    scores = []

    # 1. 이익 모멘텀 신호
    if momentum is not None:
        dirKey = momentum["earningsDirection"]
        score = _DIRECTION_SCORES.get(dirKey, 0.0)
        signals["earningsMomentum"] = {
            "direction": dirKey,
            "strength": abs(score),
            "detail": momentum["momentum"],
            "persistence": momentum["persistenceScore"],
        }
        scores.append(score)

    # 2. 피어 예측 신호
    if peer is not None and peer.get("divergence") is not None:
        div = peer["divergence"]
        if div > 5:
            peerDir = "positive"
            peerScore = min(1.0, div / 20)
        elif div < -5:
            peerDir = "negative"
            peerScore = max(-1.0, div / 20)
        else:
            peerDir = "neutral"
            peerScore = 0.0
        signals["peerPrediction"] = {
            "direction": peerDir,
            "strength": abs(peerScore),
            "divergence": peer["divergence"],
        }
        scores.append(peerScore)

    # 3. 구조변화 신호
    if structural is not None:
        stabDir = structural["overallStability"]
        stabScore = _DIRECTION_SCORES.get(stabDir, 0.0)
        signals["structuralBreak"] = {
            "direction": stabDir,
            "strength": abs(stabScore),
            "nBreaks": sum(1 for m in structural["metrics"] if m["hasBreak"]),
        }
        scores.append(stabScore)

    # 4. 거시경제 신호 (방향성은 중립 — 조건부 위험 지표)
    if macro is not None:
        cyclicality = macro["sectorCyclicality"]
        _DIRECTION_SCORES.get(cyclicality, 0.0) if cyclicality == "defensive" else 0.0
        signals["macroSensitivity"] = {
            "direction": cyclicality,
            "strength": 0.0,
            "cyclicality": cyclicality,
            "relevantIndicators": macro.get("relevantIndicators", []),
        }
        # 매크로는 방향 점수에 포함하지 않음 (조건부 지표)

    # 5. 공시 변화 신호
    if disclosure is not None:
        discDir = disclosure["signalDirection"]
        discScore = _DIRECTION_SCORES.get(discDir, 0.0)
        signals["disclosureDelta"] = {
            "direction": discDir,
            "strength": abs(discScore),
            "overallChange": disclosure["overallChangeRate"],
        }
        scores.append(discScore)

    # 5b. 거시-재무 동적 회귀 신호
    if macroReg is not None and macroReg.get("rSquared", 0) > 0.1:
        # netMacroEffect가 있으면 사용, 없으면 betas에서 추정
        netEffect = macro.get("netMacroEffect", 0) if macro else 0
        macroRegScore = _clamp(netEffect / 10)  # ±10% → ±1.0
        macroRegDir = "positive" if macroRegScore > 0.15 else ("negative" if macroRegScore < -0.15 else "neutral")
        signals["macroRegression"] = {
            "direction": macroRegDir,
            "strength": abs(macroRegScore),
            "rSquared": macroReg["rSquared"],
            "confidence": macroReg["confidence"],
            "nObs": macroReg["nObs"],
        }
        scores.append(macroRegScore)

    # 5c. 이벤트 충격 신호
    if eventImp is not None:
        resilience = eventImp.get("resilience", "medium")
        nEvents = len(eventImp.get("events", []))
        if resilience == "low" and nEvents > 0:
            eventScore = -0.5
            eventDir = "negative"
        elif resilience == "high":
            eventScore = 0.2
            eventDir = "positive"
        else:
            eventScore = 0.0
            eventDir = "neutral"
        signals["eventImpact"] = {
            "direction": eventDir,
            "strength": abs(eventScore),
            "resilience": resilience,
            "nEvents": nEvents,
            "avgRecoveryYears": eventImp.get("avgRecoveryYears"),
        }
        if nEvents > 0:
            scores.append(eventScore)

    # 6. 재고/매출채권 괴리 신호
    if inventory is not None:
        risk = inventory["riskScore"]
        invScore = -(risk - 50) / 50  # 50 이하=긍정, 50 이상=부정
        invDir = "negative" if risk > 60 else ("positive" if risk < 30 else "neutral")
        signals["inventoryDivergence"] = {
            "direction": invDir,
            "strength": abs(invScore),
            "riskScore": risk,
            "inventorySignal": inventory["inventorySignal"],
            "receivableSignal": inventory["receivableSignal"],
        }
        scores.append(invScore)

    # 7. 공시 타이밍 신호
    if timing is not None:
        timingScore = timing["peerConsensus"]
        timingDir = "positive" if timingScore > 0.2 else ("negative" if timingScore < -0.2 else "neutral")
        signals["announcementTiming"] = {
            "direction": timingDir,
            "strength": abs(timingScore),
            "peerConsensus": timing["peerConsensus"],
            "bellwether": timing["bellwetherSignal"],
            "peersReported": timing["sectorPeersReported"],
        }
        scores.append(timingScore)

    # 8. 공급망 모멘텀 신호
    if supplyChain is not None:
        scScore = supplyChain["networkMomentum"]
        scDir = "positive" if scScore > 0.15 else ("negative" if scScore < -0.15 else "neutral")
        signals["supplyChain"] = {
            "direction": scDir,
            "strength": abs(scScore),
            "networkMomentum": supplyChain["networkMomentum"],
            "nLinked": supplyChain["nLinkedListed"],
            "risk": supplyChain["supplyChainRisk"],
        }
        scores.append(scScore)

    # 9. 컨센서스 매출 방향
    consensus = calcConsensusDirection(company, basePeriod=basePeriod)
    if consensus is not None:
        cnsDir = consensus["direction"]
        cnsScore = _DIRECTION_SCORES.get(cnsDir, 0.0)
        signals["consensusDirection"] = {
            "direction": cnsDir,
            "strength": abs(cnsScore),
            "expectedGrowth": consensus["expectedGrowthPct"],
            "confidence": consensus["confidence"],
        }
        scores.append(cnsScore)

    # 10. 수급 누적 방향
    flowDir = calcFlowDirection(company, basePeriod=basePeriod)
    if flowDir is not None:
        fDir = flowDir["direction"]
        fScore = _DIRECTION_SCORES.get(fDir, 0.0)
        signals["flowDirection"] = {
            "direction": fDir,
            "strength": abs(fScore),
            "smartMoneyNet": flowDir["smartMoneyNet"],
            "confidence": flowDir["confidence"],
        }
        scores.append(fScore)

    # 11. 매출 모멘텀 (전분기 방향 유지)
    revDir = calcRevenueDirection(company, basePeriod=basePeriod)
    if revDir is not None:
        rDir = revDir["direction"]
        rScore = _DIRECTION_SCORES.get(rDir, 0.0)
        signals["revenueDirection"] = {
            "direction": rDir,
            "strength": abs(rScore),
            "latestYoyGrowth": revDir["latestYoyGrowth"],
            "streak": revDir["streak"],
            "confidence": revDir["confidence"],
        }
        scores.append(rScore)

    if not scores:
        return None

    # 단순 평균 (학술적 최적)
    avgScore = sum(scores) / len(scores)

    if avgScore > 0.25:
        consensus = "bullish"
    elif avgScore < -0.25:
        consensus = "bearish"
    else:
        consensus = "neutral"

    # 신호 합의도 (표준편차 기반)
    if len(scores) >= 2:
        mean = avgScore
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std = math.sqrt(variance)
        agreementScore = max(0, 1.0 - std)
    else:
        agreementScore = 0.5

    # 신뢰도
    nSignals = len(scores)
    if nSignals >= 4 and agreementScore > 0.6:
        confidence = "high"
    elif nSignals >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    # AI/forecast 엔진 소비용 요약
    keyDrivers = []
    keyRisks = []
    for name, sig in signals.items():
        if sig.get("direction") in ("up", "positive", "accelerating"):
            keyDrivers.append(name)
        elif sig.get("direction") in ("down", "negative", "decelerating", "volatile"):
            keyRisks.append(name)

    # 매출 방향 예측 (모멘텀 기반 — 검증 정확도 71.3%)
    revPrediction = None
    if revDir is not None:
        revPrediction = {
            "direction": revDir["direction"],
            "confidence": revDir["confidence"],
            "streak": revDir["streak"],
            "olsAgree": revDir.get("olsAgree"),
            "expectedAccuracy": (
                77.7
                if revDir.get("olsAgree") and revDir["streak"] >= 2
                else 74.7
                if revDir["streak"] >= 2
                else 77.7
                if revDir.get("olsAgree")
                else 71.3
            ),
        }

    return {
        "signals": signals,
        "consensus": consensus,
        "directionScore": round(avgScore, 3),
        "agreementScore": round(agreementScore, 3),
        "confidence": confidence,
        "nSignals": nSignals,
        "revenuePrediction": revPrediction,
        "aiContext": {
            "directionBias": round(avgScore, 3),
            "keyDrivers": keyDrivers,
            "keyRisks": keyRisks,
        },
    }


# ══════════════════════════════════════
# calc 7: 예측신호 플래그
# ══════════════════════════════════════


@memoizedCalc
def calcPredictionFlags(company, *, basePeriod: str | None = None) -> list[tuple[str, str]] | None:
    """예측신호 경고 플래그.

    Returns
    -------
    list[tuple[str, str]] | None
        (코드, 메시지) 튜플 목록. 코드는 EARN_DECEL, HIGH_ACCRUAL 등 플래그 ID.
        플래그가 없으면 None.

    Capabilities:
        - 13 신호 결과 → 위험/기회 플래그 (EARN_DECEL/HIGH_ACCRUAL/STRUCT_VOLATILE 등) list
        - 코드 + 한 줄 메시지 tuple

    Guide:
        story flag 박스 + AI 위험 경고 답변 표준 입력. flag ≥ 3 = 복합 위험.

    When:
        Story flag + AI 사전 경고 답변.

    How:
        13 sub-calc 결과 임계 비교 → 위반 시 tuple 누적.

    Requires:
        sub-calc 가용.

    Raises:
        없음.

    Example:
        >>> calcPredictionFlags(company)
        [('EARN_DECEL', '이익 감속 ...'), ('HIGH_ACCRUAL', '...')]

    See Also:
        - calcPredictionSynthesis : 종합 score
        - story.bridges.alerts : flag 소비

    AIContext:
        "이 종목 사전 경고" 답변 시 flag list 인용.
    """
    flags = []

    # 이익 모멘텀
    momentum = calcEarningsMomentum(company, basePeriod=basePeriod)
    if momentum:
        if momentum["momentum"] == "decelerating":
            flags.append(("EARN_DECEL", "이익 감속 추세 — 최근 3년 연속 감소"))
        if momentum["highAccrualWarning"]:
            flags.append(("HIGH_ACCRUAL", "높은 발생액 비율 — 이익의 현금 뒷받침 약함"))
        if momentum["persistenceScore"] < 30:
            flags.append(("LOW_PERSIST", "낮은 이익 지속성 — OCF/NI 비율 낮음"))

    # 구조변화
    structural = calcStructuralBreak(company, basePeriod=basePeriod)
    if structural:
        if structural["overallStability"] == "volatile":
            flags.append(("STRUCT_VOLATILE", "다수 지표에서 구조변화 감지 — 추세 추정 신뢰도 낮음"))
        for m in structural["metrics"]:
            if m["hasBreak"] and m["name"] == "revenue":
                flags.append(("REV_BREAK", f"매출 구조변화 감지 ({m['breakYear']})"))

    # 공시 변화
    disclosure = calcDisclosureDelta(company, basePeriod=basePeriod)
    if disclosure:
        if disclosure["riskChangeRate"] > 60:
            flags.append(("RISK_SURGE", f"리스크 공시 급변 ({disclosure['riskChangeRate']:.0f}%)"))
        if disclosure["signalDirection"] == "negative" and disclosure["signalStrength"] == "strong":
            flags.append(("DISC_NEGATIVE", "공시 변화 부정적 신호 — 리스크 섹션 대폭 확대"))

    # 피어 괴리
    peer = calcPeerPrediction(company, basePeriod=basePeriod)
    if peer and peer.get("divergence") is not None:
        if peer["divergence"] < -15:
            flags.append(("PEER_BELOW", f"피어 대비 {peer['divergence']:+.1f}%p 하회 예측"))
        elif peer["divergence"] > 15:
            flags.append(("PEER_ABOVE", f"피어 대비 {peer['divergence']:+.1f}%p 상회 예측"))

    # 거시-재무 회귀
    macroReg = calcMacroRegression(company, basePeriod=basePeriod)
    if macroReg:
        if macroReg["rSquared"] > 0.3 and macroReg["confidence"] in ("high", "medium"):
            betas = macroReg.get("betas", {})
            for indicator, beta in betas.items():
                if abs(beta) > 2.0:
                    flags.append(("MACRO_HIGH_BETA", f"거시 베타 높음: {indicator} β={beta:+.1f}"))

    # 이벤트 충격
    eventImp = calcEventImpact(company, basePeriod=basePeriod)
    if eventImp:
        if eventImp.get("resilience") == "low":
            flags.append(("LOW_RESILIENCE", f"충격 회복력 낮음 (평균 {eventImp.get('avgRecoveryYears', '?')}년)"))
        nEvents = len(eventImp.get("events", []))
        if nEvents >= 3:
            flags.append(("FREQUENT_EVENTS", f"최근 충격 이벤트 {nEvents}건"))

    # 재고/매출채권 괴리
    inventory = calcInventoryDivergence(company, basePeriod=basePeriod)
    if inventory:
        if inventory["riskScore"] > 70:
            flags.append(("INV_HIGH_RISK", f"재고/매출채권 위험 점수 {inventory['riskScore']}"))
        if inventory["inventorySignal"] == "building":
            h = inventory["history"]
            div = h[0]["divergence"] if h and h[0].get("divergence") is not None else 0
            flags.append(("INV_DIVERGE", f"재고 급증 vs 매출 (괴리 {div:+.1f}%p)"))
        if inventory["receivableSignal"] == "deteriorating":
            flags.append(("DSO_SPIKE", "매출채권 회수 악화 — 매출 대비 채권 급증"))
        if inventory["noaGrowth"] is not None and inventory["noaGrowth"] > 20:
            flags.append(("NOA_SURGE", f"순영업자산 급증 {inventory['noaGrowth']:+.1f}%"))

    # 업종 타이밍
    timing = calcAnnouncementTiming(company, basePeriod=basePeriod)
    if timing:
        dirs = timing["reportedDirection"]
        total = sum(dirs.values())
        if total >= 3 and dirs["down"] / total >= 0.7:
            flags.append(("SECTOR_DOWNTURN", f"업종 {dirs['down']}/{total} 기업 실적 하락"))

    # 공급망 리스크
    sc = calcSupplyChainSignal(company, basePeriod=basePeriod)
    if sc:
        if sc["supplyChainRisk"] == "high":
            flags.append(("NETWORK_RISK", f"관계사 {sc['nLinkedListed']}개 중 다수 실적 악화"))

    return flags if flags else None


__all__ = ["calcPredictionFlags", "calcPredictionSynthesis"]
