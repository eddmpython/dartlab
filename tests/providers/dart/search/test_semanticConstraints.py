from __future__ import annotations

import polars as pl

from dartlab.providers.dart.search.semanticConstraints import (
    SemanticConstraintPlan,
    compileSemanticMapperFromRows,
    matchSemanticAlias,
    planSemanticConstraints,
    rankBySemanticConstraints,
    rowSourceClass,
    semanticScopeMask,
)


def test_mapper_compiles_edgar_ticker_alias_from_rows() -> None:
    mapper = compileSemanticMapperFromRows(
        [
            {"source": "edgar-panel", "sourceRef": "edgar:panel:1", "corp_name": "ADI", "stock_code": "ADI"},
            {"source": "panel", "sourceRef": "dart:panel:1", "corp_name": "005930", "stock_code": "005930"},
        ]
    )

    alias = matchSemanticAlias("ADI 2026 분기보고서 공시 원문", mapper)

    assert alias is not None
    assert alias.stockCode == "ADI"
    assert alias.dominantSourceClass == "edgar"


def test_plan_promotes_ticker_alias_to_edgar_source_constraint() -> None:
    mapper = compileSemanticMapperFromRows(
        [{"source": "edgar-panel", "sourceRef": "edgar:panel:1", "corp_name": "ADI", "stock_code": "ADI"}]
    )

    plan = planSemanticConstraints("ADI 2026 분기보고서 공시 원문", mapper=mapper)

    assert plan.facets.stockCode == "ADI"
    assert plan.facets.years == ("2026",)
    assert plan.sourceClasses == ("edgar",)
    assert plan.sourceReason == "aliasDominantEdgar"


def test_korean_query_treats_common_filing_acronym_as_term_not_us_ticker() -> None:
    """한국 공시에 흔한 약어(HBM)를 미국 티커로 읽어 EDGAR 로 좁히지 않는다. 진짜 티커(ADI·AAPL)는 그대로다.

    2026-10-13 "반도체 HBM 투자 사업의 내용" 이 Hudbay Minerals(HBM) 40-F 만 돌려줬다.
    """
    mapper = compileSemanticMapperFromRows(
        [
            {"source": "edgar-panel", "sourceRef": "edgar:panel:h", "corp_name": "HBM", "stock_code": "HBM"},
            {"source": "edgar-panel", "sourceRef": "edgar:panel:a", "corp_name": "ADI", "stock_code": "ADI"},
            {"source": "edgar-panel", "sourceRef": "edgar:panel:p", "corp_name": "AAPL", "stock_code": "AAPL"},
        ]
    )
    frequency = {"hbm": 175, "adi": 5, "aapl": 0}.get

    hbm = planSemanticConstraints("반도체 HBM 투자 사업의 내용", mapper=mapper, krFilingFrequency=frequency)
    assert hbm.matchedAlias == "" and hbm.facets.stockCode is None
    assert hbm.sourceClasses == ("panel",)

    adi = planSemanticConstraints("ADI 2026 분기보고서", mapper=mapper, krFilingFrequency=frequency)
    assert adi.facets.stockCode == "ADI" and adi.sourceClasses == ("edgar",)
    aapl = planSemanticConstraints("AAPL 위험요인", mapper=mapper, krFilingFrequency=frequency)
    assert aapl.facets.stockCode == "AAPL" and aapl.sourceClasses == ("edgar",)
    english = planSemanticConstraints("HBM 10-K risk factors", mapper=mapper, krFilingFrequency=frequency)
    assert english.facets.stockCode == "HBM"


def test_periodic_report_query_routes_to_panel_not_original_filings() -> None:
    """정기보고서는 panel 에만 있다. "사업보고서 제출" 이 "제출" 때문에 allFilings 로 좁혀져 감사보고서제출만 나왔다."""
    mapper = compileSemanticMapperFromRows([])
    for query in ("사업보고서 제출", "분기보고서 제출", "반기보고서 제출"):
        assert planSemanticConstraints(query, mapper=mapper).sourceClasses == ("panel",)
    assert planSemanticConstraints("감사보고서 제출", mapper=mapper).sourceClasses == ("allFilings",)


