"""예측신호 → 경고 플래그 룰 9 종.

`_predictionSynthesis.calcPredictionFlags` 가 sub-calc 결과마다 임계 비교를 인라인으로
쌓아 올려 한 함수가 40 분기까지 커졌다. 룰끼리 의존이 없고 각자 자기 sub-calc 결과만
읽으므로, 신호별로 `(코드, 메시지)` 리스트를 내는 순수 함수로 갈랐다.

각 함수는 결과가 falsy 면 빈 리스트를 돌려주고, 호출자는 나열 순서 그대로 이어 붙인다.
플래그 코드·메시지 문구는 story flag 박스와 AI 답변이 그대로 인용하는 계약이라 바꾸지 않는다.
"""

from __future__ import annotations

# 플래그 메시지에 이미 나가 있는 긴 줄표 (U+2014). 문구가 곧 반환 계약이라 바꾸지 않고,
# 소스에는 리터럴을 남기지 않으려 코드포인트로 고정한다 (신규 문구에는 쓰지 않는다).
_OUTPUT_DASH = chr(0x2014)

_Flag = tuple[str, str]


def _momentumFlags(momentum) -> list[_Flag]:
    """이익 모멘텀: 감속 추세·높은 발생액·낮은 지속성."""
    if not momentum:
        return []
    flags: list[_Flag] = []
    if momentum["momentum"] == "decelerating":
        flags.append(("EARN_DECEL", f"이익 감속 추세 {_OUTPUT_DASH} 최근 3년 연속 감소"))
    if momentum["highAccrualWarning"]:
        flags.append(("HIGH_ACCRUAL", f"높은 발생액 비율 {_OUTPUT_DASH} 이익의 현금 뒷받침 약함"))
    if momentum["persistenceScore"] < 30:
        flags.append(("LOW_PERSIST", f"낮은 이익 지속성 {_OUTPUT_DASH} OCF/NI 비율 낮음"))
    return flags


def _structuralFlags(structural) -> list[_Flag]:
    """구조변화: 전반 불안정 + 매출 지표 구조변화."""
    if not structural:
        return []
    flags: list[_Flag] = []
    if structural["overallStability"] == "volatile":
        flags.append(("STRUCT_VOLATILE", f"다수 지표에서 구조변화 감지 {_OUTPUT_DASH} 추세 추정 신뢰도 낮음"))
    for m in structural["metrics"]:
        if m["hasBreak"] and m["name"] == "revenue":
            flags.append(("REV_BREAK", f"매출 구조변화 감지 ({m['breakYear']})"))
    return flags


def _disclosureFlags(disclosure) -> list[_Flag]:
    """공시 변화: 리스크 섹션 급변 + 부정 신호 강도."""
    if not disclosure:
        return []
    flags: list[_Flag] = []
    if disclosure["riskChangeRate"] > 60:
        flags.append(("RISK_SURGE", f"리스크 공시 급변 ({disclosure['riskChangeRate']:.0f}%)"))
    if disclosure["signalDirection"] == "negative" and disclosure["signalStrength"] == "strong":
        flags.append(("DISC_NEGATIVE", f"공시 변화 부정적 신호 {_OUTPUT_DASH} 리스크 섹션 대폭 확대"))
    return flags


def _peerFlags(peer) -> list[_Flag]:
    """피어 괴리: ±15%p 밖이면 하회/상회 플래그."""
    if not (peer and peer.get("divergence") is not None):
        return []
    if peer["divergence"] < -15:
        return [("PEER_BELOW", f"피어 대비 {peer['divergence']:+.1f}%p 하회 예측")]
    if peer["divergence"] > 15:
        return [("PEER_ABOVE", f"피어 대비 {peer['divergence']:+.1f}%p 상회 예측")]
    return []


def _macroRegressionFlags(macroReg) -> list[_Flag]:
    """거시-재무 회귀: 설명력이 충분할 때만 고베타 지표를 플래그."""
    if not macroReg:
        return []
    if not (macroReg["rSquared"] > 0.3 and macroReg["confidence"] in ("high", "medium")):
        return []
    flags: list[_Flag] = []
    for indicator, beta in macroReg.get("betas", {}).items():
        if abs(beta) > 2.0:
            flags.append(("MACRO_HIGH_BETA", f"거시 베타 높음: {indicator} β={beta:+.1f}"))
    return flags


def _eventImpactFlags(eventImp) -> list[_Flag]:
    """이벤트 충격: 회복력 저하 + 충격 빈발."""
    if not eventImp:
        return []
    flags: list[_Flag] = []
    if eventImp.get("resilience") == "low":
        flags.append(("LOW_RESILIENCE", f"충격 회복력 낮음 (평균 {eventImp.get('avgRecoveryYears', '?')}년)"))
    nEvents = len(eventImp.get("events", []))
    if nEvents >= 3:
        flags.append(("FREQUENT_EVENTS", f"최근 충격 이벤트 {nEvents}건"))
    return flags


def _inventoryFlags(inventory) -> list[_Flag]:
    """재고/매출채권 괴리: 위험 점수·재고 급증·수금 악화·순영업자산 급증."""
    if not inventory:
        return []
    flags: list[_Flag] = []
    if inventory["riskScore"] > 70:
        flags.append(("INV_HIGH_RISK", f"재고/매출채권 위험 점수 {inventory['riskScore']}"))
    if inventory["inventorySignal"] == "building":
        h = inventory["history"]
        div = h[0]["divergence"] if h and h[0].get("divergence") is not None else 0
        flags.append(("INV_DIVERGE", f"재고 급증 vs 매출 (괴리 {div:+.1f}%p)"))
    if inventory["receivableSignal"] == "deteriorating":
        flags.append(("DSO_SPIKE", f"매출채권 회수 악화 {_OUTPUT_DASH} 매출 대비 채권 급증"))
    if inventory["noaGrowth"] is not None and inventory["noaGrowth"] > 20:
        flags.append(("NOA_SURGE", f"순영업자산 급증 {inventory['noaGrowth']:+.1f}%"))
    return flags


def _announcementTimingFlags(timing) -> list[_Flag]:
    """업종 타이밍: 이미 발표한 동종사 70% 이상이 하락이면 업종 침체."""
    if not timing:
        return []
    dirs = timing["reportedDirection"]
    total = sum(dirs.values())
    if total >= 3 and dirs["down"] / total >= 0.7:
        return [("SECTOR_DOWNTURN", f"업종 {dirs['down']}/{total} 기업 실적 하락")]
    return []


def _supplyChainFlags(sc) -> list[_Flag]:
    """공급망: 관계사 실적 악화가 넓게 퍼졌는지."""
    if not sc:
        return []
    if sc["supplyChainRisk"] == "high":
        return [("NETWORK_RISK", f"관계사 {sc['nLinkedListed']}개 중 다수 실적 악화")]
    return []
