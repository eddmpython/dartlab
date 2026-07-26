from __future__ import annotations

import pytest
from fastapi import HTTPException

from dartlab.server.api import company as companyApi
from dartlab.story import lensProducts


class _Company:
    stockCode = "005930"
    market = "KR"


def test_company_lenses_route_excludes_internal_results(monkeypatch):
    monkeypatch.setattr(companyApi, "get_company", lambda code: _Company())
    monkeypatch.setattr(
        lensProducts,
        "collectLensProducts",
        lambda company: {
            "schemaVersion": 1,
            "target": company.stockCode,
            "market": company.market,
            "engines": [],
            "products": {},
            "tensions": {
                "schemaVersion": 1,
                "items": [],
                "evaluations": [
                    {"patternId": pattern, "status": "blocked", "reason": "missingProduct"}
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
            "results": {"analysis": {"private": True}},
            "statusCounts": {},
            "gaps": [],
            "noComposite": True,
        },
    )

    payload = companyApi.apiCompanyLenses("005930")

    assert payload["target"] == "005930"
    assert payload["noComposite"] is True
    assert payload["tensions"]["items"] == []
    assert "results" not in payload


def test_company_lenses_route_rejects_invalid_public_contract(monkeypatch):
    monkeypatch.setattr(companyApi, "get_company", lambda code: _Company())
    monkeypatch.setattr(
        lensProducts,
        "collectLensProducts",
        lambda company: {
            "schemaVersion": 1,
            "target": company.stockCode,
            "market": company.market,
            "engines": ["analysis"],
            "products": {"analysis": {"status": "usable"}},
            "tensions": {},
            "results": {},
            "statusCounts": {"usable": 1},
            "gaps": [],
            "noComposite": True,
        },
    )

    with pytest.raises(HTTPException) as excInfo:
        companyApi.apiCompanyLenses("005930")
    assert excInfo.value.status_code == 404
    assert "필수 키" in str(excInfo.value.detail)
