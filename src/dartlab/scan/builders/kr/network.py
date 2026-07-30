"""Panel 계열회사 표를 runtime용 기업집단 artifact로 변환한다."""

from __future__ import annotations

import os
import re
import struct
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from dartlab.core.memory import withMemoryBudget
from dartlab.scan.builders.kr.common import panelDir, scanDir
from dartlab.scan.builders.kr.corpProfile import _loadJurirStockMap, normalizeJurirNo
from dartlab.scan.builders.kr.parquetContent import (
    _readDictionarySelectedContents,
    _UnsupportedContentLayout,
)
from dartlab.scan.network.affiliates import (
    AFFILIATE_DOCS_SCHEMA,
    AFFILIATE_DOCS_SCHEMA_VERSION,
    compileAffiliateGroups,
    validateAffiliateDocsArtifact,
)
from dartlab.scan.network.scanner import _normalizeCompanyName, loadListing

_MEMBERSHIP_SCHEMA = {column: AFFILIATE_DOCS_SCHEMA[column] for column in list(AFFILIATE_DOCS_SCHEMA)[:4]}
_OUTPUT_SCHEMA = AFFILIATE_DOCS_SCHEMA
_METADATA_BATCH_ROWS = 4096
_CONTENT_BATCH_ROWS = 256
_MAX_PANEL_WORKERS = 2
_MAX_ARROW_CONTENT_BYTES = 128 * 1024 * 1024
_DUCKDB_CONTENT_LOCK = Lock()
_ARROW_CONTENT_LOCK = Lock()
_SERIAL_ARROW_CONTENT_BYTES = 32 * 1024 * 1024

_REGISTRATION_NUMBER = re.compile(r"(?<!\d)[0-9]{6}-?[0-9]{7}(?!\d)")


class AffiliateDocsBuildError(RuntimeError):
    """계열회사 prebuild의 source 또는 schema 실패."""

    def __init__(self, code: str, source: Path, cause: BaseException) -> None:
        self.code = code
        self.source = source
        super().__init__(f"affiliate docs build failed: code={code}, source={source}: {cause}")


def panelContentRequiresSerialRead(source: Path) -> bool:
    """Parquet footer만 읽어 contentRaw가 전용 serial 구간을 요구하는지 판정한다."""

    with pq.ParquetFile(source, memory_map=False, pre_buffer=False) as parquet:
        if "contentRaw" not in parquet.schema_arrow.names:
            raise ValueError(f"panel contentRaw 컬럼 누락: {source}")
        contentIndex = parquet.schema_arrow.names.index("contentRaw")
        largestContentChunk = max(
            (
                parquet.metadata.row_group(index).column(contentIndex).total_uncompressed_size
                for index in range(parquet.num_row_groups)
            ),
            default=0,
        )
    return largestContentChunk > _SERIAL_ARROW_CONTENT_BYTES


@dataclass(frozen=True)
class _AffiliateReadResult:
    rows: frozenset[tuple[str, str, str, str]]
    unknownLegalRows: int = 0
    nameOnlyRows: int = 0
    nameMismatchRows: int = 0


def _rowNameCodes(row: list[str], nameToCode: dict[str, str]) -> set[str]:
    """표 한 행의 회사명 후보를 listing 종목코드 후보로만 변환한다."""

    codes: set[str] = set()
    for cell in row:
        normalized = _normalizeCompanyName(cell)
        code = nameToCode.get(cell) or nameToCode.get(normalized)
        if code:
            codes.add(code)
    return codes


