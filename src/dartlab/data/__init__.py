"""이전 ``dartlab.data`` import를 ``dartlab.dataHub``로 연결하는 호환 계층."""

from __future__ import annotations

import sys
import types
from typing import Any

import dartlab.dataHub as _dataHubModule
from dartlab.dataHub import __all__ as _dataHubExports

for _name in _dataHubExports:
    globals()[_name] = getattr(_dataHubModule, _name)


class _CompatibilityModule(types.ModuleType):
    """호환 module 호출을 canonical DataHub instance로 위임한다."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return _dataHubModule(*args, **kwargs)


sys.modules[__name__].__class__ = _CompatibilityModule

__all__ = list(_dataHubExports)
