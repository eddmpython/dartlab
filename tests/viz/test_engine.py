"""viz 엔진 단위 테스트.

emit_chart / emit_diagram / extract_viz_specs / VizSpec / COLORS 테스트.
데이터 로드 없음, mock 전용.
"""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.unit


# ── COLORS ──


def test_colors_is_list():
    from dartlab.core.palette import COLORS

    assert isinstance(COLORS, list)


def test_colors_has_at_least_5():
    from dartlab.core.palette import COLORS

    assert len(COLORS) >= 5


def test_colors_are_hex_strings():
    from dartlab.core.palette import COLORS

    for color in COLORS:
        assert isinstance(color, str)
        assert color.startswith("#")


# ── VizSpec ──


def test_vizspec_chart_defaults():
    from dartlab.viz.spec import VizSpec

    spec = VizSpec()
    assert spec.vizType == "chart"
    assert spec.chartType == ""
    assert spec.title == ""
    assert spec.series == []
    assert spec.categories == []


def test_vizspec_chart_construction():
    from dartlab.viz.spec import VizSpec

    spec = VizSpec(
        vizType="chart",
        chartType="bar",
        title="매출 추이",
        series=[{"name": "매출", "data": [100, 200], "type": "bar"}],
        categories=["2023", "2024"],
    )
    assert spec.chartType == "bar"
    assert spec.title == "매출 추이"
    assert len(spec.series) == 1
    assert len(spec.categories) == 2


def test_vizspec_chart_to_dict():
    from dartlab.viz.spec import VizSpec

    spec = VizSpec(chartType="line", title="Test", series=[], categories=["A"])
    d = spec.toDict()
    assert d["chartType"] == "line"
    assert d["title"] == "Test"
    assert "vizType" not in d  # chart 모드에서는 vizType 생략 (하위호환)
    assert d["categories"] == ["A"]


def test_vizspec_diagram_construction():
    from dartlab.viz.spec import VizSpec

    spec = VizSpec(
        vizType="diagram",
        diagramType="mermaid",
        source="graph LR\n  A-->B",
        title="흐름도",
    )
    assert spec.vizType == "diagram"
    assert spec.diagramType == "mermaid"


def test_vizspec_diagram_to_dict():
    from dartlab.viz.spec import VizSpec

    spec = VizSpec(
        vizType="diagram",
        diagramType="mermaid",
        source="graph LR\n  A-->B",
        title="흐름도",
        meta={"source": "test"},
    )
    d = spec.toDict()
    assert d["vizType"] == "diagram"
    assert d["diagramType"] == "mermaid"
    assert d["source"] == "graph LR\n  A-->B"
    assert d["title"] == "흐름도"
    assert "chartType" not in d


def test_vizspec_to_json():
    from dartlab.viz.spec import VizSpec

    spec = VizSpec(chartType="bar", title="테스트")
    j = spec.toJson()
    parsed = json.loads(j)
    assert parsed["chartType"] == "bar"
    assert parsed["title"] == "테스트"


def test_vizspec_from_dict_chart():
    from dartlab.viz.spec import VizSpec

    d = {"chartType": "combo", "title": "T", "series": [], "categories": []}
    spec = VizSpec.fromDict(d)
    assert spec.vizType == "chart"
    assert spec.chartType == "combo"


def testSpecPriceChartNormalizesOhlcvRows():
    from dartlab.viz.generators import specPriceChart

    rows = [
        {"date": "2026-01-02", "open": "10,000", "high": "10,500", "low": "9,900", "close": "10,200", "volume": "1000"},
        {"date": "2026-01-03", "open": 10200, "high": 10800, "low": 10100, "close": 10700, "volume": 1500},
    ]

    spec = specPriceChart(rows, stockCode="005930", corpName="삼성전자")

    assert spec is not None
    assert spec["chartType"] == "price-chart"
    assert spec["data"][0]["close"] == 10200.0
    assert spec["series"][0]["name"] == "종가"
    assert spec["evidenceBinding"]["tableRef"] == "gather:price:D"


