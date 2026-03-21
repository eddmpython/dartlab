"""공통 픽스처 — 데이터가 없으면 skip.

데이터 경로는 dartlab 패키지의 config.dataDir 기준.
DARTLAB_DATA_DIR 환경변수 또는 dartlab.dataDir로 변경 가능.

마커 구조:
- requires_samsung, requires_finance 등: 개별 데이터 의존성 (로컬에 없으면 skip)
- requires_data: CI 통합 마커 (pytest -m "not requires_data" 로 데이터 의존 테스트 제외)

skipif 마커가 붙은 테스트에 자동으로 requires_data 마커를 추가한다.
→ CI에서 -m "not requires_data" 한 줄이면 데이터 의존 테스트 전체 제외.
"""

from pathlib import Path

import pytest

from dartlab.core.dataLoader import _dataDir

SAMSUNG = "005930"
HYUNDAI = "005380"
SHINHAN = "055550"
KAKAO = "035720"


def _has_data(code: str, category: str = "docs") -> bool:
    return (_dataDir(category) / f"{code}.parquet").exists()


requires_samsung = pytest.mark.skipif(not _has_data(SAMSUNG, "docs"), reason="삼성전자 docs 데이터 없음")
requires_hyundai = pytest.mark.skipif(not _has_data(HYUNDAI, "docs"), reason="현대자동차 docs 데이터 없음")
requires_finance = pytest.mark.skipif(not _has_data(SAMSUNG, "finance"), reason="삼성전자 finance 데이터 없음")
requires_report = pytest.mark.skipif(not _has_data(SAMSUNG, "report"), reason="삼성전자 report 데이터 없음")
requires_shinhan = pytest.mark.skipif(not _has_data(SHINHAN, "finance"), reason="신한지주 finance 데이터 없음")
requires_kakao = pytest.mark.skipif(not _has_data(KAKAO, "finance"), reason="카카오 finance 데이터 없음")


_DATA_SKIP_REASONS = frozenset(
    {
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
    }
)


def pytest_collection_modifyitems(items):
    """skipif reason이 데이터 관련이면 requires_data 마커 자동 추가."""
    data_mark = pytest.mark.requires_data
    for item in items:
        for marker in item.iter_markers("skipif"):
            reason = marker.kwargs.get("reason", "")
            if reason in _DATA_SKIP_REASONS:
                item.add_marker(data_mark)
                break


@pytest.fixture(autouse=True)
def _isolated_dartlab_home(tmp_path, monkeypatch):
    """shared AI profile/secret store를 테스트별 임시 경로로 격리."""
    home = tmp_path / "dartlab-home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DARTLAB_HOME", str(Path(home)))


# ── Session-scoped Company fixtures: 한 번만 로드하여 재사용 ──


@pytest.fixture(scope="session")
def samsung():
    """삼성전자 Company — 전체 세션에서 한 번만 로드."""
    if not _has_data(SAMSUNG, "docs"):
        pytest.skip("삼성전자 docs 데이터 없음")
    from dartlab import Company

    return Company(SAMSUNG)


@pytest.fixture(scope="session")
def samsung_with_finance():
    """삼성전자 Company (finance 데이터 필수) — 세션에서 한 번만 로드."""
    if not _has_data(SAMSUNG, "docs") or not _has_data(SAMSUNG, "finance"):
        pytest.skip("삼성전자 docs/finance 데이터 없음")
    from dartlab import Company

    return Company(SAMSUNG)
