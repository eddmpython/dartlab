"""종목 레벨 정량분석 엔진 — 31축 7그룹.

기술적 지표부터 팩터 모델, 텍스트 감성, 포트폴리오 최적화까지.
dartlab.quant("축명", "종목코드") 로 접근.

Usage::

    import dartlab

    dartlab.quant()                                # 가이드 (축 카탈로그)
    dartlab.quant("모멘텀", "005930")              # 모멘텀 분석
    dartlab.quant("momentum", "005930")            # 영문 키
    dartlab.quant("팩터", "AAPL")                  # EDGAR 종목
    dartlab.quant("순위")                          # 횡단면 (종목 불필요)
    dartlab.quant("평균분산", ["005930","000660"])  # 포트폴리오
    dartlab.quant.momentum("005930")               # 속성 접근자
"""

from __future__ import annotations

import importlib
import re
import warnings
from dataclasses import dataclass
from typing import Any

import polars as pl

from dartlab.core.market import isKrStockCode
from dartlab.quant.signal.analyzer import enrichWithIndicators, technicalVerdict

__all__ = ["Quant", "enrichWithIndicators", "technicalVerdict"]


# ── 31축 레지스트리 + alias + 그룹 (분리: _registry.py SSOT, re-export 으로 BC 보존) ──
from dartlab.quant._registry import (
    _ALIASES,
    _AXIS_REGISTRY,
    _GROUPS,
    _OLD_METRICS,
    _AxisEntry,
)

# ── 축 해석 ──────────────────────────────────────────────


def _resolve(axis: str) -> str:
    """축 정식 이름 또는 명시 alias → 정규 축 이름.

    consistency_no_alias 원칙: case-insensitive 매칭 (``axis.lower()``) 은 silent
    alias 라 인정하지 않는다. 사용자는 정식 표기 (camelCase: ``"toneChange"``,
    ``"eventSignal"``) 또는 ``_ALIASES`` 등록 한글/영문 alias 만 사용한다.
    """
    stripped = axis.strip()
    if stripped in _AXIS_REGISTRY:
        return stripped
    if stripped in _ALIASES:
        return _ALIASES[stripped]
    # fuzzy hint
    axis_names = sorted(set(list(_AXIS_REGISTRY.keys()) + list(_ALIASES.keys())))
    hint = ", ".join(axis_names[:20])
    msg = f"'{axis}' 축을 찾을 수 없습니다. 사용 가능: {hint}..."
    raise KeyError(msg)


def _isStockCode(value: str) -> bool:
    """값이 종목코드처럼 보이는지 판별.

    consistency_no_alias 원칙: case-insensitive lookup 안 함. ``s in _AXIS_REGISTRY``
    strict 매칭으로 axis 와 ticker 충돌 검사 (예: ``"price"`` 는 axis, ``"PRICE"`` 는
    ticker 후보 — registry strict 매칭이 ``False`` 라 ticker 로 판정).
    """
    if not isinstance(value, str):
        return False
    s = value.strip()
    # KRX 단축코드 (6자리 숫자 또는 숫자 선두 영숫자, 예 0008Z0)
    if isKrStockCode(s):
        return True
    # 알파벳 1-5자 (미국 ticker, US ticker 표준은 uppercase)
    if re.match(r"^[A-Z]{1,5}$", s) and s not in _AXIS_REGISTRY and s not in _ALIASES:
        return True
    return False


# ── Quant 클래스 ─────────────────────────────────────────


