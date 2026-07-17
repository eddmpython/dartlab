"""기업이야기 편집 금지 규칙 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import publishGate as pg  # noqa: E402
from auditBlog import publish_gate as auditPublishGate  # noqa: E402
from companyReportPolicy import validateCompanyReportDebtRatioBan  # noqa: E402


def writeCompanyPost(
    root: Path,
    body: str,
    *,
    brief: str = "{}",
    cardPlan: str = "",
    svg: str = "",
) -> Path:
    postDir = root / "blog" / "05-company-reports" / "01-policy-test"
    assetsDir = postDir / "assets"
    assetsDir.mkdir(parents=True)
    (postDir / "index.md").write_text(
        f"---\ncategory: company-reports\n---\n\n{body}\n",
        encoding="utf-8",
    )
    (postDir / "brief.json").write_text(brief, encoding="utf-8")
    if cardPlan:
        (postDir / "cards.plan.json").write_text(cardPlan, encoding="utf-8")
    if svg:
        (assetsDir / "risk.svg").write_text(svg, encoding="utf-8")
    return postDir


@pytest.mark.parametrize(
    "body",
    [
        "이 회사의 부채 비율은 205%다.",
        "The debt-to-equity ratio reached 2.05.",
        "The liabilities-to-shareholders-equity multiple reached 2.05.",
        "The debt/equity figure reached 2.05.",
        "D/E ratio 2.05 is the central insight.",
        "자본 대비 총부채가 2.05배다.",
        "부채총계를 자본총계로 나누면 205%가 된다.",
    ],
)
def testCompanyReportDebtRatioBanBlocksTermsAndProxy(body: str, tmp_path: Path) -> None:
    postDir = writeCompanyPost(tmp_path, body)

    errors = validateCompanyReportDebtRatioBan(postDir)

    assert errors
    assert any("index.md" in error for error in errors)


def testCompanyReportDebtRatioBanScansPlansAndSvg(tmp_path: Path) -> None:
    postDir = writeCompanyPost(
        tmp_path,
        "절대 차입금과 이자비용을 본다.",
        brief='{"insight": "debt to equity ratio is the hook"}',
        cardPlan='{"headline": "부채비율 205%"}',
        svg="<svg><text>부채 / 자본</text></svg>",
    )

    errors = validateCompanyReportDebtRatioBan(postDir)

    assert any("brief.json" in error for error in errors)
    assert any("cards.plan.json" in error for error in errors)
    assert any("assets/risk.svg" in error for error in errors)


def testCompanyReportDebtRatioBanAllowsUsefulDebtEvidence(tmp_path: Path) -> None:
    postDir = writeCompanyPost(
        tmp_path,
        "총차입금 2조원, 순차입금 1조원, 이자비용 500억원과 2027년 만기를 함께 본다.",
        brief='{"watchMetric": "영업현금흐름과 이자보상배율"}',
        svg="<svg><text>2027년 만기 1조원</text></svg>",
    )

    assert validateCompanyReportDebtRatioBan(postDir) == []


def testDebtRatioBanDoesNotApplyToOtherCategories(tmp_path: Path) -> None:
    postDir = writeCompanyPost(tmp_path, "부채비율 계산법을 설명한다.")
    indexPath = postDir / "index.md"
    indexPath.write_text(
        indexPath.read_text(encoding="utf-8").replace("company-reports", "reading-disclosures"),
        encoding="utf-8",
    )

    assert validateCompanyReportDebtRatioBan(postDir) == []


def testAuditGateIncludesCompanyReportDebtRatioBan(tmp_path: Path) -> None:
    postDir = writeCompanyPost(tmp_path, "부채비율 205%를 핵심 근거로 삼는다.")

    errors = auditPublishGate(postDir)

    assert any("기업이야기 금지 지표 발견(index.md)" in error for error in errors)


def testMediaOnlyGateCannotBypassCompanyReportDebtRatioBan(monkeypatch, tmp_path: Path) -> None:
    postDir = writeCompanyPost(tmp_path, "D/E ratio 2.05를 핵심 근거로 삼는다.")
    monkeypatch.setattr(pg, "mediaReferenceErrors", lambda _: [])
    monkeypatch.setattr(pg, "trackedBinaryErrors", lambda _: [])
    monkeypatch.setattr(pg, "verifyRemoteAssets", lambda _: [])

    errors = pg.validatePost(postDir, requireContractV2=False, mediaOnly=True)

    assert any("기업이야기 금지 지표 발견(index.md)" in error for error in errors)
