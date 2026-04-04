"""macro 보고서 빌더 — 11축 전부를 review Block으로 변환.

3막 서사 구조. 상황별 템플릿에 따라 강조축이 달라지지만 데이터는 전부 포함.
"""

from __future__ import annotations

import polars as pl

from dartlab.review.blocks import (
    ChartBlock,
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
)

from .charts import (
    spec_corporate_table,
    spec_cycle_indicators,
    spec_earnings_cycle,
    spec_fear_greed_components,
    spec_fci_timeline,
    spec_ponzi_ratio,
    spec_recession_prob,
    spec_trade_tot,
)


# ══════════════════════════════════════
# 신호등 대시보드 (0막)
# ══════════════════════════════════════


def build_dashboard_blocks(summary: dict) -> list:
    """신호등 대시보드 — 전 축 상태를 한눈에."""
    blocks: list = []
    score = summary.get("score", 0)

    # 종합 판정
    blocks.append(MetricBlock([("종합 판정", f"{summary.get('overallLabel', '중립')} ({score:+.1f})")]))

    # 전 축 상태 한 줄
    cycle = summary.get("cycle") or {}
    rates = summary.get("rates") or {}
    fg = (summary.get("sentiment") or {}).get("fearGreed") or {}
    liq = summary.get("liquidity") or {}
    forecast = summary.get("forecast") or {}
    crisis = summary.get("crisis") or {}
    inventory = summary.get("inventory") or {}
    trade = summary.get("trade") or {}
    corporate = summary.get("corporate") or {}

    signals = [
        ("사이클", cycle.get("phaseLabel", "—")),
        ("금리", (rates.get("outlook") or {}).get("direction", "—")),
        ("심리", f"F&G {fg.get('score', '—')}"),
        ("유동성", liq.get("regimeLabel", "—")),
        ("침체확률", f"{(forecast.get('recessionProb') or {}).get('probability', 0) * 100:.0f}%"),
        ("위기", (crisis.get("ghsScore") or {}).get("zoneLabel", "—")),
    ]

    # 재고 (있으면)
    ip = inventory.get("inventoryPhase") or {}
    if ip.get("phaseLabel"):
        signals.append(("재고", ip["phaseLabel"]))

    # 교역 (KR)
    tot = trade.get("termsOfTrade") or {}
    if tot.get("directionLabel"):
        signals.append(("교역", tot["directionLabel"]))

    # Nowcast (있으면)
    nc = forecast.get("nowcast") or {}
    if nc.get("gdpEstimate") is not None:
        signals.append(("GDP추정", f"{nc['gdpEstimate']:.1f}%"))

    blocks.append(MetricBlock(signals))

    # 기여도
    contributions = summary.get("contributions") or {}
    if contributions:
        parts = sorted(contributions.items(), key=lambda x: -abs(x[1]))
        blocks.append(TextBlock("기여도: " + ", ".join(f"{k} {v:+.1f}" for k, v in parts)))

    # FCI 차트
    fci_chart = spec_fci_timeline(liq)
    if fci_chart:
        blocks.append(ChartBlock(fci_chart, caption="FCI 시계열"))

    return blocks


# ══════════════════════════════════════
# 제1막: 국면 진단
# ══════════════════════════════════════