def _resolveTableAffiliates(
    tables: list[list[list[str]]],
    nameToCode: dict[str, str],
    jurirToCode: dict[str, str],
) -> tuple[set[str], int, int, int, bool]:
    """법인등록번호가 정확히 일치하는 상장사만 affiliate로 확정한다."""

    affiliateCodes: set[str] = set()
    unknownLegalRows = 0
    nameOnlyRows = 0
    nameMismatchRows = 0
    hasIdentityCandidates = False
    for table in tables:
        for row in table:
            nameCodes = _rowNameCodes(row, nameToCode)
            legalIds = {
                normalized
                for cell in row
                for match in _REGISTRATION_NUMBER.findall(cell)
                if (normalized := normalizeJurirNo(match)) is not None
            }
            if not legalIds:
                if nameCodes:
                    hasIdentityCandidates = True
                    nameOnlyRows += 1
                continue

            hasIdentityCandidates = True
            legalCodes = {jurirToCode[legalId] for legalId in legalIds if legalId in jurirToCode}
            if len(legalIds) != 1 or len(legalCodes) != 1:
                unknownLegalRows += 1
                continue
            legalCode = legalCodes.pop()
            affiliateCodes.add(legalCode)
            if nameCodes and legalCode not in nameCodes:
                nameMismatchRows += 1
    return affiliateCodes, unknownLegalRows, nameOnlyRows, nameMismatchRows, hasIdentityCandidates


def _isWellFormedFragment(content: str) -> bool:
    """table parser가 데이터 표를 만들지 못한 fragment의 XML 문법만 구분한다."""

    try:
        ET.fromstring(f"<root>{content}</root>")
    except (ET.ParseError, ValueError):
        return False
    return True


def _parseRevisionTables(
    contents: list[str],
    *,
    code: str,
    source: Path,
) -> list[list[list[str]]]:
    """선택 revision의 XML table을 파싱하고 손상 fragment를 구분한다."""

    from dartlab.providers.dart.panel.text import parsePanelXmlTables

    tables: list[list[list[str]]] = []
    for content in (value for value in contents if "<TR" in value):
        parsed = parsePanelXmlTables(content)
        if not parsed and not _isWellFormedFragment(content):
            raise AffiliateDocsBuildError(
                code,
                source,
                ValueError("계열회사 section의 XML table이 손상됐습니다"),
            )
        tables.extend(parsed)
    return tables


def _readRevisionIndexes(parquet: pq.ParquetFile) -> dict[tuple[str, str], list[int]]:
    """좁은 metadata batch만 읽어 계열회사 revision별 행 번호를 모은다."""

    revisionIndexes: dict[tuple[str, str], list[int]] = {}
    rowOffset = 0
    batches = parquet.iter_batches(
        batch_size=_METADATA_BATCH_ROWS,
        columns=["sectionLeaf", "period", "rceptNo"],
        use_threads=False,
    )
    for batch in batches:
        sectionLeaves = batch.column("sectionLeaf").to_pylist()
        periods = batch.column("period").to_pylist()
        receiptNumbers = batch.column("rceptNo").to_pylist()
        for localIndex, sectionLeaf in enumerate(sectionLeaves):
            if not sectionLeaf or "계열회사" not in sectionLeaf:
                continue
            period = periods[localIndex]
            if not period:
                continue
            receiptNumber = receiptNumbers[localIndex] or ""
            revisionIndexes.setdefault((period, receiptNumber), []).append(rowOffset + localIndex)
        rowOffset += batch.num_rows
    return revisionIndexes


def _readSelectedContentsDuckDb(
    source: Path,
    selectedIndexes: set[int],
) -> dict[int, str]:
    """합법적인 oversized multi-page dictionary를 직렬 bounded query로 읽는다."""

    import duckdb

    connection = None
    rows: list[tuple[int, str | None]] = []
    with _DUCKDB_CONTENT_LOCK:
        try:
            connection = duckdb.connect()
            connection.execute("SET threads = 1")
            connection.execute("SET memory_limit = '1200MB'")
            connection.execute("SET preserve_insertion_order = false")
            rows = connection.execute(
                """
                SELECT file_row_number, contentRaw
                FROM read_parquet(?, file_row_number = true)
                WHERE file_row_number IN (SELECT unnest(?))
                """,
                [str(source), sorted(selectedIndexes)],
            ).fetchall()
        except duckdb.Error as queryError:
            if connection is not None:
                try:
                    connection.close()
                except duckdb.Error as closeError:
                    failures = ExceptionGroup(
                        "oversized panel query와 DuckDB close가 함께 실패했습니다",
                        [queryError, closeError],
                    )
                    raise ValueError("oversized panel query와 close가 함께 실패했습니다") from failures
            raise ValueError(f"oversized panel content query 실패: {queryError}") from queryError
        else:
            try:
                connection.close()
            except duckdb.Error as closeError:
                raise ValueError(f"oversized panel DuckDB close 실패: {closeError}") from closeError

    actualIndexes = {rowIndex for rowIndex, _ in rows}
    if actualIndexes != selectedIndexes:
        missing = sorted(selectedIndexes - actualIndexes)[:5]
        unexpected = sorted(actualIndexes - selectedIndexes)[:5]
        raise ValueError(f"oversized panel content 행 불일치: missing={missing}, unexpected={unexpected}")
    return {rowIndex: content for rowIndex, content in rows if content is not None}


