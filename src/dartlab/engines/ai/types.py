"""LLM 분석기 타입 정의."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Literal

ProviderName = Literal[
    "openai",
    "ollama",
    "custom",
    "codex",
    "oauth-codex",
]


@dataclass
class LLMConfig:
    """LLM 연결 설정."""

    provider: ProviderName = "codex"
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.3
    max_tokens: int = 4096
    system_prompt: str | None = None

    def __post_init__(self):
        import os

        if self.base_url is None:
            env_url = os.environ.get("DARTLAB_LLM_BASE_URL")
            if env_url:
                self.base_url = env_url

    def merge(self, overrides: dict[str, Any]) -> LLMConfig:
        """per-call override 적용한 새 Config 반환."""
        vals = dataclasses.asdict(self)
        vals.update({k: v for k, v in overrides.items() if v is not None})
        return LLMConfig(**vals)


@dataclass
class LLMResponse:
    """LLM 응답 결과."""

    answer: str
    provider: str
    model: str
    context_tables: list[str] = field(default_factory=list)
    usage: dict[str, int] | None = None


@dataclass
class ToolCall:
    """LLM이 요청한 도구 호출."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResponse(LLMResponse):
    """도구 호출을 포함할 수 있는 LLM 응답."""

    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"


# ── 대화 히스토리/뷰어 경량 타입 (server Pydantic 모델 대체) ──


@dataclass(frozen=True)
class HistoryMeta:
    """히스토리 메시지의 메타 정보."""

    company: str | None = None
    stockCode: str | None = None
    modules: list[str] | None = None
    market: str | None = None
    topic: str | None = None
    topicLabel: str | None = None
    dialogueMode: str | None = None
    questionTypes: list[str] | None = None
    userGoal: str | None = None


@dataclass(frozen=True)
class HistoryItem:
    """대화 히스토리 한 턴."""

    role: str
    text: str
    meta: HistoryMeta | None = None


@dataclass(frozen=True)
class ViewContextCompany:
    """뷰어 컨텍스트의 회사 정보."""

    company: str | None = None
    corpName: str | None = None
    stockCode: str | None = None
    market: str | None = None


@dataclass(frozen=True)
class ViewContextInfo:
    """뷰어 컨텍스트 — 현재 사용자가 보고 있는 화면."""

    type: str
    company: ViewContextCompany | None = None
    topic: str | None = None
    topicLabel: str | None = None
    period: str | None = None
    data: dict[str, Any] | None = None


def history_from_dicts(items: list[dict] | None) -> list[HistoryItem] | None:
    """dict 리스트 → HistoryItem 리스트 변환.

    server Pydantic 모델이나 raw dict 모두 지원.
    """
    if not items:
        return None
    result: list[HistoryItem] = []
    for item in items:
        if hasattr(item, "model_dump"):
            item = item.model_dump()

        meta_raw = item.get("meta")
        meta = None
        if meta_raw:
            if hasattr(meta_raw, "model_dump"):
                meta_raw = meta_raw.model_dump()
            if isinstance(meta_raw, dict):
                meta = HistoryMeta(**{k: v for k, v in meta_raw.items() if k in HistoryMeta.__dataclass_fields__})
            elif isinstance(meta_raw, HistoryMeta):
                meta = meta_raw

        result.append(
            HistoryItem(
                role=item.get("role", "user"),
                text=item.get("text", ""),
                meta=meta,
            )
        )
    return result


def view_context_from_dict(data: Any | None) -> ViewContextInfo | None:
    """dict → ViewContextInfo 변환.

    server Pydantic ViewContext나 raw dict 모두 지원.
    """
    if not data:
        return None
    if hasattr(data, "model_dump"):
        data = data.model_dump()

    company_raw = data.get("company")
    company = None
    if company_raw:
        if hasattr(company_raw, "model_dump"):
            company_raw = company_raw.model_dump()
        if isinstance(company_raw, dict):
            company = ViewContextCompany(
                **{k: v for k, v in company_raw.items() if k in ViewContextCompany.__dataclass_fields__}
            )
        elif isinstance(company_raw, ViewContextCompany):
            company = company_raw

    return ViewContextInfo(
        type=data.get("type", "viewer"),
        company=company,
        topic=data.get("topic"),
        topicLabel=data.get("topicLabel"),
        period=data.get("period"),
        data=data.get("data"),
    )