def build_phase_blocks(summary: dict) -> list:
    """제1막 — 사이클 + 금리 + 자산 + 심리 + 재고. 지금 어디인가."""
    blocks: list = []
    cycle = summary.get("cycle") or {}
    rates = summary.get("rates") or {}
    assets = summary.get("assets") or {}
    sentiment = summary.get("sentiment") or {}
    inventory = summary.get("inventory") or {}

    # ── 사이클 ──
    blocks.append(HeadingBlock("경제 사이클", level=2))
    blocks.append(MetricBlock([
        ("국면", cycle.get("phaseLabel", "—")),
        ("신뢰도", str(cycle.get("confidence", "—"))),
    ]))
    signals = cycle.get("signals") or []
    if signals:
        blocks.append(TextBlock("근거: " + " / ".join(signals[:4])))

    sector = cycle.get("sectorStrategy")
    if sector:
        blocks.append(TextBlock("섹터: " + ", ".join(f"{k}={v}" for k, v in sector.items())))

    transition = cycle.get("transition")
    if transition:
        blocks.append(TextBlock(f"전환 감지: {transition.get('from', '?')} → {transition.get('to', '?')} (진행 {transition.get('progress', '?')})"))

    # 사이클 지표 차트
    cycle_chart = spec_cycle_indicators(cycle.get("timeseries") or {})
    if cycle_chart:
        blocks.append(ChartBlock(cycle_chart))

    # ── 금리 ──
    blocks.append(HeadingBlock("금리 환경", level=2))
    outlook = rates.get("outlook") or {}
    expect = rates.get("expectation") or {}
    rate_m = [("방향", outlook.get("direction", "—"))]
    if expect.get("spread2yFf") is not None:
        rate_m.append(("2Y-FF", f"{expect['spread2yFf']:+.2f}%p"))
        rate_m.append(("강도", expect.get("strength", "—")))
    blocks.append(MetricBlock(rate_m))

    # DKW 분해
    decomp = rates.get("decomposition")
    if decomp:
        blocks.append(MetricBlock([
            ("명목", f"{decomp.get('nominal', 0):.2f}%"),
            ("실질", f"{decomp.get('realRate', 0):.2f}%"),
            ("BEI", f"{decomp.get('expectedInflation', 0):.2f}%"),
            ("기간프리미엄", f"{decomp.get('termPremium', 0):.2f}%"),
        ]))

    # Nelson-Siegel
    yc = rates.get("yieldCurve")
    if yc:
        blocks.append(MetricBlock([
            ("β0(Level)", f"{yc.get('beta0', 0):.2f}"),
            ("β1(Slope)", f"{yc.get('beta1', 0):.2f}"),
            ("β2(Curv)", f"{yc.get('beta2', 0):.2f}"),
            ("RMSE", f"{yc.get('rmse', 0):.4f}"),
        ]))
        blocks.append(TextBlock(yc.get("description", "")))

    # BEI/실질금리 4분면
    rr = rates.get("realRateRegime")
    if rr:
        blocks.append(MetricBlock([
            ("실질금리", f"{rr.get('realRate', 0):.2f}%"),
            ("BEI", f"{rr.get('bei', 0):.2f}%"),
            ("regime", rr.get("regimeLabel", "—")),
        ]))

    # 고용
    emp = rates.get("employment") or {}
    if emp.get("stateLabel"):
        blocks.append(MetricBlock([("고용", emp["stateLabel"])]))
        reasoning = emp.get("reasoning") or []
        if reasoning:
            blocks.append(TextBlock(" / ".join(reasoning[:3])))

    # 물가
    inf = rates.get("inflation") or {}
    if inf.get("stateLabel"):
        blocks.append(MetricBlock([("물가", inf["stateLabel"])]))
        reasoning = inf.get("reasoning") or []
        if reasoning:
            blocks.append(TextBlock(" / ".join(reasoning[:3])))

    # ── 자산 ──
    blocks.append(HeadingBlock("자산 신호", level=2))

    # 5대 자산 테이블
    asset_list = assets.get("assets") or []
    if asset_list:
        rows = []
        for a in asset_list:
            rows.append({
                "자산": a.get("label", ""),
                "수준": f"{a.get('level', 0):.2f}" if a.get("level") is not None else "—",
                "변화": f"{a.get('change', 0):+.2f}" if a.get("change") is not None else "—",
                "해석": a.get("interpretation", ""),
            })
        if rows:
            blocks.append(TableBlock("5대 자산", pl.DataFrame(rows)))

    # 금 3요인
    gd = assets.get("goldDrivers")
    if gd:
        blocks.append(MetricBlock([
            ("실질금리 효과", f"{gd.get('realRateEffect', 0):+.2f}"),
            ("달러 효과", f"{gd.get('dollarEffect', 0):+.2f}"),
            ("안전자산 효과", f"{gd.get('safeHavenEffect', 0):+.2f}"),
            ("지배 요인", gd.get("dominant", "—")),
        ]))

    # VIX 구간
    vr = assets.get("vixRegime")
    if vr:
        buy_sig = vr.get("buySignal", 0)
        blocks.append(MetricBlock([
            ("VIX", f"{vr.get('level', 0):.1f}"),
            ("구간", vr.get("zoneLabel", "—")),
            ("분할매수", f"{buy_sig}차" if buy_sig else "없음"),
        ]))

    # Cu/Au
    cu = assets.get("copperGold")
    if cu:
        blocks.append(MetricBlock([("Cu/Au", f"{cu.get('directionLabel', '—')} ({cu.get('implication', '')})")]))

    # ── 심리 ──
    blocks.append(HeadingBlock("시장 심리", level=2))
    fg = sentiment.get("fearGreed")
    if fg:
        blocks.append(MetricBlock([
            ("공포탐욕", f"{fg.get('score', 0):.0f} ({fg.get('zoneLabel', '—')})"),
        ]))
        # 구성요소 분해
        comps = fg.get("components") or {}
        if comps:
            comp_items = [(k, f"{v:.1f}") for k, v in comps.items()]
            blocks.append(MetricBlock(comp_items))

        fg_chart = spec_fear_greed_components(fg)
        if fg_chart:
            blocks.append(ChartBlock(fg_chart, caption="공포탐욕 구성요소"))

    # ── 재고순환 ──
    ip = inventory.get("inventoryPhase") or {}
    ism_bar = inventory.get("ismBarometer") or {}
    ism_alloc = inventory.get("ismAllocation") or {}

    if ip.get("phase") or ism_bar.get("level"):
        blocks.append(HeadingBlock("재고순환", level=2))

    if ip.get("phase"):
        blocks.append(MetricBlock([
            ("국면", ip.get("phaseLabel", "—")),
            ("비율", f"{ip.get('ratio', 0):.3f}"),
            ("주식", ip.get("equityLabel", "—")),
        ]))
        blocks.append(TextBlock(ip.get("description", "")))

    if ism_bar.get("level"):
        blocks.append(MetricBlock([
            ("ISM", f"{ism_bar['level']:.1f} ({ism_bar.get('zoneLabel', '—')})"),
            ("주식", ism_bar.get("equityLabel", "—")),
            ("금리", ism_bar.get("rateLabel", "—") or "—"),
        ]))

    if ism_alloc.get("stance"):
        blocks.append(MetricBlock([("ISM 배분", f"{ism_alloc.get('stanceLabel', '—')}")]))

    return blocks


