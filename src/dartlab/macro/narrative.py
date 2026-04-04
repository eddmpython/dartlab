"""macro 보고서 서사 엔진 — 숫자를 의미로 변환.

3계층: Atomic(지표→문장) → Section(What-Why-SoWhat) → Transition(막간 인과)

설계 원칙 (Goldman/BIS/IMF/Bridgewater 참고):
- 결론 먼저 (역피라미드)
- 인과 연결어 사용 (때문이다, 반면, 지속되면)
- What-Why-So What 3문장
- 교차 분석 (축 간 모순/확인 감지)
"""

from __future__ import annotations


# ══════════════════════════════════════
# 이상값 검증
# ══════════════════════════════════════

_VALID_RANGES = {
    "gdpEstimate": (-10, 20),
    "probability": (0, 1),
    "fci": (-5, 5),
    "score": (-10, 10),
    "ponziRatio": (0, 1),
    "leverageLevel": (0, 500),
}


def _safe(value, key: str = "") -> float | None:
    """이상값 검증. 범위 밖이면 None."""
    if value is None or not isinstance(value, (int, float)):
        return None
    if key in _VALID_RANGES:
        lo, hi = _VALID_RANGES[key]
        if not (lo <= value <= hi):
            return None
    return value


# ══════════════════════════════════════
# Layer 1: Atomic — 지표 해석 1문장
# ══════════════════════════════════════


def _narrate_fci(fci: dict) -> str:
    """FCI What-Why-So What."""
    val = _safe(fci.get("value"), "fci")
    if val is None:
        return ""
    regime = fci.get("regimeLabel", "")
    comps = fci.get("components") or {}

    # What
    what = f"금융환경은 {regime}적이다 (FCI {val:+.2f})."

    # Why — 가장 큰 기여 변수
    if comps:
        sorted_comps = sorted(comps.items(), key=lambda x: -abs(x[1]))
        dominant = sorted_comps[0]
        direction = "상승" if dominant[1] > 0 else "하락"
        why = f"이는 {dominant[0]} {direction}(z={dominant[1]:+.1f})이 주도하기 때문이다."
    else:
        why = ""

    # So What
    if val < -0.5:
        so_what = "완화적 환경은 위험자산에 우호적이나, 과열 징후를 경계해야 한다."
    elif val > 0.5:
        so_what = "긴축적 환경은 기업 자금조달 비용을 높이고 경기에 부정적이다."
    else:
        so_what = "중립적 환경으로 방향 전환 신호를 주시해야 한다."

    return f"{what} {why} {so_what}"


def _narrate_cycle(cycle: dict) -> str:
    """사이클 국면 해석."""
    phase = cycle.get("phaseLabel", "")
    confidence = cycle.get("confidence", "")
    signals = cycle.get("signals") or []

    if not phase:
        return ""

    what = f"경제는 {phase} 국면에 있다."

    if signals:
        why = f"주요 근거는 {', '.join(signals[:2])}이다."
    else:
        why = ""

    if confidence == "low":
        so_what = "신뢰도가 낮아 국면 전환 가능성이 있다 — 가장 주의해야 할 시점이다."
    elif phase in ("expansion", "recovery"):
        so_what = "확장 환경에서는 위험자산 비중 유지가 적절하다."
    elif phase == "contraction":
        so_what = "수축 환경에서는 방어적 포지션과 유동성 확보가 우선이다."
    else:
        so_what = "둔화 환경에서는 포트폴리오 리밸런싱을 준비해야 한다."

    return f"{what} {why} {so_what}"


