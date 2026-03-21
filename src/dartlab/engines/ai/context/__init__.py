"""AI context package."""

from . import company_adapter as _company_adapter
from . import builder as _builder
from . import snapshot as _snapshot

for _module in (_builder, _snapshot, _company_adapter):
    globals().update(
        {
            name: getattr(_module, name)
            for name in dir(_module)
            if not name.startswith("__")
        }
    )
