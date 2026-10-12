"""providers/dart/search/qualityGate.py mirror tests."""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.unit


def _gold_rows() -> list[dict[str, str]]:
    return [
        {
            "query": "삼보산업 유상증자 공시 원문",
            "target": "filing",
            "expectedSourceRef": "dart:allFilings:20260612000344#section=0",
            "goldOrigin": "real",
            "reviewStatus": "reviewed",
        },
        {
            "query": "PCE 전문가 뉴스 원문",
            "target": "news",
            "expectedSourceRef": "news:kb-20260612-pce",
            "goldOrigin": "real",
            "reviewStatus": "reviewed",
        },
        {
            "query": "가상상장사999 20990101 합병 공시 원문",
            "target": "noAnswer",
            "goldOrigin": "real",
            "reviewStatus": "reviewed",
        },
    ]


def _results() -> dict[str, list[dict[str, object]]]:
    return {
        "삼보산업 유상증자 공시 원문": [
            {
                "source": "allFilings",
                "sourceRef": "dart:allFilings:20260612000344#section=0",
                "answerable": True,
                "dataAsOf": "20260612",
            }
        ],
        "PCE 전문가 뉴스 원문": [
            {
                "source": "news",
                "sourceRef": "news:kb-20260612-pce",
                "answerable": True,
                "dataAsOf": "20260612",
            }
        ],
        "가상상장사999 20990101 합병 공시 원문": [
            {"source": "allFilings", "sourceRef": "dart:allFilings:other#section=0", "answerable": False}
        ],
    }


def test_evaluate_query_gold_rows_marks_release_eligible_for_real_reviewed_gold() -> None:
    from dartlab.providers.dart.search.qualityGate import evaluateQueryGoldRows

    report = evaluateQueryGoldRows(_gold_rows(), _results(), minRows=3)

    assert report["releaseEligible"] is True
    assert report["metrics"]["overallReadyRate"] == 1.0
    assert report["metrics"]["docHit10"] == 1.0
    assert report["metrics"]["memoryCitationTop3Exact"] == 1.0
    assert report["metrics"]["newsSourcePrecision10"] == 1.0
    assert report["metrics"]["noAnswerFalseAcceptRate"] == 0.0


def test_evaluate_query_gold_rows_blocks_proxy_gold() -> None:
    from dartlab.providers.dart.search.qualityGate import evaluateQueryGoldRows

    rows = _gold_rows()
    rows[0]["goldOrigin"] = "runtimeGenerated"
    report = evaluateQueryGoldRows(rows, _results(), minRows=3)

    assert report["releaseEligible"] is False
    assert "proxyGoldRows:1" in report["blockers"]


def test_evaluate_query_gold_rows_allows_proxy_only_for_experiment_mode() -> None:
    from dartlab.providers.dart.search.qualityGate import evaluateQueryGoldRows

    rows = _gold_rows()
    rows[0]["goldOrigin"] = "runtimeGenerated"

    report = evaluateQueryGoldRows(rows, _results(), minRows=3, requireRealReviewed=False)

    assert report["releaseEligible"] is True
    assert report["realReviewedRows"] == 2


def test_evaluate_query_gold_rows_matches_results_by_query_id() -> None:
    from dartlab.providers.dart.search.qualityGate import evaluateQueryGoldRows

    rows = [
        {
            "queryId": "q1",
            "query": "유상증자 공시",
            "target": "filing",
            "expectedSourceRef": "dart:allFilings:1#section=0",
            "goldOrigin": "real",
            "reviewStatus": "reviewed",
        },
        {
            "queryId": "q2",
            "query": "없는 공시",
            "target": "noAnswer",
            "goldOrigin": "real",
            "reviewStatus": "reviewed",
        },
    ]
    results = {
        "q1": [{"source": "allFilings", "sourceRef": "dart:allFilings:1#section=0", "answerable": True}],
        "q2": [{"source": "allFilings", "sourceRef": "dart:allFilings:other#section=0", "answerable": False}],
    }

    report = evaluateQueryGoldRows(rows, results, minRows=2, requiredTargets=("filing", "noAnswer"))

    assert report["releaseEligible"] is True
    assert report["metrics"]["overallReadyRate"] == 1.0


