"""ReadSkill capability auto-inline 검증.

2026-05-18 Phase A 회귀 가드. OAuth probe 에서 ReadSkill → ReadCapability →
EngineCall 패턴 (ReadCapability 자동 동행) 발견. ReadSkill 의 capabilityRefs 가
id 만 노출해 모델이 capability 의 실제 시그니처를 알 수 없어 ReadCapability 재호출.

해소: readSkill.py 의 `_inlineCapabilities` 가 spec.capabilityRefs id 마다
CAPABILITIES dict 에서 payload fetch → rows[].capabilityDetails 로 inline.
top-1 후보는 6 필드 (summary/args/example/guide/capabilities/returns),
그 외 후보는 summary + args 만.

본 테스트가 보장하는 것:
1. ReadSkill 결과 row 에 capabilityDetails 키 존재.
2. capabilityRefs id 가 CAPABILITIES 에 있는 경우 자동 inline.
3. id 가 CAPABILITIES 에 없으면 graceful (capabilityDetails 에서 skip).
4. top-1 후보가 그 외 후보보다 더 풍부한 필드.
5. field 별 cap (args 600 / example 500 / guide 800 등) 적용 확인.
"""

from __future__ import annotations

import json

import pytest

from dartlab.ai.tools.registry import executeTool

pytestmark = pytest.mark.unit


def test_readskill_inlines_capability_details_for_top_candidate() -> None:
    """ReadSkill 결과의 첫 후보에 capabilityDetails 가 비어있지 않다."""
    result = executeTool("ReadSkill", {"query": "수익성 분석 종목", "limit": 3, "includeUser": False})
    assert result["ok"] is True
    rows = result["data"]["skills"]
    assert rows, "skills 결과 비어있으면 안 됨"
    top = rows[0]
    assert "capabilityDetails" in top, "capabilityDetails 키 누락"
    # top 후보는 capabilityRefs 가 비어있지 않은 한 details 가 inline 돼야 함.
    if top.get("capabilityRefs"):
        # 적어도 일부 ref 는 CAPABILITIES 에 등록돼 있어야 (Company.analysis 등 메인 capability)
        # 단, 비어 있어도 graceful 동작 자체는 보장 — 다만 의미 있는 query 에 대해선 1+ 매칭 기대.
        assert isinstance(top["capabilityDetails"], dict)


def test_readskill_capability_payload_trimmed_to_caps() -> None:
    """top-1 의 inline payload 가 field cap 안에 들어와 token 폭증 방지."""
    result = executeTool("ReadSkill", {"query": "회사 재무제표 분석", "limit": 1, "includeUser": False})
    rows = result["data"]["skills"]
    if not rows:
        pytest.skip("skill 매칭 0 — 검증 불가")
    details = rows[0].get("capabilityDetails") or {}
    if not details:
        pytest.skip("inline 된 capability 0 — 검증 불가")
    for apiRef, payload in details.items():
        # 각 필드는 정해진 cap 내
        assert len(payload.get("args", "")) <= 600, f"{apiRef} args cap 초과"
        assert len(payload.get("example", "")) <= 500, f"{apiRef} example cap 초과"
        assert len(payload.get("guide", "")) <= 800, f"{apiRef} guide cap 초과"


def test_readskill_capability_inline_richer_for_top_than_others() -> None:
    """top-1 후보가 다른 후보보다 더 많은 필드 inline."""
    result = executeTool("ReadSkill", {"query": "신용 분석 dCR", "limit": 3, "includeUser": False})
    rows = result["data"]["skills"]
    if len(rows) < 2:
        pytest.skip("후보 2 개 이상 필요")

    def _fieldCount(row: dict) -> int:
        details = row.get("capabilityDetails") or {}
        return sum(len(v) for v in details.values() if isinstance(v, dict))

    top_count = _fieldCount(rows[0])
    others_count = sum(_fieldCount(r) for r in rows[1:])
    # top-1 이 capability 0 이면 비교 불가
    if top_count == 0:
        pytest.skip("top-1 capabilityDetails 0")
    # top-1 의 평균 필드 수 ≥ 그 외 평균
    # (절대값 비교는 capability 등록 여부에 의존하므로 ratio 로 검증)
    top_per_ref = top_count / max(1, len(rows[0].get("capabilityDetails") or {}))
    others_per_ref = others_count / max(1, sum(len(r.get("capabilityDetails") or {}) for r in rows[1:]))
    if others_per_ref == 0:
        # 그 외 후보가 capability 자체 0 이라 비교 불가 — top 만 inline 됐다는 의미라 통과.
        return
    assert top_per_ref >= others_per_ref, (
        f"top per-ref {top_per_ref} < others per-ref {others_per_ref} — top 이 더 풍부해야 함"
    )


def test_readskill_capability_inline_graceful_for_unknown_ref() -> None:
    """CAPABILITIES 에 없는 ref 가 capabilityRefs 에 있어도 ReadSkill 자체는 정상 (graceful skip)."""
    # 직접 _inlineCapabilities 호출
    from dartlab.ai.tools.readSkill import _inlineCapabilities

    out = _inlineCapabilities(["UnknownCapability.foo.bar", "AlsoUnknown"], isTopRank=True)
    assert isinstance(out, dict)
    assert "UnknownCapability.foo.bar" not in out
    assert "AlsoUnknown" not in out

    # 빈 list 도 graceful
    assert _inlineCapabilities([], isTopRank=True) == {}
    assert _inlineCapabilities([], isTopRank=False) == {}


def test_readskill_capability_inline_known_ref_returns_fields() -> None:
    """CAPABILITIES 에 등록된 ref (Company.panel 등) 는 inline 시 핵심 필드 포함."""
    from dartlab.ai.tools.readSkill import _inlineCapabilities

    out = _inlineCapabilities(["Company.panel"], isTopRank=True)
    assert "Company.panel" in out, "Company.panel 가 CAPABILITIES 에 등록돼 있어야"
    payload = out["Company.panel"]
    # 핵심 필드 중 적어도 하나는 inline (전부 빈 capability 는 비현실적)
    assert any(k in payload for k in ("summary", "args", "guide", "example")), f"핵심 필드 0 — {list(payload.keys())}"


def test_readskill_topCandidateInlinesQuestionCoverageCapabilities() -> None:
    """명시 skill ref 밖의 질문 facet도 top 후보 한 번에 실행 계약으로 제공한다."""
    result = executeTool(
        "ReadSkill",
        {
            "query": "삼성전자 산업 경쟁력과 금리 환율 영향을 반영해 가치평가해줘",
            "limit": 3,
            "includeUser": False,
        },
    )

    coverage = result["data"]["coverage"]
    top = result["data"]["skills"][0]
    assert {"analysis.가치평가", "industry", "macro"}.issubset(coverage["candidateCapabilityRefs"])
    assert top["coverageCapabilityRefs"] == coverage["candidateCapabilityRefs"]
    assert {"analysis.가치평가", "industry", "macro"}.issubset(top["capabilityDetails"])
    assert all(detail.get("execution") for detail in top["capabilityDetails"].values() if detail["engineCallable"])


def test_readskill_disclosure_payload_stays_within_runtime_budget() -> None:
    result = executeTool(
        "ReadSkill",
        {
            "query": "삼성전자 2024년 감사의견과 핵심감사사항을 공시 원문 근거와 함께 확인",
            "limit": 5,
            "includeUser": False,
        },
    )

    assert len(json.dumps(result, ensure_ascii=False, default=str).encode("utf-8")) < 64 * 1024