# ══════════════════════════════════════
# 제2막: 인과 역추적
# ══════════════════════════════════════


def build_causation_blocks(summary: dict) -> list:
    """제2막 — 위기 + 유동성 + 기업집계. 왜 이 국면인가."""
    blocks: list = []
    crisis = summary.get("crisis") or {}
    liquidity = summary.get("liquidity") or {}
    corporate = summary.get("corporate") or {}

    # ── 신용 환경 ──
    blocks.append(HeadingBlock("신용 환경", level=2))

    cg = crisis.get("creditGap")
    if cg:
        blocks.append(MetricBlock([
            ("Credit-to-GDP gap", f"{cg.get('gap', 0):+.1f}%p"),
            ("구간", cg.get("zoneLabel", "—")),
            ("CCyB", f"{cg.get('ccybBuffer', 0):.1f}%"),
        ]))

    ghs = crisis.get("ghsScore")
    if ghs:
        blocks.append(MetricBlock([
            ("GHS 위기점수", f"{ghs.get('score', 0):.0f}/100"),
            ("3년 내 위기확률", f"{ghs.get('crisisProb', 0) * 100:.0f}%"),
            ("구간", ghs.get("zoneLabel", "—")),
        ]))

    # 설비투자 압력
    capex = crisis.get("capexPressure")
    if capex:
        blocks.append(MetricBlock([
            ("설비투자 압력", capex.get("pressureLabel", "—")),
            ("HY 스프레드", f"{capex.get('spreadLevel', 0):.0f}bp ({capex.get('spreadChange', 0):+.0f})"),
        ]))

    # ── 위기 프레임워크 ──
    blocks.append(HeadingBlock("위기 프레임워크", level=2))

    minsky = crisis.get("minskyPhase")
    if minsky:
        blocks.append(MetricBlock([("Minsky", f"{minsky.get('phaseLabel', '—')} ({minsky.get('confidence', '')})")]))
        minsky_signals = minsky.get("signals") or []
        if minsky_signals:
            blocks.append(TextBlock(" / ".join(minsky_signals[:4])))

    koo = crisis.get("kooRecession")
    if koo:
        blocks.append(MetricBlock([
            ("Koo BSR", "활성" if koo.get("isBSR") else "비활성"),
            ("민간잉여", f"{koo.get('privateSurplus', 0):.1f}%"),
        ]))
        if koo.get("description"):
            blocks.append(TextBlock(koo["description"]))

    fisher = crisis.get("fisherDeflation")
    if fisher:
        blocks.append(MetricBlock([
            ("Fisher", fisher.get("riskLabel", "—")),
            ("DSR", f"{fisher.get('dsr', 0):.1f}%"),
            ("CPI", f"{fisher.get('cpiYoy', 0):+.1f}%"),
        ]))

    # 달러 안전자산
    dsh = crisis.get("dollarSafeHaven")
    if dsh:
        blocks.append(MetricBlock([
            ("달러 안전자산", dsh.get("statusLabel", "—")),
            ("VIX", f"{dsh.get('vix', 0):.1f}"),
            ("DXY 3M", f"{dsh.get('dxyChange3m', 0):+.1f}%"),
        ]))

    # KR 특화
    kr_housing = crisis.get("krHousingStress")
    if kr_housing:
        blocks.append(MetricBlock([
            ("부동산 스트레스", kr_housing.get("stressLabel", "—")),
            ("아파트 YoY", f"{kr_housing.get('housePriceYoy', 0):+.1f}%"),
        ]))

    kr_credit = crisis.get("krCreditRisk")
    if kr_credit:
        blocks.append(MetricBlock([("KR 신용위험", kr_credit.get("signal", "—"))]))

    # ── 유동성 상세 ──
    blocks.append(HeadingBlock("유동성 환경", level=2))
    blocks.append(MetricBlock([
        ("regime", liquidity.get("regimeLabel", "—")),
        ("score", f"{liquidity.get('score', 0):+.1f}"),
    ]))

    # NFCI
    nfci = liquidity.get("nfci")
    if nfci:
        blocks.append(MetricBlock([("NFCI", f"{nfci.get('value', 0):+.3f} ({nfci.get('regimeLabel', '')})")]))

    # FCI + 구성요소
    fci = liquidity.get("fci")
    if fci:
        blocks.append(MetricBlock([("FCI", f"{fci.get('value', 0):+.3f} ({fci.get('regimeLabel', '')})")]))
        comps = fci.get("components") or {}
        if comps:
            blocks.append(MetricBlock([(k, f"{v:+.3f}") for k, v in comps.items()]))

    # 유동성 개별 신호
    liq_signals = liquidity.get("signals") or []
    if liq_signals:
        blocks.append(TextBlock(" / ".join(liq_signals[:5])))

    # ── 기업 실태 ──
    ec = corporate.get("earningsCycle")
    pr = corporate.get("ponziRatio")
    lc = corporate.get("leverageCycle")

    if ec or pr or lc:
        blocks.append(HeadingBlock("기업 실태 (바텀업)", level=2))

        if ec:
            blocks.append(MetricBlock([
                ("이익사이클", ec.get("currentLabel", "—")),
                ("종목수", str(ec.get("companyCount", "—"))),
            ]))
        if pr:
            blocks.append(MetricBlock([
                ("Ponzi비율", f"{pr.get('currentRatio', 0):.1%}"),
                ("추세", pr.get("trendLabel", "—")),
            ]))
        if lc:
            blocks.append(MetricBlock([
                ("레버리지", f"{lc.get('currentLevel', 0):.1f}%"),
                ("추세", lc.get("trendLabel", "—")),
            ]))

        # 기업집계 시계열 테이블
        corp_table = spec_corporate_table(corporate)
        if corp_table:
            blocks.append(TableBlock("기업집계 시계열", pl.DataFrame(corp_table)))

        # 차트
        ec_chart = spec_earnings_cycle(corporate)
        if ec_chart:
            blocks.append(ChartBlock(ec_chart))
        ponzi_chart = spec_ponzi_ratio(corporate)
        if ponzi_chart:
            blocks.append(ChartBlock(ponzi_chart))

    return blocks


