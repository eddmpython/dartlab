"""Pydantic 모델 — 요청/응답 스키마."""

from __future__ import annotations

from pydantic import BaseModel


class HistoryMeta(BaseModel):
	company: str | None = None
	stockCode: str | None = None
	modules: list[str] | None = None


class HistoryMessage(BaseModel):
	role: str
	text: str
	meta: HistoryMeta | None = None


class AskRequest(BaseModel):
	company: str | None = None
	question: str
	provider: str | None = None
	model: str | None = None
	include: list[str] | None = None
	exclude: list[str] | None = None
	stream: bool = False
	history: list[HistoryMessage] | None = None


class ConfigureRequest(BaseModel):
	provider: str = "codex"
	model: str | None = None
	api_key: str | None = None
	base_url: str | None = None
