"""Pydantic 모델 — 요청/응답 스키마."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


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
    data: dict[str, Any] | None = None


class HistoryMessage(BaseModel):
    role: str
    text: str
    meta: HistoryMeta | None = None


class AskRequest(BaseModel):
    company: str | None = None
    question: str
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    include: list[str] | None = None
    exclude: list[str] | None = None
    stream: bool = False
    history: list[HistoryMessage] | None = None
    viewContext: ViewContext | None = None


class ConfigureRequest(BaseModel):
    provider: str = "codex"
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
