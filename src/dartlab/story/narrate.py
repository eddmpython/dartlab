"""Conditional Narrative Assembly — 데이터 값 기반 해석 문장 생성.

AP통신/Arria NLG 패턴: 변화율/수준/추세에 따라 조건 분기 → 해석 문장.
임계값과 레이블을 _THRESHOLDS에서 중앙 관리.
기준을 바꾸면 모든 해석 문장이 자동 반영.
"""

from __future__ import annotations

# ── 임계값 중앙 관리 ──
# (cutoff, label) 쌍.
# higher_is_better(기본): 값 > cutoff → label. 내림차순.
# lower_is_better: 값 < cutoff → label. 오름차순.

_THRESHOLDS: dict[str, dict] = {
    "growth_yoy": {
        "breakpoints": [(20, "급성장"), (5, "성장"), (-5, "보합"), (-20, "역성장"), (None, "급감")],
    },
    "growth_cagr": {
        "breakpoints": [(10, "견조"), (0, "완만한 성장"), (-5, "정체"), (None, "구조적 역성장")],
    },
    "margin_delta": {
        "breakpoints": [(5, "대폭 확대"), (1, "개선"), (-1, "보합"), (-5, "하락"), (None, "급락")],
    },
    "margin_level": {
        "breakpoints": [(20, "높은 마진"), (10, "양호한 마진"), (0, "낮은 마진"), (None, "영업적자")],
    },
    "debt_ratio": {
        "lower_is_better": True,
        "breakpoints": [
            (50, "매우 안정적인 자본 구조"),
            (100, "안정적인 자본 구조"),
            (200, "보통 수준의 레버리지"),
            (300, "다소 높은 레버리지"),
            (None, "과도한 레버리지"),
        ],
    },
    "ocf_to_ni": {
        "breakpoints": [
            (150, "이익 대비 현금 회수가 매우 우수하다 (감가상각 등 비현금 항목이 크다)"),
            (100, "이익이 현금으로 잘 뒷받침된다"),
            (60, "현금 전환이 다소 부족하다"),
            (0, "이익의 현금 뒷받침이 크게 부족하다"),
            (None, "영업현금흐름이 적자다"),
        ],
    },
    "hhi": {
        "breakpoints": [
            (5000, "매출이 단일 부문에 과도하게 집중되어 있다"),
            (2500, "상위 부문 의존도가 높다"),
            (1500, "적절히 다각화되어 있다"),
            (None, "매출이 고르게 분산되어 있다"),
        ],
    },
    "strategy_sharpe": {
        "breakpoints": [
            (1.0, "강한 통계적 우위"),
            (0.4, "양호한 우위"),
            (0.0, "중립"),
            (-0.3, "약한 비효율"),
            (None, "불리"),
        ],
    },
}

# 학술 출처 — 8 스타일별 (Phase 4 R5)
_STRATEGY_SOURCES: dict[str, str] = {
    "trendFollow": "TSMOM (Moskowitz-Ooi-Pedersen 2012)",
    "meanReversion": "Statistical Arbitrage (Avellaneda-Lee 2008)",
    "breakout": "Turtle System 1 (Faith 1980s, Donchian 1960s)",
    "dipBuy": "BTFD (강세장 단기 약세 진입)",
    "eventDriven": "PEAD (Bernard-Thomas 1989, 한국 Park-Chai 2020)",
    "flowFollow": "외국인 수급 단기 효과 (Choe-Kho-Stulz 2005)",
    "lowVolDefensive": "BAB (Frazzini-Pedersen 2014, self z-score 변형)",
    "seasonalKR": "TOM (Lakonishok-Smidt 1988, 한국재무학회 2018)",
}

_STRATEGY_LABELS: dict[str, str] = {
    "trendFollow": "추세추종",
    "meanReversion": "평균회귀",
    "breakout": "돌파",
    "dipBuy": "눌림목매수",
    "eventDriven": "이벤트드리븐",
    "flowFollow": "수급추종",
    "lowVolDefensive": "저변동방어",
    "seasonalKR": "한국캘린더",
}

_Z_SCORE_LABELS: dict[str, str] = {
    "안전": "단기 부실 위험은 낮다",
    "회색": "재무 악화 시 부실 전이 가능성이 있다",
    "위험": "부실 가능성에 주의가 필요하다",
}


def _classify(value: float, key: str) -> str:
    """값을 임계값 테이블에서 레이블로 변환."""
    cfg = _THRESHOLDS.get(key)
    if not cfg:
        return ""
    breakpoints = cfg["breakpoints"]
    lower_is_better = cfg.get("lower_is_better", False)

    if lower_is_better:
        for cutoff, label in breakpoints:
            if cutoff is None:
                return label
            if value < cutoff:
                return label
        return breakpoints[-1][1]

    for cutoff, label in breakpoints:
        if cutoff is None or value > cutoff:
            return label
    return breakpoints[-1][1] if breakpoints else ""


# ── 추세 감지 유틸 ──


def _detectTrend(values: list, minCount: int = 3) -> str | None:
    """숫자 리스트에서 추세 감지. 최신이 앞(index 0).

    비교는 등호 없이 한다. 예전에는 `>=` 로 판정하고 개선을 먼저 확인해서, 값이 하나도
    움직이지 않은 계열이 "improving" 으로 나왔다. 부채비율 100% 가 네 기 내내 그대로인
    회사가 "부채가 지속적으로 증가하는 추세" 로, 영업이익률 12% 가 그대로인 회사가
    "(보합)" 이라 적고 곧바로 "4기 연속 개선 중" 이라 적혔다. 한 문장이 자기를 뒤집었다.
    """
    valid = [v for v in values if v is not None]
    if len(valid) < minCount:
        return None
    if all(valid[i] == valid[i + 1] for i in range(len(valid) - 1)):
        return "flat"
    if all(valid[i] > valid[i + 1] for i in range(len(valid) - 1)):
        return "improving"
    if all(valid[i] < valid[i + 1] for i in range(len(valid) - 1)):
        return "declining"
    return "mixed"


# ── Narrate 함수 ──


# ── Quant 서사 5단계 (Phase 6) ──────────────────────────────────────────────
# analysis 가 재무 서사를 만들듯, quant 는 주가 서사를 만들어 story 에 준다.
# 5 분석 엔진 공통 패턴: 데이터 소비 → 분석기준·서사·관점·근거 → story 도구.


