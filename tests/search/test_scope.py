"""core/search scope 파라미터 + fieldIndex 동작 단위 테스트."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_scope_validation():
    """잘못된 scope 값은 ValueError."""
    import dartlab

    with pytest.raises(ValueError, match="scope"):
        dartlab.search("test", scope="invalid")


def test_top_level_search_accepts_top_k_alias(monkeypatch):
    """문서/skill 의 topK alias 는 limit 로 흡수한다."""
    import dartlab
    import dartlab.providers.dart.search as searchPkg

    calls = {}

    def fakeSearch(query, *, corp=None, start=None, end=None, limit=10, scope="auto", relatedTo=None, excludeCorp=None):
        assert relatedTo is None and excludeCorp is None
        calls.update({"query": query, "corp": corp, "start": start, "end": end, "limit": limit, "scope": scope})
        return "ok"

    monkeypatch.setattr(searchPkg, "search", fakeSearch)

    assert dartlab.search("유상증자", topK=3, scope="title") == "ok"
    assert calls == {"query": "유상증자", "corp": None, "start": None, "end": None, "limit": 3, "scope": "title"}


def test_tokenize_content():
    """content 토크나이저(음절 bigram + ascii 소문자) 동작."""
    from dartlab.providers.dart.search.fieldIndex import tokenizeContent

    # 한글 run 별 음절 bigram (1음절 run 은 그대로)
    assert tokenizeContent("원재료 가격 급등") == ["원재", "재료", "가격", "급등"]
    # 영문 소문자화 + 숫자 제외 (vocab 오염 차단)
    assert tokenizeContent("HBM 투자 2025") == ["투자", "hbm"]
    # 조사 흡수 — "배당을" 이 "배당" 질의와 토큰 공유
    assert "배당" in tokenizeContent("배당을 지급")
    # 빈 문자열
    assert tokenizeContent("") == []
    assert tokenizeContent(None) == []


def test_build_content_segment_smoke():
    """소규모 문서로 세그먼트 빌드 + 구조 검증."""
    from dartlab.providers.dart.search.fieldIndex import buildContentSegment

    rows = [
        {
            "rcept_no": "20260101000001",
            "section_order": 0,
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "rcept_dt": "20260101",
            "report_nm": "사업보고서",
            "section_title": "사업의 내용",
            "section_content": "반도체 HBM 투자 확대. 원재료 가격 상승 우려.",
            "source": "docs",
        },
        {
            "rcept_no": "20260101000002",
            "section_order": 0,
            "corp_code": "00164779",
            "corp_name": "SK하이닉스",
            "stock_code": "000660",
            "rcept_dt": "20260101",
            "report_nm": "사업보고서",
            "section_title": "사업의 내용",
            "section_content": "환율 변동 리스크 관리. 해외 매출 비중 확대.",
            "source": "docs",
        },
    ]
    idx, meta = buildContentSegment(rows, showProgress=False)
    assert idx["nDocs"] == 2
    assert len(idx["stemDict"]) > 0
    assert meta.height == 2
    # 토큰(음절 bigram)이 인덱스에 실제 들어갔는지
    assert "반도" in idx["stemDict"]
    assert "도체" in idx["stemDict"]
    assert "환율" in idx["stemDict"]


def test_bm25_ranks_relevant_doc():
    """BM25 스코어링이 관련 문서를 상위로 올리는지."""

    from dartlab.providers.dart.search.fieldIndex import _scoreBM25, buildContentSegment, tokenizeContent

    rows = [
        {
            "rcept_no": "a",
            "section_order": 0,
            "section_content": "반도체 HBM 투자",
            "corp_name": "",
            "stock_code": "",
            "rcept_dt": "",
            "report_nm": "",
            "section_title": "",
            "corp_code": "",
            "source": "",
        },
        {
            "rcept_no": "b",
            "section_order": 0,
            "section_content": "화장품 유통 계약",
            "corp_name": "",
            "stock_code": "",
            "rcept_dt": "",
            "report_nm": "",
            "section_title": "",
            "corp_code": "",
            "source": "",
        },
    ]
    idx, _ = buildContentSegment(rows, showProgress=False)
    scores = _scoreBM25(idx, tokenizeContent("반도체 HBM"))
    # 첫 문서 > 두 번째 문서
    assert scores[0] > scores[1]


def test_segment_save_load_roundtrip(tmp_path):
    """saveSegmentWithSidecar + loadSegment 왕복 (compact-only — sidecar SSOT)."""
    from dartlab.providers.dart.search.fieldIndex import (
        buildContentSegment,
        loadSegment,
        saveSegmentWithSidecar,
    )

    rows = [
        {
            "rcept_no": "x",
            "section_order": 0,
            "section_content": "테스트 문서 내용",
            "corp_name": "테스트",
            "stock_code": "",
            "rcept_dt": "",
            "report_nm": "",
            "section_title": "",
            "corp_code": "",
            "source": "",
        },
    ]
    idx, meta = buildContentSegment(rows, showProgress=False)
    saveSegmentWithSidecar(idx, meta, "test_main", tmp_path)

    loaded = loadSegment("test_main", inDir=tmp_path)
    assert loaded is not None
    loadedIdx, loadedMeta = loaded
    assert loadedIdx["nDocs"] == idx["nDocs"]
    assert loadedIdx["stemDict"] == idx["stemDict"]
    assert loadedMeta.height == meta.height
    assert "evidenceText" not in loadedMeta.columns

    loadedWithEvidence = loadSegment("test_main", inDir=tmp_path, includeEvidenceText=True)
    assert loadedWithEvidence is not None
    assert "evidenceText" in loadedWithEvidence[1].columns


def test_load_segment_missing_returns_none(tmp_path):
    """없는 세그먼트 로드 시 None."""
    from dartlab.providers.dart.search.fieldIndex import loadSegment

    assert loadSegment("nonexistent", inDir=tmp_path) is None


def test_search_scope_title_works(monkeypatch):
    """scope='title'이 기존 방식으로 동작하는지."""
    import polars as pl

    import dartlab
    from dartlab.providers.dart.search import api

    monkeypatch.setattr(
        api,
        "_searchTitle",
        lambda query, *, corpCode, stockCode, limit: pl.DataFrame({"info": ["ok"]}),
    )

    r = dartlab.search("유상증자", scope="title", topK=3)
    assert isinstance(r, pl.DataFrame)


@pytest.mark.parametrize("scope", ["auto", "content", "title", "both", "news"])
def testDateRangeBeforeCandidateLimit(tmp_path, monkeypatch, scope):
    """기간 밖 고득점 공시가 후보를 채워도 지정 기간의 두 경계 공시를 회수한다."""
    import polars as pl

    import dartlab
    from dartlab.providers.dart.search import fieldIndex, ngramIndex, unified

    rows = []
    for number, date in enumerate(["20260731"] * 100 + ["20260901"] * 100 + ["20260801", "20260831"]):
        content = "반기보고서 " * 20 if number < 200 else "반기보고서 기업 현황과 재무제표를 설명합니다."
        rows.append(
            {
                "rcept_no": f"{date}{number:06d}",
                "section_order": 0,
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "stock_code": "005930",
                "rcept_dt": date,
                "report_nm": "반기보고서",
                "section_title": "",
                "section_content": content,
                "content_raw": content,
                "fetch_status": "ok",
                "source": "news" if scope == "news" else "allFilings",
            }
        )
    segment = fieldIndex.buildContentSegment(rows, showProgress=False)
    monkeypatch.setattr(fieldIndex, "_getSegments", lambda: {"main": segment})
    monkeypatch.setattr(unified, "_getSegments", lambda: {"main": segment})
    monkeypatch.setattr(unified, "_activeIndexDir", lambda: tmp_path)
    monkeypatch.setattr(ngramIndex, "_stemIndexDir", lambda: tmp_path)
    monkeypatch.setattr(ngramIndex, "_cachedIndex", None)
    monkeypatch.setattr(ngramIndex, "_cachedMeta", None)
    sourcePath = tmp_path / "filings.parquet"
    pl.DataFrame(rows).write_parquet(sourcePath)
    ngramIndex.buildNgramIndex([sourcePath], showProgress=False)

    hits = dartlab.search(
        "반기보고서",
        corp=None if scope == "news" else "005930",
        scope=scope,
        start="20260801",
        end="20260831",
        limit=2,
    )
    assert set(hits["rcept_no"]) == {"20260801000200", "20260831000201"}


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        ("20260801", None, [False, False, False, True, True]),
        (None, "20260801", [False, False, True, True, False]),
        ("20260801", "20260801", [False, False, False, True, False]),
    ],
)
def testDateMaskIncludesBoundsAndExcludesUnknown(start, end, expected):
    import polars as pl

    from dartlab.providers.dart.search.fieldIndex import _scopeMask

    meta = pl.DataFrame({"rcept_dt": [None, "", "20260731", "20260801", "20260802"]})
    assert _scopeMask(meta, None, None, start=start, end=end).tolist() == expected
