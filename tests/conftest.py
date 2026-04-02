"""공통 픽스처 — 데이터가 없으면 skip.

데이터 경로는 dartlab 패키지의 config.dataDir 기준.
DARTLAB_DATA_DIR 환경변수 또는 dartlab.dataDir로 변경 가능.

마커 구조 (3-tier):
- unit: 순수 로직/mock만 — 데이터 로드 없음, 병렬 안전
- integration: Company 1개 로딩 필요 — 중간 무게
- heavy: 대량 데이터 로드 — 단독 실행 필수
- requires_data: CI 통합 마커 (pytest -m "not requires_data" 로 데이터 의존 테스트 제외)
- requires_samsung, requires_finance 등: 개별 데이터 의존성 (로컬에 없으면 skip)

테스트 실행 가이드 (반드시 test-lock.sh 경유):
  bash scripts/test-lock.sh tests/ -m "unit" -v --tb=short             # 1단계: unit (안전, 빠름)
  bash scripts/test-lock.sh tests/ -m "integration" -v --tb=short      # 2단계: integration (Company 로딩)
  bash scripts/test-lock.sh tests/ -m "heavy" -v --tb=short            # 3단계: heavy (단독)
  ⚠ pytest tests/ -v 전체 한번에 돌리면 메모리 크래시 위험
  ⚠ Polars 네이티브 Rust 메모리는 gc.collect()로 회수 불가 — fixture 해제가 유일한 방법

메모리 안전 정책:
  - Company fixture는 module scope (session scope 금지)
  - 각 모듈 테스트 완료 후 GC 강제 실행
  - 1200MB 초과 시 pytest.exit()으로 안전 종료
"""

import gc
import os
from pathlib import Path

import pytest

from dartlab.core.dataLoader import _dataDir
from dartlab.core.memory import PRESSURE_CRITICAL_MB, get_memory_mb


def pytest_configure(config):
    """테스트 시작 전 안전 검사."""
    # test-lock.sh 없이 직접 pytest를 호출한 경우 경고
    if not os.environ.get("DARTLAB_TEST_LOCKED"):
        import warnings

        warnings.warn(
            "⚠ test-lock.sh 없이 pytest 직접 실행 — "
            "다른 세션과 동시 실행 시 OOM 위험.\n"
            "  권장: bash scripts/test-lock.sh tests/ -m unit -v",
            stacklevel=1,
        )


SAMSUNG = "005930"
HYUNDAI = "005380"
SHINHAN = "055550"
KAKAO = "035720"
AAPL = "AAPL"

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
requires_edgar = pytest.mark.skipif(not _has_data(AAPL, "edgar"), reason="EDGAR finance 데이터 없음")


