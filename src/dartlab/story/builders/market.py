"""story 블록 빌더 — market 도메인 (debt-honesty P3-3 god-split). 공유 imports·상수·헬퍼는 _shared."""

from __future__ import annotations

from dartlab.story.builders._shared import (
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
    _flagsBlock,
    _hasMeta,
    _meta,
    narrateStrategy,
    narrateTechnicalVerdict,
    pl,
)

# ── 시장분석 (technicalAnalysis) 빌더 ──


def technicalVerdictBlock(data: dict) -> list:
    """calcTechnicalVerdict 결과 → 기술적 종합 판단."""
    if not data:
        return []

    verdict = data.get("verdict", "")
    score = data.get("score", 0)
    rsi = data.get("rsi")
    adx = data.get("adx")
    above20 = data.get("aboveSma20")
    above60 = data.get("aboveSma60")
    bbPos = data.get("bbPosition")

    metrics = [("종합 판단", f"{verdict} (score {score:+d})")]
    if rsi is not None:
        rsiLabel = "과매수" if rsi >= 70 else "과매도" if rsi <= 30 else "중립"
        metrics.append(("RSI (14)", f"{rsi:.1f} ({rsiLabel})"))
    if adx is not None:
        adxLabel = "강한 추세" if adx >= 25 else "추세 약함"
        metrics.append(("ADX (14)", f"{adx:.1f} ({adxLabel})"))
    if above20 is not None:
        metrics.append(("SMA 20일", "위" if above20 else "아래"))
    if above60 is not None:
        metrics.append(("SMA 60일", "위" if above60 else "아래"))
    if bbPos is not None:
        metrics.append(("BB 위치", f"{bbPos:.0f}%"))

    blocks: list = [
        HeadingBlock(
            _meta("technicalVerdict").label,
            level=2,
            helper="카테고리 간 우선순위 없음 — audit 통과한 독립 분해. 미래 예측 아님.",
        ),
        MetricBlock(metrics),
    ]

    # ── 카테고리 서브섹션 (Phase 5 verdict 강화, audit 통과 라벨만) ──
    categories = data.get("categories") or {}
    # 12년 audit 통과: trend 만 (momentum/volatility 12년 전라벨 fail → drop)
    cat_ko = {"trend": "추세"}
    for key, ko in cat_ko.items():
        cat = categories.get(key)
        if not cat:
            continue
        cat_metrics = [
            ("점수", f"{cat['score']:.0f}/100"),
            ("라벨", cat["label"]),
        ]
        inds = cat.get("indicators", {})
        for ik, iv in inds.items():
            if isinstance(iv, bool):
                cat_metrics.append((ik, "예" if iv else "아니오"))
            elif isinstance(iv, float):
                cat_metrics.append((ik, f"{iv:.1f}"))
            elif isinstance(iv, (list, dict)):
                continue  # 중첩 구조 skip
            else:
                cat_metrics.append((ik, str(iv)))
        blocks.append(HeadingBlock(f"{ko} ({key})", level=3))
        blocks.append(MetricBlock(cat_metrics))

    # narrate (Phase 5 E)
    narrative = narrateTechnicalVerdict(data)
    if narrative:
        blocks.append(TextBlock(narrative))

    return blocks


def technicalSignalsBlock(data: dict) -> list:
    """calcTechnicalSignals 결과 → 최근 매매 신호."""
    if not data:
        return []

    summary = data.get("signalSummary", {})
    bullish = summary.get("bullish", 0)
    bearish = summary.get("bearish", 0)

    blocks: list = [
        HeadingBlock(
            _meta("technicalSignals").label,
            level=2,
            helper="최근 20거래일 기준 매매 신호 집계",
        ),
        MetricBlock(
            [
                ("매수 신호", f"{bullish}건"),
                ("매도 신호", f"{bearish}건"),
            ]
        ),
    ]

    # 신호별 상세
    signals = data.get("signals", {})
    signalNames = {
        "goldenCross": "골든/데드크로스",
        "rsiSignal": "RSI 신호",
        "macdSignal": "MACD 신호",
        "bollingerSignal": "볼린저 신호",
    }
    sigMetrics = []
    for key, label in signalNames.items():
        val = signals.get(key, 0)
        if val > 0:
            sigMetrics.append((label, f"매수 {val}건"))
        elif val < 0:
            sigMetrics.append((label, f"매도 {abs(val)}건"))
    if sigMetrics:
        blocks.append(MetricBlock(sigMetrics))

    # 최근 이벤트 테이블
    events = data.get("recentEvents", [])
    if events:
        eventNames = {
            "goldenCross": "골든/데드크로스",
            "rsiSignal": "RSI",
            "macdSignal": "MACD",
            "bollingerSignal": "볼린저",
        }
        rows = {
            "날짜": [e.get("date", "") for e in events],
            "신호": [eventNames.get(e.get("type", ""), e.get("type", "")) for e in events],
            "방향": [e.get("direction", "") for e in events],
        }
        blocks.append(TableBlock("최근 신호 이벤트", pl.DataFrame(rows)))

    return blocks


