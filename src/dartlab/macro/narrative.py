"""macro 보고서 서사 자동 생성 — 인과 연결 문장."""

from __future__ import annotations


def generate_circulation_summary(summary: dict) -> str:
    """순환 서사 요약 — 보고서 첫 단락."""
    parts = []

    # 국면
    cycle = summary.get("cycle") or {}
    phase = cycle.get("phaseLabel")
    if phase:
        parts.append(f"현재 경제는 {phase} 국면에 있다.")

    # 침체확률
    forecast = summary.get("forecast") or {}
    rp = forecast.get("recessionProb") or {}
    prob = rp.get("probability")
    if prob is not None:
        parts.append(f"침체확률 {prob * 100:.0f}%({'낮음' if prob < 0.2 else '경계' if prob < 0.4 else '높음'}).")

    # FCI
    liq = summary.get("liquidity") or {}
    fci = liq.get("fci") or {}
    fci_val = fci.get("value")
    if fci_val is not None:
        parts.append(f"FCI {fci_val:+.2f}({fci.get('regimeLabel', '')}).")

    # 기업집계
    corporate = summary.get("corporate") or {}
    pr = corporate.get("ponziRatio") or {}
    ponzi = pr.get("currentRatio")
    if ponzi is not None:
        parts.append(f"Ponzi비율 {ponzi:.1%}{'(경계)' if ponzi > 0.3 else ''}.")

    # 금리
    rates = summary.get("rates") or {}
    yc = rates.get("yieldCurve")
    if yc:
        parts.append(yc.get("description", ""))

    # 종합
    overall = summary.get("overallLabel", "")
    score = summary.get("score", 0)
    if overall:
        parts.append(f"종합 판정: {overall} ({score:+.1f}).")

    return " ".join(parts)


def generate_act_transition(act: int, summary: dict) -> str:
    """막 간 인과 연결 문장."""
    cycle = summary.get("cycle") or {}
    phase = cycle.get("phase", "")
    crisis = summary.get("crisis") or {}
    forecast = summary.get("forecast") or {}

    if act == 1:
        # 1막→2막: 국면의 원인
        cg = crisis.get("creditGap") or {}
        gap_label = cg.get("zoneLabel", "")
        minsky = crisis.get("minskyPhase") or {}
        minsky_label = minsky.get("phaseLabel", "")
        if gap_label or minsky_label:
            return f"이 국면의 배경: 신용환경 {gap_label}, Minsky {minsky_label}."
        return ""

    if act == 2:
        # 2막→3막: 원인에서 전망으로
        rp = forecast.get("recessionProb") or {}
        prob = rp.get("probability", 0)
        hamilton = forecast.get("hamiltonRegime") or {}
        regime = hamilton.get("currentRegime", "")
        parts = []
        if prob > 0.3:
            parts.append(f"침체확률이 {prob * 100:.0f}%로 경계 수준")
        if regime == "contraction":
            parts.append("Hamilton RS가 수축 국면을 감지")
        if parts:
            return "전망: " + ", ".join(parts) + "."
        return "전망: 현재 추세 지속 전망."

    return ""


def generate_so_what(summary: dict) -> str:
    """So What — 투자 시사점."""
    parts = []

    allocation = summary.get("allocation")
    if allocation:
        parts.append(
            f"자산배분: 주식 {allocation.get('equity', 0)}%, "
            f"채권 {allocation.get('bond', 0)}%, "
            f"금 {allocation.get('gold', 0)}%, "
            f"현금 {allocation.get('cash', 0)}%."
        )

    strategies = summary.get("strategies")
    if strategies:
        active = strategies.get("active", 0)
        bullish = strategies.get("bullish", 0)
        bearish = strategies.get("bearish", 0)
        parts.append(f"40전략 중 {active}개 활성 (bullish {bullish}, bearish {bearish}).")

    if not parts:
        return ""
    return " ".join(parts)