def _readSelectedContents(
    source: Path,
    parquet: pq.ParquetFile,
    selectedIndexes: set[int],
) -> dict[int, str]:
    """선택 content만 읽고 대형 legacy dictionary는 streaming으로 제한한다."""

    if not selectedIndexes:
        return {}
    contentIndex = parquet.schema_arrow.names.index("contentRaw")
    largestContentChunk = max(
        parquet.metadata.row_group(index).column(contentIndex).total_uncompressed_size
        for index in range(parquet.num_row_groups)
    )
    hasDictionaryChunk = any(
        parquet.metadata.row_group(index).column(contentIndex).dictionary_page_offset is not None
        for index in range(parquet.num_row_groups)
    )
    dictionaryGuard = _ARROW_CONTENT_LOCK if largestContentChunk > _SERIAL_ARROW_CONTENT_BYTES else nullcontext()
    try:
        with dictionaryGuard:
            return _readDictionarySelectedContents(source, parquet, selectedIndexes)
    except _UnsupportedContentLayout:
        if largestContentChunk > _MAX_ARROW_CONTENT_BYTES and hasDictionaryChunk:
            return _readSelectedContentsDuckDb(source, selectedIndexes)

    contents: dict[int, str] = {}
    rowOffset = 0
    readGuard = _ARROW_CONTENT_LOCK if largestContentChunk > _SERIAL_ARROW_CONTENT_BYTES else nullcontext()
    with readGuard:
        for rowGroupIndex in range(parquet.num_row_groups):
            rowCount = parquet.metadata.row_group(rowGroupIndex).num_rows
            groupSelectedIndexes = {index for index in selectedIndexes if rowOffset <= index < rowOffset + rowCount}
            if not groupSelectedIndexes:
                rowOffset += rowCount
                continue

            batchOffset = rowOffset
            batches = parquet.iter_batches(
                batch_size=_CONTENT_BATCH_ROWS,
                row_groups=[rowGroupIndex],
                columns=["contentRaw"],
                use_threads=False,
            )
            for batch in batches:
                batchEnd = batchOffset + batch.num_rows
                localIndexes = sorted(
                    index - batchOffset for index in groupSelectedIndexes if batchOffset <= index < batchEnd
                )
                if localIndexes:
                    contentColumn = batch.column("contentRaw")
                    for localIndex in localIndexes:
                        content = contentColumn[localIndex].as_py()
                        if content is not None:
                            contents[batchOffset + localIndex] = content
                batchOffset = batchEnd
            rowOffset += rowCount
            pa.default_memory_pool().release_unused()
    return contents