def quantModuleBlock(key: str, data: dict | None) -> list:
    """quant 서사 모듈 1개 → Block (analysis calc 패턴).

    각 calc*Narrative 함수가 독립으로 반환한 dict 를 story 블록으로 변환.
    analysis 의 개별 calc → builder 패턴과 동일.
    """
    if not data:
        return []
    narrative = data.get("narrative", "")
    if not narrative or narrative.endswith("데이터 없음.") or narrative.endswith("데이터 부족."):
        return []
    label = _meta(key).label if _hasMeta(key) else key
    return [
        HeadingBlock(label, level=3),
        TextBlock(narrative),
    ]


def strategySnapshotBlock(data: dict) -> list:
    """calcStrategySnapshot 결과 → 8 검증 스타일 진입 진단 카드.

    Strategy DSL 의 story 6막 (전망) 진입점. 시총 의존 0.
    """
    if not data:
        return []

    style_labels = {
        "trendFollow": "추세추종",
        "meanReversion": "평균회귀",
        "breakout": "돌파",
        "dipBuy": "눌림목매수",
        "eventDriven": "이벤트드리븐",
        "flowFollow": "수급추종(KR)",
        "lowVolDefensive": "저변동방어",
        "seasonalKR": "한국캘린더(KR)",
    }

    rows_label = []
    rows_sharpe = []
    rows_mdd = []
    rows_dsr = []
    rows_entry = []
    rows_exit = []
    rows_trades = []
    rows_verdict = []
    for key, label in style_labels.items():
        snap = data.get(key)
        if snap is None or snap.get("status") != "ok":
            continue
        sharpe = snap.get("sharpe", 0.0)
        rows_label.append(label)
        rows_sharpe.append(f"{sharpe:+.2f}")
        rows_mdd.append(f"{snap.get('mdd', 0.0) * 100:+.1f}%")
        rows_dsr.append(f"{snap.get('dsr', 0.0):.2f}")
        rows_entry.append("●" if snap.get("entry_today") else "—")
        rows_exit.append("●" if snap.get("exit_today") else "—")
        rows_trades.append(str(snap.get("trades", 0)))
        # 판정
        if sharpe >= 1.2:
            rows_verdict.append("강함")
        elif sharpe >= 0.6:
            rows_verdict.append("양호")
        elif sharpe >= 0.2:
            rows_verdict.append("보통")
        elif sharpe > -1e-6:
            rows_verdict.append("약함")
        else:
            rows_verdict.append("부정")

    if not rows_label:
        return []

    table = pl.DataFrame(
        {
            "스타일": rows_label,
            "Sharpe": rows_sharpe,
            "MDD": rows_mdd,
            "DSR": rows_dsr,
            "오늘진입": rows_entry,
            "오늘청산": rows_exit,
            "Trades": rows_trades,
            "판정": rows_verdict,
        }
    )

    # 활성 진입 신호 narrate (1줄)
    activeStyles = [style_labels[k] for k, v in data.items() if v.get("entry_today") and v.get("status") == "ok"]
    helper = (
        "8 검증 스타일 백테스트 결과 + 오늘 시점 진입/청산 진단. "
        "Sharpe ≥ 1.2 강함, ≥ 0.6 양호, < 0.2 약함. DSR (Bailey-Lopez) 가 우연성 검증."
    )
    if activeStyles:
        helper += f"\n오늘 진입 신호 활성 스타일: {', '.join(activeStyles)}"

    blocks: list = [
        HeadingBlock(
            "전략별 진입 진단",
            level=2,
            helper=helper,
        ),
        TableBlock("스타일 백테스트 매트릭스", table),
    ]

    # 학술 출처 + 5년 결과 + 오늘 신호 narrate (Phase 4 R5)
    narrative = narrateStrategy(data)
    if narrative:
        blocks.append(TextBlock(narrative))

    return blocks


