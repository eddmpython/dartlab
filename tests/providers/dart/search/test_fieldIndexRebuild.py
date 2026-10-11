"""mirror smoke — dart/search/fieldIndexRebuild.py (split helper).

분할 helper 모듈의 임포트 가능성 + 룰 7 mirror 슬롯 충족.
"""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.unit


def test_import() -> None:
    import dartlab.providers.dart.search.fieldIndexRebuild as mod

    assert mod is not None


def test_write_index_manifest_callable() -> None:
    from dartlab.providers.dart.search.fieldIndexRebuild import writeIndexManifest

    assert callable(writeIndexManifest)


def test_manifest_meta_read_is_streamed_and_canary_text_is_bounded(tmp_path, monkeypatch) -> None:
    import polars as pl

    from dartlab.providers.dart.search.fieldIndexRebuild import _readManifestMeta

    path = tmp_path / "main_meta.parquet"
    pl.DataFrame(
        {
            "source": ["allFilings"],
            "text": ["긴 본문" * 1000],
            "evidenceText": ["더 긴 증거 본문" * 1000],
        }
    ).write_parquet(path)

    def _eagerReadForbidden(*args, **kwargs):
        raise AssertionError("manifest generation must not eagerly read segment metadata")

    monkeypatch.setattr(pl, "read_parquet", _eagerReadForbidden)
    meta = _readManifestMeta(path)

    assert meta.columns == ["source", "text"]
    assert len(meta.item(0, "text")) == 120


def test_rebuild_main_from_catalog_callable() -> None:
    from dartlab.providers.dart.search.fieldIndexRebuild import rebuildMainFromCatalog

    assert callable(rebuildMainFromCatalog)


