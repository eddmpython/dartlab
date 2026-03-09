"""공통 픽스처 — 데이터가 없으면 skip.

데이터 경로는 dartlab 패키지의 config.dataDir 기준.
DARTLAB_DATA_DIR 환경변수 또는 dartlab.dataDir로 변경 가능.
"""

import os

import pytest

from dartlab.core.dataLoader import _dataDir

SAMSUNG = "005930"
HYUNDAI = "005380"


def _has_data(code: str, category: str = "docs") -> bool:
    return (_dataDir(category) / f"{code}.parquet").exists()


requires_samsung = pytest.mark.skipif(
    not _has_data(SAMSUNG, "docs"), reason="삼성전자 docs 데이터 없음"
)
requires_hyundai = pytest.mark.skipif(
    not _has_data(HYUNDAI, "docs"), reason="현대자동차 docs 데이터 없음"
)
requires_finance = pytest.mark.skipif(
    not _has_data(SAMSUNG, "finance"), reason="삼성전자 finance 데이터 없음"
)
requires_report = pytest.mark.skipif(
    not _has_data(SAMSUNG, "report"), reason="삼성전자 report 데이터 없음"
)