def _narrate_rates(rates: dict) -> str:
    """금리 환경 해석."""
    outlook = rates.get("outlook") or {}
    direction = outlook.get("direction", "")
    yc = rates.get("yieldCurve") or {}
    rr = rates.get("realRateRegime") or {}
    emp = rates.get("employment") or {}
    inf = rates.get("inflation") or {}

    parts = []

    if direction:
        what = f"금리 방향은 {direction}이다."
        parts.append(what)

    # NS 곡선 해석
    interp = yc.get("interpretation", "")
    if interp == "inverted":
        parts.append("수익률곡선이 역전되어 있다 — 역사적으로 6-18개월 후 침체를 선행한다.")
    elif interp == "steep_normal":
        parts.append("수익률곡선이 가파른 정상이다 — 시장이 경기 확장과 인플레이션 지속을 반영한다.")
    elif interp == "flat":
        parts.append("수익률곡선이 평탄화되고 있다 — 경기 둔화 가능성에 주의해야 한다.")

    # 실질금리 regime
    regime = rr.get("regime", "")
    if regime == "tightening":
        parts.append("실질금리 상승 + BEI 상승은 금융 긴축을 의미한다.")
    elif regime == "deflation":
        parts.append("실질금리 높고 BEI 낮음은 디플레이션 위험을 시사한다.")
    elif regime == "goldilocks":
        parts.append("실질금리와 BEI 모두 안정적인 골디락스 구간이다.")

    # 고용-물가 교차
    emp_state = emp.get("state", "")
    inf_state = inf.get("state", "")
    if emp_state == "strong" and inf_state == "hot":
        parts.append("고용이 강하면서 물가도 높다 — 스태그플레이션 위험이 아닌지 확인이 필요하다.")
    elif emp_state == "weak" and inf_state == "cool":
        parts.append("고용과 물가 모두 냉각되고 있다 — 금리 인하 압력이 강해질 것이다.")
    elif emp_state == "strong" and inf_state in ("cool", "target"):
        parts.append("고용은 탄탄하고 물가는 안정적이다 — 이상적인 환경이다.")

    return " ".join(parts)


def _narrate_crisis(crisis: dict) -> str:
    """위기 프레임워크 해석."""
    parts = []

    minsky = crisis.get("minskyPhase") or {}
    phase = minsky.get("phase", "")
    if phase == "overtrading":
        parts.append("Minsky 관점에서 과열 국면이다 — 신용 팽창과 자산 급등이 동시에 진행 중이다.")
    elif phase == "discredit":
        parts.append("Minsky 공황 국면의 징후가 보인다 — 신용 경색이 시작되고 있다.")
    elif phase == "boom":
        parts.append("Minsky 호황 국면이다 — 신용이 확장 중이지만 아직 과열은 아니다.")

    koo = crisis.get("kooRecession") or {}
    if koo.get("isBSR"):
        parts.append(f"민간 금융잉여가 GDP의 {koo.get('privateSurplus', 0):.1f}%에 달하고 금리가 낮다 — "
                     "대차대조표 침체 징후다. 금리 인하만으로는 부족하고 재정 확대가 필수적이다.")

    fisher = crisis.get("fisherDeflation") or {}
    if fisher.get("risk") == "high":
        parts.append("부채서비스비율이 높고 물가가 하락 중이다 — Fisher 부채-디플레이션 악순환 위험이 있다.")

    ghs = crisis.get("ghsScore") or {}
    prob = ghs.get("crisisProb", 0)
    if prob > 0.2:
        parts.append(f"GHS 모델 기준 3년 내 금융위기 확률이 {prob * 100:.0f}%이다 — 신용 팽창과 자산가격 급등이 동시에 진행 중이다.")

    if not parts:
        parts.append("현재 구조적 위기 징후는 관측되지 않는다.")

    return " ".join(parts)


def _narrate_corporate(corporate: dict) -> str:
    """기업 실태 해석."""
    ec = corporate.get("earningsCycle") or {}
    pr = corporate.get("ponziRatio") or {}
    lc = corporate.get("leverageCycle") or {}

    parts = []

    direction = ec.get("currentDirection", "")
    yoys = ec.get("yoyChanges") or []
    last_yoy = yoys[-1] if yoys and yoys[-1] is not None else None

    if direction == "contracting" and last_yoy is not None:
        parts.append(f"전종목 영업이익이 YoY {last_yoy:+.1f}%로 수축 중이다.")
    elif direction == "expanding" and last_yoy is not None:
        parts.append(f"전종목 영업이익이 YoY {last_yoy:+.1f}%로 확장 중이다.")

    ponzi = _safe(pr.get("currentRatio"), "ponziRatio")
    if ponzi is not None:
        if ponzi > 0.3:
            parts.append(f"Ponzi비율 {ponzi:.1%}로 상장기업의 {ponzi:.0%}이 영업이익으로 이자를 충당하지 못한다 — 금융 시스템 취약성이 높아지고 있다.")
        elif ponzi > 0.2:
            parts.append(f"Ponzi비율 {ponzi:.1%}로 경계 수준이다.")

    lev = lc.get("currentLevel")
    trend = lc.get("trendLabel", "")
    if lev is not None and trend == "상승":
        parts.append(f"부채비율 중간값 {lev:.1f}%로 상승 추세이다 — 레버리지 축적이 진행 중이다.")

    # 교차: 이익 수축 + Ponzi 상승 = 위험
    if direction == "contracting" and ponzi is not None and ponzi > 0.3:
        parts.append("이익이 수축하면서 Ponzi비율이 높다 — 기업 부도 위험이 상승하고 있다.")

    return " ".join(parts) if parts else ""


