from __future__ import annotations

import importlib
import json

import polars as pl
import pytest

import dartlab
from dartlab.ai.tools.engineCall import (
    _CANONICAL_COMPANY_CAPABILITY_REFS,
    _CANONICAL_TOP_LEVEL_CAPABILITY_REFS,
    _JSON_MAX_BYTES,
    _isCanonicalExecutableApiRef,
    _jsonableResult,
    _resultToRefs,
    engineCall,
)
from dartlab.ai.tools.registry import toolSpecs
from dartlab.reference.capability import loadCapabilities

pytestmark = pytest.mark.unit
engineCallModule = importlib.import_module("dartlab.ai.tools.engineCall")


@pytest.mark.parametrize("apiRef", ["Company.audit", "Company.view", "Company.sources"])
def test_noncanonical_company_member_is_blocked_before_company_resolution(
    apiRef: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    resolved = False

    def failResolution(target: str):
        nonlocal resolved
        resolved = True
        raise AssertionError(f"Company resolution must not run for {target}")

    monkeypatch.setattr(engineCallModule, "_capabilityExists", lambda candidate: candidate == apiRef)
    monkeypatch.setattr(engineCallModule, "_resolveCompany", failResolution)

    result = engineCall({"apiRef": apiRef, "target": "005930"})

    assert result.ok is False
    assert result.error == "non_public_api_ref"
    assert resolved is False


def test_company_execution_allowlist_matches_formal_capability_refs() -> None:
    expected = {
        "Company.panel",
        "Company.select",
        "Company.trace",
        "Company.filings",
        "Company.analysis",
        "Company.credit",
        "Company.gather",
        "Company.quant",
        "Company.macro",
        "Company.story",
        "Company.reportModel",
        "Company.industry",
        "Company.simulate",
    }

    assert _CANONICAL_COMPANY_CAPABILITY_REFS == expected
    assert all(_isCanonicalExecutableApiRef(apiRef) for apiRef in expected)
    assert not _isCanonicalExecutableApiRef("Company.audit")
    assert not _isCanonicalExecutableApiRef("Company.sources")


def test_engine_call_tool_spec_requires_canonical_capability_ref() -> None:
    spec = next(item for item in toolSpecs() if item["name"] == "EngineCall")

    assert "canonical capabilityRef" in spec["description"]
    assert "canonical capabilityRef" in spec["inputSchema"]["properties"]["apiRef"]["description"]


def test_company_panel_suppresses_protocol_corrupting_stdout(monkeypatch, capsys) -> None:
    expected = engineCallModule.ToolResult(True, "ok")

    def noisyCompanyShow(_plan):
        print("library diagnostic must not reach MCP stdout")
        return expected

    monkeypatch.setattr(engineCallModule, "_capabilityExists", lambda candidate: candidate == "Company.panel")
    monkeypatch.setattr(engineCallModule, "_companyShow", noisyCompanyShow)

    assert engineCall({"apiRef": "Company.panel", "args": {"stockCode": "005930"}}) is expected
    assert capsys.readouterr().out == ""


def test_top_level_execution_allowlist_excludes_stateful_and_open_world_apis() -> None:
    expected = {
        "analysis",
        "capabilities",
        "codeToName",
        "compare",
        "credit",
        "data",
        "dataHub",
        "gather",
        "help",
        "industry",
        "listing",
        "macro",
        "nameToCode",
        "pastInsight",
        "quant",
        "scan",
        "search",
        "searchName",
        "sectorInsights",
        "simulate",
    }

    assert _CANONICAL_TOP_LEVEL_CAPABILITY_REFS == expected
    assert not {"ask", "collect", "collectAll", "config", "setup", "verbose"} & expected


@pytest.mark.parametrize("apiRef", ["ask", "collect", "collectAll", "config", "setup", "verbose"])
def test_risky_top_level_api_is_blocked_before_dispatch(apiRef: str, monkeypatch: pytest.MonkeyPatch) -> None:
    dispatched = False

    def failDispatch(*args, **kwargs):
        nonlocal dispatched
        dispatched = True
        raise AssertionError(f"risky API must not run: {apiRef}, {args}, {kwargs}")

    monkeypatch.setattr(engineCallModule, "_aliasToCanonical", lambda candidate, plan: candidate)
    monkeypatch.setattr(engineCallModule, "_capabilityExists", lambda candidate: candidate == apiRef)
    monkeypatch.setattr(dartlab, apiRef, failDispatch, raising=False)

    result = engineCall({"apiRef": apiRef, "args": {}})

    assert result.ok is False
    assert result.error == "non_public_api_ref"
    assert dispatched is False


@pytest.mark.parametrize(
    "apiRef",
    [
        "compare",
        "scan",
        "scan.growth",
        "gather.price",
        "analysis.가치평가",
        "dataHub.catalog",
        "dataHub.query",
        "simulate",
    ],
)
def test_existing_formal_top_level_and_axis_capabilities_remain_executable(apiRef: str) -> None:
    assert apiRef.split(".", 1)[0] in dartlab.__all__ or apiRef.startswith(("scan.", "dataHub."))
    assert _isCanonicalExecutableApiRef(apiRef)


@pytest.mark.parametrize("apiRef", ["scan.market", "scan.industry"])
def test_reference_only_scan_contract_is_not_dispatched_as_axis(apiRef: str) -> None:
    capability = loadCapabilities()[apiRef]

    assert capability["kind"] == "ai_contract"
    assert capability["engineCallable"] is False
    result = engineCall({"apiRef": apiRef, "args": {}})
    assert result.ok is False
    assert result.error == "non_public_api_ref"


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ({"key": "analysis"}, {"key": "analysis", "search": None}),
        ({"path": "analysis"}, {"key": "analysis", "search": None}),
        ({"search": "재무건전성"}, {"key": None, "search": "재무건전성"}),
    ],
)
def test_capabilities_dispatch_preserves_documented_dict_args(
    args: dict[str, str], expected: dict[str, str | None], monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, str | None] = {}

    def fakeCapabilities(key=None, *, search=None):
        captured.update({"key": key, "search": search})
        return {"summary": "상세", "requires": ""}

    monkeypatch.setattr(engineCallModule, "_capabilityExists", lambda apiRef: apiRef == "capabilities")
    monkeypatch.setattr(dartlab, "capabilities", fakeCapabilities)

    result = engineCall({"apiRef": "capabilities", "args": args})

    assert result.ok is True
    assert captured == expected
    assert result.data["result"] == {"summary": "상세", "requires": ""}