def narrateTrend(verdictData: dict | None) -> str:
    """추세 서사 — MA 정배열 + ADX + 12년 audit 근거."""
    if not verdictData:
        return "추세 데이터 없음."
    cats = verdictData.get("categories", {})
    trend = cats.get("trend", {})
    inds = trend.get("indicators", {})

    label = trend.get("label", "")
    ma = inds.get("ma_alignment", "혼조")
    ma_score = inds.get("ma_alignment_score", 0)
    adx = verdictData.get("adx") or inds.get("adx", 0)
    st = inds.get("supertrend", "")
    psar = inds.get("psar", "")

    if label == "강한 상승":
        text = f"추세 강한 상승 (MA {ma} {ma_score}단계, ADX {adx:.0f})"
        if st == "long" and psar == "long":
            text += ". Supertrend + PSAR 모두 상승 확인"
        text += ". 12년 audit t=7.63 검증 — 다음 20봉 수익률 통계 우위."
    else:
        text = f"추세 횡보 (MA {ma}, ADX {adx:.0f})"
        text += ". 방향성 약함 — 추세 전략 효과 제한적."
    return text


def narrateQuantRisk(riskData: dict | None, verdictData: dict | None) -> str:
    """리스크 서사 — ATR + 베타 + 변동성 등급."""
    if not riskData:
        return "리스크 데이터 없음."
    atr_pct = riskData.get("atrPercent", 0)
    vol_grade = riskData.get("volatilityGrade", "")
    beta_dict = riskData.get("beta") or (verdictData or {}).get("beta") or {}
    beta_val = beta_dict.get("value") if isinstance(beta_dict, dict) else beta_dict
    rsi = (verdictData or {}).get("rsi")

    parts = []
    if atr_pct:
        grade_ko = {"high": "높음", "medium": "보통", "low": "낮음"}.get(vol_grade, vol_grade)
        parts.append(f"일일 변동성 ATR {atr_pct:.1f}% ({grade_ko})")
    if beta_val is not None:
        if beta_val > 1.3:
            parts.append(f"베타 {beta_val:.2f} — 시장 하락 시 더 큰 손실")
        elif beta_val < 0.7:
            parts.append(f"베타 {beta_val:.2f} — 시장 대비 방어적")
        else:
            parts.append(f"베타 {beta_val:.2f}")
    if rsi is not None:
        if rsi >= 70:
            parts.append(f"RSI {rsi:.0f} 과매수 — 단기 조정 가능")
        elif rsi <= 30:
            parts.append(f"RSI {rsi:.0f} 과매도 — 반등 기대")
        else:
            parts.append(f"RSI {rsi:.0f} 중립")
    return ". ".join(parts) + "." if parts else "리스크 데이터 부족."


def narrateSignals(signalsData: dict | None) -> str:
    """수급 신호 서사 — 최근 20일 매수/매도 신호 집계."""
    if not signalsData:
        return "신호 데이터 없음."
    summary = signalsData.get("signalSummary", {})
    bullish = summary.get("bullish", 0)
    bearish = summary.get("bearish", 0)
    events = signalsData.get("recentEvents", [])

    parts = [f"최근 20일 매수 {bullish}건 / 매도 {bearish}건"]
    # 가장 최근 이벤트 1~2개 언급
    if events:
        recent = events[-2:]
        for ev in recent:
            parts.append(f"{ev.get('type', '')} {ev.get('direction', '')}")
    if bullish > bearish + 1:
        parts.append("→ 단기 매수 우위")
    elif bearish > bullish + 1:
        parts.append("→ 단기 매도 우위")
    else:
        parts.append("→ 매수·매도 균형")
    return ". ".join(parts) + "."


def narrateStrategyVerdict(strategyData: dict | None) -> str:
    """전략 검증 서사 — 스타일별 Sharpe + 오늘 진입 신호."""
    if not strategyData:
        return "전략 데이터 없음."
    style_ko = {
        "trendFollow": "추세추종",
        "meanReversion": "평균회귀",
        "breakout": "돌파",
        "dipBuy": "눌림목매수",
        "eventDriven": "이벤트드리븐",
        "flowFollow": "수급추종",
        "lowVolDefensive": "저변동방어",
        "seasonalKR": "한국캘린더",
    }
    strong = []
    active = []
    for key, ko in style_ko.items():
        snap = strategyData.get(key)
        if not snap or snap.get("status") != "ok":
            continue
        sharpe = snap.get("sharpe", 0)
        dsr = snap.get("dsr", 0)
        if sharpe >= 0.5 and dsr >= 0.7:
            strong.append(f"{ko} Sharpe {sharpe:+.2f} (DSR {dsr:.2f})")
        if snap.get("entry_today"):
            active.append(ko)

    parts = []
    if strong:
        parts.append("검증된 전략: " + ", ".join(strong[:3]))
    if active:
        parts.append("오늘 진입 활성: " + ", ".join(active))
    if not strong:
        parts.append("12년 검증에서 강한 우위 스타일 없음")
    return ". ".join(parts) + "."


def narrateCrosscheck(divergenceData: dict | None) -> str:
    """재무-시장 교차 서사 — analysis 등급 vs 기술적 판단 일치/불일치."""
    if not divergenceData:
        return "교차진단 데이터 없음."
    diagnosis = divergenceData.get("diagnosis", "")
    fin_grade = divergenceData.get("financialGrade", "")
    tech_verdict = divergenceData.get("technicalVerdict", "")

    if diagnosis:
        return f"재무-시장 교차: {diagnosis}."
    parts = []
    if fin_grade:
        parts.append(f"재무 등급 {fin_grade}")
    if tech_verdict:
        parts.append(f"기술 {tech_verdict}")
    if parts:
        return " + ".join(parts) + "."
    return "교차진단 정보 부족."


def narrateQuantConclusion(
    trendLabel: str,
    bullishSignals: int,
    bearishSignals: int,
    activeStyles: list[str],
    diagnosis: str,
) -> str:
    """결론 — 5 서사 방향 카운트 (가중치 X)."""
    bull = 0
    bear = 0
    if trendLabel == "강한 상승":
        bull += 1
    elif trendLabel == "횡보":
        pass  # 중립
    else:
        bear += 1
    if bullishSignals > bearishSignals + 1:
        bull += 1
    elif bearishSignals > bullishSignals + 1:
        bear += 1
    if activeStyles:
        bull += 1
    if "정합" in diagnosis or "일치" in diagnosis:
        bull += 1
    elif "괴리" in diagnosis or "불일치" in diagnosis:
        bear += 1

    if bull >= 3:
        return "**결론: 매수 우위** — 추세·수급·전략 정합."
    if bear >= 3:
        return "**결론: 매도 우위** — 추세 약세·수급 이탈·리스크 확대."
    if bull >= 2:
        return "**결론: 약한 매수 우위** — 일부 지표 긍정."
    if bear >= 2:
        return "**결론: 약한 매도 우위** — 일부 지표 부정."
    return "**결론: 혼조** — 분석 엔진 간 불일치, 관망 권장."


