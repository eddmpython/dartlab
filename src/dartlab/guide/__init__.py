"""dartlab 안내 데스크 — 시스템 총괄 관리 엔진.

레이어 외부 교차 관심사 패키지. 모든 레이어(L0~L3)가 import 가능.

사용법::

    import dartlab

    # 서브패키지로 직접 접근
    dartlab.guide.checkReady("finance", stockCode="005930")
    dartlab.guide.whatCanIDo("재무 분석")
    dartlab.guide.envSnapshot()
    dartlab.guide.forAi("삼성전자 분석해줘")

    # 또는 싱글턴 import
    from dartlab.guide import guide
    guide.checkReady("ai")
"""

from dartlab.guide.desk import GuideDesk, getDesk
from dartlab.guide.readiness import (
    ReadinessIssue,
    ReadinessResult,
    ReadyStatus,
    registerChecker,
)
from dartlab.guide.credentials import CredentialManager, CredentialStatus, EnvironmentSnapshot
from dartlab.guide import hints
from dartlab.guide.capabilities import (
    CapabilityChannel,
    CapabilityKind,
    CapabilityRegistry,
    CapabilitySpec,
    UiAction,
    ViewSpec,
    WidgetSpec,
    build_capability_summary,
    clear_capability_registry,
    get_capability_specs,
    get_default_capability_registry,
    register_tool_capability,
)

# 편의 싱글턴
guide = getDesk()

# ── 모듈 레벨 편의 함수 — dartlab.guide.checkReady() 직접 호출 가능 ──


def checkReady(feature: str, **kwargs):
    """guide.checkReady() 바로가기."""
    return guide.checkReady(feature, **kwargs)


def checkReadyAll(features: list[str], **kwargs):
    """guide.checkReadyAll() 바로가기."""
    return guide.checkReadyAll(features, **kwargs)


def require(feature: str, **kwargs):
    """guide.require() 바로가기."""
    return guide.require(feature, **kwargs)


def whatCanIDo(question: str = "", *, topK: int = 10) -> str:
    """guide.whatCanIDo() 바로가기."""
    return guide.whatCanIDo(question, topK=topK)


def envSnapshot() -> EnvironmentSnapshot:
    """guide.envSnapshot() 바로가기."""
    return guide.envSnapshot()


def forAi(question: str) -> dict:
    """guide.forAi() 바로가기."""
    return guide.forAi(question)


def handleError(error: Exception, *, feature: str | None = None) -> str:
    """guide.handleError() 바로가기."""
    return guide.handleError(error, feature=feature)


def describe(funcName: str) -> str | None:
    """guide.describe() 바로가기."""
    return guide.describe(funcName)


def listFeatures() -> list[str]:
    """guide.listFeatures() 바로가기."""
    return guide.listFeatures()


__all__ = [
    "CapabilityChannel",
    "CapabilityKind",
    "CapabilityRegistry",
    "CapabilitySpec",
    "CredentialManager",
    "CredentialStatus",
    "EnvironmentSnapshot",
    "GuideDesk",
    "ReadinessIssue",
    "ReadinessResult",
    "ReadyStatus",
    "UiAction",
    "ViewSpec",
    "WidgetSpec",
    "build_capability_summary",
    "checkReady",
    "checkReadyAll",
    "clear_capability_registry",
    "describe",
    "envSnapshot",
    "forAi",
    "get_capability_specs",
    "get_default_capability_registry",
    "getDesk",
    "guide",
    "handleError",
    "listFeatures",
    "registerChecker",
    "register_tool_capability",
    "require",
    "whatCanIDo",
]