def test_capabilities_rejects_key_and_search_together(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(engineCallModule, "_capabilityExists", lambda apiRef: apiRef == "capabilities")

    result = engineCall({"apiRef": "capabilities", "args": {"key": "analysis", "search": "재무건전성"}})

    assert result.ok is False
    assert result.error == "invalid_args"


def test_companyPanelDocumentTopicFiltersPeriodAndEmitsExactDocumentEvidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeCompany:
        stockCode = "005930"
        receivedTopic = ""

        def panel(self, topic: str):
            type(self).receivedTopic = topic
            return pl.DataFrame(
                {
                    "rcept_no": ["20250311001085", "20240312000001"],
                    "period": ["2024Q4", "2023Q4"],
                    "adt_opinion": ["적정의견", "적정의견"],
                    "core_adt_matter": ["재고자산 평가", "매출 인식"],
                }
            )

    monkeypatch.setattr(engineCallModule, "_resolveCompany", lambda _target: FakeCompany())

    result = engineCall(
        {
            "apiRef": "Company.panel",
            "args": {"stockCode": "005930", "topic": "감사", "period": "2024"},
        }
    )

    assert result.ok is True
    assert FakeCompany.receivedTopic == "auditOpinion"
    assert result.data["rowCount"] == 1
    assert result.data["tableRef"] == "table:Company.panel:005930"
    assert "result" not in result.data
    document = next(ref for ref in result.refs if ref.kind == "docRef")
    assert document.payload["rceptNo"] == "20250311001085"
    assert document.payload["filedAt"] == "2025-03-11"
    assert document.payload["section"] == "auditOpinion"
    assert "재고자산 평가" in document.payload["excerpt"]
    assert any(ref.kind == "dateRef" and ref.payload["period"] == "2024Q4" for ref in result.refs)


@pytest.mark.parametrize(
    ("apiRef", "args", "attribute", "expected"),
    [
        ("codeToName", {"stockCode": "005930"}, "stockCode", "005930"),
        ("simulate", {"target": "005930"}, "code", "005930"),
    ],
)
def test_generic_public_call_forwards_reserved_target_argument(
    apiRef: str,
    args: dict[str, str],
    attribute: str,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str] = {}

    if apiRef == "codeToName":

        def fakeCallable(stockCode: str):
            captured["stockCode"] = stockCode
            return "삼성전자"

    else:

        def fakeCallable(code: str):
            captured["code"] = code
            return {"status": "complete"}

    monkeypatch.setattr(dartlab, apiRef, fakeCallable)

    result = engineCall({"apiRef": apiRef, "args": args})

    assert result.ok is True
    assert captured[attribute] == expected


def test_data_hub_axis_dispatch_preserves_public_facade(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fakeDataHub(axis: str, target=None, **kwargs):
        captured.update({"axis": axis, "target": target, "kwargs": kwargs})
        return {"status": "complete", "snapshotId": "catalog:v1", "gaps": []}

    monkeypatch.setattr(engineCallModule, "_capabilityExists", lambda apiRef: apiRef == "dataHub.catalog")
    monkeypatch.setattr(dartlab, "dataHub", fakeDataHub)

    result = engineCall({"apiRef": "dataHub.catalog", "args": {"query": {"search": "price"}}})

    assert result.ok is True
    assert captured == {"axis": "catalog", "target": None, "kwargs": {"query": {"search": "price"}}}
    assert result.data["result"]["status"] == "complete"
    assert result.refs[0].payload["snapshotId"] == "catalog:v1"


def test_large_result_is_bounded_and_preserves_audit_contract() -> None:
    source = {
        "bulk": [{"payload": "가" * 20_000, "index": index} for index in range(1_000)],
        "status": "partial",
        "gaps": [{"code": "missing.price", "message": "가격 기준점 없음"}],
        "coverage": {"requestedAssets": 3, "resolvedAssets": 2},
        "asOf": "2025-Q4",
        "snapshotId": "data-snapshot:v1",
        "contractHash": "a" * 64,
        "provenance": ["source:filing"],
        "lineageRefs": ["lineage:filing"],
        "executionReceipts": ["receipt:query"],
    }

    payload = _jsonableResult(source)
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    assert len(encoded) <= _JSON_MAX_BYTES
    assert payload["status"] == "partial"
    assert payload["gaps"][0]["code"] == "missing.price"
    assert payload["coverage"]["resolvedAssets"] == 2
    assert payload["asOf"] == "2025-Q4"
    assert payload["snapshotId"] == "data-snapshot:v1"
    assert payload["contractHash"] == "a" * 64
    assert payload["provenance"] == ["source:filing"]
    assert payload["lineageRefs"] == ["lineage:filing"]
    assert payload["executionReceipts"] == ["receipt:query"]
    assert payload["_dartlabSerialization"]["truncated"] is True
    assert set(payload["_dartlabSerialization"]["reasons"]) & {"maxBytes", "maxContainerItems", "maxStringBytes"}


def test_large_mapping_keeps_late_audit_fields_without_copying_all_entries() -> None:
    source = {f"field{index:05d}": index for index in range(25_000)}
    source["status"] = "partial"
    source["asOf"] = "2025-Q4"
    source["lineageRefs"] = ["lineage:late"]

    payload = _jsonableResult(source)

    assert payload["status"] == "partial"
    assert payload["asOf"] == "2025-Q4"
    assert payload["lineageRefs"] == ["lineage:late"]
    assert len(payload) <= 201
    assert payload["_dartlabSerialization"]["reasons"] == ["maxContainerItems"]
    assert payload["_dartlabSerialization"]["omittedItems"] == 24_803


def test_opaque_and_cyclic_results_use_deterministic_markers_without_address_repr() -> None:
    opaque = _jsonableResult(object())
    cycle: list[object] = []
    cycle.append(cycle)
    cyclic = _jsonableResult(cycle)
    encoded = json.dumps({"opaque": opaque, "cyclic": cyclic}, ensure_ascii=False, sort_keys=True)

    assert opaque["serializationError"] == "unsupportedType"
    assert opaque["_type"] == "builtins.object"
    assert "cycle" in cyclic[0]["serializationError"]
    assert "0x" not in encoded


def test_depth_and_mapping_key_limits_are_explicit() -> None:
    nested: object = {"leaf": "value"}
    for _ in range(30):
        nested = {"nested": nested}

    depthPayload = _jsonableResult(nested)
    keyPayload = _jsonableResult({1: "silently-stringified-before", "status": "partial"})

    assert "maxDepth" in depthPayload["_dartlabSerialization"]["reasons"]
    assert 'serializationError": "maxDepth' in json.dumps(depthPayload, sort_keys=True)
    assert "1" not in keyPayload
    assert keyPayload["status"] == "partial"
    assert "nonStringMappingKey" in keyPayload["_dartlabSerialization"]["reasons"]


def test_execution_ref_keeps_status_gap_provenance_and_time_without_result_duplication() -> None:
    result = _resultToRefs(
        "Company.simulate",
        {
            "bulk": list(range(25_000)),
            "status": "partial",
            "quality": "partial",
            "gaps": [{"code": "missing.shares"}],
            "coverage": {"requestedAssets": 2, "resolvedAssets": 1},
            "asOf": "2025-Q4",
            "latestAsOf": "2026-Q1",
            "dataSnapshotId": "snapshot:data:v1",
            "dataContractHash": "b" * 64,
            "dataLineageRefs": ["lineage:one"],
            "dataExecutionReceipts": ["receipt:one"],
            "nodes": {
                "dcf": {
                    "status": "partial",
                    "provenance": "dcf:v1",
                    "refs": ["value:shares"],
                    "asOf": "2025-Q4",
                }
            },
        },
        target="005930",
    )
    execution = result.refs[0]

    assert execution.kind == "executionRef"
    assert "result" not in execution.payload
    assert execution.payload["status"] == "partial"
    assert execution.payload["gaps"][0]["code"] == "missing.shares"
    assert execution.payload["asOf"] == "2025-Q4"
    assert execution.payload["dataSnapshotId"] == "snapshot:data:v1"
    assert execution.payload["dataContractHash"] == "b" * 64
    assert execution.payload["dataLineageRefs"] == ["lineage:one"]
    assert execution.payload["dataExecutionReceipts"] == ["receipt:one"]
    assert execution.payload["nodes"]["dcf"]["provenance"] == "dcf:v1"
    assert len(execution.payload["preview"].encode("utf-8")) <= 4_000


def test_partial_simulation_preserves_honest_warning_without_invented_path_values() -> None:
    result = _resultToRefs(
        "simulate",
        {
            "stockCode": "005930",
            "scenarioName": "baseline",
            "quality": "partial",
            "requestedAsOf": "2024-Q4",
            "warnings": ["historicalSimulationParametersUnavailable"],
            "revenuePath": None,
            "marginPath": None,
            "fcfPath": None,
            "dcfPerShare": None,
        },
        target="005930",
    )

    execution = next(ref for ref in result.refs if ref.kind == "executionRef")
    table = next(ref for ref in result.refs if ref.kind == "tableRef")

    assert execution.id == "execution:simulate:005930"
    assert execution.payload["warnings"] == ["historicalSimulationParametersUnavailable"]
    assert table.payload["complete"] is False
    assert table.payload["rows"] == []
    assert table.payload["gaps"] == ["historicalSimulationParametersUnavailable"]
    assert not any(ref.kind == "valueRef" and "value" in ref.payload for ref in result.refs)