def _narrate_trade(trade: dict) -> str:
    """교역 해석 (KR)."""
    tot = trade.get("termsOfTrade") or {}
    proxy = trade.get("totProxy") or {}
    ep = trade.get("exportProfit") or {}
    usc = trade.get("usConsumptionLink") or {}

    parts = []

    tot_dir = tot.get("directionLabel", "")
    proxy_dir = proxy.get("directionLabel", "")

    if tot_dir:
        parts.append(f"교역조건은 {tot_dir} 추세이다.")

    # 교역조건과 대용치 방향 비교
    if tot_dir and proxy_dir and tot_dir != proxy_dir:
        parts.append(f"그러나 교역조건 대용치(환율-유가)는 {proxy_dir}을 보이고 있어 신호가 엇갈린다.")
    elif proxy_dir:
        parts.append(f"교역조건 대용치도 {proxy_dir}으로 방향이 일치한다.")

    ep_signal = ep.get("signalLabel", "")
    if ep_signal:
        parts.append(f"수출기업 이익 선행 신호는 {ep_signal}이다.")

    us_impl = usc.get("implication", "")
    if us_impl:
        parts.append(f"미국 소비와의 연결: {us_impl}")

    return " ".join(parts) if parts else ""


# ══════════════════════════════════════
# Layer 2: 교차 분석 — 축 간 모순/확인
# ══════════════════════════════════════


def detect_conflicts(summary: dict) -> list[str]:
    """상충하는 신호를 감지하여 해석."""
    conflicts = []

    forecast = summary.get("forecast") or {}
    cycle = summary.get("cycle") or {}
    crisis = summary.get("crisis") or {}
    sentiment = summary.get("sentiment") or {}
    inventory = summary.get("inventory") or {}
    corporate = summary.get("corporate") or {}

    # Hamilton contraction vs LEI expansion
    hamilton = forecast.get("hamiltonRegime") or {}
    lei = forecast.get("lei") or {}
    h_regime = hamilton.get("currentRegime", "")
    l_signal = lei.get("signal", "") or lei.get("growthSignal", "")
    if "contraction" in h_regime and l_signal == "expansion":
        conflicts.append(
            "Hamilton RS가 수축 국면을 감지하지만 LEI는 확장을 보이고 있다. "
            "Hamilton은 GDP 분기 데이터 기반이고 LEI는 월간 선행지표 기반이므로 "
            "시차가 존재한다 — LEI 방향이 향후 Hamilton 전환을 예고할 수 있다."
        )

    # 심리 공포 vs 사이클 확장
    fg = (sentiment.get("fearGreed") or {}).get("score")
    phase = cycle.get("phase", "")
    if fg is not None and fg < 30 and phase in ("expansion", "recovery"):
        conflicts.append(
            f"시장 심리가 공포(F&G {fg:.0f})인 반면 사이클은 {cycle.get('phaseLabel', '')} 국면이다. "
            "일시적 충격(VIX 급등 등)일 가능성이 높으며, 역투자 기회일 수 있다."
        )

    # 이익 수축 vs 재고 보충
    ec_dir = (corporate.get("earningsCycle") or {}).get("currentDirection", "")
    inv_phase = (inventory.get("inventoryPhase") or {}).get("phase", "")
    if ec_dir == "contracting" and inv_phase in ("active_restock", "passive_destock"):
        conflicts.append(
            "기업 이익이 수축 중인데 재고순환은 보충/바닥 국면이다. "
            "재고 사이클이 이익에 선행하므로, 이익 회복의 초기 신호일 수 있다."
        )

    return conflicts


