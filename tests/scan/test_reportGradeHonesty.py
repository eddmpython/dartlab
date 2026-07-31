"""KR report scan 축의 자료 부재 판정 계약 회귀.

감사의견·ICR 처럼 등급의 몸통이 되는 입력을 읽지 못했을 때, 형제 축과 같은 정직 gap
라벨을 내고 실질 리스크 판정("관찰"·"주의")을 날조하지 않는 것을 고정한다.
audit 은 등급 규칙을 테스트에 복제하지 않고 실제 ``scanAudit`` 을 합성 source 로 부른다.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.scan.audit import _normalizeOpinion, scanAudit
from dartlab.scan.debt.risk import classifyRisk

pytestmark = pytest.mark.unit


class TestDebtRiskHonesty:
    """ICR 결측에서 등급을 날조하지 않는다."""

    def testMissingIcrWithNoSignalIsDataGap(self) -> None:
        """ICR 도 상향 신호도 없으면 '관찰'이 아니라 '자료부족'이다."""
        assert classifyRisk(icr=None, shortRatio=None) == "자료부족"
        assert classifyRisk(icr=None, shortRatio=10.0, shortDebtTotal=0.0) == "자료부족"

    def testMissingIcrWithObservedShortDebtStillWarns(self) -> None:
        """관측된 단기 리파이낸싱 사실은 ICR 없이도 상향 근거가 된다."""
        assert classifyRisk(icr=None, shortRatio=60.0) == "주의"
        assert classifyRisk(icr=None, shortRatio=None, shortDebtTotal=100.0) == "주의"

    @pytest.mark.parametrize(
        ("icr", "shortRatio", "shortDebtTotal", "expected"),
        [
            (0.5, 60.0, None, "고위험"),
            (0.5, 10.0, 100.0, "고위험"),
            (0.5, 10.0, None, "주의"),
            (5.0, 60.0, None, "주의"),
            (2.0, 10.0, None, "관찰"),
            (5.0, 10.0, None, "안전"),
        ],
    )
    def testKnownIcrGradesUnchanged(
        self,
        icr: float,
        shortRatio: float,
        shortDebtTotal: float | None,
        expected: str,
    ) -> None:
        """ICR 이 있는 정상 경로의 등급 정책은 그대로다 (회귀 가드)."""
        assert classifyRisk(icr=icr, shortRatio=shortRatio, shortDebtTotal=shortDebtTotal) == expected


def _auditSource(opinions: dict[str, str | None]) -> pl.DataFrame:
    """종목별 감사의견 하나짜리 합성 auditOpinion source 를 만든다."""
    codes = list(opinions)
    return pl.DataFrame(
        {
            "stockCode": codes,
            "year": ["2024"] * len(codes),
            "quarter": ["4분기"] * len(codes),
            "adt_opinion": [opinions[c] for c in codes],
            "adtor": ["삼일회계법인"] * len(codes),
            "adt_reprt_spcmnt_matter": [""] * len(codes),
        }
    )


def _runAudit(monkeypatch: pytest.MonkeyPatch, opinions: dict[str, str | None]) -> dict[str, str]:
    """실제 scanAudit 을 합성 source 로 실행해 종목별 위험등급을 돌려준다."""
    monkeypatch.setattr(
        "dartlab.scan.audit.scanParquets",
        lambda *_args, **_kwargs: _auditSource(opinions),
    )
    result = scanAudit(verbose=False)
    return {row["stockCode"]: row["riskLevel"] for row in result.iter_rows(named=True)}


class TestAuditOpinionHonesty:
    """감사의견을 읽지 못하면 종합 리스크를 만들지 않는다."""

    def testMissingOpinionYieldsDataGap(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """의견 부재 종목은 '관찰'이 아니라 '자료부족'이다 (결함 회귀)."""
        assert _runAudit(monkeypatch, {"000001": None})["000001"] == "자료부족"

    def testUnparsedOpinionMarkerYieldsDataGap(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """각주 마커처럼 표준 범주 밖 문자열도 판정으로 바꾸지 않는다."""
        markers = {"000001": "(*2)", "000002": "주1)", "000003": "(주1)"}
        for marker in markers.values():
            assert _normalizeOpinion(marker) == marker
        grades = _runAudit(monkeypatch, markers)
        assert set(grades.values()) == {"자료부족"}

    def testKnownOpinionGradesUnchanged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """표준 감사의견의 등급 정책은 그대로다 (회귀 가드)."""
        grades = _runAudit(
            monkeypatch,
            {
                "000001": "적정의견",
                "000002": "한정의견",
                "000003": "의견거절",
                "000004": "부적정의견",
            },
        )
        assert grades["000001"] == "안전"
        assert grades["000002"] == "주의"
        assert grades["000003"] == "고위험"
        assert grades["000004"] == "고위험"
