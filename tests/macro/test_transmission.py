from __future__ import annotations

from pathlib import Path

import polars as pl


class FakeGather:
    def macro(self, seriesId: str) -> pl.DataFrame:
        base = float(len(seriesId))
        return pl.DataFrame(
            {
                "date": ["2026-04-30", "2026-05-31"],
                "value": [base, base + 1.5],
            }
        )


def testAnalyzeTransmissionReturnsSectorEdgesWithLineage(monkeypatch) -> None:
    from dartlab.macro.transmission import transmission

    monkeypatch.setattr(transmission, "getGather", lambda asOf=None: FakeGather())
    result = transmission.analyzeTransmission(market="KR", sectorKey="semiconductor")

    assert result["market"] == "KR"
    assert result["drivers"]
    assert result["edges"]
    assert result["dataAsOf"] == "2026-05-31"
    assert result["product"]["status"] == "partial"
    assert result["product"]["payload"]["companyBound"] is False
    assert {edge["evidenceLabel"] for edge in result["edges"]} <= {"OBS", "PRIOR", "TPL"}
    assert {"fx-export-revenue", "export-demand-revenue", "rate-debt-interest"} <= {
        edge["id"] for edge in result["edges"]
    }
    for driver in result["drivers"]:
        lineage = driver["sourceLineage"]
        assert lineage["sourceSeriesId"] == driver["sourceSeriesId"]
        assert lineage["date"] == "2026-05-31"
        assert lineage["value"] is not None
        assert lineage["artifactPath"].startswith("macro/")


def testMacroTransmissionPublicDispatch(monkeypatch) -> None:
    import dartlab
    from dartlab.macro.transmission import transmission

    monkeypatch.setattr(transmission, "getGather", lambda asOf=None: FakeGather())
    result = dartlab.macro("전파", market="KR", sectorKey="bank")

    assert result["market"] == "KR"
    assert any(edge["id"] == "rate-bank-margin" for edge in result["edges"])
    assert result["sourceRefs"][0] == "dartlab://macro/transmission"


def testCompanyTransmissionBindsFinancialEvidence(monkeypatch) -> None:
    from dartlab.macro.transmission import transmission

    monkeypatch.setattr(transmission, "getGather", lambda asOf=None: FakeGather())
    companyEvidence = [
        {
            "id": "analysis.debtRatio",
            "label": "부채비율",
            "value": 42.0,
            "unit": "%",
            "status": "derived",
            "sourceRef": "dartlab://analysis/005930/product/drivers/debtRatio",
        },
        {
            "id": "analysis.interestCoverage",
            "label": "이자보상배율",
            "value": 15.0,
            "unit": "배",
            "status": "derived",
            "sourceRef": "dartlab://analysis/005930/product/drivers/interestCoverage",
        },
    ]

    result = transmission.analyzeTransmission(
        market="KR",
        sectorKey="semiconductor",
        stockCode="005930",
        companyEvidence=companyEvidence,
        asOf="2026-06-01",
    )

    rateEdge = next(edge for edge in result["edges"] if edge["id"] == "rate-debt-interest")
    assert rateEdge["resolvedEvidenceLevel"] == "companyObserved"
    assert rateEdge["companyEvidenceCoverage"] == 0.5
    assert rateEdge["impactDirection"] == "headwind"
    assert result["product"]["status"] == "partial"
    assert result["product"]["identity"]["target"] == "005930"
    assert result["product"]["payload"]["companyEdgeCount"] >= 1
    claim = next(row for row in result["product"]["claims"] if row["id"] == "macro.companyTransmission")
    assert claim["direction"] == "adverse"
    assert claim["basis"] == "macroCompanyEdges"


def testMacroTransmissionBuildsCompanyContextInsideMacroLayer(monkeypatch) -> None:
    from dartlab.macro import Macro
    from dartlab.macro.transmission import transmission

    class Company:
        stockCode = "005930"

        def industry(self):
            return {"industry": "semiconductor", "stage": "fab", "stageName": "전공정"}

        def analysis(self, axis):
            assert axis == "종합평가"
            return {
                "product": {
                    "drivers": [
                        {
                            "id": "debtRatio",
                            "label": "부채비율",
                            "value": 42.0,
                            "unit": "%",
                            "period": "2025",
                            "direction": "positive",
                        }
                    ]
                }
            }

    monkeypatch.setattr(transmission, "getGather", lambda asOf=None: FakeGather())
    result = Macro()("전파", market="KR", company=Company())

    assert result["stockCode"] == "005930"
    assert result["sectorKey"] == "semiconductor"
    assert result["product"]["payload"]["companyBound"] is True


def testTransmissionTargetPositionalDoesNotCollideWithMarket(monkeypatch) -> None:
    import dartlab
    from dartlab.macro.transmission import transmission

    monkeypatch.setattr(transmission, "getGather", lambda asOf=None: FakeGather())
    result = dartlab.macro("전파", "ignored-target", market="KR", sectorKey="bank")

    assert result["market"] == "KR"
    assert any(edge["id"] == "rate-bank-margin" for edge in result["edges"])


def testTransmissionDoesNotImportCompanyOrAnalysis() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / "src" / "dartlab" / "macro" / "transmission" / "transmission.py").read_text(encoding="utf-8")

    assert "dartlab.analysis" not in source
    assert "dartlab.company" not in source
    assert "Company(" not in source
