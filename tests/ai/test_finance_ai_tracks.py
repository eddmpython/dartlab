"""finance AI 격상 9 트랙 smoke + contract 검증.

Track A v1 (filing deep-link) / B (confidence + provenance + ProvenanceTree) /
G (dCR badge) / E (industry badge) / I (EvidenceGate) /
D (ScenarioOverlay) / C (PeerCompareN) / F (viz dataContract) contract 고정.

목적: 이름 / 시그니처 / 핵심 키 회귀 차단. dartlab 데이터 의존 무거운 경로는 skip.
"""

from __future__ import annotations

import pytest

from dartlab.ai.tools import executeTool, listToolNames

pytestmark = pytest.mark.unit


def test_9track_tools_registered() -> None:
    """9 트랙 신규 도구 모두 registry 에 등록 (CompareCompanies 는 PeerCompareN 에 흡수)."""
    names = listToolNames()
    for tool in ("PeerCompareN", "ScenarioOverlay", "EvidenceGate"):
        assert tool in names, f"{tool} 누락"
    assert "CompareCompanies" not in names, "CompareCompanies 는 PeerCompareN 에 흡수되어 제거됨"


def test_track_b_confidence_label_ssot() -> None:
    """Track B — core/confidence.label 의 low/mid/high 매핑 SSOT."""
    from dartlab.core.confidence import label

    assert label(95) == "high"
    assert label(70) == "mid"
    assert label(50) == "mid"
    assert label(40) == "mid"
    assert label(39) == "low"


def test_track_b_verify_penalty() -> None:
    """Track B — verify 실패 시 -50, 0 미만 떨어지지 않음."""
    from dartlab.core.confidence import applyVerifyPenalty

    assert applyVerifyPenalty(100, verifyOk=True) == 100
    assert applyVerifyPenalty(100, verifyOk=False) == 50
    assert applyVerifyPenalty(30, verifyOk=False) == 0  # max(0, 30-50)


def test_track_b_base_scores_policy() -> None:
    """Track B — method 별 base score 정책 고정."""
    from dartlab.core.confidence import baseScore

    assert baseScore("filing_direct") == 95
    assert baseScore("ratio") == 80
    assert baseScore("trend") == 75
    assert baseScore("forecast") == 30
    assert baseScore("scenario") == 35
    assert baseScore("llm") == 40
    assert baseScore("external") == 50


def test_track_f_data_contract_validate() -> None:
    """Track F — viz dataContract.validate silent-fail 방지."""
    from dartlab.viz.dataContract import validate

    contract = {"shape": "crossSection", "requiredKeys": ["stockCode", "roe"], "peerCount": 3}
    ok, _ = validate(contract, [{"stockCode": "005930", "roe": 13.5}])
    assert ok is True
    ok2, msg = validate(contract, [{"stockCode": "005930"}])
    assert ok2 is False
    assert "roe" in msg


def test_track_i_evidence_gate_missing() -> None:
    """Track I — requiredEvidence 모두 누락 시 data.ok=False + missing 리스트.

    tool-execution status (`result['ok']`) 와 gate validation status (`data['ok']`) 분리:
    gate 가 정상 실행돼 누락을 *발견* 한 것은 tool 실패 아님. 외부 ok=False 면
    agent.py 의 failure_streak 가 gate 검증 실패까지 도구 실패로 계상해 결국 차단되는
    회귀 (2026-05-17 OAuth Q2 probe 에서 EvidenceGate "error" status 표시 확인).
    """
    result = executeTool("EvidenceGate", {"skillId": "recipes.fundamental.valuation.damodaran.index", "refs": []})
    assert result["ok"] is True  # tool 정상 실행
    assert result["data"]["ok"] is False  # gate validation 실패
    assert isinstance(result["data"]["missing"], list)
    assert len(result["data"]["missing"]) >= 1


def test_track_d_scenario_missing_name() -> None:
    """Track D — scenarioName 필수 검증."""
    result = executeTool("ScenarioOverlay", {"scenarioName": ""})
    assert result["ok"] is False
    assert result["error"] == "missing_scenario"


def test_track_c_compare_empty() -> None:
    """Track C — PeerCompareN stockCodes 부족(2 개 미만)은 에러 (CompareCompanies 흡수)."""
    result = executeTool("PeerCompareN", {"stockCodes": []})
    assert result["ok"] is False
    assert result["error"] == "insufficient_stock_codes"
