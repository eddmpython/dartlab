"""매크로 유동성 분석 — M2 + 연준 B/S + 신용스프레드 + FCI.

- ``LiquidityRegime`` / ``classifyLiquidityRegime`` — 유동성 환경 판정
- ``CapexPressure`` / ``capexPressure`` — 신용스프레드 → 설비투자 압력
- ``calcLiquidity`` — gather 통한 데이터 수집 + 종합 분석
"""

from __future__ import annotations

from dataclasses import dataclass

from dartlab.macro.seriesFetch import (
    applyOverrides,
    collectTimeseries,
    fetchChangePct,
    fetchLatest,
    fetchSeriesList,
    fetchYoy,
    getGather,
)


@dataclass(frozen=True)
class LiquidityRegime:
    """유동성 환경 판정 결과."""

    regime: str | None  # "abundant" | "normal" | "tight"
    regimeLabel: str  # "풍부" | "정상" | "긴축"
    score: float | None  # -3 ~ +3 (양수=풍부, 음수=긴축)
    signals: tuple[str, ...]
    status: str = "observed"
    observedInputs: int = 0
    totalInputs: int = 5


def classifyLiquidityRegime(
    m2Yoy: float | None = None,
    fedBsChangePct: float | None = None,
    hySpread: float | None = None,
    igSpread: float | None = None,
    rrpChangePct: float | None = None,
) -> LiquidityRegime:
    """유동성 환경 종합 판정.

    Capabilities:
        5 변수 (M2 YoY + 연준 B/S + HY/IG 스프레드 + 역레포) 임계 매칭 score
        합산 → 3 regime (abundant/normal/tight) + signals 라벨 list.
        Bridgewater 글로벌 유동성 모델 단순화.

    Args:
        m2Yoy: M2 통화량 YoY (%). 옵션.
        fedBsChangePct: 연준 총자산 3M 변화율 (%). 옵션.
        hySpread: HY OAS (bps). 옵션.
        igSpread: IG OAS (bps). 옵션.
        rrpChangePct: 역레포 잔액 변화율 (%, 음수=유동성 방출). 옵션.

    Returns:
        LiquidityRegime — regime(abundant/normal/tight)/regimeLabel/score(-3~+3)/
        signals tuple.

    Example:
        >>> r = classifyLiquidityRegime(m2Yoy=8, hySpread=320)
        >>> r.regime, r.score
        ('abundant', 2.0)

    Guide:
        |score| ≥ 1.5 = 표준 regime 판정. signals 의 dominant 요인 인용으로
        "M2 팽창 + HY 안정 = 풍부" 답변 완성.

    When:
        ``calcLiquidity`` 내부 + AI 유동성 답변 1 차.

    How:
        각 변수 임계 매칭 → score (±0.5~1.5) 누적 → ±1.5 임계로 regime.

    Requires:
        FRED M2SL/WALCL/BAMLH0A0HYM2/BAMLC0A0CM/RRPONTSYD 중 일부.

    Raises:
        없음 — 부분 입력도 동작.

    See Also:
        - calcLiquidity : 본 함수 + NFCI/FCI 종합
        - capexPressure : HY 단일 변수

    AIContext:
        regimeLabel + signals 1~2 인용으로 한 문장 답변.

    LLM Specifications:
        AntiPatterns:
            - 단일 변수 (M2 만) 단정
            - score 절대값 인용 + regime 미노출
        OutputSchema:
            LiquidityRegime ``(regime, regimeLabel, score, signals)``.
        Prerequisites: FRED 5 시리즈 중 1+.
        Freshness: 일간 (HY/IG/RRP) ~ 주간 (M2/WALCL).
        Dataflow: 5 임계 → score 합산 → regime.
        TargetMarkets: US (FRED). KR 미지원.
    """
    signals: list[str] = []
    score = 0.0
    observed_inputs = sum(value is not None for value in (m2Yoy, fedBsChangePct, hySpread, igSpread, rrpChangePct))

    if observed_inputs < 2:
        return LiquidityRegime(
            regime=None,
            regimeLabel="판정불가",
            score=None,
            signals=(f"유동성 판정 근거 부족 ({observed_inputs}/5)",),
            status="unavailable",
            observedInputs=observed_inputs,
        )

    # M2 통화량
    if m2Yoy is not None:
        if m2Yoy > 6:
            score += 1.5
            signals.append(f"M2 YoY +{m2Yoy:.1f}% — 통화 팽창")
        elif m2Yoy > 2:
            score += 0.5
            signals.append(f"M2 YoY +{m2Yoy:.1f}% — 정상 성장")
        elif m2Yoy > -2:
            signals.append(f"M2 YoY {m2Yoy:+.1f}% — 정체")
        else:
            score -= 1.5
            signals.append(f"M2 YoY {m2Yoy:+.1f}% — 통화 수축")

    # 연준 B/S
    if fedBsChangePct is not None:
        if fedBsChangePct > 2:
            score += 1
            signals.append(f"연준 B/S 3M {fedBsChangePct:+.1f}% — QE/확대")
        elif fedBsChangePct < -2:
            score -= 1
            signals.append(f"연준 B/S 3M {fedBsChangePct:+.1f}% — QT/축소")

    # HY 스프레드 (신용 시장 유동성)
    if hySpread is not None:
        if hySpread < 350:
            score += 0.5
            signals.append(f"HY 스프레드 {hySpread:.0f}bp — 신용 완화")
        elif hySpread > 500:
            score -= 1
            signals.append(f"HY 스프레드 {hySpread:.0f}bp — 신용 경색")

    # IG 스프레드
    if igSpread is not None:
        if igSpread < 100:
            score += 0.5
            signals.append(f"IG 스프레드 {igSpread:.0f}bp — 투자등급 안정")
        elif igSpread > 200:
            score -= 0.5
            signals.append(f"IG 스프레드 {igSpread:.0f}bp — 투자등급 경고")

    # 역레포 (음수 변화 = 유동성이 시장으로 방출)
    if rrpChangePct is not None:
        if rrpChangePct < -10:
            score += 0.5
            signals.append(f"역레포 {rrpChangePct:+.1f}% — 유동성 방출")
        elif rrpChangePct > 10:
            score -= 0.5
            signals.append(f"역레포 {rrpChangePct:+.1f}% — 유동성 흡수")

    if score >= 1.5:
        regime, label = "abundant", "풍부"
    elif score <= -1.5:
        regime, label = "tight", "긴축"
    else:
        regime, label = "normal", "정상"

    return LiquidityRegime(
        regime=regime,
        regimeLabel=label,
        score=round(score, 1),
        signals=tuple(signals),
        status="observed",
        observedInputs=observed_inputs,
    )


