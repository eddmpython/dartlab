"""구조화 투자논거 빌더 — ROIC−WACC 인과 + 밸류에이션으로 thesis 합성 (정규식 산문 폐기).

사상: thesis 는 형용사가 아니라 메커니즘이다. "강한 회사"가 아니라 "ROIC X%가 WACC를 Y%p
상회를 N년 방어 → 자본이 가치 창출". 데이터가 섞이면(사이클) 단정 대신 *조건부*로 정직하게
쓴다(과장 금지). 반증 가능(bearCase)·관점전환 트리거를 정량으로 결박.
self-calc 0 — ROIC 시계열은 L2 analysis(calcRoicTimeline)가 계산, 본 모듈은 해석·서사.
현재 계약은 ``docs/handbook/architecture/analysisProducts.md``에 정리돼 있다.
"""

from __future__ import annotations

from typing import Any


def _spreadPersistence(history: list[dict]) -> dict | None:
    """ROIC−WACC 스프레드 시계열(최신순) → 레벨·지속성·추세. None roic(미완연도) 제외."""
    valid = [h for h in history if h.get("roic") is not None and h.get("spread") is not None]
    if not valid:
        return None
    spreads = [h["spread"] for h in valid]
    n = len(spreads)
    mean = sum(spreads) / n
    posRatio = sum(1 for s in spreads if s > 0) / n
    half = n // 2
    trend = "stable"
    if half >= 1:
        recent = sum(spreads[:half]) / half
        old = sum(spreads[half:]) / (n - half)
        trend = "widening" if recent - old > 1 else "narrowing" if recent - old < -1 else "stable"
    return {
        "roicLatest": valid[0].get("roic"),
        "waccLatest": valid[0].get("waccEstimate"),
        "spreadLatest": spreads[0],
        "mean": round(mean, 2),
        "posRatio": round(posRatio, 2),
        "years": n,
        "trend": trend,
    }


def _composeCentral(sig: dict | None, conclusion: str) -> str:
    """스프레드 시그널 → 중심논거(메커니즘 1문장, 데이터 섞이면 조건부)."""
    if not sig or sig.get("roicLatest") is None or sig.get("waccLatest") is None:
        return conclusion or "초과수익 시그널 부족 — 자본수익성 판정 보류"
    roic, wacc, mean, pos, yrs = sig["roicLatest"], sig["waccLatest"], sig["mean"], sig["posRatio"], sig["years"]
    excess = roic - wacc
    if mean >= 2 and pos >= 0.7:
        return f"ROIC {roic:.1f}%가 WACC {wacc:.1f}%를 {excess:+.1f}%p 상회, 최근 {yrs}년 중 {pos * 100:.0f}% 기간 초과수익 방어 — 자본이 지속적으로 가치를 창출"
    if mean >= 0 and pos >= 0.4:
        return f"ROIC {roic:.1f}% vs WACC {wacc:.1f}% (최근 {excess:+.1f}%p) — 사이클 평균 초과수익 {mean:+.1f}%p의 조건부 가치 창출, 저점기 자본비용 미회수 병존"
    return f"ROIC {roic:.1f}%가 WACC {wacc:.1f}%를 평균 {mean:.1f}%p 하회 — 자본비용 미회수, 지속적 가치 창출 미확인(구조적 또는 사이클 저점)"


def _composeTriggers(sig: dict | None, warnings: list[str]) -> list[str]:
    """관점전환 트리거 — 스프레드 추세 + 경고 시그널(정량 결박)."""
    triggers: list[str] = []
    if sig:
        if sig["trend"] == "widening":
            triggers.append("ROIC−WACC 스프레드 추세가 narrowing 으로 전환 시 가치창출 논거 약화")
        elif sig["trend"] == "narrowing":
            triggers.append(
                f"ROIC−WACC 스프레드 narrowing 진행 중 — 최근 {sig['spreadLatest']:+.1f}%p, 추가 축소 시 해자 침식"
            )
        if sig["posRatio"] < 0.5:
            triggers.append("최근 분기 ROIC < WACC 지속 시 자본비용 미회수 고착")
    triggers.extend(warnings[:3])
    return triggers[:5]


