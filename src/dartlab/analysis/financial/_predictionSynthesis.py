"""analysis/financial/predictionSignals 종합 + flags 함수 분리.

predictionSignals.py 가 2430 줄 god module 이라 다중 신호 종합 + flag 산출 분리.
identity 보존을 위해 predictionSignals.py 가 본 모듈에서 re-export 한다.

함수:
- calcPredictionSynthesis. 5 신호 단순 평균 앙상블 (Green & Armstrong 2015)
- calcPredictionFlags. 위험/기회 플래그 산출
"""

from __future__ import annotations

import logging
import math

from dartlab.analysis.financial import _predictionFlagRules as rules
from dartlab.analysis.financial._predictionProbability import _DIRECTION_SCORES, _clamp
from dartlab.core.memory import memoizedCalc

log = logging.getLogger(__name__)


def _lazy(name):
    """Lazy lookup. predictionSignals 본체 import 회피 (순환 방지)."""
    import importlib

    return getattr(importlib.import_module("dartlab.analysis.financial.predictionSignals"), name)


def calcEarningsMomentum(*args, **kwargs) -> dict | None:
    """predictionSignals.calcEarningsMomentum lazy proxy. 본체로 위임.

    Requires:
        predictionSignals 본체 모듈 import 가능.

    Raises:
        없음. 본체 위임.

    Example:
        >>> calcEarningsMomentum(company)["momentum"]
        0.18
    """
    return _lazy("calcEarningsMomentum")(*args, **kwargs)


