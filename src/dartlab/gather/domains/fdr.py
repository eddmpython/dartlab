"""FinanceDataReader 데이터 도메인 — KR/US 히스토리.

optional dependency: ``pip install finance-datareader``
fallback 체인에서 naver 다음 순서로 사용.
"""

from __future__ import annotations

import importlib
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from ..types import SourceUnavailableError

log = logging.getLogger(__name__)

_CACHE_DIR = Path.home() / ".dartlab" / "cache" / "history"


def _available() -> bool:
    """FinanceDataReader 패키지 설치 여부를 확인.

    Returns
    -------
    bool
        ``True`` — ``finance-datareader`` import 가능.
        ``False`` — 미설치.
    """
    try:
        importlib.import_module("FinanceDataReader")
    except ImportError:
        return False
    return True


async def fetchHistory(
    stockCode: str,
    client=None,
    *,
    start: str = "",
    end: str = "",
    market: str = "KR",
    limit: int | None = None,
    **kwargs,
) -> list[dict]:
    """OHLCV 히스토리 — FDR 경유.

    Capabilities: FinanceDataReader 일별 OHLCV — KR/US 양쪽 stable backend.
    AIContext: gather.history fallback 최후 보루 — Yahoo/Naver/FMP 모두 실패 후.
    Guide: FDR 라이브러리 의존 — 미설치 시 raise.
    When: primary source 전부 실패 후 last-resort fallback.
    How: FinanceDataReader.DataReader 호출 → list[dict].

    Args:
        stock_code: 종목코드 (KR: "005930", US: "AAPL").
        start: 시작일 (YYYY-MM-DD). 빈 문자열이면 최대한 과거.
        end: 종료일. 빈 문자열이면 오늘.
        limit: 반환 행수 상한 (가장 최근 N일). None이면 전체.

    Returns:
        [{"date": ..., "open": ..., "high": ..., "low": ..., "close": ..., "volume": ...}, ...]

    Raises:
        SourceUnavailableError: optional dependency, provider 호출 또는 응답 schema가 유효하지 않은 경우.

    Example:
        >>> rows = await fetchHistory("005930", start="2024-01-01", end="2024-12-31")

    Requires:
        ``finance-datareader`` optional install (미설치 시 빈 list). Parquet 캐시
        디렉토리 (``~/.dartlab/cache/history/``) 쓰기 권한.

    See Also:
        sources/history.fetch : 본 함수의 호출 체인.
        yahooChart.fetchHistory · naverGlobal.fetchHistory · fmp.fetchHistory : 동행 source.
    """
    if not _available():
        raise SourceUnavailableError("FinanceDataReader optional dependency가 설치되지 않았습니다")

    try:
        fdr = importlib.import_module("FinanceDataReader")
    except ImportError as exc:
        raise SourceUnavailableError("FinanceDataReader를 import할 수 없습니다") from exc

    startDate = start or "1990-01-01"
    endDate = end or (date.today() + timedelta(days=1)).isoformat()

    # Parquet 캐시 확인
    cached = _loadCache(stockCode, market)
    if cached is not None:
        try:
            requiredFields = ("date", "open", "high", "low", "close", "volume")
            for row in cached:
                if not isinstance(row, dict) or any(field not in row for field in requiredFields):
                    raise ValueError("필수 OHLCV 필드가 없습니다")
                datetime.strptime(str(row["date"])[:10], "%Y-%m-%d")
                float(row["open"])
                float(row["high"])
                float(row["low"])
                float(row["close"])
                int(row["volume"])
            filtered = [r for r in cached if (not start or r["date"] >= start) and (not end or r["date"] <= end)]
        except (KeyError, TypeError, ValueError) as exc:
            raise SourceUnavailableError("FDR history 캐시 schema가 올바르지 않습니다") from exc
        if filtered:
            if limit is not None and limit > 0:
                return filtered[-limit:]
            return filtered

    try:
        df = fdr.DataReader(stockCode, startDate, endDate)
    except (ImportError, OSError, ValueError, KeyError, TypeError) as exc:
        raise SourceUnavailableError(f"FDR history 요청 실패: {stockCode}") from exc

    if df.empty:
        return []

    requiredColumns = {"Open", "High", "Low", "Close"}
    columns = set(getattr(df, "columns", ()))
    missingColumns = requiredColumns - columns
    if missingColumns:
        missing = ", ".join(sorted(missingColumns))
        raise SourceUnavailableError(f"FDR history 응답에 필수 열이 없습니다: {missing}")

    rows: list[dict] = []
    try:
        for idx, row in df.iterrows():
            dateStr = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
            datetime.strptime(dateStr, "%Y-%m-%d")
            rows.append(
                {
                    "date": dateStr,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row.get("Volume", 0)),
                }
            )
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceUnavailableError("FDR history 행을 해석할 수 없습니다") from exc

    # Parquet 캐시 저장
    _saveCache(stockCode, market, rows)

    if limit is not None and limit > 0:
        return rows[-limit:]
    return rows


def _cacheKey(stockCode: str, market: str) -> Path:
    """OHLCV 히스토리 Parquet 캐시 파일 경로를 생성.

    Parameters
    ----------
    stockCode : str
        종목코드 (예: ``"005930"``, ``"AAPL"``).
    market : str
        시장 코드 (예: ``"KR"``, ``"US"``). 소문자로 변환하여 하위 디렉터리 결정.

    Returns
    -------
    Path
        ``~/.dartlab/cache/history/{market}/{stockCode}.parquet`` 경로.
        부모 디렉터리가 없으면 자동 생성.
    """
    subdir = _CACHE_DIR / market.lower()
    subdir.mkdir(parents=True, exist_ok=True)
    return subdir / f"{stockCode}.parquet"


def _saveCache(stockCode: str, market: str, rows: list[dict]) -> None:
    """OHLCV 히스토리를 Parquet 캐시로 저장.

    Parameters
    ----------
    stockCode : str
        종목코드.
    market : str
        시장 코드.
    rows : list[dict]
        OHLCV 행 목록. 빈 리스트면 저장하지 않음.

    Returns
    -------
    None
        파일 저장 완료 후 반환. 저장 실패 시 경고 로그만 남김.
    """
    if not rows:
        return
    try:
        import polars as pl

        df = pl.DataFrame(rows)
        path = _cacheKey(stockCode, market)
        df.write_parquet(path)
        log.debug("FDR 캐시 저장: %s (%d rows)", path, len(rows))
    except (ImportError, OSError, ValueError, KeyError, TypeError) as exc:
        log.warning("FDR 캐시 저장 실패: %s", exc)


def _loadCache(stockCode: str, market: str) -> list[dict] | None:
    """Parquet 캐시에서 OHLCV 히스토리를 로드.

    캐시 파일이 1일 이내 생성된 경우만 사용한다.

    Parameters
    ----------
    stockCode : str
        종목코드.
    market : str
        시장 코드.

    Returns
    -------
    list[dict] | None
        캐시된 OHLCV 행 목록. 각 dict는 date/open/high/low/close/volume 키 포함.
        캐시 없음, 1일 초과, 읽기 실패 시 None.
    """
    path = _cacheKey(stockCode, market)
    if not path.exists():
        return None

    import os
    from datetime import datetime

    mtime = datetime.fromtimestamp(os.path.getmtime(path))
    if (datetime.now() - mtime).days > 1:
        return None

    try:
        import polars as pl

        df = pl.read_parquet(path)
        return df.to_dicts()
    except (ImportError, OSError, ValueError):
        return None
