"""unified 모듈 mirror smoke — searchUnified 공개 표면."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_imports() -> None:
    """모듈 import smoke."""
    from dartlab.providers.dart.search import unified

    assert unified is not None


def test_search_unified_callable() -> None:
    """searchUnified() callable smoke."""
    from dartlab.providers.dart.search.unified import searchUnified

    assert callable(searchUnified)


def test_empty_query_returns_empty() -> None:
    """빈 질의 → 빈 DataFrame (인덱스 접근 0)."""
    import polars as pl

    from dartlab.providers.dart.search.unified import searchUnified

    df = searchUnified("")
    assert isinstance(df, pl.DataFrame)
    assert df.height == 0


def test_body_semantic_rerank_prefers_panel_report_body_over_news_and_boilerplate() -> None:
    from dartlab.providers.dart.search.unified import _rerankBodySemanticHits

    ranked = _rerankBodySemanticHits(
        "환율 리스크 사업보고서 본문",
        [
            {
                "source": "news",
                "report_nm": "",
                "section_title": "환율 리스크 뉴스",
                "text": "환율 리스크",
                "score": 40.0,
            },
            {
                "source": "allFilings",
                "report_nm": "일괄신고서",
                "section_title": "일괄신고서",
                "text": "제72기 사업보고서 제출에 따른 정정 환율 리스크",
                "score": 30.0,
            },
            {
                "source": "panel",
                "report_nm": "사업보고서",
                "section_title": "위험관리",
                "text": "본문 환율 리스크",
                "score": 1.0,
            },
        ],
        None,
    )

    assert ranked[0]["source"] == "panel"


def test_body_semantic_intent_catches_topic_plus_original_filing_query() -> None:
    from dartlab.providers.dart.search.unified import _prefersBodySemanticRerank

    assert _prefersBodySemanticRerank("HBM 설비투자와 TC bonder 증설을 언급한 공시 원문")
    assert not _prefersBodySemanticRerank("환율 리스크 사업보고서 본문")
    assert not _prefersBodySemanticRerank("특수관계자 거래 주석")
    assert not _prefersBodySemanticRerank("유상증자 결정 정정 공시")


def test_body_semantic_rerank_prefers_topical_body_over_generic_filing_title() -> None:
    from dartlab.providers.dart.search.unified import _rerankBodySemanticHits

    ranked = _rerankBodySemanticHits(
        "HBM 설비투자와 TC bonder 증설을 언급한 공시 원문",
        [
            {
                "source": "panel",
                "report_nm": "분기보고서",
                "section_title": "회사 개요",
                "text": "분기보고서 제출대상법인 유형 주권상장법인 투자 관련 일반 본문",
                "score": 120.0,
            },
            {
                "source": "allFilings",
                "report_nm": "타법인 주식 및 출자증권 양수결정",
                "section_title": "정정신고",
                "text": "정정대상 공시서류 양도내역 매매대금 변경",
                "score": 90.0,
            },
            {
                "source": "allFilings",
                "report_nm": "단일판매ㆍ공급계약체결",
                "section_title": "단일판매ㆍ공급계약체결",
                "text": "HBM4 제조용 TC BONDER 장비 수주 설비투자 증설",
                "score": 2.0,
            },
        ],
        None,
    )

    assert "HBM4" in ranked[0]["text"]


def test_event_title_rerank_prefers_requested_report_label() -> None:
    from dartlab.providers.dart.search.unified import _rerankEventTitleHits

    ranked = _rerankEventTitleHits(
        "사업보고서 제출",
        [
            {
                "source": "allFilings",
                "report_nm": "감사보고서제출",
                "section_title": "감사보고서 제출",
                "rcept_dt": "20260612",
                "score": 100.0,
            },
            {
                "source": "allFilings",
                "report_nm": "사업보고서",
                "section_title": "사업보고서",
                "rcept_dt": "20260318",
                "score": 1.0,
            },
        ],
        None,
    )

    assert ranked[0]["report_nm"] == "사업보고서"


def test_event_title_rerank_promotes_explicit_prospectus_title() -> None:
    from dartlab.providers.dart.search.unified import _rerankEventTitleHits

    ranked = _rerankEventTitleHits(
        "공시 원문 투자설명서 6.0 주식회사 케이티스카이라이프 투 자 설 명",
        [
            {
                "source": "allFilings",
                "sourceRef": "dart:allFilings:20250721000015#section=0",
                "report_nm": "주요사항보고서(자기주식처분결정)",
                "section_title": "6.0 처분예정금액",
                "text": "주식회사 케이티스카이라이프 자기주식 처분",
                "rcept_dt": "20250721",
                "score": 120.0,
            },
            {
                "source": "allFilings",
                "sourceRef": "dart:allFilings:20260617000006#section=0",
                "report_nm": "투자설명서",
                "section_title": "투 자 설 명 서",
                "text": "6.0 주식회사 케이티스카이라이프",
                "rcept_dt": "20260617",
                "score": 20.0,
            },
        ],
        None,
    )

    assert ranked[0]["sourceRef"] == "dart:allFilings:20260617000006#section=0"


def test_report_label_candidate_lane_uses_body_when_title_metadata_missing() -> None:
    import polars as pl

    from dartlab.providers.dart.search.unified import _reportLabels, _scoreReportLabelEvidence

    meta = pl.DataFrame(
        [
            {
                "source": "allFilings",
                "rcept_dt": "20250320",
                "report_nm": "감사보고서제출",
                "section_title": "감사보고서제출",
                "text": "사업보고서 제출 기한 연장",
                "evidenceText": "사업보고서 제출 기한 연장",
            },
            {
                "source": "panel",
                "rcept_dt": "20260320",
                "report_nm": "",
                "section_title": "0",
                "text": "사업보고서 제출 기한 연장 신고서",
                "evidenceText": "사업보고서 제출 기한 연장 신고서",
            },
        ]
    )

    scores = _scoreReportLabelEvidence(meta, _reportLabels("사업보고서 제출"), "사업보고서 제출")

    assert scores[0] == 0
    assert scores[1] > 0


def test_report_label_candidate_lane_uses_literal_company_overlap() -> None:
    import polars as pl

    from dartlab.providers.dart.search.unified import _reportLabels, _scoreReportLabelEvidence

    meta = pl.DataFrame(
        [
            {
                "source": "allFilings",
                "rcept_dt": "20260617",
                "report_nm": "투자설명서",
                "section_title": "투자설명서",
                "text": "투자설명서 주식회사 다른회사",
                "evidenceText": "투자설명서 주식회사 다른회사",
            },
            {
                "source": "allFilings",
                "rcept_dt": "20260617",
                "report_nm": "투자설명서",
                "section_title": "투자설명서",
                "text": "투자설명서 6.0 주식회사 케이티스카이라이프 투 자 설 명 서",
                "evidenceText": "투자설명서 6.0 주식회사 케이티스카이라이프 투 자 설 명 서",
            },
        ]
    )

    scores = _scoreReportLabelEvidence(
        meta,
        _reportLabels("공시 원문 투자설명서 6.0 주식회사 케이티스카이라이프 투 자 설 명"),
        "공시 원문 투자설명서 6.0 주식회사 케이티스카이라이프 투 자 설 명",
    )

    assert scores[1] > scores[0]


def test_reportSurfaceCache_survivesIdReuse() -> None:
    """id(meta) 재사용 교차오염 회귀.

    ``_reportSurfaceFrame`` 은 ``id(meta)`` 를 캐시 키로 썼다. 파이썬 id 는 GC 후
    재사용되므로, 이전에 캐시된 프레임의 id 를 새 meta 가 물려받고 height 까지 같으면
    stale 프레임을 돌려줘 랭킹이 0 으로 무너졌다. 로컬 단독 실행은 캐시가 비어 안 터지고
    CI xdist 에서 이웃 테스트와 충돌할 때만 터지던 버그다. 여기서는 그 조건을 직접 만든다.
    캐시에 같은 키로 엉뚱한(height 만 같은) 프레임을 심어 두고, 진짜 meta 의 결과가
    그 stale 값이 아니라 자기 내용으로 나오는지 본다.
    """
    import polars as pl

    from dartlab.providers.dart.search import unified

    metaTruth = pl.DataFrame({"report_nm": ["증권신고서", "투자설명서"], "rcept_dt": ["20240101", "20240102"]})
    stale = pl.DataFrame({"report_nm": ["전혀다른것", "쓰레기값"], "rcept_dt": ["19990101", "19990102"]})
    staleFrame = unified._reportSurfaceFrame(stale, titleCols=["report_nm"], evidenceCols=[])

    # height 는 같지만 내용이 다른 stale 을 진짜 meta 의 id 키 자리에 심는다.
    unified._REPORT_SURFACE_CACHE[id(metaTruth)] = (stale, staleFrame)

    frame = unified._reportSurfaceFrame(metaTruth, titleCols=["report_nm"], evidenceCols=[])
    titles = frame["_title"].to_list()
    assert "증권신고서" in titles[0], f"stale 프레임이 새어 나왔다: {titles}"
    assert "전혀다른것" not in "".join(titles)


def test_event_title_weights_boost_supply_contract_for_order_query() -> None:
    from dartlab.providers.dart.search.fieldIndex import tokenizeContent
    from dartlab.providers.dart.search.unified import _eventTitleWeights

    weights = _eventTitleWeights("대규모 수주 계약 공시", None)

    for token in tokenizeContent("단일판매 공급계약체결"):
        assert weights[token] >= 3.0