def calcPeerPrediction(*args, **kwargs) -> dict | None:
    """predictionSignals.calcPeerPrediction lazy proxy. 본체로 위임.

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
    """predictionSignals.calcStructuralBreak lazy proxy. 본체로 위임.

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
    """predictionSignals.calcMacroSensitivity lazy proxy. 본체로 위임.

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
    """predictionSignals.calcMacroRegression lazy proxy. 본체로 위임.

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
    """predictionSignals.calcEventImpact lazy proxy. 본체로 위임.

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
    """predictionSignals.calcDisclosureDelta lazy proxy. 본체로 위임.

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
    """predictionSignals.calcInventoryDivergence lazy proxy. 본체로 위임.

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
    """predictionSignals.calcAnnouncementTiming lazy proxy. 본체로 위임.

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
    """predictionSignals.calcSupplyChainSignal lazy proxy. 본체로 위임.

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
    """predictionSignals.calcConsensusDirection lazy proxy. 본체로 위임.

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
    """predictionSignals.calcFlowDirection lazy proxy. 본체로 위임.

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
    """predictionSignals.calcRevenueDirection lazy proxy. 본체로 위임.

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
    """다중 신호 종합. 5개 신호의 단순 평균 앙상블.

    학술 근거: 32편 논문, 97개 비교에서 단순 평균이 최적 (Green & Armstrong 2015).

    Returns
    -------
    dict
        signals : dict. 신호별 상세 (direction, strength, 개별 지표)
        consensus : str. 종합 합의 ("bullish" | "bearish" | "neutral")
        directionScore : float. 방향 점수 (-1.0 ~ +1.0)
        agreementScore : float. 신호 합의도 (0.0 ~ 1.0)
        confidence : str. 신뢰도 ("high" | "medium" | "low")
        nSignals : int. 유효 신호 수
        revenuePrediction : dict | None. 매출 방향 예측 (direction, confidence, streak, expectedAccuracy(%))
        aiContext : dict. AI 소비용 요약 (directionBias, keyDrivers, keyRisks)

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
        없음. sub-calc None 일 때 skip.

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

    # 신호 1~8. 각 빌더는 (신호 dict, 방향 점수 또는 None) 또는 None 을 낸다.
    # 나열 순서가 곧 signals dict 삽입 순서이자 scores 누적 순서다 (평균 합산 순서 보존).
    signals: dict[str, dict] = {}
    scores: list[float] = []
    for key, built in (
        ("earningsMomentum", _earningsMomentumSignal(momentum)),
        ("peerPrediction", _peerPredictionSignal(peer)),
        ("structuralBreak", _structuralBreakSignal(structural)),
        ("macroSensitivity", _macroSensitivitySignal(macro)),
        ("disclosureDelta", _disclosureDeltaSignal(disclosure)),
        ("macroRegression", _macroRegressionSignal(macroReg, macro)),
        ("eventImpact", _eventImpactSignal(eventImp)),
        ("inventoryDivergence", _inventoryDivergenceSignal(inventory)),
        ("announcementTiming", _announcementTimingSignal(timing)),
        ("supplyChain", _supplyChainSignal(supplyChain)),
    ):
        _mergeSignal(signals, scores, key, built)

    # 9~11 번은 여기서 호출한다. 앞 신호 조립이 끝난 뒤에 부르는 원본 순서를 유지해야
    # 조립 중 예외가 나면 뒤 sub-calc 를 부르지 않는 동작이 같다.
    _mergeSignal(
        signals,
        scores,
        "consensusDirection",
        _consensusDirectionSignal(calcConsensusDirection(company, basePeriod=basePeriod)),
    )
    _mergeSignal(
        signals,
        scores,
        "flowDirection",
        _flowDirectionSignal(calcFlowDirection(company, basePeriod=basePeriod)),
    )
    revDir = calcRevenueDirection(company, basePeriod=basePeriod)
    _mergeSignal(signals, scores, "revenueDirection", _revenueDirectionSignal(revDir))

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

    agreementScore = _agreementScore(scores, avgScore)
    nSignals = len(scores)
    keyDrivers, keyRisks = _driversAndRisks(signals)

    return {
        "signals": signals,
        "consensus": consensus,
        "directionScore": round(avgScore, 3),
        "agreementScore": round(agreementScore, 3),
        "confidence": _confidenceLabel(nSignals, agreementScore),
        "nSignals": nSignals,
        "revenuePrediction": _revenuePrediction(revDir),
        "aiContext": {
            "directionBias": round(avgScore, 3),
            "keyDrivers": keyDrivers,
            "keyRisks": keyRisks,
        },
    }


def _mergeSignal(signals: dict, scores: list, key: str, built: tuple | None) -> None:
    """신호 하나를 dict 에 얹고, 방향 점수가 있으면 앙상블 표본에 넣는다."""
    if built is None:
        return
    payload, score = built
    signals[key] = payload
    if score is not None:
        scores.append(score)


def _earningsMomentumSignal(momentum) -> tuple[dict, float] | None:
    """신호 1: 이익 모멘텀."""
    if momentum is None:
        return None
    dirKey = momentum["earningsDirection"]
    score = _DIRECTION_SCORES.get(dirKey, 0.0)
    return {
        "direction": dirKey,
        "strength": abs(score),
        "detail": momentum["momentum"],
        "persistence": momentum["persistenceScore"],
    }, score


def _peerPredictionSignal(peer) -> tuple[dict, float] | None:
    """신호 2: 피어 대비 괴리. ±5%p 밴드 밖만 방향으로 읽는다."""
    if peer is None or peer.get("divergence") is None:
        return None
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
    return {
        "direction": peerDir,
        "strength": abs(peerScore),
        "divergence": peer["divergence"],
    }, peerScore


def _structuralBreakSignal(structural) -> tuple[dict, float] | None:
    """신호 3: 구조변화."""
    if structural is None:
        return None
    stabDir = structural["overallStability"]
    stabScore = _DIRECTION_SCORES.get(stabDir, 0.0)
    return {
        "direction": stabDir,
        "strength": abs(stabScore),
        "nBreaks": sum(1 for m in structural["metrics"] if m["hasBreak"]),
    }, stabScore


def _macroSensitivitySignal(macro) -> tuple[dict, None] | None:
    """신호 4: 거시경제. 조건부 위험 지표라 방향 점수에는 넣지 않는다 (score=None)."""
    if macro is None:
        return None
    cyclicality = macro["sectorCyclicality"]
    return {
        "direction": cyclicality,
        "strength": 0.0,
        "cyclicality": cyclicality,
        "relevantIndicators": macro.get("relevantIndicators", []),
    }, None


def _disclosureDeltaSignal(disclosure) -> tuple[dict, float] | None:
    """신호 5: 공시 변화."""
    if disclosure is None:
        return None
    discDir = disclosure["signalDirection"]
    discScore = _DIRECTION_SCORES.get(discDir, 0.0)
    return {
        "direction": discDir,
        "strength": abs(discScore),
        "overallChange": disclosure["overallChangeRate"],
    }, discScore


def _macroRegressionSignal(macroReg, macro) -> tuple[dict, float] | None:
    """신호 5b: 거시-재무 동적 회귀. 설명력이 낮으면(rSquared<=0.1) 신호로 세우지 않는다."""
    if macroReg is None or not (macroReg.get("rSquared", 0) > 0.1):
        return None
    # netMacroEffect가 있으면 사용, 없으면 betas에서 추정
    netEffect = macro.get("netMacroEffect", 0) if macro else 0
    macroRegScore = _clamp(netEffect / 10)  # ±10% → ±1.0
    macroRegDir = "positive" if macroRegScore > 0.15 else ("negative" if macroRegScore < -0.15 else "neutral")
    return {
        "direction": macroRegDir,
        "strength": abs(macroRegScore),
        "rSquared": macroReg["rSquared"],
        "confidence": macroReg["confidence"],
        "nObs": macroReg["nObs"],
    }, macroRegScore


def _eventImpactSignal(eventImp) -> tuple[dict, float | None] | None:
    """신호 5c: 이벤트 충격. 이벤트가 0 건이면 신호는 남기고 점수만 뺀다."""
    if eventImp is None:
        return None
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
    payload = {
        "direction": eventDir,
        "strength": abs(eventScore),
        "resilience": resilience,
        "nEvents": nEvents,
        "avgRecoveryYears": eventImp.get("avgRecoveryYears"),
    }
    return payload, (eventScore if nEvents > 0 else None)


def _inventoryDivergenceSignal(inventory) -> tuple[dict, float] | None:
    """신호 6: 재고/매출채권 괴리. riskScore 50 을 중립축으로 부호를 뒤집는다."""
    if inventory is None:
        return None
    risk = inventory["riskScore"]
    invScore = -(risk - 50) / 50  # 50 이하=긍정, 50 이상=부정
    invDir = "negative" if risk > 60 else ("positive" if risk < 30 else "neutral")
    return {
        "direction": invDir,
        "strength": abs(invScore),
        "riskScore": risk,
        "inventorySignal": inventory["inventorySignal"],
        "receivableSignal": inventory["receivableSignal"],
    }, invScore


def _announcementTimingSignal(timing) -> tuple[dict, float] | None:
    """신호 7: 업종 공시 타이밍."""
    if timing is None:
        return None
    timingScore = timing["peerConsensus"]
    timingDir = "positive" if timingScore > 0.2 else ("negative" if timingScore < -0.2 else "neutral")
    return {
        "direction": timingDir,
        "strength": abs(timingScore),
        "peerConsensus": timing["peerConsensus"],
        "bellwether": timing["bellwetherSignal"],
        "peersReported": timing["sectorPeersReported"],
    }, timingScore


def _supplyChainSignal(supplyChain) -> tuple[dict, float] | None:
    """신호 8: 공급망 모멘텀."""
    if supplyChain is None:
        return None
    scScore = supplyChain["networkMomentum"]
    scDir = "positive" if scScore > 0.15 else ("negative" if scScore < -0.15 else "neutral")
    return {
        "direction": scDir,
        "strength": abs(scScore),
        "networkMomentum": supplyChain["networkMomentum"],
        "nLinked": supplyChain["nLinkedListed"],
        "risk": supplyChain["supplyChainRisk"],
    }, scScore


def _consensusDirectionSignal(consensus) -> tuple[dict, float] | None:
    """신호 9: 컨센서스 매출 방향."""
    if consensus is None:
        return None
    cnsDir = consensus["direction"]
    cnsScore = _DIRECTION_SCORES.get(cnsDir, 0.0)
    return {
        "direction": cnsDir,
        "strength": abs(cnsScore),
        "expectedGrowth": consensus["expectedGrowthPct"],
        "confidence": consensus["confidence"],
    }, cnsScore


def _flowDirectionSignal(flowDir) -> tuple[dict, float] | None:
    """신호 10: 수급 누적 방향."""
    if flowDir is None:
        return None
    fDir = flowDir["direction"]
    fScore = _DIRECTION_SCORES.get(fDir, 0.0)
    return {
        "direction": fDir,
        "strength": abs(fScore),
        "smartMoneyNet": flowDir["smartMoneyNet"],
        "confidence": flowDir["confidence"],
    }, fScore


def _revenueDirectionSignal(revDir) -> tuple[dict, float] | None:
    """신호 11: 매출 모멘텀 (전분기 방향 유지)."""
    if revDir is None:
        return None
    rDir = revDir["direction"]
    rScore = _DIRECTION_SCORES.get(rDir, 0.0)
    return {
        "direction": rDir,
        "strength": abs(rScore),
        "latestYoyGrowth": revDir["latestYoyGrowth"],
        "streak": revDir["streak"],
        "confidence": revDir["confidence"],
    }, rScore


def _agreementScore(scores: list[float], avgScore: float) -> float:
    """신호 합의도 (표준편차 기반). 표본이 1 개면 중립 0.5."""
    if len(scores) < 2:
        return 0.5
    variance = sum((s - avgScore) ** 2 for s in scores) / len(scores)
    return max(0, 1.0 - math.sqrt(variance))


def _confidenceLabel(nSignals: int, agreementScore: float) -> str:
    """신호 수와 합의도로 신뢰도 라벨."""
    if nSignals >= 4 and agreementScore > 0.6:
        return "high"
    if nSignals >= 2:
        return "medium"
    return "low"


def _driversAndRisks(signals: dict) -> tuple[list[str], list[str]]:
    """AI/forecast 엔진 소비용 요약. 방향 라벨을 driver/risk 두 바구니로 가른다."""
    keyDrivers: list[str] = []
    keyRisks: list[str] = []
    for name, sig in signals.items():
        if sig.get("direction") in ("up", "positive", "accelerating"):
            keyDrivers.append(name)
        elif sig.get("direction") in ("down", "negative", "decelerating", "volatile"):
            keyRisks.append(name)
    return keyDrivers, keyRisks


def _revenuePrediction(revDir) -> dict | None:
    """매출 방향 예측 (모멘텀 기반). 검증 정확도는 streak/OLS 동의 조합으로 갈린다."""
    if revDir is None:
        return None
    return {
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
    # 룰 본문은 `_predictionFlagRules` 에 있다. 여기서는 sub-calc 호출과 룰 적용을
    # 원본 순서 그대로 번갈아 둔다 (앞 룰이 죽으면 뒤 sub-calc 를 부르지 않는 동작 보존).
    flags: list[tuple[str, str]] = []
    flags.extend(rules._momentumFlags(calcEarningsMomentum(company, basePeriod=basePeriod)))
    flags.extend(rules._structuralFlags(calcStructuralBreak(company, basePeriod=basePeriod)))
    flags.extend(rules._disclosureFlags(calcDisclosureDelta(company, basePeriod=basePeriod)))
    flags.extend(rules._peerFlags(calcPeerPrediction(company, basePeriod=basePeriod)))
    flags.extend(rules._macroRegressionFlags(calcMacroRegression(company, basePeriod=basePeriod)))
    flags.extend(rules._eventImpactFlags(calcEventImpact(company, basePeriod=basePeriod)))
    flags.extend(rules._inventoryFlags(calcInventoryDivergence(company, basePeriod=basePeriod)))
    flags.extend(rules._announcementTimingFlags(calcAnnouncementTiming(company, basePeriod=basePeriod)))
    flags.extend(rules._supplyChainFlags(calcSupplyChainSignal(company, basePeriod=basePeriod)))

    return flags if flags else None


__all__ = ["calcPredictionFlags", "calcPredictionSynthesis"]