def narrateTechnicalVerdict(data: dict) -> str | None:
    """verdict 축 카테고리 → 한국어 1~2문장 (Phase 5, 12년 audit 통과분만).

    12년 audit 결과: trend 카테고리의 "강한 상승" (t=7.63@20d) 과
    "횡보" (t=-6.26@20d) 만 통계적 유의미. momentum/volatility/volume/pattern 전부 fail.
    과적합 아닌 진짜 신호만 narrate.
    """
    categories = data.get("categories") or {}
    trend = categories.get("trend")
    if not trend:
        return None

    inds = trend.get("indicators", {})
    ma = inds.get("ma_alignment", "")
    adx = inds.get("adx", 0)
    score = trend.get("score", 50)
    label = trend.get("label", "")

    # 기존 verdict 최상위 지표 참조 (rsi/adx/bbPosition — audit 통과 아니지만 참고 정보)
    rsi = data.get("rsi")
    bb = data.get("bbPosition")

    parts: list[str] = []

    if label == "강한 상승":
        parts.append(f"추세 강한 상승 (MA {ma}, ADX {adx:.0f}) — 12년 검증 유의미 (t=7.63)")
    else:
        parts.append(f"추세 횡보 (MA {ma}, ADX {adx:.0f}) — 방향성 약함")

    # 참고 지표 (audit 미통과이지만 사실 데이터로 노출)
    ref = []
    if rsi is not None:
        ref.append(f"RSI {rsi:.0f}")
    if bb is not None:
        ref.append(f"BB {bb:.0f}%")
    if ref:
        parts.append(f"참고: {', '.join(ref)}")

    return ". ".join(parts) + "."


def narrateGrowth(yoy: float | None, cagr: float | None) -> str | None:
    """매출 성장률 해석."""
    if yoy is None and cagr is None:
        return None
    parts = []
    if yoy is not None:
        label = _classify(yoy, "growth_yoy")
        parts.append(
            f"매출이 전년 대비 {yoy:+.1f}% {label}했다" if label != "보합" else f"매출이 {yoy:+.1f}%로 보합 수준이다"
        )
    if cagr is not None:
        label = _classify(cagr, "growth_cagr")
        parts.append(
            f"중기 CAGR {cagr:+.1f}%로 {label}"
            + ("하다" if label == "견조" else " 기조다" if "성장" in label else "다")
        )
    if yoy is not None and cagr is not None:
        if yoy > 10 and cagr < 0:
            parts.append("단기 반등이지만 중기 추세는 아직 하락이다")
        elif yoy < -10 and cagr > 5:
            parts.append("일시적 역성장이며 중기 성장 기조는 유효하다")
    return ". ".join(parts) + "." if parts else None


def narrateMargin(data: dict) -> str | None:
    """마진 추이 해석 — Phase 7: drivers (인과) + turningPoints (변화점) 자동 포함."""
    history = data.get("history", [])
    if len(history) < 2:
        return None
    latest, prev = history[0], history[1]
    opm = latest.get("operatingMargin")
    opm_prev = prev.get("operatingMargin")
    if opm is None or opm_prev is None:
        return None

    delta = opm - opm_prev
    direction = _classify(delta, "margin_delta")
    level = _classify(opm, "margin_level")
    text = f"영업이익률 {opm_prev:.1f}% → {opm:.1f}% ({direction}). {level} 수준"

    margins = [h.get("operatingMargin") for h in history[:4] if h.get("operatingMargin") is not None]
    trend = _detectTrend(margins)
    if trend == "improving":
        text += f"이며, {len(margins)}기 연속 개선 중이다"
    elif trend == "declining":
        text += f"이며, {len(margins)}기 연속 악화 추세다"
    elif trend == "flat":
        text += f"이며, {len(margins)}기 내내 같은 수준이다"
    else:
        text += "이다"
    text += "."

    # Phase 7 G24: drivers 자동 narrative (왜 그런가)
    drivers = latest.get("drivers") or []
    if drivers and abs(delta) >= 0.5:  # 변화 유의미 시만
        top = sorted(drivers, key=lambda d: abs(d.get("contribution_pp") or 0), reverse=True)[:2]
        parts = []
        for d in top:
            contrib = d.get("contribution_pp")
            if contrib is None or abs(contrib) < 0.3:
                continue
            sign = "+" if contrib > 0 else ""
            parts.append(f"{d['factor']} {sign}{contrib:.1f}%p")
        if parts:
            text += f" 주요 driver — {', '.join(parts)}."

    # Phase 7 G25: turningPoints — 최근 주요 변화점 1건
    tps = data.get("turningPoints") or []
    recent_tp = next((tp for tp in tps if tp.get("magnitude") in ("moderate", "major")), None)
    if recent_tp:
        direction_kr = "급등" if recent_tp["direction"] == "up" else "급락"
        text += f" {recent_tp['period']}에 {direction_kr} ({recent_tp['before']:.1f}% → {recent_tp['after']:.1f}%)."

    return text


def narrateCashFlow(data: dict, fmtAmt=None) -> str | None:
    """현금흐름 해석. fmtAmt는 금액 포맷 함수."""
    history = data.get("history", [])
    if not history:
        return None
    latest = history[0]
    fcf = latest.get("fcf")
    pattern = latest.get("pattern", "")
    if latest.get("ocf") is None:
        return None

    fmt = fmtAmt or (lambda v: f"{v:,.0f}")
    parts = []
    patLabel = pattern.split(" — ")[0] if pattern else ""
    if patLabel:
        parts.append(f"현금흐름 패턴은 '{patLabel}'")
    if fcf is not None:
        if fcf > 0:
            parts.append(f"FCF {fmt(fcf)}로 잉여현금 창출 중이다")
        else:
            parts.append(f"FCF {fmt(fcf)}로 투자가 영업현금을 초과한다")
    return ". ".join(parts) + "." if parts else None


def narrateCashQuality(data: dict) -> str | None:
    """이익의 현금 전환 해석.

    비율만 보고 판정하면 안 된다. 영업현금흐름을 순이익으로 나눈 값이라 순손실을 낸 회사는
    현금을 잘 벌어도 비율이 음수로 나온다. 예전에는 그것을 "영업현금흐름이 적자다" 라고
    읽어서, 영업현금이 손실의 두 배만큼 들어온 회사가 현금이 마르고 있다고 보고됐다.
    감액이나 초기 성장 국면에서 흔한 조합이고, 진짜 영업적자와 구분도 되지 않았다.
    """
    history = data.get("history", [])
    if not history:
        return None
    latest = history[0]
    ratio = latest.get("ocfToNi")
    if ratio is None:
        return None

    ocf = latest.get("ocf")
    if ocf is not None and ocf < 0:
        return f"영업CF/순이익 {ratio:.0f}%. 영업현금흐름이 적자다."
    if ocf is not None and ratio < 0:
        return f"영업CF/순이익 {ratio:.0f}%. 순손실이지만 영업에서는 현금이 들어온다."
    quality = _classify(ratio, "ocf_to_ni")
    return f"영업CF/순이익 {ratio:.0f}%. {quality}."