def _readAffiliateRows(
    source: Path,
    code: str,
    nameToCode: dict[str, str],
    jurirToCode: dict[str, str],
) -> _AffiliateReadResult:
    """metadata 선필터 후 표가 있는 최신 계열회사 revision만 읽는다."""

    required = {"sectionLeaf", "contentRaw", "period", "rceptNo"}
    try:
        parquet = pq.ParquetFile(source, memory_map=False, pre_buffer=False)
        try:
            missing = sorted(required - set(parquet.schema_arrow.names))
            if missing:
                raise ValueError(f"panel 필수 컬럼 누락: {', '.join(missing)}")
            revisionIndexes = _readRevisionIndexes(parquet)
            if not revisionIndexes:
                return _AffiliateReadResult(frozenset())
            selectedContents = _readSelectedContents(
                source,
                parquet,
                {index for selectedIndexes in revisionIndexes.values() for index in selectedIndexes},
            )

            fallbackRevision: tuple[str, str] | None = None
            for (period, receiptNumber), selectedIndexes in sorted(
                revisionIndexes.items(),
                reverse=True,
            ):
                contents = [selectedContents[index] for index in selectedIndexes if index in selectedContents]
                tables = _parseRevisionTables(contents, code=code, source=source)
                if not tables:
                    continue

                resolvedCodes, unknownLegal, nameOnly, nameMismatch, hasCandidates = _resolveTableAffiliates(
                    tables,
                    nameToCode,
                    jurirToCode,
                )
                affiliateCodes = {code, *resolvedCodes}
                if len(affiliateCodes) > 1 or hasCandidates:
                    return _AffiliateReadResult(
                        frozenset((code, affiliateCode, period, receiptNumber) for affiliateCode in affiliateCodes),
                        unknownLegalRows=unknownLegal,
                        nameOnlyRows=nameOnly,
                        nameMismatchRows=nameMismatch,
                    )
                if fallbackRevision is None:
                    fallbackRevision = (period, receiptNumber)
            if fallbackRevision is not None:
                period, receiptNumber = fallbackRevision
                return _AffiliateReadResult(frozenset({(code, code, period, receiptNumber)}))
            return _AffiliateReadResult(frozenset())
        finally:
            parquet.close()
    except AffiliateDocsBuildError:
        raise
    except (pa.ArrowException, OSError, RuntimeError, ValueError, struct.error) as exc:
        raise AffiliateDocsBuildError(code, source, exc) from exc
    finally:
        pa.default_memory_pool().release_unused()


def _writeAtomic(frame: pl.DataFrame, outputPath: Path) -> None:
    outputPath.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporaryName = tempfile.mkstemp(
        prefix=f".{outputPath.stem}-",
        suffix=".tmp.parquet",
        dir=outputPath.parent,
    )
    os.close(descriptor)
    temporary = Path(temporaryName)
    try:
        frame.write_parquet(temporary, compression="zstd")
        parquet = pq.ParquetFile(temporary, memory_map=False, pre_buffer=False)
        try:
            actualColumns = parquet.schema_arrow.names
            actualRows = parquet.metadata.num_rows
        finally:
            parquet.close()
        if actualColumns != frame.columns or actualRows != frame.height:
            raise RuntimeError(
                "affiliate docs 임시 artifact 검증 실패: "
                f"rows={actualRows}/{frame.height}, "
                f"columns={actualColumns}/{frame.columns}"
            )
        with temporary.open("r+b") as written:
            os.fsync(written.fileno())
        os.replace(temporary, outputPath)
    except BaseException as primaryError:
        try:
            temporary.unlink(missing_ok=True)
        except BaseException as cleanupError:
            raise BaseExceptionGroup(
                "affiliate docs artifact write와 temp cleanup이 함께 실패했습니다",
                [primaryError, cleanupError],
            ) from primaryError
        raise


def _readPrior(outputPath: Path) -> pl.DataFrame:
    try:
        prior = pl.read_parquet(outputPath)
    except (pl.exceptions.PolarsError, OSError) as exc:
        raise RuntimeError(f"기존 affiliate docs artifact를 읽을 수 없습니다: {outputPath}") from exc
    validateAffiliateDocsArtifact(prior, str(outputPath))
    return prior.select(_MEMBERSHIP_SCHEMA.keys())


