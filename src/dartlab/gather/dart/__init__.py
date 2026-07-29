"""gather DART 도메인 — viewer 무인증 단건 fetch + OpenDART fetch client·키·콜렉터.

ecos/, fred/ 와 동일 패턴의 외부 데이터 SSOT 서브엔진. providers/dart (build/read)
와 분리 — DART 의 모든 network fetch(client·키·viewer·콜렉터)를 gather 가 전담(ETL Extract).

호출 패턴::

    from dartlab.gather.dart import Dart
    df = Dart().doc("20240315000123")

untrusted 본문:
    viewer 본문은 외부 1차 출처지만 호출자가 외부 untrusted 마커로 감싸는 책임.

NOTE: facade/viewer/types 는 lazy ``__getattr__`` 노출 — client/keys/콜렉터 서브모듈
import 시 무거운 viewer 로딩과 facade/infra 순환 import를 회피. client/keys/
콜렉터(allFilingsCollector/batch 등)는 서브모듈로 직접 import 한다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dartlab.core.pluginDiscovery import lazyAttribute

if TYPE_CHECKING:
    from .facade import Dart
    from .types import DartDocError, DartDocMeta, DocumentNotFoundError, InvalidRceptNoError, ViewerPageParseError
    from .viewer import docMeta, fetch, fetchAsync

__all__ = [
    "Dart",
    "DartDocError",
    "DartDocMeta",
    "DocumentNotFoundError",
    "InvalidRceptNoError",
    "ViewerPageParseError",
    "docMeta",
    "fetch",
    "fetchAsync",
]

_LAZY: dict[str, str] = {
    "Dart": "dartlab.gather.dart.facade",
    "DartDocError": "dartlab.gather.dart.types",
    "DartDocMeta": "dartlab.gather.dart.types",
    "DocumentNotFoundError": "dartlab.gather.dart.types",
    "InvalidRceptNoError": "dartlab.gather.dart.types",
    "ViewerPageParseError": "dartlab.gather.dart.types",
    "docMeta": "dartlab.gather.dart.viewer",
    "fetch": "dartlab.gather.dart.viewer",
    "fetchAsync": "dartlab.gather.dart.viewer",
}


def __getattr__(name: str):
    """lazy re-export — facade/viewer/types 를 접근 시점에만 import (순환·무거운 로딩 회피)."""
    return lazyAttribute(__name__, _LAZY, name)