def test_kr_filing_doc_frequency_counts_only_korean_filing_sources() -> None:
    import numpy as np

    from dartlab.providers.dart.search.semanticConstraints import krFilingDocFrequency

    idx = {"stemDict": {"hbm": 0}, "offsets": np.array([0, 3]), "docIds": np.array([0, 1, 2])}
    meta = pl.DataFrame({"source": ["allFilings", "edgar-panel", "panel"]})
    assert krFilingDocFrequency("hbm", {"main": (idx, meta)}) == 2
    assert krFilingDocFrequency("aapl", {"main": (idx, meta)}) == 0


def test_plan_matches_short_and_hyphenated_edgar_tickers() -> None:
    mapper = compileSemanticMapperFromRows(
        [
            {"source": "edgar-panel", "sourceRef": "edgar:panel:p", "corp_name": "P", "stock_code": "P"},
            {"source": "edgar-panel", "sourceRef": "edgar:panel:bf-a", "corp_name": "BF-A", "stock_code": "BF-A"},
        ]
    )

    assert planSemanticConstraints("EDGAR P 2026 10-Q", mapper=mapper).facets.stockCode == "P"
    assert planSemanticConstraints("EDGAR BF-A 2025 분기보고서", mapper=mapper).facets.stockCode == "BF-A"


def test_semantic_scope_mask_filters_concrete_source_class() -> None:
    meta = pl.DataFrame({"source": ["panel", "edgar-panel", "allFilings"]})
    mapper = compileSemanticMapperFromRows(
        [{"source": "edgar-panel", "sourceRef": "edgar:panel:1", "corp_name": "ADI", "stock_code": "ADI"}]
    )
    plan = planSemanticConstraints("ADI 10-Q", mapper=mapper)

    mask = semanticScopeMask(meta, plan)

    assert mask is not None
    assert mask.tolist() == [False, True, False]


def test_rank_by_semantic_constraints_sinks_violating_rows() -> None:
    plan = SemanticConstraintPlan(
        facets=planSemanticConstraints(
            "AAPL 2026 10-K",
            mapper=compileSemanticMapperFromRows(
                [{"source": "edgar-panel", "corp_name": "AAPL", "stock_code": "AAPL"}]
            ),
        ).facets,
        sourceClasses=("edgar",),
    )
    hits = [
        {
            "source": "panel",
            "sourceRef": "dart:panel:x",
            "stock_code": "005930",
            "rcept_dt": "20260101",
            "section_title": "0",
            "score": 100.0,
        },
        {
            "source": "edgar-panel",
            "sourceRef": "edgar:panel:x",
            "stock_code": "AAPL",
            "rcept_dt": "20260101",
            "section_title": "10-K",
            "score": 1.0,
        },
    ]

    ranked = rankBySemanticConstraints(hits, plan)

    assert ranked[0]["sourceRef"] == "edgar:panel:x"
    assert ranked[0]["constraintViolationReason"] == ""
    assert "constraintMismatch:sourceClass" in ranked[1]["constraintViolationReason"]


def test_rank_by_semantic_constraints_prefers_fresher_equal_constraint_rows() -> None:
    plan = planSemanticConstraints(
        "메디톡스 2026 자기주식 취득 공시 원문",
        mapper=compileSemanticMapperFromRows(
            [
                {"source": "allFilings", "corp_name": "메디톡스", "stock_code": "086900"},
            ]
        ),
    )
    hits = [
        {
            "source": "allFilings",
            "sourceRef": "dart:old",
            "stock_code": "086900",
            "rcept_dt": "20260101",
            "report_nm": "주요사항보고서(자기주식취득결정)",
            "score": 100.0,
        },
        {
            "source": "allFilings",
            "sourceRef": "dart:new",
            "stock_code": "086900",
            "rcept_dt": "20260617",
            "report_nm": "주요사항보고서(자기주식취득결정)",
            "score": 1.0,
        },
    ]

    ranked = rankBySemanticConstraints(hits, plan)

    assert ranked[0]["sourceRef"] == "dart:new"