def _collectMembershipRows(
    targetCodes: list[str],
    sourceByCode: dict[str, Path],
    nameToCode: dict[str, str],
    jurirToCode: dict[str, str],
) -> _AffiliateReadResult:
    """회사 두 개까지만 rolling 제출해 full panel 순회를 bounded 병렬화한다."""

    targets = [(code, sourceByCode[code]) for code in targetCodes if code in sourceByCode]
    if not targets:
        return _AffiliateReadResult(frozenset())
    if len(targets) == 1:
        code, source = targets[0]
        return _readAffiliateRows(source, code, nameToCode, jurirToCode)

    rows: set[tuple[str, str, str, str]] = set()
    unknownLegalRows = 0
    nameOnlyRows = 0
    nameMismatchRows = 0
    nextTargetIndex = 0
    pending: dict[Future[_AffiliateReadResult], str] = {}
    with ThreadPoolExecutor(
        max_workers=min(_MAX_PANEL_WORKERS, len(targets)),
        thread_name_prefix="scan-affiliate",
    ) as executor:
        while nextTargetIndex < min(_MAX_PANEL_WORKERS, len(targets)):
            code, source = targets[nextTargetIndex]
            pending[executor.submit(_readAffiliateRows, source, code, nameToCode, jurirToCode)] = code
            nextTargetIndex += 1

        while pending:
            completed, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in completed:
                pending.pop(future)
                result = future.result()
                rows.update(result.rows)
                unknownLegalRows += result.unknownLegalRows
                nameOnlyRows += result.nameOnlyRows
                nameMismatchRows += result.nameMismatchRows
                if nextTargetIndex < len(targets):
                    code, source = targets[nextTargetIndex]
                    pending[executor.submit(_readAffiliateRows, source, code, nameToCode, jurirToCode)] = code
                    nextTargetIndex += 1
    return _AffiliateReadResult(
        frozenset(rows),
        unknownLegalRows=unknownLegalRows,
        nameOnlyRows=nameOnlyRows,
        nameMismatchRows=nameMismatchRows,
    )


def _buildOutput(
    memberships: pl.DataFrame,
    codeToName: dict[str, str],
    listingCodes: set[str],
) -> pl.DataFrame:
    if memberships.is_empty():
        return pl.DataFrame(schema=_OUTPUT_SCHEMA)
    memberships = memberships.unique(
        subset=["sourceStockCode", "affiliateStockCode"],
        keep="last",
        maintain_order=True,
    )
    codeToGroup = compileAffiliateGroups(memberships, codeToName, listingCodes)
    groupFrame = pl.DataFrame(
        {
            "affiliateStockCode": list(codeToGroup),
            "groupName": list(codeToGroup.values()),
        },
        schema={"affiliateStockCode": pl.Utf8, "groupName": pl.Utf8},
    )
    datasetAsOf = max(
        (receipt[:8] for receipt in memberships["sourceRceptNo"].to_list() if receipt and len(receipt) >= 8),
        default=max(memberships["sourcePeriod"].drop_nulls().to_list(), default=""),
    )
    return (
        memberships.join(groupFrame, on="affiliateStockCode", how="left")
        .with_columns(
            pl.lit(datasetAsOf).alias("datasetAsOf"),
            pl.lit(AFFILIATE_DOCS_SCHEMA_VERSION, dtype=pl.Int16).alias("schemaVersion"),
        )
        .select(_OUTPUT_SCHEMA.keys())
        .sort("sourceStockCode", "affiliateStockCode")
    )


