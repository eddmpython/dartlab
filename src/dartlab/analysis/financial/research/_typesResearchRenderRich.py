"""ResearchResult rich rendering — Console / HTML 렌더 함수."""

from __future__ import annotations

from dartlab.core.utils.fmt import fmtBig as _fmtBig
from dartlab.core.utils.fmt import fmtNum as _fmtNum
from dartlab.core.utils.fmt import fmtPrice as _fmtPrice


def _renderSectorKpis(result, console) -> None:
    """Lazy proxy — _typesResearchRenderSummary.py 의 _renderSectorKpis (cycle 회피)."""
    from dartlab.analysis.financial.research._typesResearchRenderSummary import (
        _renderSectorKpis as _f,
    )

    _f(result, console)


def _opinionColor(opinion: str) -> str:
    """투자의견 → rich 색상."""
    m = {"강력매수": "bold green", "매수": "green", "중립": "yellow", "매도": "red", "강력매도": "bold red"}
    return m.get(opinion, "white")


def _profileBadge(profile: str) -> tuple[str, str]:
    """프로파일 → (뱃지, 색상)."""
    m = {
        "premium": ("★", "bold green"),
        "growth": ("▲", "green"),
        "stable": ("●", "cyan"),
        "caution": ("▼", "yellow"),
        "distress": ("✗", "bold red"),
    }
    return m.get(profile, ("?", "white"))


def _assessColor(assessment: str) -> str:
    """평가 → 색상."""
    return {"high": "green", "good": "green", "moderate": "yellow", "neutral": "yellow"}.get(assessment, "red")


def _distressColor(level: str) -> str:
    """부실 수준 → 색상."""
    return {"safe": "green", "watch": "cyan", "warning": "yellow", "danger": "red", "critical": "bold red"}.get(
        level, "white"
    )


def _verdictColor(verdict: str) -> str:
    """밸류에이션 판정 → 색상."""
    return {"저평가": "green", "적정": "yellow", "고평가": "red"}.get(verdict, "white")


def _richPrint(result, console) -> None:
    """rich Console에 전체 리포트 출력."""
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    name = result.meta.corpName or result.meta.stockCode
    ex = result.executive

    # ── 1. Header ──
    header = Text()
    header.append(f"{name}\n", style="bold white")
    header.append(f"생성일 {result.meta.generatedAt[:10] if result.meta.generatedAt else '-'}  ")
    header.append("커버리지 ")
    score = result.meta.coverageScore
    filled = int(score * 15)
    header.append("█" * filled, style="green")
    header.append("░" * (15 - filled), style="dim")
    header.append(f" {score:.0%}")
    if result.meta.warnings:
        header.append(f"\n⚠ {', '.join(result.meta.warnings)}", style="yellow")
    console.print(Panel(header, title="[bold]Research Report[/bold]", border_style="blue"))

    # ── 2. Executive Summary ──
    execTable = Table(show_header=False, box=None, padding=(0, 2))
    execTable.add_column(style="dim", width=10)
    execTable.add_column()
    if ex.opinion:
        badge, bcolor = _profileBadge(ex.profile)
        execTable.add_row(
            "투자의견", f"[{_opinionColor(ex.opinion)}]{ex.opinion}[/]  [{bcolor}]{badge} {ex.profile}[/]"
        )
    if ex.currentPrice is not None:
        priceText = f"{ex.currentPrice:,.0f}"
        if ex.targetPrice:
            priceText += f"  →  [bold]{ex.targetPrice:,.0f}[/bold]"
        if ex.upside is not None:
            color = "green" if ex.upside > 0 else "red"
            priceText += f"  [{color}]({ex.upside:+.1%})[/{color}]"
        execTable.add_row("가격", priceText)
    if ex.grades:
        gradeText = Text()
        for k, v in ex.grades.items():
            color = "green" if v in ("A", "B") else "yellow" if v == "C" else "red"
            gradeText.append(f" {k}=", style="dim")
            gradeText.append(v, style=f"bold {color}")
        execTable.add_row("등급", gradeText)
    if ex.keyMetrics:
        metricText = " | ".join(f"{m['label']} {m['value']}{m.get('unit', '')}" for m in ex.keyMetrics)
        execTable.add_row("핵심지표", metricText)
    console.print(Panel(execTable, title="[bold]Executive Summary[/bold]", border_style="cyan"))

    # ── 3. Investment Thesis ──
    _renderThesis(result, console)

    # ── 3.5 Narrative Analysis ──
    _renderNarrative(result, console)

    # ── 4. Valuation ──
    _renderValuation(result, console)

    # ── 5. Quant + Earnings Quality ──
    _renderQuantAndQuality(result, console)

    # ── 6. Risk Analysis ──
    _renderRisk(result, console)

    # ── 7. Forecast ──
    _renderForecast(result, console)

    # ── 8. Peer ──
    _renderPeer(result, console)

    # ── 9. Market Data ──
    _renderMarket(result, console)

    # ── 10. Financial Trends ──
    _renderFinancial(result, console)

    # ── 11. Sector KPIs ──
    _renderSectorKpis(result, console)

    # ── 12. Overview ──
    if result.overview and result.overview.description:
        from rich.panel import Panel

        console.print(Panel(result.overview.description[:300], title="[bold]Overview[/bold]", border_style="dim"))

    # ── 13. Disclaimer ──
    console.print(f"\n[dim italic]{result.DISCLAIMER}[/]")


