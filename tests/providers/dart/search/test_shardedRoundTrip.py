"""sidecar(STORED) round-trip + BM25 byte-parity — npz 폐기 기반(P0/P2) 게이트.

``saveShardedSegment`` 산출(postings/terms/docLengths.bin)을 ``loadShardedSegment`` 가 무손실 복원해
CSR(offsets/docIds/termFreqs/docLengths)이 빌더 원본과 array-equal 이고, ``_scoreBM25`` 결과가 빌더 원본과
동일함을 검증한다. 이 게이트가 통과해야 엔진이 npz 없이 sidecar 만으로 검색 가능(PRD 기둥1·§13).
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from dartlab.providers.dart.search.fieldIndex import (
    _decodeVarintStream,
    _encodeVarintArray,
    _IncrementalBuilder,
    _scoreBM25,
    loadShardedSegment,
    saveShardedSegment,
    tokenizeContent,
    writeSegmentCompanions,
)


def _meta(n: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "rcept_no": [f"R{i:08d}" for i in range(n)],
            "section_order": [0] * n,
            "corp_code": [f"C{i}" for i in range(n)],
            "corp_name": [f"회사{i}" for i in range(n)],
            "stock_code": [f"{i:06d}" for i in range(n)],
            "rcept_dt": ["20260618"] * n,
            "report_nm": ["분기보고서"] * n,
            "section_title": [""] * n,
            "text": ["t"] * n,
            "source": ["panel"] * n,
            "sourceRef": [""] * n,
            "sourceDataAsOf": ["20260618"] * n,
            "contentLen": [10] * n,
            "url": [""] * n,
            "evidenceText": ["e"] * n,
        }
    )


def _build(docs: list[str]) -> dict:
    b = _IncrementalBuilder()
    for d in docs:
        b.addDoc(d)
    return b.finalize()


def test_decode_varint_stream_roundtrip():
    # 빈 스트림은 _encodeVarintArray(빈 배열) 미지원(.max 불가)이라 디코드만 직접 검증.
    assert _decodeVarintStream(b"", 0).tolist() == []
    cases = [
        [0],
        [1, 300, 5, 127, 128, 16383, 16384, 1 << 20, 1 << 27],
        list(range(0, 5000, 7)),
    ]
    for vals in cases:
        arr = np.array(vals, dtype=np.int64)
        raw, _ = _encodeVarintArray(arr)
        out = _decodeVarintStream(raw, len(arr))
        assert out.tolist() == vals


@pytest.mark.unit
def testLargeVarintStreamPreservesValuesAcrossByteBoundary():
    values = np.tile(np.array([0, 127, 128, 16384, 1 << 27], dtype=np.int64), 150000)
    raw, _ = _encodeVarintArray(values)
    np.testing.assert_array_equal(_decodeVarintStream(raw, len(values)), values)


@pytest.mark.unit
@pytest.mark.parametrize("raw,count", [(b"\x80", 1), (b"\x01\x80", 1), (b"\x01", 0), (b"\x80" * 10 + b"\x00", 1)])
def testMalformedVarintStreamRejected(raw, count):
    with pytest.raises(ValueError):
        _decodeVarintStream(raw, count)


@pytest.mark.unit
def testShardedLoadCrossesTermBatchesWithoutReadingWholePostings(tmp_path, monkeypatch):
    from pathlib import Path

    size = 4200
    idx = {
        "stemDict": {f"term{i}": i for i in range(size)},
        "offsets": np.arange(size + 1, dtype=np.int64) * 2,
        "docIds": np.tile(np.array([0, 2], dtype=np.int32), size),
        "termFreqs": np.tile(np.array([1, 300], dtype=np.int32), size),
        "docLengths": np.array([size, 0, size * 300], dtype=np.int32),
        "nDocs": 3,
        "avgDocLength": size * 301 / 3,
    }
    meta = _meta(3)
    writeSegmentCompanions(idx, meta, "main", tmp_path)
    saveShardedSegment(idx, meta, "main", tmp_path)
    original = Path.read_bytes

    def readBytes(path):
        assert not path.name.endswith(".postings.bin"), "postings 전체 read_bytes 금지"
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", readBytes)
    loaded, _ = loadShardedSegment("main", tmp_path)
    for key in ("offsets", "docIds", "termFreqs", "docLengths"):
        np.testing.assert_array_equal(loaded[key], idx[key])


def test_sharded_roundtrip_and_bm25_parity(tmp_path):
    docs = [
        "삼성전자 반도체 매출 증가 영업이익",
        "현대차 자동차 영업이익 매출",
        "반도체 수요 매출 증가 HBM 투자",
        "배당 자사주 소각 주주환원 정책",
        "삼성 반도체 배당 유상증자",
        "현대차 배당 자사주",
    ]
    idx0 = _build(docs)
    meta = _meta(len(docs))
    writeSegmentCompanions(idx0, meta, "main", tmp_path)  # stems/info/meta.parquet (loadShardedSegment 동반물)
    saveShardedSegment(idx0, meta, "main", tmp_path)

    res = loadShardedSegment("main", tmp_path)
    assert res is not None
    idxS, metaS = res

    # CSR 무손실 복원
    for key in ("offsets", "docIds", "termFreqs", "docLengths"):
        assert np.array_equal(idxS[key], idx0[key]), f"{key} 불일치"
    assert idxS["nDocs"] == idx0["nDocs"]
    assert idxS["stemDict"] == idx0["stemDict"]
    assert metaS.height == len(docs)
    narrowIdx, narrowMeta = loadShardedSegment("main", tmp_path, metaColumns=("source", "rcept_no"))
    assert narrowMeta.columns == ["source", "rcept_no"]
    assert narrowMeta.height == metaS.height
    np.testing.assert_array_equal(narrowIdx["docIds"], idxS["docIds"])

    # BM25 byte-parity (sidecar 복원 idx == 빌더 원본 idx)
    for q in ["반도체 매출", "배당 자사주", "삼성 반도체", "현대차 배당", "HBM 투자", "없는단어"]:
        toks = tokenizeContent(q)
        np.testing.assert_array_equal(_scoreBM25(idxS, toks), _scoreBM25(idx0, toks))
