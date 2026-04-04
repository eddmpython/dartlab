"""교역조건(Terms of Trade) 분석 + 수출이익 선행 신호.

순수 데이터 + 판정 함수. 외부 의존성 없음.
core/ 계층 소속 — macro(시장 해석) 엔진에서 소비.

교역조건은 수출물가지수/수입물가지수 비율이다.
한국경제에서 교역조건은 가장 앞서는 선행지표로 알려져 있다.

학술 근거:
- 투자전략 11: 교역조건이 선행지수 중 가장 앞선다
- 투자전략 12: 교역조건 대용치 = 환율상승률 - 유가상승률
- 투자전략 31: 교역조건 대용치 → 수출기업 이익 선행
"""

from __future__ import annotations

from dataclasses import dataclass


# ══════════════════════════════════════
# 데이터 구조
# ══════════════════════════════════════


@dataclass(frozen=True)
class ToTSignal:
    """교역조건 신호."""

    level: float  # 교역조건 지수 (100 기준)
    momentum: float  # 전기 대비 변화
    direction: str  # "improving" | "stable" | "deteriorating"
    directionLabel: str  # "개선" | "안정" | "악화"
    earningsImplication: str  # "positive" | "neutral" | "negative"
    earningsLabel: str  # "수출이익 개선" | "중립" | "수출이익 악화"
    description: str


@dataclass(frozen=True)
class ToTProxy:
    """교역조건 대용치 (환율-유가)."""

    value: float  # 대용치 값 (환율상승률 - 유가상승률)
    direction: str  # "improving" | "stable" | "deteriorating"
    directionLabel: str  # "개선" | "안정" | "악화"
    components: dict[str, float]  # {"fxYoy": ..., "oilYoy": ...}
    description: str


@dataclass(frozen=True)
class ExportProfitSignal:
    """수출이익 선행 신호."""

    signal: str  # "strong_positive" | "positive" | "neutral" | "negative" | "strong_negative"
    signalLabel: str  # "강한 개선" | "개선" | "중립" | "악화" | "강한 악화"
    confidence: str  # "high" | "medium" | "low"
    components: dict[str, float]  # tot, exportVol 등
    description: str


@dataclass(frozen=True)
class TradeLeadingSignal:
    """양국 선행지수 상대강도 → 환율 방향."""

    relativeStrength: float  # US LEI - KR CLI (정규화)
    fxDirection: str  # "krw_weaken" | "stable" | "krw_strengthen"
    fxLabel: str  # "원화약세" | "안정" | "원화강세"
    description: str


# ══════════════════════════════════════
# 판정 함수
# ══════════════════════════════════════


def calcToT(
    exportPriceIdx: float,
    importPriceIdx: float,
    prevExportPriceIdx: float | None = None,
    prevImportPriceIdx: float | None = None,
) -> ToTSignal:
    """교역조건 계산 + 방향 판별.

    Args:
        exportPriceIdx: 수출물가지수
        importPriceIdx: 수입물가지수
        prevExportPriceIdx: 이전 기간 수출물가지수 (모멘텀용)
        prevImportPriceIdx: 이전 기간 수입물가지수 (모멘텀용)

    Returns:
        ToTSignal: 교역조건 수준 + 방향 + 수출이익 시사점
    """
    if importPriceIdx <= 0:
        return ToTSignal(
            level=0.0,
            momentum=0.0,
            direction="stable",
            directionLabel="판별불가",
            earningsImplication="neutral",
            earningsLabel="중립",
            description="수입물가 데이터 부재",
        )

    tot = (exportPriceIdx / importPriceIdx) * 100
    prev_tot = None
    if prevExportPriceIdx is not None and prevImportPriceIdx is not None and prevImportPriceIdx > 0:
        prev_tot = (prevExportPriceIdx / prevImportPriceIdx) * 100

    momentum = tot - prev_tot if prev_tot is not None else 0.0

    # 방향 판별: 2%p 이상 변화 시 의미있는 변화
    if momentum > 2:
        direction = "improving"
        direction_label = "개선"
        earnings = "positive"
        earnings_label = "수출이익 개선"
        desc = f"교역조건 {tot:.1f} (전기대비 +{momentum:.1f}) — 수출가격 상대 상승, 기업 이익 개선 선행"
    elif momentum < -2:
        direction = "deteriorating"
        direction_label = "악화"
        earnings = "negative"
        earnings_label = "수출이익 악화"
        desc = f"교역조건 {tot:.1f} (전기대비 {momentum:.1f}) — 수입원가 상대 상승, 기업 마진 압박"
    else:
        direction = "stable"
        direction_label = "안정"
        earnings = "neutral"
        earnings_label = "중립"
        desc = f"교역조건 {tot:.1f} (전기대비 {momentum:+.1f}) — 안정적 유지"

    return ToTSignal(
        level=round(tot, 2),
        momentum=round(momentum, 2),
        direction=direction,
        directionLabel=direction_label,
        earningsImplication=earnings,
        earningsLabel=earnings_label,
        description=desc,
    )