def _renderThesis(result, console) -> None:
    """Investment Thesis 패널."""
    from rich.panel import Panel
    from rich.text import Text

    th = result.thesis
    thText = Text()
    if th.summaryNarrative:
        thText.append(f"{th.summaryNarrative}\n\n", style="bold")
    if th.bullCase:
        thText.append("Bull Case\n", style="bold green")
        for b in th.bullCase:
            thText.append(f"  + {b}\n", style="green")
    if th.bearCase:
        thText.append("Bear Case\n", style="bold red")
        for b in th.bearCase:
            thText.append(f"  - {b}\n", style="red")
    if th.catalysts:
        thText.append("촉매\n", style="bold yellow")
        for c in th.catalysts:
            thText.append(f"  ▸ {c}\n", style="yellow")
    if th.monitoringPoints:
        thText.append("모니터링\n", style="bold dim")
        for m in th.monitoringPoints:
            thText.append(f"  ◦ {m}\n", style="dim")
    thText.append(f"\n확신도 {th.confidence:.0%}", style="bold")
    console.print(Panel(thText, title="[bold]Investment Thesis[/bold]", border_style="green"))


def _renderNarrative(result, console) -> None:
    """Narrative Analysis 패널."""
    na = result.narrativeAnalysis
    if na is None or not na.paragraphs:
        return
    from rich.panel import Panel
    from rich.text import Text

    nt = Text()
    severityStyle = {
        "positive": "green",
        "negative": "red",
        "warning": "yellow",
        "neutral": "dim",
    }
    for p in na.paragraphs:
        color = severityStyle.get(p.severity, "white")
        icon = {"positive": "▲", "negative": "▼", "warning": "⚠", "neutral": "●"}.get(p.severity, "●")
        nt.append(f"{icon} {p.title}\n", style=f"bold {color}")
        nt.append(f"  {p.body}\n\n")
    if na.crossReferences:
        nt.append("교차분석\n", style="bold cyan")
        for cr in na.crossReferences:
            nt.append(f"  ◆ {cr}\n", style="cyan")
        nt.append("\n")
    if na.forwardImplications:
        nt.append("전망 시사점\n", style="bold magenta")
        for fi in na.forwardImplications:
            nt.append(f"  → {fi}\n", style="magenta")
    console.print(Panel(nt, title="[bold]Deep Analysis[/bold]", border_style="bright_blue"))


def _renderValuation(result, console) -> None:
    """Valuation 패널."""
    va = result.valuationAnalysis
    if va is None:
        return
    if va.dcfPerShare is None and va.ddmPerShare is None and va.relativePerShare is None and va.fairValueRange is None:
        return
    from rich.panel import Panel
    from rich.table import Table

    vt = Table(show_header=True, box=None, padding=(0, 2))
    vt.add_column("방법론")
    vt.add_column("적정가", justify="right")
    vt.add_column("비고")
    if va.dcfPerShare is not None:
        mos = f"안전마진 {va.dcfMos:.0f}%" if va.dcfMos is not None else ""
        vt.add_row("DCF", _fmtPrice(va.dcfPerShare), mos)
    if va.ddmPerShare is not None:
        vt.add_row("DDM (배당)", _fmtPrice(va.ddmPerShare), "")
    if va.relativePerShare is not None:
        vt.add_row("상대가치", _fmtPrice(va.relativePerShare), "섹터 배수 기반")
    if va.fairValueRange:
        lo, hi = va.fairValueRange
        color = _verdictColor(va.verdict)
        vt.add_row(
            "[bold]종합[/bold]",
            f"[bold]{lo:,.0f} ~ {hi:,.0f}원[/bold]",
            f"[{color}]{va.verdict}[/{color}]",
        )
    for m in va.methodology:
        vt.add_row("", "", f"[dim]{m}[/dim]")
    for w in va.warnings:
        vt.add_row("", "", f"[yellow]⚠ {w}[/yellow]")
    console.print(Panel(vt, title="[bold]Valuation[/bold]", border_style="magenta"))


