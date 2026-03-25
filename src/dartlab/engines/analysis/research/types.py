"""Research 엔진 데이터 타입 — 종합 기업분석 리포트."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

# ══════════════════════════════════════
# 정량 스코어링
# ══════════════════════════════════════


@dataclass
class PiotroskiScore:
    """Piotroski F-Score (0-9)."""

    total: int = 0
    components: dict[str, bool] = field(default_factory=dict)
    interpretation: str = ""  # "strong" | "moderate" | "weak"


@dataclass
class MagicFormulaScore:
    """Greenblatt Magic Formula."""

    roic: float | None = None
    earningsYield: float | None = None


@dataclass
class QmjScore:
    """AQR Quality Minus Junk (4-pillar)."""

    profitability: float | None = None
    growth: float | None = None
    safety: float | None = None
    payout: float | None = None
    composite: float | None = None


@dataclass
class LynchFairValue:
    """Peter Lynch Fair Value."""

    earningsGrowthRate: float | None = None  # 5Y EPS CAGR (%)
    fairValue: float | None = None  # growthRate * EPS
    currentPrice: float | None = None
    pegRatio: float | None = None
    signal: str | None = None  # "undervalued" | "fair" | "overvalued"


@dataclass
class DuPontResult:
    """DuPont 3-factor 분해."""

    netMargin: list[float | None] = field(default_factory=list)
    assetTurnover: list[float | None] = field(default_factory=list)
    equityMultiplier: list[float | None] = field(default_factory=list)
    roe: list[float | None] = field(default_factory=list)
    periods: list[str] = field(default_factory=list)
    driver: str = ""  # "margin" | "turnover" | "leverage" | "balanced"


@dataclass
class QuantScores:
    """정량 스코어링 프레임워크 종합."""

    piotroski: PiotroskiScore | None = None
    magicFormula: MagicFormulaScore | None = None
    qmj: QmjScore | None = None
    lynchFairValue: LynchFairValue | None = None
    buffettOwnerEarnings: float | None = None
    dupont: DuPontResult | None = None


# ══════════════════════════════════════
# 리포트 섹션
# ══════════════════════════════════════


@dataclass
class ResearchMeta:
    """리포트 메타데이터."""

    stockCode: str = ""
    corpName: str = ""
    generatedAt: str = ""
    dataAsOf: str = ""
    coverageScore: float = 0.0  # 0~1
    market: str = "KR"
    currency: str = "KRW"
    warnings: list[str] = field(default_factory=list)


@dataclass
class ExecutiveSummary:
    """핵심 요약."""

    opinion: str = ""  # "강력매수" ~ "강력매도"
    profile: str = ""  # "premium" | "growth" | "stable" | "caution" | "distress"
    targetPrice: float | None = None
    currentPrice: float | None = None
    upside: float | None = None
    thesis: str = ""
    grades: dict[str, str] = field(default_factory=dict)
    keyMetrics: list[dict[str, object]] = field(default_factory=list)


@dataclass
class InvestmentThesis:
    """투자논거."""

    bullCase: list[str] = field(default_factory=list)
    bearCase: list[str] = field(default_factory=list)
    catalysts: list[str] = field(default_factory=list)
    monitoringPoints: list[str] = field(default_factory=list)
    confidence: float = 0.0
    summaryNarrative: str = ""


@dataclass
class CompanyOverview:
    """기업 개요."""

    description: str | None = None
    sectorName: str | None = None
    industryName: str | None = None
    newsHeadlines: list[str] = field(default_factory=list)


@dataclass
class SectorKpi:
    """단일 섹터 KPI."""

    name: str = ""
    label: str = ""
    value: float | None = None
    benchmark: float | None = None
    unit: str = ""
    assessment: str = ""  # "good" | "neutral" | "bad"


@dataclass
class SectorKpis:
    """섹터별 특화 KPI."""

    sectorName: str = ""
    kpis: list[SectorKpi] = field(default_factory=list)


@dataclass
class FinancialAnalysis:
    """재무 분석."""

    dupont: DuPontResult | None = None
    marginTrends: dict[str, list[float | None]] = field(default_factory=dict)
    periods: list[str] = field(default_factory=list)


@dataclass
class EarningsQuality:
    """이익의 질."""

    cfToNi: float | None = None
    accrualRatio: float | None = None
    ccc: float | None = None  # Cash Conversion Cycle (days)
    beneishMScore: float | None = None
    assessment: str = ""  # "high" | "moderate" | "low" | "questionable"


@dataclass
class MarketData:
    """시장 데이터 요약."""

    currentPrice: float | None = None
    marketCap: float | None = None
    per: float | None = None
    pbr: float | None = None
    dividendYield: float | None = None
    high52w: float | None = None
    low52w: float | None = None
    targetPrice: float | None = None
    analystCount: int | None = None
    buyRatio: float | None = None
    foreignHoldingRatio: float | None = None
    baseRate: float | None = None
    usdKrw: float | None = None


@dataclass
class ForecastData:
    """전망 데이터."""

    revenueConsensus: list[dict[str, object]] = field(default_factory=list)
    selfForecast: dict[str, object] | None = None
    scenarioSummary: dict[str, object] | None = None


# ══════════════════════════════════════
# 새 섹션 타입 — v2
# ══════════════════════════════════════


@dataclass
class InsightDetail:
    """insight 영역 상세 — 등급 + 근거 수치."""

    area: str = ""
    grade: str = ""
    summary: str = ""
    details: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)


@dataclass
class DistressSection:
    """부실 리스크 스코어카드."""

    level: str = ""  # safe/watch/warning/danger/critical
    overall: float = 0.0  # 0~100
    creditGrade: str = ""  # AAA~D
    creditDescription: str = ""
    riskFactors: list[str] = field(default_factory=list)
    cashRunwayMonths: float | None = None
    axesSummary: list[dict[str, object]] = field(default_factory=list)


@dataclass
class AnomalySection:
    """이상치 탐지 결과."""

    items: list[dict[str, object]] = field(default_factory=list)
    criticalCount: int = 0
    warningCount: int = 0


@dataclass
class RiskSection:
    """종합 리스크 — distress + anomalies + insight.risk 통합."""

    distress: DistressSection | None = None
    anomalies: AnomalySection | None = None
    insightRisk: InsightDetail | None = None
    riskNarrative: str = ""


@dataclass
class ValuationSection:
    """밸류에이션 — DCF/DDM/상대가치 종합."""

    dcfPerShare: float | None = None
    dcfMos: float | None = None  # 안전마진 (%)
    ddmPerShare: float | None = None
    relativePerShare: float | None = None
    fairValueRange: tuple[float, float] | None = None
    verdict: str = ""  # "저평가" | "적정" | "고평가"
    methodology: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class PeerSection:
    """동종업 비교 — 섹터 배수 기반 (OOM 안전)."""

    sectorName: str = ""
    sectorMultiples: dict[str, float] = field(default_factory=dict)
    companyMultiples: dict[str, float | None] = field(default_factory=dict)
    premiumDiscount: dict[str, float | None] = field(default_factory=dict)
    peerNarrative: str = ""


# ══════════════════════════════════════
# Narrative Analysis — v3
# ══════════════════════════════════════


@dataclass
class NarrativeParagraph:
    """단일 교차분석 서술 단위."""

    dimension: str = ""  # "dupont"|"margin"|"growth"|"cashflow"|"efficiency"|"segment"|"sectorRelative"
    title: str = ""
    body: str = ""  # 2-3문장 교차분석 서술
    severity: str = ""  # "positive"|"neutral"|"negative"|"warning"


@dataclass
class NarrativeAnalysis:
    """7차원 교차분석 서술 결과."""

    paragraphs: list[NarrativeParagraph] = field(default_factory=list)
    forwardImplications: list[str] = field(default_factory=list)
    crossReferences: list[str] = field(default_factory=list)


# ══════════════════════════════════════
# 렌더링 헬퍼
# ══════════════════════════════════════


def _fmtNum(v: float | None, suffix: str = "", precision: int = 1) -> str:
    """숫자 포맷."""
    if v is None:
        return "-"
    return f"{v:,.{precision}f}{suffix}"


def _fmtBig(v: float | None) -> str:
    """자동 단위 포맷 (조/억/만)."""
    if v is None:
        return "-"
    av = abs(v)
    if av >= 1e12:
        return f"{v / 1e12:,.1f}조"
    if av >= 1e8:
        return f"{v / 1e8:,.0f}억"
    if av >= 1e4:
        return f"{v / 1e4:,.0f}만"
    return f"{v:,.0f}"


def _fmtPrice(v: float | None) -> str:
    """주가 포맷."""
    if v is None:
        return "-"
    return f"{v:,.0f}원"


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


# ══════════════════════════════════════
# ResearchResult
# ══════════════════════════════════════


@dataclass
class ResearchResult:
    """종합 기업분석 리포트."""

    # 기존 섹션
    meta: ResearchMeta = field(default_factory=ResearchMeta)
    executive: ExecutiveSummary = field(default_factory=ExecutiveSummary)
    thesis: InvestmentThesis = field(default_factory=InvestmentThesis)
    overview: CompanyOverview | None = None
    sectorKpis: SectorKpis | None = None
    financial: FinancialAnalysis | None = None
    earningsQuality: EarningsQuality | None = None
    quantScores: QuantScores | None = None
    marketData: MarketData | None = None
    forecast: ForecastData | None = None

    # v2 새 섹션
    insightDetails: list[InsightDetail] = field(default_factory=list)
    valuationAnalysis: ValuationSection | None = None
    riskAnalysis: RiskSection | None = None
    peerAnalysis: PeerSection | None = None

    # v3 교차분석 서술
    narrativeAnalysis: NarrativeAnalysis | None = None

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        try:
            from rich.console import Console

            console = Console(highlight=False, force_terminal=True)
            with console.capture() as capture:
                self._richPrint(console)
            return capture.get()
        except ImportError:
            return self.summary()

    def _repr_html_(self) -> str:
        """Jupyter / Colab / Marimo HTML 렌더링."""
        try:
            from rich.console import Console

            console = Console(record=True, force_jupyter=True, width=100)
            self._richPrint(console)
            return console.export_html(inline_styles=True)
        except ImportError:
            return f"<pre>{self.summary()}</pre>"

    def _richPrint(self, console) -> None:
        """rich Console에 전체 리포트 출력."""
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        name = self.meta.corpName or self.meta.stockCode
        ex = self.executive

        # ── 1. Header ──
        header = Text()
        header.append(f"{name}\n", style="bold white")
        header.append(f"생성일 {self.meta.generatedAt[:10] if self.meta.generatedAt else '-'}  ")
        header.append("커버리지 ")
        score = self.meta.coverageScore
        filled = int(score * 15)
        header.append("█" * filled, style="green")
        header.append("░" * (15 - filled), style="dim")
        header.append(f" {score:.0%}")
        if self.meta.warnings:
            header.append(f"\n⚠ {', '.join(self.meta.warnings)}", style="yellow")
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
        self._renderThesis(console)

        # ── 3.5 Narrative Analysis ──
        self._renderNarrative(console)

        # ── 4. Valuation ──
        self._renderValuation(console)

        # ── 5. Quant + Earnings Quality ──
        self._renderQuantAndQuality(console)

        # ── 6. Risk Analysis ──
        self._renderRisk(console)

        # ── 7. Forecast ──
        self._renderForecast(console)

        # ── 8. Peer ──
        self._renderPeer(console)

        # ── 9. Market Data ──
        self._renderMarket(console)

        # ── 10. Financial Trends ──
        self._renderFinancial(console)

        # ── 11. Sector KPIs ──
        self._renderSectorKpis(console)

        # ── 12. Overview ──
        if self.overview and self.overview.description:
            from rich.panel import Panel

            console.print(Panel(self.overview.description[:300], title="[bold]Overview[/bold]", border_style="dim"))

        # ── 13. Disclaimer ──
        console.print(f"\n[dim italic]{self.DISCLAIMER}[/]")

    def _renderThesis(self, console) -> None:
        """Investment Thesis 패널."""
        from rich.panel import Panel
        from rich.text import Text

        th = self.thesis
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

    def _renderNarrative(self, console) -> None:
        """Narrative Analysis 패널."""
        na = self.narrativeAnalysis
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

    def _renderValuation(self, console) -> None:
        """Valuation 패널."""
        va = self.valuationAnalysis
        if va is None:
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

    def _renderQuantAndQuality(self, console) -> None:
        """Quant Scores + Earnings Quality 패널 (side by side)."""
        from rich.columns import Columns
        from rich.panel import Panel
        from rich.table import Table

        panels = []
        if self.quantScores:
            qt = Table(show_header=False, box=None, padding=(0, 1))
            qt.add_column(style="dim", width=12)
            qt.add_column()
            qs = self.quantScores
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

        if self.earningsQuality:
            eq = self.earningsQuality
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
            from rich.columns import Columns

            console.print(Columns(panels, equal=True, expand=True))

    def _renderRisk(self, console) -> None:
        """Risk Analysis 패널."""
        ra = self.riskAnalysis
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
                riskText.append(f"  [{color}]● {item.get('text', '')}[/{color}]\n")
        if ra.riskNarrative:
            riskText.append(f"\n{ra.riskNarrative}", style="italic")
        console.print(Panel(riskText, title="[bold]Risk Analysis[/bold]", border_style="red"))

    def _renderForecast(self, console) -> None:
        """Forecast 패널."""
        fc = self.forecast
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
                _fmtBig(rev * 1e6 if rev else None),
                _fmtBig(op * 1e6 if op else None),
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

    def _renderPeer(self, console) -> None:
        """Peer Comparison 패널."""
        pa = self.peerAnalysis
        if pa is None:
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

    def _renderMarket(self, console) -> None:
        """Market Data 패널."""
        md = self.marketData
        if md is None:
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

    def _renderFinancial(self, console) -> None:
        """Financial Trends 패널."""
        if not self.financial or not self.financial.periods:
            return
        from rich.panel import Panel
        from rich.table import Table

        fa = self.financial
        ft = Table(show_header=True, box=None, padding=(0, 2))
        ft.add_column("지표")
        for p in fa.periods:
            ft.add_column(p, justify="right")
        if fa.marginTrends.get("operatingMargin"):
            ft.add_row("영업이익률", *[_fmtNum(v, "%") for v in fa.marginTrends["operatingMargin"]])
        if fa.marginTrends.get("netMargin"):
            ft.add_row("순이익률", *[_fmtNum(v, "%") for v in fa.marginTrends["netMargin"]])
        if fa.dupont and fa.dupont.roe:
            ft.add_row("ROE", *[_fmtNum(v * 100 if v else None, "%") for v in fa.dupont.roe])
        console.print(Panel(ft, title="[bold]Financial Trends[/bold]", border_style="dim"))

    def _renderSectorKpis(self, console) -> None:
        """Sector KPIs 패널."""
        if not self.sectorKpis:
            return
        from rich.panel import Panel
        from rich.table import Table

        st = Table(show_header=True, box=None, padding=(0, 2))
        st.add_column("KPI")
        st.add_column("값", justify="right")
        st.add_column("벤치마크", justify="right", style="dim")
        st.add_column("평가")
        for kpi in self.sectorKpis.kpis:
            val = f"{kpi.value}{kpi.unit}" if kpi.value is not None else "-"
            bench = f"{kpi.benchmark}{kpi.unit}" if kpi.benchmark is not None else "-"
            badge = {"good": "[green]✓[/]", "bad": "[red]✗[/]", "neutral": "[yellow]~[/]"}.get(kpi.assessment, "")
            st.add_row(kpi.label, val, bench, badge)
        console.print(Panel(st, title=f"[bold]섹터 KPI — {self.sectorKpis.sectorName}[/bold]", border_style="yellow"))

    def summary(self) -> str:
        """plain text 전체 출력 (rich 없는 환경용)."""
        sep = "-" * 50
        lines: list[str] = []
        name = self.meta.corpName or self.meta.stockCode

        lines.append(f"{'=' * 50}")
        lines.append(f"  {name} 종합 기업분석 리포트")
        lines.append(f"{'=' * 50}")
        lines.append(f"  생성일: {self.meta.generatedAt[:10] if self.meta.generatedAt else '-'}")
        lines.append(f"  커버리지: {self.meta.coverageScore:.0%}")
        if self.meta.warnings:
            lines.append(f"  ! {', '.join(self.meta.warnings)}")

        ex = self.executive
        lines.append(f"\n{sep}")
        lines.append("  Executive Summary")
        lines.append(sep)
        if ex.opinion:
            lines.append(f"  투자의견: {ex.opinion}  |  프로파일: {ex.profile}")
        if ex.currentPrice is not None:
            p = f"  현재가: {ex.currentPrice:,.0f}"
            if ex.targetPrice:
                p += f"  ->  목표가: {ex.targetPrice:,.0f}"
            if ex.upside is not None:
                p += f"  ({ex.upside:+.1%})"
            lines.append(p)

        th = self.thesis
        lines.append(f"\n{sep}")
        lines.append("  Investment Thesis")
        lines.append(sep)
        if th.summaryNarrative:
            lines.append(f"  {th.summaryNarrative}")
        for b in th.bullCase:
            lines.append(f"  + {b}")
        for b in th.bearCase:
            lines.append(f"  - {b}")
        lines.append(f"  확신도: {th.confidence:.0%}")

        if self.narrativeAnalysis and self.narrativeAnalysis.paragraphs:
            lines.append(f"\n{sep}")
            lines.append("  Deep Analysis")
            lines.append(sep)
            for p in self.narrativeAnalysis.paragraphs:
                lines.append(f"  [{p.dimension}] {p.body}")
            if self.narrativeAnalysis.crossReferences:
                for cr in self.narrativeAnalysis.crossReferences:
                    lines.append(f"  * {cr}")
            if self.narrativeAnalysis.forwardImplications:
                for fi in self.narrativeAnalysis.forwardImplications:
                    lines.append(f"  -> {fi}")

        if self.valuationAnalysis:
            va = self.valuationAnalysis
            lines.append(f"\n{sep}")
            lines.append("  Valuation")
            lines.append(sep)
            if va.dcfPerShare is not None:
                lines.append(f"  DCF: {va.dcfPerShare:,.0f}원")
            if va.ddmPerShare is not None:
                lines.append(f"  DDM: {va.ddmPerShare:,.0f}원")
            if va.relativePerShare is not None:
                lines.append(f"  상대가치: {va.relativePerShare:,.0f}원")
            if va.fairValueRange:
                lo, hi = va.fairValueRange
                lines.append(f"  적정범위: {lo:,.0f} ~ {hi:,.0f}원 ({va.verdict})")

        if self.riskAnalysis and self.riskAnalysis.distress:
            d = self.riskAnalysis.distress
            lines.append(f"\n{sep}")
            lines.append(f"  Risk: {d.level} (신용 {d.creditGrade})")
            lines.append(sep)
            for rf in d.riskFactors[:3]:
                lines.append(f"  ▸ {rf}")

        if self.marketData:
            md = self.marketData
            lines.append(f"\n{sep}")
            lines.append("  Market Data")
            lines.append(sep)
            parts = []
            if md.marketCap and md.marketCap > 0:
                parts.append(f"시총 {_fmtBig(md.marketCap)}")
            if md.per is not None:
                parts.append(f"PER {md.per:.1f}")
            if md.pbr is not None:
                parts.append(f"PBR {md.pbr:.2f}")
            if parts:
                lines.append(f"  {' | '.join(parts)}")

        lines.append(f"\n{'=' * 50}")
        lines.append(f"  {self.DISCLAIMER}")
        lines.append(f"{'=' * 50}")
        return "\n".join(lines)

    def toDict(self) -> dict:
        """전체 리포트를 dict로 변환."""
        return asdict(self)
