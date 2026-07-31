"""reference docs bridge 의 대조 불가 표면화 계약 회귀.

재무제표를 못 읽은 것과 본문 금액이 재무제표와 안 맞는 것은 다른 답이다. 빈 dict 로
뭉개면 소비자(server analysis API)가 matchRate 0.0 이라는 경보성 사실 주장을 낸다.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.reference.docs.bridge import getFinanceAmounts

pytestmark = pytest.mark.unit


class _Company:
    """panel 호출을 흉내내는 최소 대역."""

    def __init__(self, frames: dict[str, object] | None = None, error: Exception | None = None):
        self._frames = frames or {}
        self._error = error

    def panel(self, name: str):
        """요청한 재무제표를 돌려주거나 주입된 실패를 낸다."""
        if self._error is not None:
            raise self._error
        frame = self._frames.get(name)
        if frame is None:
            raise FileNotFoundError(f"{name} 없음")
        return frame


def _statement(period: str) -> pl.DataFrame:
    """항목·기간 열을 가진 최소 재무제표."""
    return pl.DataFrame({"항목": ["매출액"], period: [1_000_000_000.0]})


def testAllStatementsUnreadableRaises() -> None:
    """세 장을 모두 못 읽으면 빈 dict 가 아니라 RuntimeError 다 (결함 회귀).

    panel artifact 부재(FileNotFoundError)는 이 함수가 흡수하던 대표 경로다.
    """
    with pytest.raises(RuntimeError, match="읽지 못해"):
        getFinanceAmounts(_Company(error=FileNotFoundError("panel 없음")), "2024")


def testUnhandledIoErrorPropagates() -> None:
    """흡수 목록 밖 I/O 실패는 그대로 전파된다 (소비자가 실패로 본다)."""
    with pytest.raises(OSError, match="disk"):
        getFinanceAmounts(_Company(error=OSError("disk")), "2024")


def testMissingPeriodRaises() -> None:
    """재무는 읽었지만 대조할 기간이 없으면 0% 매칭이 아니라 실패다."""
    company = _Company({"IS": _statement("2019Q4"), "BS": _statement("2019Q4"), "CF": _statement("2019Q4")})

    with pytest.raises(RuntimeError, match="기간"):
        getFinanceAmounts(company, "2024")


def testReadableStatementsReturnAmounts() -> None:
    """정상 경로는 그대로 계정 금액을 돌려준다 (회귀 가드)."""
    company = _Company({"IS": _statement("2024Q4"), "BS": _statement("2024Q4"), "CF": _statement("2024Q4")})

    amounts = getFinanceAmounts(company, "2024")

    assert amounts["매출액"] == pytest.approx(10.0)  # 10억


def testAnnualPeriodFallsBackToQ4() -> None:
    """연간 표기는 Q4 열로 해소된다 (기존 계약 유지)."""
    company = _Company({"IS": _statement("2024Q4")})

    assert getFinanceAmounts(company, "2024")["매출액"] == pytest.approx(10.0)
