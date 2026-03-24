"""personaCases.json의 expectedRoute/expectedModules를 LLM 없이 결정론적 검증.

이 테스트는 personaCases에 새 케이스를 추가하면 자동으로 라우팅/모듈 선택을
CI에서 검증한다. LLM 호출이 없으므로 빠르고 결정론적이다.
"""

from __future__ import annotations

from types import SimpleNamespace

import polars as pl
import pytest

from dartlab.core.memory import BoundedCache
from dartlab.engines.ai.context.builder import _resolve_context_route
from dartlab.engines.ai.eval.replayRunner import PersonaEvalCase, loadPersonaCases
from dartlab.engines.company.dart._docs_accessor import _DocsAccessor
from dartlab.engines.company.dart.company import Company

pytestmark = pytest.mark.unit

# ── Mock Company (test_ai_context_routing.py 패턴 재사용) ────


def _project(df: pl.DataFrame, columns: list[str] | None) -> pl.DataFrame:
    """select 호출 호환용."""
    if not columns:
        return df
    available = [c for c in columns if c in df.columns]
    return df.select(available) if available else pl.DataFrame()


_MOCK_DOCS_DF = pl.DataFrame(
    {
        "year": ["2024", "2024", "2023", "2023"],
        "report_type": [
            "사업보고서 (2024.12)",
            "사업보고서 (2024.12)",
            "사업보고서 (2023.12)",
            "사업보고서 (2023.12)",
        ],
        "rcept_date": ["2025-03-01", "2025-03-01", "2024-03-01", "2024-03-01"],
        "section_order": [10, 20, 10, 20],
        "section_title": ["II. 사업의 내용", "III. 재무에 관한 사항", "II. 사업의 내용", "III. 재무에 관한 사항"],
        "content": [
            "반도체, 디스플레이 사업 개요",
            "재무 요약 정보",
            "반도체, 배터리 사업 개요",
            "전년 재무 정보",
        ],
    }
)


def _makeMockCompany(*, hasDocs: bool = True, hasFinance: bool = False) -> Company:
    """LLM 없이 라우팅 테스트용 mock Company."""
    company = Company.__new__(Company)
    company.stockCode = "005930"
    company.corpName = "삼성전자"
    company._cache = BoundedCache(max_entries=30)
    company._hasDocs = hasDocs
    company._hasFinanceParquet = hasFinance
    company._hasReport = False
    company._financeChecked = True
    company._notesAccessor = None
    company.docs = _DocsAccessor(company)
    company.finance = SimpleNamespace()
    company.report = SimpleNamespace()
    company._profileAccessor = None

    if hasDocs:
        company.docs._rawDf = _MOCK_DOCS_DF
        company.docs.select = lambda columns=None: _project(_MOCK_DOCS_DF, columns)
    return company


# ── 케이스 로드 ──────────────────────────────────────────

_ALL_CASES: list[PersonaEvalCase] = loadPersonaCases()


# ── 라우팅 결정론적 검증 ─────────────────────────────────


class TestPersonaCasesRouting:
    """personaCases의 expectedRoute를 LLM 없이 검증."""

    @pytest.mark.parametrize(
        "case",
        [c for c in _ALL_CASES if c.expectedRoute],
        ids=[c.id for c in _ALL_CASES if c.expectedRoute],
    )
    def test_route_match(self, case: PersonaEvalCase):
        actual = _resolve_context_route(case.question, include=None, q_types=[])
        assert actual == case.expectedRoute, (
            f"[{case.id}] expected route={case.expectedRoute}, got={actual}\n"
            f"  question: {case.question}"
        )


# ── groundTruthFacts 구조 검증 ───────────────────────────


class TestPersonaCasesIntegrity:
    """personaCases.json 구조 무결성 검증."""

    def test_all_cases_have_required_fields(self):
        for case in _ALL_CASES:
            assert case.id, "id 누락"
            assert case.persona, f"[{case.id}] persona 누락"
            assert case.question, f"[{case.id}] question 누락"

    def test_critical_cases_have_stock_code(self):
        """critical severity 케이스는 반드시 stockCode가 있어야 한다."""
        for case in _ALL_CASES:
            if case.severity == "critical":
                assert case.stockCode, f"[{case.id}] critical case에 stockCode 누락"

    def test_no_duplicate_ids(self):
        ids = [c.id for c in _ALL_CASES]
        assert len(ids) == len(set(ids)), f"중복 id: {[i for i in ids if ids.count(i) > 1]}"

    def test_severity_values_valid(self):
        validSeverities = {"critical", "high", "medium", "low"}
        for case in _ALL_CASES:
            assert case.severity in validSeverities, f"[{case.id}] invalid severity: {case.severity}"

    def test_ground_truth_facts_structure(self):
        """groundTruthFacts가 채워져 있으면 올바른 구조인지 검증."""
        for case in _ALL_CASES:
            for fact in case.groundTruthFacts:
                assert "metric" in fact, f"[{case.id}] fact에 metric 누락"
                assert "value" in fact, f"[{case.id}] fact에 value 누락"
                assert isinstance(fact["value"], (int, float)), (
                    f"[{case.id}] fact value가 숫자가 아님: {type(fact['value'])}"
                )


# ── mustNotSay / forbiddenUiTerms 메타 검증 ──────────────


class TestPersonaCasesMeta:
    """메타데이터 일관성 검증."""

    def test_forbidden_ui_terms_not_in_question(self):
        """forbiddenUiTerms가 질문에 포함되어 있으면 안 된다 (내부 명칭 노출 방지)."""
        for case in _ALL_CASES:
            for term in case.forbiddenUiTerms:
                assert term not in case.question, (
                    f"[{case.id}] forbiddenUiTerm '{term}' 이 question에 포함됨"
                )

    def test_must_include_terms_not_empty_for_high_severity(self):
        """high/critical severity 케이스는 mustInclude가 비어있으면 안 된다."""
        for case in _ALL_CASES:
            if case.severity in ("critical", "high"):
                assert case.mustInclude, f"[{case.id}] high/critical case에 mustInclude 비어있음"