def narrateLeverage(data: dict) -> str | None:
    """레버리지 추이 해석."""
    history = data.get("history", [])
    if not history:
        return None
    latest = history[0]
    dr = latest.get("debtRatio")
    ndr = latest.get("netDebtRatio")
    if dr is None:
        return None

    level = _classify(dr, "debt_ratio")
    text = f"부채비율 {dr:.0f}%. {level}"
    if ndr is not None and ndr < 0:
        text += f". 순부채비율 {ndr:.0f}%로 순현금 상태다"

    drs = [h.get("debtRatio") for h in history[:4] if h.get("debtRatio") is not None]
    trend = _detectTrend(drs)
    if trend == "improving":
        text += ". 부채가 지속적으로 증가하는 추세다"
    elif trend == "declining":
        text += ". 부채를 꾸준히 줄이고 있다"
    elif trend == "flat":
        text += f". {len(drs)}기 내내 같은 수준이다"

    return text + "."


def narrateDistress(data: dict) -> str | None:
    """부실 판별 해석."""
    latest = data.get("latestScore")
    zone = data.get("zone", "")
    if latest is None:
        return None
    desc = _Z_SCORE_LABELS.get(zone, "판정 불가")
    return f"Altman Z-Score {latest:.2f} — {zone} 구간. {desc}."


def narrateROIC(data: dict) -> str | None:
    """ROIC vs WACC 해석 — Phase 7: drivers (Margin×Turnover×Tax 분해) + turningPoints 포함."""
    history = data.get("history", [])
    if not history:
        return None
    latest = history[0]
    roic = latest.get("roic")
    wacc = latest.get("waccEstimate")
    spread = latest.get("spread")
    if roic is None:
        return None

    text = f"ROIC {roic:.1f}%"
    if wacc is not None and spread is not None:
        if spread > 5:
            text += f", WACC {wacc:.1f}% 대비 Spread +{spread:.1f}%p — 투자한 자본이 높은 가치를 창출하고 있다"
        elif spread > 0:
            text += f", WACC 대비 Spread +{spread:.1f}%p — 자본비용을 상회하여 가치를 창출 중이다"
        else:
            text += f", WACC 대비 Spread {spread:+.1f}%p — 투자 자본이 가치를 파괴하고 있다"
    text += "."

    # Phase 7 G24: ROIC 변화 drivers (Margin × Turnover × Tax)
    drivers = latest.get("drivers") or []
    if drivers:
        top = sorted(drivers, key=lambda d: abs(d.get("contribution_pp") or 0), reverse=True)
        parts = []
        for d in top[:2]:
            contrib = d.get("contribution_pp")
            if contrib is None or abs(contrib) < 0.5:
                continue
            sign = "+" if contrib > 0 else ""
            parts.append(f"{d['factor']} {sign}{contrib:.1f}%p")
        if parts:
            text += f" ROIC 변화 driver — {', '.join(parts)}."

    # Phase 7 G25: ROIC turningPoints
    tps = data.get("turningPoints") or []
    recent_tp = next((tp for tp in tps if tp.get("magnitude") in ("moderate", "major")), None)
    if recent_tp:
        direction_kr = "급등" if recent_tp["direction"] == "up" else "급락"
        text += f" {recent_tp['period']}에 {direction_kr} ({recent_tp['before']:.1f}% → {recent_tp['after']:.1f}%)."

    # decomposition (Phase 1) — dominantDriver 도 첨부
    decomp = latest.get("decomposition") or {}
    dominant = decomp.get("dominantDriver")
    if dominant == "margin":
        text += " (마진 중심 ROIC — 가격 결정력 우위)"
    elif dominant == "turnover":
        text += " (자산회전 중심 ROIC — 효율성 우위)"

    return text


def narrateValuation(data: dict) -> str | None:
    """가치평가 종합 해석."""
    verdict = data.get("verdict", "")
    fvr = data.get("fairValueRange")
    price = data.get("currentPrice")
    if not verdict:
        return None

    text = f"종합 판정: {verdict}"
    if fvr and price and price > 0:
        mid = (fvr[0] + fvr[1]) / 2
        margin = (mid - price) / price * 100
        if margin > 30:
            text += f". 적정가 대비 {margin:.0f}% 할인 — 안전마진이 충분하다"
        elif margin > 0:
            text += f". 적정가 대비 {margin:.0f}% 할인 — 소폭 저평가"
        elif margin > -20:
            text += f". 적정가 대비 {margin:.0f}% 프리미엄 — 적정 수준"
        else:
            text += f". 적정가 대비 {abs(margin):.0f}% 프리미엄 — 고평가 주의"
    return text + "."


def narrateStrategy(snap: dict) -> str | None:
    """전략별 진입 진단 narrate (story 시장분석 6막 prospect).

    8 검증 스타일 백테스트 결과를 학술 출처 + 5년 결과 + 오늘 신호로 한국어 narrate.
    """
    if not snap:
        return None

    parts: list[str] = []

    # 1) 강한 우위 스타일 (sharpe ≥ 0.6 + DSR ≥ 0.7)
    strong = []
    for key, label in _STRATEGY_LABELS.items():
        s = snap.get(key)
        if not s or s.get("status") != "ok":
            continue
        if s.get("sharpe", 0) >= 0.6 and s.get("dsr", 0) >= 0.7:
            src = _STRATEGY_SOURCES.get(key, "")
            sharpe = s.get("sharpe", 0)
            dsr = s.get("dsr", 0)
            wr = s.get("winrate", 0) * 100
            strong.append(f"**{label}** ({src}) — Sharpe {sharpe:+.2f}, DSR {dsr:.2f}, 승률 {wr:.0f}%")
    if strong:
        parts.append("[5년 백테스트 강한 우위] " + " / ".join(strong) + ".")

    # 2) 오늘 진입 활성 신호
    active_today = []
    for key, label in _STRATEGY_LABELS.items():
        s = snap.get(key)
        if not s or s.get("status") != "ok":
            continue
        if s.get("entry_today"):
            stop = s.get("stop_level")
            stop_str = f", ATR stop {stop:,.0f}" if stop else ""
            active_today.append(f"**{label}**{stop_str}")
    if active_today:
        parts.append("[오늘 진입 신호 활성] " + ", ".join(active_today) + ".")

    # 3) 청산 신호
    exit_today = []
    for key, label in _STRATEGY_LABELS.items():
        s = snap.get(key)
        if not s or s.get("status") != "ok":
            continue
        if s.get("exit_today"):
            exit_today.append(label)
    if exit_today:
        parts.append("[오늘 청산 신호] " + ", ".join(exit_today) + ".")

    # 4) 데이터 한계/NotApplicable 명시
    limited = []
    for key, label in _STRATEGY_LABELS.items():
        s = snap.get(key)
        if not s:
            continue
        if s.get("status") == "data_limited":
            limited.append(f"{label}(데이터 부족)")
        elif s.get("status") == "not_applicable":
            limited.append(f"{label}(KR 전용)")
    if limited:
        parts.append("[제한] " + ", ".join(limited) + ".")

    # 5) 통계 신뢰도 경고 (DSR < 0.5)
    weak_dsr = []
    for key, label in _STRATEGY_LABELS.items():
        s = snap.get(key)
        if not s or s.get("status") != "ok":
            continue
        dsr = s.get("dsr", 0)
        sharpe = s.get("sharpe", 0)
        if abs(sharpe) > 0.3 and dsr < 0.5:
            weak_dsr.append(f"{label}(DSR {dsr:.2f})")
    if weak_dsr:
        parts.append("[⚠ 통계 신뢰도 약함] " + ", ".join(weak_dsr) + " — 우연 가능성 배제 어려움.")

    return " ".join(parts) if parts else None


