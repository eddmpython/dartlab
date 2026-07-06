"""P2 리포트 emitter 게이트 — Story 블록 → 계약 ReportBlock 매핑 + pro 블록 합성 (offline).

플랜 SSOT: mainPlan/professional-report-engine/03-report-engine-architecture.md §2.3.
buildReportModel 은 self-calc 0 — 본 파일은 순수 매핑 헬퍼(_mapBlock·_valuationView·
_scenarioSet·_buildThesis)를 합성 입력으로 검증. company 데이터 의존 end-to-end 는 CI.
"""

from __future__ import annotations

from dartlab.story.blocks import FlagBlock, HeadingBlock, MetricBlock, TableBlock, TextBlock
from dartlab.story.report import _creditView, _headlineKpis, _mapBlock, _scenarioSet, _valuationView


class _FakeDf:
    """to_dicts 만 흉내내는 경량 DataFrame 스텁(테스트용)."""

    def __init__(self, rows: list[dict]):
        self._rows = rows

    def to_dicts(self) -> list[dict]:
        """행 dict 리스트 반환."""
        return self._rows


# ── 블록 매핑 (legacy 6 → 계약 8) ──


def test_map_heading_and_text():
    assert _mapBlock(HeadingBlock(title="수익체력")) == {"type": "heading", "title": "수익체력"}
    assert _mapBlock(TextBlock(text="요약")) == {"type": "text", "text": "요약"}
    assert _mapBlock(TextBlock(text="")) is None, "빈 text 는 graceful None"


def test_map_metrics_and_flags():
    m = _mapBlock(MetricBlock(metrics=[("ROIC", "9.9%"), ("WACC", "7.7%")]))
    assert m == {"type": "metrics", "metrics": [{"label": "ROIC", "value": "9.9%"}, {"label": "WACC", "value": "7.7%"}]}
    f = _mapBlock(FlagBlock(flags=["부채 급증"], kind="warning"))
    assert f == {"type": "flags", "kind": "warning", "flags": ["부채 급증"]}
    fo = _mapBlock(FlagBlock(flags=["현금 풍부"], kind="opportunity"))
    assert fo["kind"] == "opportunity"


def test_map_table_stringifies_cells():
    t = _mapBlock(TableBlock(label="요약", df=_FakeDf([{"연도": 2024, "매출": None}])))
    assert t["type"] == "table"
    assert t["data"] == [{"연도": "2024", "매출": ""}], "None=빈칸, 숫자=문자열"


# ── pro 블록 합성 ──


def test_valuation_view_from_dfv():
    dfv = {
        "dFV": 196337,
        "currentPrice": 80000,
        "primaryModel": "dcf2stage",
        "qualityWACC": {"adjustedWACC": 7.72},
        "reinvestmentCheck": {"fundamentalGrowth": 8.91, "reinvestRate": 0.9, "roic0": 9.9},
        "reverseDcf": {"impliedGrowth": 12.0, "supportedGrowth": 8.91, "verdict": "시장 과대 성장 반영"},
    }
    v = _valuationView(dfv)
    assert v["model"] == "DCF"
    assert v["intrinsic"] == 196337 and v["current"] == 80000
    assert v["wacc"] == 7.72 and v["g"] == 8.91 and v["roic"] == 9.9
    assert v["reverseDcf"]["impliedGrowth"] == 12.0
    assert {"label": "내재가치", "value": 196337} in v["bridge"]


def test_valuation_view_none_on_no_intrinsic():
    assert _valuationView({"dFV": None}) is None
    assert _valuationView({"dFV": 0}) is None, "0/음수 내재가치 = None"


def test_scenario_set_legs_and_upside():
    dfv = {"scenarios": {"bear": 172777, "base": 196337, "bull": 219897}, "currentPrice": 100000}
    s = _scenarioSet(dfv)
    assert [leg["key"] for leg in s["legs"]] == ["bear", "base", "bull"]
    base = next(leg for leg in s["legs"] if leg["key"] == "base")
    assert base["intrinsic"] == 196337 and base["upside"] == 96.3, "upside = (iv-cur)/cur×100"