# ══════════════════════════════════════
# Layer 3: Transition Narrator — 막간 인과
# ══════════════════════════════════════


def generate_circulation_summary(summary: dict, template: str = "normal") -> str:
    """순환 서사 — 보고서 첫 단락. 결론 먼저."""
    cycle_text = _narrate_cycle(summary.get("cycle") or {})
    crisis_text = _narrate_crisis(summary.get("crisis") or {})
    corporate_text = _narrate_corporate(summary.get("corporate") or {})
    trade_text = _narrate_trade(summary.get("trade") or {})

    if template == "crisis":
        return f"{crisis_text} {corporate_text} {cycle_text}".strip()
    elif template == "kr":
        return f"{cycle_text} {trade_text} {corporate_text}".strip()
    else:
        fci_text = _narrate_fci((summary.get("liquidity") or {}).get("fci") or {})
        return f"{cycle_text} {fci_text} {corporate_text}".strip()


def generate_act_transition(act: int, summary: dict) -> str:
    """막 간 인과 연결."""
    if act == 1:
        # 1막→2막: 국면의 원인
        parts = []
        crisis = summary.get("crisis") or {}
        liquidity = summary.get("liquidity") or {}

        minsky = crisis.get("minskyPhase") or {}
        if minsky.get("phaseLabel"):
            parts.append(f"Minsky 관점에서 현재는 {minsky['phaseLabel']} 국면이다")

        fci = liquidity.get("fci") or {}
        if fci.get("regimeLabel"):
            parts.append(f"금융환경은 {fci['regimeLabel']}적이다")

        corporate = summary.get("corporate") or {}
        ponzi = (corporate.get("ponziRatio") or {}).get("currentRatio")
        if ponzi is not None and ponzi > 0.25:
            parts.append(f"기업 Ponzi비율이 {ponzi:.1%}로 취약하다")

        if parts:
            return "이 국면의 구조적 배경: " + ", ".join(parts) + "."
        return ""

    if act == 2:
        # 2막→3막: 원인에서 전망으로
        forecast = summary.get("forecast") or {}
        rp = forecast.get("recessionProb") or {}
        prob = _safe(rp.get("probability"), "probability")

        hamilton = forecast.get("hamiltonRegime") or {}
        regime = hamilton.get("currentRegime", "")

        parts = []
        if prob is not None:
            if prob > 0.3:
                parts.append(f"침체확률이 {prob * 100:.0f}%로 경계 수준이다")
            else:
                parts.append(f"침체확률은 {prob * 100:.0f}%로 낮다")

        conflicts = detect_conflicts(summary)
        if conflicts:
            parts.append("다만 " + conflicts[0])

        if parts:
            return "전망: " + ". ".join(parts) + "."
        return "전망: 현재 추세가 지속될 가능성이 높다."

    return ""


def generate_so_what(summary: dict) -> str:
    """So What — 투자 시사점. 왜 이 비중인가."""
    allocation = summary.get("allocation") or {}
    strategies = summary.get("strategies") or {}

    parts = []

    eq = allocation.get("equity", 0)
    if eq >= 60:
        parts.append(f"주식 비중 {eq}%는 확장 환경과 완화적 금융조건을 반영한다.")
    elif eq <= 30:
        parts.append(f"주식 비중 {eq}%는 수축/위기 환경에서의 방어적 포지션이다.")

    rationale = allocation.get("rationale") or []
    if rationale:
        parts.append("근거: " + " / ".join(rationale[:3]))

    bullish = strategies.get("bullish", 0)
    bearish = strategies.get("bearish", 0)
    if bullish > bearish * 3:
        parts.append(f"40전략 중 bullish {bullish}개로 시장 환경이 전반적으로 우호적이다.")
    elif bearish > bullish:
        parts.append(f"40전략 중 bearish {bearish}개로 방어가 필요한 환경이다.")

    return " ".join(parts) if parts else ""


def generate_rates_narrative(rates: dict) -> str:
    """금리 환경 서사."""
    return _narrate_rates(rates)