def testCompileVisualAcceptsPriceChart():
    from dartlab.ai.tools.compileVisual import compileVisual

    result = compileVisual(
        chartType="price-chart",
        title="삼성전자 주가",
        data=[
            {"date": "2026-01-02", "open": 100, "high": 110, "low": 95, "close": 108, "volume": 1000},
            {"date": "2026-01-03", "open": 108, "high": 111, "low": 101, "close": 103, "volume": 1200},
        ],
        source="gather:price:KR:005930",
    )

    assert result.ok
    assert result.data["spec"]["chartType"] == "price-chart"
    assert len(result.data["spec"]["data"]) == 2


def testSpecBalanceStructureTrendPreservesStacks():
    from dartlab.viz.generators import specBalanceStructureTrend

    view = {
        "title": "자산 배치와 조달 구조",
        "periods": ["2024", "2025"],
        "totalAssetsSeries": [100.0, 120.0],
        "totalFundingSeries": [100.0, 120.0],
        "assetTrendParts": [
            {"id": "cash", "label": "현금", "values": [20, 24], "shares": [20, 20], "color": "#60a5fa"},
            {"id": "tangible", "label": "유형자산", "values": [40, 48], "shares": [40, 40], "color": "#94a3b8"},
        ],
        "fundingTrendParts": [
            {"id": "tradePayables", "label": "영업부채", "values": [15, 18], "shares": [15, 15]},
            {"id": "equity", "label": "자본", "values": [70, 84], "shares": [70, 70]},
        ],
        "equityTrendParts": [
            {"id": "retainedEarnings", "label": "이익잉여금", "values": [55, 66], "shares": [78.6, 78.6]},
        ],
        "debtRatio": 42.8,
    }

    spec = specBalanceStructureTrend(view, stockCode="005930", corpName="삼성전자")

    assert spec is not None
    assert spec["chartType"] == "balance-structure-trend"
    assert spec["categories"] == ["2024", "2025"]
    assert spec["options"]["totalAssetsSeries"] == [100.0, 120.0]
    assert spec["options"]["totalFundingSeries"] == [100.0, 120.0]
    assert {s["stack"] for s in spec["series"]} == {"assetTrendParts", "fundingTrendParts", "equityTrendParts"}
    assert spec["evidenceBinding"]["topic"] == "BS"


def test_vizspec_from_dict_diagram():
    from dartlab.viz.spec import VizSpec

    d = {"vizType": "diagram", "diagramType": "mermaid", "source": "graph TD"}
    spec = VizSpec.fromDict(d)
    assert spec.vizType == "diagram"
    assert spec.diagramType == "mermaid"
    assert spec.source == "graph TD"


# ── emit_chart / emit_diagram (stdout 캡처) ──


def test_emit_chart_marker_format(capsys):
    from dartlab.viz import emitChart

    spec = {"chartType": "bar", "title": "Test", "evidenceIds": ["test:fixture"]}
    emitChart(spec)
    captured = capsys.readouterr().out.strip()

    assert captured.startswith("<!--DARTLAB_VIZ:")
    assert captured.endswith(":VIZ_END-->")

    # 마커 안의 JSON 파싱 가능해야 한다
    json_str = captured[len("<!--DARTLAB_VIZ:") : -len(":VIZ_END-->")]
    parsed = json.loads(json_str)
    assert parsed["chartType"] == "bar"
    assert parsed["title"] == "Test"


def test_emit_chart_adds_viztype(capsys):
    from dartlab.viz import emitChart

    spec = {"chartType": "line", "title": "X", "evidenceIds": ["test:fixture"]}
    emitChart(spec)
    captured = capsys.readouterr().out.strip()
    json_str = captured[len("<!--DARTLAB_VIZ:") : -len(":VIZ_END-->")]
    parsed = json.loads(json_str)
    assert parsed["vizType"] == "chart"