# ══════════════════════════════════════
# 제3막: 전망과 리스크
# ══════════════════════════════════════


def build_outlook_blocks(summary: dict) -> list:
    """제3막 — 예측 + 교역 + 리스크. 무엇이 올 것인가."""
    blocks: list = []
    forecast = summary.get("forecast") or {}
    crisis = summary.get("crisis") or {}
    trade = summary.get("trade") or {}

    # ── 침체 전망 ──
    blocks.append(HeadingBlock("침체 전망", level=2))
    rp = forecast.get("recessionProb")
    sahm = forecast.get("sahmRule")
    hamilton = forecast.get("hamiltonRegime")
    lei = forecast.get("lei")
    nc = forecast.get("nowcast")

    metrics = []
    if rp:
        metrics.append(("프로빗", f"{rp.get('probability', 0) * 100:.1f}% ({rp.get('zoneLabel', '')})"))
    if sahm:
        triggered = " ⚠ 트리거" if sahm.get("triggered") else ""
        metrics.append(("Sahm", f"{sahm.get('value', 0):.2f}%p{triggered}"))
    if hamilton:
        metrics.append(("Hamilton", f"{hamilton.get('currentRegime', '—')} ({hamilton.get('currentProb', 0):.0%})"))
    if lei and isinstance(lei, dict):
        metrics.append(("LEI", lei.get("signalLabel", lei.get("growthLabel", "—"))))
    if metrics:
        blocks.append(MetricBlock(metrics))

    # Hamilton 상세
    if hamilton:
        h_detail = [("수렴", "✅" if hamilton.get("converged") else "❌")]
        if hamilton.get("iterations"):
            h_detail.append(("반복", str(hamilton["iterations"])))
        if hamilton.get("contractionProb") is not None:
            h_detail.append(("침체확률", f"{hamilton['contractionProb'] * 100:.1f}%"))
        blocks.append(MetricBlock(h_detail))

    # LEI 상세
    if lei and isinstance(lei, dict) and lei.get("level") is not None:
        lei_m = [("LEI 수준", f"{lei.get('level', 0):.2f}")]
        if lei.get("mom") is not None:
            lei_m.append(("MoM", f"{lei['mom']:+.3f}"))
        if lei.get("mom6m") is not None:
            lei_m.append(("6M 연율", f"{lei['mom6m']:+.2f}%"))
        blocks.append(MetricBlock(lei_m))

    # Nowcast
    if nc:
        blocks.append(MetricBlock([
            ("GDP Nowcast", f"{nc.get('gdpEstimate', 0):.2f}%"),
            ("신뢰도", nc.get("confidence", "—")),
        ]))

    # 침체확률 차트
    rc_chart = spec_recession_prob(forecast)
    if rc_chart:
        blocks.append(ChartBlock(rc_chart))

    # 침체 대시보드 구성요소
    dashboard = crisis.get("recessionDashboard") or {}
    dash_comps = dashboard.get("components") or {}
    if dash_comps:
        blocks.append(MetricBlock([
            ("종합", f"{dashboard.get('composite', 0) * 100:.1f}% ({dashboard.get('zoneLabel', '')})"),
        ] + [(k, f"{v * 100:.1f}%") for k, v in dash_comps.items()]))

    # ── 교역 전망 (KR) ──
    tot = trade.get("termsOfTrade")
    if tot:
        blocks.append(HeadingBlock("교역 전망", level=2))
        blocks.append(MetricBlock([
            ("교역조건", f"{tot.get('level', 0):.1f} ({tot.get('directionLabel', '—')})"),
            ("모멘텀", f"{tot.get('momentum', 0):+.1f}"),
            ("수출이익", tot.get("earningsLabel", "—")),
        ]))

    tp = trade.get("totProxy")
    if tp:
        blocks.append(MetricBlock([
            ("ToT 대용치", f"{tp.get('value', 0):+.1f}%p ({tp.get('directionLabel', '—')})"),
        ]))

    ep = trade.get("exportProfit")
    if ep:
        blocks.append(MetricBlock([
            ("수출이익 선행", f"{ep.get('signalLabel', '—')} ({ep.get('confidence', '')})"),
        ]))

    lrs = trade.get("leadingRelativeStrength")
    if lrs:
        blocks.append(MetricBlock([("양국 선행지수", f"{lrs.get('fxLabel', '—')}")]))

    usc = trade.get("usConsumptionLink")
    if usc:
        blocks.append(MetricBlock([("미국소비→한국주가", usc.get("implication", "—"))]))

    # 교역 차트
    tot_chart = spec_trade_tot(trade)
    if tot_chart:
        blocks.append(ChartBlock(tot_chart))

    # ── 리스크 경고 ──
    flags = []
    if dashboard.get("composite", 0) > 0.3:
        flags.append(f"침체 종합확률 {dashboard.get('composite', 0) * 100:.0f}%")
    if dashboard.get("historicalMatch"):
        flags.append(f"역사 패턴: {dashboard['historicalMatch']}년과 유사")
    cg = crisis.get("creditGap") or {}
    if cg.get("zone") in ("warning", "danger"):
        flags.append(f"Credit-to-GDP gap {cg.get('zoneLabel', '')} ({cg.get('gap', 0):+.1f}%p)")
    ghs = crisis.get("ghsScore") or {}
    if ghs.get("crisisProb", 0) > 0.2:
        flags.append(f"GHS 위기확률 {ghs.get('crisisProb', 0) * 100:.0f}%")
    if flags:
        blocks.append(FlagBlock(flags, kind="warning"))

    return blocks


