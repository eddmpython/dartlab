"""AI-usable capability registry.

`core/registry.py`가 데이터 source-of-truth라면, 이 모듈은
AI가 실제로 호출/사용할 수 있는 capability surface의 source-of-truth다.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


class CapabilityKind:
    """AI capability 종류 상수."""

    DATA = "data"
    ANALYSIS = "analysis"
    WORKFLOW = "workflow"
    UI_ACTION = "ui_action"
    CODING = "coding"
    SYSTEM = "system"


class CapabilityChannel:
    """capability 노출 채널 상수."""

    CHAT = "chat"
    MCP = "mcp"
    CLI = "cli"
    UI = "ui"


@dataclass(frozen=True)
class WidgetSpec:
    """Single registered widget in an AI-rendered view."""

    widget: str
    props: dict[str, Any] = field(default_factory=dict)
    key: str | None = None
    title: str | None = None
    description: str | None = None

    def to_payload(self) -> dict[str, Any]:
        """widget 정보를 직렬화 가능한 dict로 변환."""
        payload = {
            "widget": self.widget,
            "props": self.props,
        }
        if self.key:
            payload["key"] = self.key
        if self.title:
            payload["title"] = self.title
        if self.description:
            payload["description"] = self.description
        return payload


@dataclass(frozen=True)
class ViewSpec:
    """canonical UI 레이아웃 스키마 — 렌더러/싱크가 소비."""

    layout: str = "stack"
    widgets: list[WidgetSpec] = field(default_factory=list)
    title: str | None = None
    subtitle: str | None = None
    source: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        """뷰 레이아웃을 직렬화 가능한 dict로 변환."""
        payload: dict[str, Any] = {
            "layout": self.layout,
            "widgets": [widget.to_payload() for widget in self.widgets],
        }
        if self.title:
            payload["title"] = self.title
        if self.subtitle:
            payload["subtitle"] = self.subtitle
        if self.source:
            payload["source"] = self.source
        return payload

    @classmethod
    def single_widget(
        cls,
        widget: str,
        props: dict[str, Any] | None = None,
        *,
        key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        layout: str = "stack",
        view_title: str | None = None,
        subtitle: str | None = None,
        source: dict[str, Any] | None = None,
    ) -> "ViewSpec":
        """위젯 하나로 구성된 ViewSpec 생성."""
        return cls(
            layout=layout,
            widgets=[
                WidgetSpec(
                    widget=widget,
                    props=props or {},
                    key=key,
                    title=title,
                    description=description,
                )
            ],
            title=view_title,
            subtitle=subtitle,
            source=source or {},
        )


@dataclass(frozen=True)
class UiAction:
    """Canonical UI action payload."""

    action: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        """액션을 직렬화 가능한 dict로 변환."""
        return {"action": self.action, **self.payload}

    @classmethod
    def navigate(
        cls,
        *,
        view: str = "viewer",
        topic: str | None = None,
        period: str | None = None,
        chapter: int | None = None,
        stock_code: str | None = None,
        company: str | None = None,
    ) -> "UiAction":
        """뷰어/topic/기간으로 화면 이동."""
        payload: dict[str, Any] = {"view": view}
        if topic:
            payload["topic"] = topic
        if period:
            payload["period"] = period
        if chapter is not None:
            payload["chapter"] = chapter
        if stock_code:
            payload["stockCode"] = stock_code
        if company:
            payload["company"] = company
        return cls(action="navigate", payload=payload)

    @classmethod
    def render(
        cls,
        component: str | None = None,
        props: dict[str, Any] | None = None,
        *,
        view: ViewSpec | dict[str, Any] | None = None,
    ) -> "UiAction":
        """컴포넌트 또는 ViewSpec을 렌더링."""
        payload: dict[str, Any] = {}
        if component:
            payload["component"] = component
            payload["props"] = props or {}

        resolved_view = view.to_payload() if isinstance(view, ViewSpec) else view
        if resolved_view is None and component:
            resolved_view = ViewSpec.single_widget(component, props).to_payload()
        if resolved_view is not None:
            payload["view"] = resolved_view

        return cls(action="render", payload=payload)

    @classmethod
    def render_widget(
        cls,
        widget: str,
        props: dict[str, Any] | None = None,
        *,
        key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        layout: str = "stack",
        view_title: str | None = None,
        subtitle: str | None = None,
        source: dict[str, Any] | None = None,
    ) -> "UiAction":
        """단일 위젯을 ViewSpec으로 감싸 렌더링."""
        return cls.render(
            view=ViewSpec.single_widget(
                widget,
                props,
                key=key,
                title=title,
                description=description,
                layout=layout,
                view_title=view_title,
                subtitle=subtitle,
                source=source,
            )
        )

    @classmethod
    def update(cls, target: str, payload: dict[str, Any] | None = None) -> "UiAction":
        """대상 컴포넌트 상태 업데이트."""
        data = {"target": target}
        if payload:
            data.update(payload)
        return cls(action="update", payload=data)

    @classmethod
    def toast(cls, message: str, *, level: str = "info") -> "UiAction":
        """토스트 알림 표시."""
        return cls(action="toast", payload={"message": message, "level": level})

    @classmethod
    def layout(cls, target: str, value: str = "toggle") -> "UiAction":
        """사이드바/풀스크린 등 레이아웃 제어. target: sidebar|fullscreen, value: open|close|toggle"""
        return cls(action="layout", payload={"target": target, "value": value})

    @classmethod
    def switch_view(cls, view: str) -> "UiAction":
        """chat/viewer 뷰 전환."""
        return cls(action="switch_view", payload={"target": view})

    @classmethod
    def select_company(cls, stock_code: str, corp_name: str = "", market: str = "") -> "UiAction":
        """종목 선택 + 뷰어 로드."""
        return cls(
            action="select_company",
            payload={"stockCode": stock_code, "corpName": corp_name, "market": market},
        )


@dataclass(frozen=True)
class CapabilitySpec:
    """Single AI-usable capability definition."""

    id: str
    label: str
    description: str
    input_schema: dict[str, Any]
    kind: str = CapabilityKind.WORKFLOW
    channels: tuple[str, ...] = (CapabilityChannel.CHAT, CapabilityChannel.MCP)
    requires_company: bool = False
    result_kind: str = "text"
    stability: str = "experimental"
    ai_hint: str = ""
    tags: tuple[str, ...] = ()
    source: str = "tool_runtime"
    # ── 동적 도구 선택용 메타데이터 ──
    questionTypes: tuple[str, ...] = ()
    category: str = "general"
    priority: int = 50
    dependsOn: tuple[str, ...] = ()

    def to_dict(self, *, detail: bool = False) -> dict[str, Any]:
        """capability 정보를 dict로 변환. detail=True이면 전체 필드 포함."""
        data = asdict(self)
        if detail:
            return data
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "channels": list(self.channels),
            "requiresCompany": self.requires_company,
            "resultKind": self.result_kind,
            "stability": self.stability,
        }


class CapabilityRegistry:
    """AI capability 등록소 — id 기반 CapabilitySpec 저장/조회."""

    def __init__(self) -> None:
        self._items: dict[str, CapabilitySpec] = {}

    def register(self, spec: CapabilitySpec) -> None:
        """capability 등록. 동일 id는 덮어쓴다."""
        self._items[spec.id] = spec

    def clear(self) -> None:
        """등록된 모든 capability 제거."""
        self._items.clear()

    def get(self, capability_id: str) -> CapabilitySpec | None:
        """id로 CapabilitySpec 조회."""
        return self._items.get(capability_id)

    def list(self) -> list[CapabilitySpec]:
        """등록된 전체 CapabilitySpec 목록."""
        return list(self._items.values())

    @property
    def size(self) -> int:
        """등록된 capability 수."""
        return len(self._items)


_DEFAULT_REGISTRY = CapabilityRegistry()


def get_default_capability_registry() -> CapabilityRegistry:
    """전역 기본 CapabilityRegistry 반환."""
    return _DEFAULT_REGISTRY


def clear_capability_registry() -> None:
    """전역 registry 초기화."""
    _DEFAULT_REGISTRY.clear()


def register_tool_capability(
    capability_id: str,
    description: str,
    parameters: dict[str, Any],
    *,
    label: str | None = None,
    kind: str = CapabilityKind.WORKFLOW,
    channels: tuple[str, ...] = (CapabilityChannel.CHAT, CapabilityChannel.MCP),
    requires_company: bool = False,
    result_kind: str = "text",
    stability: str = "experimental",
    ai_hint: str = "",
    tags: tuple[str, ...] = (),
    source: str = "tool_runtime",
    questionTypes: tuple[str, ...] = (),
    category: str = "general",
    priority: int = 50,
    dependsOn: tuple[str, ...] = (),
) -> CapabilitySpec:
    """도구 capability를 전역 registry에 등록하고 CapabilitySpec을 반환."""
    spec = CapabilitySpec(
        id=capability_id,
        label=label or capability_id,
        description=description,
        input_schema=parameters,
        kind=kind,
        channels=tuple(dict.fromkeys(channels)),
        requires_company=requires_company,
        result_kind=result_kind,
        stability=stability,
        ai_hint=ai_hint,
        tags=tags,
        source=source,
        questionTypes=questionTypes,
        category=category,
        priority=priority,
        dependsOn=dependsOn,
    )
    _DEFAULT_REGISTRY.register(spec)
    return spec


def get_capability_specs(
    *,
    channel: str | None = None,
    kind: str | None = None,
    category: str | None = None,
) -> list[CapabilitySpec]:
    """채널/종류/카테고리로 필터링한 capability 목록."""
    specs = _DEFAULT_REGISTRY.list()
    if channel is not None:
        specs = [spec for spec in specs if channel in spec.channels]
    if kind is not None:
        specs = [spec for spec in specs if spec.kind == kind]
    if category is not None:
        specs = [spec for spec in specs if spec.category == category]
    return specs


def build_capability_summary(specs: list[CapabilitySpec] | None = None) -> dict[str, Any]:
    """capability 통계 요약 — total/byKind/byChannel."""
    specs = specs if specs is not None else get_capability_specs()
    by_kind: dict[str, int] = {}
    by_channel: dict[str, int] = {}
    for spec in specs:
        by_kind[spec.kind] = by_kind.get(spec.kind, 0) + 1
        for channel in spec.channels:
            by_channel[channel] = by_channel.get(channel, 0) + 1
    return {
        "total": len(specs),
        "byKind": by_kind,
        "byChannel": by_channel,
    }
