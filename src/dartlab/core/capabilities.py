"""호환 shim — 새 코드는 dartlab.guide.capabilities를 사용하세요."""

from dartlab.guide.capabilities import *  # noqa: F401,F403
from dartlab.guide.capabilities import (  # noqa: F401
    _DEFAULT_REGISTRY,
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