# ══════════════════════════════════════
# 설비투자 압력 (투자전략 32)
# ══════════════════════════════════════


@dataclass(frozen=True)
class CapexPressure:
    """신용스프레드 기반 설비투자 압력."""

    pressure: str  # "easing" | "neutral" | "tightening"
    pressureLabel: str  # "완화" | "중립" | "긴축"
    spreadLevel: float  # HY 스프레드 (bps)
    spreadChange: float  # 변화 (bps)
    description: str


def capexPressure(hySpread: float, hySpreadChange: float) -> CapexPressure:
    """신용스프레드 → 설비투자 압력.

    투자전략 32: 신용스프레드는 곧 설비투자 조정압력이다.
    HY 스프레드 상승 → 기업 자금조달 비용 증가 → 설비투자 축소.

    Args:
        hySpread: HY 스프레드 (bps)
        hySpreadChange: HY 스프레드 3개월 변화 (bps)

    Example:
        >>> r = capexPressure(550, 120)
        >>> r.pressure
        'tightening'

    Requires:
        FRED BAMLH0A0HYM2 (HY OAS) latest + 3M ago.

    Raises:
        없음.
    """
    if hySpreadChange > 100 or hySpread > 500:
        return CapexPressure(
            pressure="tightening",
            pressureLabel="긴축",
            spreadLevel=round(hySpread, 0),
            spreadChange=round(hySpreadChange, 0),
            description=f"HY 스프레드 {hySpread:.0f}bp ({hySpreadChange:+.0f}bp) — 설비투자 축소 압력 강화",
        )
    elif hySpreadChange < -50 or hySpread < 350:
        return CapexPressure(
            pressure="easing",
            pressureLabel="완화",
            spreadLevel=round(hySpread, 0),
            spreadChange=round(hySpreadChange, 0),
            description=f"HY 스프레드 {hySpread:.0f}bp ({hySpreadChange:+.0f}bp) — 설비투자 환경 개선",
        )
    else:
        return CapexPressure(
            pressure="neutral",
            pressureLabel="중립",
            spreadLevel=round(hySpread, 0),
            spreadChange=round(hySpreadChange, 0),
            description=f"HY 스프레드 {hySpread:.0f}bp ({hySpreadChange:+.0f}bp) — 설비투자 중립",
        )


