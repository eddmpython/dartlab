"""DART OpenAPI 클라이언트.

from dartlab import OpenDart

d = OpenDart()
s = d("삼성전자")

s.finance(2020)                         # 2020~현재 Q1~Q4
s.report("배당", 2020)                  # 배당 2020~현재
s.filings("2024")                       # 공시
s.info()                                # 개황
s.shares()                              # 지분공시
s.saveFinance("재무.csv", 2020, kr=True) # 한글 컬럼 저장
호환 alias:
    from dartlab import Dart

NOTE: Dart/OpenDart 파사드·korColumns 는 lazy ``__getattr__`` 노출 —
build(``build.saver``→``core.dartConstants``) ↔ facade 순환 import 회피. DartClient·키·
DartApiError 는 gather fetch 전담(core.dartClient seam). zip 병렬 fetch 는 gather.dart.document.
"""

from __future__ import annotations

# core 재노출(경량) — gather 가 fetch 전담, providers 소비자 호환용 seam.
from dartlab.core.dartClient import DartApiError, DartClient
from dartlab.core.pluginDiscovery import lazyAttribute

# NOTE: Dart/OpenDart/korColumns 는 아래 ``__getattr__`` 로 런타임 lazy 재노출
# (``_LAZY`` 문자열 importlib) — providers↛gather 단방향 유지 위해 static import 는 두지 않는다.

__all__ = [
    "OpenDart",
    "OpenDartCompany",
    "Dart",
    "DartCompany",
    "DartClient",
    "DartApiError",
    "korColumns",
]

_LAZY: dict[str, str] = {
    "OpenDart": "dartlab.gather.dart.dart",
    "OpenDartCompany": "dartlab.gather.dart.dart",
    "Dart": "dartlab.gather.dart.dart",
    "DartCompany": "dartlab.gather.dart.dart",
    "korColumns": "dartlab.providers.dart.build.saver",
}


def __getattr__(name: str):
    """lazy re-export — facade/collector/korColumns 를 접근 시점에만 import (순환 회피)."""
    return lazyAttribute(__name__, _LAZY, name)
