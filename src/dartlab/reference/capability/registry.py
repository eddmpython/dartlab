"""AI-usable capability registry.

`core/registry.py`가 데이터 source-of-truth라면, 이 모듈은
AI가 실제로 호출/사용할 수 있는 capability surface의 source-of-truth다.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .execution import ENGINE_QUESTION_CONTRACTS


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

    def toPayload(self) -> dict[str, Any]:
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

    def toPayload(self) -> dict[str, Any]:
        """뷰 레이아웃을 직렬화 가능한 dict로 변환."""
        payload: dict[str, Any] = {
            "layout": self.layout,
            "widgets": [widget.toPayload() for widget in self.widgets],
        }
        if self.title:
            payload["title"] = self.title
        if self.subtitle:
            payload["subtitle"] = self.subtitle
        if self.source:
            payload["source"] = self.source
        return payload

    @classmethod
    def singleWidget(
        cls,
        widget: str,
        props: dict[str, Any] | None = None,
        *,
        key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        layout: str = "stack",
        viewTitle: str | None = None,
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
            title=viewTitle,
            subtitle=subtitle,
            source=source or {},
        )


@dataclass(frozen=True)
class UiAction:
    """Canonical UI action payload."""

    action: str
    payload: dict[str, Any] = field(default_factory=dict)

    def toPayload(self) -> dict[str, Any]:
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
        stockCode: str | None = None,
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
        if stockCode:
            payload["stockCode"] = stockCode
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

        resolved_view = view.toPayload() if isinstance(view, ViewSpec) else view
        if resolved_view is None and component:
            resolved_view = ViewSpec.singleWidget(component, props).toPayload()
        if resolved_view is not None:
            payload["view"] = resolved_view

        return cls(action="render", payload=payload)

    @classmethod
    def renderWidget(
        cls,
        widget: str,
        props: dict[str, Any] | None = None,
        *,
        key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        layout: str = "stack",
        viewTitle: str | None = None,
        subtitle: str | None = None,
        source: dict[str, Any] | None = None,
    ) -> "UiAction":
        """단일 위젯을 ViewSpec으로 감싸 렌더링."""
        return cls.render(
            view=ViewSpec.singleWidget(
                widget,
                props,
                key=key,
                title=title,
                description=description,
                layout=layout,
                viewTitle=viewTitle,
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
    def switchView(cls, view: str) -> "UiAction":
        """chat/viewer 뷰 전환."""
        return cls(action="switch_view", payload={"target": view})

    @classmethod
    def selectCompany(cls, stockCode: str, corpName: str = "", market: str = "") -> "UiAction":
        """종목 선택 + 뷰어 로드."""
        return cls(
            action="select_company",
            payload={"stockCode": stockCode, "corpName": corpName, "market": market},
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
    requiresCompany: bool = False
    resultKind: str = "text"
    stability: str = "experimental"
    aiHint: str = ""
    tags: tuple[str, ...] = ()
    source: str = "tool_runtime"
    # ── 동적 도구 선택용 메타데이터 ──
    questionTypes: tuple[str, ...] = ()
    category: str = "general"
    priority: int = 50
    dependsOn: tuple[str, ...] = ()
    freshness: dict[str, Any] = field(default_factory=dict)
    comparisonCompleteness: dict[str, Any] = field(default_factory=dict)
    requiredEvidence: tuple[str, ...] = ()
    toolArgPolicy: tuple[str, ...] = ()

    def toDict(self, *, detail: bool = False) -> dict[str, Any]:
        """capability 정보를 dict로 변환. detail=True이면 전체 필드 포함."""
        data = asdict(self)
        if detail:
            return data
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "channels": list(self.channels),
            "requiresCompany": self.requiresCompany,
            "resultKind": self.resultKind,
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

    def get(self, capabilityId: str) -> CapabilitySpec | None:
        """id로 CapabilitySpec 조회."""
        return self._items.get(capabilityId)

    def list(self) -> list[CapabilitySpec]:
        """등록된 전체 CapabilitySpec 목록."""
        return list(self._items.values())

    @property
    def size(self) -> int:
        """등록된 capability 수."""
        return len(self._items)


_DEFAULT_REGISTRY = CapabilityRegistry()


def getDefaultCapabilityRegistry() -> CapabilityRegistry:
    """전역 기본 CapabilityRegistry 반환."""
    return _DEFAULT_REGISTRY


def clearCapabilityRegistry() -> None:
    """전역 registry 초기화."""
    _DEFAULT_REGISTRY.clear()


def registerToolCapability(
    capabilityId: str,
    description: str,
    parameters: dict[str, Any],
    *,
    label: str | None = None,
    kind: str = CapabilityKind.WORKFLOW,
    channels: tuple[str, ...] = (CapabilityChannel.CHAT, CapabilityChannel.MCP),
    requiresCompany: bool = False,
    resultKind: str = "text",
    stability: str = "experimental",
    aiHint: str = "",
    tags: tuple[str, ...] = (),
    source: str = "tool_runtime",
    questionTypes: tuple[str, ...] = (),
    category: str = "general",
    priority: int = 50,
    dependsOn: tuple[str, ...] = (),
    freshness: dict[str, Any] | None = None,
    comparisonCompleteness: dict[str, Any] | None = None,
    requiredEvidence: tuple[str, ...] = (),
    toolArgPolicy: tuple[str, ...] = (),
) -> CapabilitySpec:
    """도구 capability를 전역 registry에 등록하고 CapabilitySpec을 반환."""
    spec = CapabilitySpec(
        id=capabilityId,
        label=label or capabilityId,
        description=description,
        input_schema=parameters,
        kind=kind,
        channels=tuple(dict.fromkeys(channels)),
        requiresCompany=requiresCompany,
        resultKind=resultKind,
        stability=stability,
        aiHint=aiHint,
        tags=tags,
        source=source,
        questionTypes=questionTypes,
        category=category,
        priority=priority,
        dependsOn=dependsOn,
        freshness=freshness or {},
        comparisonCompleteness=comparisonCompleteness or {},
        requiredEvidence=requiredEvidence,
        toolArgPolicy=toolArgPolicy,
    )
    _DEFAULT_REGISTRY.register(spec)
    return spec


def getCapabilitySpecs(
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


def buildCapabilitySummary(specs: list[CapabilitySpec] | None = None) -> dict[str, Any]:
    """capability 통계 요약 — total/byKind/byChannel."""
    specs = specs if specs is not None else getCapabilitySpecs()
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


# Analysis Graph contract SSOT.
#
# 이 dict는 런타임 분기용 임시 키워드 뭉치가 아니라, docstring/CAPABILITIES 위에
# 얹히는 최소 기계 검증 계약이다. src/dartlab/reference/capability/builder.py가 이 값을
# CAPABILITIES 및 Analysis Graph로 라이브 컴파일한다.
ANALYSIS_CONTRACTS: dict[str, dict[str, Any]] = {
    "gather.krx": {
        "contractId": "gather.krx.close",
        "capabilityRefs": ["gather.krx"],
        "tool": "gather",
        "questionTypes": ["recent_price_mover"],
        "questionTriggers": {
            "allAny": [
                ["주가", "가격", "종목", "stock", "price"],
                [
                    "오른",
                    "상승",
                    "급등",
                    "수익률",
                    "모멘텀",
                    "랭킹",
                    "순위",
                    "mover",
                    "return",
                    "ranking",
                    "rank",
                    "rose",
                    "risen",
                    "gainer",
                    "gainers",
                    "recently",
                ],
            ]
        },
        "toolMatch": [{"tool": "gather", "args": {"axis": "krx", "targetIn": ["", "close", "raw"]}}],
        "toolNames": ["pythonExec", "gather", "capabilities"],
        "requiredEvidence": ["asOf", "period", "universe", "metric"],
        "evidenceSchema": {
            "targetKeys": ["stockCode", "code"],
            "metricKeys": ["returnPct", "close_return_pct"],
            "periodKeys": ["period", "date"],
            "asOfKeys": ["asOf", "end", "date"],
            "valueKeys": ["returnPct", "value"],
            "unit": "%",
            "basisKeys": ["rank", "corpName", "stockCode"],
        },
        "freshness": {"cadence": "daily", "maxStaleBusinessDays": 10},
        "comparisonCompleteness": {"mode": "full_universe_ranking"},
        "visualPolicy": {"requiredFor": ["recent_price_mover"], "preferredType": "chart"},
        "artifactPolicy": {"primaryCsv": True},
        "toolArgPolicy": ["start_lte_end", "end_not_future", "target_close_for_price_returns"],
        "preflightActions": [
            {"tool": "pythonExec", "argsTemplate": {"kind": "krx_price_mover"}, "primaryEvidence": True}
        ],
        "priority": 100,
    },
    "gather.macro": {
        "contractId": "macro.recent",
        "capabilityRefs": ["gather.macro", "macro"],
        "tool": "gather",
        "questionTypes": ["macro_recent"],
        "questionTriggers": {
            "allAny": [
                ["최근", "현재", "오늘", "어제", "latest", "recent", "지금"],
                ["금리", "환율", "fx", "rate", "macro", "원달러", "usdkrw"],
            ]
        },
        "toolMatch": [{"tool": "gather", "args": {"axis": "macro"}}],
        "toolNames": ["gather", "macro", "capabilities"],
        "requiredEvidence": ["asOf", "metric", "value"],
        "evidenceSchema": {
            "targetKeys": ["target", "metric"],
            "metricKeys": ["metric", "target"],
            "periodKeys": ["date", "period"],
            "asOfKeys": ["date", "asOf"],
            "valueKeys": ["value", "close"],
        },
        "freshness": {"cadence": "daily_or_policy", "maxStaleBusinessDays": 10, "discloseMixedAsOf": True},
        "visualPolicy": {"requiredFor": ["macro_recent"], "preferredType": "chart"},
        "priority": 75,
    },
    "scan.market": {
        "kind": "ai_contract",
        "summary": "시장/업종/스크리닝 질문 scan primary evidence 계약",
        "contractId": "scan.market_screen",
        "capabilityRefs": ["scan"],
        "tool": "scan",
        "questionTypes": ["market_scan"],
        "questionTriggers": {
            "any": [
                "scan",
                "screen",
                "screening",
                "profitable stocks",
                "profitability",
                "스크리닝",
                "종목 발굴",
                "좋은 종목",
                "수익성 좋은",
            ]
        },
        "toolMatch": [{"tool": "scan"}],
        "toolNames": ["scan", "pythonExec", "capabilities"],
        "requiredEvidence": ["target", "metric", "value"],
        "evidenceSchema": {
            "targetKeys": ["종목코드", "stockCode", "code"],
            "metricKeys": ["ROE", "ROA", "영업이익률", "순이익률", "등급", "metric"],
            "valueKeys": ["ROE", "ROA", "영업이익률", "순이익률", "value"],
            "basisKeys": ["종목명", "corpName", "등급"],
        },
        "comparisonCompleteness": {"mode": "full_universe_screening"},
        "visualPolicy": {"requiredFor": ["market_scan"], "preferredType": "chart"},
        "artifactPolicy": {"primaryCsv": True},
        "toolArgPolicy": ["scan_required_for_market_screening", "no_company_pair_preflight_for_industry_scan"],
        "preflightActions": [
            {
                "tool": "scan",
                "argsTemplate": {"axis": "profitability", "sortBy": "ROE", "descending": True, "limit": 20},
                "primaryEvidence": True,
            }
        ],
        "priority": 110,
    },
    "scan.industry": {
        "kind": "ai_contract",
        "summary": "산업 taxonomy universe를 먼저 고정한 뒤 scan으로 같은 축 수익성 evidence를 만든다",
        "contractId": "scan.industry_screen",
        "capabilityRefs": ["industry", "scan"],
        "tool": "scan",
        "questionTypes": ["industry_scan"],
        "questionTriggers": {
            "allAny": [
                ["scan", "screen", "screening", "compare", "comparison", "비교", "스크리닝", "찾아", "좋은", "수익성"],
                ["industry", "sector", "업종", "산업", "반도체", "semiconductor"],
            ]
        },
        "toolMatch": [
            {"tool": "industry"},
            {"tool": "scan"},
            {"tool": "pythonExec", "args": {"kind": "industry_scan"}},
        ],
        "toolNames": ["industry", "scan", "pythonExec", "capabilities"],
        "requiredEvidence": ["industry", "universe", "target", "metric", "value"],
        "evidenceSchema": {
            "targetKeys": ["종목코드", "stockCode", "code"],
            "metricKeys": ["ROE", "ROA", "영업이익률", "순이익률", "공정", "공정명", "등급", "metric"],
            "valueKeys": ["ROE", "ROA", "영업이익률", "순이익률", "신뢰도", "value"],
            "basisKeys": ["종목명", "corpName", "공정명", "역할", "위치", "등급"],
        },
        "comparisonCompleteness": {"mode": "industry_universe_screening"},
        "visualPolicy": {"requiredFor": ["industry_scan"], "preferredType": "chart"},
        "artifactPolicy": {"primaryCsv": True},
        "toolArgPolicy": ["industry_universe_required", "scan_required_for_market_screening"],
        "preflightActions": [
            {
                "tool": "industry",
                "argsTemplate": {"industryId": "{industryId}"},
                "primaryEvidence": True,
            },
            {
                "tool": "scan",
                "argsTemplate": {"axis": "profitability", "sortBy": "ROE", "descending": True, "limit": 50},
                "primaryEvidence": True,
            },
            {
                "tool": "pythonExec",
                "argsTemplate": {"kind": "industry_scan", "industryId": "{industryId}"},
                "primaryEvidence": True,
            },
        ],
        "acceptanceCriteria": {"industryUniverse": True, "primaryCsv": True, "visual": True},
        "priority": 108,
    },
    "Company.analysis": {
        "contractId": "company.analysis",
        "capabilityRefs": ["Company.analysis", "Company.panel"],
        "tool": "analysis",
        "questionTypes": ["company_compare", "cashflow"],
        "toolMatch": [{"tool": "analysis"}],
        "toolNames": ["analysis", "show", "credit", "pastInsight", "capabilities"],
        "requiredEvidence": ["target", "metric", "period", "value"],
        "evidenceSchema": {
            "targetKeys": ["stockCode", "target", "code"],
            "metricKeys": ["metric", "axis", "score", "value"],
            "periodKeys": ["period", "basePeriod", "year"],
            "valueKeys": ["value", "score"],
        },
        "artifactPolicy": {"primaryCsv": True},
        "priority": 90,
    },
    "aiContract.comparison.same_axis": {
        "kind": "ai_contract",
        "summary": "회사 비교 동일 축 evidence 계약",
        "contractId": "comparison.same_axis",
        "capabilityRefs": ["Company.panel", "Company.analysis", "Company.credit", "scan"],
        "questionTypes": ["company_compare"],
        "questionTriggers": {"any": ["비교", "대비", "vs", " versus ", "둘 중", "어느 쪽", "누가"]},
        "toolNames": [
            "searchCompany",
            "analysis",
            "credit",
            "show",
            "pastInsight",
            "scan",
            "gather",
            "macro",
            "industry",
            "pythonExec",
        ],
        "requiredEvidence": ["target", "metric", "period", "value"],
        "evidenceSchema": {
            "targetKeys": ["stockCode", "target", "code"],
            "metricKeys": ["metric", "axis", "score", "value"],
            "periodKeys": ["period", "basePeriod", "year"],
            "valueKeys": ["value", "score"],
        },
        "comparisonCompleteness": {"mode": "same_metric_each_target", "minTargets": 2},
        "visualPolicy": {"requiredFor": ["company_compare"], "preferredType": "chart_or_diagram"},
        "artifactPolicy": {"primaryCsv": True},
        "toolArgPolicy": ["no_missing_side_in_comparison"],
        "toolBudget": {"skipTools": ["quant", "credit"], "maxHeavyCallsPerTargetTool": 1},
        "preflightActions": [
            {"tool": "analysis", "argsTemplate": {"axis": "종합평가"}, "primaryEvidence": True},
            {
                "tool": "show",
                "argsTemplate": {
                    "topic": "IS",
                    "freq": "Y",
                    "scope": "consolidated",
                    "raw": False,
                    "fields": ["매출액", "영업이익"],
                },
                "primaryEvidence": True,
            },
        ],
        "priority": 90,
    },
    "aiContract.disclosure.importance": {
        "kind": "ai_contract",
        "summary": "공시 중요도 분석 근거 깊이 계약",
        "contractId": "disclosure.importance",
        "capabilityRefs": ["Company.filings", "Company.panel", "search"],
        "tool": "disclosure",
        "questionTypes": ["disclosure_importance"],
        "questionTriggers": {
            "any": [
                "공시",
                "filing",
                "dart",
                "보고서",
                "감사의견",
                "핵심감사",
                "감사사항",
                "주석",
                "리스 약정",
                "우발채무",
                "소송 내용",
                "risk factor",
            ]
        },
        "toolMatch": [
            {"tool": "disclosure"},
            {"tool": "filings"},
            {"tool": "liveFilings"},
            {"tool": "search"},
        ],
        "toolNames": ["disclosure", "liveFilings", "filings", "readFiling", "search", "capabilities"],
        "requiredEvidence": ["docRef", "filedAt", "title", "formType", "basis"],
        "evidenceSchema": {
            "targetKeys": ["stockCode", "corpCode"],
            "metricKeys": ["formType", "reportName", "title"],
            "periodKeys": ["filedAt", "date", "rceptDt"],
            "asOfKeys": ["filedAt", "date", "rceptDt"],
            "basisKeys": ["basis", "title", "reportName"],
        },
        "freshness": {"cadence": "filing_date", "disclosureRequired": True},
        "visualPolicy": {"requiredFor": ["disclosure_importance"], "preferredType": "diagram"},
        "artifactPolicy": {"primaryCsv": True},
        "toolArgPolicy": [
            "title_only_scope_must_not_be_presented_as_body_analysis",
            "sections_false",
            "max_chars_4000",
        ],
        "priority": 106,
    },
    "aiContract.cashflow.primary": {
        "kind": "ai_contract",
        "summary": "현금흐름 질문 primary evidence 계약",
        "contractId": "cashflow.primary",
        "capabilityRefs": ["Company.panel", "Company.analysis", "Company.credit"],
        "questionTypes": ["cashflow"],
        "questionTriggers": {"any": ["현금흐름", "cashflow", "cash flow", "fcf", "ocf"]},
        "toolNames": ["analysis", "show", "credit", "capabilities"],
        "requiredEvidence": ["target", "metric", "period", "value"],
        "evidenceSchema": {
            "targetKeys": ["stockCode", "target"],
            "metricKeys": ["OCF", "FCF", "CAPEX", "metric", "axis"],
            "periodKeys": ["period", "year"],
            "valueKeys": ["value", "OCF", "FCF", "CAPEX"],
        },
        "visualPolicy": {"requiredFor": ["cashflow"], "preferredType": "chart"},
        "preflightActions": [
            {"tool": "analysis", "argsTemplate": {"axis": "현금흐름"}, "primaryEvidence": True},
            {
                "tool": "show",
                "argsTemplate": {"topic": "CF", "freq": "Y", "scope": "consolidated", "raw": False},
                "primaryEvidence": True,
            },
        ],
        "priority": 85,
    },
    "aiContract.capabilities.valid_key": {
        "kind": "ai_contract",
        "summary": "capabilities key 오염 방지 계약",
        "contractId": "capabilities.valid_key",
        "capabilityRefs": ["capabilities"],
        "tool": "capabilities",
        "questionTypes": ["meta_help"],
        "questionTriggers": {"any": ["뭐 할 수", "어떻게 써", "사용법", "help", "capabilities"]},
        "toolMatch": [{"tool": "capabilities"}],
        "toolNames": ["capabilities", "Read"],
        "requiredEvidence": ["valid_key_or_search"],
        "toolArgPolicy": ["reject_polluted_capabilities_key"],
        "priority": 70,
    },
    **ENGINE_QUESTION_CONTRACTS,
}


def getAnalysisContractSpecs() -> dict[str, dict[str, Any]]:
    """Analysis Graph 계약 원천을 반환한다."""
    return ANALYSIS_CONTRACTS