def test_emit_diagram_marker_format(capsys):
    from dartlab.viz import emitDiagram

    emitDiagram("mermaid", "graph LR\n  A-->B", title="다이어그램")
    captured = capsys.readouterr().out.strip()

    assert captured.startswith("<!--DARTLAB_VIZ:")
    assert captured.endswith(":VIZ_END-->")

    json_str = captured[len("<!--DARTLAB_VIZ:") : -len(":VIZ_END-->")]
    parsed = json.loads(json_str)
    assert parsed["vizType"] == "diagram"
    assert parsed["diagramType"] == "mermaid"
    assert parsed["source"] == "graph LR\n  A-->B"
    assert parsed["title"] == "다이어그램"


def test_emit_diagram_default_title(capsys):
    from dartlab.viz import emitDiagram

    emitDiagram("mermaid", "graph TD")
    captured = capsys.readouterr().out.strip()
    json_str = captured[len("<!--DARTLAB_VIZ:") : -len(":VIZ_END-->")]
    parsed = json.loads(json_str)
    assert parsed["title"] == ""


# ── 메타 가이드 차트 거부 (R21 audit 후속 발견) ──


def test_emit_chart_rejects_meta_guide_axis_items(capsys, caplog):
    """analysis() 가이드 dataframe 의 axis/items 를 차트화하면 거부.

    거부 경고는 logger.warning (caplog), 정상 marker 는 stdout (capsys).
    """
    import logging

    from dartlab.viz import emitChart

    spec = {
        "chartType": "bar",
        "title": "analysis 엔진 축별 항목 수",
        "categories": [
            "수익구조",
            "자금조달",
            "자산구조",
            "현금흐름",
            "수익성",
            "성장성",
            "안정성",
            "효율성",
            "이익품질",
            "비용구조",
            "자본배분",
            "투자효율",
            "재무정합성",
            "가치평가",
        ],
        "series": [{"name": "items", "data": [8, 9, 4, 4, 6, 5, 6, 2, 6, 5, 7, 5, 6, 9]}],
    }
    with caplog.at_level(logging.WARNING, logger="dartlab.viz"):
        emitChart(spec)
    out = capsys.readouterr().out
    # 마커 emit 안 되고 (stdout), 거부 메시지 출력 (logger.warning)
    assert "DARTLAB_VIZ" not in out
    assert "차트 거부" in caplog.text
    assert "메타데이터" in caplog.text


def test_emit_chart_passes_real_data(capsys, caplog):
    """진짜 종목 시계열 데이터는 통과."""
    import logging

    from dartlab.viz import emitChart

    spec = {
        "chartType": "line",
        "title": "삼성전자 매출 추이",
        "categories": ["2021", "2022", "2023", "2024", "2025"],
        "series": [{"name": "매출", "data": [279.6, 302.2, 258.9, 300.9, 333.6]}],
        "evidenceIds": ["test:fixture"],
    }
    with caplog.at_level(logging.WARNING, logger="dartlab.viz"):
        emitChart(spec)
    out = capsys.readouterr().out
    assert "DARTLAB_VIZ" in out
    assert "차트 거부" not in caplog.text


def test_emit_chart_passes_axis_categories_with_real_values(capsys):
    """축 이름은 같지만 진짜 분석 값(큰 숫자)은 통과 — false positive 방지."""
    from dartlab.viz import emitChart

    spec = {
        "chartType": "bar",
        "title": "축별 점수 비교",
        "categories": ["수익구조", "자금조달", "자산구조", "현금흐름", "수익성"],
        "series": [{"name": "점수", "data": [85.3, 72.1, 91.4, 68.7, 77.9]}],
        "evidenceIds": ["test:fixture"],
    }
    emitChart(spec)
    captured = capsys.readouterr().out
    # 데이터가 25 초과라 가이드 패턴 아님 → 통과
    assert "DARTLAB_VIZ" in captured


# ── extract_viz_specs ──


def test_extract_single_spec():
    from dartlab.viz import extractVizSpecs

    spec_dict = {"chartType": "bar", "title": "T"}
    marker = f"<!--DARTLAB_VIZ:{json.dumps(spec_dict)}:VIZ_END-->"
    stdout = f"Hello\n{marker}\nWorld"

    cleaned, specs = extractVizSpecs(stdout)
    assert len(specs) == 1
    assert specs[0]["chartType"] == "bar"
    assert "DARTLAB_VIZ" not in cleaned
    assert "Hello" in cleaned
    assert "World" in cleaned


