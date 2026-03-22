"""Analyst 엔진 — 멀티소스 종합 분석.

Usage::

    from dartlab.engines.analysis.analyst import Analyst

    a = Analyst()
    report = a.report(company, current_price=200000)
    print(report)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dartlab.engines.gather import Gather, MarketSnapshot

from .synthesizer import synthesize
from .types import AnalystReport, ValuationMethod

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)


class Analyst:
    """종합 애널리스트 엔진 facade.

    DCF + 시장 데이터 → 가중평균 목표가 + 투자의견.

    Example::

        a = Analyst()
        report = a.report(company, current_price=200000)
        print(report.target_price)
        print(report.opinion)
    """

    def __init__(self, gather: Gather | None = None) -> None:
        self._gather = gather or Gather()
        self._owns_gather = gather is None

    def report(
        self,
        company=None,
        *,
        stock_code: str = "",
        company_name: str = "",
        current_price: float = 0.0,
        dcf_target: float | None = None,
        dcf_confidence: float = 0.5,
        shares: int = 0,
        company_financials: dict | None = None,
        market_snapshot: MarketSnapshot | None = None,
    ) -> AnalystReport:
        """종합 애널리스트 리포트 생성.

        Args:
            company: dartlab Company 객체 (있으면 자동 추출).
            stock_code: 종목코드.
            company_name: 회사명.
            current_price: 현재 주가 (0이면 시장에서 수집).
            dcf_target: DCF 목표가 (없으면 DCF skip).
            dcf_confidence: DCF 신뢰도.
            shares: 발행주식수.
            company_financials: EPS/BPS/EBITDA dict.
            market_snapshot: 미리 수집한 MarketSnapshot.

        Returns:
            AnalystReport.
        """
        # Company 객체에서 자동 추출
        if company is not None:
            stock_code, company_name, shares, company_financials = _extract_from_company(
                company, stock_code, company_name, shares, company_financials
            )

        # 시장 데이터 수집
        if market_snapshot is None and stock_code:
            try:
                snap = self._gather.collect(stock_code)
                market_snapshot = snap.to_market_snapshot()
            except OSError as exc:
                log.warning("시장 데이터 수집 실패: %s", exc)

        # 현재가 — 시장에서 가져오기
        if current_price <= 0 and market_snapshot and market_snapshot.current_price > 0:
            current_price = market_snapshot.current_price

        # 합성
        return synthesize(
            dcf_target=dcf_target,
            dcf_confidence=dcf_confidence,
            market=market_snapshot,
            company_financials=company_financials,
            shares=shares,
            current_price=current_price,
            company_name=company_name,
            stock_code=stock_code,
        )

    def collect_market(self, stock_code: str) -> MarketSnapshot:
        """시장 데이터만 수집."""
        return self._gather.collect(stock_code).to_market_snapshot()

    def close(self) -> None:
        """리소스 정리."""
        if self._owns_gather:
            self._gather.close()

    def __repr__(self) -> str:
        return "Analyst()"


def _extract_from_company(
    company,
    stock_code: str,
    company_name: str,
    shares: int,
    financials: dict | None,
) -> tuple[str, str, int, dict | None]:
    """Company 객체에서 필요한 정보 추출."""
    # 종목코드
    if not stock_code:
        try:
            stock_code = getattr(company, "stockCode", "") or getattr(company, "stock_code", "")
        except AttributeError:
            pass

    # 회사명
    if not company_name:
        try:
            company_name = getattr(company, "name", "") or ""
        except AttributeError:
            pass

    # 발행주식수
    if shares <= 0:
        try:
            profile = getattr(company, "profile", None)
            if profile:
                shares_val = getattr(profile, "sharesOutstanding", 0)
                if shares_val:
                    shares = int(shares_val)
        except (AttributeError, TypeError, ValueError):
            pass

    # 재무 데이터 — EPS, BPS
    if financials is None:
        financials = {}
        try:
            ratios = company.finance.ratios
            if ratios is not None:
                eps = ratios.get("eps") if isinstance(ratios, dict) else getattr(ratios, "eps", None)
                bps = ratios.get("bps") if isinstance(ratios, dict) else getattr(ratios, "bps", None)
                if eps:
                    financials["eps"] = float(eps)
                if bps:
                    financials["bps"] = float(bps)
        except (AttributeError, TypeError, ValueError):
            pass

    return stock_code, company_name, shares, financials or None


__all__ = [
    "Analyst",
    "AnalystReport",
    "ValuationMethod",
]