@withMemoryBudget(limitMb=1000)
def buildAffiliateDocs(
    *,
    outputPath: str | Path | None = None,
    incremental: bool = False,
    changedCodes: Iterable[str] | None = None,
    removedCodes: Iterable[str] = (),
    verbose: bool = False,
) -> Path:
    """Panel 계열회사 표를 ``network/affiliateDocs.parquet``로 prebuild한다.

    Full 빌드는 모든 panel을 읽는다. Incremental 빌드는 명시된 변경 source를 기존
    artifact에서 교체하고 삭제 code를 source와 affiliate 양쪽에서 제거한 뒤 전체
    group label을 다시 계산한다.

    Capabilities:
        구형과 신형 panel을 bounded batch로 읽고 full 또는 incremental artifact를 발행한다.

    AIContext:
        공개 network graph가 전종목 raw panel을 runtime에 순회하지 않도록 ground truth를 준비한다.

    Guide:
        full은 전체 panel을 기준으로 재생성하고 incremental은 변경 source만 기존 membership과 교체한다.

    When:
        scan full prebuild 또는 panel 변경분이 있는 incremental prebuild 단계.

    How:
        metadata 선필터, 선택 content batch 파싱, 역색인 clustering, 임시 파일 교체 순서로 실행한다.

    Requires:
        panel parquet, KR listing, 출력 가능한 scan data directory.

    Args:
        outputPath: 출력 parquet 경로. None이면 scan network 기본 경로.
        incremental: 기존 artifact를 변경 회사 단위로 갱신할지 여부.
        changedCodes: 증분에서 다시 읽을 source 종목코드.
        removedCodes: source와 affiliate 양쪽에서 제거할 종목코드.
        verbose: 결과 행 수와 크기를 출력할지 여부.

    Returns:
        원자 발행된 affiliateDocs parquet 경로.

    Raises:
        RuntimeError: 증분 기준 artifact가 없을 때.
        ValueError: 증분 changedCodes가 명시되지 않았을 때.
        FileNotFoundError: 명시된 변경 panel source가 없을 때.
        AffiliateDocsBuildError: panel layout, table 또는 artifact가 손상됐을 때.

    Example:
        >>> buildAffiliateDocs(outputPath="scan/network/affiliateDocs.parquet")  # doctest: +SKIP

    SeeAlso:
        ``dartlab.scan.network.affiliates.compileAffiliateGroups`` · ``dartlab.scan.network.buildGraph``.
    """

    sourceDir = panelDir()
    destination = Path(outputPath) if outputPath is not None else scanDir() / "network" / "affiliateDocs.parquet"
    if incremental and not destination.exists():
        raise RuntimeError("affiliate docs 증분 기준 artifact 부재: PREBUILD_FULL=1이 필요합니다")

    changed = None if changedCodes is None else {str(code) for code in changedCodes}
    if incremental and changed is None:
        raise ValueError("incremental affiliate docs 빌드는 changedCodes를 명시해야 합니다")
    sourceByCode = {source.stem: source for source in sourceDir.glob("*.parquet")}
    missingChangedCodes = sorted((changed or set()) - set(sourceByCode))
    if incremental and missingChangedCodes:
        sample = ", ".join(missingChangedCodes[:10])
        remainder = len(missingChangedCodes) - min(10, len(missingChangedCodes))
        suffix = f" 외 {remainder}개" if remainder else ""
        raise FileNotFoundError(f"변경 panel source 누락: {sample}{suffix}")
    targetCodes = sorted(sourceByCode) if not incremental else sorted(changed or ())
    if not targetCodes and not incremental:
        raise FileNotFoundError(f"panel parquet 부재: {sourceDir}")

    nameToCode, codeToName, listingCodes, _ = loadListing()
    jurirToCode = _loadJurirStockMap()
    readResult = _collectMembershipRows(targetCodes, sourceByCode, nameToCode, jurirToCode)

    rebuilt = pl.DataFrame(
        sorted(readResult.rows),
        schema=_MEMBERSHIP_SCHEMA,
        orient="row",
    )
    if incremental:
        memberships = _readPrior(destination).filter(~pl.col("sourceStockCode").is_in(sorted(changed or ())))
        memberships = pl.concat([memberships, rebuilt], how="vertical_relaxed")
    else:
        memberships = rebuilt

    removed = sorted({str(code) for code in removedCodes})
    if removed:
        memberships = memberships.filter(
            ~pl.col("sourceStockCode").is_in(removed) & ~pl.col("affiliateStockCode").is_in(removed)
        )

    output = _buildOutput(memberships, codeToName, listingCodes)
    _writeAtomic(output, destination)

    if verbose:
        sizeMb = destination.stat().st_size / 1024 / 1024
        print(f"[affiliateDocs] {output.height:,}행, {sizeMb:.1f}MB -> {destination}")
        print(
            "[affiliateDocs] identity diagnostics: "
            f"unknownLegal={readResult.unknownLegalRows:,}, "
            f"nameOnly={readResult.nameOnlyRows:,}, "
            f"nameMismatch={readResult.nameMismatchRows:,}"
        )
    return destination