def test_write_index_manifest_includes_artifact_canary_pack(tmp_path) -> None:
    from dartlab.providers.dart.search.fieldIndex import buildContentSegment
    from dartlab.providers.dart.search.fieldIndexRebuild import saveSegmentWithSidecar, writeIndexManifest

    idx, meta = buildContentSegment(
        [
            {
                "section_content": "유상증자 자금조달 계획",
                "rcept_no": "20260615000001",
                "section_order": 0,
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "stock_code": "005930",
                "rcept_dt": "20260615",
                "report_nm": "주요사항보고서",
                "section_title": "",
                "source": "allFilings",
                "sourceRef": "dart:allFilings:20260615000001#section=0",
            }
        ],
        showProgress=False,
    )
    saveSegmentWithSidecar(idx, meta, "main", tmp_path)
    (tmp_path / "source_manifest_set.json").write_text(
        json.dumps(
            {
                "schemaVersion": "searchSourceManifestSet.v1",
                "sourceManifestSetId": "abc123",
                "expectedSources": ["allFilings"],
                "combinedCatalogRows": 1,
                "combinedCatalogSha256": "hash",
                "sources": [
                    {
                        "source": "allFilings",
                        "dataAsOf": "20260615",
                        "snapshotScope": "full",
                        "totalRows": 1,
                        "catalogRows": 1,
                        "manifestSha256": "manifest-hash",
                        "catalogSha256": "catalog-hash",
                        "producer": "test",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    import polars as pl

    pl.DataFrame(
        [
            {
                "corpName": "삼성전자",
                "stockCode": "005930",
                "grade": "AA",
                "weakAxis": "inventory",
                "dataAsOf": "20260616",
                "neighborsJson": "[]",
            }
        ]
    ).write_parquet(tmp_path / "entityGraphCatalog.parquet")
    pl.DataFrame(
        [
            {
                "source": "allFilings",
                "sourceRef": "dart:allFilings:20260615000001#section=0",
                "text": "유상증자",
            }
        ]
    ).write_parquet(tmp_path / "catalog_snapshot.parquet")

    manifest = writeIndexManifest(tmp_path, tier="full", buildCommand="test")

    assert manifest["canaryPackVersion"] == "artifact-source-v3"
    assert manifest["sourceCanaryPack"][0]["expectedSource"] == "allFilings"
    assert manifest["sourceCanaryPack"][0]["expectedSourceRef"] == "dart:allFilings:20260615000001#section=0"
    assert manifest["sourceCanaryPack"][-1]["target"] == "noAnswer"
    assert "catalog_snapshot.parquet" in manifest["requiredFiles"]
    assert "catalog_snapshot.parquet" in manifest["fileHashes"]
    assert "source_manifest_set.json" in manifest["requiredFiles"]
    assert "source_manifest_set.json" in manifest["fileHashes"]
    assert manifest["sourceManifestSetId"] == "abc123"
    assert manifest["sourceManifestSet"]["sources"][0]["source"] == "allFilings"
    assert "entityGraphCatalog.parquet" in manifest["requiredFiles"]
    assert "entityGraphCatalog.parquet" in manifest["fileHashes"]
    assert manifest["entityGraphCatalog"]["schemaVersion"] == "searchEntityGraphCatalog.v1"
    assert manifest["entityGraphCatalog"]["nEntities"] == 1
    assert manifest["entityGraphCatalog"]["stockCodeCount"] == 1
    assert manifest["entityGraphCatalog"]["dataAsOf"] == "20260616"


def test_edgar_period_to_data_as_of_uses_quarter_end() -> None:
    from dartlab.providers.dart.search.freshness import periodToDataAsOf

    assert periodToDataAsOf("2025Q4") == "20251231"
    assert periodToDataAsOf("2026Q1") == "20260331"
    assert periodToDataAsOf("bad") == ""


def test_clear_delta_segment_removes_artifacts(monkeypatch, tmp_path) -> None:
    """clearDeltaSegment: delta artifact 를 제거하고 캐시를 비운다."""
    from dartlab.providers.dart.search import fieldIndex, fieldIndexRebuild

    monkeypatch.setattr(fieldIndex, "_contentIndexDir", lambda tier=None: tmp_path)
    (tmp_path / "delta.npz").write_bytes(b"\x00")

    fieldIndexRebuild.clearDeltaSegment(tier="full")
    assert not (tmp_path / "delta.npz").exists()


# ── 메모리 상한 빌드(2026-10 Search Index Build runner 강제 종료 회귀 가드) ─────────────────
# 행마다 dict 를 만들던 빌드는 변경분 105 만 행에서 runner 메모리를 넘겼다. 행 묶음 빌드가 같은 산출물을
# 내는지, 묶음·블록 경계에서 결과가 바뀌지 않는지 고정한다.


def _catalogFrame():
    import polars as pl

    return pl.DataFrame(
        {
            "docKey": ["k1", "k2", "k3", "k4"],
            "rceptNo": ["20260101000001", "", None, "20260101000004"],
            "sourceRef": ["ref1", "ref2", "ref3", "ref4"],
            "sectionOrder": [0, 2, None, 1],
            "corpCode": ["00126380", "", "", "00164779"],
            "companyName": ["삼성전자", "", "뉴스", "SK하이닉스"],
            "stockCode": ["005930", "", None, ""],
            "ticker": ["", "AAPL", "", "000660"],
            "date": ["20260101", "20260102", "20260103", "20260104"],
            "reportName": ["사업보고서", "10-K", "", "분기보고서"],
            "title": ["", "Item 1", "기사 제목", ""],
            "sectionKey": ["사업의 내용", "", "", "재무"],
            "searchText": ["배당 정책과 자금 조달 " * 400, "revenue growth outlook", "증자 공시 기사", "삭제된 문서"],
            "source": ["dartPanel", "edgarPanel", "newsPublic", "allFilings"],
            "sourceDataAsOf": ["", "20260102", "", ""],
            "url": ["", "https://x", "https://news/1", ""],
            "deleted": [False, False, False, True],
        }
    )


def _segmentBytes(base, name):
    import polars as pl

    out = {}
    for path in sorted(base.iterdir()):
        if not path.name.startswith(name):
            continue
        if path.suffix == ".parquet":
            out[path.name] = pl.read_parquet(path)
        elif path.name.endswith(("search_meta.json", "_info.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            data.pop("builtAt", None)
            out[path.name] = data
        else:
            out[path.name] = path.read_bytes()
    return out


def _assertSameSegment(left, right):
    assert left.keys() == right.keys()
    for key, value in left.items():
        other = right[key]
        if hasattr(value, "equals"):
            assert value.schema == other.schema, key
            assert value.equals(other), key
        else:
            assert value == other, key


def test_rebuild_main_from_parquet_path_matches_frame_and_skips_deleted(tmp_path, monkeypatch) -> None:
    """경로로 묶음씩 읽은 main 과 메모리 DataFrame 으로 만든 main 이 같고, 삭제 행은 색인하지 않는다."""
    import polars as pl

    from dartlab.providers.dart.search import fieldIndex, fieldIndexRebuild

    catalog = _catalogFrame()
    catalogPath = tmp_path / "catalog.parquet"
    catalog.write_parquet(catalogPath)
    monkeypatch.setattr(fieldIndexRebuild, "_FEED_BATCH", 2)  # 묶음 경계를 여러 번 지나게 한다

    dirs = {}
    for label, rows in (("frame", catalog), ("path", catalogPath)):
        out = tmp_path / label
        monkeypatch.setattr(fieldIndex, "_contentIndexDir", lambda tier=None, out=out: out)
        assert fieldIndexRebuild.rebuildMainFromCatalog(rows, tier="full") == 3
        dirs[label] = _segmentBytes(out, "main")
    _assertSameSegment(dirs["frame"], dirs["path"])

    meta = pl.read_parquet(tmp_path / "frame" / "main_meta.parquet")
    assert meta["docKey"].to_list() == ["k1", "k2", "k3"]
    assert meta["rcept_no"].to_list() == ["20260101000001", "ref2", "ref3"]  # 빈 값·null 이면 다음 열
    assert meta["stock_code"].to_list() == ["005930", "AAPL", ""]
    assert meta["section_title"].to_list() == ["사업의 내용", "Item 1", "기사 제목"]
    assert meta["source"].to_list() == ["panel", "edgar-panel", "news"]
    assert meta["url"].to_list() == ["", "", "https://news/1"]  # 뉴스만 url
    assert meta["sourceDataAsOf"].to_list() == ["20260101", "20260102", "20260103"]
    assert meta["contentLen"].to_list() == [1500, len("revenue growth outlook"), len("증자 공시 기사")]
    assert meta.schema["contentLen"] == pl.Int64 and meta.schema["deleted"] == pl.Boolean
    assert meta["evidenceText"].str.len_chars().max() == fieldIndexRebuild.EVIDENCE_TEXT_LIMIT


def test_rebuild_delta_tombstone_and_legacy_columns(tmp_path, monkeypatch) -> None:
    """delta 는 tombstone 을 빈 문서로 남기고, 옛 열 이름(rceptNo·searchText)도 같은 규칙으로 읽는다."""
    import polars as pl

    from dartlab.providers.dart.search import fieldIndex, fieldIndexRebuild

    monkeypatch.setattr(fieldIndex, "_contentIndexDir", lambda tier=None: tmp_path)
    monkeypatch.setattr(fieldIndexRebuild, "_FEED_BATCH", 3)
    rows = _catalogFrame()
    assert fieldIndexRebuild.rebuildDeltaFromCatalog(rows, tier="full") == 4

    meta = pl.read_parquet(tmp_path / "delta_meta.parquet")
    assert meta["deleted"].to_list() == [False, False, False, True]
    assert meta["contentLen"].to_list()[-1] == 0 and meta["text"].to_list()[-1] == ""
    assert meta["evidenceText"].to_list()[-1] == "삭제된 문서"  # tombstone 도 증거 원문은 보존(기존 규칙)
    overrides = json.loads((tmp_path / "delta_overrides.json").read_text(encoding="utf-8"))
    expected = meta.select(["docKey", "sourceRef", "rcept_no", "section_order", "deleted"]).to_dicts()
    assert overrides == expected
    assert (tmp_path / "delta_overrides.json").read_text(encoding="utf-8") == json.dumps(
        expected, ensure_ascii=False, separators=(",", ":")
    )
    lengths = (tmp_path / "delta.docLengths.bin").read_bytes()
    assert len(lengths) == 4 * 4 and lengths[-4:] == b"\x00\x00\x00\x00"


def test_postings_block_boundaries_do_not_change_bytes(tmp_path, monkeypatch) -> None:
    """posting 블록을 아주 작게 잘라도 postings.bin·terms.bin 은 한 번에 인코딩한 것과 같다."""
    import numpy as np

    from dartlab.providers.dart.search import fieldIndex

    rng = np.random.default_rng(7)
    counts = rng.integers(1, 9, size=40)
    offsets = np.zeros(len(counts) + 1, dtype=np.int64)
    np.cumsum(counts, out=offsets[1:])
    docIds = np.concatenate([np.sort(rng.choice(5000, size=c, replace=False)) for c in counts]).astype(np.int32)
    termFreqs = rng.integers(1, 400, size=len(docIds)).astype(np.int32)

    whole, wholeLen = fieldIndex._writePostings(tmp_path / "whole.bin", offsets, docIds, termFreqs)
    monkeypatch.setattr(fieldIndex, "_POSTINGS_BLOCK", 5)
    small, smallLen = fieldIndex._writePostings(tmp_path / "small.bin", offsets, docIds, termFreqs)

    assert wholeLen == smallLen
    assert (tmp_path / "whole.bin").read_bytes() == (tmp_path / "small.bin").read_bytes()
    assert np.array_equal(whole, small)
