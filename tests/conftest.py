"""공통 픽스처 — 데이터가 없으면 skip.

데이터 경로는 dartlab 패키지의 config.dataDir 기준.
DARTLAB_DATA_DIR 환경변수 또는 dartlab.dataDir로 변경 가능.

마커 구조:
- requires_samsung, requires_finance 등: 개별 데이터 의존성 (로컬에 없으면 skip)
- requires_data: CI 통합 마커 (pytest -m "not requires_data" 로 데이터 의존 테스트 제외)

skipif 마커가 붙은 테스트에 자동으로 requires_data 마커를 추가한다.
→ CI에서 -m "not requires_data" 한 줄이면 데이터 의존 테스트 전체 제외.
"""

import pytest

from dartlab.core.dataLoader import _dataDir

SAMSUNG = "005930"
HYUNDAI = "005380"
SHINHAN = "055550"
KAKAO = "035720"


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
requires_shinhan = pytest.mark.skipif(
    not _has_data(SHINHAN, "finance"), reason="신한지주 finance 데이터 없음"
)
requires_kakao = pytest.mark.skipif(
    not _has_data(KAKAO, "finance"), reason="카카오 finance 데이터 없음"
)


_DATA_SKIP_REASONS = frozenset({
    "삼성전자 docs 데이터 없음",
    "현대자동차 docs 데이터 없음",
    "삼성전자 finance 데이터 없음",
    "삼성전자 report 데이터 없음",
    "신한지주 finance 데이터 없음",
    "카카오 finance 데이터 없음",
    "EDGAR parquet 데이터 없음",
    "EDGAR tickers.parquet 없음",
    "삼성전자 데이터 없음",
    "벤치마크 종목 finance 데이터 없음",
    "BS 항등식 검증 종목 finance 데이터 없음",
})


def pytest_collection_modifyitems(items):
    """skipif reason이 데이터 관련이면 requires_data 마커 자동 추가."""
    data_mark = pytest.mark.requires_data
    for item in items:
        for marker in item.iter_markers("skipif"):
            reason = marker.kwargs.get("reason", "")
            if reason in _DATA_SKIP_REASONS:
                item.add_marker(data_mark)
                break
