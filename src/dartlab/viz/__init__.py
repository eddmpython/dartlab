"""dartlab.viz — 통합 시각화 엔진.

차트(ChartSpec), 다이어그램(Mermaid), AI 시각화 emit을 하나의 엔진에서 관리한다.

사용법::

    import dartlab

    # Company → ChartSpec 자동 생성
    specs = dartlab.viz.auto_chart(c)
    spec = dartlab.viz.spec_revenue_trend(c)

    # DataFrame → Plotly Figure (Jupyter용)
    dartlab.viz.line(df, x="year", y=["매출액"])
    dartlab.viz.bar(df, x="year", y=["영업이익"])
    dartlab.viz.revenue(c).show()

    # AI 코드에서 차트/다이어그램 출력
    from dartlab.viz import emit_chart, emit_diagram
    emit_chart({"chartType": "combo", "title": "...", ...})
    emit_diagram("mermaid", "graph LR\\n  A-->B")

    # ChartSpec → Plotly Figure 변환
    from dartlab.viz.renderers.plotly import from_spec
    fig = from_spec(spec)
"""

from __future__ import annotations

import json

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


# ── 팔레트 (SSOT 는 dartlab.viz.palette) ──
# core/select.py 가 viz 의존 없이 HTML 렌더 — viz import 시점에 자동 등록.
# pyodide 등 plotly 미설치 환경은 viz import 자체가 실패해 register 도 안 됨.
from dartlab.reference.render import register as _registerRenderer

# ── 새 SSOT API: catalog + builder + render 4 매체 ──
from dartlab.viz.builder import buildView  # noqa: F401
from dartlab.viz.catalog import (  # noqa: F401  # noqa: F401
    CATALOG,
    CREDIT_KEYS,
    DUPONT_KEYS,
    GROWTH_KEYS,
    QUALITY_KEYS,
    SNOWFLAKE_KEYS,
    STORY_KEYS,
    TAB_KEYS,
    VALUE_KEYS,
    listCards,
)
from dartlab.viz.catalog.finance import FINANCE_DASHBOARD_KEYS, OVERVIEW_KEYS  # noqa: F401
from dartlab.viz.charts import (
    balanceSheet as balance_sheet_chart,
)

# ── DataFrame → Plotly Figure (Jupyter) ──
from dartlab.viz.charts import (  # noqa: F401
    balanceSheetComposition,
    bar,
    cashflow,
    cashflowPattern,
    dividendAnalysis,
    line,
    pie,
    profitabilityRatios,
    revenue,
    # 하위호환 alias
    revenueTrend,
    waterfall,
)
from dartlab.viz.charts import (
    dividend as dividend_chart,
)
from dartlab.viz.charts import (
    profitability as profitability_chart,
)

# ── Company → ChartSpec 생성기 ──
from dartlab.viz.generators import (  # noqa: F401
    SPEC_GENERATORS,
    autoChart,
    specBalanceSheet,
    specBalanceStructureTrend,
    specCashflowSignedMatrix,
    specCashflowWaterfall,
    specDiffHeatmap,
    specDividend,
    specEvidenceCoverage,
    specGrowthYoyBar,
    specHoverSpark,
    specIncomeTrendMatrix,
    specInsightRadar,
    specKpiRibbon,
    specLeverageTrend,
    specMarginTrend,
    specPeerMatrix,
    specPeerRadar,
    specPriceChart,
    specProfitability,
    specRatioSparklines,
    specRevenueScenarioBand,
    specRevenueTrend,
    specSensitivityHeatmap,
)
from dartlab.viz.layout import (  # noqa: F401
    BLOCKS,
    KIND_DEFAULT_TIER,
    listBlocks,
    packSkyline,
    planTabLayout,
    queryCards,
    resolveLayout,
)
from dartlab.viz.palette import COLORS, INTENT_MAP, TONE_MAP, resolveColor  # noqa: F401
from dartlab.viz.render import toAscii, toPlotly, toRechartsSpec, toSvg  # noqa: F401

# ── ChartSpec → 매체 렌더러 ──
from dartlab.viz.renderers.ascii import renderAscii  # noqa: F401
from dartlab.viz.renderers.network import renderNetwork  # noqa: F401
from dartlab.viz.renderers.plotly import PlotlyChartRenderer
from dartlab.viz.renderers.plotly import fromSpec as chart_from_spec  # noqa: F401
from dartlab.viz.renderers.svg import renderSvg  # noqa: F401

# ── AI stdout 마커 추출 ──
from dartlab.viz.spec.extract import extractVizSpecs  # noqa: F401