def test_rank_by_semantic_constraints_prefers_query_topic_surface() -> None:
    mapper = compileSemanticMapperFromRows([{"source": "allFilings", "corp_name": "KX", "stock_code": "122450"}])
    plan = planSemanticConstraints("KX 2026 합병 공시 원문", mapper=mapper)
    hits = [
        {
            "source": "allFilings",
            "sourceRef": "dart:unrelated",
            "stock_code": "122450",
            "rcept_dt": "20260617",
            "report_nm": "주주명부폐쇄기간또는기준일설정",
            "score": 100.0,
        },
        {
            "source": "allFilings",
            "sourceRef": "dart:merger",
            "stock_code": "122450",
            "rcept_dt": "20260617",
            "report_nm": "주요사항보고서(회사합병결정)",
            "score": 1.0,
        },
    ]

    ranked = rankBySemanticConstraints(hits, plan)

    assert ranked[0]["sourceRef"] == "dart:merger"


def test_rank_by_semantic_constraints_prefers_result_phase_when_query_is_generic() -> None:
    mapper = compileSemanticMapperFromRows([{"source": "allFilings", "corp_name": "메타랩스", "stock_code": "090370"}])
    plan = planSemanticConstraints("메타랩스 2026 유상증자 공시 원문", mapper=mapper)
    hits = [
        {
            "source": "allFilings",
            "sourceRef": "dart:decision",
            "stock_code": "090370",
            "rcept_dt": "20260609",
            "report_nm": "주요사항보고서(유상증자결정)",
            "score": 100.0,
        },
        {
            "source": "allFilings",
            "sourceRef": "dart:result",
            "stock_code": "090370",
            "rcept_dt": "20260617",
            "report_nm": "유상증자또는주식관련사채등의발행결과(자율공시)",
            "score": 1.0,
        },
    ]

    ranked = rankBySemanticConstraints(hits, plan)

    assert plan.topicTerms == ("유상증자",)
    assert ranked[0]["sourceRef"] == "dart:result"
    sibling = next(row for row in ranked if row["sourceRef"] == "dart:decision")
    assert sibling["constraintViolationReason"] == "constraintSiblingDedup"


def test_rank_by_semantic_constraints_prefers_decision_when_query_says_decision() -> None:
    mapper = compileSemanticMapperFromRows([{"source": "allFilings", "corp_name": "메타랩스", "stock_code": "090370"}])
    plan = planSemanticConstraints("메타랩스 2026 유상증자 결정 공시 원문", mapper=mapper)
    hits = [
        {
            "source": "allFilings",
            "sourceRef": "dart:result",
            "stock_code": "090370",
            "rcept_dt": "20260617",
            "report_nm": "유상증자또는주식관련사채등의발행결과(자율공시)",
            "score": 100.0,
        },
        {
            "source": "allFilings",
            "sourceRef": "dart:decision",
            "stock_code": "090370",
            "rcept_dt": "20260609",
            "report_nm": "주요사항보고서(유상증자결정)",
            "score": 1.0,
        },
    ]

    ranked = rankBySemanticConstraints(hits, plan)

    assert ranked[0]["sourceRef"] == "dart:decision"


def test_rank_by_semantic_constraints_prefers_major_shareholder_change_report() -> None:
    mapper = compileSemanticMapperFromRows([{"source": "allFilings", "corp_name": "팬오션", "stock_code": "028670"}])
    plan = planSemanticConstraints("팬오션 2026 최대주주 변경 공시 원문", mapper=mapper)
    hits = [
        {
            "source": "allFilings",
            "sourceRef": "dart:bulk-holding",
            "stock_code": "028670",
            "rcept_dt": "20260617",
            "report_nm": "주식등의대량보유상황보고서(일반)",
            "score": 100.0,
        },
        {
            "source": "allFilings",
            "sourceRef": "dart:major-shareholder",
            "stock_code": "028670",
            "rcept_dt": "20260617",
            "report_nm": "최대주주등소유주식변동신고서",
            "score": 1.0,
        },
    ]

    ranked = rankBySemanticConstraints(hits, plan)

    assert ranked[0]["sourceRef"] == "dart:major-shareholder"
    assert ranked[0]["semanticPhaseScore"] > 0