def test_build_miss_ledger_rows_records_doc_miss_and_false_accept() -> None:
    from dartlab.providers.dart.search.qualityGate import buildMissLedgerRows

    results = _results()
    results["삼보산업 유상증자 공시 원문"] = [
        {"source": "allFilings", "sourceRef": "dart:allFilings:wrong#section=0", "answerable": True}
    ]
    results["가상상장사999 20990101 합병 공시 원문"] = [
        {"source": "allFilings", "sourceRef": "dart:allFilings:wrong#section=0", "answerable": True}
    ]

    rows = buildMissLedgerRows(_gold_rows(), results)

    failureTypes = {row["failureType"] for row in rows}
    assert "docMiss10" in failureTypes
    assert "falseAccept" in failureTypes
    assert {row["policyCandidate"] for row in rows} >= {"rankingOrFacetPolicy", "negativeAnswerabilityPolicy"}


def test_evaluate_query_gold_rows_does_not_count_unanswerable_doc_hit() -> None:
    from dartlab.providers.dart.search.qualityGate import evaluateQueryGoldRows

    rows = _gold_rows()
    results = _results()
    results["삼보산업 유상증자 공시 원문"] = [
        {
            "source": "allFilings",
            "sourceRef": "dart:allFilings:20260612000344#section=0",
            "answerable": False,
            "notAnswerableReason": "missingDataAsOf",
        }
    ]

    report = evaluateQueryGoldRows(rows, results, minRows=3)

    assert report["releaseEligible"] is False
    assert report["rows"][0]["docHit10"] is False
    assert report["metrics"]["docHit10"] < 1.0


def test_evaluate_query_gold_rows_accepts_semantic_filing_event_hit() -> None:
    from dartlab.providers.dart.search.qualityGate import evaluateQueryGoldRows

    rows = [
        {
            "query": "유상증자 공시 원문",
            "target": "filing",
            "expectedSourceRef": "dart:allFilings:reviewed-example#section=0",
            "goldOrigin": "real",
            "reviewStatus": "reviewed",
        }
    ]
    results = {
        "유상증자 공시 원문": [
            {
                "source": "allFilings",
                "sourceRef": "dart:allFilings:newer-relevant#section=0",
                "report_nm": "[기재정정]주요사항보고서(유상증자결정)",
                "answerable": True,
            }
        ]
    }

    report = evaluateQueryGoldRows(rows, results, minRows=1, requiredTargets=("filing",))

    assert report["releaseEligible"] is True
    assert report["rows"][0]["matchMode"] == "semantic"
    assert report["metrics"]["docHit10"] == 1.0
    assert report["metrics"]["exactDocHit10"] == 0.0


def test_evaluate_query_gold_rows_accepts_curated_synonym_event_hit() -> None:
    from dartlab.providers.dart.search.qualityGate import evaluateQueryGoldRows

    rows = [
        {
            "query": "대규모 수주 계약 공시",
            "target": "filing",
            "expectedSourceRef": "dart:allFilings:reviewed-supply-contract#section=0",
            "goldOrigin": "real",
            "reviewStatus": "reviewed",
        }
    ]
    results = {
        "대규모 수주 계약 공시": [
            {
                "source": "allFilings",
                "sourceRef": "dart:allFilings:newer-supply-contract#section=0",
                "report_nm": "단일판매ㆍ공급계약체결",
                "answerable": True,
            }
        ]
    }

    report = evaluateQueryGoldRows(rows, results, minRows=1, requiredTargets=("filing",))

    assert report["releaseEligible"] is True
    assert report["rows"][0]["matchMode"] == "semantic"


def test_evaluate_query_gold_rows_accepts_dynamic_news_semantic_hit() -> None:
    from dartlab.providers.dart.search.qualityGate import evaluateQueryGoldRows

    rows = [
        {
            "query": "뉴스로 신제품 출시",
            "target": "news",
            "expectedSourceRef": "news:reviewed-old",
            "goldOrigin": "real",
            "reviewStatus": "reviewed",
        }
    ]
    results = {
        "뉴스로 신제품 출시": [
            {
                "source": "news",
                "sourceRef": "news:fresh-relevant",
                "section_title": "LG전자, 무선청소기 신제품 출시",
                "answerable": True,
            }
        ]
    }

    report = evaluateQueryGoldRows(rows, results, minRows=1, requiredTargets=("news",))

    assert report["releaseEligible"] is True
    assert report["rows"][0]["matchMode"] == "semantic"
    assert report["metrics"]["exactDocHit10"] == 0.0


