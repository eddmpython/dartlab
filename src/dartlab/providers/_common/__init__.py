"""providers/_common. DART, EDGAR, EDINET 공통 helper 파사드.

로직은 형제 모듈이 소유하고 여기는 진입면만 모은다. `httpRetry` 는 원래 이 파일 본문에
있었는데, `__init__` 이 로직을 담으면 import 부작용과 재export 가 한 파일에 섞여 어디를
고쳐야 하는지 흐려진다.

공개 경로는 그대로다. `from dartlab.providers._common import httpRetry`.
"""

from __future__ import annotations

from dartlab.providers._common.httpRetry import httpRetry

__all__ = ["httpRetry"]