def test_scenario_set_none_without_base():
    assert _scenarioSet({"scenarios": {}}) is None


# ── P1e 신용 pro 블록 (creditPanel) ──


def test_credit_view_maps_badge(monkeypatch):
    from dartlab.credit import engine as _engine

    result = {
        "grade": "dCR-AA+",
        "gradeRaw": "AA+",
        "score": 12.0,
        "healthScore": 88.0,
        "pdEstimate": 0.4,
        "outlook": "안정적",
        "investmentGrade": True,
        "axes": [{"name": "레버리지", "weight": 0.25, "score": 82}, "junk"],
    }
    monkeypatch.setattr(_engine, "evaluateCompany", lambda c, **k: result)
    cv = _creditView(object())
    assert cv["grade"] == "dCR-AA+" and cv["gradeRaw"] == "AA+"
    assert cv["pdEstimate"] == 0.4 and cv["outlook"] == "안정적"
    assert cv["investmentGrade"] is True
    assert cv["confidenceMethod"] == "ratio" and cv["confidence"] is not None
    assert cv["axes"] == [{"name": "레버리지", "weight": 0.25, "score": 82}], "dict 아닌 축은 걸러짐"


def test_credit_view_none_on_no_grade(monkeypatch):
    from dartlab.credit import engine as _engine

    monkeypatch.setattr(_engine, "evaluateCompany", lambda c, **k: None)
    assert _creditView(object()) is None, "평가 None 이면 None"
    monkeypatch.setattr(_engine, "evaluateCompany", lambda c, **k: {"grade": None})
    assert _creditView(object()) is None, "grade 없으면 None (graceful skip)"


def test_headline_includes_credit_grade():
    kpis = _headlineKpis(None, None, {"gradeRaw": "AA+"})
    assert {"label": "신용등급", "value": "AA+"} in kpis
    assert _headlineKpis(None, None, None) == [], "credit None 이면 신용 KPI 미추가"


def test_build_report_model_emits_credit_section(monkeypatch):
    """emitter end-to-end 배선 (무거운 company 의존은 monkeypatch): credit 섹션이 조립되는지."""
    import types

    from dartlab.analysis.valuation import dFV as _dfv
    from dartlab.credit import engine as _engine
    from dartlab.story import registry as _registry
    from dartlab.story import thesis as _thesis
    from dartlab.story.report import buildReportModel

    sec = types.SimpleNamespace(key="earnings", title="수익체력", blocks=[TextBlock(text="요약")])
    card = types.SimpleNamespace(grades={"수익성": "A"}, conclusion="양호")
    story = types.SimpleNamespace(sections=[sec], summaryCard=card, stockCode="005930", corpName="삼성전자")
    result = {
        "grade": "dCR-AA+",
        "gradeRaw": "AA+",
        "score": 10,
        "healthScore": 90,
        "pdEstimate": 0.4,
        "outlook": "안정적",
        "investmentGrade": True,
        "axes": [],
    }
    monkeypatch.setattr(_registry, "buildStory", lambda c, **k: story)
    monkeypatch.setattr(_dfv, "calcDFV", lambda c, **k: None)
    monkeypatch.setattr(_engine, "evaluateCompany", lambda c, **k: result)
    monkeypatch.setattr(_thesis, "buildThesis", lambda *a, **k: None)

    model = buildReportModel(object(), "full")
    assert model.get("schemaVersion") == 2
    creditSecs = [s for s in model["sections"] if s["sourceEngine"] == "credit"]
    assert len(creditSecs) == 1, "credit 섹션 1개 배선"
    blk = creditSecs[0]["blocks"][0]
    assert blk["type"] == "creditPanel" and blk["view"]["gradeRaw"] == "AA+"
    assert {"label": "신용등급", "value": "AA+"} in model["headlineKpis"]
    assert model["provenance"]["engines"].get("credit"), "provenance 에 credit 엔진 집계"