def marketBetaBlock(data: dict) -> list:
    """calcMarketBeta 결과 → 시장 베타 + CAPM."""
    if not data:
        return []

    metrics = []
    beta = data.get("value")
    if beta is not None:
        metrics.append(("베타 (β)", f"{beta:.3f}"))
    alpha = data.get("alpha")
    if alpha is not None:
        metrics.append(("연간 알파", f"{alpha:+.2f}%"))
    r2 = data.get("rSquared")
    if r2 is not None:
        metrics.append(("R²", f"{r2:.4f}"))
    capm = data.get("capm")
    if capm is not None:
        metrics.append(("CAPM 기대수익률", f"{capm:.1f}%"))
    rs = data.get("relativeStrength")
    if rs is not None:
        rsLabel = "상대 강세" if rs > 0 else "상대 약세"
        metrics.append(("상대강도 (RSI 차이)", f"{rs:+.1f} ({rsLabel})"))

    if not metrics:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("marketBeta").label,
            level=2,
            helper="β < 1 시장보다 안정, β > 1 시장보다 변동 큼. α > 0이면 시장 초과 수익",
        ),
        MetricBlock(metrics),
    ]

    interp = data.get("interpretation")
    if interp:
        blocks.append(TextBlock(interp, style="dim", indent="h2"))

    return blocks


def fundamentalDivergenceBlock(data: dict) -> list:
    """calcFundamentalDivergence 결과 → 재무-시장 괴리 진단."""
    if not data:
        return []

    metrics = []
    fg = data.get("financialGrade")
    tv = data.get("technicalVerdict")
    div = data.get("divergence")

    if fg:
        metrics.append(("재무 등급", fg))
    if tv:
        ts = data.get("technicalScore", 0)
        metrics.append(("기술적 판단", f"{tv} (score {ts:+d})"))
    if div:
        metrics.append(("교차검증", div))

    if not metrics:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("fundamentalDivergence").label,
            level=2,
            helper="재무 분석과 시장 반응이 일치하면 신뢰도 ↑, 괴리하면 원인 분석 필요",
        ),
        MetricBlock(metrics),
    ]

    diagnosis = data.get("diagnosis")
    if diagnosis:
        blocks.append(TextBlock(diagnosis, indent="h2"))

    return blocks


def marketRiskBlock(data: dict) -> list:
    """calcMarketRisk 결과 → 안정성 섹션에 배치되는 시장 리스크."""
    if not data:
        return []

    metrics = []
    beta = data.get("beta")
    if beta is not None:
        metrics.append(("시장 베타", f"{beta:.3f}"))
    atrPct = data.get("atrPercent")
    volGrade = data.get("volatilityGrade")
    if atrPct is not None:
        metrics.append(("일일 변동성 (ATR%)", f"{atrPct:.1f}%"))
    if volGrade:
        metrics.append(("변동성 등급", volGrade))
    rs = data.get("relativeStrength")
    if rs is not None:
        metrics.append(("시장 대비 상대강도", f"{rs:+.1f}"))

    if not metrics:
        return []

    return [
        HeadingBlock(
            _meta("marketRisk").label,
            level=2,
            helper="β > 1.5 고위험, ATR% > 5% 고변동. 상대강도 양수면 시장보다 강함",
        ),
        MetricBlock(metrics),
    ]


def marketAnalysisFlagsBlock(data) -> list:
    """calcMarketAnalysisFlags 결과 → FlagBlock."""
    flags = data if isinstance(data, list) else []
    return _flagsBlock(flags)


def riskDecompositionBlock(data) -> list:
    """calcMultiFactorRisk 결과 → systematic/idiosyncratic + 팩터별 기여 (Barra-style)."""
    if not data or data.get("error"):
        return []
    sysR = data.get("systematicRisk")
    resR = data.get("residualRisk")
    totR = data.get("totalRisk")
    sysShare = data.get("systematicShare")
    if sysR is None or resR is None:
        return []

    metrics = [
        ("총 리스크 (annualized)", f"{totR:.1f}%"),
        ("Systematic (팩터)", f"{sysR:.1f}% ({sysShare:.0f}%)"),
        ("Idiosyncratic (고유)", f"{resR:.1f}% ({100 - sysShare:.0f}%)"),
    ]
    contribs = data.get("factorContributions") or {}
    for name, pct in contribs.items():
        metrics.append((f"  {name} 기여 (% of sys)", f"{pct:+.1f}%"))

    interp = data.get("interpretation", "")
    helper = (
        f"{data.get('model', 'Multi-Factor')}: 종목 총 리스크를 systematic (FF 팩터) + idiosyncratic (고유) 로 분해. "
        f"{interp}"
    )

    return [
        HeadingBlock(
            _meta("riskDecomposition").label,
            level=2,
            helper=helper,
        ),
        MetricBlock(metrics),
    ]


