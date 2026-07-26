from __future__ import annotations

from tests.calibration.lensProductCalibration import auditBundle, enrichCandidateTags, selectCohort, summarizeRun


def _candidate(code: str, industry: str, value: float) -> dict:
    return {
        "stockCode": code,
        "name": code,
        "industryId": industry,
        "industryName": industry,
        "industryConfidence": 0.9,
        "scanAxes": ["debt", "growth", "profitability", "valuation"],
        "scanCoverage": 4,
        "metrics": {
            "marketCap": value,
            "operatingMargin": value,
            "revenueCagr": value,
            "debtRatio": value,
            "interestCoverage": value,
        },
    }


def _product(engine: str, *, status: str = "usable") -> dict:
    payload = {"blockRefs": []}
    evidence = [{"id": f"{engine}.x", "kind": "calculation", "sourceRef": "dartlab://x", "status": "derived"}]
    score = 100.0
    if engine == "analysis":
        payload["coverage"] = {"observedRequiredDomains": 4}
    elif engine == "credit":
        payload["coverage"] = {"weightCoverage": 100.0}
    elif engine == "industry":
        payload["coverage"] = {
            "observedBlocks": 4,
            "totalBlocks": 4,
            "blocks": {"position": True},
        }
    elif engine == "quant":
        payload["classification"] = "confirmation"
        evidence = [
            {"id": f"quant.{index}", "kind": "calculation", "sourceRef": "dartlab://x", "status": "derived"}
            for index in range(3)
        ]
    else:
        payload.update({"companyBound": True, "companyEdgeCount": 1, "edgeCount": 1})
        evidence = [{"id": "macro.x", "kind": "macroObservation", "sourceRef": "dartlab://x", "status": "observed"}]
    return {
        "schemaVersion": 1,
        "identity": {"target": "005930", "market": "KR", "engine": engine, "axis": "x", "version": "1"},
        "time": {"asOf": "2026-07-18", "dataAsOf": "2026-07-18", "period": None, "knowledgeBoundary": "2026-07-18"},
        "status": status,
        "conclusion": {"label": "판단", "summary": "근거 기반 판단"},
        "confidence": {
            "level": "high",
            "score": score,
            "method": {
                "analysis": "requiredDomainCoverage",
                "credit": "validAxisWeightCoverage",
                "industry": "mappingConfidenceAndBlockCoverage",
                "quant": "threeBlockCoverageAndSignalClarity",
                "macro": "macroObservationAndCompanyEvidenceCoverage",
            }[engine],
        },
        "drivers": [],
        "evidence": evidence,
        "assumptions": [{"id": "expectationMethod"}] if engine == "quant" else [],
        "gaps": [],
        "scenarios": [],
        "falsifiers": [{"id": "break"}],
        "payload": payload,
    }


def test_select_cohort_is_deterministic_and_covers_industries():
    rows = [
        _candidate("000001", "semi", 1.0),
        _candidate("000002", "semi", 2.0),
        _candidate("000003", "bank", 3.0),
        _candidate("000004", "bio", 4.0),
        _candidate("000005", "auto", 5.0),
    ]

    first = selectCohort(rows, limit=4)
    second = selectCohort(list(reversed(rows)), limit=4)

    assert [row["stockCode"] for row in first] == [row["stockCode"] for row in second]
    assert {row["industryId"] for row in first} == {"semi", "bank", "bio", "auto"}


def test_candidate_tags_include_metric_quintiles_and_coverage():
    tagged = enrichCandidateTags([_candidate(f"{index:06d}", "industry", float(index)) for index in range(1, 11)])

    assert {tag for row in tagged for tag in row["tags"] if tag.startswith("band:marketCap:")} == {
        "band:marketCap:q1",
        "band:marketCap:q2",
        "band:marketCap:q3",
        "band:marketCap:q4",
        "band:marketCap:q5",
    }
    assert all("scanCoverage:4" in row["tags"] for row in tagged)


def test_audit_bundle_accepts_five_honest_products():
    bundle = {
        "schemaVersion": 1,
        "target": "005930",
        "market": "KR",
        "engines": ["analysis", "credit", "industry", "quant", "macro"],
        "products": {engine: _product(engine) for engine in ("analysis", "credit", "industry", "quant", "macro")},
        "statusCounts": {"usable": 5},
        "gaps": [],
        "noComposite": True,
    }

    result = auditBundle(bundle)

    assert result["productCount"] == 5
    assert result["hardIssueCount"] == 0


def test_audit_bundle_rejects_status_overclaim():
    bundle = {
        "target": "005930",
        "market": "KR",
        "products": {"analysis": _product("analysis")},
        "noComposite": True,
    }
    bundle["products"]["analysis"]["payload"]["coverage"]["observedRequiredDomains"] = 1

    result = auditBundle(bundle)

    assert any(issue["rule"] == "statusHonesty" for issue in result["issues"])


def test_summary_requires_all_four_gates():
    cohort = {"companies": [{"stockCode": "005930"}]}
    record = {
        "stockCode": "005930",
        "state": "calculated",
        "elapsedSeconds": 12.0,
        "peakRssMb": 500.0,
        "audit": {
            "productCount": 5,
            "statuses": {engine: "usable" for engine in ("analysis", "credit", "industry", "quant", "macro")},
            "issues": [],
            "reviewIssueCount": 0,
        },
    }

    result = summarizeRun(cohort, [record])

    assert result["excellent"] is True
    assert all(result["gates"].values())


def test_summary_rejects_nonblocked_but_never_usable_quant():
    cohort = {"companies": [{"stockCode": f"{index:06d}"} for index in range(4)]}
    records = []
    for index in range(4):
        statuses = {engine: "usable" for engine in ("analysis", "credit", "industry", "quant", "macro")}
        statuses["quant"] = "partial"
        records.append(
            {
                "stockCode": f"{index:06d}",
                "state": "calculated",
                "elapsedSeconds": 12.0,
                "peakRssMb": 500.0,
                "audit": {"productCount": 5, "statuses": statuses, "issues": [], "reviewIssueCount": 0},
            }
        )

    result = summarizeRun(cohort, records)

    assert result["utilityRates"]["quant"] == 1.0
    assert result["usableRates"]["quant"] == 0.0
    assert result["gates"]["decisivenessPassed"] is False
    assert result["excellent"] is False
