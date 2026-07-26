"""EDGAR panel builder — 합성 SEC text → 보드(16-col) 단일 artifact (data 0)."""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_filing_text_to_board(builtTicker) -> None:
    from dartlab.providers.edgar.panel.build.builder import filingTextToBoard

    from ..synthData import synthSubmissionTxt

    board = filingTextToBoard(synthSubmissionTxt(), ticker=builtTicker)
    assert board
    # 재무표 disclosureKey 앵커 (BS/IS 본표)
    anchored = {r["disclosureKey"] for r in board if r["disclosureKey"]}
    assert "BS" in anchored and "IS" in anchored
    # 서술 leaf 는 null key
    assert any(r["disclosureKey"] is None and r["leafType"] == "text" for r in board)


def test_build_edgar_panel_artifacts(builtTicker) -> None:
    from dartlab.providers.dart.panel.schema import PANEL_SCHEMA
    from dartlab.providers.edgar.panel.build.builder import buildEdgarPanel, panelPath

    from ..synthData import synthSubmissionTxt

    stats = buildEdgarPanel(builtTicker, [{"text": synthSubmissionTxt()}])
    assert stats["rows"] > 0 and stats["filings"] == 1

    board = pl.read_parquet(str(panelPath(builtTicker)))
    assert list(board.columns) == list(PANEL_SCHEMA.keys()), "보드 16-col 계약 위반"
    assert board.schema == PANEL_SCHEMA
    assert board["period"].unique().to_list() == ["2024Q4"]
    assert board.filter(pl.col("corp") == "TEST").height == board.height


def test_build_edgar_panel_native_payload_read(builtTicker) -> None:
    """소문자 native 는 별도 artifact 없이 edgar/panel contentRaw payload 에서 read-time 분해."""
    from dartlab.providers.edgar.panel.build.builder import buildEdgarPanel, panelPath
    from dartlab.providers.edgar.panel.native import decodeNativeCellsPayload, readNative

    from ..synthData import synthSubmissionTxt

    buildEdgarPanel(builtTicker, [{"text": synthSubmissionTxt()}])
    board = pl.read_parquet(str(panelPath(builtTicker)))
    payloadRows = [cell for raw in board["contentRaw"].to_list() for cell in decodeNativeCellsPayload(raw)]
    assert payloadRows
    assert {r["statement"] for r in payloadRows} >= {"BS", "IS"}

    isWide = readNative(builtTicker, statement="is", freq="year")
    bsWide = readNative(builtTicker, statement="bs", freq="year")
    assert isWide is not None and not isWide.is_empty()
    assert bsWide is not None and not bsWide.is_empty()
    assert "2024" in isWide.columns and "2024" in bsWide.columns


def test_resolve_cik(builtTicker) -> None:
    from dartlab.providers.edgar.panel.build.builder import resolveCikForTicker

    assert resolveCikForTicker("TEST") == "0000012345"
    assert resolveCikForTicker("test") == "0000012345"  # 대소문자 무관
    assert resolveCikForTicker("NOPE") is None


def test_append_filing_texts_to_panel_incremental(builtTicker, tmp_path) -> None:
    """appendFilingTextsToPanel — 신규 accession 만 기존 artifact 에 append + 정정 idempotent.

    회귀 가드: per-filing 증분이 전체 history 재독 없이 동작하고, 같은 accession 재-append 가
    행을 늘리지 않아야(중복 0) EDGAR raw 폐기 전략과 정합.
    """
    from dartlab.providers.edgar.panel.build.builder import (
        appendFilingTextsToPanel,
        buildEdgarPanel,
        existingAccessions,
        panelPath,
    )

    from ..synthData import synthSubmissionTxt

    # 초기 빌드 (1 filing)
    buildEdgarPanel(builtTicker, [{"text": synthSubmissionTxt()}], overwrite=True)
    acc0 = existingAccessions(builtTicker)
    rows0 = pl.read_parquet(str(panelPath(builtTicker))).height
    assert len(acc0) == 1 and rows0 > 0

    # 신규 filing(다른 accession + period) append
    record2 = {
        "text": synthSubmissionTxt(accession="0000012345-25-000002", periodEnd="20231231"),
        "accession_no": "0000012345-25-000002",
    }
    stat = appendFilingTextsToPanel(builtTicker, [record2])
    assert stat["appended"] == 1
    acc1 = existingAccessions(builtTicker)
    rows1 = pl.read_parquet(str(panelPath(builtTicker))).height
    assert len(acc1) == 2 and rows1 > rows0  # 기존 보존 + 신규 추가

    # 같은 accession 재-append → 행 불변(정정 idempotent, 중복 0)
    appendFilingTextsToPanel(builtTicker, [record2])
    rows2 = pl.read_parquet(str(panelPath(builtTicker))).height
    assert rows2 == rows1