def totProxy(fxYoy: float, oilYoy: float) -> ToTProxy:
    """교역조건 대용치: 환율상승률 - 유가상승률.

    투자전략 12: 원/달러 환율 상승률에서 유가 상승률을 빼면
    교역조건의 대용치를 구할 수 있다.

    Args:
        fxYoy: 환율(USDKRW) 전년대비 변화율 (%)
            원화 약세(환율 상승) → 수출 유리 → 양수
        oilYoy: WTI 유가 전년대비 변화율 (%)
            유가 상승 → 수입원가 상승 → 교역조건 악화

    Returns:
        ToTProxy: 대용치 + 방향
    """
    value = fxYoy - oilYoy

    if value > 5:
        direction = "improving"
        direction_label = "개선"
        desc = f"교역조건 대용치 {value:+.1f}%p — 환율 상승이 유가 상승을 상회, 수출 환경 개선"
    elif value < -5:
        direction = "deteriorating"
        direction_label = "악화"
        desc = f"교역조건 대용치 {value:+.1f}%p — 유가 상승이 환율 상승을 압도, 수입원가 부담"
    else:
        direction = "stable"
        direction_label = "안정"
        desc = f"교역조건 대용치 {value:+.1f}%p — 환율과 유가 효과 상쇄"

    return ToTProxy(
        value=round(value, 2),
        direction=direction,
        directionLabel=direction_label,
        components={"fxYoy": round(fxYoy, 2), "oilYoy": round(oilYoy, 2)},
        description=desc,
    )


def exportProfitLeading(
    totMomentum: float,
    exportVolMomentum: float,
) -> ExportProfitSignal:
    """수출기업 이익 선행 신호.

    투자전략 31: 교역조건 대용치는 수출기업 이익에 선행한다.
    교역조건 방향 × 수출량 모멘텀 조합으로 판별.

    Args:
        totMomentum: 교역조건(또는 대용치) 모멘텀
        exportVolMomentum: 수출량 증가율 (%)

    Returns:
        ExportProfitSignal: 수출이익 선행 신호
    """
    tot_positive = totMomentum > 2
    tot_negative = totMomentum < -2
    vol_positive = exportVolMomentum > 3
    vol_negative = exportVolMomentum < -3

    components = {
        "totMomentum": round(totMomentum, 2),
        "exportVolMomentum": round(exportVolMomentum, 2),
    }

    if tot_positive and vol_positive:
        return ExportProfitSignal(
            signal="strong_positive",
            signalLabel="강한 개선",
            confidence="high",
            components=components,
            description="교역조건 개선 + 수출량 증가 — 수출기업 이익 강한 상승 선행",
        )
    elif tot_positive or (not tot_negative and vol_positive):
        return ExportProfitSignal(
            signal="positive",
            signalLabel="개선",
            confidence="medium",
            components=components,
            description="교역조건 또는 수출량 한 가지 개선 — 수출기업 이익 완만 상승 예상",
        )
    elif tot_negative and vol_negative:
        return ExportProfitSignal(
            signal="strong_negative",
            signalLabel="강한 악화",
            confidence="high",
            components=components,
            description="교역조건 악화 + 수출량 감소 — 수출기업 이익 급감 선행",
        )
    elif tot_negative or vol_negative:
        return ExportProfitSignal(
            signal="negative",
            signalLabel="악화",
            confidence="medium",
            components=components,
            description="교역조건 또는 수출량 한 가지 악화 — 수출기업 이익 하방 압력",
        )
    else:
        return ExportProfitSignal(
            signal="neutral",
            signalLabel="중립",
            confidence="low",
            components=components,
            description="교역조건과 수출량 모두 안정 — 현 수준 유지 전망",
        )


def leadingIndexRelativeStrength(
    usLeiMom: float,
    krCliMom: float,
) -> TradeLeadingSignal:
    """양국 선행지수 상대강도 → 환율 방향.

    투자전략 14: 양국 선행지수의 상대강도가 환율 방향을 결정한다.

    Args:
        usLeiMom: 미국 LEI 모멘텀 (전월대비 %)
        krCliMom: 한국 CLI 모멘텀 (전월대비 %)

    Returns:
        TradeLeadingSignal: 상대강도 → 환율 방향
    """
    relative = usLeiMom - krCliMom

    if relative > 1.0:
        return TradeLeadingSignal(
            relativeStrength=round(relative, 2),
            fxDirection="krw_weaken",
            fxLabel="원화약세",
            description=f"미국 선행지수 우위 ({relative:+.1f}%p) — 달러 강세/원화 약세 압력",
        )
    elif relative < -1.0:
        return TradeLeadingSignal(
            relativeStrength=round(relative, 2),
            fxDirection="krw_strengthen",
            fxLabel="원화강세",
            description=f"한국 선행지수 우위 ({relative:+.1f}%p) — 원화 강세 압력",
        )
    else:
        return TradeLeadingSignal(
            relativeStrength=round(relative, 2),
            fxDirection="stable",
            fxLabel="안정",
            description=f"양국 선행지수 균형 ({relative:+.1f}%p) — 환율 중립",
        )
