"""Industry 회사 대표 제품 계약 회귀."""

from __future__ import annotations

import pytest

from dartlab.industry.product import blockedIndustryResult, buildIndustryProduct

pytestmark = pytest.mark.unit


class _Company:
    stockCode = "005930"
    market = "KR"


def _result() -> dict:
    return {
        "stockCode": "005930",
        "market": "KR",
        "industry": "semiconductor",
        "industryName": "반도체",
        "stage": "fab",
        "stageName": "전공정",
        "role": "제조",
        "stream": "midstream",
        "confidence": 0.9,
        "source": "manual",
        "updatedAt": "2026-04-14",
        "peers": [{"stockCode": "000660", "corpName": "SK하이닉스", "confidence": 0.9}],
        "sectorMetrics": {
            "peerCount": 25,
            "myOpmPercentile": 82.0,
            "myCagrPercentile": 65.0,
            "myRoePercentile": 70.0,
        },
        "sectorCycle": {"phase": "확장", "direction": "개선", "confidence": 0.5},
        "profitPool": {
            "판정": "집중형",
            "리더_끝해": ("fab", "전공정"),
            "stage시계열": [{"공정": "fab", "끝해(조)": 50.0}],
            "생존편향주의": "현재 멤버십을 과거에 소급",
        },
        "relationships": {
            "count": 10,
            "byType": {"supplier": 6, "customer": 4},
            "evidenceCoverage": 80.0,
            "amountCoverage": 30.0,
            "ratioCoverage": 20.0,
            "top": [],
        },
        "concentration": {
            "industry": {"hhi": 2200.0, "hhiRisk": "중간"},
            "supply": {"hhi": 1800.0, "hhiRisk": "중간"},
        },
    }


def testIndustryProductUsesExistingPositionAndNativeBlocks() -> None:
    result = _result()

    product = buildIndustryProduct(_Company(), result)

    assert product["status"] == "usable"
    assert product["identity"]["axis"] == "회사위치"
    assert product["time"]["dataAsOf"]["sourceDataAsOf"] == "2026-04-14"
    assert product["conclusion"]["label"] == "반도체 · 전공정"
    assert "최근 유효연도 리더" in product["conclusion"]["summary"]
    assert product["payload"]["coverage"]["observedBlocks"] == 6
    assert any(row["id"] == "myOpmPercentile" for row in product["drivers"])
    assert product["claims"] == [
        {
            "id": "industry.cycle",
            "label": "산업 국면",
            "comparisonKey": "industryCycle",
            "basis": "industryCycle",
            "direction": "supportive",
            "horizon": "currentCycle",
            "asOf": product["time"]["asOf"],
            "dataAsOf": product["time"]["dataAsOf"],
            "period": "2026-04-14",
            "status": "derived",
            "sourceRef": "dartlab://industry/005930/sectorCycle",
            "evidenceRefs": ["industry.sectorCycle"],
            "falsifierRefs": ["sectorCycleBreak"],
            "value": "확장",
        }
    ]
    assert any(row["id"] == "survivorshipBias" for row in product["assumptions"])


def testMissingNativeBlocksMakesPartialNotFabricated() -> None:
    result = _result()
    result["sectorMetrics"] = None
    result["sectorCycle"] = None
    result["profitPool"] = None
    result["relationships"] = None

    product = buildIndustryProduct(_Company(), result)

    assert product["status"] == "partial"
    assert any(gap["id"] == "industry.sectorMetrics" for gap in product["gaps"])
    assert any(gap["id"] == "industry.demandPricingDriver" for gap in product["gaps"])


def testEdgarIndustryReturnsBlockedContract() -> None:
    class _UsCompany:
        stockCode = "AAPL"
        market = "US"

    result = blockedIndustryResult(_UsCompany(), reason="US taxonomy 없음")

    assert result["product"]["status"] == "blocked"
    assert result["product"]["identity"]["market"] == "US"
    assert result["product"]["gaps"][0]["status"] == "blocked"