_DATA_SKIP_REASONS = frozenset(
    {
        "삼성전자 docs 데이터 없음",
        "현대자동차 docs 데이터 없음",
        "삼성전자 finance 데이터 없음",
        "삼성전자 report 데이터 없음",
        "신한지주 finance 데이터 없음",
        "카카오 finance 데이터 없음",
        "EDGAR finance 데이터 없음",
        "EDGAR parquet 데이터 없음",
        "EDGAR tickers.parquet 없음",
        "삼성전자 데이터 없음",
        "벤치마크 종목 finance 데이터 없음",
        "BS 항등식 검증 종목 finance 데이터 없음",
        "벤치마크 종목 finance fixture 없음",
        "BS 항등식 검증 종목 fixture 없음",
        "삼성전자 finance fixture 없음",
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
def _clear_sections_prepared_cache():
    """sections pipeline Phase 1 캐시를 테스트마다 초기화."""
    yield
    try:
        from dartlab.providers.dart.docs.sections.pipeline import clearPreparedCache

        clearPreparedCache()
    except ImportError:
        pass


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


# ══════════════════════════════════════════════════════════════
# MockCompany — 데이터 없이 unit 테스트 가능한 가짜 Company
# ══════════════════════════════════════════════════════════════


def _make_synthetic_df(
    stmt: str,
    accounts: list[str],
    periods: list[str] | None = None,
    *,
    base_value: float = 1_000_000,
) -> "pl.DataFrame":
    """합성 재무 DataFrame 생성. period 컬럼은 실제 형식."""
    import polars as _pl

    if periods is None:
        periods = ["2024Q4", "2023Q4", "2022Q4", "2021Q4", "2020Q4"]

    rows: list[dict] = []
    for i, acct in enumerate(accounts):
        row: dict = {"계정명": acct}
        for j, p in enumerate(periods):
            # 각 계정/기간마다 약간 다른 값
            val = base_value * (len(accounts) - i) * (1 + 0.05 * j)
            row[p] = round(val, 0)
        rows.append(row)
    return _pl.DataFrame(rows)


_IS_ACCOUNTS = [
    "매출액",
    "매출원가",
    "매출총이익",
    "판매비와관리비",
    "영업이익",
    "당기순이익",
    "법인세비용",
    "이자비용",
    "감가상각비",
]

_BS_ACCOUNTS = [
    "자산총계",
    "부채총계",
    "자본총계",
    "유동자산",
    "유동부채",
    "비유동자산",
    "현금및현금성자산",
    "재고자산",
    "매출채권",
    "매입채무",
    "유형자산",
]

_CF_ACCOUNTS = [
    "영업활동으로인한현금흐름",
    "투자활동으로인한현금흐름",
    "재무활동으로인한현금흐름",
]

# 분기 포함 기간 목록 (select → toDict → annualColsFromPeriods 호환)
_QUARTERLY_PERIODS = [
    "2024Q4",
    "2024Q3",
    "2024Q2",
    "2024Q1",
    "2023Q4",
    "2023Q3",
    "2023Q2",
    "2023Q1",
    "2022Q4",
    "2022Q3",
    "2022Q2",
    "2022Q1",
    "2021Q4",
    "2020Q4",
]


class _MockNotesAccessor:
    """notes.inventory 등 전부 None 반환."""

    def __getattr__(self, name: str):
        return None


class _MockDocsAccessor:
    """docs.diff() 등 None 반환."""

    def diff(self):
        return None


class _MockFinanceAccessor:
    """finance.ratios / ratioSeries 기본 반환."""

    @property
    def ratios(self):
        return None

    @property
    def ratioSeries(self):
        return None


class _MockSelectResult:
    """SelectResult 호환 mock — .df 프로퍼티 제공."""

    def __init__(self, df: "pl.DataFrame", topic: str = ""):
        self._df = df
        self._topic = topic

    @property
    def df(self) -> "pl.DataFrame":
        return self._df

    @property
    def topic(self) -> str:
        return self._topic

    def __getattr__(self, name: str):
        return getattr(self._df, name)


class MockCompany:
    """데이터 없이 unit 테스트 가능한 경량 Company mock.

    실제 Company 인터페이스의 핵심 메서드를 제공:
    - stockCode, corpName, market, currency
    - IS, BS, CF, annual, cumulative
    - select(stmt, accounts) → MockSelectResult
    - show(topic), topicSummaries(), insights
    - notes, sector, gather(axis)
    - _cache (memoized_calc 호환)
    """

    def __init__(
        self,
        stockCode: str = "005930",
        corpName: str = "삼성전자",
        market: str = "KOSPI",
        currency: str = "KRW",
    ):
        self.stockCode = stockCode
        self.corpName = corpName
        self.market = market
        self.currency = currency
        self.notes = _MockNotesAccessor()
        self.docs = _MockDocsAccessor()
        self.finance = _MockFinanceAccessor()
        self._cache: dict = {}

        # 합성 DataFrame 미리 생성
        self._is_df = _make_synthetic_df("IS", _IS_ACCOUNTS, _QUARTERLY_PERIODS, base_value=1_000_000)
        self._bs_df = _make_synthetic_df("BS", _BS_ACCOUNTS, _QUARTERLY_PERIODS, base_value=5_000_000)
        self._cf_df = _make_synthetic_df("CF", _CF_ACCOUNTS, _QUARTERLY_PERIODS, base_value=500_000)

    @property
    def IS(self):
        return self._is_df

    @property
    def BS(self):
        return self._bs_df

    @property
    def CF(self):
        return self._cf_df

    @property
    def annual(self):
        return self._is_df

    @property
    def cumulative(self):
        return self._is_df

    @property
    def sector(self):
        return None

    @property
    def insights(self):
        return {"overall": "B+", "profitability": "A"}

    def select(self, stmt: str, accounts: list[str] | str | None = None, colList=None):
        """재무제표 계정 필터 — MockSelectResult 반환."""
        if isinstance(accounts, str):
            accounts = [accounts]

        mapping = {"IS": self._is_df, "BS": self._bs_df, "CF": self._cf_df}
        df = mapping.get(stmt)
        if df is None:
            return None

        if accounts is not None:
            import polars as _pl

            mask = _pl.col("계정명").is_in(accounts)
            filtered = df.filter(mask)
            if filtered.height == 0:
                # 찾지 못한 계정은 0으로 채운 행 생성
                period_cols = [c for c in df.columns if c != "계정명"]
                rows = []
                for acct in accounts:
                    row = {"계정명": acct}
                    for p in period_cols:
                        row[p] = 0.0
                    rows.append(row)
                filtered = _pl.DataFrame(rows)
            return _MockSelectResult(filtered, stmt)
        return _MockSelectResult(df, stmt)

    def show(self, topic: str, block=None, *, period=None, raw=False):
        """topic 데이터 반환 — IS/BS/CF는 합성 DataFrame."""
        mapping = {"IS": self._is_df, "BS": self._bs_df, "CF": self._cf_df}
        return mapping.get(topic)

    def topicSummaries(self):
        return {"IS": "손익계산서 요약", "BS": "재무상태표 요약", "CF": "현금흐름표 요약"}

    def gather(self, axis: str, *args, **kwargs):
        if axis == "price":
            import polars as _pl

            return _pl.DataFrame(
                {
                    "date": ["2024-12-30", "2024-12-27", "2024-12-26"],
                    "close": [72000, 71500, 71800],
                    "volume": [10000000, 9500000, 11000000],
                }
            )
        return None

    def trace(self, topic: str, period: str | None = None):
        return {"topic": topic, "source": "mock", "period": period}

    def diff(self):
        return None

    def filings(self, **kwargs):
        return []

    @staticmethod
    def listing(**kwargs):
        import polars as _pl

        return _pl.DataFrame({"종목코드": ["005930"], "회사명": ["삼성전자"]})

    @staticmethod
    def search(keyword: str):
        import polars as _pl

        return _pl.DataFrame({"종목코드": ["005930"], "회사명": ["삼성전자"]})


@pytest.fixture
def mock_company():
    """데이터 없이 unit 테스트 가능한 MockCompany fixture."""
    return MockCompany()


@pytest.fixture
def empty_mock_company():
    """모든 select가 None을 반환하는 빈 MockCompany."""

    class EmptyMockCompany(MockCompany):
        def select(self, stmt, accounts=None, colList=None):
            return None

        def show(self, topic, block=None, *, period=None, raw=False):
            return None

        @property
        def sector(self):
            return None

        def gather(self, axis, *args, **kwargs):
            return None

    return EmptyMockCompany(stockCode="999999", corpName="빈회사")


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
def aapl():
    """AAPL (Apple Inc.) EDGAR Company — 모듈 단위로 로드/해제."""
    if not _has_data(AAPL, "edgar"):
        pytest.skip("EDGAR finance 데이터 없음")
    from dartlab import Company

    c = Company(AAPL)
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
