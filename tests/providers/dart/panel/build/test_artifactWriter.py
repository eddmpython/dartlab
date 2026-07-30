"""Panel parquet의 bounded row-group 저장 계약 회귀."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import pytest


def _panelRow(
    index: int,
    *,
    receiptNumber: str = "20250319000001",
    content: str | None = None,
    period: str = "2024Q4",
) -> dict[str, object]:
    return {
        "chapter": "I",
        "sectionLeaf": f"section-{index}",
        "sectionPath": f"I\u001fsection-{index}",
        "blockLeaf": "",
        "xbrlClass": None,
        "xbrlMatched": False,
        "xbrlMatchScore": 0.0,
        "atocId": None,
        "aassocnote": None,
        "blockOrder": index,
        "contentRaw": content or f"<P>{index}</P>",
        "period": period,
        "corp": "000001",
        "rceptNo": receiptNumber,
        "disclosureKey": None,
    }


def test_company_panel_uses_bounded_row_groups(tmp_path: Path) -> None:
    from dartlab.providers.dart.build.saver import _ROW_GROUP_SIZE
    from dartlab.providers.dart.panel.build.artifactWriter import PanelArtifactAssembler
    from dartlab.providers.dart.panel.build.builder import _finalizePeriodRows

    rows = [_panelRow(index) for index in range(_ROW_GROUP_SIZE + 1)]
    destination = tmp_path / "000001.parquet"
    with PanelArtifactAssembler(destination) as assembler:
        assembler.add(
            _finalizePeriodRows(rows),
            period="2024Q4",
            receiptNumber="20250319000001",
        )
        assembler.commit(merge=False, overwrite=True)

    metadata = pq.read_metadata(destination)
    assert metadata.num_row_groups == 2
    assert max(metadata.row_group(index).num_rows for index in range(metadata.num_row_groups)) <= _ROW_GROUP_SIZE


def test_company_panel_creates_destination_parent_before_lock(tmp_path: Path) -> None:
    from dartlab.providers.dart.panel.build.artifactWriter import PanelArtifactAssembler
    from dartlab.providers.dart.panel.build.builder import _finalizePeriodRows

    destination = tmp_path / "new-panel-root" / "000001.parquet"
    with PanelArtifactAssembler(destination) as assembler:
        assembler.add(
            _finalizePeriodRows([_panelRow(0)]),
            period="2024Q4",
            receiptNumber="20250319000001",
        )
        assembler.commit(merge=False, overwrite=True)

    assert destination.is_file()
    assert pl.read_parquet(destination).height == 1


def test_company_panel_never_memory_maps_compressed_stages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """자식 stage 검증과 최종 조립은 Windows mmap 정지를 피한다."""

    from dartlab.providers.dart.panel.build import artifactWriter
    from dartlab.providers.dart.panel.build.builder import _finalizePeriodRows

    original = artifactWriter.pq.ParquetFile
    memoryMapOptions: list[bool | None] = []

    def openParquet(*args: object, **kwargs: object) -> pq.ParquetFile:
        memoryMapOptions.append(kwargs.get("memory_map"))  # type: ignore[arg-type]
        return original(*args, **kwargs)

    monkeypatch.setattr(artifactWriter.pq, "ParquetFile", openParquet)
    destination = tmp_path / "000001.parquet"
    with artifactWriter.PanelArtifactAssembler(destination) as assembler:
        stage = assembler.stageRoot / "child-stage.parquet"
        _finalizePeriodRows([_panelRow(0)]).write_parquet(stage)
        assembler.registerStage(
            stage,
            period="2024Q4",
            receiptNumber="20250319000001",
            sequence=0,
        )
        assembler.commit(merge=False, overwrite=True)

    assert memoryMapOptions
    assert set(memoryMapOptions) == {False}


def test_document_stage_is_atomic_and_fully_readable(tmp_path: Path) -> None:
    """자식 stage는 fsync와 footer 검증 뒤 원자 발행되고 모든 data page를 읽을 수 있다."""

    from dartlab.providers.dart.panel.build.artifactWriter import writePanelStage
    from dartlab.providers.dart.panel.build.builder import _finalizePeriodRows

    frame = _finalizePeriodRows([_panelRow(index) for index in range(3)])
    stage = tmp_path / "document-00000000-00.parquet"

    assert writePanelStage(frame, stage) == 3
    assert stage.is_file()
    assert not list(tmp_path.glob(".*.tmp"))
    with pq.ParquetFile(stage, memory_map=False, pre_buffer=False) as parquet:
        restored = parquet.read(use_threads=False)
    assert restored.num_rows == 3
    assert restored.schema.equals(frame.to_arrow().schema)


def test_document_stage_corruption_never_becomes_visible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """완독할 수 없는 임시 parquet는 최종 stage로 발행되지 않는다."""

    from dartlab.providers.dart.panel.build import artifactWriter
    from dartlab.providers.dart.panel.build.builder import _finalizePeriodRows

    def writeCorrupt(_table: object, where: Any, **_kwargs: Any) -> None:
        Path(where).write_bytes(b"PAR1broken")

    monkeypatch.setattr(artifactWriter.pq, "write_table", writeCorrupt)
    stage = tmp_path / "document-00000000-00.parquet"
    with pytest.raises(pa.ArrowInvalid):
        artifactWriter.writePanelStage(
            _finalizePeriodRows([_panelRow(0)]),
            stage,
        )

    assert not stage.exists()
    assert not list(tmp_path.glob(".*.tmp"))


def test_company_panel_rejects_noncanonical_stage_schema(tmp_path: Path) -> None:
    from dartlab.providers.dart.panel.build.artifactWriter import (
        PanelArtifactAssembler,
        PanelArtifactLayoutError,
    )
    from dartlab.providers.dart.panel.build.builder import _finalizePeriodRows

    wrong = _finalizePeriodRows([_panelRow(0)]).with_columns(pl.col("blockOrder").cast(pl.Int64))
    with (
        PanelArtifactAssembler(tmp_path / "000001.parquet") as assembler,
        pytest.raises(PanelArtifactLayoutError, match="PANEL_SCHEMA"),
    ):
        assembler.add(
            wrong,
            period="2024Q4",
            receiptNumber="20250319000001",
        )


def _zipBytes(label: str, *, empty: bool = False) -> bytes:
    content = "" if empty else f"<SECTION-1><TITLE>사업의 내용</TITLE><P>{label}</P></SECTION-1>"
    xml = f"<DOCUMENT>{content}</DOCUMENT>"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("report.xml", xml.encode("utf-8"))
    return buffer.getvalue()


def _loadRef() -> pl.DataFrame:
    from dartlab.providers.dart.panel.build.builder import panelXbrlRefPath

    return pl.read_parquet(panelXbrlRefPath())


def test_documents_keep_receipt_provenance_isolated(tmp_path: Path) -> None:
    from dartlab.providers.dart.panel.build import builder

    builder.buildPanelFromStream(
        "000001",
        [
            ("20250319000001", _zipBytes("A")),
            ("20250320000002", _zipBytes("B")),
        ],
        refDf=_loadRef(),
        outBaseDir=tmp_path,
        overwrite=True,
        verbose=False,
    )

    result = pl.read_parquet(tmp_path / "000001.parquet")
    assert result["rceptNo"].unique(maintain_order=True).to_list() == [
        "20250319000001",
        "20250320000002",
    ]
    contents = result["contentRaw"].to_list()
    assert any("<P>A</P>" in content for content in contents)
    assert any("<P>B</P>" in content for content in contents)


def test_receipt_upsert_matches_full_build_and_is_idempotent(tmp_path: Path) -> None:
    from dartlab.providers.dart.panel.build import builder

    incrementalDir = tmp_path / "incremental"
    fullDir = tmp_path / "full"
    common = {"refDf": _loadRef(), "overwrite": True, "verbose": False}
    first = ("20250319000001", _zipBytes("A"))
    second = ("20250320000002", _zipBytes("B"))

    builder.buildPanelFromStream(
        "000001",
        [first],
        outBaseDir=incrementalDir,
        **common,
    )
    builder.buildPanelFromStream(
        "000001",
        [second],
        outBaseDir=incrementalDir,
        **common,
    )
    builder.buildPanelFromStream(
        "000001",
        [second],
        outBaseDir=incrementalDir,
        **common,
    )
    builder.buildPanelFromStream(
        "000001",
        [first, second],
        outBaseDir=fullDir,
        **common,
    )

    incremental = pl.read_parquet(incrementalDir / "000001.parquet")
    full = pl.read_parquet(fullDir / "000001.parquet")
    assert incremental.equals(full)
    assert incremental["rceptNo"].unique(maintain_order=True).to_list() == [
        "20250319000001",
        "20250320000002",
    ]


def test_corrupt_stream_preserves_existing_artifact(
    tmp_path: Path,
) -> None:
    from dartlab.providers.dart.panel.build import builder

    destination = tmp_path / "000001.parquet"
    destination.write_bytes(b"existing")

    with pytest.raises(builder.PanelBuildError, match="zip_read"):
        builder.buildPanelFromStream(
            "000001",
            [("20250319000001", b"not-a-zip")],
            refDf=pl.read_parquet(builder.panelXbrlRefPath()),
            outBaseDir=tmp_path,
        )

    assert destination.read_bytes() == b"existing"
    assert not list(tmp_path.glob("*.tmp"))


def test_changed_to_empty_removes_only_matching_receipt(tmp_path: Path) -> None:
    from dartlab.providers.dart.panel.build import builder

    common = {
        "refDf": _loadRef(),
        "outBaseDir": tmp_path,
        "overwrite": True,
        "verbose": False,
    }
    builder.buildPanelFromStream(
        "000001",
        [
            ("20250319000001", _zipBytes("A")),
            ("20250320000002", _zipBytes("B")),
        ],
        **common,
    )
    builder.buildPanelFromStream(
        "000001",
        [("20250319000001", _zipBytes("empty", empty=True))],
        **common,
    )

    result = pl.read_parquet(tmp_path / "000001.parquet")
    assert result["rceptNo"].unique().to_list() == ["20250320000002"]

    builder.buildPanelFromStream(
        "000001",
        [("20250320000002", _zipBytes("empty", empty=True))],
        **common,
    )
    empty = pl.read_parquet(tmp_path / "000001.parquet")
    assert empty.is_empty()
    assert empty.columns == list(builder.PANEL_SCHEMA)
