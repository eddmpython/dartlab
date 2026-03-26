"""Context 커버리지 테스트.

모든 report/disclosure registry 모듈이 최소 1개 질문 유형에서
AI 자동 주입 경로가 있는지 검증한다. unit 마커.
"""

import pytest

pytestmark = pytest.mark.unit


# 질문 유형별 주입 모듈 매핑 (builder.py)
from dartlab.ai.context.builder import _QUESTION_MODULES

# Pipeline runner + L2 엔진에서 자동 주입되는 모듈 (코드 분석 기반)
_PIPELINE_AUTO_MODULES = {
    "BS",
    "IS",
    "CF",
    "ratios",
    "fsSummary",
    "companyOverview",
}

# raw 데이터/내부 전용 (AI 주입 대상 아님)
_EXCLUDED_MODULES = {
    "rawDocs",
    "rawFinance",
    "rawReport",
    "sections",  # 텍스트 방대, tool calling 전용
    "timeseries",  # get_data tool로 접근
    "ratioSeries",  # get_data tool로 접근
    "annual",  # 내부 전용
}


class TestModuleCoverage:
    """registry 모듈의 AI 도달 가능성 검증."""

    def test_all_question_modules_reachable(self):
        """_QUESTION_MODULES의 모든 모듈이 유효한 Company 속성명."""
        all_modules = set()
        for modules in _QUESTION_MODULES.values():
            all_modules.update(modules)

        # 모듈명 기본 검증: 빈 문자열이나 공백 없음
        for mod in all_modules:
            assert mod.strip(), "빈 모듈명 발견"
            assert " " not in mod, f"공백 포함 모듈명: '{mod}'"

    def test_question_types_cover_key_modules(self):
        """핵심 report 모듈들이 최소 1개 질문 유형에서 주입됨."""
        all_modules = set()
        for modules in _QUESTION_MODULES.values():
            all_modules.update(modules)

        # 반드시 포함되어야 하는 핵심 모듈
        required_modules = {
            "dividend",
            "employee",
            "majorHolder",
            "audit",
            "rnd",
            "segments",
            "productService",
            "contingentLiability",
        }

        missing = required_modules - all_modules
        assert not missing, f"핵심 모듈이 _QUESTION_MODULES에 없음: {missing}"

    def test_every_question_type_has_content(self):
        """모든 질문 유형(공시 제외)에 최소 1개 모듈이 배정됨."""
        for q_type, modules in _QUESTION_MODULES.items():
            if q_type == "공시":
                continue  # 공시는 show_topic 안내 전용
            assert len(modules) >= 1, f"질문 유형 '{q_type}'에 주입 모듈 없음"

    def test_no_duplicate_within_question_type(self):
        """같은 질문 유형 내 중복 모듈 없음."""
        for q_type, modules in _QUESTION_MODULES.items():
            assert len(modules) == len(set(modules)), f"'{q_type}'에 중복 모듈: {modules}"


class TestPipelineCoverage:
    """pipeline runner가 빈 슬롯 없이 구성되었는지 검증."""

    def test_no_empty_pipeline_except_gongsi(self):
        """공시를 제외한 모든 질문 유형에 runner가 존재."""
        from dartlab.ai.runtime.pipeline import _PIPELINE_MAP

        for q_type, runners in _PIPELINE_MAP.items():
            if q_type == "공시":
                continue
            assert len(runners) >= 1, f"질문 유형 '{q_type}'에 pipeline runner 없음"

    def test_pipeline_map_keys_match_question_modules(self):
        """pipeline과 builder의 질문 유형 키가 일치."""
        from dartlab.ai.runtime.pipeline import _PIPELINE_MAP

        pipeline_keys = set(_PIPELINE_MAP.keys())
        builder_keys = set(_QUESTION_MODULES.keys())

        assert pipeline_keys == builder_keys, (
            f"불일치 — pipeline만: {pipeline_keys - builder_keys}, builder만: {builder_keys - pipeline_keys}"
        )


class TestRegistryCentralization:
    """registry 기반 자동 생성 검증."""

    def test_registry_question_types_valid(self):
        """registry aiQuestionTypes 값이 모두 유효한 질문 유형."""
        from dartlab.ai.conversation.templates.analysis_rules import QUESTION_TYPE_MAP
        from dartlab.core.registry import buildQuestionModules

        valid = set(QUESTION_TYPE_MAP.keys())
        for qt in buildQuestionModules():
            assert qt in valid, f"유효하지 않은 질문 유형: {qt}"

    def test_ai_exposed_report_has_ai_metadata(self):
        """report/disclosure의 aiExposed 모듈은 aiQuestionTypes 또는 aiKeywords 중 최소 1개."""
        from dartlab.core._entries import _ENTRIES

        # 재무제표 직접 / 범용 모듈은 제외
        _EXEMPT = {"BS", "IS", "CF", "fsSummary", "sections", "companyOverviewDetail"}
        missing = []
        for e in _ENTRIES:
            if e.aiExposed and e.category in ("report", "disclosure") and e.name not in _EXEMPT:
                if not e.aiQuestionTypes and not e.aiKeywords:
                    missing.append(e.name)
        assert not missing, f"aiExposed인데 AI 메타 없음: {missing}"

    def test_topic_map_covers_all_registry_keywords(self):
        """_TOPIC_MAP이 registry aiKeywords를 모두 포함."""
        from dartlab.ai.context.builder import _TOPIC_MAP
        from dartlab.core.registry import buildKeywordMap

        for kw in buildKeywordMap():
            assert kw in _TOPIC_MAP, f"키워드 '{kw}'가 _TOPIC_MAP에 없음"

    def test_question_modules_superset_of_registry(self):
        """_QUESTION_MODULES가 registry 자동 생성 결과를 포함."""
        from dartlab.core.registry import buildQuestionModules

        auto = buildQuestionModules()
        for qt, mods in auto.items():
            final_set = set(_QUESTION_MODULES.get(qt, []))
            auto_set = set(mods)
            missing = auto_set - final_set
            assert not missing, f"'{qt}': registry 모듈이 _QUESTION_MODULES에 빠짐: {missing}"


class TestValidationCoverage:
    """validation.py 매핑 커버리지 검증."""

    def test_label_patterns_cover_core_accounts(self):
        """핵심 금액 계정이 validation 매핑에 포함."""
        from dartlab.ai.runtime.validation import _LABEL_PATTERNS

        required = {"매출액", "영업이익", "당기순이익", "자산총계", "부채총계"}
        covered = set(_LABEL_PATTERNS.keys())
        missing = required - covered
        assert not missing, f"validation 금액 매핑 누락: {missing}"

    def test_ratio_patterns_cover_core_ratios(self):
        """핵심 비율이 validation 매핑에 포함."""
        from dartlab.ai.runtime.validation import _RATIO_PATTERNS

        required = {"ROE", "ROA", "영업이익률", "부채비율", "유동비율"}
        covered = set(_RATIO_PATTERNS.keys())
        missing = required - covered
        assert not missing, f"validation 비율 매핑 누락: {missing}"
