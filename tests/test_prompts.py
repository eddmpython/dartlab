"""prompts 모듈 테스트."""

import pytest

pytestmark = pytest.mark.unit

from dartlab.ai.conversation.prompts import (
    _classify_question,
    _match_sector,
    build_system_prompt,
)


class TestBuildSystemPrompt:
    def test_default_korean(self):
        result = build_system_prompt()
        assert "K-IFRS" in result
        assert "한국어" in result or "한국" in result

    def test_english(self):
        result = build_system_prompt(lang="en")
        assert "K-IFRS" in result
        assert "Korean" in result

    def test_custom_override(self):
        custom = "You are a custom analyst."
        result = build_system_prompt(custom=custom)
        assert result == custom

    def test_topic_governance(self):
        """majorHolder+executive 포함 시 지배구조 프롬프트 추가."""
        result = build_system_prompt(included_modules=["BS", "IS", "majorHolder", "executive"])
        assert "지배구조" in result

    def test_topic_risk(self):
        """리스크 관련 모듈 포함 시 리스크 프롬프트 추가."""
        result = build_system_prompt(included_modules=["BS", "contingentLiability", "sanction"])
        assert "리스크" in result

    def test_topic_dividend(self):
        """배당 모듈 포함 시 배당 프롬프트 추가."""
        result = build_system_prompt(included_modules=["dividend", "shareCapital"])
        assert "배당" in result

    def test_topic_investment(self):
        """투자 관련 모듈 포함 시 투자 프롬프트 추가."""
        result = build_system_prompt(included_modules=["rnd", "tangibleAsset"])
        assert "투자" in result or "R&D" in result

    def test_no_modules(self):
        """included_modules=None이면 토픽 프롬프트 없음."""
        base = build_system_prompt()
        with_none = build_system_prompt(included_modules=None)
        assert base == with_none

    def test_empty_modules(self):
        """빈 리스트면 토픽 프롬프트 없음."""
        base = build_system_prompt()
        with_empty = build_system_prompt(included_modules=[])
        assert base == with_empty

    def test_backward_compatible(self):
        """인자 없이 호출 가능."""
        result = build_system_prompt()
        assert len(result) > 100

    def test_no_topic_when_unrelated(self):
        """무관한 모듈만 있으면 토픽 프롬프트 불포함 (교차검증은 포함됨)."""
        result = build_system_prompt(included_modules=["BS", "IS", "CF"])
        # BS/IS/CF는 토픽 프롬프트를 트리거하지 않지만 교차검증 규칙은 추가됨
        assert "지배구조 분석 참고" not in result
        assert "리스크 분석 참고" not in result
        assert "배당 분석 참고" not in result
        assert "교차검증" in result

    # ── 업종별 벤치마크 ──

    def test_sector_semiconductor(self):
        """반도체 업종 벤치마크 추가."""
        result = build_system_prompt(sector="반도체와반도체장비")
        assert "반도체" in result
        assert "사이클" in result

    def test_sector_bank(self):
        """은행 업종 벤치마크."""
        result = build_system_prompt(sector="은행")
        assert "NIM" in result

    def test_sector_unknown(self):
        """알 수 없는 업종이면 벤치마크 없음."""
        base = build_system_prompt()
        result = build_system_prompt(sector="우주항공")
        assert result == base

    def test_sector_none(self):
        """sector=None이면 벤치마크 없음."""
        base = build_system_prompt()
        result = build_system_prompt(sector=None)
        assert result == base

    # ── Few-shot ──

    def test_fewshot_health(self):
        """건전성 질문에 few-shot 예시 추가."""
        result = build_system_prompt(question_type="건전성")
        assert "부채비율" in result
        assert "분석 예시" in result

    def test_fewshot_profitability(self):
        """수익성 few-shot."""
        result = build_system_prompt(question_type="수익성")
        assert "분석 예시" in result

    def test_fewshot_none(self):
        """question_type=None이면 few-shot 없음."""
        base = build_system_prompt()
        result = build_system_prompt(question_type=None)
        assert result == base

    def test_fewshot_unknown(self):
        """알 수 없는 유형이면 few-shot 없음."""
        base = build_system_prompt()
        result = build_system_prompt(question_type="unknown_type")
        assert result == base

    # ── 교차검증 ──

    def test_cross_validation(self):
        """BS/IS/CF 포함 시 교차검증 규칙 추가."""
        result = build_system_prompt(included_modules=["BS", "IS"])
        assert "교차검증" in result
        assert "영업이익 vs 영업CF" in result

    # ── 복합 ──

    def test_combined_all(self):
        """업종 + 토픽 + few-shot 모두 적용."""
        result = build_system_prompt(
            included_modules=["BS", "IS", "dividend"],
            sector="반도체",
            question_type="건전성",
        )
        assert "반도체" in result
        assert "배당" in result
        assert "분석 예시" in result
        assert "교차검증" in result

    def test_no_tools_prompt_strips_tool_guidance(self):
        result = build_system_prompt(allow_tools=False)
        assert "## 현재 실행 제약" in result
        assert "이번 답변에서는 도구 호출을 사용할 수 없습니다" in result
        assert "손익계산서/재무상태표/현금흐름표/재무비율" in result
        assert "## 공시 데이터 접근법 (도구 사용)" not in result
        assert "## 공시 도구" not in result


# ══════════════════════════════════════
# _classify_question
# ══════════════════════════════════════


class TestClassifyQuestion:
    def test_health(self):
        assert _classify_question("재무 건전성을 분석해줘") == "건전성"

    def test_profitability(self):
        assert _classify_question("수익성은 어떤가요") == "수익성"

    def test_dividend(self):
        assert _classify_question("배당 정책") == "배당"

    def test_none_for_unknown(self):
        assert _classify_question("xyz 알려줘") is None


# ══════════════════════════════════════
# _match_sector
# ══════════════════════════════════════


class TestMatchSector:
    def test_exact(self):
        assert _match_sector("반도체") == "반도체"

    def test_partial(self):
        assert _match_sector("반도체와반도체장비") == "반도체"

    def test_bank(self):
        assert _match_sector("은행") == "금융/은행"

    def test_none(self):
        assert _match_sector("") is None

    def test_unknown(self):
        assert _match_sector("우주산업") is None