# ══════════════════════════════════════
# 자산배분 시사점 (4막)
# ══════════════════════════════════════


def build_allocation_blocks(summary: dict) -> list:
    """자산배분 — 포트폴리오 + 40전략 전체."""
    blocks: list = []
    allocation = summary.get("allocation")
    strategies = summary.get("strategies")

    if allocation:
        blocks.append(HeadingBlock("포트폴리오 매핑", level=2))
        blocks.append(MetricBlock([
            ("주식", f"{allocation.get('equity', 0)}%"),
            ("채권", f"{allocation.get('bond', 0)}%"),
            ("금", f"{allocation.get('gold', 0)}%"),
            ("현금", f"{allocation.get('cash', 0)}%"),
        ]))
        rationale = allocation.get("rationale") or []
        for r in rationale:
            blocks.append(TextBlock(r))

    if strategies:
        blocks.append(HeadingBlock("투자전략", level=2))
        blocks.append(MetricBlock([
            ("활성", f"{strategies.get('active', 0)}/{strategies.get('total', 40)}"),
            ("Bullish", str(strategies.get("bullish", 0))),
            ("Bearish", str(strategies.get("bearish", 0))),
        ]))

        # Bullish 전략 테이블
        sigs = strategies.get("signals") or []
        bullish = [s for s in sigs if s.get("active") and s.get("direction") == "bullish"]
        bearish = [s for s in sigs if s.get("active") and s.get("direction") == "bearish"]

        def _strat_table(items, label):
            if not items:
                return
            rows = [{"#": s.get("id", ""), "전략": s.get("name", ""), "강도": f"{s.get('strength', 0):.2f}", "설명": s.get("description", "")[:40]} for s in sorted(items, key=lambda x: -(x.get("strength") or 0))]
            blocks.append(TableBlock(label, pl.DataFrame(rows)))

        _strat_table(bullish, "Bullish 전략")
        _strat_table(bearish, "Bearish 전략")

    return blocks
