"""의미 인덱스의 증분·원문 위치·검색 범위 계약. 모델 품질은 실제 corpus 실험으로 확인한다."""

from types import SimpleNamespace

import numpy as np
import polars as pl
import pytest

from dartlab.providers.dart.search import semanticIndex as semantic
from dartlab.providers.dart.search.catalog import normalizeCatalogRows

pytestmark = pytest.mark.unit


@pytest.fixture
def encoder(monkeypatch):
    calls = []

    def encode(texts, **kwargs):
        calls.extend(texts)
        return np.asarray([[1.0, 0.0] for text in texts], dtype=np.float32)

    monkeypatch.setattr(semantic, "_DIM", 2)
    monkeypatch.setattr(semantic, "_encoder", lambda: SimpleNamespace(encode=encode))
    monkeypatch.setattr(semantic, "_reranker", lambda: SimpleNamespace(embed=lambda texts: iter(encode(texts))))
    monkeypatch.setattr(semantic, "_rerankVector", lambda text: np.array([1.0, 0.0], dtype=np.float32))
    return calls


def catalog(path, rows):
    normalizeCatalogRows(rows).write_parquet(path)


def testExplicitModelPreparationPinsRevisionsAndDownloadFiles(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(semantic, "_requireModels", lambda: None)
    monkeypatch.setattr(semantic, "_modelDir", lambda name: tmp_path / name.rsplit("/", 1)[-1])
    monkeypatch.setattr("huggingface_hub.snapshot_download", lambda name, **kwargs: calls.append((name, kwargs)))
    semantic.prepareSemanticModels()
    assert [name for name, args in calls] == [semantic._MODEL, semantic._RERANK_MODEL]
    assert [args["revision"] for name, args in calls] == [semantic._REVISION, semantic._RERANK_REVISION]
    for name, args in calls:
        assert len(args["revision"]) == 40
        assert args["local_dir"] == str(tmp_path / name.rsplit("/", 1)[-1])
        assert "tokenizer.json" in args["allow_patterns"]
        assert all("*" not in pattern for pattern in args["allow_patterns"])
    assert "model.safetensors" in calls[0][1]["allow_patterns"]
    assert "onnx/model_qint8_avx512_vnni.onnx" in calls[1][1]["allow_patterns"]


def testCatalogSourceLineageSurvivesSemanticProjection(tmp_path, encoder):
    from dartlab.providers.dart.search.sourceCatalog import buildCatalogSnapshot, buildSourceManifest

    raw, snapshot, index = tmp_path / "raw.parquet", tmp_path / "catalog.parquet", tmp_path / "index"
    pl.DataFrame([{"rceptNo": "20250101000001", "date": "20250101", "searchText": "전력 공급 계획"}]).write_parquet(raw)
    manifest = buildSourceManifest("allFilings", [raw], producerRun={"id": "run-1"})
    assert manifest["totalRows"] == manifest["changedRows"] == 1
    assert manifest["producerRun"] == {"id": "run-1"}
    assert manifest["files"][0]["sizeBytes"] == raw.stat().st_size
    assert manifest["files"][0]["hash"]
    frame = buildCatalogSnapshot("allFilings", [raw], sourceDataAsOf="20250102", sourceAdapterVersion="trial-v2")
    assert frame["sourceAdapterVersion"].to_list() == ["trial-v2"]
    frame.write_parquet(snapshot)
    semantic.buildSemanticIndex(indexDir=index, sources=[(snapshot, "catalog")])
    hit = semantic.searchSemantic("전력", indexDir=index).row(0, named=True)
    assert hit["sourceRef"] == frame["sourceRef"][0]
    assert hit["sourceDataAsOf"] == "20250102"
    assert hit["coverage"] == "catalogExcerpt"


def testIncrementalReusesTextAndRemovesDeletedDocuments(tmp_path, encoder):
    source, index = tmp_path / "source.parquet", tmp_path / "index"
    rows = [
        {"rceptNo": "20250101000001", "searchText": "전력 설비", "title": "투자"},
        {"rceptNo": "20250102000001", "searchText": "반도체 증설", "title": "투자"},
    ]
    catalog(source, rows)
    first = semantic.buildSemanticIndex(indexDir=index, sources=[(source, "catalog")])
    assert first["encoded"] == 2
    info = semantic.semanticIndexInfo(indexDir=index)
    assert info["available"] and info["passages"] == 2
    assert "shards" not in info
    assert semantic.buildSemanticIndex(indexDir=index, sources=[(source, "catalog")])["encoded"] == 0
    rows[0]["companyName"] = "변경된 이름"
    rows[1]["deleted"] = True
    rows.append({"rceptNo": "20250202000001", "searchText": "새로운 본문", "title": "투자"})
    catalog(source, rows)
    update = semantic.buildSemanticIndex(indexDir=index, sources=[(source, "catalog")])
    assert update["encoded"] == 1 and update["reused"] == 1
    result = semantic.searchSemantic("투자", indexDir=index)
    assert result.height == 2
    assert "20250102000001" not in result["rcept_no"]
    assert "변경된 이름" in result["corp_name"]
    assert semantic.semanticIndexInfo(indexDir=index)["passages"] == 2


def testFailedRebuildKeepsLastReadableSnapshot(tmp_path, encoder, monkeypatch):
    source, index = tmp_path / "source.parquet", tmp_path / "index"
    catalog(source, [{"rceptNo": "20250101000001", "searchText": "원래 문서"}])
    semantic.buildSemanticIndex(indexDir=index, sources=[(source, "catalog")])
    before = (index / "manifest.json").read_bytes()
    files = {path.name for path in index.iterdir()}
    catalog(source, [{"rceptNo": "20250101000001", "searchText": "수정된 문서"}])
    monkeypatch.setattr(
        semantic,
        "_encoder",
        lambda: SimpleNamespace(encode=lambda *a, **k: (_ for _ in ()).throw(ValueError("failure"))),
    )
    with pytest.raises(ValueError, match="failure"):
        semantic.buildSemanticIndex(indexDir=index, sources=[(source, "catalog")])
    assert (index / "manifest.json").read_bytes() == before
    assert {path.name for path in index.iterdir()} == files


def testBuildKeepsRetiredShardsWhileReaderIsActive(tmp_path, encoder):
    from filelock import FileLock

    source, index = tmp_path / "source.parquet", tmp_path / "index"
    catalog(source, [{"rceptNo": "20250101000001", "searchText": "원래 본문"}])
    semantic.buildSemanticIndex(indexDir=index, sources=[(source, "catalog")])
    old = semantic._manifest(index)["shards"][0]
    with FileLock(str(index / "read.lock")):
        catalog(source, [{"rceptNo": "20250101000001", "searchText": "수정 본문"}])
        semantic.buildSemanticIndex(indexDir=index, sources=[(source, "catalog")])
        assert (index / old["meta"]).exists()
        assert (index / old["vectors"]).exists()
    semantic.buildSemanticIndex(indexDir=index, sources=[(source, "catalog")])
    assert not (index / old["meta"]).exists()


def testLocalPanelTailAndCleanedTextOffsetsArePreserved(tmp_path, encoder):
    source = tmp_path / "005930.parquet"
    text = "앞쪽 설명 " * 1200 + "마지막 문단의 공급망 위험"
    pl.DataFrame(
        {
            "rceptNo": ["20250101000001"],
            "contentRaw": [f"<p>{text}</p>"],
            "period": ["2024Q4"],
            "blockOrder": [42],
            "sectionLeaf": ["사업의 내용"],
        }
    ).write_parquet(source)
    rows = list(semantic._passages(source, "dartPanel"))
    assert rows[-1]["text"].endswith("마지막 문단의 공급망 위험")
    assert all(row["text"] == text[row["charStart"] : row["charEnd"]] for row in rows)
    assert len({row["passageId"] for row in rows}) == len(rows)
    assert all(row["sourceRef"] == "dart:panel:20250101000001#section=42" for row in rows)
    assert all(row["coverage"] == "localFullText" for row in rows)


def testFiltersApplyBeforeRankingAndRelatedSearchExcludesSeed(tmp_path, encoder):
    source, index = tmp_path / "source.parquet", tmp_path / "index"
    rows = [
        {
            "rceptNo": f"20250{i}01000001",
            "searchText": f"설비 {i}",
            "date": f"20250{i}01",
            "stockCode": "005930" if i < 4 else "000660",
        }
        for i in range(1, 5)
    ]
    rows.append({"source": "news", "url": "https://example.org/news", "searchText": "뉴스", "date": "20250201"})
    catalog(source, rows)
    semantic.buildSemanticIndex(indexDir=index, sources=[(source, "catalog")])
    result = semantic.searchSemantic(
        "설비",
        corpCode="notOnPanel",
        stockCode="005930",
        sourceKind="filing",
        start="20250201",
        end="20250301",
        indexDir=index,
        limit=2,
    )
    assert set(result["rcept_no"]) == {"20250201000001", "20250301000001"}
    seed = result["passageId"][0]
    related = semantic.searchSemantic("", relatedTo=seed, indexDir=index)
    assert seed not in related["passageId"]
    assert set(related["relationType"]) == {"semanticSimilarity"}
    otherCompanies = semantic.searchSemantic("", relatedTo=seed, excludeStockCode="005930", indexDir=index)
    assert set(otherCompanies["stock_code"]) == {"000660"}
    assert "news" not in otherCompanies["source"]
    assert list(semantic.iterSemantic("", relatedTo=seed, excludeStockCode="005930", indexDir=index)) == (
        otherCompanies.to_dicts()
    )
    with pytest.raises(ValueError, match="passageId"):
        semantic.searchSemantic("", relatedTo="missing", indexDir=index)


def testMissingSemanticIndexExplainsPreparation(tmp_path, encoder):
    assert semantic.semanticIndexInfo(indexDir=tmp_path) == {"available": False}
    assert encoder == []
    with pytest.raises(RuntimeError, match="--build-semantic"):
        semantic.searchSemantic("설비", indexDir=tmp_path)


def testCorpCodeFilterAlsoReachesLocalRawPanel(tmp_path, encoder):
    source, panel, index = tmp_path / "catalog.parquet", tmp_path / "005930.parquet", tmp_path / "index"
    catalog(
        source,
        [{"rceptNo": "20250101000001", "searchText": "catalog 발췌", "corpCode": "00126380", "stockCode": "005930"}],
    )
    pl.DataFrame(
        {
            "rceptNo": ["20250102000001"],
            "contentRaw": ["로컬 본문의 다른 설명"],
            "blockOrder": [1],
            "period": ["2024Q4"],
        }
    ).write_parquet(panel)
    semantic.buildSemanticIndex(indexDir=index, sources=[(source, "catalog"), (panel, "dartPanel")])
    hits = semantic.searchSemantic("설명", corpCode="00126380", indexDir=index)
    assert hits.height == 2
    assert set(hits["coverage"]) == {"catalogExcerpt", "localFullText"}


def testPublicRelatedSearchReachesOwner(monkeypatch):
    import dartlab
    import dartlab.providers.dart.search as searchPackage

    calls = []
    monkeypatch.setattr(searchPackage, "search", lambda query, **kwargs: calls.append((query, kwargs)))
    dartlab.search("", scope="semantic", relatedTo="source@passage", corp="AAPL")
    assert calls[0][0] == ""
    assert calls[0][1]["relatedTo"] == "source@passage"
    assert calls[0][1]["corp"] == "AAPL"


@pytest.mark.parametrize("start,end", [("2024-01-01", None), ("20250230", None), ("20251231", "20250101")])
def testSemanticDatesRejectInvalidRanges(tmp_path, start, end):
    with pytest.raises(ValueError):
        semantic.searchSemantic("설비", start=start, end=end, indexDir=tmp_path)
