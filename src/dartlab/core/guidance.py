"""호환 shim — 새 코드는 dartlab.guide.messaging을 사용하세요."""

from dartlab.guide.messaging import (  # noqa: F401
    _SIMPLE,
    _STRUCTURED,
    _ctx,
    _StructuredMsg,
    emit,
    format,
    progress,
    suggest,
)
