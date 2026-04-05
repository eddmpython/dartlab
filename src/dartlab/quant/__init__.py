"""종목 레벨 정량분석 엔진 — 30축 7그룹.

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

from dartlab.quant.analyzer import enrichWithIndicators, technicalVerdict

__all__ = ["Quant", "enrichWithIndicators", "technicalVerdict"]


# ── Axis Registry ────────────────────────────────────────


@dataclass(frozen=True)
class _AxisEntry:
    """quant 축 메타데이터."""

    module: str
    fn: str
    label: str
    description: str
    example: str
    group: str
    stockRequired: bool = True  # False = 횡단면/시장 레벨
    multiStock: bool = False  # True = 종목 리스트 입력


# ── A: 기술적 (technical) — 가격 전용 ────────────────────

_AXIS_REGISTRY: dict[str, _AxisEntry] = {
    "indicators": _AxisEntry(
        module="dartlab.quant._ax_technical",
        fn="analyze_indicators",
        label="지표",
        description="45개 기술적 지표 DataFrame (SMA, EMA, MACD, RSI, BB 등)",
        example='quant("지표", "005930")',
        group="technical",
    ),
    "signals": _AxisEntry(
        module="dartlab.quant._ax_technical",
        fn="analyze_signals",
        label="신호",
        description="최근 매매 신호 이벤트 (골든크로스, RSI, MACD, 볼린저)",
        example='quant("신호", "005930")',
        group="technical",
    ),
    "verdict": _AxisEntry(
        module="dartlab.quant._ax_technical",
        fn="analyze_verdict",
        label="판단",
        description="종합 기술적 판단 (강세/중립/약세) + RSI/SMA/BB",
        example='quant("판단", "005930")',
        group="technical",
    ),
    "momentum": _AxisEntry(
        module="dartlab.quant.momentum",
        fn="analyze_momentum",
        label="모멘텀",
        description="12-1개월 횡단면, 시계열 모멘텀, 52주 신고가 비율",
        example='quant("모멘텀", "005930")',
        group="technical",
    ),
    "volatility": _AxisEntry(
        module="dartlab.quant.volatility",
        fn="analyze_volatility",
        label="변동성",
        description="GARCH(1,1), HAR-RV 실현변동성, 변동성 기간구조",
        example='quant("변동성", "005930")',
        group="technical",
    ),
    "regime": _AxisEntry(
        module="dartlab.quant.regime",
        fn="analyze_regime",
        label="레짐",
        description="Hamilton 2-state HMM (bull/bear), 추세추종 신호",
        example='quant("레짐", "005930")',
        group="technical",
    ),
    "pattern": _AxisEntry(
        module="dartlab.quant.pattern",
        fn="analyze_pattern",
        label="패턴",
        description="캔들스틱 10종 + zigzag 기반 지지/저항",
        example='quant("패턴", "005930")',
        group="technical",
    ),
    # ── B: 리스크 (risk) — 가격 + 벤치마크 ────────────────
    "beta": _AxisEntry(
        module="dartlab.quant._ax_technical",
        fn="analyze_beta",
        label="베타",
        description="시장 베타 + CAPM + 알파 + R²",
        example='quant("베타", "005930")',
        group="risk",
    ),
    "factor": _AxisEntry(
        module="dartlab.quant.factor",
        fn="analyze_factor",
        label="팩터",
        description="Fama-French 5 + q-factor 분해 (MKT/SMB/HML/RMW/CMA)",
        example='quant("팩터", "005930")',
        group="risk",
    ),
    "tailrisk": _AxisEntry(
        module="dartlab.quant.tailrisk",
        fn="analyze_tailrisk",
        label="꼬리위험",
        description="CVaR, 최대낙폭, Sortino, 하방편차",
        example='quant("꼬리위험", "005930")',
        group="risk",
    ),
    "residual": _AxisEntry(
        module="dartlab.quant.residual",
        fn="analyze_residual",
        label="잔여수익",
        description="팩터 제거 후 잔여 모멘텀/알파",
        example='quant("잔여수익", "005930")',
        group="risk",
    ),
    # ── C: 미시구조 (microstructure) — 가격 + 거래량/수급 ─
    "liquidity": _AxisEntry(
        module="dartlab.quant.microstructure",
        fn="analyze_liquidity",
        label="유동성",
        description="Amihud 비유동성, Roll 스프레드, 회전율",
        example='quant("유동성", "005930")',
        group="microstructure",
    ),
    "flow": _AxisEntry(
        module="dartlab.quant.flowAnalysis",
        fn="analyze_flow",
        label="수급",
        description="기관/외국인 매매 분석 (KR전용)",
        example='quant("수급", "005930")',
        group="microstructure",
    ),
    "volume": _AxisEntry(
        module="dartlab.quant.volumeAnalysis",
        fn="analyze_volume",
        label="거래량",
        description="OBV 추세, 거래량-가격 괴리, 누적분배",
        example='quant("거래량", "005930")',
        group="microstructure",
    ),
    # ── D: 펀더멘털 퀀트 (fundamental) — scan 프리빌드 ────
    "divergence": _AxisEntry(
        module="dartlab.quant._ax_technical",
        fn="analyze_divergence",
        label="괴리",
        description="재무-기술적 괴리 진단",
        example='quant("괴리", "005930")',
        group="fundamental",
    ),
    "quality": _AxisEntry(
        module="dartlab.quant.qualityFactor",
        fn="analyze_quality",
        label="퀄리티",
        description="Asness 퀄리티 팩터: 수익성+안전성+성장성 복합",
        example='quant("퀄리티", "005930")',
        group="fundamental",
    ),
    "value": _AxisEntry(
        module="dartlab.quant.valueFactor",
        fn="analyze_value",
        label="가치",
        description="가치 신호: PBR/PER/PSR vs 가격 모멘텀",
        example='quant("가치", "005930")',
        group="fundamental",
    ),
    "earnings": _AxisEntry(
        module="dartlab.quant.earningsMomentum",
        fn="analyze_earnings",
        label="이익모멘텀",
        description="SUE, PEAD, 이익 수정 모멘텀",
        example='quant("이익모멘텀", "005930")',
        group="fundamental",
    ),
    # ── E: 텍스트/공시 (text) — dartlab 고유 차별화 ───────
    "sentiment": _AxisEntry(
        module="dartlab.quant.textSentiment",
        fn="analyze_sentiment",
        label="공시심리",
        description="Loughran-McDonald 감성 사전 기반 공시 텍스트 스코어링",
        example='quant("공시심리", "005930")',
        group="text",
    ),
    "toneChange": _AxisEntry(
        module="dartlab.quant.toneChange",
        fn="analyze_tone_change",
        label="톤변화",
        description="기간별 공시 톤 변화 감지",
        example='quant("톤변화", "005930")',
        group="text",
    ),
    "eventSignal": _AxisEntry(
        module="dartlab.quant.eventSignal",
        fn="analyze_event_signal",
        label="이벤트신호",
        description="allFilings 이벤트 기반 신호 (경영진변경, M&A 등)",
        example='quant("이벤트신호", "005930")',
        group="text",
    ),
    "riskText": _AxisEntry(
        module="dartlab.quant.riskText",
        fn="analyze_risk_text",
        label="리스크텍스트",
        description="리스크 팩터 출현/소멸 텍스트 델타",
        example='quant("리스크텍스트", "005930")',
        group="text",
    ),
    "governanceQuant": _AxisEntry(
        module="dartlab.quant.governanceQuant",
        fn="analyze_governance_quant",
        label="거버넌스퀀트",
        description="지배구조 품질 정량화 (사외이사비율, 감사의견, 보수)",
        example='quant("거버넌스퀀트", "005930")',
        group="text",
    ),
    # ── F: 횡단면 (crossSection) — 시장 레벨 ─────────────
    "ranking": _AxisEntry(
        module="dartlab.quant.ranking",
        fn="analyze_ranking",
        label="순위",
        description="멀티팩터 복합 순위 (모멘텀+가치+퀄리티+리스크)",
        example='quant("순위")',
        group="crossSection",
        stockRequired=False,
    ),
    "pairs": _AxisEntry(
        module="dartlab.quant.pairsTrading",
        fn="analyze_pairs",
        label="페어",
        description="공적분 기반 페어 트레이딩 후보 탐색",
        example='quant("페어")',
        group="crossSection",
        stockRequired=False,
    ),
    "screen": _AxisEntry(
        module="dartlab.quant.screening",
        fn="analyze_screen",
        label="스크린",
        description="팩터 스크리닝 프리셋 (가치/모멘텀/퀄리티/저변동)",
        example='quant("스크린")',
        group="crossSection",
        stockRequired=False,
    ),
    # ── G: 포트폴리오 (portfolio) — 멀티종목 ─────────────
    "meanvar": _AxisEntry(
        module="dartlab.quant.portfolio",
        fn="analyze_meanvar",
        label="평균분산",
        description="Markowitz 평균-분산 최적화",
        example='quant("평균분산", ["005930","000660"])',
        group="portfolio",
        multiStock=True,
    ),
    "riskparity": _AxisEntry(
        module="dartlab.quant.portfolio",
        fn="analyze_riskparity",
        label="리스크패리티",
        description="HRP (Lopez de Prado) 계층적 리스크 패리티",
        example='quant("리스크패리티", ["005930","000660"])',
        group="portfolio",
        multiStock=True,
    ),
    "allocation": _AxisEntry(
        module="dartlab.quant.portfolio",
        fn="analyze_allocation",
        label="자산배분",
        description="Black-Litterman + 리스크 버짓팅",
        example='quant("자산배분", ["005930","000660"])',
        group="portfolio",
        multiStock=True,
    ),
}

# ── Alias 테이블 ─────────────────────────────────────────

_ALIASES: dict[str, str] = {
    # A: 기술적
    "지표": "indicators",
    "기술지표": "indicators",
    "신호": "signals",
    "매매신호": "signals",
    "판단": "verdict",
    "종합판단": "verdict",
    "기술판단": "verdict",
    "모멘텀": "momentum",
    "추세": "momentum",
    "변동성": "volatility",
    "vol": "volatility",
    "레짐": "regime",
    "국면": "regime",
    "패턴": "pattern",
    "캔들": "pattern",
    "차트패턴": "pattern",
    # B: 리스크
    "베타": "beta",
    "시장베타": "beta",
    "팩터": "factor",
    "팩터분해": "factor",
    "꼬리위험": "tailrisk",
    "테일리스크": "tailrisk",
    "CVaR": "tailrisk",
    "최대낙폭": "tailrisk",
    "잔여수익": "residual",
    "잔여모멘텀": "residual",
    "알파": "residual",
    # C: 미시구조
    "유동성": "liquidity",
    "비유동성": "liquidity",
    "수급": "flow",
    "외국인": "flow",
    "기관": "flow",
    "거래량": "volume",
    "OBV": "volume",
    # D: 펀더멘털 퀀트
    "괴리": "divergence",
    "재무괴리": "divergence",
    "퀄리티": "quality",
    "품질": "quality",
    "가치": "value",
    "밸류": "value",
    "이익모멘텀": "earnings",
    "SUE": "earnings",
    "PEAD": "earnings",
    # E: 텍스트/공시
    "공시심리": "sentiment",
    "감성": "sentiment",
    "톤변화": "toneChange",
    "이벤트신호": "eventSignal",
    "이벤트": "eventSignal",
    "리스크텍스트": "riskText",
    "거버넌스퀀트": "governanceQuant",
    "거버넌스": "governanceQuant",
    "지배구조": "governanceQuant",
    # F: 횡단면
    "순위": "ranking",
    "랭킹": "ranking",
    "페어": "pairs",
    "페어트레이딩": "pairs",
    "스크린": "screen",
    "스크리닝": "screen",
    "필터": "screen",
    # G: 포트폴리오
    "평균분산": "meanvar",
    "마코위츠": "meanvar",
    "리스크패리티": "riskparity",
    "HRP": "riskparity",
    "자산배분": "allocation",
    "블랙리터만": "allocation",
}

# 기존 metric 이름 (하위호환용)
_OLD_METRICS = {"indicators", "signals", "beta", "divergence", "flags", "verdict"}


# ── 축 해석 ──────────────────────────────────────────────


def _resolve(axis: str) -> str:
    """한글/영문 alias → 정규 축 이름으로 변환."""
    stripped = axis.strip()
    lower = stripped.lower()
    if lower in _AXIS_REGISTRY:
        return lower
    # camelCase 매칭 (toneChange, eventSignal 등)
    if stripped in _AXIS_REGISTRY:
        return stripped
    if stripped in _ALIASES:
        return _ALIASES[stripped]
    if lower in _ALIASES:
        return _ALIASES[lower]
    # fuzzy hint
    axis_names = sorted(set(list(_AXIS_REGISTRY.keys()) + list(_ALIASES.keys())))
    hint = ", ".join(axis_names[:20])
    msg = f"'{axis}' 축을 찾을 수 없습니다. 사용 가능: {hint}..."
    raise KeyError(msg)


def _is_stock_code(value: str) -> bool:
    """값이 종목코드처럼 보이는지 판별."""
    if not isinstance(value, str):
        return False
    s = value.strip()
    # 6자리 숫자 (한국)
    if re.match(r"^\d{6}$", s):
        return True
    # 알파벳 1-5자 (미국 ticker)
    if re.match(r"^[A-Z]{1,5}$", s.upper()) and s.lower() not in _AXIS_REGISTRY and s not in _ALIASES:
        return True
    return False


# ── 그룹 정의 ────────────────────────────────────────────

_GROUPS = {
    "technical": "기술적",
    "risk": "리스크",
    "microstructure": "미시구조",
    "fundamental": "펀더멘털",
    "text": "텍스트/공시",
    "crossSection": "횡단면",
    "portfolio": "포트폴리오",
}


# ── Quant 클래스 ─────────────────────────────────────────


class Quant:
    """종목 레벨 정량분석 엔진 — 30축 7그룹.

    dartlab.quant("축명", "종목코드") 로 접근.
    """

    def __call__(
        self,
        axis: str | list | None = None,
        stockCode: str | list | None = None,
        **kwargs: Any,
    ) -> pl.DataFrame | dict | Any:
        """정량분석 실행.

        Args:
            axis: 분석 축 (None이면 가이드). 종목코드도 가능 (하위호환).
            stockCode: 종목코드/ticker 또는 종목 리스트.
            **kwargs: 축별 추가 파라미터.

        Returns:
            가이드 DataFrame, 분석 결과 dict, 또는 DataFrame.
        """
        if axis is None and stockCode is None:
            return self._guide()

        # ── 하위호환 브릿지 ──
        # 기존: quant("005930", "indicators") → 새: quant("indicators", "005930")
        if axis is not None and isinstance(axis, str) and _is_stock_code(axis):
            if stockCode is not None and isinstance(stockCode, str):
                if stockCode.lower() in _AXIS_REGISTRY or stockCode in _ALIASES or stockCode in _OLD_METRICS:
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
            msg = (
                f'quant("{entry.label}") 축은 종목코드가 필요합니다.\n'
                f"  사용법: {entry.example}"
            )
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
        """축 카탈로그 — 그룹별 정리."""
        rows = []
        for key, entry in _AXIS_REGISTRY.items():
            group_label = _GROUPS.get(entry.group, entry.group)
            stock_note = ""
            if not entry.stockRequired:
                stock_note = " (종목 불필요)"
            elif entry.multiStock:
                stock_note = " (종목 리스트)"
            rows.append(
                {
                    "그룹": group_label,
                    "축": entry.label,
                    "key": key,
                    "설명": entry.description + stock_note,
                    "예시": entry.example,
                }
            )
        return pl.DataFrame(rows)

    def __repr__(self) -> str:
        counts = {}
        for entry in _AXIS_REGISTRY.values():
            g = _GROUPS.get(entry.group, entry.group)
            counts[g] = counts.get(g, 0) + 1
        parts = [f"{g} {n}" for g, n in counts.items()]
        return f"Quant({len(_AXIS_REGISTRY)}축: {', '.join(parts)})"

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
