"""Conditional Narrative Assembly — 데이터 값 기반 해석 문장 생성.

AP통신/Arria NLG 패턴: 변화율/수준/추세에 따라 조건 분기 → 해석 문장.
임계값과 레이블을 _THRESHOLDS에서 중앙 관리.
기준을 바꾸면 모든 해석 문장이 자동 반영.
"""

from __future__ import annotations

# ── 임계값 중앙 관리 ──
# (cutoff, label) 쌍. 값이 cutoff 초과일 때 해당 label 적용.
# None은 나머지(else).

_THRESHOLDS: dict[str, list[tuple[float | None, str]]] = {
    "growth_yoy": [
        (20, "급성장"), (5, "성장"), (-5, "보합"), (-20, "역성장"), (None, "급감"),
    ],
    "growth_cagr": [
        (10, "견조"), (0, "완만한 성장"), (-5, "정체"), (None, "구조적 역성장"),
    ],
    "margin_delta": [
        (5, "대폭 확대"), (1, "개선"), (-1, "보합"), (-5, "하락"), (None, "급락"),
    ],
    "margin_level": [
        (20, "높은 마진"), (10, "양호한 마진"), (0, "낮은 마진"), (None, "영업적자"),
    ],
    "debt_ratio": [
        (None, "과도한 레버리지"), (300, "다소 높은 레버리지"),
        (200, "보통 수준의 레버리지"), (100, "안정적인 자본 구조"),
        (50, "매우 안정적인 자본 구조"),
    ],
    "ocf_to_ni": [
        (150, "이익 대비 현금 회수가 매우 우수하다 (감가상각 등 비현금 항목이 크다)"),
        (100, "이익이 현금으로 잘 뒷받침된다"),
        (60, "현금 전환이 다소 부족하다"),
        (0, "이익의 현금 뒷받침이 크게 부족하다"),
        (None, "영업현금흐름이 적자다"),
    ],
    "hhi": [
        (5000, "매출이 단일 부문에 과도하게 집중되어 있다"),
        (2500, "상위 부문 의존도가 높다"),
        (1500, "적절히 다각화되어 있다"),
        (None, "매출이 고르게 분산되어 있다"),
    ],
}

_Z_SCORE_LABELS: dict[str, str] = {
    "안전": "단기 부실 위험은 낮다",
    "회색": "재무 악화 시 부실 전이 가능성이 있다",
    "위험": "부실 가능성에 주의가 필요하다",
}


def _classify(value: float, key: str) -> str:
    """값을 임계값 테이블에서 레이블로 변환."""
    thresholds = _THRESHOLDS.get(key, [])

    # debt_ratio는 lower_is_better (역순)
    if key == "debt_ratio":
        for cutoff, label in [
            (50, "매우 안정적인 자본 구조"),
            (100, "안정적인 자본 구조"),
            (200, "보통 수준의 레버리지"),
            (300, "다소 높은 레버리지"),
        ]:
            if value < cutoff:
                return label
        return "과도한 레버리지"

    # 기본: higher_is_better (내림차순)
    for cutoff, label in thresholds:
        if cutoff is None or value > cutoff:
            return label
    return thresholds[-1][1] if thresholds else ""


# ── 추세 감지 유틸 ──


def _detectTrend(values: list, min_count: int = 3) -> str | None:
    """숫자 리스트에서 추세 감지. 최신이 앞(index 0)."""
    valid = [v for v in values if v is not None]
    if len(valid) < min_count:
        return None
    improving = all(valid[i] >= valid[i + 1] for i in range(len(valid) - 1))
    declining = all(valid[i] <= valid[i + 1] for i in range(len(valid) - 1))
    if improving:
        return "improving"
    if declining:
        return "declining"
    return "mixed"


# ── Narrate 함수 ──


def narrateGrowth(yoy: float | None, cagr: float | None) -> str | None:
    """매출 성장률 해석."""
    if yoy is None and cagr is None:
        return None
    parts = []
    if yoy is not None:
        label = _classify(yoy, "growth_yoy")
        parts.append(f"매출이 전년 대비 {yoy:+.1f}% {label}했다" if label != "보합" else f"매출이 {yoy:+.1f}%로 보합 수준이다")
    if cagr is not None:
        label = _classify(cagr, "growth_cagr")
        parts.append(f"중기 CAGR {cagr:+.1f}%로 {label}" + ("하다" if label == "견조" else " 기조다" if "성장" in label else "다"))
    if yoy is not None and cagr is not None:
        if yoy > 10 and cagr < 0:
            parts.append("단기 반등이지만 중기 추세는 아직 하락이다")
        elif yoy < -10 and cagr > 5:
            parts.append("일시적 역성장이며 중기 성장 기조는 유효하다")
    return ". ".join(parts) + "." if parts else None


def narrateMargin(data: dict) -> str | None:
    """마진 추이 해석."""
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
    else:
        text += "이다"

    return text + "."


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
    """이익의 현금 전환 해석."""
    history = data.get("history", [])
    if not history:
        return None
    ratio = history[0].get("ocfToNi")
    if ratio is None:
        return None
    quality = _classify(ratio, "ocf_to_ni")
    return f"영업CF/순이익 {ratio:.0f}% — {quality}."


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
    text = f"부채비율 {dr:.0f}% — {level}"
    if ndr is not None and ndr < 0:
        text += f". 순부채비율 {ndr:.0f}%로 순현금 상태다"

    drs = [h.get("debtRatio") for h in history[:4] if h.get("debtRatio") is not None]
    trend = _detectTrend(drs)
    if trend == "improving":
        text += ". 부채가 지속적으로 증가하는 추세다"
    elif trend == "declining":
        text += ". 부채를 꾸준히 줄이고 있다"

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
    """ROIC vs WACC 해석."""
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
    return text + "."


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


# ── 막 결론 ──


_USED_THREAD_IDS: set[str] = set()


def resetActSummaryState() -> None:
    """막 결론 중복 방지 상태 초기화. 새 보고서 시작 시 호출."""
    _USED_THREAD_IDS.clear()


def buildActSummary(actNum: str, sections: list, threads: list) -> str | None:
    """막 결론 문장 자동 생성. 이미 사용한 thread는 재사용하지 않는다."""
    actSectionKeys = {s.key for s in sections}

    # 이 막에 관련된 thread 중 아직 안 쓴 것만
    actThreads = [
        t for t in threads
        if actSectionKeys & set(t.involvedSections) and t.threadId not in _USED_THREAD_IDS
    ]

    if actThreads:
        priority = {"critical": 0, "warning": 1, "positive": 2, "neutral": 3}
        actThreads.sort(key=lambda t: priority.get(t.severity, 9))
        main = actThreads[0]
        _USED_THREAD_IDS.add(main.threadId)
        return f"**{actNum}막 결론**: {main.story}"

    # thread 없으면 섹션 요약 조합
    summaries = [s.summary for s in sections if getattr(s, "summary", None)]
    if summaries:
        return f"**{actNum}막 결론**: {' / '.join(summaries[:2])}"
    return None
