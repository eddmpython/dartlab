"""Rule — boolean entry/exit + sizing/stop 명시 주입.

dartlab Strategy DSL 의 핵심 객체. 가중치 필드 없음 — 사용자가 boolean 으로 직접
컴포즈. sizing/stop 은 명시 안 하면 equal 1.0 / no stop.

사용 예:
    >>> from dartlab.quant.strategy import Rule
    >>> rule = (
    ...     Rule.entry(rsi_oversold & regime_bull)
    ...         .exit(rsi_overbought)
    ...         .withSizing("kelly", winProb=0.55, winLossRatio=2.0, fraction=0.25)
    ...         .withStop("atr", k=3.0)
    ... )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class Rule:
    """boolean entry/exit + sizing/stop 핸들 보관 (가중치 없음).

    Attributes:
        entry_expr: boolean numpy array (True = 진입 시그널)
        exit_expr: boolean numpy array (True = 청산 시그널)
        sizing: dict {method: str, kwargs: dict} — None 이면 equal 1.0
        stop: dict {method: str, kwargs: dict} — None 이면 no stop
        meta: 식별자/주석 (백테스트 결과에 포함)
    """

    entry_expr: np.ndarray
    exit_expr: np.ndarray
    sizing: dict[str, Any] | None = None
    stop: dict[str, Any] | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ent = np.asarray(self.entry_expr)
        ex = np.asarray(self.exit_expr)
        if ent.dtype != np.bool_:
            ent = ent.astype(np.bool_)
        if ex.dtype != np.bool_:
            ex = ex.astype(np.bool_)
        if len(ent) != len(ex):
            raise ValueError(f"entry/exit length mismatch: {len(ent)} vs {len(ex)}")
        self.entry_expr = ent
        self.exit_expr = ex

    @classmethod
    def entry(cls, expr) -> "_RuleBuilder":
        """체이닝 빌더 시작점.

        Parameters
        ----------
        expr : array-like
            boolean numpy array (True = 진입 시그널).

        Returns
        -------
        _RuleBuilder
            .exit() 로 이어서 Rule 완성.

        Example:
            >>> Rule.entry(rsi < 30).exit(rsi > 70)
            Rule(...)

        Requires:
            expr 가 array-like + boolean.

        Raises:
            없음.
        """
        return _RuleBuilder(entry=expr)

    def withSizing(self, method: str, **kwargs) -> "Rule":
        """진입 시 고정 포지션 사이징 - equal / fixed / kelly / vol_target_at_entry.

        명시 안 하면 equal 1.0 (전 자본 진입).

        Example:
            >>> rule.withSizing("fixed", weight=0.5)

        Requires:
            method와 인자는 vectorBacktest가 검증한다. 동적 vol targeting은 아직 지원하지
            않으며 ``vol_target_at_entry``는 신호 확정 시점의 trailing 변동성으로 거래
            전체의 고정 size를 정한다.

        Raises:
            없음.
        """
        return Rule(
            entry_expr=self.entry_expr,
            exit_expr=self.exit_expr,
            sizing={"method": method, "kwargs": kwargs},
            stop=self.stop,
            meta=self.meta,
        )

    def withStop(self, method: str, **kwargs) -> "Rule":
        """손절 명시 — atr / fixed_pct / chandelier.

        명시 안 하면 no stop (entry/exit 시그널만 사용, 홀드).

        Example:
            >>> rule.withStop("atr", multiplier=2.0)

        Requires:
            method 가 stop 메서드 키.

        Raises:
            없음.
        """
        return Rule(
            entry_expr=self.entry_expr,
            exit_expr=self.exit_expr,
            sizing=self.sizing,
            stop={"method": method, "kwargs": kwargs},
            meta=self.meta,
        )

    def withMeta(self, **kw) -> "Rule":
        """메타데이터 주입 — 백테스트 결과에 식별자/주석 포함.

        Parameters
        ----------
        **kw
            임의의 key=value 쌍 (예: name="myRule", version=2).

        Returns
        -------
        Rule
            meta 가 병합된 새 Rule.

        Requires:
            없음 — 빈 dict 와도 동작.

        Raises:
            없음 — 단순 dict merge.
        """
        merged = {**self.meta, **kw}
        return Rule(
            entry_expr=self.entry_expr,
            exit_expr=self.exit_expr,
            sizing=self.sizing,
            stop=self.stop,
            meta=merged,
        )

    def shiftLag(self, lag: int = 1) -> "Rule":
        """Lookahead 가드 — entry/exit boolean 을 lag 봉만큼 미루기.

        사용자가 만든 신호가 t 시점 정보를 사용했는지 확신 없을 때 paranoid mode.
        lag=1 이면 어제 신호로 오늘 진입 (next-bar 체결과 결합 시 t-1 신호 → t+1 체결).

        학술 근거: Lopez de Prado AFML — "When in doubt, shift by 1".

        Capabilities:
            - entry_expr/exit_expr 시리즈 lag 봉만큼 right-shift → 미래 정보 차단
            - meta 에 ``shift_lag`` 키로 기록

        Args:
            lag: 미룰 봉 수. 기본 ``1``. 0 이면 self 반환.

        Returns:
            Rule — 새 객체 (immutable 패턴).

        Guide:
            Lopez de Prado AFML 권고. lag=1 = next-bar 체결 안전 가드. lag=2+ = 매우 보수적.

        When:
            신호 안전성 검증 + AI lookahead 의혹 답변.

        How:
            새 array 초기화 → ent[lag:] = entry[:-lag] → 새 Rule 반환.

        Requires:
            self.entry_expr/exit_expr 동일 길이.

        Raises:
            없음.

        Example:
            >>> rule.shiftLag(1).meta["shift_lag"]
            1

        See Also:
            - lookaheadCheck : 누설 통계 검증
            - strategy.backtest.vectorBacktest : next-bar 체결

        AIContext:
            "lookahead bias 안전한가" 답변 시 shiftLag(1) 적용 권장.
        """
        if lag <= 0:
            return self
        n = len(self.entry_expr)
        ent = np.zeros(n, dtype=np.bool_)
        ex = np.zeros(n, dtype=np.bool_)
        if n > lag:
            ent[lag:] = self.entry_expr[:-lag]
            ex[lag:] = self.exit_expr[:-lag]
        return Rule(
            entry_expr=ent,
            exit_expr=ex,
            sizing=self.sizing,
            stop=self.stop,
            meta={**self.meta, "shift_lag": lag},
        )

    def lookaheadCheck(self, close: np.ndarray) -> dict:
        """Lookahead leakage sanity test — entries 가 미래 정보 누설했나 통계 검증.

        방법:
            1. entry 시점의 다음 N봉 수익률 분포 vs random 시점의 분포 비교.
            2. 만약 entry 시점 직후 수익률이 비현실적으로 높으면 leakage 의심.
            3. 정직한 신호는 +1~5% 정도, leakage 신호는 +20%+ 자주 나타남.

        Capabilities:
            - entry 시점 5 봉 forward return vs random 시점 비교 → ratio + suspicious 플래그
            - ratio > 5 + entry avg > 5% 또는 entry avg > 10% 시 suspicious=True

        Args:
            close: 종가 시계열 (entry_expr 길이 일치).

        Returns:
            dict — n_entries/entry_forward_5d_avg/random_forward_5d_avg/ratio/suspicious.

        Guide:
            Rule 검증의 paranoid sanity. suspicious=True 면 신호 정의 재검토.

        When:
            Rule 정의 검증 + AI "이 신호 신뢰" 답변.

        How:
            entry indices → 5 봉 forward → 평균 vs random 시점 평균 → ratio.

        Requires:
            self.entry_expr 길이 ≥ 30 + entry 시그널 ≥ 5.

        Raises:
            없음 — 부적 시 error dict.

        Example:
            >>> rule.lookaheadCheck(close)["suspicious"]
            False

        See Also:
            - shiftLag : 가드
            - strategy.backtest.vectorBacktest : 실제 백테스트

        AIContext:
            "이 룰 lookahead 의혹" 답변 시 ratio + suspicious 인용.
        """
        n = len(self.entry_expr)
        if n < 30 or len(close) != n:
            return {"error": "length mismatch or too short"}
        entry_indices = np.where(self.entry_expr)[0]
        if len(entry_indices) < 5:
            return {"error": "too few entry signals"}
        # 5봉 forward return at entry indices
        forward = 5
        valid_entries = entry_indices[entry_indices < n - forward]
        if len(valid_entries) < 5:
            return {"error": "too few valid entry indices"}
        entry_rets = np.array([close[i + forward] / close[i] - 1 for i in valid_entries], dtype=np.float64)
        # random baseline
        np.random.seed(42)
        rand_idx = np.random.randint(0, n - forward, size=max(len(valid_entries), 100))
        rand_rets = np.array([close[i + forward] / close[i] - 1 for i in rand_idx], dtype=np.float64)

        entry_avg = float(np.mean(entry_rets))
        rand_avg = float(np.mean(rand_rets))
        ratio = entry_avg / rand_avg if abs(rand_avg) > 1e-9 else 0.0
        # suspicious: entry 평균이 random 의 5배 이상 + entry 평균이 +5% 이상
        suspicious = (abs(ratio) > 5 and abs(entry_avg) > 0.05) or abs(entry_avg) > 0.10
        return {
            "n_entries": int(len(valid_entries)),
            "entry_forward_5d_avg": round(entry_avg, 4),
            "random_forward_5d_avg": round(rand_avg, 4),
            "ratio": round(ratio, 2),
            "suspicious": bool(suspicious),
        }

    def __len__(self) -> int:
        return len(self.entry_expr)

    def __repr__(self) -> str:
        n = len(self.entry_expr)
        n_entry = int(np.sum(self.entry_expr))
        n_exit = int(np.sum(self.exit_expr))
        sz = self.sizing["method"] if self.sizing else "equal"
        st = self.stop["method"] if self.stop else "none"
        return f"Rule(len={n}, entries={n_entry}, exits={n_exit}, sizing={sz}, stop={st})"


@dataclass
class _RuleBuilder:
    """Rule 체이닝 빌더 — Rule.entry(...).exit(...) 패턴 sugar."""

    entry: Any

    def exit(self, expr) -> Rule:
        """청산 시그널을 받아 Rule 을 완성한다.

        Parameters
        ----------
        expr : array-like
            boolean numpy array (True = 청산 시그널).

        Returns
        -------
        Rule
            entry + exit 가 결합된 완성 Rule.

        Example:
            >>> Rule.entry(rsi < 30).exit(rsi > 70)
            Rule(...)

        Requires:
            expr 와 entry 길이 일치.

        Raises:
            ValueError — 길이 mismatch.
        """
        return Rule(entry_expr=self.entry, exit_expr=expr)