# ── Dashboard visual intent catalog ──
from dartlab.viz.spec.intents import VIZ_INTENTS, VizIntent, listVizIntents  # noqa: F401

_registerRenderer(PlotlyChartRenderer())

# ── evidence ref 빌더 ──
# ── VizSpec ──
from dartlab.viz.spec import VizSpec  # noqa: F401
from dartlab.viz.spec.refs import (  # noqa: F401
    chartEvidenceBinding,
    filingDeepLink,
    seriesPointRefs,
    tableRef,
    valueRef,
)

# ══════════════════════════════════════
# AI 코드용 emit 함수
# ══════════════════════════════════════

_MARKER_START = "<!--DARTLAB_VIZ:"
_MARKER_END = ":VIZ_END-->"

# dartlab.analysis() 가이드 dataframe 의 axis 컬럼 값 (22 축).
# 이걸 categories 로 쓴 차트는 메타데이터 차트라 사용자 가치 0 → 거부.
_GUIDE_AXIS_NAMES = frozenset(
    {
        "수익구조",
        "자금조달",
        "자산구조",
        "현금흐름",
        "수익성",
        "성장성",
        "안정성",
        "효율성",
        "종합평가",
        "이익품질",
        "비용구조",
        "자본배분",
        "투자효율",
        "재무정합성",
        "가치평가",
        "지배구조",
        "공시변화",
        "비교분석",
        "매출전망",
        "예측신호",
        "매크로민감도",
        "밸류에이션밴드",
    }
)


def _isMetaGuideChart(spec: dict) -> bool:
    """analysis() 가이드 dataframe 으로 만든 의미 없는 메타 차트 감지.

    시그널: categories 가 dartlab 22축 이름과 5개 이상 겹치고
    series data 가 모두 0~25 범위의 작은 값 (= items 컬럼).
    """
    cats = spec.get("categories")
    if not isinstance(cats, list) or len(cats) < 5:
        return False
    cat_set = {str(c).strip() for c in cats}
    overlap = cat_set & _GUIDE_AXIS_NAMES
    if len(overlap) < 5:
        return False
    series = spec.get("series") or []
    for s in series:
        if not isinstance(s, dict):
            continue
        data = s.get("data")
        if not isinstance(data, list) or not data:
            continue
        nums = [v for v in data if isinstance(v, (int, float))]
        if nums and all(0 <= v <= 25 for v in nums):
            return True
    return False


def _hasEvidence(spec: dict) -> bool:
    """evidence 회로 진입점이 있는지 확인.

    1.0.0 정식 계약: evidenceBinding (chart-level structured) 채워져야 한다.
    transition: 14 종 기존 generator 가 가진 legacy evidenceIds 도 통과시킨다.
    diagram (vizType=diagram) 은 evidence 의무 없음.
    """
    if spec.get("vizType") == "diagram":
        return True
    binding = spec.get("evidenceBinding")
    if isinstance(binding, dict) and binding.get("tableRef"):
        return True
    legacy = spec.get("evidenceIds")
    if isinstance(legacy, list) and legacy:
        return True
    return False


