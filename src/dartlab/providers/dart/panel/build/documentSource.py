"""DART panel의 디스크·메모리 zip 입력을 같은 계약으로 검증하고 decode한다."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

_RCEPT_RE = re.compile(r"^(\d{14})\.zip$", re.IGNORECASE)


class PanelBuildError(RuntimeError):
    """Panel source의 decode, parse, transform 또는 publish 실패."""

    def __init__(
        self,
        stage: str,
        source: str,
        cause: BaseException,
        *,
        receiptNumber: str | None = None,
    ) -> None:
        self.stage = stage
        self.source = source
        self.receiptNumber = receiptNumber
        receiptDetail = f", rceptNo={receiptNumber}" if receiptNumber else ""
        super().__init__(
            f"panel build failed: stage={stage}, source={source}{receiptDetail}: {type(cause).__name__}: {cause}"
        )


def _zipToXmls(archive: zipfile.ZipFile) -> list[str]:
    """열린 zip의 모든 XML을 이름순으로 decode한다.

    Args:
        archive: 경로 또는 BytesIO에서 연 ZipFile.

    Returns:
        XML member 이름순 decoded 문자열.

    Raises:
        UnicodeError: DART XML 인코딩을 판별할 수 없을 때.
        OSError: zip member를 읽을 수 없을 때.

    Example:
        >>> with zipfile.ZipFile(path) as archive:  # doctest: +SKIP
        ...     xmls = _zipToXmls(archive)
    """

    from .refScan.zipScanWorker import _decodeXmlBytes

    xmls: list[str] = []
    names = sorted(name for name in archive.namelist() if name.lower().endswith(".xml"))
    for name in names:
        with archive.open(name) as stream:
            xmls.append(_decodeXmlBytes(stream.read()))
    return xmls


def _readZip(path: Path) -> tuple[str, list[str]]:
    """로컬 zip을 접수번호와 XML 목록으로 읽는다.

    Args:
        path: 회사별 docs 폴더의 zip 경로.

    Returns:
        파일명에서 얻은 접수번호와 decoded XML 목록.

    Raises:
        PanelBuildError: zip 또는 XML member가 손상되거나 없을 때.

    Example:
        >>> _readZip(Path("20240514000001.zip"))  # doctest: +SKIP
    """

    match = _RCEPT_RE.match(path.name)
    receiptNumber = match.group(1) if match else path.stem
    try:
        with zipfile.ZipFile(path) as archive:
            xmls = _zipToXmls(archive)
    except (zipfile.BadZipFile, OSError, KeyError) as exc:
        raise PanelBuildError(
            "zip_read",
            str(path),
            exc,
            receiptNumber=receiptNumber,
        ) from exc
    if not xmls:
        cause = ValueError("zip에 XML member가 없습니다")
        raise PanelBuildError(
            "zip_schema",
            str(path),
            cause,
            receiptNumber=receiptNumber,
        ) from cause
    return receiptNumber, xmls


def _readZipBytes(raw: bytes, receiptNumber: str) -> tuple[str, list[str]]:
    """메모리 zip을 접수번호와 XML 목록으로 읽는다.

    Args:
        raw: DART document API가 반환한 zip bytes.
        receiptNumber: 파일명이 없는 입력의 명시적 접수번호.

    Returns:
        명시적 접수번호와 decoded XML 목록.

    Raises:
        PanelBuildError: 접수번호가 비거나 zip 또는 XML member가 잘못됐을 때.

    Example:
        >>> _readZipBytes(zipBytes, "20240514000001")  # doctest: +SKIP
    """

    if not receiptNumber:
        cause = ValueError("접수번호가 비어 있습니다")
        raise PanelBuildError("zip_identity", "memory", cause) from cause
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            xmls = _zipToXmls(archive)
    except (zipfile.BadZipFile, OSError, KeyError) as exc:
        raise PanelBuildError(
            "zip_read",
            "memory",
            exc,
            receiptNumber=receiptNumber,
        ) from exc
    if not xmls:
        cause = ValueError("zip에 XML member가 없습니다")
        raise PanelBuildError(
            "zip_schema",
            "memory",
            cause,
            receiptNumber=receiptNumber,
        ) from cause
    return receiptNumber, xmls


def _expandedZipBytes(source: Path | bytes, receiptNumber: str) -> int:
    """XML 해제 크기를 본문 materialization 없이 계산한다.

    Args:
        source: 로컬 zip 경로 또는 online zip bytes.
        receiptNumber: 오류 provenance용 접수번호.

    Returns:
        모든 XML member의 해제 후 byte 합.

    Raises:
        PanelBuildError: zip 또는 XML member가 손상되거나 없을 때.

    Example:
        >>> _expandedZipBytes(Path("20240514000001.zip"), "20240514000001")  # doctest: +SKIP
        1048576
    """

    try:
        handle = source if isinstance(source, Path) else io.BytesIO(source)
        with zipfile.ZipFile(handle) as archive:
            xmlInfos = [info for info in archive.infolist() if info.filename.lower().endswith(".xml")]
    except (zipfile.BadZipFile, OSError, KeyError) as exc:
        raise PanelBuildError(
            "zip_read",
            str(source) if isinstance(source, Path) else "memory",
            exc,
            receiptNumber=receiptNumber,
        ) from exc
    if not xmlInfos:
        cause = ValueError("zip에 XML member가 없습니다")
        raise PanelBuildError(
            "zip_schema",
            str(source) if isinstance(source, Path) else "memory",
            cause,
            receiptNumber=receiptNumber,
        ) from cause
    return sum(info.file_size for info in xmlInfos)


__all__ = ["PanelBuildError"]
