"""전종목 EDGAR 단일 계정/비율 시계열 배치 추출.

1,272 LoC 단일 모듈이 룰 3 임계(800)를 넘겨 책임별로 갈랐다. 공개 호출 계약
(``scanAccount`` · ``scanAccounts`` · ``scanRatio``)과 모듈 경로는 그대로다.

- ``sql``: DuckDB 실행 튜닝값과 연도 집계 SQL
- ``types``: 오류 계약과 내부 값 타입
- ``taxonomy``: snakeId <-> XBRL concept key 해소, ticker universe 정규화
- ``pipeline``: parquet 스캔 실행과 결과 조립
- ``api``: 공개 호출 계약
"""

from __future__ import annotations

from dartlab.providers.edgar.finance.scanAccount.api import (
    scanAccount,
    scanAccounts,
    scanRatio,
)
from dartlab.providers.edgar.finance.scanAccount.types import (
    EdgarScanError,
    EdgarScanExecutionError,
    EdgarScanMappingError,
    EdgarScanStorageError,
)

__all__ = [
    "EdgarScanError",
    "EdgarScanExecutionError",
    "EdgarScanMappingError",
    "EdgarScanStorageError",
    "scanAccount",
    "scanAccounts",
    "scanRatio",
]