def _renderQuantAndQuality(result, console) -> None:
    """Quant Scores + Earnings Quality 패널 (side by side)."""
    from rich.columns import Columns
    from rich.panel import Panel
    from rich.table import Table

    panels = []
    if result.quantScores:
        qt = Table(show_header=False, box=None, padding=(0, 1))
        qt.add_column(style="dim", width=12)
        qt.add_column()
        qs = result.quantScores
        if qs.piotroski:
            p = qs.piotroski
            bar = "[green]●[/]" * p.total + "[dim]○[/]" * (9 - p.total)
            qt.add_row("Piotroski", f"{bar}  {p.total}/9 ({p.interpretation})")
        if qs.magicFormula:
            mf = qs.magicFormula
            parts = []
            if mf.roic is not None:
                parts.append(f"ROIC {mf.roic:.1f}%")
            if mf.earningsYield is not None:
                parts.append(f"EY {mf.earningsYield:.1f}%")
            qt.add_row("Magic Formula", " | ".join(parts) if parts else "-")
        if qs.qmj and qs.qmj.composite is not None:
            q = qs.qmj
            qt.add_row(
                "QMJ",
                f"{q.composite:.2f}  (P{q.profitability:.1f} G{q.growth:.1f} S{q.safety:.1f})",
            )
        if qs.lynchFairValue:
            lv = qs.lynchFairValue
            sig = {
                "undervalued": "[green]저평가[/]",
                "overvalued": "[red]고평가[/]",
                "fair": "[yellow]적정[/]",
            }.get(lv.signal or "", "")
            parts = []
            if lv.fairValue is not None:
                parts.append(f"적정 {lv.fairValue:,.0f}")
            if lv.pegRatio is not None:
                parts.append(f"PEG {lv.pegRatio:.2f}")
            parts.append(sig)
            qt.add_row("Lynch", " ".join(parts))
        if qs.buffettOwnerEarnings is not None:
            qt.add_row("Buffett OE", _fmtBig(qs.buffettOwnerEarnings))
        if qs.dupont:
            qt.add_row("DuPont", f"주도: [bold]{qs.dupont.driver}[/bold]")
        panels.append(Panel(qt, title="[bold]Quant Scores[/bold]", border_style="magenta"))

    if result.earningsQuality:
        eq = result.earningsQuality
        et = Table(show_header=False, box=None, padding=(0, 1))
        et.add_column(style="dim", width=10)
        et.add_column()
        et.add_row("평가", f"[{_assessColor(eq.assessment)}]{eq.assessment}[/]")
        if eq.cfToNi is not None:
            et.add_row("CF/NI", _fmtNum(eq.cfToNi, precision=2))
        if eq.accrualRatio is not None:
            et.add_row("Accrual", _fmtNum(eq.accrualRatio, precision=4))
        if eq.ccc is not None:
            et.add_row("CCC", f"{eq.ccc:.0f}일")
        if eq.beneishMScore is not None:
            color = "green" if eq.beneishMScore < -2.22 else "red"
            et.add_row("Beneish M", f"[{color}]{eq.beneishMScore:.2f}[/]")
        panels.append(Panel(et, title="[bold]이익의 질[/bold]", border_style="magenta"))

    if panels:
        console.print(Columns(panels, equal=True, expand=True))


