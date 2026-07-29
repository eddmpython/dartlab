"""Gather macro mixin — 거시경제 지표 (KR ECOS + US FRED) 4 메서드."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import polars as pl

from ..infra.telemetry import emitGatherFetch
from .context import GatherMixinContext


class _SdmxFacade(Protocol):
    def series(
        self,
        indicatorId: str,
        *,
        startPeriod: str | None = None,
        endPeriod: str | None = None,
    ) -> "pl.DataFrame":
        """정규화된 지표 ID의 SDMX 시계열을 반환한다."""
        ...

    def close(self) -> None:
        """provider가 보유한 HTTP 자원을 닫는다."""
        ...


class _GatherMacroMixin(GatherMixinContext):
    """거시지표 메서드 모음 — KR/US + Sprint 2 EU/GLOBAL (ECB/BIS/OECD/IMF SDMX)."""

    _KNOWN_MARKETS = {"KR", "US", "EU", "GLOBAL"}

    # eddmpython PRIORITY_INDICATORS (12개)
    _MACRO_KR = [
        "CPI",
        "BASE_RATE",
        "USDKRW",
        "M2",
        "CLI",
        "CCI",
        "CSI",
        "IPI",
        "MANUFACTURING",
        "TRADE",
        "HOUSE_PRICE",
        "APT_PRICE",
    ]

    # Sprint 2 PR2 — ECB Data Portal 8 핵심 지표 (SDMX live, HF 미동기)
    _MACRO_EU = [
        "ECB_M3",
        "ECB_HICP",
        "ECB_DEPO_RATE",
        "ECB_MRO_RATE",
        "ECB_UNEMP",
        "ECB_EURUSD",
        "ECB_BUND_10Y",
        "ECB_GDP_EA",
    ]

    # Sprint 2 PR3~5 — BIS + OECD + IMF 핵심 지표 (SDMX live)
    _MACRO_GLOBAL = [
        # BIS — 글로벌 정책금리 4 국 + 환율
        "BIS_POLICY_RATE_US",
        "BIS_POLICY_RATE_EU",
        "BIS_POLICY_RATE_JP",
        "BIS_POLICY_RATE_KR",
        "BIS_EER_BROAD_USD",
        # OECD — 선행지표 + 신뢰지수
        "OECD_LEI",
        "OECD_BCI",
        "OECD_CCI",
        # IMF — 환율 + 원유
        "IMF_FX_USD_KRW",
        "IMF_FX_USD_JPY",
        "IMF_OIL_BRENT",
    ]

    # eddmpython fred/config.py INDICATORS (24개)
    _MACRO_US = [
        "GDP",
        "CPIAUCSL",
        "CPILFESL",
        "PCEPI",
        "PCEPILFE",
        "UNRATE",
        "FEDFUNDS",
        "DGS10",
        "M2SL",
        "TB3MS",
        "SP500",
        "VIXCLS",
        "AAA",
        "HOUST",
        "CSUSHPISA",
        "INDPRO",
        "PAYEMS",
        "RSAFS",
        "CES0500000003",
        "ICSA",
        "USSLIND",
        "UMCSENT",
        "DRTSCILM",
        "DTWEXBGS",
        "DCOILWTICO",
    ]

    def macro(
        self,
        market: str = "KR",
        indicator: str | None = None,
        *,
        start: str | None = None,
        end: str | None = None,
        apiKey: str | None = None,
        scope: str = "default",
    ) -> "pl.DataFrame":
        """거시경제 지표 시계열 조회.

        Capabilities:
            - 기본: HuggingFace 벌크 데이터셋 — API 키 불필요
            - KR: ECOS (한국은행) — CPI, 기준금리, 환율 등 12개 핵심 지표
            - US: FRED — GDP, CPI, 실업률, 연방기금금리 등 24개 핵심 지표
            - 스마트 라우팅: 지표 코드만으로 KR/US 자동 감지
            - 전체 지표: wide DataFrame (date + 각 지표 컬럼)
            - 단일 지표: (date, value) DataFrame
            - 직접 API: apiKey 명시 시만 ECOS/FRED API 호출

        AIContext:
            - macro 엔진의 raw 데이터 원천. analysis/quant 가 regime/anomaly 분석에 사용

        Guide:
            indicator 인자가 KR/US 둘 중 어디 코드인지 자동 감지 (스마트 라우팅).
            "CPI" 는 KR, "FEDFUNDS" 는 US 로 자동 분기.

        When:
            거시경제 지표 시계열 필요 시. 단일 지표 또는 시장 전체.

        How:
            indicator → _detectMarket → HF 벌크 또는 직접 API → wide/single DF.

        Args:
            market: "KR" 또는 "US". 지표 코드 직접 전달도 가능 (자동 감지).
            indicator: 지표 코드 ("CPI", "FEDFUNDS" 등). None이면 전체 지표.
            start: 시작일 (YYYY-MM-DD). None이면 기본 기간.
            end: 종료일. None이면 오늘.
            apiKey: ECOS/FRED 직접 API 키. None이면 HF 벌크 데이터셋 사용.
            scope: "default" (기존 핵심 지표) 또는 "catalog" (전체 카탈로그).

        Returns:
            pl.DataFrame — wide DataFrame (전체) 또는 (date, value) (단일).

        Requires:
            기본 HF 경로: 불필요.
            직접 API 경로: KR ECOS_API_KEY, US FRED_API_KEY 값을 apiKey 로 명시 전달.

        Raises:
            ValueError: scope 가 ``"default"``/``"catalog"`` 외일 때.

        Example::

            g = getDefaultGather()
            g.macro()                 # KR 전체 지표 wide DF
            g.macro("US")             # US 전체 지표 wide DF
            g.macro("CPI")            # CPI (자동 KR 감지)
            g.macro("FEDFUNDS")       # 연방기금금리 (자동 US 감지)
            g.macro("KR", "CPI")      # 명시적 KR + CPI
            g.macro("US", "SP500")    # 명시적 US + S&P500

        See Also:
            ``dartlab.macro`` 엔진 — 본 raw 데이터의 분석 결과.
            ``dartlab.gather.bulkData.macroHf`` — HF 벌크 경로.
        """
        t0 = time.monotonic()
        try:
            if scope not in {"default", "catalog"}:
                raise ValueError("scope 는 'default' 또는 'catalog' 여야 합니다.")
            # 스마트 라우팅: market 위치에 지표 코드가 온 경우
            if market not in self._KNOWN_MARKETS:
                indicator = market
                market = self._detectMarket(indicator)
            if market == "KR":
                return self._macroKR(indicator, start=start, end=end, apiKey=apiKey, scope=scope)
            if market == "EU":
                return self._macroEU(indicator, start=start, end=end)
            if market == "GLOBAL":
                return self._macroGlobal(indicator, start=start, end=end)
            return self._macroUS(indicator, start=start, end=end, apiKey=apiKey, scope=scope)
        finally:
            emitGatherFetch("macro", (time.monotonic() - t0) * 1000, cacheHit=False, market=market)

    def _detectMarket(self, indicator: str) -> str:
        """지표 코드로 market 자동 감지.

        Sprint 2 prefix 룰 (ECB_/BIS_/OECD_/IMF_) 가 KR/US 보다 우선. 그 외:
        ECOS 카탈로그에 있으면 KR, 없으면 US.

        Parameters
        ----------
        indicator : str
            거시지표 코드 ("CPI", "FEDFUNDS", "ECB_M3", "BIS_POLICY_RATE_US" 등).

        Returns
        -------
        str
            "EU" — ``ECB_`` prefix.
            "GLOBAL" — ``BIS_`` / ``OECD_`` / ``IMF_`` prefix.
            "KR" — ECOS 카탈로그 등록.
            "US" — 그 외 (FRED 가정).
        """
        if indicator.startswith("ECB_"):
            return "EU"
        if indicator.startswith(("BIS_", "OECD_", "IMF_")):
            return "GLOBAL"
        from dartlab.gather.ecos.catalog import getEntry

        if getEntry(indicator):
            return "KR"
        return "US"

    def _macroEU(
        self,
        indicator: str | None,
        *,
        start: str | None,
        end: str | None,
    ) -> "pl.DataFrame":
        """EU 거시지표 — ECB SDMX live fetch.

        Sig: ``_macroEU(indicator, *, start, end) -> pl.DataFrame | None``

        Capabilities: ECB facade 위임 — 단일 indicator 또는 _MACRO_EU 전체.
        AIContext: macro(market="EU") 의 backend.
        Guide: HF 동기화 없음 — 항상 live SDMX. apiKey 불필요 (ECB 무인증).
        When: market="EU" 분기 진입 시.
        How: indicator None 이면 _MACRO_EU compare 흉내 (각 series 호출), 있으면 단일 series.

        Args:
            indicator: ``ECB_`` prefix ID 또는 None.
            start: ``startPeriod`` (예: ``"2020-01"``). None 가능.
            end: ``endPeriod``. None 가능.

        Returns:
            pl.DataFrame — SDMX 응답.

        Raises:
            ImportError: ECB 모듈을 불러올 수 없을 때.
            SdmxClientError: ECB 호출 또는 응답 해석에 실패할 때.

        Example:
            >>> g.macro("EU", "ECB_M3")

        See Also:
            ``dartlab.gather.ecb.Ecb`` — 위임 대상.
        """
        t0 = time.monotonic()
        try:
            from dartlab.gather.ecb import Ecb

            e = Ecb()
            try:
                if indicator:
                    return e.series(indicator, startPeriod=start, endPeriod=end)
                import polars as pl

                out: pl.DataFrame | None = None
                for ind in self._MACRO_EU:
                    df = e.series(ind, startPeriod=start, endPeriod=end)
                    df = df.select(["date", pl.col("value").alias(ind)])
                    out = df if out is None else out.join(df, on="date", how="full", coalesce=True)
                assert out is not None
                return out.sort("date")
            finally:
                e.close()
        finally:
            emitGatherFetch("macroEU", (time.monotonic() - t0) * 1000, cacheHit=False, market="EU")

    def _macroGlobal(
        self,
        indicator: str | None,
        *,
        start: str | None,
        end: str | None,
    ) -> "pl.DataFrame":
        """GLOBAL 거시지표 — BIS/OECD/IMF SDMX live fetch.

        Sig: ``_macroGlobal(indicator, *, start, end) -> pl.DataFrame | None``

        Capabilities: prefix (``BIS_``/``OECD_``/``IMF_``) → 해당 facade 위임.
        AIContext: macro(market="GLOBAL") 의 backend — 3 SDMX provider 공통 진입.
        Guide: indicator 가 None 이면 _MACRO_GLOBAL compare. 단일 indicator 는 prefix 라우팅.
        When: market="GLOBAL" 분기 진입.
        How: indicator prefix → provider 선택 → facade.series 위임.

        Args:
            indicator: ``BIS_``/``OECD_``/``IMF_`` prefix ID 또는 None.
            start: ``startPeriod``.
            end: ``endPeriod``.

        Returns:
            pl.DataFrame — wide (전체) 또는 단일 series.

        Raises:
            ImportError: SDMX provider 모듈을 불러올 수 없을 때.
            ValueError: 단일 지표 prefix가 지원 범위 밖일 때.
            SdmxClientError: provider 호출 또는 응답 해석에 실패할 때.

        Example:
            >>> g.macro("GLOBAL", "BIS_POLICY_RATE_US")

        See Also:
            ``dartlab.gather.bis.Bis`` · ``dartlab.gather.oecd.Oecd`` · ``dartlab.gather.imf.Imf``.
        """
        t0 = time.monotonic()
        try:
            from dartlab.gather.bis import Bis
            from dartlab.gather.imf import Imf
            from dartlab.gather.oecd import Oecd

            def _factoryFor(ind: str) -> _SdmxFacade:
                if ind.startswith("BIS_"):
                    return Bis()
                if ind.startswith("OECD_"):
                    return Oecd()
                if ind.startswith("IMF_"):
                    return Imf()
                raise ValueError(f"지원하지 않는 GLOBAL macro 지표 prefix: {ind}")

            if indicator:
                facade = _factoryFor(indicator)
                try:
                    return facade.series(indicator, startPeriod=start, endPeriod=end)
                finally:
                    facade.close()

            import polars as pl

            facades: dict[str, _SdmxFacade] = {}
            try:
                out: pl.DataFrame | None = None
                for ind in self._MACRO_GLOBAL:
                    prov = ind.split("_", 1)[0]
                    facade = facades.get(prov)
                    if facade is None:
                        facade = _factoryFor(ind)
                        facades[prov] = facade
                    df = facade.series(ind, startPeriod=start, endPeriod=end)
                    df = df.select(["date", pl.col("value").alias(ind)])
                    out = df if out is None else out.join(df, on="date", how="full", coalesce=True)
                assert out is not None
                return out.sort("date")
            finally:
                for facade in facades.values():
                    facade.close()
        finally:
            emitGatherFetch("macroGlobal", (time.monotonic() - t0) * 1000, cacheHit=False, market="GLOBAL")

    def _macroKR(
        self,
        indicator: str | None,
        *,
        start: str | None,
        end: str | None,
        apiKey: str | None = None,
        scope: str = "default",
    ) -> "pl.DataFrame":
        """KR 거시지표 — ECOS (한국은행) API 조회.

        Parameters
        ----------
        indicator : str | None
            지표 코드 ("CPI", "BASE_RATE" 등). None이면 12개 핵심 지표 전체.
        start : str | None
            시작일 (YYYY-MM-DD). None이면 기본 기간.
        end : str | None
            종료일 (YYYY-MM-DD). None이면 오늘.

        Returns
        -------
        pl.DataFrame
            단일 지표: date (Date), value (Float64) 컬럼.
            전체 지표: date + 각 지표명 컬럼 (wide DataFrame).

        Raises
        ------
        ImportError
            ECOS 또는 HF 모듈을 불러올 수 없는 경우.
        ValueError
            HF 카탈로그 밖 지표를 apiKey 없이 요청한 경우.
        EcosError
            ECOS 직접 API 호출 또는 응답 해석에 실패한 경우.
        """
        t0 = time.monotonic()
        try:
            if apiKey is None:
                from dartlab.gather.bulkData import macroHf
                from dartlab.gather.ecos import catalog as ecos_catalog

                indicator = ecos_catalog.resolveId(indicator)
                ids = ecos_catalog.getAllIds() if scope == "catalog" else self._MACRO_KR
                if indicator:
                    return macroHf.fetchSeries("ecos", indicator, start=start, end=end)
                return macroHf.fetchMulti("ecos", ids, start=start, end=end)

            from dartlab.gather.ecos import Ecos

            ecos = Ecos(apiKey=apiKey)
            try:
                if indicator:
                    from dartlab.gather.ecos import catalog as ecos_catalog

                    normalizedIndicator = ecos_catalog.resolveId(indicator)
                    if normalizedIndicator is None:
                        raise ValueError("ECOS macro indicator가 비어 있습니다.")
                    return ecos.series(normalizedIndicator, start=start, end=end)
                return ecos.compare(self._MACRO_KR, start=start, end=end)
            finally:
                ecos.close()
        finally:
            emitGatherFetch("macroKR", (time.monotonic() - t0) * 1000, cacheHit=False, market="KR")

    def _macroUS(
        self,
        indicator: str | None,
        *,
        start: str | None,
        end: str | None,
        apiKey: str | None = None,
        scope: str = "default",
    ) -> "pl.DataFrame":
        """US 거시지표 — FRED API 조회.

        Parameters
        ----------
        indicator : str | None
            지표 코드 ("FEDFUNDS", "GDP" 등). None이면 24개 핵심 지표 전체.
        start : str | None
            시작일 (YYYY-MM-DD). None이면 기본 기간.
        end : str | None
            종료일 (YYYY-MM-DD). None이면 오늘.

        Returns
        -------
        pl.DataFrame
            단일 지표: date (Date), value (Float64) 컬럼.
            전체 지표: date + 각 지표명 컬럼 (wide DataFrame).

        Raises
        ------
        ImportError
            FRED 또는 HF 모듈을 불러올 수 없는 경우.
        ValueError
            HF 카탈로그 밖 지표를 apiKey 없이 요청한 경우.
        FredError
            FRED 직접 API 호출 또는 응답 해석에 실패한 경우.
        """
        t0 = time.monotonic()
        try:
            if apiKey is None:
                from dartlab.gather.bulkData import macroHf
                from dartlab.gather.fred import catalog as fred_catalog

                ids = fred_catalog.getAllIds() if scope == "catalog" else self._MACRO_US
                if indicator:
                    return macroHf.fetchSeries("fred", indicator, start=start, end=end)
                return macroHf.fetchMulti("fred", ids, start=start, end=end)

            from dartlab.gather.fred import Fred

            fred = Fred(apiKey=apiKey)
            try:
                if indicator:
                    return fred.series(indicator, start=start, end=end)
                return fred.compare(self._MACRO_US, start=start, end=end)
            finally:
                fred.close()
        finally:
            emitGatherFetch("macroUS", (time.monotonic() - t0) * 1000, cacheHit=False, market="US")