def narrateConcentration(data: dict) -> str | None:
    """매출 집중도 해석."""
    hhi = data.get("hhi")
    label = data.get("hhiLabel", "")
    topPct = data.get("topPct")
    if hhi is None:
        return None

    level = _classify(hhi, "hhi")
    text = f"HHI {hhi:,.0f} ({label}). {level}"
    if topPct is not None:
        text += f". 1위 부문이 전체의 {topPct:.0f}%를 차지한다"
    return text + "."


def narrateMacroEnvironment(summary: dict) -> str | None:
    """종합 매크로 환경 → 1-2문장 서술."""
    if not summary:
        return None
    overall_label = summary.get("overallLabel", "")
    score = summary.get("score", 0)
    reasons = summary.get("reasons", [])
    if not overall_label:
        return None

    if score >= 1.0:
        tone = "경제 환경이 우호적이다"
    elif score <= -1.0:
        tone = "경제 환경이 비우호적이다"
    else:
        tone = "경제 환경이 혼조세다"

    parts = [f"{tone} (종합 {score:+.1f})."]
    if reasons:
        top = ", ".join(reasons[:2])
        parts.append(f"주요 근거: {top}.")
    return " ".join(parts)


# ── 막 결론 ──


def buildActSummary(actNum: str, sections: list, threads: list, usedIds: set[str] | None = None) -> str | None:
    """막 결론 문장 자동 생성. usedIds로 이미 사용한 thread를 추적한다."""
    actSectionKeys = {s.key for s in sections}
    used = usedIds if usedIds is not None else set()

    actThreads = [t for t in threads if actSectionKeys & set(t.involvedSections) and t.threadId not in used]

    if actThreads:
        priority = {"critical": 0, "warning": 1, "positive": 2, "neutral": 3}
        actThreads.sort(key=lambda t: priority.get(t.severity, 9))
        main = actThreads[0]
        used.add(main.threadId)
        return f"**{actNum}막 결론**: {main.story}"

    summaries = [s.summary for s in sections if getattr(s, "summary", None)]
    if summaries:
        return f"**{actNum}막 결론**: {' / '.join(summaries[:2])}"
    return None


# ── 인과 연쇄 narrate ──


def narrateCausalChain(metrics: dict) -> str | None:
    """핵심 비율 간 인과 방향을 감지하여 3막 인과 문장 생성.

    metrics: {opm_delta, fcf_delta_pct, debt_delta_pp, roe_delta, ic_delta} 변화량 dict.
    """
    if not metrics:
        return None

    parts = []

    opm_d = metrics.get("opm_delta")
    fcf_d = metrics.get("fcf_delta_pct")
    debt_d = metrics.get("debt_delta_pp")

    def _mag(v: float | None) -> str:
        if v is None:
            return ""
        return "급격히 " if abs(v) > 10 else "" if abs(v) < 3 else ""

    def _dir(v: float | None) -> str:
        if v is None:
            return ""
        return "상승" if v > 0 else "하락"

    if opm_d is not None and abs(opm_d) >= 2:
        parts.append(f"영업이익률이 {_mag(opm_d)}{abs(opm_d):.1f}%p {_dir(opm_d)}하면서")

    if fcf_d is not None and abs(fcf_d) >= 10:
        parts.append(f"FCF가 {abs(fcf_d):.0f}% {_dir(fcf_d)}")

    if debt_d is not None and abs(debt_d) >= 5:
        parts.append(f"부채비율이 {abs(debt_d):.0f}%p {_dir(debt_d)}")

    if len(parts) >= 2:
        chain = " → ".join(parts)
        conclusion = ""
        if opm_d and opm_d < -3 and debt_d and debt_d > 5:
            conclusion = " — 수익성 악화가 재무 부담으로 전이되는 구조"
        elif opm_d and opm_d > 3 and fcf_d and fcf_d > 15:
            conclusion = " — 수익성 개선이 현금흐름으로 확인되는 선순환"
        return chain + conclusion

    return None


# ── 업종 맥락 narrate ──


_SECTOR_CONTEXT: dict[str, str] = {
    "construction": (
        "건설업은 수주→시공→정산의 장기 사이클을 가진다. "
        "수주잔고 회전(잔고/매출)이 핵심 선행지표이며, "
        "도급(시공)과 자체개발(분양) 마진 갭이 수익성을 결정한다. "
        "PF(프로젝트파이낸싱) 노출은 하방 리스크의 핵심."
    ),
    "semiconductor": (
        "반도체는 3-5년 CAPEX 사이클에 지배된다. "
        "확장기에는 CAPEX/매출이 30%+로 급등하고, "
        "축소기에는 유지투자만으로 FCF가 급증한다. "
        "웨이퍼 ASP와 가동률이 분기 실적의 핵심 변수."
    ),
    "gaming": (
        "게임·엔터는 IP 포트폴리오의 집중도가 수익 변동성을 결정한다. "
        "단일 IP 의존(HHI>4000)은 신작 실패 시 급락 리스크. "
        "DAU/MAU 추이와 ARPU가 매출 방향의 선행지표."
    ),
    "pharma": (
        "제약·바이오는 R&D 투자→임상→승인→매출의 10년+ 사이클. "
        "Phase별 성공확률(Phase I 10%, Phase III 50%)이 파이프라인 가치를 결정한다. "
        "마일스톤/로열티 수익 구조와 특허 만료(patent cliff)가 핵심 리스크."
    ),
}