def _renderRisk(result, console) -> None:
    """Risk Analysis 패널."""
    ra = result.riskAnalysis
    if ra is None:
        return
    from rich.panel import Panel
    from rich.text import Text

    riskText = Text()
    if ra.distress:
        d = ra.distress
        color = _distressColor(d.level)
        riskText.append("부실 위험: ", style="dim")
        riskText.append(f"{d.level.upper()}", style=f"bold {color}")
        riskText.append(f"  (종합 {d.overall:.0f}/100, 신용 {d.creditGrade})\n")
        if d.cashRunwayMonths is not None:
            riskText.append(f"현금소진 예상: {d.cashRunwayMonths:.0f}개월\n", style="yellow")
        for rf in d.riskFactors[:3]:
            riskText.append(f"  ▸ {rf}\n", style="dim")
    if ra.anomalies and ra.anomalies.items:
        a = ra.anomalies
        riskText.append("\n이상치: ", style="dim")
        riskText.append(f"Critical {a.criticalCount}", style="bold red")
        riskText.append(f" / Warning {a.warningCount}\n", style="yellow")
        for item in a.items[:4]:
            sev = item.get("severity", "")
            color = "red" if sev in ("critical", "danger") else "yellow"
            riskText.append(f"  ● {item.get('text', '')}\n", style=color)
    if ra.riskNarrative:
        riskText.append(f"\n{ra.riskNarrative}", style="italic")
    console.print(Panel(riskText, title="[bold]Risk Analysis[/bold]", border_style="red"))


def _renderForecast(result, console) -> None:
    """Forecast 패널."""
    fc = result.forecast
    if fc is None:
        return
    from rich.panel import Panel
    from rich.table import Table

    ft = Table(show_header=True, box=None, padding=(0, 1))
    ft.add_column("연도", style="dim")
    ft.add_column("매출", justify="right")
    ft.add_column("영업이익", justify="right")
    ft.add_column("EPS", justify="right")
    for rc in fc.revenueConsensus:
        rev = rc.get("revenueEst")
        op = rc.get("operatingProfitEst")
        ft.add_row(
            str(rc.get("fiscalYear", "?")),
            _fmtBig(rev * 1e8 if rev else None),
            _fmtBig(op * 1e8 if op else None),
            _fmtNum(rc.get("epsEst"), "원", precision=0) if rc.get("epsEst") else "-",
        )
    if fc.selfForecast:
        sf = fc.selfForecast
        method = sf.get("method", "")
        gr = sf.get("growthRate")
        conf = sf.get("confidence", "")
        if gr is not None:
            ft.add_row("", f"[dim]자체예측 성장 {gr:.1f}% ({method}, {conf})[/dim]", "", "")
    if fc.scenarioSummary:
        sc = fc.scenarioSummary
        base = sc.get("base")
        bull = sc.get("bull")
        bear = sc.get("bear")
        if base is not None:
            ft.add_row(
                "",
                f"[dim]시나리오 Base {_fmtPrice(base)} / Bull {_fmtPrice(bull)} / Bear {_fmtPrice(bear)}[/dim]",
                "",
                "",
            )
    console.print(Panel(ft, title="[bold]Forecast[/bold]", border_style="blue"))


def _renderPeer(result, console) -> None:
    """Peer Comparison 패널."""
    pa = result.peerAnalysis
    if pa is None:
        return
    hasCompanyData = any(v is not None for v in pa.companyMultiples.values())
    if not hasCompanyData and not pa.sectorMultiples:
        return
    from rich.panel import Panel
    from rich.table import Table

    pt = Table(show_header=True, box=None, padding=(0, 2))
    pt.add_column("배수")
    pt.add_column("기업", justify="right")
    pt.add_column("섹터", justify="right", style="dim")
    pt.add_column("할인/할증", justify="right")
    for key in ["PER", "PBR", "EV/EBITDA"]:
        cv = pa.companyMultiples.get(key)
        sv = pa.sectorMultiples.get(key)
        pd = pa.premiumDiscount.get(key)
        cvText = f"{cv:.1f}배" if cv is not None else "-"
        svText = f"{sv:.1f}배" if sv is not None else "-"
        if pd is not None:
            color = "green" if pd < 0 else "red"
            pdText = f"[{color}]{pd:+.0f}%[/{color}]"
        else:
            pdText = "-"
        pt.add_row(key, cvText, svText, pdText)
    if pa.peerNarrative:
        pt.add_row("", f"[dim]{pa.peerNarrative}[/dim]", "", "")
    console.print(Panel(pt, title=f"[bold]Peer — {pa.sectorName}[/bold]", border_style="yellow"))


