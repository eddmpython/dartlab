"""quant 엔진 공용 헬퍼 — OHLCV fetch, market 감지, scan parquet 로드."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


# ── Market 감지 ──────────────────────────────────────────


def detect_market(stockCode: str) -> str:
    """종목코드에서 시장을 자동 감지.

    6자리 숫자 → KR, 알파벳 포함 → US.
    """
    if stockCode and stockCode.strip().isdigit() and len(stockCode.strip()) == 6:
        return "KR"
    return "US"


def resolve_market(stockCode: str, market: str = "auto") -> str:
    """market 파라미터 해석. auto이면 자동 감지."""
    if market and market.lower() != "auto":
        return market.upper()
    return detect_market(stockCode)


# ── OHLCV fetch ──────────────────────────────────────────


def fetch_ohlcv(stockCode: str, **kwargs: Any):
    """gather("price")로 OHLCV 수집. 실패 시 None."""
    try:
        from dartlab.gather.entry import GatherEntry

        g = GatherEntry()
        return g("price", stockCode, **kwargs)
    except (ImportError, ValueError, TypeError, RuntimeError):
        log.warning("OHLCV fetch 실패: %s", stockCode)
        return None


def fetch_benchmark(market: str = "KR", **kwargs: Any):
    """벤치마크 OHLCV 수집. KR=KOSPI, US=S&P500."""
    symbol = "KOSPI" if market == "KR" else "^GSPC"
    try:
        from dartlab.gather.entry import GatherEntry

        g = GatherEntry()
        return g("price", symbol, **kwargs)
    except (ImportError, ValueError, TypeError, RuntimeError):
        log.warning("벤치마크 fetch 실패: %s", symbol)
        return None


# ── scan parquet 로드 (메모리 안전) ──────────────────────


def _scan_data_root() -> Path:
    """data/ 루트 경로."""
    from dartlab.core.dataLoader import _getDataRoot

    return Path(_getDataRoot())


def load_scan_parquet(name: str, market: str = "KR"):
    """scan 프리빌드 parquet lazy scan 로드.

    Args:
        name: "finance", "changes" 또는 report/ 하위 이름
        market: "KR" | "US"

    Returns:
        pl.LazyFrame 또는 None
    """
    import polars as pl

    root = _scan_data_root()
    if market == "KR":
        base = root / "dart" / "scan"
    else:
        base = root / "edgar" / "scan"

    # finance.parquet 또는 report/ 하위
    path = base / f"{name}.parquet"
    if not path.exists():
        path = base / "report" / f"{name}.parquet"
    if not path.exists():
        log.warning("scan parquet 없음: %s", path)
        return None

    return pl.scan_parquet(path)


def load_docs_for_stock(stockCode: str):
    """단일 종목 docs parquet 로드.

    Returns:
        pl.DataFrame 또는 None
    """
    import polars as pl

    root = _scan_data_root()
    path = root / "dart" / "docs" / f"{stockCode}.parquet"
    if not path.exists():
        log.warning("docs parquet 없음: %s", path)
        return None

    return pl.read_parquet(path)


def load_changes_for_stock(stockCode: str):
    """changes.parquet에서 단일 종목 필터링.

    Returns:
        pl.DataFrame 또는 None
    """
    import polars as pl

    root = _scan_data_root()
    path = root / "dart" / "scan" / "changes.parquet"
    if not path.exists():
        return None

    lf = pl.scan_parquet(path)
    for col in ("stockCode", "종목코드", "corp_code"):
        try:
            return lf.filter(pl.col(col) == stockCode).collect()
        except pl.exceptions.ColumnNotFoundError:
            continue
    return None


# ── scan parquet에서 종목 백분위 계산 ────────────────────


def stock_percentile(lf, stockCode: str, col: str, stock_col: str = "stockCode", reverse: bool = False):
    """scan lazy frame에서 특정 종목의 컬럼 백분위를 계산.

    Args:
        lf: pl.LazyFrame (scan parquet)
        stockCode: 종목코드
        col: 백분위를 구할 컬럼명
        stock_col: 종목코드 컬럼명
        reverse: True이면 높은 값 = 낮은 백분위 (PBR 등)

    Returns:
        (value, percentile) 또는 (None, None)
    """
    import polars as pl

    try:
        # 종목코드 컬럼 자동 탐색
        schema_names = lf.collect_schema().names()
        actual_stock_col = None
        for c in (stock_col, "종목코드", "stockCode", "corp_code"):
            if c in schema_names:
                actual_stock_col = c
                break
        if actual_stock_col is None or col not in schema_names:
            return None, None

        # 이 종목의 값
        row = lf.filter(pl.col(actual_stock_col) == stockCode).select(col).collect()
        if len(row) == 0 or row.item() is None:
            return None, None

        val = float(row.item())

        # 전체 분포에서 백분위
        all_vals = lf.select(col).drop_nulls().collect().to_series()
        if len(all_vals) == 0:
            return val, None

        if reverse:
            pct = float((all_vals > val).sum() / len(all_vals))
        else:
            pct = float((all_vals < val).sum() / len(all_vals))

        return val, round(pct, 4)
    except (KeyError, ValueError, TypeError):
        return None, None


def load_allfilings_for_stock(stockCode: str):
    """allFilings parquet에서 단일 종목 데이터 로드.

    data/dart/allFilings/*.parquet에서 corp_code 또는 stockCode로 필터링.

    Returns:
        pl.DataFrame 또는 None
    """
    import polars as pl

    root = _scan_data_root()
    adir = root / "dart" / "allFilings"
    if not adir.exists():
        return None

    parquets = sorted(adir.glob("*.parquet"))
    # _meta.parquet 제외
    parquets = [p for p in parquets if "_meta" not in p.name]
    if not parquets:
        return None

    frames = []
    for p in parquets[-60:]:  # 최근 60일분만 (메모리 안전)
        try:
            lf = pl.scan_parquet(p)
            schema = lf.collect_schema().names()
            for col in ("stockCode", "종목코드", "corp_code"):
                if col in schema:
                    filtered = lf.filter(pl.col(col) == stockCode).collect()
                    if len(filtered) > 0:
                        frames.append(filtered)
                    break
        except (OSError, pl.exceptions.ComputeError):
            continue

    if not frames:
        return None
    return pl.concat(frames, how="diagonal_relaxed")


# ── OHLCV → numpy 변환 ──────────────────────────────────


def ohlcv_to_arrays(df):
    """Polars OHLCV DataFrame → numpy 배열 dict.

    Returns:
        dict with keys: open, high, low, close, volume, date
        또는 빈 dict
    """
    import numpy as np

    if df is None or df.is_empty():
        return {}

    result = {}
    for col in ("open", "high", "low", "close", "volume"):
        if col in df.columns:
            result[col] = df.get_column(col).to_numpy().astype(np.float64)

    if "date" in df.columns:
        result["date"] = df.get_column("date").to_list()

    return result
