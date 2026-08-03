"""투자 의사결정 메모는 기존 엔진 결과를 9차원 상태로 정직하게 조립한다."""

from __future__ import annotations

from dartlab.story.investmentMemo import buildInvestmentDecision


def _product(engine: str, *, status: str = "usable") -> dict:
    return {
        "status": status,
        "identity": {"engine": engine},
        "time": {"asOf": "2026-08-01"},
        "conclusion": {"summary": f"{engine} 대표 판단"},
        "claims": [
            {
                "id": claim_id,
                "label": label,
                "value": value,
                "unit": "%",
                "status": "observed",
            }
            for claim_id, label, value in (
                ("analysis.revenueCagr", "매출 CAGR", 8.0),
                ("analysis.operatingIncomeCagr", "영업이익 CAGR", 12.0),
                ("analysis.operatingMargin", "영업이익률", 14.0),
            )
        ]
        if engine == "analysis"
        else [],
        "evidence": [{"id": f"{engine}:evidence", "sourceRef": f"{engine}:source"}],
        "gaps": [] if status == "usable" else [{"reason": "부분 근거"}],
    }


def test_investment_memo_has_stable_nine_dimension_contract() -> None:
    result = buildInvestmentDecision(
        thesis={
            "central": "초과수익이 유지되는 동안 가치가 창출된다.",
            "bearCase": "수익성 하락이 구조화되면 논지가 깨진다.",
            "triggers": ["ROIC-WACC가 0%p 미만"],
            "pillars": [{"refs": [{"id": "thesis:1"}]}],
        },
        lensProducts={engine: _product(engine) for engine in ("analysis", "industry", "macro")},
        lensTensions={"items": []},
        valuation={
            "current": 70000,
            "intrinsic": 80000,
            "reverseDcf": {"verdict": "현재가는 8% 성장을 반영"},
        },
        scenarios={
            "legs": [
                {"key": "bear", "intrinsic": 50000, "upside": -28.6, "growth": -2},
                {"key": "base", "intrinsic": 80000, "upside": 14.3, "growth": 5},
                {"key": "bull", "intrinsic": 100000, "upside": 42.9, "growth": 9},
            ]
        },
        catalystEvents=[
            {
                "status": "observed",
                "title": "다음 실적 발표",
                "date": "2026-10-30",
                "refs": ["event:1"],
            }
        ],
        asOf="2026-08-03",
    )

    assert result["requiredDimensionCount"] == 9
    assert result["usableDimensionCount"] == 9
    assert result["decisionStatus"] == "supported"
    assert result["dimensions"]["counterThesis"]["claim"].startswith("수익성 하락")
    assert result["dimensions"]["valuation"]["details"]["upside"] == 14.3
    assert result["policy"]["personalizedTradeInstruction"] is False
    assert result["policy"]["scenarioProbabilitiesPublished"] is False


def test_investment_memo_does_not_fill_missing_dimensions_with_generalities() -> None:
    result = buildInvestmentDecision(
        thesis={},
        lensProducts={},
        lensTensions={},
        valuation={},
        scenarios={},
        asOf=None,
    )

    assert result["decisionStatus"] == "insufficient"
    assert result["usableDimensionCount"] == 0
    assert all(row["status"] == "blocked" for row in result["dimensions"].values())
    assert result["dimensions"]["catalysts"]["claim"] == ""


def test_catalyst_can_be_not_observed_only_after_complete_coverage() -> None:
    result = buildInvestmentDecision(
        thesis={},
        lensProducts={},
        lensTensions={},
        valuation={},
        scenarios={},
        asOf="2026-08-03",
        catalystEvents=[{"coverageComplete": True, "status": "none"}],
    )

    assert result["dimensions"]["catalysts"]["status"] == "notObserved"
    assert result["dimensions"]["catalysts"]["claim"] == "관측된 근접 촉매 없음"


def test_partial_core_can_be_supported_when_seven_dimensions_are_usable() -> None:
    products = {engine: _product(engine) for engine in ("analysis", "industry", "macro")}
    products["analysis"]["status"] = "partial"
    products["analysis"]["claims"] = products["analysis"]["claims"][:1]
    result = buildInvestmentDecision(
        thesis={
            "central": "검증 가능한 중심논지",
            "bearCase": "검증 가능한 반대논지",
            "triggers": ["정량 무효화 조건"],
        },
        lensProducts=products,
        lensTensions={},
        valuation={"current": 70000, "intrinsic": 80000},
        scenarios={
            "legs": [
                {"key": "bear", "intrinsic": 50000, "upside": -28.6, "growth": 0.8},
                {"key": "base", "intrinsic": 80000, "upside": 14.3, "growth": 1.0},
                {"key": "bull", "intrinsic": 100000, "upside": 42.9, "growth": 1.2},
            ]
        },
        catalystEvents=[{"status": "observed", "title": "실적 발표"}],
        asOf="2026-08-03",
    )

    assert result["dimensions"]["earningsInflection"]["status"] == "partial"
    assert result["dimensions"]["valuation"]["status"] == "partial"
    assert result["usableDimensionCount"] == 7
    assert result["decisionStatus"] == "supported"
