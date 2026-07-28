"""Analyst 엔진 — 멀티소스 종합 분석.

Usage::

    from dartlab.analysis.valuation.analyst import Analyst

    a = Analyst()
    report = a.report(company, current_price=200000)
    log.info(report)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from dartlab.core.types import MarketSnapshot

# Gather 는 runtime 에 core.di.getMacroProvider 경유 (정공법 B+C — gather 직접 의존 X)
# type 주석은 문자열로 ("Gather") — TYPE_CHECKING import 도 lint-imports 위반이라 제거
from .synthesizer import synthesize
from .types import AnalystReport, ValuationMethod

if TYPE_CHECKING:
    from dartlab.analysis.forecast.forecast import (
        ForecastResult,
        ScenarioResult,
        SensitivityResult,
    )
    from dartlab.analysis.forecast.revenueForecast import RevenueForecastResult
    from dartlab.analysis.forecast.simulation import (
        MonteCarloResult,
        SimulationResult,
        StressTestResult,
    )
    from dartlab.analysis.valuation.dcf import (
        DCFResult,
        DDMResult,
        RelativeValuationResult,
        ValuationSummary,
    )

log = logging.getLogger(__name__)


class Analyst:
    """종합 애널리스트 엔진 facade.

    DCF + 시장 데이터 → 가중평균 목표가 + 투자의견.

    Example::

        a = Analyst()
        report = a.report(company, current_price=200000)
        log.info(report.target_price)
        log.info(report.opinion)
    """

    def __init__(self, gather: Any = None) -> None:
        if gather is None:
            from dartlab.core.di import getMacroProvider

            self._gather = getMacroProvider().getDefaultGather()
        else:
            self._gather = gather
        # 두 경로 모두 차용이다: None 이면 공유 싱글턴을 빌리는 것이지 자체 생성이 아니다.
        # 싱글턴을 close 하면 프로세스 전체 gather 가 죽는다 (소유권 위반 수리, 2026-07-03).
        self._owns_gather = False

    def report(
        self,
        company=None,
        *,
        stockCode: str = "",
        companyName: str = "",
        currentPrice: float = 0.0,
        dcfTarget: float | None = None,
        dcfConfidence: float = 0.5,
        shares: int = 0,
        companyFinancials: dict | None = None,
        marketSnapshot: MarketSnapshot | None = None,
    ) -> AnalystReport:
        """종합 애널리스트 리포트 생성.

        Capabilities:
            - DCF 목표가 + 시장 컨센서스 + 피어 멀티플 + 상대가치 4 채널 합성
            - Company 객체에서 종목코드/회사명/발행주식수/EPS/BPS 자동 추출
            - 시장 스냅샷 미지정 시 self._gather 경유 자동 수집

        Args:
            company: dartlab Company 객체 (있으면 자동 추출).
            stockCode: 종목코드.
            companyName: 회사명.
            currentPrice: 현재 주가 (0이면 시장에서 수집).
            dcfTarget: DCF 목표가 (없으면 DCF skip).
            dcfConfidence: DCF 신뢰도.
            shares: 발행주식수.
            companyFinancials: EPS/BPS/EBITDA dict.
            marketSnapshot: 미리 수집한 MarketSnapshot.

        Returns:
            AnalystReport — target_price, opinion, methods, confidence 등 종합 리포트.

        Example:
            >>> a = Analyst()
            >>> r = a.report(company, currentPrice=75000)
            >>> r.target_price, r.opinion

        Guide:
            DCF 결과 없으면 컨센서스+멀티플 가중 재배분. 4 채널 중 가용 채널만
            정규화 후 가중평균. DCF↔컨센서스 괴리 50% 초과 시 DCF 가중치 ×0.7.

        When:
            Company 분석 종료 시 종합 의견·목표가 산출 단계.

        How:
            Analyst().report(company=c, currentPrice=p) 또는 marketSnapshot 직접 주입.

        Requires:
            company 또는 (stockCode + marketSnapshot) 중 하나 + synthesize 헬퍼.

        Raises:
            없음 — 데이터 부족 시 AnalystReport(warnings=[...]) 반환.

        See Also:
            - synthesize : 가중평균 합성 본체
            - collectMarket : 시장 스냅샷만 수집

        AIContext:
            target_price + opinion + confidence 셋 함께 노출, methods 의 weight
            분포로 신뢰도 근거 인용. DCF 단독 인용 금지.
        """
        # Company 객체에서 자동 추출
        if company is not None:
            stockCode, companyName, shares, companyFinancials = _extractFromCompany(
                company, stockCode, companyName, shares, companyFinancials
            )

        # 시장 데이터 수집
        if marketSnapshot is None and stockCode:
            try:
                snap = self._gather.collect(stockCode)
                marketSnapshot = snap.toMarketSnapshot()
            except OSError as exc:
                log.warning("시장 데이터 수집 실패: %s", exc)

        # 현재가 — 시장에서 가져오기
        if currentPrice <= 0 and marketSnapshot and marketSnapshot.currentPrice > 0:
            currentPrice = marketSnapshot.currentPrice

        # 합성
        return synthesize(
            dcfTarget=dcfTarget,
            dcfConfidence=dcfConfidence,
            market=marketSnapshot,
            companyFinancials=companyFinancials,
            shares=shares,
            currentPrice=currentPrice,
            companyName=companyName,
            stockCode=stockCode,
        )

    def collectMarket(self, stockCode: str) -> MarketSnapshot:
        """시장 데이터만 수집.

        Capabilities:
            - 종목코드 → gather provider 호출 → MarketSnapshot 변환

        Parameters
        ----------
        stockCode : str
            종목코드.

        Returns
        -------
        MarketSnapshot
            현재가, 시가총액, 거래량 등 시장 스냅샷.

        Example:
            >>> a = Analyst()
            >>> snap = a.collectMarket("005930")
            >>> snap.currentPrice

        Guide:
            Analyst.report 와 별개로 시장 스냅샷만 미리 받아 두고 싶을 때 사용.

        When:
            UI/CLI 가 사전에 시장 데이터를 캐시할 필요가 있는 시점.

        How:
            Analyst().collectMarket("005930") 형식.

        Requires:
            self._gather (di.getMacroProvider().getDefaultGather()) 가용.

        Raises:
            gather provider 가 던지는 OSError/네트워크 오류 — 호출자가 처리.

        See Also:
            - report : 시장 데이터 + DCF 등 통합 리포트

        AIContext:
            "현재가/시총만 확인" 요청 시 사용.
        """
        return self._gather.collect(stockCode).toMarketSnapshot()

    def close(self) -> None:
        """리소스 정리.

        Capabilities:
            - 자체 생성한 gather 인스턴스의 close 호출 (외부 주입 시 skip)

        Returns
        -------
        None

        Example:
            >>> a = Analyst()
            >>> a.close()

        Guide:
            with 컨텍스트 미지원 — 명시적 close 호출 또는 GC 의존.

        When:
            장시간 실행 후 gather 의 HTTP 세션/캐시 해제 필요 시.

        How:
            Analyst 인스턴스의 close() 메서드 호출.

        Requires:
            __init__ 시 gather 주입 없이 자체 생성된 인스턴스에서만 의미.

        Raises:
            없음 — gather.close 에서 예외 발생 가능 (호출자가 처리).

        See Also:
            - __init__ : gather 자체 생성 여부 (_owns_gather)

        AIContext:
            세션 종료 알림 시 인용.
        """
        if self._owns_gather:
            self._gather.close()

    def __repr__(self) -> str:
        return "Analyst()"


def _extractFromCompany(
    company,
    stockCode: str,
    companyName: str,
    shares: int,
    financials: dict | None,
) -> tuple[str, str, int, dict | None]:
    """Company 객체에서 필요한 정보 추출.

    회사명은 ``company.name``, 주식수는 ``company.profile.sharesOutstanding`` 을 읽고 있었다.
    두 이름 다 Company 표면에 없어서 삼성전자를 넣어도 ``('005930', '', 0)`` 이 나왔다.
    애널리스트 보고서가 회사명 없이, 주당 지표 없이 만들어지고 있었다는 뜻이다.
    지금은 ``corpName`` 과 ``capital`` 축의 발행주식총수를 쓴다.
    """
    # 종목코드
    if not stockCode:
        stockCode = getattr(company, "stockCode", "") or ""

    # 회사명
    if not companyName:
        companyName = getattr(company, "corpName", "") or ""

    # 발행주식수
    if shares <= 0:
        try:
            df = company.capital()
            if df is not None and getattr(df, "height", 0):
                sharesVal = df.row(0, named=True).get("발행주식총수")
                if sharesVal:
                    shares = int(sharesVal)
        except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
            log.debug("%s 발행주식수 조회 실패: %s", stockCode or companyName, exc)

    # 재무 데이터 — EPS, BPS
    if financials is None:
        financials = {}
        try:
            ratios = company._finance.ratios
            if ratios is not None:
                eps = ratios.get("eps") if isinstance(ratios, dict) else getattr(ratios, "eps", None)
                bps = ratios.get("bps") if isinstance(ratios, dict) else getattr(ratios, "bps", None)
                if eps:
                    financials["eps"] = float(eps)
                if bps:
                    financials["bps"] = float(bps)
        except (AttributeError, TypeError, ValueError):
            pass

    return stockCode, companyName, shares, financials or None


__all__ = [
    "Analyst",
    "AnalystReport",
    "ValuationMethod",
    # forecast
    "ForecastResult",
    "ScenarioResult",
    "SensitivityResult",
    # valuation
    "DCFResult",
    "DDMResult",
    "RelativeValuationResult",
    "ValuationSummary",
    # simulation
    "SimulationResult",
    "MonteCarloResult",
    "StressTestResult",
    # revenue forecast
    "RevenueForecastResult",
]


# ── lazy re-export (순환 의존 방지) ──

_LAZY_MAP: dict[str, tuple[str, str]] = {
    "ForecastResult": ("dartlab.analysis.forecast.forecast", "ForecastResult"),
    "ScenarioResult": ("dartlab.analysis.forecast.forecast", "ScenarioResult"),
    "SensitivityResult": ("dartlab.analysis.forecast.forecast", "SensitivityResult"),
    "forecastMetric": ("dartlab.analysis.forecast.forecast", "forecastMetric"),
    "forecastAll": ("dartlab.analysis.forecast.forecast", "forecastAll"),
    "scenarioAnalysis": ("dartlab.analysis.forecast.forecast", "scenarioAnalysis"),
    "sensitivityAnalysis": ("dartlab.analysis.forecast.forecast", "sensitivityAnalysis"),
    "RevenueForecastResult": ("dartlab.analysis.forecast.revenueForecast", "RevenueForecastResult"),
    "forecastRevenue": ("dartlab.analysis.forecast.revenueForecast", "forecastRevenue"),
    "SimulationResult": ("dartlab.analysis.forecast.simulation", "SimulationResult"),
    "MonteCarloResult": ("dartlab.analysis.forecast.simulation", "MonteCarloResult"),
    "StressTestResult": ("dartlab.analysis.forecast.simulation", "StressTestResult"),
    "simulateScenario": ("dartlab.analysis.forecast.simulation", "simulateScenario"),
    "simulateAllScenarios": ("dartlab.analysis.forecast.simulation", "simulateAllScenarios"),
    "monteCarloForecast": ("dartlab.analysis.forecast.simulation", "monteCarloForecast"),
    "stressTest": ("dartlab.analysis.forecast.simulation", "stressTest"),
    "DCFResult": ("dartlab.analysis.valuation.dcf", "DCFResult"),
    "DDMResult": ("dartlab.analysis.valuation.dcf", "DDMResult"),
    "RelativeValuationResult": ("dartlab.analysis.valuation.dcf", "RelativeValuationResult"),
    "ValuationSummary": ("dartlab.analysis.valuation.dcf", "ValuationSummary"),
    "dcfValuation": ("dartlab.analysis.valuation.dcf", "dcfValuation"),
    "ddmValuation": ("dartlab.analysis.valuation.dcf", "ddmValuation"),
    "fullValuation": ("dartlab.analysis.valuation.dcf", "fullValuation"),
    "relativeValuation": ("dartlab.analysis.valuation.dcf", "relativeValuation"),
}


def __getattr__(name: str) -> object:
    if name in _LAZY_MAP:
        import importlib

        modPath, attr = _LAZY_MAP[name]
        mod = importlib.import_module(modPath)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
