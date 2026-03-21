"""Pydantic 모델 검증 테스트."""

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit

from dartlab.server.models import (
    AiProfileUpdateRequest,
    AiSecretUpdateRequest,
    AskRequest,
    ConfigureRequest,
    HistoryMessage,
    HistoryMeta,
    TocChapter,
    TocResponse,
    TocTopic,
    ViewContext,
    ViewContextCompany,
)


class TestAskRequest:
    def test_minimal_valid(self):
        req = AskRequest(question="삼성전자 실적은?")
        assert req.question == "삼성전자 실적은?"
        assert req.company is None
        assert req.stream is False

    def test_full_valid(self):
        req = AskRequest(
            company="삼성전자",
            question="매출 추세",
            provider="openai",
            model="gpt-4o",
            stream=True,
        )
        assert req.company == "삼성전자"
        assert req.provider == "openai"
        assert req.stream is True

    def test_empty_question_rejected(self):
        with pytest.raises(ValidationError):
            AskRequest(question="")

    def test_question_max_length(self):
        req = AskRequest(question="x" * 5000)
        assert len(req.question) == 5000

    def test_question_too_long(self):
        with pytest.raises(ValidationError):
            AskRequest(question="x" * 5001)

    def test_company_max_length(self):
        with pytest.raises(ValidationError):
            AskRequest(question="test", company="x" * 101)

    def test_with_history(self):
        req = AskRequest(
            question="후속 질문",
            history=[
                HistoryMessage(role="user", text="삼성전자 실적"),
                HistoryMessage(role="assistant", text="삼성전자는..."),
            ],
        )
        assert len(req.history) == 2
        assert req.history[0].role == "user"


class TestHistoryMessage:
    def test_basic(self):
        msg = HistoryMessage(role="user", text="질문")
        assert msg.role == "user"
        assert msg.meta is None

    def test_with_meta(self):
        msg = HistoryMessage(
            role="user",
            text="질문",
            meta=HistoryMeta(company="삼성전자", stockCode="005930"),
        )
        assert msg.meta.stockCode == "005930"


class TestViewContext:
    def test_basic(self):
        vc = ViewContext(type="company", topic="BS")
        assert vc.type == "company"
        assert vc.period is None

    def test_with_company(self):
        vc = ViewContext(
            type="company",
            company=ViewContextCompany(stockCode="005930", corpName="삼성전자"),
        )
        assert vc.company.stockCode == "005930"


class TestConfigureRequest:
    def test_defaults(self):
        req = ConfigureRequest()
        assert req.provider == "codex"
        assert req.role is None


class TestAiProfileUpdateRequest:
    def test_all_none(self):
        req = AiProfileUpdateRequest()
        assert req.provider is None
        assert req.temperature is None

    def test_with_values(self):
        req = AiProfileUpdateRequest(provider="openai", temperature=0.7, max_tokens=4096)
        assert req.temperature == 0.7


class TestAiSecretUpdateRequest:
    def test_basic(self):
        req = AiSecretUpdateRequest(provider="openai")
        assert req.clear is False

    def test_clear(self):
        req = AiSecretUpdateRequest(provider="openai", clear=True)
        assert req.clear is True


class TestTocModels:
    def test_toc_topic(self):
        t = TocTopic(topic="BS", label="재무상태표", textCount=5, tableCount=3)
        assert t.hasChanges is False

    def test_toc_response(self):
        resp = TocResponse(
            stockCode="005930",
            corpName="삼성전자",
            chapters=[
                TocChapter(
                    chapter="I",
                    topics=[TocTopic(topic="BS", label="재무상태표", textCount=5, tableCount=3)],
                )
            ],
        )
        assert len(resp.chapters) == 1
        assert resp.chapters[0].topics[0].topic == "BS"
