"""Pydantic 모델 — 요청/응답 스키마."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HistoryMeta(BaseModel):
    """AI 대화 이력의 메타데이터."""

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
    """뷰 컨텍스트 내 회사 정보."""

    company: str | None = None
    corpName: str | None = None
    stockCode: str | None = None
    market: str | None = None


class ViewContext(BaseModel):
    """현재 SPA 화면 상태를 서버에 전달하는 컨텍스트."""

    type: str
    company: ViewContextCompany | None = None
    topic: str | None = None
    topicLabel: str | None = None
    period: str | None = None  # B2: 현재 보고 있는 기간
    data: dict[str, Any] | None = None


class HistoryMessage(BaseModel):
    """AI 대화 이력의 단일 메시지."""

    role: str
    text: str
    meta: HistoryMeta | None = None


class AskRequest(BaseModel):
    """AI 질문 요청 스키마."""

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
    reportMode: bool = False
    history: list[HistoryMessage] | None = Field(None, max_length=50)
    viewContext: ViewContext | None = None


class ConfigureRequest(BaseModel):
    """LLM provider 설정/검증 요청."""

    provider: str = "codex"
    role: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None


class AiProfileUpdateRequest(BaseModel):
    """AI 프로필 갱신 요청."""

    provider: str | None = None
    role: str | None = None
    model: str | None = None
    base_url: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    system_prompt: str | None = None


class AiSecretUpdateRequest(BaseModel):
    """Provider API 키 저장/삭제 요청."""

    provider: str
    api_key: str | None = None
    clear: bool = False


class DartKeyUpdateRequest(BaseModel):
    """OpenDART API 키 저장/삭제 요청."""

    api_key: str | None = Field(None, max_length=500)


class ChannelConnectRequest(BaseModel):
    """외부 채널(Telegram/Slack/Discord) 연결 요청."""

    token: str | None = Field(None, max_length=500)
    botToken: str | None = Field(None, max_length=500)
    appToken: str | None = Field(None, max_length=500)


# --- Viewer 응답 스키마 ---


class TocTopic(BaseModel):
    """뷰어 목차의 개별 topic 항목."""

    topic: str
    label: str
    textCount: int
    tableCount: int
    hasChanges: bool = False


class TocChapter(BaseModel):
    """뷰어 목차의 장(chapter) 그룹."""

    chapter: str
    topics: list[TocTopic]


class TocResponse(BaseModel):
    """뷰어 목차 전체 응답."""

    stockCode: str
    corpName: str
    chapters: list[TocChapter]


# --- Room 협업 세션 ---


class RoomJoinRequest(BaseModel):
    """협업 룸 참여 요청."""

    name: str = Field(..., min_length=1, max_length=30)


class RoomJoinResponse(BaseModel):
    """협업 룸 참여 응답 -- 멤버 ID와 현재 상태 포함."""

    memberId: str
    roomId: str
    members: list[dict]
    navState: dict
    chatHistory: list[dict]


class RoomAskRequest(BaseModel):
    """협업 룸 AI 질문 요청."""

    question: str = Field(..., min_length=1, max_length=5000)
    company: str | None = Field(None, max_length=100)


class RoomNavigateRequest(BaseModel):
    """협업 룸 화면 이동 요청."""

    stockCode: str | None = None
    topic: str | None = None
    period: str | None = None


class RoomChatRequest(BaseModel):
    """협업 룸 채팅 메시지 전송 요청."""

    text: str = Field(..., min_length=1, max_length=500)


class RoomReactRequest(BaseModel):
    """협업 룸 리액션 전송 요청."""

    emoji: str = Field(..., max_length=4)
    targetEvent: str | None = None