def factorTearSheetBlock(data) -> list:
    """calcFactorTearSheetAll 결과 → 4 팩터 long-short Sharpe + alpha 원천 (Alphalens 표준)."""
    if not data:
        return []
    factors = data.get("factors") or []
    if not factors:
        return []

    # 팩터별 한 줄: "SMB Sharpe = +0.85 (강한 alpha — 소형주 프리미엄)"
    metrics: list[tuple[str, str]] = []
    for f in factors:
        name = f.get("factorName", "")
        sharpe = f.get("longShortSharpe")
        interp = f.get("interpretation", "")
        annR = f.get("longShortAnnualReturn")
        annV = f.get("longShortAnnualVol")
        winR = f.get("longShortWinRate")
        if sharpe is None:
            continue
        metrics.append(
            (
                f"{name}",
                f"Sharpe {sharpe:+.2f} · 연수익 {annR:+.1f}% · 변동성 {annV:.1f}% · WinRate {winR:.0f}% — {interp}",
            )
        )
    if not metrics:
        return []

    strongest = data.get("strongest", "?")
    universe = data.get("universe", "?")
    year = data.get("year", "?")
    isReal = data.get("isRealFamaFrench", False)

    helper = (
        f"Long-short 일별 시계열 Sharpe ({year}년 fundamental, universe {universe}종목, "
        f"{'진짜 KRX 시총 기반' if isReal else 'book equity proxy fallback'}). "
        "Sharpe > 1.0 = 강한 alpha, 0.5~1.0 = 약함, < 0 = 역방향. "
        f"가장 강한 팩터: {strongest}"
    )

    return [
        HeadingBlock(
            _meta("factorTearSheet").label,
            level=2,
            helper=helper,
        ),
        MetricBlock(metrics),
    ]


def factorICBlock(data) -> list:
    """calcFactorICAll 결과 → 4 팩터 Cross-Sectional IC / ICIR (Grinold & Kahn Ch.5)."""
    if not data:
        return []
    factors = data.get("factors") or []
    if not factors:
        return []

    metrics: list[tuple[str, str]] = []
    for f in factors:
        name = f.get("factorName", "")
        icMean = f.get("icMean")
        icStd = f.get("icStd")
        icir = f.get("icir")
        hit = f.get("hitRate")
        t = f.get("tStat")
        interp = f.get("interpretation", "")
        if icir is None:
            continue
        metrics.append(
            (
                f"{name}",
                f"ICIR {icir:+.2f} · IC {icMean:+.4f}±{icStd:.4f} · Hit {hit:.0f}% · t={t:+.2f} — {interp}",
            )
        )
    if not metrics:
        return []

    strongest = data.get("strongest", "?")
    horizon = data.get("horizon", "?")
    fundYear = data.get("fundYear", "?")
    retYear = data.get("retYear", "?")

    helper = (
        f"일별 횡단면 Spearman IC (전년 {fundYear} 펀더멘털 → {retYear} Q2~Q4 {horizon}일 forward return). "
        "ICIR > 0.5 = 강한 예측력, 0.3~0.5 = 중간, < 0.1 = 노이즈. "
        f"가장 강한 팩터: {strongest}. look-ahead bias 방지."
    )

    return [
        HeadingBlock(
            _meta("factorIC").label,
            level=2,
            helper=helper,
        ),
        MetricBlock(metrics),
    ]


# ── Sprint 2 재무 알파 9축 블록 ──


def altmanFactorBlock(data) -> list:
    """calcAltmanFactor → safe/grey/distress 3 zone + top 10."""
    if not data or data.get("status") != "ok":
        return []
    zones = data.get("zones", {})
    methodology = data.get("methodology") or {}
    thresholds = methodology.get("thresholds") or {}
    modelName = methodology.get("modelName") or f"Altman {data.get('variant', '').upper()}"
    distress_below = thresholds.get("distressBelow")
    safe_above = thresholds.get("safeAbove")
    metrics = [
        (
            f"safe zone (score > {safe_above})",
            f"{zones.get('safe', {}).get('count', 0)}사 ({zones.get('safe', {}).get('pct', 0)}%)",
        ),
        ("grey zone", f"{zones.get('grey', {}).get('count', 0)}사 ({zones.get('grey', {}).get('pct', 0)}%)"),
        (
            f"distress zone (score < {distress_below})",
            f"{zones.get('distress', {}).get('count', 0)}사 ({zones.get('distress', {}).get('pct', 0)}%)",
        ),
    ]
    return [
        HeadingBlock(
            _meta("altmanFactor").label,
            level=2,
            helper=f"{modelName} ({data.get('year')}, {data.get('universe')}종목, variant={data.get('variant')}). {data.get('interpretation', '')}",
        ),
        MetricBlock(metrics),
    ]


