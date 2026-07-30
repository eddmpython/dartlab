"""Legacy panel의 대형 Parquet dictionary에서 선택 content만 안전하게 읽는다."""

from __future__ import annotations

import struct
from pathlib import Path
from typing import BinaryIO

import pyarrow.parquet as pq

_MAX_CONTENT_VALUE_BYTES = 128 * 1024 * 1024
_PAGE_HEADER_SCAN_BYTES = 4096
_ZSTD_FRAME_MAGIC = b"\x28\xb5\x2f\xfd"


class _UnsupportedContentLayout(RuntimeError):
    """선택 dictionary streaming이 지원하지 않는 parquet layout."""


def _readVarint(data: bytes, offset: int) -> tuple[int, int]:
    """Parquet hybrid stream의 unsigned varint 하나를 읽는다."""

    value = 0
    shift = 0
    while offset < len(data):
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, offset
        shift += 7
        if shift > 63:
            break
    raise ValueError("contentRaw dictionary index varint가 손상됐습니다")


def _decodeHybrid(data: bytes, bitWidth: int, count: int) -> list[int]:
    """Parquet RLE/bit-packed hybrid 정수를 bounded buffer에서 해독한다."""

    if bitWidth < 0 or bitWidth > 32:
        raise ValueError(f"contentRaw dictionary bit width가 잘못됐습니다: {bitWidth}")
    values: list[int] = []
    offset = 0
    byteWidth = (bitWidth + 7) // 8
    mask = (1 << bitWidth) - 1
    while len(values) < count:
        header, offset = _readVarint(data, offset)
        if header == 0:
            raise ValueError("contentRaw dictionary index run 길이가 0입니다")
        if header & 1 == 0:
            runLength = header >> 1
            end = offset + byteWidth
            if end > len(data):
                raise ValueError("contentRaw dictionary RLE run이 잘렸습니다")
            value = int.from_bytes(data[offset:end], "little")
            offset = end
            values.extend([value] * min(runLength, count - len(values)))
            continue

        runLength = (header >> 1) * 8
        packedBytes = (header >> 1) * bitWidth
        end = offset + packedBytes
        if end > len(data):
            raise ValueError("contentRaw dictionary bit-packed run이 잘렸습니다")
        packed = int.from_bytes(data[offset:end], "little")
        offset = end
        values.extend((packed >> (index * bitWidth)) & mask for index in range(min(runLength, count - len(values))))
    return values


def _zstdPayloadOffset(chunk: bytes, label: str) -> int:
    """Thrift page header 다음 zstd frame 시작 위치를 찾는다."""

    offset = chunk[:_PAGE_HEADER_SCAN_BYTES].find(_ZSTD_FRAME_MAGIC)
    if offset < 0:
        raise _UnsupportedContentLayout(f"{label} zstd frame을 찾을 수 없습니다")
    return offset