def _renderMarket(result, console) -> None:
    """Market Data 패널."""
    md = result.marketData
    if md is None:
        return
    hasData = (md.marketCap and md.marketCap > 0) or md.per is not None or md.pbr is not None
    if not hasData:
        return
    from rich.panel import Panel
    from rich.table import Table

    mt = Table(show_header=False, box=None, padding=(0, 1))
    mt.add_column(style="dim", width=10)
    mt.add_column()
    if md.marketCap and md.marketCap > 0:
        mt.add_row("시가총액", _fmtBig(md.marketCap))
    if md.per is not None:
        mt.add_row("PER", _fmtNum(md.per, "배"))
    if md.pbr is not None:
        mt.add_row("PBR", _fmtNum(md.pbr, "배", precision=2))
    if md.dividendYield is not None:
        mt.add_row("배당률", _fmtNum(md.dividendYield, "%"))
    if md.high52w and md.low52w and md.high52w > 0:
        mt.add_row("52주", f"{md.low52w:,.0f} ~ {md.high52w:,.0f}")
    if md.foreignHoldingRatio is not None:
        mt.add_row("외인보유", _fmtNum(md.foreignHoldingRatio, "%"))
    if md.analystCount and md.analystCount > 0:
        mt.add_row("애널리스트", f"{md.analystCount}명")
    if md.baseRate is not None:
        mt.add_row("기준금리", _fmtNum(md.baseRate, "%"))
    console.print(Panel(mt, title="[bold]Market Data[/bold]", border_style="blue"))


def _renderSummaryPanel(
    console,
    periods,
    summary,
    *,
    gateKey: str,
    tableTitle: str,
    panelTitle: str,
    labels: dict,
    percentKeys: set | None = None,
    ratioKeys: set | None = None,
) -> None:
    """라벨 표 하나를 기간 열 표로 그려 패널에 담는다. 자료가 없으면 아무 것도 안 그린다.

    `gateKey` 가 비면 섹션 전체를 건너뛴다. 대표 항목이 없으면 나머지가 있어도 읽을 수 없는
    표가 되기 때문이고, 이 규칙은 섹션마다 대표 항목이 달라 인자로 받는다.

    값 표기는 세 가지다. 백분율, 배수, 큰 금액. 어느 것인지는 지표가 정하지 그리는 쪽이
    정하지 않는다.
    """
    if not summary or not summary.get(gateKey):
        return
    from rich.panel import Panel
    from rich.table import Table

    table = Table(show_header=True, box=None, padding=(0, 2), title=tableTitle)
    table.add_column("지표", style="dim")
    for period in periods:
        table.add_column(period, justify="right")
    for key, label in labels.items():
        values = summary.get(key)
        if not values:
            continue
        if percentKeys and key in percentKeys:
            table.add_row(label, *[_fmtNum(v, "%", precision=1) for v in values])
        elif ratioKeys and key in ratioKeys:
            table.add_row(label, *[_fmtNum(v, "배", precision=2) for v in values])
        else:
            table.add_row(label, *[_fmtBig(v) for v in values])
    console.print(Panel(table, title=f"[bold]{panelTitle}[/bold]", border_style="cyan"))


def _addTrendRows(table, trends: dict, rows: tuple, *, unit: str = "%", precision: int = 1, big: bool = False) -> None:
    """값이 있는 지표만 골라 표에 행으로 붙인다.

    없는 지표는 빈 행을 만들지 않고 건너뛴다. 자료가 없는 것과 값이 0 인 것이 표에서
    같아 보이면 안 되기 때문이다.
    """
    for key, label in rows:
        values = trends.get(key)
        if not values:
            continue
        if big:
            table.add_row(label, *[_fmtBig(v) for v in values])
        else:
            table.add_row(label, *[_fmtNum(v, unit, precision=precision) for v in values])