def narrateSectorContext(sector: str, kpis: dict | None) -> str | None:
    """업종 고정 맥락 + KPI 수치 동적 삽입."""
    base = _SECTOR_CONTEXT.get(sector)
    if not base:
        return None

    parts = [base]

    if kpis:
        if sector == "semiconductor":
            cc = kpis.get("capexCycle", {})
            if cc.get("phase"):
                parts.append(
                    f"현재 CAPEX 사이클: **{cc['phase']}** (CAPEX/매출 {cc.get('latest', '?')}%, 5Y 평균 {cc.get('avg', '?')}%)"
                )
        elif sector == "construction":
            cm = kpis.get("contractMix", {})
            if cm.get("contractRatio"):
                parts.append(f"매출 구성: 도급 {cm['contractRatio']:.0f}% / 자체개발 {cm.get('selfDevRatio', 0):.0f}%")
            pf = kpis.get("pfExposure", {})
            if pf.get("pfRelatedItems"):
                parts.append(f"PF 관련 충당부채 항목: {pf['pfRelatedItems']}건 감지")
        elif sector == "gaming":
            cc = kpis.get("contentConcentration", {})
            if cc.get("topIp"):
                parts.append(
                    f"주력 IP: {cc['topIp']} (매출 비중 {cc.get('topShare', '?')}%, 집중도 {cc.get('verdict', '?')})"
                )
        elif sector == "pharma":
            ps = kpis.get("pipelineStages", {})
            if ps.get("stages"):
                stage_str = ", ".join(f"{k} {v}건" for k, v in ps["stages"].items())
                parts.append(f"파이프라인 감지: {stage_str} (추정 평균 POS {ps.get('avgPOS', '?')}%)")
            rd = kpis.get("rdIntensity", {})
            if rd.get("latest"):
                parts.append(f"R&D 집중도: {rd['latest']:.1f}% ({rd.get('verdict', '')})")

    return " ".join(parts)


# ── How축 narrate (진단 → 처방) ──


def narrateImprovementLevers(data: dict) -> str | None:
    """개선 레버 시뮬레이션 → 자연어 처방."""
    levers = data.get("levers", [])
    if not levers:
        return None
    top = levers[0]
    base = data.get("baseCase", {})
    impact = top.get("impact", {})

    parts = [f"가장 효과적인 개선 레버는 **{top['name']}**이다."]
    if impact.get("opm") is not None and base.get("opm") is not None:
        parts.append(f"이를 달성하면 OPM이 {base['opm']:.1f}% → {impact['opm']:.1f}%로 개선된다.")
    if impact.get("fcf_change_pct") is not None:
        parts.append(f"FCF는 {impact['fcf_change_pct']:+.0f}% 변화한다.")
    if top.get("difficulty") and top.get("timeframe"):
        parts.append(f"난이도는 {top['difficulty']}, 예상 소요 기간은 {top['timeframe']}.")
    if len(levers) > 1:
        parts.append(f"차순위 레버는 {levers[1]['name']}.")
    return " ".join(parts)


def narrateGradeUpgrade(data: dict) -> str | None:
    """신용등급 상향 경로 → 자연어."""
    grade = data.get("currentGrade", "")
    target = data.get("targetGrade", "")
    weakest = data.get("weakestAxis", "")
    improvements = data.get("improvements", [])

    if not grade or not target:
        return None

    parts = [f"현재 {grade}에서 {target}로 상향하려면"]
    if weakest:
        parts.append(f"가장 약한 축인 **{weakest}**를 우선 개선해야 한다.")
    if improvements:
        imp = improvements[0]
        parts.append(f"구체적으로 {imp['change']}이 필요하다.")
    return " ".join(parts)


def narrateTechnicalAction(data: dict) -> str | None:
    """기술적 행동 목표 → 자연어."""
    verdict = data.get("technicalVerdict", "")
    current = data.get("currentPrice", 0)
    targets = data.get("targets", [])

    if not current:
        return None

    parts = [f"현재가 {current:,}원, 기술적 판정 **{verdict}**."]
    if data.get("support"):
        parts.append(f"지지선 {data['support']:,}원, 저항선 {data.get('resistance', 0):,}원.")
    if targets:
        t = targets[0]
        parts.append(f"{t['signal']} 시 {t['triggerPrice']:,}원에서 {t['action']} ({t['confidence']}).")
    return " ".join(parts)


def narrateCyclicalAction(data: dict) -> str | None:
    """사이클 대응 → 자연어."""
    phase = data.get("phaseLabel", "")
    actions = data.get("actions", [])

    if not phase:
        return None

    parts = [f"현재 사이클 국면: **{phase}**."]
    if actions:
        top = actions[0]
        parts.append(f"최우선 행동: {top['action']} — {top['reason']}.")
        if top.get("urgency") == "critical":
            parts.append("긴급도 최상.")
    precedent = data.get("historicalPrecedent")
    if precedent:
        parts.append(f"역사적 선례: {precedent}.")
    return " ".join(parts)


# ── dFV narrate ──


def narrateDFV(data: dict) -> str | None:
    """dFV v2 → 자연어 (anchor + 삼각검증)."""
    dfv = data.get("dFV")
    current = data.get("currentPrice")
    upside = data.get("upside")
    opinion = data.get("opinion", "")
    confidence = data.get("confidence", "")
    primary = data.get("primaryModel", "")

    if not dfv:
        return None

    parts = [f"**dartlab 적정주가 {dfv:,}원**"]
    if current and upside is not None:
        parts.append(f"(현재 {current:,}원 대비 {upside:+.1f}%).")
    parts.append(f"투자 의견 **{opinion}**, 신뢰도 **{confidence}**.")
    parts.append(f"Primary 모델: **{primary.upper()}**.")

    # Damodaran 생애주기 × 템플릿
    phase = data.get("lifeCyclePhase")
    template = data.get("companyType")
    if phase:
        try:
            from dartlab.story.templates import LIFECYCLE_PHASES

            phase_label = LIFECYCLE_PHASES.get(phase, {}).get("label", phase)
        except ImportError:
            phase_label = phase
        if template:
            parts.append(f"단계: **{template} × 생애주기 {phase_label}**.")
        else:
            parts.append(f"생애주기: **{phase_label}**.")

    # 삼각검증 결과
    tri = data.get("triangulation", {})
    checks = tri.get("checks", [])
    if checks:
        verdicts = [f"{c['method'].upper()}: {c['verdict']}({c['divergence']:.0f}%)" for c in checks]
        parts.append(f"삼각검증: {', '.join(verdicts)}.")

    # Quality WACC
    qw = data.get("qualityWACC", {})
    spread = qw.get("totalSpread", 0)
    if spread != 0:
        parts.append(f"Quality WACC 가감 {spread:+.1f}%p ({qw.get('adjustedWACC', 0):.1f}%).")

    # 시나리오
    sc = data.get("scenarios", {})
    if sc:
        parts.append(f"시나리오: Bull {sc.get('bull', 0):,} / Bear {sc.get('bear', 0):,}.")

    # Survival 가중 (Dark Side)
    surv = data.get("survival")
    if surv and surv.get("pSurvival") is not None:
        p = surv["pSurvival"]
        if p < 0.95:
            liq = surv.get("liquidationValue")
            liq_str = f" (청산가치 {liq:,.0f}원)" if liq else ""
            parts.append(f"생존가중 p={p:.2f} 적용{liq_str}.")

    # DDM floor
    floor = data.get("dividendFloor")
    if floor:
        parts.append(f"배당 하한 {floor['value']:,}원.")

    # Consistency flags (Damodaran 정합성 검증)
    flags = data.get("consistencyFlags") or []
    critical = [f for f in flags if f.get("severity") == "critical"]
    warns = [f for f in flags if f.get("severity") == "warn"]
    if critical:
        msgs = "; ".join(f["message"] for f in critical[:2])
        parts.append(f"⚠ 정합성 위반: {msgs}.")
    elif warns:
        parts.append(f"정합성 경고 {len(warns)}건 — 가정 재검토.")

    return " ".join(parts)