class Quant:
    """종목 레벨 정량 분석 엔진 — 31 축 7 그룹 가격 기반 분석.

    Capabilities:
        가격·거래량 시계열 기반 정량 분석. 8 그룹 30+ 축 — 기술적 (technicalVerdict,
        signal/momentum/analyzer), 리스크 (volatility/tailrisk), 팩터 (value/quality/
        size), 백테스트 (strategy/screen), 알파 (factor/calc, factor/ranking),
        regime (quadrant), 포트폴리오 (mapping/optimize), 시나리오 (strategyRules).

    Args:
        없음 (callable). 실제 인자는 ``__call__`` 시그니처:
        ``axis``/``stockCode``/``**kwargs``.

    Returns:
        ``Quant`` 인스턴스. 호출 가능 객체.

    Example:
        >>> from dartlab import quant
        >>> quant()                              # 31 축 가이드
        >>> quant("기술", "005930")              # 삼성전자 기술적 분석
        >>> quant("변동성", "AAPL")              # Apple 변동성
        >>> quant("백테스트", "005930")          # 백테스트
        >>> quant("팩터")                         # 시장 전체 팩터 스코어

    Guide:
        Macro (시장) → Quant (종목) → Analysis (재무) 의 중간 레벨. 기술적
        진단 + 리스크 패널 + 팩터 노출 + 백테스트 입력 산출. 한국어 축 키
        (기술/변동성/팩터/백테스트/regime 등) 로 접근.

    SeeAlso:
        - ``Macro``: 시장 사이클 — Quant 사용 전 컨텍스트 확립
        - ``analysis``: 재무 분석 — Quant 의 기술/심리 신호와 교차
        - ``enrichWithIndicators``: 가격 DataFrame → 지표 추가
        - ``technicalVerdict``: 다중 지표 합산 판정

    Requires:
        Company 객체 또는 직접 가격 시계열. 가격 캐시 (`scan/builders`) 또는
        market data API.

    AIContext:
        "이 종목 기술적으로 어떄?" · "변동성 위험 평가" · "팩터 노출 분해"
        · "백테스트 돌려봐" 등 종목 정량 질문에 매칭. company 분석에 가격
        신호를 더할 때, Macro 컨텍스트 위에서 종목별 quant 판정.

    LLM Specifications:
        AntiPatterns:
            - 종목코드 미지정 + axis 만 — 일부 축은 stockCode 필수 (예: 기술/
              변동성/백테스트)
            - axis 영문 (technical/volatility) — 한국어 키만 매핑
            - 시장 자동 추론 — KR/US 명시 권장
        OutputSchema:
            - axis=None: ``pl.DataFrame`` 가이드 (axis/label/description/group)
            - axis="기술": ``{indicators, verdict, signals}``
            - axis="변동성": ``{historical, conditional, tail}``
            - axis="팩터": ``{value, momentum, quality, composite}``
            - axis="백테스트": ``{returns, sharpe, maxDrawdown, equity}``
        Prerequisites:
            가격 시계열 (Company.price 또는 외부 fetch). 백테스트는 일자별
            close + volume 시리즈 ≥ 252 일.
        Freshness:
            일별 (가격 cache 갱신 주기에 종속).
        Dataflow:
            axis → _resolve → _AXIS_REGISTRY → import_module → 축 함수
            (stockCode + kwargs) → dict.
        TargetMarkets:
            - KR (네이버 history / KIS)
            - US (yfinance / EDGAR price)
    """

    def __call__(
        self,
        axis: str | list | None = None,
        stockCode: str | list | None = None,
        **kwargs: Any,
    ) -> pl.DataFrame | dict | Any:
        """가격 기반 정량 분석 — 8 그룹 30+ 축 (기술·리스크·팩터·백테스트·알파).

        Parameters
        ----------
        axis : str | None
            분석 축 또는 별칭. None 이면 가이드 DataFrame 반환.
            주요 축: "판단"(verdict), "모멘텀", "변동성", "시뮬레이션",
            "가치평가"(valuation), "altman", "piotroski", "bab" 등 30+ 축.
        stockCode : str | list | None
            종목코드/ticker. 두 번째 인자: quant("모멘텀", "005930").
            market 자동 감지 (6자리→KR, 알파벳→US).
        **kwargs
            축별 추가 파라미터. 리스크 축은 ``benchmarkMode="market"|"sector"|"style"|"auto"``
            와 ``benchmark="코스피 200"`` 명시 override를 받는다.

        Returns
        -------
        dict
            종목 지정 시 축별 분석 결과:
                verdict(판단): signal, confidence, indicators (매수/매도/중립)
                momentum(모멘텀): returns, rsi, macd, moving_averages
                volatility(변동성): realized, garch, regime
                benchmark(벤치마크): benchmarkUsed, benchmarkStack, 기간 수익률 (%)
                simulation(시뮬레이션): paths, expectedReturn, var (%)
                altman: zScore, zone (safe/grey/distress)
                piotroski: fScore (0~9점)
        pl.DataFrame
            axis=None: 가이드 — 축 목록 + 설명 + 예시.
            횡단면 축 (market="KR"): 전종목 DataFrame.

        Raises
        ------
        ValueError
            축 이름이 등록되지 않은 경우.
            종목 필수 축에서 stockCode 누락 시.
        TypeError
            axis 에 list 전달 시.

        Examples
        --------
        >>> c.quant()                          # 가이드
        >>> c.quant("판단")                     # 종합 매수/매도 판단
        >>> c.quant("모멘텀")                   # 모멘텀 지표
        >>> dartlab.quant("altman", "005930")   # Altman Z-Score
        >>> dartlab.quant("piotroski", "005930")  # Piotroski F-Score

        Notes
        -----
        주가 데이터는 gather("price") 경유 자동 수집. API 키 불필요 (Naver/Yahoo).

        Guide
        -----
        AI 역할: AI는 quant를 가격·팩터·시계열 신호 엔진으로 보고 기간, benchmark, 수익률/변동성 근거를 분리한다.
        When: 주가 기반 기술적 신호·팩터·리스크를 정량 분석할 때.
        How: quant("판단") 으로 종합 신호 확인 → 세부 축으로 근거 파악.
            quant("벤치마크") 로 시장·섹터·스타일 benchmarkStack 을 확인한다.
            beta/residual/factor/BAB 는 기본 market mode를 유지하고,
            benchmarkMode="sector" 또는 "style" 로 상대 기준을 명시 전환한다.
            analysis(재무) + quant(기술) 조합이 story full/valuation 타입의 핵심.
            credit 과 함께 사용 시 altman/piotroski 로 부도 위험 교차 검증.
        Verified:
            - quant("판단") → RSI/ADX/MACD/볼린저/상대강도 + 종합 판정 (observed via ai-ask, 2026-04-25 — 정식 Phase P 판정 아님)
            - quant("베타", benchmarkMode="sector") → KRX 섹터 지수 대비 beta.

        See Also
        --------
        analysis : 재무 인과 분석 — quant 기술 + analysis 재무 조합.
        gather : 주가·수급 데이터 수집 — quant 의 데이터 원천.
        scan : 전종목 횡단 비교.

        LLM Specifications:
            AntiPatterns:
                - axis 추측 (한글 — 판단 / 모멘텀 / 변동성 / 가치 / 베타 / altman / piotroski 등)
                - stockCode 형식 혼동 — KR 6 자리 숫자 / US ticker 알파벳
                - axis="베타" 호출 시 benchmarkMode 미지정 (default market — 섹터 의도면 명시)
                - quant("005930", "판단") deprecated 형식 (axis 가 첫 인자)
            OutputSchema:
                - axis="판단": dict — signal / confidence / indicators
                - axis="모멘텀": dict — returns / rsi / macd / moving_averages
                - axis="베타": dict — beta / benchmarkUsed / benchmarkStack
                - axis="altman": dict — zScore / zone (safe / grey / distress)
                - axis="piotroski": dict — fScore (0~9)
                - axis 미지정: 가이드 DataFrame
            Prerequisites:
                - 주가 데이터 (gather("price") 자동 수집) — 첫 호출 시간 소요
            Freshness:
                price 데이터 — T+1 (전일 종가).
            Dataflow:
                axis 입력 → _ALIASES/_OLD_METRICS 정규화 → _AXIS_REGISTRY 룩업
                → gather("price")/scan/synth 데이터 패치 → 축별 calc 함수
                → 종목 dict 또는 횡단면 pl.DataFrame 반환.
            TargetMarkets:
                - KR (Naver Finance)
                - US (Yahoo Finance)
        """
        if axis is None and stockCode is None:
            return self._guide()

        # ── 하위호환 브릿지 ──
        # 기존: quant("005930", "indicators") → 새: quant("indicators", "005930")
        if axis is not None and isinstance(axis, str) and _isStockCode(axis):
            if stockCode is not None and isinstance(stockCode, str):
                if stockCode in _AXIS_REGISTRY or stockCode in _ALIASES or stockCode in _OLD_METRICS:
                    # swap: quant("005930", "indicators") → quant("indicators", "005930")
                    warnings.warn(
                        f'dartlab.quant("{axis}", "{stockCode}") 호출 방식은 deprecated입니다. '
                        f'dartlab.quant("{stockCode}", "{axis}") 형태를 사용하세요.',
                        DeprecationWarning,
                        stacklevel=2,
                    )
                    # flags → verdict로 매핑
                    actual_axis = stockCode if stockCode != "flags" else "verdict"
                    return self._dispatch(actual_axis, axis, **kwargs)
            elif stockCode is None:
                # quant("005930") → verdict
                warnings.warn(
                    f'dartlab.quant("{axis}") 호출 방식은 deprecated입니다. '
                    f'dartlab.quant("verdict", "{axis}") 형태를 사용하세요.',
                    DeprecationWarning,
                    stacklevel=2,
                )
                return self._dispatch("verdict", axis, **kwargs)

        # ── 정상 경로 ──
        if isinstance(axis, str):
            return self._dispatch(axis, stockCode, **kwargs)

        # axis가 list면 포트폴리오 가이드 없이 에러
        msg = f"축 이름(str) 또는 None을 전달하세요. 받은 값: {type(axis)}"
        raise TypeError(msg)

    def _dispatch(self, axis: str, stockCode: str | list | None, **kwargs: Any) -> Any:
        """축을 해석하고 해당 모듈의 함수를 호출."""
        key = _resolve(axis)
        entry = _AXIS_REGISTRY[key]

        # 종목 필수인데 없으면 에러
        if entry.stockRequired and not entry.multiStock and stockCode is None:
            msg = f'quant("{entry.label}") 축은 종목코드가 필요합니다.\n  사용법: {entry.example}'
            raise ValueError(msg)

        # 멀티종목인데 리스트가 아니면 안내
        if entry.multiStock and stockCode is not None and not isinstance(stockCode, list):
            stockCode = [stockCode]

        # lazy import + 호출
        mod = importlib.import_module(entry.module)
        fn = getattr(mod, entry.fn)

        if entry.multiStock:
            return fn(stockCodes=stockCode or [], **kwargs)
        elif entry.stockRequired:
            return fn(stockCode=stockCode, **kwargs)
        else:
            # 횡단면: 종목 불필요, 있으면 필터
            if stockCode is not None:
                return fn(stockCode=stockCode, **kwargs)
            return fn(**kwargs)

    def _guide(self) -> pl.DataFrame:
        """축 카탈로그 — 통일 컬럼 (axis, label, description, example, group)."""
        from dartlab.synth.axisGuide import buildAxisGuideDataFrame

        def _desc(_k: str, entry) -> str:
            if not entry.stockRequired:
                return entry.description + " (종목 불필요)"
            if entry.multiStock:
                return entry.description + " (종목 리스트)"
            return entry.description

        return buildAxisGuideDataFrame(
            _AXIS_REGISTRY,
            groupExtractor=lambda _k, e: _GROUPS.get(e.group, e.group),
            descriptionExtractor=_desc,
            apiKey=None,
        )

    def __repr__(self) -> str:
        # 그룹별 축 이름 수집
        grouped: dict[str, list[str]] = {}
        for key, entry in _AXIS_REGISTRY.items():
            g = _GROUPS.get(entry.group, entry.group)
            grouped.setdefault(g, []).append(key)

        lines = [
            f"Quant — {len(_AXIS_REGISTRY)}축 종목 레벨 정량분석",
            "",
            "━━━ 그룹별 축 ━━━",
        ]
        for g, axes in grouped.items():
            lines.append(f"  {g} ({len(axes)}): {', '.join(axes)}")

        lines += [
            "",
            "━━━ 빠른 시작 ━━━",
            '  c = dartlab.Company("005930")',
            "  c.quant()                             # 이 가이드",
            '  c.quant("종합")                        # 기술적 종합 판정',
            '  c.quant("모멘텀")                      # 모멘텀 분석',
            '  c.quant("베타")                        # 시장 베타 + CAPM',
            "",
            "━━━ 데이터 ━━━",
            "  주가 OHLCV: 자동 수집 (네이버/Yahoo, API 키 불필요)",
            "  재무 데이터: scan/finance.parquet (자동 다운로드)",
            "",
            "  노트북: https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/04_quant.py",
        ]
        return "\n".join(lines)

    # scan → quant 폐쇄 루프 — axis 미등록 (top-level helper)
    def scanBacktest(self, scanResult, **kwargs) -> dict:
        """scan 결과 universe + signalFn / style → multi-asset backtest.

        ``runScanBacktest`` 를 ``dartlab.quant`` attribute 로 노출. axis 미등록 —
        registry dispatcher 의 ``fn(stockCode, **kw)`` 계약과 시그니처가 어긋나기 때문.
        세부 시그니처는 ``dartlab.quant.screen.scanBacktest.runScanBacktest`` 참고.

        Example:
            >>> Quant.scanBacktest(scan("저PER"), signalFn=...)

        Requires:
            scanResult 가 universe (종목 list/DataFrame) 보유.

        Raises:
            ValueError — runScanBacktest 내부 검증 실패 시.
        """
        from dartlab.quant.screen.scanBacktest import runScanBacktest

        return runScanBacktest(scanResult, **kwargs)

    # accessor 패턴: quant.momentum("005930")
    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            key = _resolve(name)
        except KeyError:
            raise AttributeError(f"Quant has no axis '{name}'") from None

        entry = _AXIS_REGISTRY[key]

        def _run(stockCode=None, **kw):
            return self._dispatch(key, stockCode, **kw)

        _run.__doc__ = f"{entry.label}: {entry.description}"
        return _run


# scanBacktest top-level helper — 서브모듈과 같은 이름이라 module attribute 를
# 함수 binding 으로 덮어쓰기 (dl.quant.scanBacktest(scanResult, ...) 호출 가능).
from dartlab.quant.screen.scanBacktest import runScanBacktest as scanBacktest  # noqa: E402, F401