def _renderTrendPanel(console, periods, fa) -> None:
    """수익성부터 규모까지 다섯 구간을 한 표에 순서대로 쌓아 패널로 낸다.

    다섯을 따로 그리지 않는 이유가 있다. 같은 기간 열을 공유하고 빈 줄로만 구분하는
    한 덩어리라, 따로 그리면 열 너비가 구간마다 달라져 눈으로 세로 비교가 안 된다.
    """
    from rich.panel import Panel
    from rich.table import Table

    # ── 1) 수익성 추이 ──
    ft = Table(show_header=True, box=None, padding=(0, 2), title="수익성 추이")
    ft.add_column("지표", style="dim")
    for p in periods:
        ft.add_column(p, justify="right")
    _addTrendRows(
        ft,
        fa.marginTrends,
        (
            ("grossMargin", "매출총이익률"),
            ("operatingMargin", "영업이익률"),
            ("netMargin", "순이익률"),
            ("costOfSalesRatio", "원가율"),
            ("sgaRatio", "판관비율"),
        ),
    )

    # ── 2) DuPont 분해 ──
    if fa.dupont and fa.dupont.roe:
        dp = fa.dupont
        ft.add_row("")  # separator
        ft.add_row(
            "[bold]ROE[/bold]",
            *[_fmtNum(v * 100 if v else None, "%") for v in dp.roe],
        )
        ft.add_row(
            "  순이익률",
            *[_fmtNum(v * 100 if v else None, "%") for v in dp.netMargin],
        )
        ft.add_row(
            "  자산회전율",
            *[_fmtNum(v, "배", precision=2) for v in dp.assetTurnover],
        )
        ft.add_row(
            "  레버리지",
            *[_fmtNum(v, "배") for v in dp.equityMultiplier],
        )

    # ── 3) 효율성 추이 ──
    if fa.marginTrends.get("dso") or fa.marginTrends.get("ccc"):
        ft.add_row("")  # separator
        _addTrendRows(
            ft,
            fa.marginTrends,
            (
                ("dso", "매출채권회전일"),
                ("dio", "재고자산회전일"),
                ("dpo", "매입채무회전일"),
                ("ccc", "[bold]CCC[/bold]"),
            ),
            unit="일",
            precision=0,
        )

    # ── 4) 성장률 ──
    if fa.marginTrends.get("salesGrowth"):
        ft.add_row("")
        ft.add_row("매출 성장률", *[_fmtNum(v, "%") for v in fa.marginTrends["salesGrowth"]])
    if fa.marginTrends.get("opGrowth"):
        ft.add_row("영업이익 성장률", *[_fmtNum(v, "%") for v in fa.marginTrends["opGrowth"]])

    # ── 5) 규모 (억 단위) ──
    if fa.marginTrends.get("sales"):
        ft.add_row("")
        ft.add_row("매출", *[_fmtBig(v) for v in fa.marginTrends["sales"]])
    _addTrendRows(ft, fa.marginTrends, (("operatingProfit", "영업이익"), ("netProfit", "순이익")), big=True)

    console.print(Panel(ft, title="[bold]Financial Analysis[/bold]", border_style="cyan"))


def _renderFinancial(result, console) -> None:
    """Financial Trends — 수익성·DuPont·효율성 종합 테이블."""
    if not result.financial or not result.financial.periods:
        return
    from rich.panel import Panel
    from rich.table import Table

    fa = result.financial
    periods = fa.periods

    _renderTrendPanel(console, periods, fa)

    # ── 6~8) BS·CF·3표 연결 요약 ──
    # 세 섹션이 "표 만들고, 라벨 표 돌며 행 추가하고, 패널로 출력" 하는 같은 모양이었다.
    # 라벨과 단위 규칙만 다르므로 그것만 자료로 넘긴다.
    _renderSummaryPanel(
        console,
        periods,
        fa.bsSummary,
        gateKey="totalAssets",
        tableTitle="재무상태표 요약",
        panelTitle="Balance Sheet Summary",
        labels={
            "totalAssets": "자산총계",
            "currentAssets": "유동자산",
            "nonCurrentAssets": "비유동자산",
            "totalLiabilities": "부채총계",
            "totalEquity": "자본총계",
            "cashAndEquivalents": "현금및현금성자산",
            "retainedEarnings": "이익잉여금",
            "debtRatio": "부채비율",
            "currentRatio": "유동비율",
        },
        percentKeys={"debtRatio", "currentRatio"},
    )
    _renderSummaryPanel(
        console,
        periods,
        fa.cfSummary,
        gateKey="operatingCf",
        tableTitle="현금흐름표 요약",
        panelTitle="Cash Flow Summary",
        labels={
            "operatingCf": "영업CF",
            "investingCf": "투자CF",
            "financingCf": "재무CF",
            "capex": "CAPEX",
            "fcf": "FCF",
        },
    )
    _renderSummaryPanel(
        console,
        periods,
        fa.crossStatementMetrics,
        gateKey="ocfToNetIncome",
        tableTitle="3표 연결 지표",
        panelTitle="Cross-Statement Metrics",
        labels={
            "ocfToNetIncome": "OCF/NI",
            "capexToDepreciation": "CAPEX/감가상각",
            "retainedEarningsGrowth": "이익잉여금 증가율",
        },
        percentKeys={"retainedEarningsGrowth"},
        ratioKeys={"ocfToNetIncome", "capexToDepreciation"},
    )
