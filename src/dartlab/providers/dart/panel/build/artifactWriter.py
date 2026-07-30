"""Panel parquet를 bounded row group으로 조립하고 원자 발행한다."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
from filelock import FileLock
from filelock import Timeout as FileLockTimeout

from dartlab.providers.dart.build.saver import _ROW_GROUP_SIZE
from dartlab.providers.dart.panel.schema import PANEL_SCHEMA

_PANEL_ARROW_SCHEMA = pl.DataFrame(schema=PANEL_SCHEMA).to_arrow().schema
# PyArrow runtime은 column 목록을 지원하지만 현재 type stub은 bool만 선언한다.
_PANEL_DICTIONARY_OPTION = cast(
    bool,
    [column for column in _PANEL_ARROW_SCHEMA.names if column != "contentRaw"],
)


class PanelArtifactLayoutError(RuntimeError):
    """기존 panel artifact가 bounded merge 계약을 위반한다."""


class PanelArtifactLockError(RuntimeError):
    """동일 회사 panel writer lock을 제한 시간 안에 얻지 못했다."""


def _validateParquet(parquet: pq.ParquetFile, source: Path) -> None:
    if not parquet.schema_arrow.equals(_PANEL_ARROW_SCHEMA):
        raise PanelArtifactLayoutError(
            "panel parquet schema가 PANEL_SCHEMA와 정확히 일치하지 않습니다: "
            f"source={source}, actual={parquet.schema_arrow}, expected={_PANEL_ARROW_SCHEMA}"
        )
    for rowGroupIndex in range(parquet.metadata.num_row_groups):
        rowCount = parquet.metadata.row_group(rowGroupIndex).num_rows
        if rowCount > _ROW_GROUP_SIZE:
            raise PanelArtifactLayoutError(
                "panel row group이 bounded merge 계약을 위반했습니다: "
                f"source={source}, rowGroup={rowGroupIndex}, rows={rowCount}, max={_ROW_GROUP_SIZE}. "
                "full rebuild가 필요합니다"
            )


def _fsyncPath(path: Path) -> None:
    with path.open("r+b") as stream:
        os.fsync(stream.fileno())


@contextmanager
def _openParquet(path: Path) -> Iterator[pq.ParquetFile]:
    """PyArrow constructor 실패 때도 Windows file handle을 닫는다.

    Args:
        path: 읽을 parquet 경로.

    Yields:
        수명 안에서만 유효한 ParquetFile.

    Raises:
        OSError: 파일을 열 수 없을 때.
        pyarrow.ArrowException: parquet footer가 손상됐을 때.

    Example:
        >>> with _openParquet(Path("stage.parquet")) as parquet:  # doctest: +SKIP
        ...     print(parquet.metadata.num_rows)
    """

    with path.open("rb") as stream:
        parquet = pq.ParquetFile(
            stream,
            memory_map=False,
            pre_buffer=False,
        )
        try:
            yield parquet
        finally:
            parquet.close(force=True)


def writePanelStage(frame: pl.DataFrame, path: Path) -> int:
    """단일 공시 frame을 footer 검증한 atomic parquet stage로 기록한다.

    Args:
        frame: 정확한 PANEL_SCHEMA를 가진 비어 있지 않은 frame.
        path: 최종 stage 경로.

    Returns:
        기록 후 metadata로 다시 확인한 행 수.

    Raises:
        PanelArtifactLayoutError: frame schema 또는 검증 행 수가 잘못됐을 때.
        OSError: write, fsync, replace 또는 cleanup이 실패할 때.
        pyarrow.ArrowException: 기록된 parquet page를 완독할 수 없을 때.

    Example:
        >>> writePanelStage(frame, Path("document-00000000-00.parquet"))  # doctest: +SKIP
        142
    """

    if frame.is_empty():
        raise PanelArtifactLayoutError("panel stage frame이 비어 있습니다")
    if frame.columns != list(PANEL_SCHEMA) or dict(frame.schema) != PANEL_SCHEMA:
        raise PanelArtifactLayoutError(
            "panel stage schema가 PANEL_SCHEMA와 정확히 일치하지 않습니다: "
            f"columns={frame.columns}, schema={dict(frame.schema)}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as temporaryFile:
        temporary = Path(temporaryFile.name)
    try:
        pq.write_table(
            frame.select(PANEL_SCHEMA.keys()).to_arrow(),
            temporary,
            compression="zstd",
            use_dictionary=_PANEL_DICTIONARY_OPTION,
            write_statistics=True,
            row_group_size=_ROW_GROUP_SIZE,
        )
        _fsyncPath(temporary)
        with _openParquet(temporary) as parquet:
            _validateParquet(parquet, temporary)
            verifiedRows = parquet.metadata.num_rows
        if verifiedRows != frame.height:
            raise PanelArtifactLayoutError(
                f"panel stage 검증 행 수가 다릅니다: path={path}, expected={frame.height}, actual={verifiedRows}"
            )
        temporary.replace(path)
    except BaseException as writeError:
        if temporary.exists():
            try:
                temporary.unlink()
            except BaseException as cleanupError:
                raise BaseExceptionGroup(
                    "panel stage write와 temporary cleanup이 모두 실패했습니다",
                    [writeError, cleanupError],
                ) from None
        raise
    return verifiedRows


@dataclass(frozen=True)
class _StageEntry:
    period: str
    receiptNumber: str
    sequence: int
    path: Path


class PanelArtifactAssembler:
    """공시 단위 frame을 임시 stage에 내리고 최종 artifact를 원자 조립한다."""

    def __init__(self, destination: Path) -> None:
        self._destination = destination
        self._temporaryDirectory = tempfile.TemporaryDirectory(prefix="dartlab-panel-")
        self._stageRoot = Path(self._temporaryDirectory.name)
        self._entries: list[_StageEntry] = []
        self._changedReceipts: set[str] = set()
        self._sequence = 0

    def __enter__(self) -> PanelArtifactAssembler:
        return self

    def __exit__(self, excType: object, excValue: object, traceback: object) -> None:
        try:
            self._temporaryDirectory.cleanup()
        except BaseException as cleanupError:
            if isinstance(excValue, BaseException):
                raise BaseExceptionGroup(
                    "panel build와 stage cleanup이 모두 실패했습니다",
                    [excValue, cleanupError],
                ) from None
            raise

    def _stage(
        self,
        frame: pl.DataFrame,
        *,
        period: str,
        receiptNumber: str,
        changed: bool,
    ) -> None:
        if frame.is_empty():
            return
        stagePath = self._stageRoot / f"{self._sequence:08d}.parquet"
        writePanelStage(frame, stagePath)
        self._entries.append(
            _StageEntry(
                period=period,
                receiptNumber=receiptNumber,
                sequence=self._sequence,
                path=stagePath,
            )
        )
        self._sequence += 1
        if changed:
            self._changedReceipts.add(receiptNumber)

    def add(self, frame: pl.DataFrame, *, period: str, receiptNumber: str) -> None:
        """새 공시 frame 하나를 bounded stage로 내린다.

        Args:
            frame: PANEL_SCHEMA를 만족하는 단일 공시 frame.
            period: 공시 귀속 기간.
            receiptNumber: DART 접수번호.

        Returns:
            None.

        Raises:
            PanelArtifactLayoutError: 필수 컬럼이 없을 때.

        Example:
            >>> assembler.add(frame, period="2024Q4", receiptNumber="20250319000001")  # doctest: +SKIP
        """

        self._stage(
            frame,
            period=period,
            receiptNumber=receiptNumber,
            changed=True,
        )

    def markChangedReceipt(self, receiptNumber: str) -> None:
        """행이 0개인 정상 공시도 기존 receipt를 제거할 수 있게 변경으로 등록한다.

        Args:
            receiptNumber: 변경된 DART 접수번호.

        Returns:
            None.

        Raises:
            PanelArtifactLayoutError: 접수번호가 비어 있을 때.

        Example:
            >>> assembler.markChangedReceipt("20250319000001")  # doctest: +SKIP
        """

        if not receiptNumber:
            raise PanelArtifactLayoutError("변경 receiptNumber가 비어 있습니다")
        self._changedReceipts.add(receiptNumber)

    @property
    def stageRoot(self) -> Path:
        """격리 worker가 stage를 쓸 수 있는 이번 build 전용 경로.

        Args:
            없음.

        Returns:
            이번 assembler 수명에만 유효한 임시 디렉터리.

        Raises:
            없음.

        Example:
            >>> assembler.stageRoot.is_dir()  # doctest: +SKIP
            True
        """

        return self._stageRoot

    def registerStage(
        self,
        path: Path,
        *,
        period: str,
        receiptNumber: str,
        sequence: int,
    ) -> int:
        """격리 worker가 쓴 bounded stage를 검증 후 조립 목록에 등록한다.

        Args:
            path: worker가 쓴 parquet stage.
            period: stage의 단일 귀속 기간.
            receiptNumber: stage의 단일 접수번호.
            sequence: 회사 입력 내 안정 정렬 순서.

        Returns:
            검증된 stage 행 수.

        Raises:
            PanelArtifactLayoutError: 경로, schema, row group 또는 identity가 잘못됐을 때.

        Example:
            >>> assembler.registerStage(path, period="2024Q4", receiptNumber="20250319000001", sequence=0)  # doctest: +SKIP
        """

        resolvedRoot = self._stageRoot.resolve()
        resolvedPath = path.resolve()
        if resolvedRoot not in resolvedPath.parents:
            raise PanelArtifactLayoutError(f"panel stage 경로가 build root를 벗어났습니다: {path}")
        if not resolvedPath.is_file() or resolvedPath.stat().st_size <= 0:
            raise PanelArtifactLayoutError(f"panel stage가 없거나 비어 있습니다: {path}")
        with _openParquet(resolvedPath) as parquet:
            _validateParquet(parquet, resolvedPath)
            rowCount = parquet.metadata.num_rows
            if rowCount <= 0:
                raise PanelArtifactLayoutError(f"panel stage가 0행입니다: {path}")
            verifiedRows = 0
            for rowGroupIndex in range(parquet.metadata.num_row_groups):
                table = parquet.read_row_group(rowGroupIndex, use_threads=False)
                verifiedRows += table.num_rows
                identity = table.select(["period", "rceptNo", "corp"])
                periods = identity.column("period").unique().to_pylist()
                receipts = identity.column("rceptNo").unique().to_pylist()
                companies = identity.column("corp").unique().to_pylist()
                expectedCompany = self._destination.stem
                if periods != [period] or receipts != [receiptNumber] or companies != [expectedCompany]:
                    raise PanelArtifactLayoutError(
                        "panel stage identity 불일치: "
                        f"path={path}, expected=({period}, {receiptNumber}, {expectedCompany}), "
                        f"actual=({periods}, {receipts}, {companies})"
                    )
                del identity
                del table
                pa.default_memory_pool().release_unused()
            if verifiedRows != rowCount:
                raise PanelArtifactLayoutError(
                    f"panel stage 완독 행 수가 다릅니다: path={path}, expected={rowCount}, actual={verifiedRows}"
                )
        self._entries.append(
            _StageEntry(
                period=period,
                receiptNumber=receiptNumber,
                sequence=sequence,
                path=resolvedPath,
            )
        )
        self._changedReceipts.add(receiptNumber)
        self._sequence = max(self._sequence, sequence + 1)
        return rowCount

    def _stageRetainedExisting(self) -> None:
        source = self._destination
        with _openParquet(source) as parquet:
            _validateParquet(parquet, source)
            for rowGroupIndex in range(parquet.metadata.num_row_groups):
                table = parquet.read_row_group(rowGroupIndex, use_threads=False)
                frame = cast(pl.DataFrame, pl.from_arrow(table))
                if frame["period"].null_count() or frame["rceptNo"].null_count():
                    raise PanelArtifactLayoutError(f"기존 panel period 또는 rceptNo가 null입니다: source={source}")
                frame = frame.filter(~pl.col("rceptNo").is_in(sorted(self._changedReceipts)))
                if not frame.is_empty():
                    for partition in frame.partition_by(
                        ["period", "rceptNo"],
                        maintain_order=True,
                    ):
                        period = partition["period"][0]
                        receiptNumber = partition["rceptNo"][0] or ""
                        if period is None:
                            raise PanelArtifactLayoutError(f"기존 panel period가 null입니다: source={source}")
                        self._stage(
                            partition,
                            period=period,
                            receiptNumber=receiptNumber,
                            changed=False,
                        )
                del frame
                del table
                pa.default_memory_pool().release_unused()

    @staticmethod
    def _closeWriter(
        writer: pq.ParquetWriter | None,
        pendingError: BaseException | None,
    ) -> None:
        if writer is None:
            if pendingError is not None:
                raise pendingError
            return
        try:
            writer.close()
        except BaseException as closeError:
            if pendingError is not None:
                raise BaseExceptionGroup(
                    "panel artifact write와 close가 모두 실패했습니다",
                    [pendingError, closeError],
                ) from None
            raise
        if pendingError is not None:
            raise pendingError

    def _assemble(self, temporary: Path) -> int:
        entries = sorted(
            self._entries,
            key=lambda entry: (entry.period, entry.receiptNumber, entry.sequence),
        )
        writer: pq.ParquetWriter | None = None
        pendingError: BaseException | None = None
        totalRows = 0
        try:
            for entry in entries:
                with _openParquet(entry.path) as parquet:
                    if writer is None:
                        writer = pq.ParquetWriter(
                            temporary,
                            _PANEL_ARROW_SCHEMA,
                            compression="zstd",
                            use_dictionary=_PANEL_DICTIONARY_OPTION,
                            write_statistics=True,
                        )
                    elif not parquet.schema_arrow.equals(_PANEL_ARROW_SCHEMA):
                        raise PanelArtifactLayoutError(f"panel stage schema 불일치: {entry.path}")
                    for rowGroupIndex in range(parquet.metadata.num_row_groups):
                        table = parquet.read_row_group(rowGroupIndex, use_threads=False)
                        writer.write_table(table, row_group_size=_ROW_GROUP_SIZE)
                        totalRows += table.num_rows
                        del table
                        pa.default_memory_pool().release_unused()
        except BaseException as exc:
            pendingError = exc
        self._closeWriter(writer, pendingError)
        return totalRows

    @staticmethod
    def _validatePublished(path: Path) -> int:
        with _openParquet(path) as parquet:
            _validateParquet(parquet, path)
            return parquet.metadata.num_rows

    def _commitLocked(self, *, merge: bool, overwrite: bool) -> int:
        if not self._entries and not self._changedReceipts:
            return 0
        if self._destination.exists() and not overwrite and not merge:
            return 0
        if merge and self._destination.exists():
            self._stageRetainedExisting()

        if not self._entries:
            emptyPath = self._stageRoot / "empty-layout.parquet"
            pl.DataFrame(schema=PANEL_SCHEMA).write_parquet(
                emptyPath,
                compression="zstd",
                statistics=True,
                row_group_size=_ROW_GROUP_SIZE,
            )
            self._entries.append(
                _StageEntry(
                    period="",
                    receiptNumber="",
                    sequence=self._sequence,
                    path=emptyPath,
                )
            )
        with tempfile.NamedTemporaryFile(
            prefix=f".{self._destination.name}.",
            suffix=".tmp",
            dir=self._destination.parent,
            delete=False,
        ) as temporaryFile:
            temporary = Path(temporaryFile.name)
        try:
            self._assemble(temporary)
            _fsyncPath(temporary)
            totalRows = self._validatePublished(temporary)
            temporary.replace(self._destination)
        except BaseException as publishError:
            if temporary.exists():
                try:
                    temporary.unlink()
                except BaseException as cleanupError:
                    raise BaseExceptionGroup(
                        "panel artifact publish와 temporary cleanup이 모두 실패했습니다",
                        [publishError, cleanupError],
                    ) from None
            raise
        return totalRows

    def commit(self, *, merge: bool, overwrite: bool) -> int:
        """stage와 선택적 기존 receipt를 정렬 조립해 destination을 원자 교체한다.

        Args:
            merge: 기존 artifact에서 변경되지 않은 receipt를 보존할지 여부.
            overwrite: full build에서 기존 artifact 교체를 허용할지 여부.

        Returns:
            발행된 전체 행 수.

        Raises:
            PanelArtifactLockError: 동일 회사 writer lock을 제한 시간에 얻지 못할 때.
            PanelArtifactLayoutError: 기존 또는 stage artifact 계약이 잘못됐을 때.

        Example:
            >>> totalRows = assembler.commit(merge=False, overwrite=True)  # doctest: +SKIP
        """

        self._destination.parent.mkdir(parents=True, exist_ok=True)
        lockPath = self._destination.with_name(f".{self._destination.name}.lock")
        lock = FileLock(lockPath, timeout=120)
        try:
            with lock:
                return self._commitLocked(merge=merge, overwrite=overwrite)
        except FileLockTimeout as exc:
            raise PanelArtifactLockError(f"panel artifact lock 획득 시간 초과: {lockPath}") from exc


__all__ = [
    "PanelArtifactAssembler",
    "PanelArtifactLayoutError",
    "PanelArtifactLockError",
    "writePanelStage",
]
