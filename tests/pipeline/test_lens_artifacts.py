from __future__ import annotations

import json

import pytest

from dartlab.pipeline import lensArtifacts


class _Company:
    stockCode = "005930"


def _bundle() -> dict:
    product = {
        "schemaVersion": 1,
        "identity": {
            "target": "005930",
            "market": "KR",
            "engine": "analysis",
            "axis": "종합평가",
            "version": "1",
        },
        "time": {
            "asOf": "2026-07-22",
            "dataAsOf": "2025Q4",
            "period": "2025Q4",
            "knowledgeBoundary": "2026-07-22",
        },
        "status": "usable",
        "conclusion": {"label": "양호", "summary": "검증된 테스트 제품"},
        "confidence": {"level": "medium", "score": 70.0, "method": "fixtureCoverage"},
        "drivers": [],
        "evidence": [
            {
                "id": "analysis.fixture",
                "kind": "fixture",
                "sourceRef": "fixture://analysis",
                "status": "derived",
            }
        ],
        "assumptions": [],
        "gaps": [],
        "scenarios": [],
        "falsifiers": [],
        "payload": {},
    }
    return {
        "schemaVersion": 1,
        "target": "005930",
        "market": "KR",
        "engines": ["analysis"],
        "products": {"analysis": product},
        "tensions": {
            "schemaVersion": 1,
            "items": [],
            "evaluations": [
                {"patternId": pattern, "status": "blocked", "reason": "missingTypedClaims"}
                for pattern in (
                    "fundamentalPriceDivergence",
                    "earningsCashDivergence",
                    "growthCreditTradeoff",
                    "industryExecutionCounterforce",
                    "macroCompanyCounterforce",
                )
            ],
            "noComposite": True,
        },
        "statusCounts": {"usable": 1},
        "gaps": [],
        "noComposite": True,
    }


def test_write_lens_artifact_is_public_and_stable(tmp_path, monkeypatch):
    monkeypatch.setattr(lensArtifacts, "buildLensArtifact", lambda company, refresh=False: _bundle())

    path = lensArtifacts.writeLensArtifact(_Company(), tmp_path, minProducts=1)

    assert path.name == "005930.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["noComposite"] is True
    assert "results" not in payload


def test_write_lens_artifact_refuses_product_floor_failure(tmp_path, monkeypatch):
    bundle = _bundle()
    bundle["products"] = {}
    monkeypatch.setattr(lensArtifacts, "buildLensArtifact", lambda company, refresh=False: bundle)

    with pytest.raises(RuntimeError, match="하한"):
        lensArtifacts.writeLensArtifact(_Company(), tmp_path, minProducts=1)


def test_build_lens_artifact_refuses_private_results(monkeypatch):
    from dartlab.story import lensProducts

    monkeypatch.setattr(lensProducts, "collectLensProducts", lambda company, refresh=False: {"results": {"x": 1}})
    monkeypatch.setattr(
        lensProducts,
        "publicLensBundle",
        lambda bundle: {**_bundle(), "results": bundle["results"]},
    )

    with pytest.raises(ValueError, match="내부 results"):
        lensArtifacts.buildLensArtifact(_Company())


def test_public_artifact_rejects_incomplete_product_and_tension(tmp_path, monkeypatch):
    invalidProduct = _bundle()
    invalidProduct["products"]["analysis"] = {"status": "usable"}
    monkeypatch.setattr(lensArtifacts, "buildLensArtifact", lambda company, refresh=False: invalidProduct)
    with pytest.raises(ValueError, match="필수 키"):
        lensArtifacts.writeLensArtifact(_Company(), tmp_path, minProducts=1)

    invalidTension = _bundle()
    invalidTension["tensions"]["items"] = [{"id": "fixture"}]
    invalidTension["tensions"]["evaluations"][0]["status"] = "active"
    monkeypatch.setattr(lensArtifacts, "buildLensArtifact", lambda company, refresh=False: invalidTension)
    with pytest.raises(ValueError, match="필수 키"):
        lensArtifacts.writeLensArtifact(_Company(), tmp_path, minProducts=1)


def test_unavailable_artifact_preserves_company_coverage_without_fake_products(tmp_path):
    path = lensArtifacts.writeUnavailableLensArtifact(
        "AAPL",
        tmp_path,
        market="US",
        reason="검증된 산업 taxonomy 없음",
    )
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["target"] == "AAPL"
    assert payload["products"] == {}
    assert payload["tensions"]["items"] == []
    assert len(payload["gaps"]) == 5
    assert {row["engine"] for row in payload["gaps"]} == {
        "analysis",
        "credit",
        "industry",
        "quant",
        "macro",
    }
    assert payload["noComposite"] is True
