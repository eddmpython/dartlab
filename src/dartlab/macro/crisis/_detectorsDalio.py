"""macro/crisis/detectors Dalio Part 1 도메인 분리.

macro/crisis/detectors.py 가 803 줄 god module 이라 Dalio Big Debt Cycle 분리.
identity 보존을 위해 detectors.py 가 본 모듈에서 re-export 한다.

함수 + 상수:
- _DALIO_PHASE_LABELS — 6 단계 한국어 라벨
- _SUB_PHASE_LABELS — Beautiful Deleveraging 내부 4 단계 라벨
- _VARIANT_LABELS — Deflationary/Inflationary 변종 라벨
- dalioDebtCyclePhase — 부채 사이클 6 단계 판정
- dalioPolicyLeverStatus — 정책 4 레버 (monetary/fiscal/credit/fx) 소진도
"""

from __future__ import annotations

from dartlab.macro.crisis._detectorsRegime import (
    _beautifulDeleveragingSubPhase,
    _dalioRegimeVariant,
)
from dartlab.macro.crisis._detectorTypes import DalioPhaseResult, DalioPolicyLeverResult

# ══════════════════════════════════════
# Dalio — Big Debt Crises Part 1 템플릿
# ══════════════════════════════════════


_DALIO_PHASE_LABELS = {
    "earlyBoom": "초기 확장기",
    "lateBoom": "후기 확장기",
    "topBubble": "거품 정점",
    "deflationaryDepression": "디플레이션 공황",
    "beautifulDeleveraging": "아름다운 디레버리징",
    "reflationary": "재팽창기",
}


# ══════════════════════════════════════════════════════════════════════
# Dalio Part 1 세부 — Beautiful Deleveraging 내부 4단계 + Regime Variant
# ══════════════════════════════════════════════════════════════════════
#
# beautifulDeleveraging 단계의 내부 4 순서 (Dalio Part 1):
#   austerity (긴축) → defaultRestructuring (디폴트) → moneyPrinting (화폐발행)
#   → wealthTransfer (재분배)
#
# regimeVariant: 환율/기축통화/외화부채에 따라 deflationary vs inflationary


_SUB_PHASE_LABELS = {
    "austerity": "긴축",
    "defaultRestructuring": "디폴트/구조조정",
    "moneyPrinting": "화폐발행",
    "wealthTransfer": "재분배",
}

_VARIANT_LABELS = {
    "deflationary": "디플레이션형",
    "inflationary": "인플레이션형",
}