def _topicGold(query: str, target: str) -> list[dict]:
    return [
        {
            "query": query,
            "target": target,
            "expectedSourceRef": "dart:panel:expected#section=0",
            "goldOrigin": "real",
            "reviewStatus": "reviewed",
        }
    ]


def test_evaluate_query_gold_rows_body_topic_needs_topic_words_not_report_type() -> None:
    from dartlab.providers.dart.search.qualityGate import evaluateQueryGoldRows

    query = "환율 리스크 사업보고서 본문"
    reportOnly = {
        "source": "panel",
        "sourceRef": "dart:panel:report-only#section=0",
        "report_nm": "사업보고서 (2025.12)",
        "text": "환율 변동",
        "answerable": True,
    }
    report = evaluateQueryGoldRows(_topicGold(query, "filing"), {query: [reportOnly]}, minRows=1)
    assert report["rows"][0]["matchMode"] == "miss"

    edgar = {**reportOnly, "source": "edgar-panel", "text": "환율 리스크"}
    report = evaluateQueryGoldRows(_topicGold(query, "filing"), {query: [edgar]}, minRows=1)
    assert report["rows"][0]["matchMode"] == "miss"

    covered = {**reportOnly, "text": "환율 리스크 관리"}
    report = evaluateQueryGoldRows(_topicGold(query, "filing"), {query: [covered]}, minRows=1)
    assert report["rows"][0]["matchMode"] == "semantic"
    assert report["metrics"]["exactDocHit10"] == 0.0


def test_evaluate_query_gold_rows_edgar_topic_reads_chunk_evidence() -> None:
    import json

    from dartlab.providers.dart.search.qualityGate import evaluateQueryGoldRows

    query = "EDGAR goodwill impairment risk"
    cards = [{"label": "chunk", "value": "evidenceText", "evidence": "Notes: Goodwill, Impairment, Risk Management"}]
    row = {
        "source": "edgar-panel",
        "sourceRef": "edgar:panel:other#section=0",
        "report_nm": "10-K (2025Q4)",
        "text": "UNITED STATES SECURITIES AND EXCHANGE COMMISSION",
        "fieldCards": json.dumps(cards),
        "answerable": True,
    }
    report = evaluateQueryGoldRows(_topicGold(query, "edgar"), {query: [row]}, minRows=1)
    assert report["rows"][0]["matchMode"] == "semantic"

    dart = {**row, "source": "panel", "sourceRef": "dart:panel:other#section=0"}
    report = evaluateQueryGoldRows(_topicGold(query, "edgar"), {query: [dart]}, minRows=1)
    assert report["rows"][0]["matchMode"] == "miss"


def test_evaluate_query_gold_rows_reports_metrics_by_kind_for_edgar() -> None:
    from dartlab.providers.dart.search.qualityGate import evaluateQueryGoldRows

    rows = [
        {
            "query": "AAPL risk factor 10-K",
            "target": "edgar",
            "expectedSourceRef": "edgar:0000320193-26-000001",
            "goldOrigin": "real",
            "reviewStatus": "reviewed",
        }
    ]
    results = {
        "AAPL risk factor 10-K": [
            {"source": "edgar-panel", "sourceRef": "edgar:0000320193-26-000001", "answerable": True}
        ]
    }

    report = evaluateQueryGoldRows(rows, results, minRows=1, requiredTargets=("edgar",))

    assert report["releaseEligible"] is True
    assert report["metricsByKind"]["edgar"]["rows"] == 1
    assert report["metricsByKind"]["edgar"]["docHit10"] == 1.0


