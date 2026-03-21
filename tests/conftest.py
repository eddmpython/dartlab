"""공통 픽스처 — 데이터가 없으면 skip.

데이터 경로는 dartlab 패키지의 config.dataDir 기준.
DARTLAB_DATA_DIR 환경변수 또는 dartlab.dataDir로 변경 가능.

마커 구조:
- requires_samsung, requires_finance 등: 개별 데이터 의존성 (로컬에 없으면 skip)
- requires_data: CI 통합 마커 (pytest -m "not requires_data" 로 데이터 의존 테스트 제외)
- unit: 순수 로직/mock만 — 데이터 로드 없음, 병렬 안전
- heavy: 대량 데이터 로드 — 단독 실행 필수

테스트 실행 가이드:
  pytest -m "unit" -v              # 가벼운 테스트만 (안전, 빠름)
  pytest -m "not unit and not heavy" -v  # 중간 테스트
  pytest -m "heavy" -v             # 무거운 테스트 (단독)
  ⚠ pytest tests/ -v 전체 한번에 돌리면 메모리 크래시 위험
  ⚠ Polars 네이티브 Rust 메모리는 gc.collect()로 회수 불가 — fixture 해제가 유일한 방법

메모리 안전 정책:
  - Company fixture는 module scope (session scope 금지)
  - 각 모듈 테스트 완료 후 GC 강제 실행
  - 1200MB 초과 시 pytest.exit()으로 안전 종료
"""

import gc
from pathlib import Path

import pytest

from dartlab.core.dataLoader import _dataDir
from dartlab.core.memory import PRESSURE_CRITICAL_MB, get_memory_mb

SAMSUNG = "005930"
HYUNDAI = "005380"
SHINHAN = "055550"
KAKAO = "035720"

# ── 메모리 안전 한계 (MB) ──
# 이 값을 넘으면 pytest 자체를 안전 종료하여 OOM 방지
_PYTEST_MEMORY_LIMIT_MB = PRESSURE_CRITICAL_MB


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


@pytest.fixture(autouse=True)
def _memory_guard_per_test():
    """매 테스트 후 메모리 체크 + GC.

    PRESSURE_CRITICAL_MB 초과 시 pytest를 안전 종료하여 OOM/시스템 크래시 방지.
    Polars 네이티브 메모리는 gc.collect()로 회수 불가하므로,
    이 시점에서 잡히면 이미 위험한 상태 → 즉시 종료가 유일한 안전책.
    """
    yield
    gc.collect()
    mem = get_memory_mb()
    if mem > _PYTEST_MEMORY_LIMIT_MB:
        pytest.exit(
            f"⚠ 메모리 안전 종료: {mem:.0f}MB > {_PYTEST_MEMORY_LIMIT_MB:.0f}MB 한계 초과.\n"
            f"  Polars 네이티브 메모리는 GC로 회수 불가합니다.\n"
            f"  테스트를 그룹별로 분리해서 실행하세요:\n"
            f"    pytest -m unit -v\n"
            f"    pytest -m 'not unit and not heavy' -v\n"
            f"    pytest -m heavy -v",
            returncode=99,
        )


# ── Module-scoped Company fixtures: 모듈 단위로 로드/해제 ──
# ⚠ session scope는 메모리 크래시 원인이므로 사용 금지 (2026-03-21)


@pytest.fixture(scope="module")
def samsung():
    """삼성전자 Company — 모듈 단위로 로드/해제."""
    if not _has_data(SAMSUNG, "docs"):
        pytest.skip("삼성전자 docs 데이터 없음")
    from dartlab import Company

    c = Company(SAMSUNG)
    yield c
    del c
    gc.collect()


@pytest.fixture(scope="module")
def samsung_with_finance():
    """삼성전자 Company (finance 데이터 필수) — 모듈 단위로 로드/해제."""
    if not _has_data(SAMSUNG, "docs") or not _has_data(SAMSUNG, "finance"):
        pytest.skip("삼성전자 docs/finance 데이터 없음")
    from dartlab import Company

    c = Company(SAMSUNG)
    yield c
    del c
    gc.collect()