def test_list_recent_filings_parse() -> None:
    """listRecentFilings — master.idx 파싱(form 필터·accession·txt_url) — 네트워크 mock."""
    from dartlab.gather.original.edgar import collect

    idx = (
        "Description: Master Index\n"
        "CIK|Company Name|Form Type|Date Filed|Filename\n"
        "--------------------------------------------------------\n"
        "320193|APPLE INC|10-Q|2026-06-03|edgar/data/320193/0000320193-26-000077.txt\n"
        "1234|FOO CORP|8-K|2026-06-03|edgar/data/1234/0001234-26-000001.txt\n"
    )

    class _Resp:
        status_code = 200
        text = idx

        def raise_for_status(self):
            return None

    import httpx

    orig = httpx.get
    httpx.get = lambda *a, **k: _Resp()  # noqa: E731
    try:
        rows = collect.listRecentFilings(["20260603"], forms=["10-Q", "10-K"])
    finally:
        httpx.get = orig

    assert len(rows) == 1  # 8-K 제외
    r = rows[0]
    assert r["cik"] == "0000320193" and r["accession_no"] == "0000320193-26-000077"
    assert r["txt_url"].endswith("edgar/data/320193/0000320193-26-000077.txt")


def test_merge_keeping_schema_recasts_dtype_drift(tmp_path) -> None:
    """_mergeKeepingSchema — 옛 parquet 의 dtype drift 를 schema 계약으로 재캐스트 + 기존 보존."""
    from dartlab.providers.dart.panel.schema import PANEL_SCHEMA
    from dartlab.providers.edgar.panel.build.builder import _mergeKeepingSchema, _rowsToDf

    base = {k: None for k in PANEL_SCHEMA}
    old = {**base, "rceptNo": "OLD-1", "period": "2024Q4", "blockOrder": 5, "corp": "X"}
    # 기존 parquet 에 dtype drift 주입(blockOrder UInt32 → Int64)
    existing = _rowsToDf([old], PANEL_SCHEMA).with_columns(pl.col("blockOrder").cast(pl.Int64))
    target = tmp_path / "X.parquet"
    existing.write_parquet(str(target))

    new = {**base, "rceptNo": "NEW-1", "period": "2025Q1", "blockOrder": 7, "corp": "X"}
    merged = _mergeKeepingSchema(target, [new], PANEL_SCHEMA, {"NEW-1"})

    assert merged.schema == PANEL_SCHEMA  # drift 가 계약 dtype 으로 복구
    assert set(merged["rceptNo"].to_list()) == {"OLD-1", "NEW-1"}  # 기존 보존 + 신규


def test_merge_keeping_schema_warns_on_silent_cast_loss(tmp_path, caplog) -> None:
    """strict=False 재캐스트가 비-null 값을 *조용히* null 로 만들면(오버플로) 경고로 관측화(finding C)."""
    import logging

    from dartlab.providers.dart.panel.schema import PANEL_SCHEMA
    from dartlab.providers.edgar.panel.build.builder import _mergeKeepingSchema, _rowsToDf

    base = {k: None for k in PANEL_SCHEMA}
    # 기존 parquet 의 blockOrder(UInt32) 에 UInt32 max 초과 Int64 주입 → cast strict=False 시 null
    existing = _rowsToDf([{**base, "rceptNo": "OLD-1", "period": "2024Q4", "corp": "X"}], PANEL_SCHEMA).with_columns(
        pl.Series("blockOrder", [5_000_000_000], dtype=pl.Int64)
    )
    target = tmp_path / "X.parquet"
    existing.write_parquet(str(target))

    new = {**base, "rceptNo": "NEW-1", "period": "2025Q1", "blockOrder": 7, "corp": "X"}
    with caplog.at_level(logging.WARNING):
        merged = _mergeKeepingSchema(target, [new], PANEL_SCHEMA, {"NEW-1"})

    assert merged.filter(pl.col("rceptNo") == "OLD-1")["blockOrder"].to_list() == [None]  # 오버플로 → null
    assert any("비-null→null" in r.message for r in caplog.records)  # 손실 경고 남김


def test_build_edgar_panel_all(builtTicker) -> None:
    """buildEdgarPanelAll — ticker별 text records dict."""
    from dartlab.providers.edgar.panel.build.builder import buildEdgarPanelAll

    from ..synthData import synthSubmissionTxt

    res = buildEdgarPanelAll({"TEST": [{"text": synthSubmissionTxt()}]})
    assert res["TEST"]["rows"] > 0