def _readExact(stream: BinaryIO, size: int, label: str) -> bytes:
    """압축 stream에서 요청한 byte 수를 전부 읽거나 손상을 보고한다."""

    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            raise ValueError(f"{label}가 잘렸습니다")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _readDictionaryRowGroupContents(
    source: Path,
    parquet: pq.ParquetFile,
    rowGroupIndex: int,
    selectedIndexes: set[int],
) -> dict[int, str]:
    """한 row group의 dictionary page를 streaming 해 선택 content만 보존한다."""

    contentIndex = parquet.schema_arrow.names.index("contentRaw")
    columnSchema = parquet.schema.column(contentIndex)
    rowGroup = parquet.metadata.row_group(rowGroupIndex)
    column = rowGroup.column(contentIndex)
    if (
        columnSchema.max_definition_level != 1
        or columnSchema.max_repetition_level != 0
        or columnSchema.physical_type != "BYTE_ARRAY"
        or column.compression != "ZSTD"
        or column.dictionary_page_offset is None
        or "RLE_DICTIONARY" not in column.encodings
    ):
        raise _UnsupportedContentLayout("contentRaw이 optional ZSTD dictionary layout이 아닙니다")
    if not selectedIndexes:
        return {}
    if min(selectedIndexes) < 0 or max(selectedIndexes) >= rowGroup.num_rows:
        raise ValueError("선택 contentRaw 행 번호가 parquet 범위를 벗어났습니다")

    chunkEnd = column.dictionary_page_offset + column.total_compressed_size
    with source.open("rb") as stream:
        stream.seek(column.dictionary_page_offset)
        dictionaryHeader = stream.read(
            min(_PAGE_HEADER_SCAN_BYTES, column.data_page_offset - column.dictionary_page_offset)
        )
        dictionaryPayloadOffset = _zstdPayloadOffset(dictionaryHeader, "dictionary page")
        stream.seek(column.data_page_offset)
        dataChunk = stream.read(chunkEnd - column.data_page_offset)

    dataPayloadOffset = _zstdPayloadOffset(dataChunk, "data page")
    try:
        import zstandard
    except ImportError as exc:
        raise RuntimeError("대형 panel content streaming에 zstandard가 필요합니다") from exc

    decoder = zstandard.ZstdDecompressor()
    dataFrame = dataChunk[dataPayloadOffset:]
    try:
        dataSize = zstandard.frame_content_size(dataFrame)
    except zstandard.ZstdError as exc:
        raise ValueError("contentRaw dictionary index frame header가 손상됐습니다") from exc
    maxDataBytes = max(64 * 1024, rowGroup.num_rows * 8 + 64 * 1024)
    if dataSize in {zstandard.CONTENTSIZE_UNKNOWN, zstandard.CONTENTSIZE_ERROR} or dataSize > maxDataBytes:
        raise ValueError(f"contentRaw dictionary index page 크기가 비정상입니다: {dataSize}/{maxDataBytes}")
    try:
        dataDecoder = decoder.decompressobj()
        data = dataDecoder.decompress(dataFrame)
    except zstandard.ZstdError as exc:
        raise ValueError("contentRaw dictionary index page 압축이 손상됐습니다") from exc
    if not dataDecoder.eof or dataDecoder.unused_data:
        raise _UnsupportedContentLayout("contentRaw data page가 단일 zstd frame이 아닙니다")
    if len(data) < 6:
        raise ValueError("contentRaw dictionary data page가 너무 짧습니다")

    definitionLength = struct.unpack_from("<I", data, 0)[0]
    definitionEnd = 4 + definitionLength
    if definitionEnd >= len(data):
        raise ValueError("contentRaw definition level stream이 손상됐습니다")
    definitions = _decodeHybrid(data[4:definitionEnd], 1, column.num_values)
    dictionaryBitWidth = data[definitionEnd]
    definedCount = sum(definitions)
    dictionaryIds = _decodeHybrid(
        data[definitionEnd + 1 :],
        dictionaryBitWidth,
        definedCount,
    )

    rowDictionaryIds: dict[int, int] = {}
    definedIndex = 0
    for rowIndex, isDefined in enumerate(definitions):
        if not isDefined:
            continue
        if rowIndex in selectedIndexes:
            rowDictionaryIds[rowIndex] = dictionaryIds[definedIndex]
        definedIndex += 1
    if not rowDictionaryIds:
        return {}

    selectedDictionaryIds = set(rowDictionaryIds.values())
    invalidDictionaryIds = {
        dictionaryId for dictionaryId in selectedDictionaryIds if dictionaryId < 0 or dictionaryId >= rowGroup.num_rows
    }
    if invalidDictionaryIds:
        raise ValueError(f"contentRaw dictionary id 범위 오류: {sorted(invalidDictionaryIds)[:5]}")
    selectedValues: dict[int, str] = {}
    decodedBytes = 0
    with source.open("rb") as compressed:
        compressed.seek(column.dictionary_page_offset + dictionaryPayloadOffset)
        try:
            with decoder.stream_reader(compressed, read_across_frames=False) as dictionary:
                for valueId in range(max(selectedDictionaryIds) + 1):
                    lengthBytes = _readExact(dictionary, 4, "contentRaw dictionary length")
                    length = struct.unpack("<I", lengthBytes)[0]
                    decodedBytes += 4 + length
                    if length > _MAX_CONTENT_VALUE_BYTES or decodedBytes > column.total_uncompressed_size:
                        raise ValueError(
                            "contentRaw dictionary value 크기가 비정상입니다: "
                            f"value={length}, decoded={decodedBytes}, "
                            f"column={column.total_uncompressed_size}"
                        )
                    value = _readExact(dictionary, length, "contentRaw dictionary value")
                    if valueId in selectedDictionaryIds:
                        selectedValues[valueId] = value.decode("utf-8")
        except zstandard.ZstdError as exc:
            raise ValueError("contentRaw dictionary page 압축이 손상됐습니다") from exc
    missingDictionaryIds = selectedDictionaryIds - set(selectedValues)
    if missingDictionaryIds:
        raise ValueError(f"contentRaw dictionary id 누락: {sorted(missingDictionaryIds)[:5]}")
    return {rowIndex: selectedValues[dictionaryId] for rowIndex, dictionaryId in rowDictionaryIds.items()}


def _readDictionarySelectedContents(
    source: Path,
    parquet: pq.ParquetFile,
    selectedIndexes: set[int],
) -> dict[int, str]:
    """구형 대형 dictionary row group들을 streaming 해 선택 content만 합친다."""

    contents: dict[int, str] = {}
    rowOffset = 0
    for rowGroupIndex in range(parquet.num_row_groups):
        rowCount = parquet.metadata.row_group(rowGroupIndex).num_rows
        localIndexes = {index - rowOffset for index in selectedIndexes if rowOffset <= index < rowOffset + rowCount}
        if localIndexes:
            selected = _readDictionaryRowGroupContents(
                source,
                parquet,
                rowGroupIndex,
                localIndexes,
            )
            contents.update({rowOffset + localIndex: content for localIndex, content in selected.items()})
        rowOffset += rowCount
    return contents