def test_rank_by_semantic_constraints_marks_unrelated_topic_unanswerable() -> None:
    mapper = compileSemanticMapperFromRows([{"source": "allFilings", "corp_name": "메타랩스", "stock_code": "090370"}])
    plan = planSemanticConstraints("메타랩스 2026 유상증자 공시 원문", mapper=mapper)
    hits = [
        {
            "source": "allFilings",
            "sourceRef": "dart:unrelated",
            "stock_code": "090370",
            "rcept_dt": "20260617",
            "report_nm": "기업지배구조보고서공시",
            "score": 100.0,
        },
        {
            "source": "allFilings",
            "sourceRef": "dart:result",
            "stock_code": "090370",
            "rcept_dt": "20260617",
            "report_nm": "유상증자또는주식관련사채등의발행결과(자율공시)",
            "score": 1.0,
        },
    ]

    ranked = rankBySemanticConstraints(hits, plan)

    assert ranked[0]["sourceRef"] == "dart:result"
    unrelated = next(row for row in ranked if row["sourceRef"] == "dart:unrelated")
    assert "constraintMismatch:topic" in unrelated["constraintViolationReason"]


def test_rank_by_semantic_constraints_marks_edgar_topic_mismatch_unanswerable() -> None:
    mapper = compileSemanticMapperFromRows([{"source": "edgar-panel", "corp_name": "ADI", "stock_code": "ADI"}])
    plan = planSemanticConstraints("ADI 2026 유상증자 공시 원문", mapper=mapper)
    hits = [
        {
            "source": "edgar-panel",
            "sourceRef": "edgar:panel:adi-10q",
            "stock_code": "ADI",
            "rcept_dt": "20260617",
            "section_title": "10-Q liquidity",
            "snippet": "liquidity and capital resources",
            "score": 100.0,
        }
    ]

    ranked = rankBySemanticConstraints(hits, plan)

    assert plan.sourceClasses == ("edgar",)
    assert plan.topicTerms == ("유상증자",)
    assert "constraintMismatch:topic" in ranked[0]["constraintViolationReason"]


def test_rank_by_semantic_constraints_marks_later_sibling_unanswerable() -> None:
    mapper = compileSemanticMapperFromRows([{"source": "allFilings", "corp_name": "KX", "stock_code": "122450"}])
    plan = planSemanticConstraints("KX 2026 합병 공시 원문", mapper=mapper)
    hits = [
        {
            "source": "allFilings",
            "sourceRef": "dart:primary",
            "stock_code": "122450",
            "rcept_dt": "20260617",
            "report_nm": "주요사항보고서(회사합병결정)",
            "score": 10.0,
        },
        {
            "source": "allFilings",
            "sourceRef": "dart:sibling",
            "stock_code": "122450",
            "rcept_dt": "20260617",
            "report_nm": "회사합병결정(종속회사의주요경영사항)",
            "score": 9.0,
        },
    ]

    ranked = rankBySemanticConstraints(hits, plan)

    assert ranked[0]["sourceRef"] == "dart:primary"
    sibling = next(row for row in ranked if row["sourceRef"] == "dart:sibling")
    assert sibling["constraintViolationReason"] == "constraintSiblingDedup"


def test_row_source_class_normalizes_runtime_sources() -> None:
    assert rowSourceClass({"source": "news"}) == "news"
    assert rowSourceClass({"source": "allFilings"}) == "allFilings"
    assert rowSourceClass({"source": "panel"}) == "panel"
    assert rowSourceClass({"source": "edgar-panel"}) == "edgar"
