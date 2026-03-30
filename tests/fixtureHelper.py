"""fixture 기반 테스트 헬퍼 — Company 전체 로드 없이 finance 파이프라인 검증.

핵심 패턴:
  df = loadFixture("005930", "finance")
  with patchLoadData(df):
      series, periods = buildAnnual("005930")

Company를 통째로 로드하면 200~500MB 메모리를 소모한다.
fixture parquet + patch로 동일한 검증을 ~1MB 이내에서 수행한다.
"""

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import polars as pl

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def loadFixture(stockCode: str, category: str) -> pl.DataFrame:
    """tests/fixtures/{stockCode}.{category}.parquet 로드."""
    path = FIXTURE_DIR / f"{stockCode}.{category}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"fixture 없음: {path}")
    return pl.read_parquet(path)


def hasFixture(stockCode: str, category: str) -> bool:
    """fixture parquet 존재 여부."""
    return (FIXTURE_DIR / f"{stockCode}.{category}.parquet").exists()


@contextmanager
def patchLoadData(df: pl.DataFrame):
    """dartlab.core.dataLoader.loadData를 fixture DataFrame으로 패치."""
    with patch("dartlab.core.dataLoader.loadData", return_value=df):
        yield


def buildAnnualFromFixture(stockCode: str):
    """fixture parquet로 buildAnnual 실행. (series, periods) 반환."""
    from dartlab.providers.dart.finance.pivot import buildAnnual

    df = loadFixture(stockCode, "finance")
    with patchLoadData(df):
        return buildAnnual(stockCode)


def buildTimeseriesFromFixture(stockCode: str):
    """fixture parquet로 buildTimeseries 실행. (series, periods) 반환."""
    from dartlab.providers.dart.finance.pivot import buildTimeseries

    df = loadFixture(stockCode, "finance")
    with patchLoadData(df):
        return buildTimeseries(stockCode)


# ── fixture parquet 목록 ──

def availableFixtureStocks(category: str = "finance") -> list[str]:
    """해당 카테고리의 fixture parquet이 있는 종목코드 목록."""
    return sorted(
        p.stem.split(".")[0]
        for p in FIXTURE_DIR.glob(f"*.{category}.parquet")
    )