def qFactorBlock(data) -> list:
    """calcQFactor → top Q / bottom Q."""
    if not data:
        return []
    topQ = data.get("topQ") or []
    bottomQ = data.get("bottomQ") or []
    metrics = []
    if topQ:
        metrics.append(("top Q-factor 상위 5", ", ".join(f"{c}({s})" for c, s in topQ[:5])))
    if bottomQ:
        metrics.append(("bottom 하위 5", ", ".join(f"{c}({s})" for c, s in bottomQ[:5])))
    return [
        HeadingBlock(
            _meta("qFactor").label,
            level=2,
            helper=f"Hou-Xue-Zhang q-factor ({data.get('year')}, {data.get('universe')}종목). {data.get('interpretation', '')}",
        ),
        MetricBlock(metrics),
    ]


def qmjBlock(data) -> list:
    """calcQMJ → top Quality / top Junk."""
    if not data:
        return []
    topQ = data.get("topQuality") or []
    topJ = data.get("topJunk") or []
    metrics = []
    if topQ:
        metrics.append(("top Quality 5", ", ".join(f"{c}({s})" for c, s in topQ[:5])))
    if topJ:
        metrics.append(("top Junk 5", ", ".join(f"{c}({s})" for c, s in topJ[:5])))
    return [
        HeadingBlock(
            _meta("qmj").label,
            level=2,
            helper=f"QMJ composite ({data.get('year')}, {data.get('universe')}종목). {data.get('interpretation', '')}",
        ),
        MetricBlock(metrics),
    ]


def babBlock(data) -> list:
    """calcBAB → top Low-Beta / top High-Beta + low-vol 보조."""
    if not data:
        return []
    topLow = data.get("topLow") or []
    topHigh = data.get("topHigh") or []
    metrics = []
    if topLow:
        metrics.append(("top Low-Beta 5", ", ".join(f"{c}(β={v})" for c, v in topLow[:5])))
    if topHigh:
        metrics.append(("top High-Beta 5", ", ".join(f"{c}(β={v})" for c, v in topHigh[:5])))
    topLowVol = data.get("topLowVol") or []
    if topLowVol:
        metrics.append(("top Low-Vol 5", ", ".join(f"{c}({v}%)" for c, v in topLowVol[:5])))
    return [
        HeadingBlock(
            _meta("bab").label,
            level=2,
            helper=(
                f"BAB beta ({data.get('betaWindow', 252)}일, {data.get('universe')}종목). "
                f"{data.get('interpretation', '')}"
            ),
        ),
        MetricBlock(metrics),
    ]


def fundMomentumBlock(data) -> list:
    """calcFundamentalMomentum → top double-momentum."""
    if not data:
        return []
    topD = data.get("topDouble") or []
    botD = data.get("bottomDouble") or []
    metrics = []
    if topD:
        metrics.append(("top double-momentum 5", ", ".join(f"{c}({s})" for c, s in topD[:5])))
    if botD:
        metrics.append(("bottom 5", ", ".join(f"{c}({s})" for c, s in botD[:5])))
    return [
        HeadingBlock(
            _meta("fundMomentum").label,
            level=2,
            helper=f"Chordia-Shivakumar 펀더멘털×가격 ({data.get('year')}, {data.get('universe')}종목). {data.get('interpretation', '')}",
        ),
        MetricBlock(metrics),
    ]


def technicalActionTargetsBlock(data: dict | None) -> list:
    """calcActionableTargets 결과 → 기술적 행동 목표."""
    if not data:
        return []

    from dartlab.story.narrate import narrateTechnicalAction

    blocks: list = [
        HeadingBlock(_meta("technicalActionTargets").label, level=2, helper="기술적 관점의 진입/청산 가격 목표")
    ]

    narration = narrateTechnicalAction(data)
    if narration:
        blocks.append(TextBlock(narration))

    metrics = [("현재가", f"{data['currentPrice']:,}"), ("기술적 판정", data.get("technicalVerdict", ""))]
    if data.get("support"):
        metrics.append(("지지선", f"{data['support']:,}"))
    if data.get("resistance"):
        metrics.append(("저항선", f"{data['resistance']:,}"))
    blocks.append(MetricBlock(metrics))

    targets = data.get("targets", [])
    if targets:
        rows = [
            {
                "신호": t["signal"],
                "트리거 가격": f"{t['triggerPrice']:,}",
                "행동": t["action"],
                "신뢰도": t["confidence"],
            }
            for t in targets
        ]
        blocks.append(TableBlock("행동 목표", pl.DataFrame(rows)))
    return blocks
