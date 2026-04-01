"""5부 비재무 심화 3축 (지배구조/공시변화/비교분석) 단위 테스트."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

# ── Mock 데이터 구조 ──


@dataclass
class MockMajorHolderResult:
    years: list[int]
    totalShareRatio: list[Optional[float]]
    latestHolders: list[dict]
    df: None = None


@dataclass
class MockExecutiveResult:
    df: None = None
    totalCount: int = 10
    registeredCount: int = 5
    outsideCount: int = 4


@dataclass
class MockAuditResult:
    years: list[int] = None
    opinions: list[Optional[str]] = None
    auditors: list[Optional[str]] = None
    df: None = None

    def __post_init__(self):
        if self.years is None:
            self.years = [2021, 2022, 2023, 2024]
        if self.opinions is None:
            self.opinions = ["적정의견", "적정의견", "적정의견", "적정의견"]
        if self.auditors is None:
            self.auditors = ["삼일", "삼일", "삼정", "삼정"]


@dataclass
class MockDiffSummary:
    topic: str
    chapter: str | None
    totalPeriods: int
    changedCount: int
    stableCount: int

    @property
    def changeRate(self) -> float:
        if self.totalPeriods <= 1:
            return 0.0
        return self.changedCount / (self.totalPeriods - 1)


@dataclass
class MockDiffEntry:
    topic: str
    chapter: str | None
    fromPeriod: str
    toPeriod: str
    status: str
    fromLen: int
    toLen: int


@dataclass
class MockDiffResult:
    entries: list = None
    summaries: list = None

    def __post_init__(self):
        if self.entries is None:
            self.entries = []
        if self.summaries is None:
            self.summaries = []

    @property
    def totalChanges(self) -> int:
        return len(self.entries)

    def topChanged(self, n: int = 10) -> list:
        return sorted(self.summaries, key=lambda s: s.changeRate, reverse=True)[:n]


# ── Fixtures ──


def _mockCompanyWithReport():
    """report 데이터가 있는 mock company."""
    company = MagicMock()
    company.stockCode = "005930"

    company.report.majorHolder = MockMajorHolderResult(
        years=[2021, 2022, 2023, 2024],
        totalShareRatio=[20.5, 20.3, 19.8, 19.5],
        latestHolders=[
            {"name": "이재용", "relate": "본인", "ratio": 17.5, "shares": 1000000},
            {"name": "국민연금", "relate": "기관", "ratio": 9.2, "shares": 500000},
        ],
    )

    company.report.executive = MockExecutiveResult(totalCount=10, registeredCount=5, outsideCount=4)

    company.report.audit = MockAuditResult()

    return company


def _mockCompanyWithDocs():
    """docs 데이터가 있는 mock company."""
    company = MagicMock()
    company.stockCode = "005930"
    company.topics = ["businessOverview", "riskFactors", "accountingPolicy"]

    summaries = [
        MockDiffSummary("businessOverview", "사업", 5, 3, 1),
        MockDiffSummary("riskFactors", "위험", 5, 4, 0),
        MockDiffSummary("accountingPolicy", "회계", 5, 1, 3),
        MockDiffSummary("otherTopic", "기타", 5, 0, 4),
    ]
    entries = [
        MockDiffEntry("businessOverview", "사업", "2022", "2023", "CHANGED", 1000, 1200),
        MockDiffEntry("businessOverview", "사업", "2023", "2024", "CHANGED", 1200, 1500),
        MockDiffEntry("riskFactors", "위험", "2021", "2022", "CHANGED", 500, 800),
        MockDiffEntry("riskFactors", "위험", "2022", "2023", "CHANGED", 800, 600),
        MockDiffEntry("riskFactors", "위험", "2023", "2024", "CHANGED", 600, 900),
    ]
    mockDiffResult = MockDiffResult(entries=entries, summaries=summaries)

    return company, mockDiffResult


# ── 지배구조 테스트 ──

pytestmark = pytest.mark.unit


class TestGovernance:
    def test_calcOwnershipTrend(self):
        from dartlab.analysis.financial.governance import calcOwnershipTrend

        company = _mockCompanyWithReport()
        result = calcOwnershipTrend(company)
        assert result is not None
        assert "history" in result
        assert len(result["history"]) == 4
        assert result["history"][-1]["ratio"] == 19.5
        assert result["latestHolders"][0]["name"] == "이재용"

    def test_calcBoardComposition(self):
        from dartlab.analysis.financial.governance import calcBoardComposition

        company = _mockCompanyWithReport()
        result = calcBoardComposition(company)
        assert result is not None
        assert result["totalCount"] == 10
        assert result["outsideCount"] == 4
        assert result["outsideRatio"] == 40.0

    def test_calcAuditOpinionTrend(self):
        from dartlab.analysis.financial.governance import calcAuditOpinionTrend

        company = _mockCompanyWithReport()
        result = calcAuditOpinionTrend(company)
        assert result is not None
        history = result["history"]
        assert len(history) == 4
        assert history[0]["opinion"] == "적정의견"
        # 2023: 삼일->삼정 변경
        assert history[2]["auditorChanged"] is True

    def test_calcGovernanceFlags_lowOwnership(self):
        from dartlab.analysis.financial.governance import calcGovernanceFlags

        company = _mockCompanyWithReport()
        # 19.5% < 20% -> 경영권 방어 취약
        flags = calcGovernanceFlags(company)
        assert any("경영권 방어 취약" in f for f, k in flags)

    def test_calcGovernanceFlags_goodBoard(self):
        from dartlab.analysis.financial.governance import calcGovernanceFlags

        company = _mockCompanyWithReport()
        flags = calcGovernanceFlags(company)
        # 40% 사외이사 -> 아직 50% 미만이므로 기회 플래그 없음
        assert not any("이사회 독립성 양호" in f for f, k in flags)

    def test_none_when_no_report(self):
        from dartlab.analysis.financial.governance import calcOwnershipTrend

        company = MagicMock()
        company.report.majorHolder = None
        result = calcOwnershipTrend(company)
        assert result is None


# ── 공시변화 테스트 ──


class TestDisclosureDelta:
    def test_calcDisclosureChangeSummary(self):
        from dartlab.analysis.financial.disclosureDelta import calcDisclosureChangeSummary

        company, diffResult = _mockCompanyWithDocs()
        with patch(
            "dartlab.analysis.financial.disclosureDelta._safeDiffResult",
            return_value=diffResult,
        ):
            result = calcDisclosureChangeSummary(company)
        assert result is not None
        assert result["totalChanges"] == 5
        assert result["changedTopics"] == 3
        assert result["unchangedTopics"] == 1
        assert len(result["topChanged"]) >= 1

    def test_calcKeyTopicChanges(self):
        from dartlab.analysis.financial.disclosureDelta import calcKeyTopicChanges

        company, diffResult = _mockCompanyWithDocs()
        with patch(
            "dartlab.analysis.financial.disclosureDelta._safeDiffResult",
            return_value=diffResult,
        ):
            result = calcKeyTopicChanges(company)
        assert result is not None
        topics = [kt["topic"] for kt in result["keyTopics"]]
        assert "businessOverview" in topics
        assert "riskFactors" in topics

    def test_calcChangeIntensity(self):
        from dartlab.analysis.financial.disclosureDelta import calcChangeIntensity

        company, diffResult = _mockCompanyWithDocs()
        with patch(
            "dartlab.analysis.financial.disclosureDelta._safeDiffResult",
            return_value=diffResult,
        ):
            result = calcChangeIntensity(company)
        assert result is not None
        assert result["totalDeltaBytes"] > 0
        assert len(result["topByDelta"]) >= 1

    def test_calcDisclosureDeltaFlags_riskFactors(self):
        from dartlab.analysis.financial.disclosureDelta import calcDisclosureDeltaFlags

        company, diffResult = _mockCompanyWithDocs()
        with patch(
            "dartlab.analysis.financial.disclosureDelta._safeDiffResult",
            return_value=diffResult,
        ):
            flags = calcDisclosureDeltaFlags(company)
        # riskFactors changeRate=1.0 -> 빈번한 변경
        assert any("riskFactors" in f for f, k in flags)

    def test_none_when_no_docs(self):
        from dartlab.analysis.financial.disclosureDelta import calcDisclosureChangeSummary

        company = MagicMock()
        with patch(
            "dartlab.analysis.financial.disclosureDelta._safeDiffResult",
            return_value=None,
        ):
            result = calcDisclosureChangeSummary(company)
        assert result is None


# ── 비교분석 테스트 ──


class TestPeerBenchmark:
    def test_calcPeerRanking_structure(self):
        from dartlab.analysis.financial.peerBenchmark import calcPeerRanking

        company = MagicMock()
        company.stockCode = "005930"

        mockResult = {
            "rankings": [
                {
                    "ratioName": "roe",
                    "label": "ROE",
                    "value": 15.0,
                    "percentile": 75.0,
                    "rank": 250,
                    "total": 1000,
                    "period": "2024",
                },
            ]
        }
        with patch(
            "dartlab.analysis.financial.peerBenchmark._calcPercentile",
            side_effect=lambda sc, rn, lb: {
                "ratioName": rn,
                "label": lb,
                "value": 15.0,
                "percentile": 75.0,
                "rank": 250,
                "total": 1000,
                "period": "2024",
            },
        ):
            result = calcPeerRanking(company)
        assert result is not None
        assert len(result["rankings"]) == 8  # 8 benchmark ratios

    def test_calcRiskReturnPosition(self):
        from dartlab.analysis.financial.peerBenchmark import calcRiskReturnPosition

        company = MagicMock()
        company.stockCode = "005930"

        with (
            patch(
                "dartlab.analysis.financial.peerBenchmark.calcPeerRanking",
                return_value=None,
            ),
            patch(
                "dartlab.analysis.financial.peerBenchmark._getLatestValue",
                side_effect=lambda sc, rn: (15.0, 75.0) if rn == "roe" else (80.0, 30.0),
            ),
        ):
            result = calcRiskReturnPosition(company)
        assert result is not None
        assert result["quadrant"] == "고수익-저위험"
        assert result["assessment"] == "우량"

    def test_quadrant_lowReturn_highRisk(self):
        from dartlab.analysis.financial.peerBenchmark import calcRiskReturnPosition

        company = MagicMock()
        company.stockCode = "005930"

        with (
            patch(
                "dartlab.analysis.financial.peerBenchmark.calcPeerRanking",
                return_value=None,
            ),
            patch(
                "dartlab.analysis.financial.peerBenchmark._getLatestValue",
                side_effect=lambda sc, rn: (3.0, 20.0) if rn == "roe" else (300.0, 80.0),
            ),
        ):
            result = calcRiskReturnPosition(company)
        assert result is not None
        assert result["quadrant"] == "저수익-고위험"

    def test_calcPeerBenchmarkFlags(self):
        from dartlab.analysis.financial.peerBenchmark import calcPeerBenchmarkFlags

        company = MagicMock()
        company.stockCode = "005930"

        # ROE top 5%, 부채비율 top 5%
        def mockPercentile(sc, rn, lb):
            if rn == "roe":
                return {
                    "ratioName": rn,
                    "label": "ROE",
                    "value": 25.0,
                    "percentile": 95.0,
                    "rank": 50,
                    "total": 1000,
                    "period": "2024",
                }
            if rn == "debtRatio":
                return {
                    "ratioName": rn,
                    "label": "부채비율",
                    "value": 400.0,
                    "percentile": 95.0,
                    "rank": 50,
                    "total": 1000,
                    "period": "2024",
                }
            return {
                "ratioName": rn,
                "label": lb,
                "value": 10.0,
                "percentile": 50.0,
                "rank": 500,
                "total": 1000,
                "period": "2024",
            }

        with patch(
            "dartlab.analysis.financial.peerBenchmark._calcPercentile",
            side_effect=mockPercentile,
        ):
            with patch(
                "dartlab.analysis.financial.peerBenchmark.calcRiskReturnPosition",
                return_value={"quadrant": "고수익-고위험", "assessment": "레버리지 의존"},
            ):
                flags = calcPeerBenchmarkFlags(company)

        # ROE 상위 5% -> 기회, 부채비율 상위 5% -> 경고
        assert any("ROE 상위" in f and k == "opportunity" for f, k in flags)
        assert any("부채비율 상위" in f and k == "warning" for f, k in flags)


# ── Registry 통합 테스트 ──


class TestAxisRegistry:
    def test_registry_has_21_axes(self):
        from dartlab.analysis.financial import _AXIS_REGISTRY

        assert len(_AXIS_REGISTRY) == 21

    def test_new_axes_in_registry(self):
        from dartlab.analysis.financial import _AXIS_REGISTRY

        assert "지배구조" in _AXIS_REGISTRY
        assert "공시변화" in _AXIS_REGISTRY
        assert "비교분석" in _AXIS_REGISTRY

    def test_aliases(self):
        from dartlab.analysis.financial import _ALIASES

        assert _ALIASES["governance"] == "지배구조"
        assert _ALIASES["disclosureDelta"] == "공시변화"
        assert _ALIASES["peerBenchmark"] == "비교분석"

    def test_resolve_axis(self):
        from dartlab.analysis.financial import _resolveAxis

        assert _resolveAxis("governance") == "지배구조"
        assert _resolveAxis("지배구조") == "지배구조"
        assert _resolveAxis("disclosureDelta") == "공시변화"
        assert _resolveAxis("peerBenchmark") == "비교분석"


class TestCatalog:
    def test_sections_count(self):
        from dartlab.review.catalog import SECTIONS

        assert len(SECTIONS) == 20

    def test_new_sections_exist(self):
        from dartlab.review.catalog import SECTIONS

        keys = [s.key for s in SECTIONS]
        assert "지배구조" in keys
        assert "공시변화" in keys
        assert "비교분석" in keys

    def test_new_blocks_exist(self):
        from dartlab.review.catalog import listBlocks

        blocks = listBlocks()
        blockKeys = {b.key for b in blocks}
        expected = {
            "ownershipTrend",
            "boardComposition",
            "auditOpinionTrend",
            "governanceFlags",
            "disclosureChangeSummary",
            "keyTopicChanges",
            "changeIntensity",
            "disclosureDeltaFlags",
            "peerRanking",
            "riskReturnPosition",
            "peerBenchmarkFlags",
        }
        assert expected.issubset(blockKeys)
