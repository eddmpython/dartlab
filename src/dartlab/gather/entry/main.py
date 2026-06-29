"""GatherEntry — 외부 시장 데이터 통합 수집 콜러블 (axis dispatch).

dartlab.gather() callable 의 본체. 공개 11 축 (price·flow·macro·news·sector·
insider·ownership·peers·krx·krxIndex·narrative) + 베타 2 축 (dartDoc·calendar,
hidden) = 13 축. 축 정의 SSOT 는 ``dispatch.AXIS_REGISTRY`` 한 곳 — 본 docstring
은 설명용이며 가용 축의 정본은 ``dartlab.gather()`` 가이드 / ``AXIS_REGISTRY``.

축별 위임은 getDefaultGather() 의 Gather 싱글턴 메서드 또는 정적 헬퍼
(네이버 지수 fetch) 로 간다.
"""

from __future__ import annotations

import contextlib
from typing import Any

import polars as pl

from .dispatch import (
    API_KEY_INFO,
    AXIS_REGISTRY,
    _resolveAxis,
)
from .handlers import (
    handleCalendar,
    handleDartDoc,
    handleFlow,
    handleFlowMany,
    handleInsider,
    handleKrx,
    handleKrxIndex,
    handleMacro,
    handleNarrative,
    handleNews,
    handleOwnership,
    handlePeers,
    handlePrice,
    handleResearch,
    handleSector,
    handleTheme,
)

# axis → handler dispatch 테이블 (G+ P-Q2.2). 새 axis 추가 시:
#   1. dispatch.AXIS_REGISTRY 메타 추가
#   2. handlers.py 에 handle<Axis>(g, target, *, market, ...) 정의
#   3. 본 dict 에 한 줄 추가
_AXIS_DISPATCH: dict[str, Any] = {
    "price": handlePrice,
    "flow": handleFlow,
    "macro": handleMacro,
    "news": handleNews,
    "sector": handleSector,
    "insider": handleInsider,
    "ownership": handleOwnership,
    "peers": handlePeers,
    "krx": handleKrx,
    "krxIndex": handleKrxIndex,
    "narrative": handleNarrative,
    "research": handleResearch,
    "theme": handleTheme,
    "calendar": handleCalendar,
    "dartDoc": handleDartDoc,
}