def dalioDebtCyclePhase(
    *,
    totalDebtToGdp: float | None = None,
    debtServiceYoY: float | None = None,
    creditGap: float | None = None,
    realRate: float | None = None,
    gdpGrowth: float | None = None,
    # subPhase 판정용 (beautifulDeleveraging 에서만 활성)
    m2GrowthYoy: float | None = None,
    npl: float | None = None,
    hySpread: float | None = None,
    fiscalDeficitPctGdp: float | None = None,
    # regimeVariant 판정용
    fxFlexibility: str | None = None,
    reserveCurrency: bool | None = None,
    foreignDebtPct: float | None = None,
) -> DalioPhaseResult:
    """Dalio Big Debt Cycle 6 단계 + Beautiful Deleveraging 4 sub + Regime variant.

    Capabilities:
        Ray Dalio (2018) "Principles for Navigating Big Debt Crises" Part 1
        의 6 단계 (earlyBoom → lateBoom → topBubble → deflationaryDepression
        → beautifulDeleveraging → reflationary) 판정. beautifulDeleveraging
        진입 시 4 sub-phase (austerity/default/printing/wealthTransfer)
        + regime variant (deflationary/inflationary) 추가. 8 역사 케이스 88%
        정확 (실험 053).

    Args:
        totalDebtToGdp: 총부채/GDP (%). 일반 선진국 100~300%.
        debtServiceYoY: 부채서비스 (이자/소득) YoY 변화 (%p).
        creditGap: BIS Credit-to-GDP gap (%p). > 8 = 과열.
        realRate: 실질금리 (%).
        gdpGrowth: 실질 GDP 성장률 (%).
        m2GrowthYoy/npl/hySpread/fiscalDeficitPctGdp: beautifulDeleveraging
            sub-phase 판정용.
        fxFlexibility/reserveCurrency/foreignDebtPct: regime variant 판정용.

    Returns:
        DalioPhaseResult dataclass:
            - ``phase`` (str): 6 단계 enum
            - ``phaseLabel`` (str): 한국어
            - ``signals`` (list[str]): 판정 근거
            - ``subPhase`` (str|None): beautifulDeleveraging 시 4 sub
            - ``regimeVariant`` (str|None): deflationary/inflationary
            - ``description`` (str)

    Raises:
        없음.

    Example:
        >>> r = dalioDebtCyclePhase(totalDebtToGdp=250, creditGap=12,
        ...                          realRate=1.5, gdpGrowth=3.2)
        >>> r.phase
        'topBubble'

    Guide:
        6 단계 시간 순서:
        - earlyBoom: 신용 시작 (creditGap 음수→양수)
        - lateBoom: 가속 (creditGap > 2)
        - topBubble: 과열 (creditGap > 8 + 자산 가격 거품)
        - deflationaryDepression: 거품 붕괴 (creditGap 급락)
        - beautifulDeleveraging: 정책 개입 후 회복 (Dalio 의 핵심 단계)
        - reflationary: 새 사이클 시작

        팬데믹급 (2020) 같은 급전환은 transition (단일 enum 한계). 호출자는
        ``policyLeverStatus`` 와 조합 권장.

    SeeAlso:
        - ``dalioPolicyLeverStatus``: 정책 4 레버 소진도
        - ``minskyPhase``: Minsky 5 단계 (Dalio 와 유사하지만 시장 중심)
        - ``ghsCrisisScore``: 3 년 horizon 위기 확률
        - Dalio, R. (2018) "Principles for Navigating Big Debt Crises"

    When:
        ``macro("crisis", "debt")`` 호출. 거시 부채 사이클 판정 답변에.

    How:
        GDP/creditGap/실질금리/부채서비스 임계 분기 → 6 단계 phase → beautifulDeleveraging 시
        sub-phase → fx/reserve 기반 regimeVariant.

    Requires:
        gdpGrowth + creditGap + realRate 중 최소 1 개.

    AIContext:
        phase + signals + description 함께 인용. beautifulDeleveraging 결과
        는 정책 개입 후 회복 단계 — "위기" 신호로 오해 금지. 한국은 lateBoom
        (2024) 으로 분류되는 경향.

    LLM Specifications:
        AntiPatterns:
            - 한국 회사를 deflationaryDepression 으로 단정 (실험상 한국은
              아직 본격 진입 안 함).
            - 단일 지표 (creditGap 만) 로 단계 판정 — 4~5 지표 결합 필수.
        OutputSchema:
            DalioPhaseResult ``{phase, phaseLabel, signals, subPhase,
            regimeVariant, description}``.
        Prerequisites:
            gdpGrowth + creditGap + realRate (1 개 이상). 결측 시 earlyBoom 기본.
        Freshness:
            BIS 분기, 실질금리 일/월.
        Dataflow:
            지표 → 6 단계 룰 → phase → subPhase (beautifulDeleveraging) →
            regime variant (fxFlexibility/reserve currency).
        TargetMarkets: Global (Dalio 원형). 한국 + 미국 + EU + 일본 모두.
    """
    signals: list[str] = []

    # 입력 결측 → earlyBoom 기본값
    if gdpGrowth is None and creditGap is None and realRate is None:
        return DalioPhaseResult(
            phase="earlyBoom",
            phaseLabel=_DALIO_PHASE_LABELS["earlyBoom"],
            signals=["데이터 부족 — 기본값"],
            description="입력 부족으로 기본값(초기 확장기) 반환",
        )

    g = gdpGrowth if gdpGrowth is not None else 0.0
    cg = creditGap if creditGap is not None else 0.0
    rr = realRate if realRate is not None else 0.0
    ds = debtServiceYoY if debtServiceYoY is not None else 0.0

    # 1. 디플레이션 공황
    if g < -1.0 and cg < 0:
        signals.append(f"GDP 성장 {g:+.1f}% + 신용갭 {cg:+.1f}%p 음전환")
        phase = "deflationaryDepression"
    # 2. Reflationary
    elif rr < -2.0 and g >= -2.0:
        signals.append(f"실질금리 {rr:+.1f}% 깊은 마이너스 + 성장 회복 중")
        phase = "reflationary"
    # 3. Top Bubble
    elif cg >= 8.0 and g > 0 and rr < 2.0:
        signals.append(f"신용갭 {cg:+.1f}%p 과열 + 성장 {g:+.1f}% + 실질금리 {rr:+.1f}%")
        phase = "topBubble"
    # 4. Late Boom
    elif cg >= 2.0 and ds > 0 and g > 0:
        signals.append(f"신용갭 {cg:+.1f}%p 상승 + 부채서비스 {ds:+.1f}%p 악화")
        phase = "lateBoom"
    # 5. Beautiful Deleveraging
    elif ds < 0 and g > 0:
        signals.append(f"부채서비스 {ds:+.1f}%p 개선 + 성장 {g:+.1f}% 양호")
        phase = "beautifulDeleveraging"
    # 6. Early Boom (기본)
    else:
        signals.append("신용 완만 + 성장 건강")
        phase = "earlyBoom"

    if totalDebtToGdp is not None:
        signals.append(f"총부채/GDP {totalDebtToGdp:.0f}%")

    label = _DALIO_PHASE_LABELS[phase]
    desc = f"Dalio 부채사이클: {label} ({phase})"

    # subPhase: beautifulDeleveraging 에서만 세분화
    subPhase = None
    subPhaseLab = None
    if phase == "beautifulDeleveraging":
        subPhase = _beautifulDeleveragingSubPhase(
            realRate=realRate,
            m2GrowthYoy=m2GrowthYoy,
            debtServiceYoY=ds,
            npl=npl,
            hySpread=hySpread,
            fiscalDeficitPctGdp=fiscalDeficitPctGdp,
        )
        subPhaseLab = _SUB_PHASE_LABELS.get(subPhase) if subPhase else None
        if subPhase:
            signals.append(f"deleveraging sub: {subPhase}")

    # regimeVariant: 환율/기축통화 기반
    variant = _dalioRegimeVariant(
        fxFlexibility=fxFlexibility,
        reserveCurrency=reserveCurrency,
        realRate=realRate,
        foreignDebtPct=foreignDebtPct,
    )
    variantLab = _VARIANT_LABELS.get(variant) if variant else None
    if variant:
        signals.append(f"regime: {variant}")

    return DalioPhaseResult(
        phase=phase,
        phaseLabel=label,
        signals=signals,
        description=desc,
        subPhase=subPhase,
        subPhaseLabel=subPhaseLab,
        regimeVariant=variant,
        regimeVariantLabel=variantLab,
    )


