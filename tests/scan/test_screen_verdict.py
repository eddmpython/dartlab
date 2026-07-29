"""scan screen 3상태 판정과 explain 결과 계약."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest

from dartlab.scan.screen.verdict import evaluateValue, summarizeVerdicts


def test_shared_python_typescript_conformance_vectors():
    fixture = Path(__file__).parents[1] / "fixtures" / "screenConformance.json"
    cases = json.loads(fixture.read_text(encoding="utf-8"))
    for case in cases:
        raw = case["raw"]
        if raw is not None and case.get("pythonScale"):
            raw = raw / case["pythonScale"]
        assert evaluateValue(raw, case["condition"], kind=case["kind"]) == case["expected"], case["id"]


def test_missing_is_unknown_for_all_comparison_operators():
    for op in (">", ">=", "<", "<=", "==", "!=", "between", "contains"):
        condition = {"op": op, "value": [1, 2] if op == "between" else 1}
        assert evaluateValue(None, condition) == "UNKNOWN"


def test_exists_and_not_exists_are_explicit_missing_queries():
    assert evaluateValue(None, {"op": "exists"}) == "FAIL"
    assert evaluateValue(None, {"op": "not_exists"}) == "PASS"
    assert evaluateValue(3, {"op": "exists"}) == "PASS"


def test_verdict_summary_separates_failure_missing_and_near_miss():
    rows = [
        {"stockCode": "A", "roe": 20, "debt": 40},
        {"stockCode": "B", "roe": 9, "debt": 40},
        {"stockCode": "C", "roe": None, "debt": 40},
    ]
    conditions = [
        {"field": "roe", "op": ">=", "value": 10},
        {"field": "debt", "op": "<=", "value": 80},
    ]
    result = summarizeVerdicts(rows, conditions)
    assert result["memberCodes"] == ["A"]
    assert result["nearMissCodes"] == ["B"]
    assert result["excluded"] == {"failed": 1, "missingOnly": 1}
    assert result["coverage"][0]["valid"] == 2
    assert result["funnel"][-1]["survivors"] == 1


def test_any_group_uses_pass_then_unknown_then_fail_precedence():
    rows = [
        {"stockCode": "A", "x": 2, "y": None},
        {"stockCode": "B", "x": 0, "y": None},
        {"stockCode": "C", "x": 0, "y": 0},
    ]
    conditions = [
        {
            "field": "__any__",
            "op": "any",
            "alternatives": [
                {"field": "x", "op": ">", "value": 1},
                {"field": "y", "op": ">", "value": 1},
            ],
        }
    ]
    result = summarizeVerdicts(rows, conditions)
    assert result["memberCodes"] == ["A"]
    assert result["excluded"] == {"failed": 1, "missingOnly": 1}


def test_detailed_result_preserves_executor_members_and_explains_gaps(monkeypatch):
    import dartlab.scan.builders.kr.report.fields as fields

    monkeypatch.setattr(
        fields,
        "_executeScreenSpec",
        lambda spec, applyLimit: pl.DataFrame({"stockCode": ["A"], "roe": [20.0]}),
    )
    monkeypatch.setattr(fields, "_computeDerived", lambda spec: ({}, {}))
    monkeypatch.setattr(
        fields,
        "_screenUniverse",
        lambda: pl.DataFrame({"stockCode": ["A", "B", "C"]}),
    )
    monkeypatch.setattr(
        fields,
        "_fieldMeta",
        lambda field, spec=None: {"kind": "number", "unit": "%", "operatorSet": ">,>=,<,<=,==,!=,between"},
    )
    monkeypatch.setattr(
        fields,
        "_loadFieldValues",
        lambda field, spec: pl.DataFrame({"stockCode": ["A", "B"], field: [20.0, 5.0]}),
    )

    result = fields.executeScreenSpecDetailed({"where": [{"field": "roe", "op": ">=", "value": 10}], "limit": 20})
    assert result["memberCount"] == 1
    assert result["returnedMemberCount"] == 1
    assert result["membersTruncated"] is False
    assert result["members"][0]["stockCode"] == "A"
    assert result["universe"]["count"] == 3
    assert result["coverage"][0]["valid"] == 2
    assert result["excluded"] == {"failed": 1, "missingOnly": 1}
    assert result["gaps"][0]["code"] == "datasetAsOfUnavailable"


def test_detailed_result_counts_all_members_before_payload_limit(monkeypatch):
    import dartlab.scan.builders.kr.report.fields as fields

    field = "finance.ratio.roe"
    all_members = pl.DataFrame({"stockCode": ["A", "B", "C", "D", "E"], field: [50, 40, 30, 20, 10]})
    monkeypatch.setattr(fields, "_executeScreenSpec", lambda spec, applyLimit: all_members)
    monkeypatch.setattr(fields, "_computeDerived", lambda spec: ({}, {}))
    monkeypatch.setattr(fields, "_screenUniverse", lambda: all_members.select("stockCode"))
    monkeypatch.setattr(
        fields,
        "_fieldMeta",
        lambda field, spec=None: {"kind": "number", "unit": "%", "operatorSet": ">,>=,<,<=,==,!=,between"},
    )
    monkeypatch.setattr(fields, "_loadFieldValues", lambda field, spec: all_members.select("stockCode", field))

    result = fields.executeScreenSpecDetailed({"where": [{"field": field, "op": ">=", "value": 10}], "limit": 2})

    assert result["memberCount"] == 5
    assert result["returnedMemberCount"] == 2
    assert result["membersTruncated"] is True
    assert [row["stockCode"] for row in result["members"]] == ["A", "B"]


def test_screen_rejects_unimplemented_point_in_time_and_market_scope():
    import dartlab.scan.builders.kr.report.fields as fields

    with pytest.raises(ValueError, match="asOf 시점 고정"):
        fields.executeScreenSpec({"where": [], "asOf": "2024-12-31"})
    with pytest.raises(ValueError, match="KR 시장만"):
        fields.executeScreenSpec({"where": [], "market": "US"})


def test_scan_engine_call_forwards_screen_spec_and_explain(monkeypatch):
    import dartlab
    from dartlab.ai.tools.engineCall import _scan

    captured = {}

    def fake(axis, target=None, **kwargs):
        captured.update(axis=axis, target=target, kwargs=kwargs)
        return {"schemaVersion": 1, "memberCount": 2, "members": []}

    monkeypatch.setattr(dartlab, "scan", fake)
    result = _scan(
        {
            "axis": "screen",
            "target": "resilientCompounders",
            "kwargs": {"axis": "screen", "spec": {"where": []}, "explain": True},
        }
    )
    assert result.ok is True
    assert captured == {
        "axis": "screen",
        "target": "resilientCompounders",
        "kwargs": {"spec": {"where": []}, "explain": True},
    }