def buildThesis(company: Any, card: Any, view: dict | None, *, basePeriod: str | None = None) -> dict | None:
    """ROIC−WACC 지속성 + SummaryCard + 밸류에이션 → 구조화 Thesis(반증 가능 인과 논증).

    동작: calcRoicTimeline(L2, lazy)에서 ROIC−WACC 스프레드 지속성을 측정 → 중심논거를
    메커니즘 1문장으로(데이터 섞이면 조건부) 합성, 지지기둥(스프레드·강점·밸류에이션)·약세론·
    관점전환 트리거·콜을 결박한다. self-calc 0 — 숫자는 L2 엔진 산출.

    Args:
        company: dartlab Company 인스턴스.
        card: story SummaryCard (conclusion/strengths/warnings).
        view: 계약 ValuationView dict 또는 None (intrinsic·current).
        basePeriod: 재무기간 cutoff (None=최신). 공시 가용일·시장데이터 vintage를
            고정하는 point-in-time 계약은 아님.

    Returns:
        dict | None: 계약 Thesis (central·pillars·bearCase·triggers·call). 재료 전무 시 None.

    Example:
        >>> buildThesis(dartlab.Company("005930"), card, view)
        {"central": "ROIC 9.9% vs WACC 8.7% ...", "pillars": [...], "call": "..."}

    Raises:
        없음 — calcRoicTimeline 실패 시 conclusion 폴백.
    """
    conclusion = getattr(card, "conclusion", "") if card else ""
    strengths = list(getattr(card, "strengths", []) or []) if card else []
    warnings = list(getattr(card, "warnings", []) or []) if card else []

    sig = None
    try:
        from dartlab.analysis.financial._investmentAnalysisRoic import calcRoicTimeline

        tl = calcRoicTimeline(company, basePeriod=basePeriod)
        sig = _spreadPersistence((tl or {}).get("history") or [])
    except Exception:  # noqa: BLE001 — thesis 는 ROIC 실패해도 conclusion 폴백
        sig = None

    if not sig and not conclusion and not strengths:
        return None

    central = _composeCentral(sig, conclusion)

    pillars: list[dict] = []
    if sig and sig.get("roicLatest") is not None:
        pillars.append(
            {
                "claim": f"ROIC {sig['roicLatest']:.1f}% · WACC {sig['waccLatest']:.1f}% · 스프레드 최근 {sig['spreadLatest']:+.1f}%p (추세 {sig['trend']}, {sig['years']}년)",
                "sectionKey": "수익체력",
                "refs": [],
            }
        )
    for s in strengths[: (2 if pillars else 3)]:
        pillars.append({"claim": s, "sectionKey": "", "refs": []})

    bearCase = ""
    if sig and (sig["mean"] < 0 or sig["trend"] == "narrowing"):
        bearCase = f"ROIC−WACC 스프레드가 {'평균 음수' if sig['mean'] < 0 else 'narrowing 추세'} — 자본비용 미회수 고착이 핵심 약세 시나리오"
    elif warnings:
        bearCase = warnings[0]

    call = None
    if view and view.get("intrinsic") and view.get("current"):
        iv, cur = view["intrinsic"], view["current"]
        upside = (iv - cur) / cur * 100 if cur else 0
        call = f"내재가치 {iv:,}원 vs 현재가 {cur:,}원 ({upside:+.1f}%)"
    elif view and view.get("intrinsic"):
        call = f"내재가치 {view['intrinsic']:,}원 (현재가 미확인)"

    return {
        "central": central,
        "pillars": pillars,
        "bearCase": bearCase,
        "triggers": _composeTriggers(sig, warnings),
        "call": call,
    }


__all__ = ["buildThesis"]