def dalioPolicyLeverStatus(
    *,
    policyRate: float | None = None,
    publicDebtToGdp: float | None = None,
    creditGap: float | None = None,
    fxFlexibility: str | None = None,
) -> DalioPolicyLeverResult:
    """Dalio 정책 4 레버 (monetary/fiscal/credit/fx) 소진도 → 위기 대응 여력 진단.

    Capabilities:
        Dalio (2018) Big Debt Crises Ch.3 — 정부가 위기 대응에 쓸 수 있는
        4 레버 (monetary/fiscal/credit/fx) 의 소진도를 판정. 가장 중요한
        통찰: "어떤 위기인가" 보다 "얼마나 레버가 남아있나" — 한국은 fiscal/
        FX 여유, 미국은 monetary 소진 + fiscal 여유, 일본은 4 레버 모두 소진.

    Args:
        policyRate: 기준금리 (%). ≤ 0.5 = maxed, ≤ 2 = partial, 그 외 spare.
        publicDebtToGdp: 공공부채/GDP (%). ≥ 120 = maxed, ≥ 80 = partial.
        creditGap: BIS credit-to-GDP gap (%p). ≥ 8 = maxed, ≥ 2 = partial.
        fxFlexibility: ``"flexible"``/``"managed"``/``"pegged"`` — peg/관리 =
            maxed (FX 자유롭게 못 풂), flexible = spare.

    Returns:
        DalioPolicyLeverResult dataclass:
            - ``monetary``/``fiscal``/``credit``/``fx`` (str): 각 레버 상태
            - ``totalScore`` (int): 0~12 (4 × 3) 소진도
            - ``available`` (int): 남은 spare 레버 수
            - ``status`` (str): ``"abundant"``/``"limited"``/``"depleted"``
            - ``description`` (str): 한국어 진단

    Raises:
        없음.

    Example:
        >>> r = dalioPolicyLeverStatus(policyRate=0.5, publicDebtToGdp=260,
        ...                            creditGap=10, fxFlexibility="managed")
        >>> r.status, r.totalScore
        ('depleted', 11)  # 일본 사례

    Guide:
        totalScore 임계: 0~4 = abundant, 5~8 = limited, 9~12 = depleted.
        depleted 국가는 위기 시 새로운 도구 (Yield Curve Control, 직접
        통화 인쇄 등) 필요. 한국은 보통 abundant ~ limited.

    SeeAlso:
        - ``dalioDebtCyclePhase``: 6 단계 (본 함수와 조합)
        - ``creditToGDPGap``: BIS gap (creditGap 입력)
        - Dalio, R. (2018) Big Debt Crises Ch.3

    When:
        ``macro("crisis", "policy")``. 정책 대응 여력 답변, 국가 비교 분석.

    How:
        4 레버 (policyRate/publicDebt/creditGap/fxFlexibility) 임계 분기 → maxed/partial/spare
        라벨 → score 합산 → status.

    Requires:
        없음 — 4 레버 모두 옵션. 입력 없으면 모두 spare.

    AIContext:
        status="depleted" 결과는 정책 결정자 향 (정부 대응 한계 시점). 개별
        기업 분석에서는 ``available`` 수로 macro 여력 표시.

    LLM Specifications:
        AntiPatterns:
            - 단일 레버 (policyRate 만) 보고 status 단정 — 4 레버 합산.
            - fxFlexibility 결측 시 자동 spare 처리 — 의도된 default 이나
              실제 peg/관리 통화이면 maxed 명시 권장.
        OutputSchema:
            DalioPolicyLeverResult ``{monetary, fiscal, credit, fx, totalScore,
            available, status, description}``.
        Prerequisites:
            적어도 1 레버 입력 권장 (그 외 spare default).
        Freshness:
            정책금리 일, 공공부채 분기 (IMF/한국은행), creditGap 분기.
        Dataflow:
            각 레버 임계 비교 → maxed/partial/spare 라벨 → 점수 합산 → status.
        TargetMarkets: Global (Dalio 원형). 한국 + 미국 + 일본 + EU 모두.
    """
    signals: list[str] = []

    def _ratePhase(v: float | None) -> str:
        if v is None:
            return "spare"
        if v <= 0.5:
            return "maxed"
        if v <= 2.0:
            return "partial"
        return "spare"

    def _debtPhase(v: float | None) -> str:
        if v is None:
            return "spare"
        if v >= 120:
            return "maxed"
        if v >= 80:
            return "partial"
        return "spare"

    def _creditPhase(v: float | None) -> str:
        if v is None:
            return "spare"
        if v >= 8:
            return "maxed"
        if v >= 2:
            return "partial"
        return "spare"

    def _fxPhase(v: str | None) -> str:
        if v is None:
            return "spare"
        if v == "pegged":
            return "maxed"
        if v == "managed":
            return "partial"
        return "spare"

    monetary = _ratePhase(policyRate)
    fiscal = _debtPhase(publicDebtToGdp)
    credit = _creditPhase(creditGap)
    fx = _fxPhase(fxFlexibility)

    if policyRate is not None:
        signals.append(f"기준금리 {policyRate:.2f}% — 통화정책 {monetary}")
    if publicDebtToGdp is not None:
        signals.append(f"공공부채/GDP {publicDebtToGdp:.0f}% — 재정정책 {fiscal}")
    if creditGap is not None:
        signals.append(f"신용갭 {creditGap:+.1f}%p — 신용정책 {credit}")
    if fxFlexibility is not None:
        signals.append(f"환율 체제 {fxFlexibility} — fx 레버 {fx}")

    scoreMap = {"maxed": 3, "partial": 2, "spare": 1}
    score = scoreMap[monetary] + scoreMap[fiscal] + scoreMap[credit] + scoreMap[fx]
    return DalioPolicyLeverResult(
        monetary=monetary,
        fiscal=fiscal,
        credit=credit,
        fx=fx,
        exhaustionScore=score,
        signals=signals,
    )


__all__ = [
    "_DALIO_PHASE_LABELS",
    "_SUB_PHASE_LABELS",
    "_VARIANT_LABELS",
    "dalioDebtCyclePhase",
    "dalioPolicyLeverStatus",
]