def emitChart(spec: dict) -> None:
    """AI 코드에서 차트 출력.

    런타임이 stdout에서 마커를 자동 추출하여 CHART 이벤트로 전환한다.

    Args:
        spec: ChartSpec dict. chartType, title, series, categories 필수.

    Example::

        emit_chart({
            "chartType": "combo",
            "title": "삼성전자 매출 추이",
            "series": [{"name": "매출", "data": [100, 120, 150], "type": "bar"}],
            "categories": ["2022", "2023", "2024"],
        })
    """
    # R32-1: 빈 spec 거부 — chartType 없으면 webview 가 렌더 못 함
    if not spec or "chartType" not in spec and "vizType" not in spec:
        _log.warning(
            "[차트 거부] emit_chart 에 chartType 이 필요합니다. "
            "예: emit_chart({'chartType': 'line', 'title': '...', "
            "'categories': [...], 'series': [{'name': '...', 'data': [...]}]})"
        )
        return

    # 메타 가이드 차트 거부 — AI 가 dartlab.analysis() 가이드 dataframe 의
    # items 컬럼을 막대로 그리는 패턴 차단. 사용자 가치 0.
    if _isMetaGuideChart(spec):
        _log.warning(
            "[차트 거부] analysis() 가이드 dataframe 의 'items' 컬럼은 사용자에게 "
            "가치 없는 메타데이터입니다. 차트를 그리지 말고, 진짜 종목 데이터로 "
            "다시 시각화하세요. 예시:\n"
            "  hist = c.analysis('financial', '수익성')['marginTrend']['history']\n"
            "  emit_chart({'chartType':'line', 'title':'영업이익률 추이',\n"
            "              'categories':[h['period'] for h in hist],\n"
            "              'series':[{'name':'영업이익률',\n"
            "                         'data':[h['operatingMargin'] for h in hist]}]})"
        )
        return

    # evidence 회로 진입점 누락 거부 — 모든 차트는 tableRef 까지 drill 가능해야 한다.
    if not _hasEvidence(spec):
        _log.warning(
            "[차트 거부] evidenceBinding 또는 evidenceIds 가 비어 있습니다. "
            "모든 차트는 어떤 표·계정·기간에서 파생되었는지 명시해야 합니다. 예시:\n"
            "  emit_chart({\n"
            "      'chartType': 'line', 'title': '...',\n"
            "      'categories': [...], 'series': [{'name':'...', 'data':[...]}],\n"
            "      'evidenceBinding': {\n"
            "          'tableRef': 'finance:IS:annual',\n"
            "          'source': 'finance', 'stockCode': '005930',\n"
            "          'topic': 'IS', 'periodKind': 'Y',\n"
            "          'periods': [...],\n"
            "      },\n"
            "  })"
        )
        return
    spec.setdefault("vizType", "chart")
    # DARTLAB_VIZ 마커는 **사용자 출력** (webview 가 stdout 을 파싱) — print 유지.
    print(f"{_MARKER_START}{json.dumps(spec, ensure_ascii=False)}{_MARKER_END}")


def emitDiagram(diagramType: str, source: str, *, title: str = "") -> None:
    """AI 코드에서 다이어그램 출력.

    Args:
        diagram_type: 다이어그램 종류 ("mermaid" 등).
        source: 다이어그램 소스 코드.
        title: 제목 (선택).

    Example::

        emit_diagram("mermaid", "graph LR\\n  매출-->영업이익-->순이익-->FCF")
    """
    spec = {
        "vizType": "diagram",
        "diagramType": diagramType,
        "source": source,
        "title": title,
    }
    # DARTLAB_VIZ 마커는 **사용자 출력** (webview 가 stdout 을 파싱) — print 유지.
    print(f"{_MARKER_START}{json.dumps(spec, ensure_ascii=False)}{_MARKER_END}")


__all__ = [
    # palette (SSOT)
    "COLORS",
    "INTENT_MAP",
    "TONE_MAP",
    "resolveColor",
    # 새 SSOT API
    "buildView",
    "CATALOG",
    "FINANCE_DASHBOARD_KEYS",
    # 7 분석 방법론별 카드 키 (subCategory 기준 동적 추출)
    "STORY_KEYS",
    "DUPONT_KEYS",
    "VALUE_KEYS",
    "GROWTH_KEYS",
    "CREDIT_KEYS",
    "QUALITY_KEYS",
    "SNOWFLAKE_KEYS",
    "listCards",
    "toRechartsSpec",
    "toPlotly",
    "toSvg",
    "toAscii",
    # spec
    "VizSpec",
    "VizIntent",
    "VIZ_INTENTS",
    "listVizIntents",
    # refs
    "tableRef",
    "valueRef",
    "filingDeepLink",
    "chartEvidenceBinding",
    "seriesPointRefs",
    # generators
    "auto_chart",
    "spec_revenue_trend",
    "spec_cashflow_waterfall",
    "spec_balance_sheet",
    "spec_profitability",
    "spec_dividend",
    "spec_insight_radar",
    "spec_ratio_sparklines",
    "spec_diff_heatmap",
    "spec_peer_radar",
    "spec_sensitivity_heatmap",
    "spec_margin_trend",
    "spec_leverage_trend",
    "spec_growth_yoy_bar",
    "spec_revenue_scenario_band",
    "spec_six_act_radar",
    "spec_peer_matrix",
    "specPriceChart",
    "spec_kpi_ribbon",
    "spec_hover_spark",
    "spec_evidence_coverage",
    "spec_income_trend_matrix",
    "spec_balance_structure_trend",
    "spec_cashflow_signed_matrix",
    "SPEC_GENERATORS",
    # charts (Plotly)
    "line",
    "bar",
    "pie",
    "waterfall",
    "revenue",
    "cashflow",
    "dividend_chart",
    "balance_sheet_chart",
    "profitability_chart",
    # plotly
    "chart_from_spec",
    # extract
    "extract_viz_specs",
    # emit
    "emit_chart",
    "emit_diagram",
]