def _fetchLiquidityData(market: str, asOf: str | None = None) -> dict[str, float | None]:
    """gather에서 유동성 지표 수집.

    Parameters
    ----------
    market : str
        ``"US"`` | ``"KR"``.
    as_of : str | None
        기준일. ``None`` 이면 최신.

    Returns
    -------
    dict[str, float]
        None 값은 제거된 채 반환. 가능한 키:

        - m2_yoy : float — M2 통화량 전년비 증가율 (%)
        - fed_bs_change_pct : float — 연준 재무상태표 13주 변화율 (%)
        - hy_spread : float — HY 스프레드 (bp)
        - ig_spread : float — IG 스프레드 (bp)
        - rrp_change_pct : float — 역레포 잔액 3개월 변화율 (%)
    """
    g = getGather(asOf)
    data: dict[str, float | None] = {}

    data["m2_yoy"] = fetchYoy(g, "M2SL")
    data["fed_bs_change_pct"] = fetchChangePct(g, "WALCL", 13)

    hy = fetchLatest(g, "BAMLH0A0HYM2")
    if hy is not None:
        data["hy_spread"] = hy * 100

    ig = fetchLatest(g, "BAMLC0A0CM")
    if ig is not None:
        data["ig_spread"] = ig * 100

    data["rrp_change_pct"] = fetchChangePct(g, "RRPONTSYD", 63)

    return {k: v for k, v in data.items() if v is not None}


