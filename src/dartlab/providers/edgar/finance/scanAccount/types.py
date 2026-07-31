"""EDGAR 계정 스캔의 오류 계약과 내부 값 타입.

``EdgarScanError`` 계열은 원천·매핑·저장·실행 실패를 stage 로 구분해 올린다."""

from __future__ import annotations

from dataclasses import dataclass


class EdgarScanError(RuntimeError):
    """EDGAR bulk finance scan의 원천 또는 실행 실패."""

    def __init__(self, stage: str, message: str, *, source: str | None = None) -> None:
        self.stage = stage
        self.source = source
        sourceLabel = f", source={source}" if source else ""
        super().__init__(f"EDGAR scan failed: stage={stage}{sourceLabel}: {message}")


class EdgarScanMappingError(EdgarScanError):
    """CIK, ticker, company title universe 계약 실패."""


class EdgarScanStorageError(EdgarScanError):
    """listed companyfacts shard 읽기 또는 schema 실패."""


class EdgarScanExecutionError(EdgarScanError):
    """DuckDB와 검증 fallback 실행 실패."""

    def __init__(
        self,
        stage: str,
        message: str,
        *,
        source: str | None = None,
        primaryError: BaseException | None = None,
    ) -> None:
        self.primaryError = primaryError
        super().__init__(stage, message, source=source)


@dataclass(frozen=True)
class _TaxonomyTagKeys:
    usGaap: tuple[str, ...]
    ifrsFull: tuple[str, ...]
    usGaapCommon: frozenset[str] = frozenset()
    ifrsFullCommon: frozenset[str] = frozenset()

    @property
    def empty(self) -> bool:
        """두 taxonomy 모두 concept가 없는지 반환.

        Args:
            없음.

        Returns:
            US GAAP과 IFRS concept set이 모두 비었으면 True.

        Raises:
            없음.

        Example:
            >>> _TaxonomyTagKeys((), ()).empty
            True
        """
        return not self.usGaap and not self.ifrsFull


@dataclass(frozen=True)
class _TickerUniverse:
    cikToTicker: dict[str, str]
    tickerToTitle: dict[str, str]
