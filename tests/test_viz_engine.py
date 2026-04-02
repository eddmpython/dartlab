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
    from dartlab.viz.palette import COLORS

    assert isinstance(COLORS, list)


def test_colors_has_at_least_5():
    from dartlab.viz.palette import COLORS

    assert len(COLORS) >= 5


def test_colors_are_hex_strings():
    from dartlab.viz.palette import COLORS

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


def test_vizspec_from_dict_diagram():
    from dartlab.viz.spec import VizSpec

    d = {"vizType": "diagram", "diagramType": "mermaid", "source": "graph TD"}
    spec = VizSpec.fromDict(d)
    assert spec.vizType == "diagram"
    assert spec.diagramType == "mermaid"
    assert spec.source == "graph TD"


# ── emit_chart / emit_diagram (stdout 캡처) ──


def test_emit_chart_marker_format(capsys):
    from dartlab.viz import emit_chart

    spec = {"chartType": "bar", "title": "Test"}
    emit_chart(spec)
    captured = capsys.readouterr().out.strip()

    assert captured.startswith("<!--DARTLAB_VIZ:")
    assert captured.endswith(":VIZ_END-->")

    # 마커 안의 JSON 파싱 가능해야 한다
    json_str = captured[len("<!--DARTLAB_VIZ:") : -len(":VIZ_END-->")]
    parsed = json.loads(json_str)
    assert parsed["chartType"] == "bar"
    assert parsed["title"] == "Test"


def test_emit_chart_adds_viztype(capsys):
    from dartlab.viz import emit_chart

    spec = {"chartType": "line", "title": "X"}
    emit_chart(spec)
    captured = capsys.readouterr().out.strip()
    json_str = captured[len("<!--DARTLAB_VIZ:") : -len(":VIZ_END-->")]
    parsed = json.loads(json_str)
    assert parsed["vizType"] == "chart"


def test_emit_diagram_marker_format(capsys):
    from dartlab.viz import emit_diagram

    emit_diagram("mermaid", "graph LR\n  A-->B", title="다이어그램")
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
    from dartlab.viz import emit_diagram

    emit_diagram("mermaid", "graph TD")
    captured = capsys.readouterr().out.strip()
    json_str = captured[len("<!--DARTLAB_VIZ:") : -len(":VIZ_END-->")]
    parsed = json.loads(json_str)
    assert parsed["title"] == ""


# ── extract_viz_specs ──


def test_extract_single_spec():
    from dartlab.viz.extract import extract_viz_specs

    spec_dict = {"chartType": "bar", "title": "T"}
    marker = f"<!--DARTLAB_VIZ:{json.dumps(spec_dict)}:VIZ_END-->"
    stdout = f"Hello\n{marker}\nWorld"

    cleaned, specs = extract_viz_specs(stdout)
    assert len(specs) == 1
    assert specs[0]["chartType"] == "bar"
    assert "DARTLAB_VIZ" not in cleaned
    assert "Hello" in cleaned
    assert "World" in cleaned


def test_extract_multiple_specs():
    from dartlab.viz.extract import extract_viz_specs

    m1 = f"<!--DARTLAB_VIZ:{json.dumps({'chartType': 'bar'})}:VIZ_END-->"
    m2 = f"<!--DARTLAB_VIZ:{json.dumps({'vizType': 'diagram', 'diagramType': 'mermaid'})}:VIZ_END-->"
    stdout = f"A\n{m1}\nB\n{m2}\nC"

    cleaned, specs = extract_viz_specs(stdout)
    assert len(specs) == 2
    assert specs[0]["chartType"] == "bar"
    assert specs[1]["diagramType"] == "mermaid"


def test_extract_no_specs():
    from dartlab.viz.extract import extract_viz_specs

    cleaned, specs = extract_viz_specs("plain text without markers")
    assert specs == []
    assert cleaned == "plain text without markers"


def test_extract_invalid_json_ignored():
    from dartlab.viz.extract import extract_viz_specs

    stdout = "pre <!--DARTLAB_VIZ:not-valid-json:VIZ_END--> post"
    cleaned, specs = extract_viz_specs(stdout)
    assert specs == []
    assert "DARTLAB_VIZ" not in cleaned


def test_extract_mixed_valid_invalid():
    from dartlab.viz.extract import extract_viz_specs

    valid = f"<!--DARTLAB_VIZ:{json.dumps({'ok': True})}:VIZ_END-->"
    invalid = "<!--DARTLAB_VIZ:{broken:VIZ_END-->"
    stdout = f"{valid}\n{invalid}"

    cleaned, specs = extract_viz_specs(stdout)
    assert len(specs) == 1
    assert specs[0]["ok"] is True
