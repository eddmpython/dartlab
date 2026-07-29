"""edgar/bulk LoaderProvider 구현 (정공법 B — DIP).

`core/dataLoader.py` 가 직접 ensureFinanceParquet 호출 대신 registry dispatch.
import 시점에 registerLoader 호출하여 자동 등록.
"""

from __future__ import annotations

from dartlab.core.dataLoaderContract import validateRefreshPolicy
from dartlab.core.edgarClient import ensureFinanceParquet


class EdgarBulkLoader:
    """edgar 카테고리의 LoaderProvider 구현 (SEC 벌크 finance)."""

    category = "edgar"

    def ensure(self, stockCode, path, *, sinceYear=None, asOf=None, refresh="auto"):
        """SEC 벌크 finance parquet 보장 — ``ensureFinanceParquet`` 위임.

        Args:
            stockCode: 종목 ticker.
            path: 결과 parquet 경로.
            sinceYear: 시작 연도 (현재 미사용).
            asOf: 신선도 기준 시점 (현재 미사용).
            refresh: ``auto``/``force_check``/``local_only``.

        Raises:
            ValueError: 미지원 refresh 정책.
            FileNotFoundError: ``local_only`` cache 부재 또는 변환 후 CIK parquet 부재.

        Example:
            >>> EdgarBulkLoader().ensure("AAPL", Path("..."))
        """
        validateRefreshPolicy("edgar", refresh, pyodide=False)
        if refresh == "local_only":
            if not path.is_file():
                raise FileNotFoundError(f"로컬 EDGAR finance 없음: {path}")
            return
        ensureFinanceParquet(stockCode, path, refresh=refresh == "force_check")


def registerEdgarBulkLoader() -> None:
    """edgar/bulk LoaderProvider 등록 — circular import 회피용 함수 lazy import.

    Raises:
        없음.

    Example:
        >>> registerEdgarBulkLoader()
    """
    from dartlab.core.loaders import registerLoader

    registerLoader(EdgarBulkLoader())
