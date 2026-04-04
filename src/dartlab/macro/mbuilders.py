"""macro 보고서 빌더 — macro dict → review Block 변환.

review/builders.py 패턴. 각 막의 데이터를 Block 리스트로 변환.
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

from .charts import spec_earnings_cycle, spec_fci_timeline, spec_ponzi_ratio, spec_recession_prob


# ── 신호등 이모지 ──

def _signal(zone: str) -> str:
    """zone → 신호등 기호."""
    if zone in ("expansion", "favorable", "abundant", "loose", "low", "normal"):
        return "[+]"
    if zone in ("contraction", "unfavorable", "tight", "high", "danger"):
        return "[-]"
    return "[=]"


def build_dashboard_blocks(summary: dict) -> list:
    """신호등 대시보드 + 종합 판정."""
    blocks: list = []

    # 종합 판정
    overall = summary.get("overall", "neutral")
    score = summary.get("score", 0)
    blocks.append(MetricBlock([
        ("종합 판정", f"{summary.get('overallLabel', '중립')} ({score:+.1f})"),
    ]))

    # 축별 신호등
    signals = []
    cycle = summary.get("cycle") or {}
    signals.append(("사이클", cycle.get("phaseLabel", "—")))
    rates = summary.get("rates") or {}
    outlook = rates.get("outlook") or {}
    signals.append(("금리", outlook.get("direction", "—")))
    fg = (summary.get("sentiment") or {}).get("fearGreed") or {}
    signals.append(("심리", f"F&G {fg.get('score', '—')}"))
    liq = summary.get("liquidity") or {}
    signals.append(("유동성", liq.get("regimeLabel", "—")))
    forecast = summary.get("forecast") or {}
    rp = forecast.get("recessionProb") or {}
    signals.append(("침체확률", f"{rp.get('probability', 0) * 100:.0f}%"))
    blocks.append(MetricBlock([(k, v) for k, v in signals]))

    # 기여도
    contributions = summary.get("contributions") or {}
    if contributions:
        blocks.append(TextBlock(
            "기여도: " + ", ".join(f"{k} {v:+.1f}" for k, v in sorted(contributions.items(), key=lambda x: -abs(x[1]))),
            indent="body",
        ))

    # FCI 차트
    liq_data = summary.get("liquidity") or {}
    fci_chart = spec_fci_timeline(liq_data)
    if fci_chart:
        blocks.append(ChartBlock(fci_chart, caption="FCI 시계열"))

    return blocks


def build_phase_blocks(summary: dict) -> list:
    """제1막: 국면 진단."""
    blocks: list = []
    cycle = summary.get("cycle") or {}
    rates = summary.get("rates") or {}
    assets = summary.get("assets") or {}

    # 사이클
    blocks.append(HeadingBlock("경제 사이클", level=2))
    phase = cycle.get("phaseLabel", "판별불가")
    confidence = cycle.get("confidence", "—")
    blocks.append(MetricBlock([("국면", phase), ("신뢰도", confidence)]))

    signals = cycle.get("signals") or []
    if signals:
        blocks.append(TextBlock("근거: " + " / ".join(signals[:3])))

    # 금리
    blocks.append(HeadingBlock("금리 환경", level=2))
    outlook = rates.get("outlook") or {}
    expect = rates.get("expectation") or {}
    rate_metrics = [("방향", outlook.get("direction", "—"))]
    if expect.get("spread2yFf") is not None:
        rate_metrics.append(("2Y-FF", f"{expect['spread2yFf']:+.2f}%p"))
    blocks.append(MetricBlock(rate_metrics))

    # Nelson-Siegel
    yc = rates.get("yieldCurve")
    if yc:
        blocks.append(TextBlock(yc.get("description", "")))

    # BEI/실질금리
    rr = rates.get("realRateRegime")
    if rr:
        blocks.append(MetricBlock([("실질금리 regime", rr.get("regimeLabel", "—"))]))

    # 고용/물가
    emp = rates.get("employment") or {}
    inf = rates.get("inflation") or {}
    if emp.get("stateLabel") or inf.get("stateLabel"):
        blocks.append(MetricBlock([
            ("고용", emp.get("stateLabel", "—")),
            ("물가", inf.get("stateLabel", "—")),
        ]))

    # 자산 신호
    cu_au = assets.get("copperGold")
    if cu_au:
        blocks.append(MetricBlock([("Cu/Au", f"{cu_au.get('directionLabel', '—')} ({cu_au.get('implication', '')})")]))

    return blocks


def build_causation_blocks(summary: dict) -> list:
    """제2막: 인과 역추적."""
    blocks: list = []
    crisis = summary.get("crisis") or {}
    corporate = summary.get("corporate") or {}
    liquidity = summary.get("liquidity") or {}

    # Credit-to-GDP
    cg = crisis.get("creditGap")
    if cg:
        blocks.append(HeadingBlock("신용 환경", level=2))
        blocks.append(MetricBlock([
            ("Credit-to-GDP gap", f"{cg.get('gap', 0):+.1f}%p"),
            ("구간", cg.get("zoneLabel", "—")),
            ("CCyB", f"{cg.get('ccybBuffer', 0):.1f}%"),
        ]))

    # Minsky
    minsky = crisis.get("minskyPhase")
    if minsky:
        blocks.append(MetricBlock([("Minsky 국면", f"{minsky.get('phaseLabel', '—')} ({minsky.get('confidence', '')})")]))

    # Koo BSR
    koo = crisis.get("kooRecession")
    if koo:
        blocks.append(MetricBlock([("Koo BSR", "활성" if koo.get("isBSR") else "비활성")]))

    # Fisher
    fisher = crisis.get("fisherDeflation")
    if fisher:
        blocks.append(MetricBlock([("Fisher 위험", fisher.get("riskLabel", "—"))]))

    # 유동성
    blocks.append(HeadingBlock("유동성 환경", level=2))
    blocks.append(MetricBlock([
        ("regime", liquidity.get("regimeLabel", "—")),
        ("score", f"{liquidity.get('score', 0):+.1f}"),
    ]))
    fci = liquidity.get("fci")
    if fci:
        blocks.append(MetricBlock([("FCI", f"{fci.get('value', 0):+.3f} ({fci.get('regimeLabel', '')})")]))

    # 기업집계
    ec = corporate.get("earningsCycle")
    pr = corporate.get("ponziRatio")
    if ec or pr:
        blocks.append(HeadingBlock("기업 실태", level=2))
        corp_metrics = []
        if ec:
            corp_metrics.append(("이익사이클", ec.get("currentLabel", "—")))
        if pr:
            corp_metrics.append(("Ponzi비율", f"{pr.get('currentRatio', 0):.1%}"))
        lc = corporate.get("leverageCycle")
        if lc:
            corp_metrics.append(("레버리지", f"{lc.get('currentLevel', 0):.1f}%"))
        blocks.append(MetricBlock(corp_metrics))

        # 이익사이클 차트
        ec_chart = spec_earnings_cycle(corporate)
        if ec_chart:
            blocks.append(ChartBlock(ec_chart))

        # Ponzi 차트
        ponzi_chart = spec_ponzi_ratio(corporate)
        if ponzi_chart:
            blocks.append(ChartBlock(ponzi_chart))

    return blocks


def build_outlook_blocks(summary: dict) -> list:
    """제3막: 전망과 리스크."""
    blocks: list = []
    forecast = summary.get("forecast") or {}
    crisis = summary.get("crisis") or {}

    # 침체확률
    blocks.append(HeadingBlock("침체 전망", level=2))
    rp = forecast.get("recessionProb")
    sahm = forecast.get("sahmRule")
    hamilton = forecast.get("hamiltonRegime")
    lei = forecast.get("lei")

    outlook_metrics = []
    if rp:
        outlook_metrics.append(("프로빗 침체확률", f"{rp.get('probability', 0) * 100:.1f}%"))
    if sahm:
        outlook_metrics.append(("Sahm Rule", f"{sahm.get('value', 0):.2f}%p {'⚠ 트리거' if sahm.get('triggered') else ''}"))
    if hamilton:
        outlook_metrics.append(("Hamilton RS", f"{hamilton.get('currentRegime', '—')} ({hamilton.get('currentProb', 0):.0%})"))
    if lei and isinstance(lei, dict):
        outlook_metrics.append(("LEI", lei.get("signalLabel", lei.get("growthLabel", "—"))))
    if outlook_metrics:
        blocks.append(MetricBlock(outlook_metrics))

    # 침체확률 차트
    rc_chart = spec_recession_prob(forecast)
    if rc_chart:
        blocks.append(ChartBlock(rc_chart))

    # 리스크 경고
    flags = []
    dashboard = crisis.get("recessionDashboard") or {}
    if dashboard.get("composite", 0) > 0.3:
        flags.append(f"침체 종합확률 {dashboard.get('composite', 0) * 100:.0f}% — 경계")
    if dashboard.get("historicalMatch"):
        flags.append(f"역사 패턴: {dashboard['historicalMatch']}년과 유사")
    cg = crisis.get("creditGap") or {}
    if cg.get("zone") in ("warning", "danger"):
        flags.append(f"Credit-to-GDP gap {cg.get('zoneLabel', '')} ({cg.get('gap', 0):+.1f}%p)")
    if flags:
        blocks.append(FlagBlock(flags, kind="warning"))

    return blocks


def build_allocation_blocks(summary: dict) -> list:
    """자산배분 시사점."""
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
        if rationale:
            blocks.append(TextBlock(" / ".join(rationale[:3])))

    if strategies:
        blocks.append(HeadingBlock("투자전략 요약", level=2))
        blocks.append(MetricBlock([
            ("활성", f"{strategies.get('active', 0)}/{strategies.get('total', 40)}"),
            ("Bullish", str(strategies.get("bullish", 0))),
            ("Bearish", str(strategies.get("bearish", 0))),
        ]))

        # 활성 전략 상위 10개 (strength 순)
        sigs = strategies.get("signals") or []
        active_sigs = sorted(
            [s for s in sigs if s.get("active")],
            key=lambda x: -(x.get("strength") or 0),
        )[:10]
        if active_sigs:
            rows = []
            for s in active_sigs:
                rows.append({
                    "#": s.get("id", ""),
                    "전략": s.get("name", ""),
                    "방향": s.get("direction", ""),
                    "강도": f"{s.get('strength', 0):.2f}",
                })
            blocks.append(TableBlock("활성 전략 Top 10", pl.DataFrame(rows)))

    return blocks
