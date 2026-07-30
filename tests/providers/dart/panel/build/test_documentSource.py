"""``providers/dart/panel/build/documentSource.py``의 zip 입력 계약 mirror."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest


def _zipBytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("b.xml", "<DOCUMENT>B</DOCUMENT>")
        archive.writestr("a.xml", "<DOCUMENT>A</DOCUMENT>")
    return buffer.getvalue()


def test_disk_and_memory_zip_sources_are_identical(tmp_path: Path) -> None:
    """경로와 bytes 입력은 같은 접수번호·XML 순서·해제 크기를 만든다."""

    from dartlab.providers.dart.panel.build.documentSource import (
        _expandedZipBytes,
        _readZip,
        _readZipBytes,
    )

    path = tmp_path / "20240514000001.zip"
    path.write_bytes(_zipBytes())

    disk = _readZip(path)
    memory = _readZipBytes(path.read_bytes(), path.stem)
    assert disk == memory
    assert disk[1] == ["<DOCUMENT>A</DOCUMENT>", "<DOCUMENT>B</DOCUMENT>"]
    assert _expandedZipBytes(path, path.stem) == _expandedZipBytes(path.read_bytes(), path.stem)


def test_corrupt_zip_preserves_typed_provenance() -> None:
    """손상 zip은 빈 성공값이 아니라 stage와 receipt가 있는 typed error다."""

    from dartlab.providers.dart.panel.build.documentSource import PanelBuildError, _readZipBytes

    with pytest.raises(PanelBuildError) as captured:
        _readZipBytes(b"broken", "20240514000001")

    assert captured.value.stage == "zip_read"
    assert captured.value.receiptNumber == "20240514000001"
