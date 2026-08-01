"""Strategy 5축 dispatch — strategy/backtest/style/entry/walkforward.

Quant 클래스의 `_AXIS_REGISTRY` 가 lazy import 하는 진입 모듈. analysis(L2) import 0.

5 axes:
    strategy     — Rule 직접 백테스트
    backtest     — style 또는 Rule 백테스트 (cpcv 옵션)
    style        — 8 프리셋 백테스트 (name="all" → 8개)
    entry        — 현재 시점 진입 진단
    walkforward  — Lopez 슬라이딩 window OOS Sharpe + DSR + PBO
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from dartlab.core.market import resolveMarket
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.quant.screen.dataAccess import fetchOhlcv, ohlcvToArrays
from dartlab.quant.strategy.backtest import (
    DEFAULT_FEE_BPS,
    DEFAULT_SLIP_BPS,
    BacktestResult,
    multiAssetBacktest,
    vectorBacktest,
    walkForward,
)
from dartlab.quant.strategy.backtest import (
    cpcv as cpcv_fn,
)
from dartlab.quant.strategy.presets import (
    STYLE_REGISTRY,
    listStyles,
    resolveStyle,
)
from dartlab.quant.strategy.rule import Rule


@dataclass
class _StubCompany:
    """fetchOhlcv 에 종목코드만 전달하는 임시 wrapper.

    runStrategy 등이 stockCode 만 받기 때문에, 스타일 build 가 요구하는
    company.stockCode 인터페이스를 흉내낸다.
    `_strategy_start` 속성으로 styles/_common.getArrays 가 장기 OHLCV 가져옴.
    """

    stockCode: str
    _strategy_start: str | None = None


@dataclass(frozen=True)
class EntryVerdict:
    """현재 시점 진입 진단 (entry 축 결과)."""

    style: str
    active: bool  # 오늘 entry 신호 True 인가
    exit_today: bool  # 오늘 exit 신호 True 인가
    last_price: float | None
    stop_level: float | None
    last_date: str | None
    status: str = "ok"
    reason: str | None = None

    def __repr__(self) -> str:
        if self.status != "ok":
            return f"EntryVerdict(style={self.style!r}, status={self.status!r}, reason={self.reason!r})"
        flag = "BUY" if self.active else ("EXIT" if self.exit_today else "—")
        return f"EntryVerdict({self.style}, {flag}, price={self.last_price}, stop={self.stop_level})"


# ── 공통 헬퍼 ───────────────────────────────────────────────────────────────


def _arrays(stockCode: str, *, start: str | None = None) -> dict:
    """OHLCV 가져오기. start='2020-01-01' 같이 명시하면 장기 데이터."""
    kwargs = {"start": start} if start else {}
    df = fetchOhlcv(stockCode, **kwargs)
    if isEmptyDf(df):
        return {}
    return ohlcvToArrays(df)


def _buildRuleFromStyle(styleName: str, stockCode: str, *, start: str | None = None) -> Rule | BacktestResult:
    """스타일명 → Rule 또는 NotApplicable sentinel."""
    key = resolveStyle(styleName)
    reg = STYLE_REGISTRY()
    if key not in reg:
        return BacktestResult(
            status="error",
            reason=f"unknown style: {styleName!r} (available: {list(reg.keys())})",
            style=styleName,
        )
    company = _StubCompany(stockCode=stockCode, _strategy_start=start)
    return reg[key](company)


# ── 5축 dispatch ────────────────────────────────────────────────────────────


def runStrategy(
    stockCode: str,
    *,
    rule: Rule | None = None,
    oos: bool = False,
    train: int = 252,
    test: int = 63,
    step: int = 63,
    **kwargs,
) -> BacktestResult:
    """`c.quant("strategy", rule=...)` — 사용자 정의 룰 백테스트.

    Capabilities:
        - 사용자 Rule 객체 받아 in-sample vectorBacktest 또는 walkForward 자동 분기
        - OHLCV ≥ 60 봉 필수 + open/high/low/date 부가 데이터 자동 전달

    Args:
        stockCode: 종목코드.
        rule: Rule 객체 (필수).
        oos: True 면 walkForward (sliding OOS).
        train: walkForward train 윈도우 (일). 기본 ``252``.
        test: walkForward test 윈도우. 기본 ``63``.
        step: 슬라이딩 간격. 기본 ``63``.
        **kwargs: ``start``, ``feeBps``, ``slipBps`` 등 실행 인자.

    Returns:
        BacktestResult — vectorBacktest 또는 walkForward 결과.

    Guide:
        DSL Rule 작성 후 단일 종목에서 즉시 검증. OOS 검증 필요시 ``oos=True``.

    When:
        Quant strategy 축 + AI 사용자 룰 백테스트 답변.

    How:
        ``_arrays`` → close ≥ 60 확인 → oos 분기 → vectorBacktest 또는 walkForward.

    Requires:
        Rule 객체 + close 시계열 ≥ 60 봉.

    Raises:
        없음 — 누락 시 error sentinel BacktestResult.

    Example:
        >>> runStrategy("005930", rule=my_rule).sharpe
        1.42

    See Also:
        - runBacktest : 8 프리셋 + 사용자 Rule 통합
        - runWalkforward : walkForward 단독 진입

    AIContext:
        사용자가 정의한 Rule 평가 답변 시 sharpe/mdd 인용.
    """
    if rule is None:
        return BacktestResult(status="error", reason="rule= is required", style=None)
    arr = _arrays(stockCode, start=kwargs.get("start"))
    close = arr.get("close")
    if close is None or len(close) < 60:
        return BacktestResult(status="error", reason=f"insufficient OHLCV: {stockCode}", style=None)

    if oos:
        return walkForward(
            close,
            rule,
            train=train,
            test=test,
            step=step,
            open_=arr.get("open"),
            high=arr.get("high"),
            low=arr.get("low"),
            dates=arr.get("date"),
            feeBps=kwargs.get("feeBps", DEFAULT_FEE_BPS),
            slipBps=kwargs.get("slipBps", DEFAULT_SLIP_BPS),
        )
    return vectorBacktest(
        close,
        rule,
        open_=arr.get("open"),
        high=arr.get("high"),
        low=arr.get("low"),
        volume=arr.get("volume"),
        dates=arr.get("date"),
        feeBps=kwargs.get("feeBps", DEFAULT_FEE_BPS),
        slipBps=kwargs.get("slipBps", DEFAULT_SLIP_BPS),
    )


def runBacktest(
    stockCode: str,
    *,
    style: str | Rule | None = None,
    cpcv: bool = False,
    nSplits: int = 6,
    nTest: int = 2,
    embargo: int = 5,
    **kwargs,
) -> BacktestResult:
    """`c.quant("backtest", style=... or rule=...)` — 단일 백테스트.

    Parameters
    ----------
    stockCode : str
        종목코드 (예: "005930").
    style : str | Rule | None
        8 프리셋 스타일명 또는 사용자 Rule 객체.
    cpcv : bool
        True 면 Combinatorial Purged Cross-Validation 실행.
    n_splits : int
        CPCV fold 수.
    n_test : int
        CPCV 테스트 fold 수.
    embargo : int
        CPCV 엠바고 기간 (일).
    **kwargs
        start : str — OHLCV 시작일 (예: "2014-01-01").
        feeBps, slipBps : float — 왕복 거래비용 (bps).

    Returns
    -------
    BacktestResult
        status : str — "ok" | "error" | "data_limited" | "not_applicable"
        reason : str | None — 에러/제한 사유
        style : str | None — 스타일명
        sharpe : float — Sharpe 비율 (배)
        mdd : float — 최대 낙폭 (%)
        dsr : float — Deflated Sharpe Ratio (배)
        trades : pl.DataFrame | None — 개별 거래 내역
        oos : bool — Out-of-Sample 여부

    Examples
    --------
    >>> c.quant("backtest", style="trendFollow")

    Capabilities:
        - 8 프리셋 스타일 또는 사용자 Rule 으로 단일 백테스트
        - KR-only 스타일 (flowFollow/seasonalKR) 시장 사전 체크 + cpcv 옵션

    Guide:
        Quant strategy 표준 진입. ``cpcv=True`` 면 Combinatorial Purged CV (과적합 검정).

    When:
        Quant strategy 백테스트 + AI 스타일 추천 답변.

    How:
        style str/Rule 분기 → ``_buildRuleFromStyle`` → vectorBacktest 또는 cpcv_fn.

    Requires:
        OHLCV ≥ 60 봉 + KR-only 스타일은 KR 시장 종목.

    Raises:
        없음 — 데이터 부족/스타일 미적용 시 sentinel BacktestResult.

    See Also:
        - runStrategy : 사용자 Rule 전용
        - runStyle : 8 스타일 일괄

    AIContext:
        스타일 별 백테스트 답변 시 sharpe/mdd/dsr 인용. status="data_limited" 면 데이터 부족.
    """
    if style is None:
        return BacktestResult(status="error", reason="style= or Rule= is required", style=None)

    # KR-only 사전 체크 (OHLCV fetch 전) — _build_rule_from_style 이 NotApplicable 반환
    if isinstance(style, str):
        key = resolveStyle(style)
        if key in {"flowFollow", "seasonalKR"} and resolveMarket(stockCode, "auto") != "KR":
            return BacktestResult.notApplicable(
                style=key,
                reason=f"KR-only style: {key} (data not available for non-KR markets)",
            )

    arr = _arrays(stockCode, start=kwargs.get("start"))
    close = arr.get("close")
    if close is None or len(close) < 60:
        return BacktestResult(status="error", reason=f"insufficient OHLCV: {stockCode}", style=None)

    if isinstance(style, Rule):
        rule = style
        styleName = rule.meta.get("style")
    else:
        result = _buildRuleFromStyle(style, stockCode, start=kwargs.get("start"))
        if isinstance(result, BacktestResult):
            return result  # NotApplicable 또는 error sentinel
        rule = result
        styleName = resolveStyle(style)

    # Phase 4 R4 — flowFollow 등 데이터 부족 시 data_limited sentinel
    if rule.meta.get("error") == "data_limited":
        return BacktestResult(
            status="data_limited",
            reason=rule.meta.get("reason", "data limited"),
            style=styleName,
        )

    if cpcv:
        return cpcv_fn(
            close,
            rule,
            nSplits=nSplits,
            nTest=nTest,
            embargo=embargo,
            open_=arr.get("open"),
            high=arr.get("high"),
            low=arr.get("low"),
            style=styleName,
            feeBps=kwargs.get("feeBps", DEFAULT_FEE_BPS),
            slipBps=kwargs.get("slipBps", DEFAULT_SLIP_BPS),
        )
    return vectorBacktest(
        close,
        rule,
        open_=arr.get("open"),
        high=arr.get("high"),
        low=arr.get("low"),
        volume=arr.get("volume"),
        dates=arr.get("date"),
        style=styleName,
        feeBps=kwargs.get("feeBps", DEFAULT_FEE_BPS),
        slipBps=kwargs.get("slipBps", DEFAULT_SLIP_BPS),
    )


def runStyle(
    stockCode: str | None = None,
    *,
    name: str = "all",
    **kwargs,
) -> dict[str, BacktestResult] | pl.DataFrame:
    """`c.quant("style", name=...)` — 8 프리셋 일괄/단일 백테스트.

    name="all" 또는 None → 8개 모두. name 명시 시 단일.
    stockCode 가 None 이면 가이드 카탈로그 DataFrame 반환.

    Capabilities:
        - 단일 종목 8 스타일 일괄 백테스트 → ``{styleName: BacktestResult}``
        - stockCode 미지정 시 ``listStyles`` 카탈로그 DataFrame 반환

    Args:
        stockCode: 종목코드. None 이면 카탈로그.
        name: 스타일 명 또는 ``"all"``.
        **kwargs: ``start``, ``feeBps``, ``slipBps`` 등 실행 인자.

    Returns:
        dict[str, BacktestResult] (name="all") 또는 BacktestResult (단일) 또는 pl.DataFrame (카탈로그).

    Guide:
        Quant strategy 표준 다중 스타일 진입. story 6 막 전망 박스 입력.

    When:
        Quant strategy 다중 스타일 평가 + AI 스타일 비교 답변.

    How:
        stockCode None → 카탈로그. ``name="all"`` → STYLE_REGISTRY 순회 + ``runBacktest``.

    Requires:
        stockCode 명시 시 OHLCV ≥ 60 봉.

    Raises:
        없음.

    Example:
        >>> r = runStyle("005930", name="all")
        >>> r["trendFollow"].sharpe
        1.2

    See Also:
        - runBacktest : 단일 스타일
        - listStyles : 카탈로그

    AIContext:
        "어느 스타일이 잘 맞나" 답변 시 sharpe top 인용.
    """
    if stockCode is None:
        # 카탈로그 가이드 모드
        return pl.DataFrame(listStyles())

    name = name or "all"
    if name == "all":
        results = {}
        for key in STYLE_REGISTRY().keys():
            results[key] = runBacktest(stockCode, style=key, **kwargs)
        return results

    return runBacktest(stockCode, style=name, **kwargs)


def runEntry(
    stockCode: str,
    *,
    style: str = "all",
    **kwargs,
) -> dict[str, EntryVerdict]:
    """`c.quant("entry", style=...)` — 현재 시점 진입 진단.

    백테스트 안 돌리고 마지막 봉의 entry/exit 신호 + stop level 만 한 줄 반환.

    Capabilities:
        - 마지막 봉의 entry/exit boolean + ATR stop level 즉시 평가 (백테스트 skip)
        - 8 스타일 일괄 또는 단일 → ``{styleName: EntryVerdict}``

    Args:
        stockCode: 종목코드.
        style: ``"all"`` 또는 스타일 명.
        **kwargs: ``feeBps``, ``slipBps`` 등 실행 인자.

    Returns:
        dict[str, EntryVerdict] — keys = 스타일 명, value = active/exit_today/stop_level.

    Guide:
        실시간 매수/매도 신호 진단. 백테스트 보다 빠르고 stop level 까지 함께 제공.

    When:
        오늘 진입 판단 + AI "지금 진입 가능 스타일" 답변.

    How:
        ``_arrays`` → close ≥ 30 → STYLE_REGISTRY 순회 → 마지막 봉 entry/exit + ATR stop.

    Requires:
        OHLCV ≥ 30 봉 + (선택) high/low (ATR stop level).

    Raises:
        없음 — 데이터 부족 시 ``_error`` key.

    Example:
        >>> verdicts = runEntry("005930")
        >>> verdicts["trendFollow"].active
        True

    See Also:
        - runStyle : 백테스트 일괄
        - calcStrategySnapshot : story 6 막 통합 진입

    AIContext:
        "오늘 매수 시그널" 답변 시 active=True 스타일 + stop_level 인용.
    """
    arr = _arrays(stockCode, start=kwargs.get("start"))
    close = arr.get("close")
    high = arr.get("high")
    low = arr.get("low")
    dates = arr.get("date")
    if close is None or len(close) < 30:
        return {
            "_error": EntryVerdict(
                style="-",
                active=False,
                exit_today=False,
                last_price=None,
                stop_level=None,
                last_date=None,
                status="error",
                reason=f"insufficient OHLCV: {stockCode}",
            )
        }

    last_price = float(close[-1])
    last_date_str = dates[-1].strftime("%Y-%m-%d") if dates else None

    keys = list(STYLE_REGISTRY().keys()) if style == "all" else [resolveStyle(style)]
    out: dict[str, EntryVerdict] = {}
    start = kwargs.get("start")
    for key in keys:
        result = _buildRuleFromStyle(key, stockCode, start=start)
        if isinstance(result, BacktestResult):
            out[key] = EntryVerdict(
                style=key,
                active=False,
                exit_today=False,
                last_price=last_price,
                stop_level=None,
                last_date=last_date_str,
                status=result.status,
                reason=result.reason,
            )
            continue
        rule = result
        if len(rule.entry_expr) == 0:
            out[key] = EntryVerdict(
                style=key,
                active=False,
                exit_today=False,
                last_price=last_price,
                stop_level=None,
                last_date=last_date_str,
                status="error",
                reason="empty rule",
            )
            continue
        active = bool(rule.entry_expr[-1])
        exit_today = bool(rule.exit_expr[-1])
        # ATR stop level (옵션)
        stop_level = None
        if rule.stop and high is not None and low is not None:
            from dartlab.quant.strategy.backtest import _buildStopSeries

            stops = _buildStopSeries(close, high, low, rule.stop)
            if not np.isnan(stops[-1]):
                stop_level = float(stops[-1])
        out[key] = EntryVerdict(
            style=key,
            active=active,
            exit_today=exit_today,
            last_price=last_price,
            stop_level=stop_level,
            last_date=last_date_str,
        )
    return out


def runMultiAsset(
    stockCodes: list[str] | None = None,
    *,
    style: str | None = None,
    weighting: str = "equal",
    **kwargs,
) -> BacktestResult:
    """`c.quant("multi", ["005930","000660",...], style="trendFollow")` — 멀티 종목 포트폴리오.

    Capabilities:
        - 단일 스타일 + 다종목 + 가중 방식 (equal/inv_vol/risk_parity) 으로 포트폴리오 백테스트
        - multiAssetBacktest 위임 → BacktestResult 동일 인터페이스

    Args:
        stockCodes: 종목 코드 리스트.
        style: 8 프리셋 스타일 이름.
        weighting: ``"equal"`` | ``"inv_vol"`` | ``"risk_parity"``.
        **kwargs: ``start`` 등.

    Returns:
        BacktestResult — 포트폴리오 단일 결과.

    Guide:
        단일 스타일을 다종목에 적용한 분산 효과 측정. weighting 선택으로 분산 강도 조절.

    When:
        멀티 종목 포트 평가 + AI "이 스타일로 N 종목 분산" 답변.

    How:
        resolveStyle → STYLE_REGISTRY → multiAssetBacktest 위임.

    Requires:
        stockCodes ≥ 1 + style 명시 + 각 종목 OHLCV 가용.

    Raises:
        없음 — 누락 시 error sentinel.

    Example:
        >>> r = runMultiAsset(["005930","000660"], style="trendFollow")
        >>> r.sharpe
        1.05

    See Also:
        - multiAssetBacktest : core engine
        - runStyle : 단일 종목

    AIContext:
        "다종목 분산 시 성과" 답변 시 포트 sharpe + 종목 수 인용.
    """
    if not stockCodes:
        return BacktestResult(status="error", reason="stockCodes list required", style=None)
    if not style:
        return BacktestResult(status="error", reason="style= required", style=None)

    key = resolveStyle(style)
    reg = STYLE_REGISTRY()
    if key not in reg:
        return BacktestResult(status="error", reason=f"unknown style: {style}", style=None)

    return multiAssetBacktest(
        list(stockCodes),
        reg[key],
        weighting=weighting,
        style=key,
        feeBps=kwargs.get("feeBps", DEFAULT_FEE_BPS),
        slipBps=kwargs.get("slipBps", DEFAULT_SLIP_BPS),
    )


def runWalkforward(
    stockCode: str,
    *,
    rule: Rule | None = None,
    style: str | None = None,
    train: int = 252,
    test: int = 63,
    step: int = 63,
    **kwargs,
) -> BacktestResult:
    """Lopez 슬라이딩 window Out-of-Sample 검증.

    학술 근거: Lopez de Prado (2018) — Advances in Financial ML.
    train 윈도우로 규칙을 학습하고 test 윈도우에서 OOS 성과를 측정,
    step 간격으로 슬라이딩하여 DSR·PBO 등 과적합 보정 지표를 산출한다.

    Parameters
    ----------
    stockCode : str
        종목코드 (예: "005930").
    rule : Rule | None
        사용자 정의 Rule 객체. style 과 배타적.
    style : str | None
        8 프리셋 스타일명. rule 과 배타적.
    train : int
        학습 윈도우 크기 (일, 기본 252).
    test : int
        테스트 윈도우 크기 (일, 기본 63).
    step : int
        슬라이딩 간격 (일, 기본 63).
    **kwargs
        start : str — OHLCV 시작일 (예: "2014-01-01").
        feeBps, slipBps : float — 왕복 거래비용 (bps).

    Returns
    -------
    BacktestResult
        status : str — "ok" | "error"
        reason : str | None — 에러 사유
        style : str | None — 스타일명
        sharpe : float — OOS Sharpe 비율 (배)
        mdd : float — OOS 최대 낙폭 (%)
        dsr : float — Deflated Sharpe Ratio (배)
        trades : pl.DataFrame | None — OOS 거래 내역
        oos : bool — True (항상 OOS)

    Examples
    --------
    >>> c.quant("walkforward", style="trendFollow")

    Capabilities:
        - Lopez de Prado 2018 sliding window OOS 검증 → DSR/PBO 과적합 보정 지표
        - rule 또는 style 분기 → walkForward core 위임

    Guide:
        train 윈도우로 학습 + test 윈도우 OOS 측정 + step 슬라이딩. ``train=252``, ``test=63``
        표준 (1년 학습 + 분기 테스트).

    When:
        과적합 검정 + AI 견고성 답변.

    How:
        ``_arrays`` → close ≥ train+test 확인 → rule 분기 → walkForward 위임.

    Requires:
        OHLCV ≥ train + test 봉 (기본 315 봉).

    Raises:
        없음.

    See Also:
        - runBacktest : in-sample
        - strategy.backtest.walkForward : core engine

    AIContext:
        "OOS 검정 결과" 답변 시 OOS sharpe + dsr 인용.
    """
    if rule is None and style is None:
        return BacktestResult(status="error", reason="rule= or style= required", style=None)

    arr = _arrays(stockCode, start=kwargs.get("start"))
    close = arr.get("close")
    if close is None or len(close) < train + test:
        return BacktestResult(
            status="error",
            reason=f"insufficient OHLCV for train+test: {stockCode}",
            style=None,
            oos=True,
        )

    if rule is None:
        result = _buildRuleFromStyle(style, stockCode)
        if isinstance(result, BacktestResult):
            return result
        rule = result

    return walkForward(
        close,
        rule,
        train=train,
        test=test,
        step=step,
        open_=arr.get("open"),
        high=arr.get("high"),
        low=arr.get("low"),
        dates=arr.get("date"),
        style=rule.meta.get("style") if rule.meta else None,
        feeBps=kwargs.get("feeBps", DEFAULT_FEE_BPS),
        slipBps=kwargs.get("slipBps", DEFAULT_SLIP_BPS),
    )
