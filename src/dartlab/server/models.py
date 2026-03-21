"""Pydantic 모델 — 요청/응답 스키마."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HistoryMeta(BaseModel):
    company: str | None = None
    stockCode: str | None = None
    modules: list[str] | None = None
    market: str | None = None
    topic: str | None = None
    topicLabel: str | None = None
    dialogueMode: str | None = None
    questionTypes: list[str] | None = None
    userGoal: str | None = None


class ViewContextCompany(BaseModel):
    company: str | None = None
    corpName: str | None = None
    stockCode: str | None = None
    market: str | None = None


class ViewContext(BaseModel):
    type: str
    company: ViewContextCompany | None = None
    topic: str | None = None
    topicLabel: str | None = None
    period: str | None = None  # B2: 현재 보고 있는 기간
    data: dict[str, Any] | None = None


class HistoryMessage(BaseModel):
    role: str
    text: str
    meta: HistoryMeta | None = None


class AskRequest(BaseModel):
    company: str | None = Field(None, max_length=100)
    question: str = Field(..., min_length=1, max_length=5000)
    provider: str | None = Field(None, max_length=50)
    role: str | None = Field(None, max_length=50)
    model: str | None = Field(None, max_length=100)
    api_key: str | None = Field(None, max_length=500)
    base_url: str | None = Field(None, max_length=500)
    include: list[str] | None = None
    exclude: list[str] | None = None
    stream: bool = False
    history: list[HistoryMessage] | None = Field(None, max_length=50)
    viewContext: ViewContext | None = None


class ConfigureRequest(BaseModel):
    provider: str = "codex"
    role: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None


class AiProfileUpdateRequest(BaseModel):
    provider: str | None = None
    role: str | None = None
    model: str | None = None
    base_url: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    system_prompt: str | None = None


class AiSecretUpdateRequest(BaseModel):
    provider: str
    api_key: str | None = None
    clear: bool = False


# --- Viewer 응답 스키마 ---


class TocTopic(BaseModel):
    topic: str
    label: str
    textCount: int
    tableCount: int
    hasChanges: bool = False


class TocChapter(BaseModel):
    chapter: str
    topics: list[TocTopic]


class TocResponse(BaseModel):
    stockCode: str
    corpName: str
    chapters: list[TocChapter]