def calcLiquidity(*, market: str = "US", asOf: str | None = None, overrides: dict | None = None, **kwargs) -> dict:
    """유동성 환경 종합 분석 — M2 + 연준 B/S + 신용스프레드 + FCI.

    Capabilities:
        M2 (광의통화) YoY + 연준 대차대조표 변동 (QE/QT) + HY/IG 신용스프레드
        + RRP 잔액 → 유동성 regime (abundant/neutral/tight) 합성 점수 +
        signals (판정 근거 list). 시카고 연준 NFCI (US 공식 지수) + 자체 FCI
        병렬 노출. Bridgewater/Brookings "전반적 금융 여건" 표준.

    Args:
        market: "US" | "KR".
        asOf: 기준일. None 시 최신.
        overrides: 지표 강제 치환 (예: ``{"m2_yoy": 5.0}``).

    Returns:
        dict:
            - ``market``/``regime``/``regimeLabel``/``score`` (─100~100).
            - ``signals`` (list[str]): 판정 근거.
            - ``nfci`` (dict | None, US 전용): 시카고 연준 공식 지수.
            - ``fci`` (dict | None): 자체 FCI + components.
            - ``timeseries`` (dict): m2 / hy_spread / ig_spread.

    Raises:
        없음.

    Example:
        >>> r = calcLiquidity(market="US")
        >>> r["regime"], r["score"]
        ('tight', -45.0)

    Guide:
        - regime "abundant" + 신용스프레드 < 300 bp = 위험자산 우호.
        - regime "tight" + HY spread > 500 bp = 신용 시장 경고 (위험자산 회피).
        - NFCI > 0 = 평균 대비 긴축, < 0 = 완화. 시카고 연준 표준.
        - QT 기간 (연준 B/S 축소) 와 신용스프레드 확대 동시 발생 = strong
          tight 신호.

    See Also:
        - ``classifyLiquidityRegime``: 5 변수 표준 라벨
        - ``capexPressure``: HY spread 변동 → 기업 capex
        - ``analyzeCycle``: macro cycle (본 함수 입력)

    When:
        ``analyzeSummary`` liquidity 축 진입점 + analyzeCycle 보조.

    How:
        _fetchLiquidityData → overrides → classifyLiquidityRegime → score 합산 →
        NFCI + 자체 FCI 병렬 dict 합성.

    Requires:
        FRED M2 + WALCL (연준 B/S) + HY/IG OAS + RRPONTSYD (KR 별도).

    AIContext:
        regime label + score + 핵심 signals 함께. NFCI vs 자체 FCI 차이
        있으면 양쪽 노출. overrides 사용 시 가정 명시.

    LLM Specifications:
        AntiPatterns:
            - 단일 지표 (M2 만) 로 regime 판단 — 본 함수가 5 변수 합성.
            - KR 에 NFCI 인용 — US 전용.
        OutputSchema:
            ``{market, regime, regimeLabel, score, signals: list, nfci: dict?,
              fci: dict, timeseries: dict}``.
        Prerequisites:
            FRED M2/WALCL/HY OAS/IG OAS/RRP.
        Freshness:
            주간 (FRED 갱신).
        Dataflow:
            FRED 5 변수 → classifyLiquidityRegime → score + signals → NFCI
            + 자체 FCI 추가.
        TargetMarkets: US (FRED + NFCI), KR (BOK + 자체 FCI).
    """
    data = _fetchLiquidityData(market, asOf=asOf)
    if overrides:
        data = applyOverrides(data, overrides)

    regime = classifyLiquidityRegime(
        m2Yoy=data.get("m2_yoy"),
        fedBsChangePct=data.get("fed_bs_change_pct"),
        hySpread=data.get("hy_spread"),
        igSpread=data.get("ig_spread"),
        rrpChangePct=data.get("rrp_change_pct"),
    )

    result = {
        "market": market.upper(),
        "regime": regime.regime,
        "regimeLabel": regime.regimeLabel,
        "score": regime.score,
        "signals": list(regime.signals),
        "status": regime.status,
        "observedInputs": regime.observedInputs,
        "totalInputs": regime.totalInputs,
    }

    # NFCI + 자체 FCI
    result["nfci"] = None
    result["fci"] = None
    g = getGather(asOf)

    if market.upper() == "US":
        nfci_val = fetchLatest(g, "NFCI")
        if nfci_val is not None:
            result["nfci"] = {
                "value": round(nfci_val, 3),
                "regime": "tight" if nfci_val > 0 else "loose",
                "regimeLabel": "긴축" if nfci_val > 0 else "완화",
                "description": f"NFCI {nfci_val:+.3f} — {'긴축' if nfci_val > 0 else '완화'} (평균=0)",
            }

    # 자체 FCI
    from dartlab.macro.crisis.fci import calcFCI

    if market.upper() == "US":
        sid_map = {
            "policy_rate": "FEDFUNDS",
            "long_rate": "DGS10",
            "credit_spread": "BAMLH0A0HYM2",
            "equity": "SP500",
            "fx": "DTWEXBGS",
        }
    else:
        sid_map = {
            "policy_rate": "BASE_RATE",
            "long_rate": "TREASURY_3Y",
            "credit_spread": "CORP_BOND_3Y",
            "fx": "USDKRW",
        }

    fci_vars: dict[str, list[float]] = {}
    for key, sid in sid_map.items():
        series = fetchSeriesList(g, sid)
        if series:
            fci_vars[key] = series

    if len(fci_vars) >= 3:
        fci_result = calcFCI(fci_vars, market=market)
        result["fci"] = {
            "value": fci_result.value,
            "regime": fci_result.regime,
            "regimeLabel": fci_result.regimeLabel,
            "components": fci_result.components,
            "description": fci_result.description,
        }

    result["timeseries"] = collectTimeseries(g, {"m2": "M2SL", "hy_spread": "BAMLH0A0HYM2", "ig_spread": "BAMLC0A0CM"})

    return result