def narrateLifeCycle(data: dict | None) -> str | None:
    """calcLifeCycle 결과 → 자연어."""
    if not data or not data.get("phase"):
        return None
    try:
        from dartlab.story.templates import LIFECYCLE_PHASES

        meta = LIFECYCLE_PHASES.get(data["phase"], {})
    except ImportError:
        meta = {}
    label = meta.get("label", data["phase"])
    confidence = data.get("phaseConfidence", 0)
    signals = data.get("signals") or {}
    cagr = signals.get("revenueCAGR")
    spread = signals.get("roicWACCSpread")
    payout = signals.get("dividendPayout")
    parts = [f"생애주기 **{label}** (신뢰도 {confidence:.0%})."]
    if meta.get("description"):
        parts.append(meta["description"])
    extras = []
    if cagr is not None:
        extras.append(f"매출 CAGR {cagr:.1f}%")
    if spread is not None:
        extras.append(f"ROIC-WACC {spread:+.1f}%p")
    if payout is not None:
        extras.append(f"배당성향 {payout:.0f}%")
    if extras:
        parts.append(f"지표: {', '.join(extras)}.")
    inflection = data.get("inflection") or {}
    if inflection.get("towards"):
        try:
            target_label = LIFECYCLE_PHASES.get(inflection["towards"], {}).get("label", inflection["towards"])
        except Exception:
            target_label = inflection["towards"]
        parts.append(f"전환 신호: {target_label} 방향 (score {inflection.get('score', 0):.2f}).")
    if meta.get("valuationHint"):
        parts.append(f"권고 모델: {meta['valuationHint']}.")
    return " ".join(parts)


# Phase 5 G18: valuationSins 규칙별 Damodaran rationale + override 힌트
_SINS_RATIONALE: dict[str, dict[str, str]] = {
    "roic_wacc_persist": {
        "hint": "5~10년 내 ROIC-WACC spread 축소 고려 (경쟁 진입으로 abnormal return 소멸, Damodaran Ch.12)",
        "override": "overrides={'terminalGrowth': 2.5, 'growthRates': [현재×0.5]}",
    },
    "g_vs_rf": {
        "hint": "영구성장률은 무위험수익률 초과 불가 (Damodaran 상한 권고)",
        "override": "overrides={'terminalGrowth': rf-0.5}",
    },
    "tv_weight": {
        "hint": "Terminal Value 비중 75% 초과 시 explicit 구간 확장 필요 (Ch.12)",
        "override": "overrides={'growthYears': [기존×2]}",
    },
    "reinvest_identity": {
        "hint": "g = reinvestRate × ROIC 등식 위반 — 수학적 모순 (Ch.12)",
        "override": "overrides={'reinvestmentPath': [수정값]}",
    },
    "control_synergy_overlap": {
        "hint": "Control + Synergy 합산이 standalone × 50% 초과 — 이중계산 위험 (Dark Ch.17)",
        "override": "",
    },
    "margin_ceiling": {
        "hint": "영업마진이 업종 상위 1.5배 초과 — 경쟁 진입 시 마진 회귀 가능 (Ch.11)",
        "override": "overrides={'opm': peer_p75}",
    },
    "single_model": {
        "hint": "단일 방법론 의존 — 삼각검증 필요 (Damodaran 권고)",
        "override": "overrides={'primaryModel': 'rim'} 등으로 다중 모델 호출",
    },
    "story_numbers_gap": {
        "hint": "기업유형 미판정 — narrative 없는 valuation 은 Damodaran 원칙 위반",
        "override": "",
    },
}


def _formatFlag(flag: dict, marker: str) -> list[str]:
    """flag 1건 → 3줄 (reason / Damodaran hint / override)."""
    key = flag.get("key", "")
    reason = flag.get("reason", "")
    rationale = _SINS_RATIONALE.get(key, {})
    out = [f"{marker} {reason}"]
    if rationale.get("hint"):
        out.append(f"   ↳ {rationale['hint']}")
    if rationale.get("override"):
        out.append(f"   ↳ 대응: {rationale['override']}")
    return out


def narrateValuationSins(data: dict | None) -> str | None:
    """calcValuationSins → 자연어 (정합성 경고 + Damodaran rationale + override 힌트).

    Phase 5 G18: 위반 규칙별 _SINS_RATIONALE 자동 삽입.
    """
    if not data:
        return None
    flags = data.get("flags") or []
    if not flags:
        return "밸류에이션 정합성 — 위반 규칙 없음 (Damodaran 원칙 통과)."
    severity = data.get("severity", "info")
    critical = [f for f in flags if f.get("severity") == "critical"]
    warns = [f for f in flags if f.get("severity") == "warn"]
    info = [f for f in flags if f.get("severity") == "info"]
    parts: list[str] = [f"밸류에이션 검증 (전체 {severity}):"]
    for f in critical:
        parts.extend(_formatFlag(f, "🔴"))
    for f in warns:
        parts.extend(_formatFlag(f, "🟡"))
    if info and not (critical or warns):
        for f in info[:2]:
            parts.extend(_formatFlag(f, "ℹ"))
    return " ".join(parts)


def narrateStoryPrecedents(data: dict | None) -> str | None:
    """calcStoryPrecedents 결과 → 자연어 (Possible Test)."""
    if not data:
        return None
    count = data.get("count", 0)
    confidence = data.get("confidence", "low")
    if count == 0:
        return "유사 경로 선례 없음 — 새 서사. Damodaran 'Possible Test' 통과 실패."
    precedents = data.get("precedents") or []
    sample = [p.get("name") or p.get("stockCode") for p in precedents[:3] if p.get("name") or p.get("stockCode")]
    tail = f" (대표: {', '.join(sample)})" if sample else ""
    return f"유사 경로를 걸은 기업 {count}건 발견 (신뢰도 {confidence}){tail}."


# ════════════════════════════════════════════════════════════════════
# Sprint 2~7 신규 alpha narrate 12 함수 (story = 이야기꾼 사상 정합)
# ════════════════════════════════════════════════════════════════════