class GatherEntry:
    """외부 시장 데이터 통합 수집 — 공개 11축, 전부 Polars DataFrame.

    Capabilities (가용 축의 정본 = ``dispatch.AXIS_REGISTRY`` / ``dartlab.gather()`` 가이드):
        - price: OHLCV 시계열 (KR Naver/US Yahoo, 기본 1년, 최대 6000거래일)
        - flow: 외국인/기관 수급 동향 (KR 전용, Naver)
        - macro: ECOS(KR) / FRED(US) / customs(KR 무역) + ECB(EU) · BIS/OECD/IMF(GLOBAL) 거시지표
        - news: Google News RSS 뉴스 수집 (최근 30일)
        - sector: 업종 분류 (KR KIND+Naver)
        - insider: 내부자 거래 (KR DART)
        - ownership: 기관/외국인 지분 보유 (KR Naver)
        - peers: 동종업종 피어 종목 (시총 포함, KR Naver)
        - krx / krxIndex: KRX 회사별·시장군 지수 wide (HF SSOT)
        - narrative: 뉴스 내러티브 archive (RSS+GDELT)
        - 베타(hidden): dartDoc(공시 원문) · calendar(정기공시 due)
        - 자동 fallback 체인, circuit breaker, TTL 캐시

    AIContext:
        - ask()/chat()에서 주가/수급/거시 데이터를 컨텍스트로 주입 가능
        - 기업 분석 시 시장 데이터 보충 자료로 활용

    Guide:
        - "주가 추이 보여줘" -> gather("price", "005930")
        - "미국 주가 보여줘" -> gather("price", "AAPL")  # market 자동 판정
        - "외국인 매매 동향" -> gather("flow", "005930")
        - "여러 종목 수급" -> gather("flow", targets=["005930", "000660"], parallel=2)
        - "금리 추이 알려줘" -> gather("macro", "BASE_RATE") 또는 gather("macro", "FEDFUNDS")
        - "최근 뉴스 찾아줘" -> gather("news", "삼성전자")
        - "업종 알려줘" -> gather("sector", "005930")
        - "내부자 거래 보여줘" -> gather("insider", "005930")
        - "지분 보유 현황" -> gather("ownership", "005930")
        - "동종업종 비교" -> gather("peers", "005930")
        - "미국 거시지표 전체" -> gather("macro", market="US") 또는 gather("US")
        - 주가+수급은 scan과 다름. scan은 재무 기반 횡단, gather는 시장 실시간.

    When:
        외부 시장 데이터가 필요하지만 사용자가 provider/API endpoint 를 직접 고르고
        싶지 않은 경우. 분석·quant·notebook 에 넣을 price/flow/macro/news 등
        보조 raw table 이 필요할 때.

    How:
        axis 정규화 → ``AXIS_REGISTRY`` 계약 확인 → ``GatherHttpClient.useProxy``
        호출 범위 설정 → axis handler 위임. ``targets`` batch 는 flow 에서만
        허용하며, flow batch 는 종목 단위 병렬 후 ``stockCode`` 를 붙인다.

    SeeAlso:
        - scan: 재무 기반 전종목 횡단분석 (거버넌스, 현금흐름 등)
        - Company: 개별 종목 공시/재무 데이터
        - analysis: 14축 전략분석 (재무비율, 수익구조 등)

    Args:
        axis: 축 이름 ("price", "flow", "macro", "news"). None이면 가이드 반환.
        target: 종목코드/지표코드/검색어. 축별로 다름.
        **kwargs: market ("KR"/"US"), start, end, days, proxy 등 축별/공통 옵션.

    Returns:
        pl.DataFrame — 축별 시계열 데이터. axis=None이면 공개 축 가이드 DataFrame.

    Requires:
        price/flow/news: 없음 (공개 API)
        macro: 불필요 — apiKey 명시 시 ECOS/FRED 직접 API 호출

    Raises:
        ValueError — 알 수 없는 axis, 필수 target 누락, flow 외 axis 에
        ``targets`` batch 를 준 경우.

    Example::

        import dartlab
        dartlab.gather()                              # 가이드
        dartlab.gather("price", "005930")             # 삼성전자 1년 OHLCV
        dartlab.gather("flow", "005930")              # 수급
        dartlab.gather("flow", targets=["005930", "000660"], parallel=2)  # 여러 종목 수급
        dartlab.gather("macro")                       # KR 거시 전체
        dartlab.gather("macro", "FEDFUNDS")           # 자동 US 감지
        dartlab.gather("news", "삼성전자")             # 뉴스

    LLM Specifications:
        AntiPatterns:
            - ``dartlab.gather("price", "AAPL", market="US")`` 를 필수처럼 안내.
            - Company 단축 메서드나 내부 Gather 메서드 옵션을 공개 flow 계약으로 노출.
            - flow 외 axis 에 ``targets`` 병렬 batch 가 된다고 안내.
            - proxy 가 rate-limit/공급자 제한을 우회한다고 설명.
        OutputSchema:
            - axis=None : axis/label/description/example/apiKey 가이드 DataFrame
            - price : date/open/high/low/close/volume DataFrame
            - flow : date/foreignNet/institutionNet/individualNet/foreignHoldingRatio DataFrame
            - flow targets : stockCode/date/foreignNet/institutionNet/individualNet/foreignHoldingRatio DataFrame
        Prerequisites:
            - 공개 호출은 ``dartlab.gather(axis, target?, **kwargs)``.
            - proxy 는 사용자 제공 HTTP(S) URL 이 있을 때만 지정.
        Freshness:
            외부 공급자별 갱신 주기를 따른다. price/flow/news 는 호출 시점 네트워크
            결과 또는 TTL cache 상태에 따라 달라진다.
        Dataflow:
            dartlab.gather → GatherEntry → axis handler → Gather singleton/source/domain.
        TargetMarkets:
            - KR
            - US
            - GLOBAL (macro/HF 또는 해당 source 지원 범위)
    """

    def __call__(
        self,
        axis: str | None = None,
        target: str | None = None,
        **kwargs: Any,
    ) -> pl.DataFrame:
        """외부 시장 데이터 수집 — 공개 11 축 (핵심 4: 주가·수급·거시·뉴스 + 보조 7).

        Parameters
        ----------
        axis : str, optional
            수집 축. None 이면 가이드 DataFrame 반환. 가용 축 정본 = AXIS_REGISTRY.
            핵심 — "price" OHLCV 주가, "flow" 투자자별 수급,
            "macro" 거시지표 (ECOS/FRED/customs/ECB/BIS/OECD/IMF), "news" Google News.
            보조 — "sector" 업종, "insider" 내부자거래, "ownership" 지분,
            "peers" 피어, "krx"/"krxIndex" KRX wide, "narrative" 뉴스 내러티브.
            고급 수집기 (dividends/splits/majorShareholders/collect 등) 는 축이 아니라
            ``getDefaultGather()`` 메서드 — 본 docstring 하단 "Form A vs Form B" 참조.
        target : str, optional
            종목코드/지표코드/검색어. 축에 따라 필수.
        **kwargs
            market ("KR"/"US"), start, end, days, proxy 등 축별/공통 옵션.

        Returns
        -------
        pl.DataFrame
            axis=None (가이드):
                axis : str — 축 이름
                label : str — 한글 레이블
                description : str — 설명
                example : str — 사용 예시
            axis="price":
                date : date — 날짜
                open : float — 시가
                high : float — 고가
                low : float — 저가
                close : float — 종가
                volume : int — 거래량
            axis="flow":
                date : date — 날짜
                외국인순매수 : int — 외국인 순매수량
                기관순매수 : int — 기관 순매수량
            axis="macro":
                date : date — 날짜
                지표별 컬럼 : float — ECOS/FRED 거시지표 값
            axis="news":
                title : str — 뉴스 제목
                link : str — 기사 URL
                pubDate : str — 발행일
            axis="sector":
                sectorCode : str — 업종코드
                sectorName : str — 업종명
                industryCode : str — 산업코드
                industryName : str — 산업명
                market : str — 시장 (KR/US)
            axis="insider":
                date : str — 거래일
                name : str — 거래자명
                position : str — 직위
                tradeType : str — 거래유형
                changeShares : int — 변동 주수

        Raises
        ------
        ValueError
            축 이름이 등록되지 않은 경우.
            target 필수 축에서 target 누락 시.

        Examples
        --------
        >>> dartlab.gather()                              # 가이드
        >>> dartlab.gather("price", "005930")              # KR OHLCV
        >>> dartlab.gather("price", "AAPL")                # US 주가 (자동 판정)
        >>> dartlab.gather("flow", targets=["005930", "000660"], parallel=2)
        >>> dartlab.gather("macro", "FEDFUNDS")            # 미국 기준금리
        >>> dartlab.gather("news", "삼성전자")              # Google News

        Notes
        -----
        Naver(KR)/Yahoo(US)/FRED/ECOS/Google News 경유. API 키 불필요.
        결과는 Polars DataFrame — 분석 엔진 입력으로 바로 사용 가능.

        Guide
        -----
        AI 역할: AI는 gather를 외부 데이터 수집 진입점으로 보고 데이터 신선도, 시장, 수집 가능 범위를 먼저 확인한다.
        데이터 기본기: gather 경로는 provider, latestAsOf, metric, period,
            raw table 을 먼저 evidence 로 남긴다. 수집 실패나 빈 결과는
            unavailable 로 공개하고 추정값으로 채우지 않는다.
        When: 분석 엔진에 필요한 외부 데이터를 수집할 때.
        How: gather → analysis/quant 파이프라인. gather("price") 는 quant 의 데이터 원천.
            gather("macro") 는 macro 엔진과 상호 보완 (raw 데이터 vs 분석 결과).
            단일 종목 맥락은 Company 로 target/topic/source 를 고정한 뒤 gather 로 보강하고,
            횡단 비교는 scan 결과와 분리해서 연결한다.
        Verified:
            - gather("news") → 뉴스 목록 + 헤드라인 해석 (observed via ai-ask, 2026-04-25 — 정식 Phase P 판정 아님)

        See Also
        --------
        quant : 주가 기반 정량 분석 — gather("price") 데이터 소비.
        macro : 거시 분석 — gather("macro") raw 데이터의 분석 결과.
        scan : 전종목 비교 — 사전 빌드 데이터와 gather 실시간 데이터 상호 보완.
        """
        if axis is None:
            return self._guide()

        resolved = _resolveAxis(axis)
        entry = AXIS_REGISTRY[resolved]

        if isinstance(target, (list, tuple, set)):
            kwargs["targets"] = list(target)
            target = None

        if entry.targetRequired and target is None and "targets" not in kwargs:
            raise ValueError(f'gather("{resolved}")에는 대상이 필요합니다.\n  예: {entry.example}')

        return self._run(resolved, target, **kwargs)

    def _run(self, axis: str, target: str | None, **kwargs: Any) -> pl.DataFrame:
        """축별 실행 디스패치 — table-driven (G+ P-Q2.2).

        ``_AXIS_DISPATCH`` 테이블 lookup 후 handler 호출. 인자 흐름
        (market/start/end + marketExplicit) 은 모든 handler 가 균일 시그니처로
        받음. 새 axis 추가 시 ``handlers.py`` + ``_AXIS_DISPATCH`` + ``AXIS_REGISTRY``
        세 곳만 갱신.

        Parameters
        ----------
        axis : str
            정규 축 키 (예: ``"price"``, ``"flow"``).
        target : str | None
            종목코드/지표코드/검색어.
        **kwargs
            market, start, end, days, apiKey 등 축별 옵션.

        Returns
        -------
        pl.DataFrame
            축별 시계열 데이터. 스키마는 ``__call__`` 독스트링 참조.

        Raises
        ------
        ValueError
            미등록 axis 또는 handler 가 던지는 axis-specific 오류.
        """
        from dartlab.gather import getDefaultGather

        handler = _AXIS_DISPATCH.get(axis)
        if handler is None:
            raise ValueError(f"미지원 gather 축: {axis}")

        g = getDefaultGather()
        marketExplicit = "market" in kwargs
        market = kwargs.pop("market", "KR")
        start = kwargs.pop("start", None)
        end = kwargs.pop("end", None)
        proxyScope = getattr(getattr(g, "_client", None), "useProxy", None)
        proxyContext = proxyScope(kwargs.get("proxy")) if callable(proxyScope) else contextlib.nullcontext()

        with proxyContext:
            targets = kwargs.pop("targets", None)

            if targets is not None:
                targetList = [str(item).strip() for item in targets if str(item).strip()]
                if not targetList:
                    raise ValueError(f'gather("{axis}") targets 가 비어 있습니다.')
                if axis != "flow":
                    raise ValueError('다중 targets 병렬 수집은 현재 gather("flow", targets=[...]) 에서만 지원합니다.')
                return handleFlowMany(
                    g,
                    targetList,
                    market=market,
                    start=start,
                    end=end,
                    **kwargs,
                )

            return handler(
                g,
                target,
                market=market,
                start=start,
                end=end,
                marketExplicit=marketExplicit,
                **kwargs,
            )

    def _guide(self) -> pl.DataFrame:
        """가이드 DataFrame — 축 목록 + 설명 + 사용 예시 + API 키 안내.

        ``hidden=True`` axis (데이터 준비 중) 는 가이드에서 제외된다.

        Returns
        -------
        pl.DataFrame
            axis : str — 축 이름
            label : str — 한글 레이블
            description : str — 설명 (소스+제한 포함)
            example : str — 사용 예시
            apiKey : str — 필요한 API 키 (없으면 "불필요")
        """
        rows = [
            {
                "axis": key,
                "label": entry.label,
                "description": entry.description,
                "example": entry.example,
                "apiKey": API_KEY_INFO.get(key, "불필요"),
            }
            for key, entry in AXIS_REGISTRY.items()
            if not entry.hidden
        ]
        return pl.DataFrame(rows)

    def __repr__(self) -> str:
        visibleAxes = [(k, e) for k, e in AXIS_REGISTRY.items() if not e.hidden]
        lines = [
            f"Gather — {len(visibleAxes)}축 외부 시장 데이터 수집",
            "",
            "━━━ 축 목록 ━━━",
        ]
        for key, entry in visibleAxes:
            lines.append(f"  {key:12s} {entry.label} — {entry.description[:60]}")
        lines.append("")
        lines.append("━━━ 빠른 시작 ━━━")
        lines.append("  dartlab.gather()                        # 이 가이드")
        lines.append('  dartlab.gather("price", "005930")       # 삼성전자 주가')
        lines.append('  dartlab.gather("price", "AAPL")        # 미국 주가 자동 판정')
        lines.append('  dartlab.gather("macro")                 # KR 거시지표 전체')
        lines.append('  dartlab.gather("news", "삼성전자")       # 뉴스')
        lines.append("")
        lines.append("━━━ 시장 지수 ━━━")
        lines.append('  dartlab.gather("price", "KOSPI")        # 코스피 지수')
        lines.append('  dartlab.gather("price", "KOSDAQ")       # 코스닥 지수')
        lines.append("")
        lines.append("━━━ API 키 (대부분 불필요) ━━━")
        keyed = [(k, API_KEY_INFO[k]) for k, _ in visibleAxes if "불필요" not in API_KEY_INFO.get(k, "불필요")]
        for key, info in keyed:
            lines.append(f"  {key}: {info}")
        lines.append("  → print(dartlab.gather.formatStatus()) 로 공급자별 설정 상태 + 발급 링크 확인")
        lines.append('  → dartlab.gather.setCredential("dart", "<키>") 로 암호화 저장 (.env 편집 불필요)')
        lines.append("")
        lines.append("━━━ 고급 (Form B — 축이 아닌 수집기) ━━━")
        lines.append("  g = dartlab.gather.getDefaultGather()")
        lines.append("  g.dividends / g.splits / g.majorShareholders / g.collect ...")
        lines.append("")
        lines.append(
            "노트북: https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/02_gather.py"
        )
        return "\n".join(lines)
