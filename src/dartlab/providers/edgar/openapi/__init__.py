"""EDGAR OpenAPI facade (compat shim).

from dartlab import OpenEdgar

e = OpenEdgar()
aapl = e("AAPL")

aapl.info()
aapl.filings(forms=["10-K", "10-Q"])
aapl.companyFactsJson()
aapl.saveDocs()
aapl.saveFinance()

NOTE: OpenEdgar 파사드는 gather/edgar 로 이관(SEC fetch 전담) — 본 패키지는 lazy
``__getattr__`` re-export shim(providers↛gather module-level 회피). 공개명
``dartlab.OpenEdgar`` 보존.
"""

from __future__ import annotations

from dartlab.core.pluginDiscovery import lazyAttribute

# NOTE: OpenEdgar/OpenEdgarCompany 는 아래 ``__getattr__`` 로 런타임 lazy 재노출
# (``_LAZY`` 문자열 importlib) — providers↛gather 단방향 유지 위해 static import 는 두지 않는다.

__all__ = ["OpenEdgar", "OpenEdgarCompany"]

_LAZY = {
    "OpenEdgar": "dartlab.gather.edgar.edgar",
    "OpenEdgarCompany": "dartlab.gather.edgar.edgar",
}


def __getattr__(name: str):
    """lazy re-export — OpenEdgar 파사드를 접근 시점에만 gather 에서 import."""
    return lazyAttribute(__name__, _LAZY, name)