def narrateAltman(data: dict | None) -> str | None:
    """calcAltman 결과 → 자연어 (Z-Score 부실 진단)."""
    if not data:
        return None
    zones = data.get("zones") or {}
    distress = zones.get("distress", {})
    safe = zones.get("safe", {})
    universe = data.get("universe", 0)
    variant = data.get("variant", "z")
    return (
        f"{universe}개 종목 중 부실위험 {distress.get('pct', 0)}% ({distress.get('count', 0)}사), "
        f"안전 {safe.get('pct', 0)}%. Altman {variant.upper()} 모형."
    )


def narratePiotroski(data: dict | None) -> str | None:
    """calcPiotroski 결과 → 자연어 (F-Score 9점 재무건강)."""
    if not data:
        return None
    grades = data.get("grades") or {}
    strong = grades.get("strong", {})
    weak = grades.get("weak", {})
    universe = data.get("universe", 0)
    return (
        f"{universe}개 종목 중 strong (F≥7) {strong.get('pct', 0)}% ({strong.get('count', 0)}사), "
        f"weak (F≤3) {weak.get('pct', 0)}%. Piotroski 9점 재무건강."
    )


def narrateBeneish(data: dict | None) -> str | None:
    """calcBeneish 결과 → 자연어 (M-Score 이익조작 감지)."""
    if not data:
        return None
    flags = data.get("flags") or {}
    red = flags.get("redFlag", {})
    universe = data.get("universe", 0)
    return (
        f"{universe}개 종목 중 red flag (M > -1.78) {red.get('pct', 0)}% ({red.get('count', 0)}사). "
        "Beneish 8변수 이익조작 감지 모형."
    )


def narrateAccruals(data: dict | None) -> str | None:
    """calcAccruals 결과 → 자연어 (Sloan 발생액 품질)."""
    if not data:
        return None
    groups = data.get("groups") or {}
    high = groups.get("high", {})
    low = groups.get("low", {})
    universe = data.get("universe", 0)
    return (
        f"{universe}개 종목 중 high accrual (>+5%) {high.get('pct', 0)}% (reversal risk), "
        f"low (<-5%) {low.get('pct', 0)}% (cash quality premium 후보). Sloan 1996."
    )


def narrateQFactor(data: dict | None) -> str | None:
    """calcQFactor 결과 → 자연어 (Hou-Xue-Zhang q-factor composite)."""
    if not data:
        return None
    universe = data.get("universe", 0)
    topQ = data.get("topQ") or []
    sample = ", ".join(c for c, _ in topQ[:3])
    return f"{universe}개 종목 q-factor composite — 고 ROE + 저 asset growth 조합. top 3: {sample}. Hou-Xue-Zhang 2015."


def narrateQMJ(data: dict | None) -> str | None:
    """calcQMJ 결과 → 자연어 (Asness Quality minus Junk)."""
    if not data:
        return None
    universe = data.get("universe", 0)
    topQ = data.get("topQuality") or []
    sample = ", ".join(c for c, _ in topQ[:3])
    return (
        f"{universe}개 종목 QMJ composite — 고 수익성 + 저 레버리지 조합. "
        f"top 3 quality: {sample}. Asness-Frazzini-Pedersen 2019."
    )


def narrateBAB(data: dict | None) -> str | None:
    """calcBAB 결과 → 자연어 (저베타 프리미엄)."""
    if not data:
        return None
    universe = data.get("universe", 0)
    betaWindow = data.get("betaWindow", 252)
    topLow = data.get("topLow") or []
    return (
        f"{universe}개 종목 {betaWindow}일 beta — 저베타 분위가 BAB long 후보. "
        f"top 3 low-beta: {', '.join(c for c, _ in topLow[:3])}. Frazzini-Pedersen 2014."
    )


def narrateEarningsSurprise(data: dict | None) -> str | None:
    """calcEarningsSurprise 결과 → 자연어 (PEAD drift)."""
    if not data:
        return None
    universe = data.get("universe", 0)
    topPos = data.get("topPos") or []
    return (
        f"{universe}개 종목 SUE (YoY NI growth z-score) — positive SUE 상위가 PEAD drift long 후보. "
        f"top 3: {', '.join(t[0] for t in topPos[:3])}. Bernard-Thomas 1989."
    )


def narrateFundMomentum(data: dict | None) -> str | None:
    """calcFundamentalMomentum 결과 → 자연어 (펀더멘털×가격 모멘텀)."""
    if not data:
        return None
    universe = data.get("universe", 0)
    topD = data.get("topDouble") or []
    return (
        f"{universe}개 종목 펀더멘털×가격 composite — earnings + 12-1 price 모멘텀. "
        f"top 3 double: {', '.join(c for c, _ in topD[:3])}. Chordia-Shivakumar 2006."
    )


def narrateFactorTearSheet(data: dict | None) -> str | None:
    """calcFactorTearSheetAll 결과 → 자연어 (FF5 4팩터 long-short Sharpe)."""
    if not data:
        return None
    factors = data.get("factors") or []
    if not factors:
        return None
    strongest = data.get("strongest", "?")
    universe = data.get("universe", "?")
    year = data.get("year", "?")
    sharpes = ", ".join(f"{f.get('factorName')} {f.get('longShortSharpe', 0):+.2f}" for f in factors[:4])
    return f"{year}년 {universe}종목 Fama-French — {sharpes}. 가장 강한 팩터: {strongest}."


def narrateRiskDecomposition(data: dict | None) -> str | None:
    """calcMultiFactorRisk 결과 → 자연어 (Barra 시스템/고유 리스크 분해)."""
    if not data:
        return None
    sysR = data.get("systematicRisk")
    resR = data.get("residualRisk")
    totR = data.get("totalRisk")
    sysShare = data.get("systematicShare", 0)
    if sysR is None or resR is None:
        return None
    contribs = data.get("factorContributions") or {}
    top_contrib = ""
    if contribs:
        top = max(contribs.items(), key=lambda kv: abs(kv[1]))
        top_contrib = f", 최대 기여 {top[0]} {top[1]:+.0f}%"
    return (
        f"총 리스크 {totR:.1f}% = systematic {sysR:.1f}% ({sysShare:.0f}%) + idiosyncratic {resR:.1f}%. "
        f"Barra B Σ_f Bᵀ + D 분해{top_contrib}."
    )


def narrateFactorIC(data: dict | None) -> str | None:
    """calcFactorICAll 결과 → 자연어 (Cross-Sectional IC + ICIR)."""
    if not data:
        return None
    factors = data.get("factors") or []
    if not factors:
        return None
    strongest = data.get("strongest", "?")
    horizon = data.get("horizon", "?")
    icirs = ", ".join(f"{f.get('factorName')} ICIR {f.get('icir', 0):+.2f}" for f in factors[:4])
    return (
        f"{horizon}일 forward — {icirs}. 최강 예측력: {strongest}. Grinold & Kahn Ch.5 (look-ahead 방지 + non-overlap)."
    )