def test_evaluate_query_gold_rows_blocks_forbidden_hard_negative_top3() -> None:
    from dartlab.providers.dart.search.qualityGate import evaluateQueryGoldRows

    rows = [
        {
            "query": "삼성전자 2024 유상증자 결정 공시",
            "target": "filing",
            "expectedSourceRef": "dart:allFilings:decision#section=0",
            "forbiddenSourceRefs": ["dart:allFilings:correction#section=0"],
            "constraintTags": ["same-company-sibling-filing"],
            "goldOrigin": "real",
            "reviewStatus": "reviewed",
        }
    ]
    results = {
        "삼성전자 2024 유상증자 결정 공시": [
            {
                "source": "allFilings",
                "sourceRef": "dart:allFilings:correction#section=0",
                "answerable": True,
            },
            {
                "source": "allFilings",
                "sourceRef": "dart:allFilings:decision#section=0",
                "answerable": True,
            },
        ]
    }

    report = evaluateQueryGoldRows(rows, results, minRows=1, requiredTargets=("filing",))

    assert report["releaseEligible"] is False
    assert report["metrics"]["exactDocHit10"] == 1.0
    assert report["metrics"]["hardNegativeExactDocHit10"] == 1.0
    assert report["metrics"]["hardNegativeWinRate"] == 0.0
    assert report["metrics"]["forbiddenTop3Rate"] == 1.0
    assert report["metrics"]["constraintViolationRate"] == 1.0
    assert "metric:forbiddenTop3Rate:1.0000>0.0000" in report["blockers"]


def test_evaluate_query_gold_rows_blocks_forbidden_source_family_leak() -> None:
    from dartlab.providers.dart.search.qualityGate import evaluateQueryGoldRows

    rows = [
        {
            "query": "공시 말고 뉴스로 현대차 배당 확대",
            "target": "news",
            "expectedSourceRef": "news:hyundai-dividend",
            "forbiddenSourceFamilies": ["filing"],
            "constraintTags": ["news-filing-confusion"],
            "goldOrigin": "real",
            "reviewStatus": "reviewed",
        }
    ]
    results = {
        "공시 말고 뉴스로 현대차 배당 확대": [
            {"source": "news", "sourceRef": "news:hyundai-dividend", "answerable": True},
            {"source": "allFilings", "sourceRef": "dart:allFilings:dividend", "answerable": True},
        ]
    }

    report = evaluateQueryGoldRows(rows, results, minRows=1, requiredTargets=("news",))

    assert report["releaseEligible"] is False
    assert report["metrics"]["hardNegativeWinRate"] == 1.0
    assert report["metrics"]["sourceIntentLeakRate"] == 1.0
    assert report["metrics"]["forbiddenTop3Rate"] == 1.0
    assert "metric:sourceIntentLeakRate:1.0000>0.0000" in report["blockers"]


def test_build_miss_ledger_rows_records_policy_taxonomy_from_answerability() -> None:
    from dartlab.providers.dart.search.qualityGate import buildMissLedgerRows

    rows = [
        {
            "query": "삼성전자 대표이사 변경",
            "target": "filing",
            "expectedSourceRef": "dart:allFilings:expected",
            "goldOrigin": "real",
            "reviewStatus": "reviewed",
        }
    ]
    results = {
        "삼성전자 대표이사 변경": [
            {
                "source": "allFilings",
                "sourceRef": "dart:allFilings:wrong",
                "answerable": False,
                "notAnswerableReason": "facetMismatch:company",
            }
        ]
    }

    misses = buildMissLedgerRows(rows, results)

    failureTypes = {row["failureType"] for row in misses}
    assert "docMiss10" in failureTypes
    assert "entityFacetMiss" in failureTypes
    assert {row["policyCandidate"] for row in misses} >= {"rankingOrFacetPolicy", "facetPlannerPolicy"}


def test_load_query_gold_reads_jsonl_and_write_miss_ledger(tmp_path) -> None:
    from dartlab.providers.dart.search.qualityGate import buildMissLedgerRows, loadQueryGold, writeMissLedger

    path = tmp_path / "gold.jsonl"
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in _gold_rows()), encoding="utf-8")

    rows = loadQueryGold(path)
    misses = buildMissLedgerRows(rows, {"삼보산업 유상증자 공시 원문": []})
    out = tmp_path / "miss.jsonl"
    writeMissLedger(out, misses)

    assert len(rows) == 3
    assert out.exists()