def test_extract_multiple_specs():
    from dartlab.viz import extractVizSpecs

    m1 = f"<!--DARTLAB_VIZ:{json.dumps({'chartType': 'bar'})}:VIZ_END-->"
    m2 = f"<!--DARTLAB_VIZ:{json.dumps({'vizType': 'diagram', 'diagramType': 'mermaid'})}:VIZ_END-->"
    stdout = f"A\n{m1}\nB\n{m2}\nC"

    cleaned, specs = extractVizSpecs(stdout)
    assert len(specs) == 2
    assert specs[0]["chartType"] == "bar"
    assert specs[1]["diagramType"] == "mermaid"


def test_extract_no_specs():
    from dartlab.viz import extractVizSpecs

    cleaned, specs = extractVizSpecs("plain text without markers")
    assert specs == []
    assert cleaned == "plain text without markers"


def test_extract_invalid_json_ignored():
    from dartlab.viz import extractVizSpecs

    stdout = "pre <!--DARTLAB_VIZ:not-valid-json:VIZ_END--> post"
    cleaned, specs = extractVizSpecs(stdout)
    assert specs == []
    assert "DARTLAB_VIZ" not in cleaned


def test_extract_mixed_valid_invalid():
    from dartlab.viz import extractVizSpecs

    valid = f"<!--DARTLAB_VIZ:{json.dumps({'ok': True})}:VIZ_END-->"
    invalid = "<!--DARTLAB_VIZ:{broken:VIZ_END-->"
    stdout = f"{valid}\n{invalid}"

    cleaned, specs = extractVizSpecs(stdout)
    assert len(specs) == 1
    assert specs[0]["ok"] is True


# ── 재무 템플릿 차트: 계약 호출만으로 그려지는가 ──

_IS_ROWS = {"항목": ["매출액", "영업이익", "당기순이익"], "2024": [100.0, 20.0, 15.0], "2025": [120.0, 25.0, 18.0]}
_BS_ROWS = {
    "항목": ["자산총계", "부채총계", "자본총계", "유동자산", "비유동자산"],
    "2024": [200.0, 80.0, 120.0, 90.0, 110.0],
    "2025": [220.0, 85.0, 135.0, 95.0, 125.0],
}
_CF_ROWS = {"항목": ["영업활동", "투자활동", "재무활동"], "2024": [30.0, -10.0, -5.0], "2025": [35.0, -12.0, -6.0]}
_CAPITAL_ROWS = {"stockCode": ["999999"], "DPS": [372.0], "배당수익률": [0.3]}


class _ContractCompany:
    """공개 계약(`panel` · `capital`) 만 구현한 Company 대역."""

    corpName = "테스트기업"
    stockCode = "999999"

    def panel(self, axis):
        import polars as pl

        rows = {"IS": _IS_ROWS, "BS": _BS_ROWS, "CF": _CF_ROWS}.get(axis)
        return pl.DataFrame(rows) if rows else None

    def capital(self):
        import polars as pl

        return pl.DataFrame(_CAPITAL_ROWS)


@pytest.mark.parametrize("name", ["revenue", "cashflow", "balanceSheet", "profitability", "dividend"])
def test_financeCharts_buildFromContractCallsOnly(name):
    """재무 템플릿 차트가 공개 계약 호출만으로 그려진다.

    예전에는 `company.IS` · `company.BS` · `company.CF` · `company.dividend` 속성을 읽었다.
    그 이름들은 계약에서 빠져 존재하지 않으므로, 다섯 차트가 회사 자료와 무관하게 늘
    데이터가 없다는 예외로 죽고 있었다.
    """
    pytest.importorskip("plotly")
    from dartlab.viz import charts

    fig = getattr(charts, name)(_ContractCompany())

    assert getattr(fig, "data", None), f"{name} 차트에 trace 가 없다"
