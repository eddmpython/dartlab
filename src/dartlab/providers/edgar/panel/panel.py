"""EDGAR ``Panel`` facade — DART ``Panel`` mirror with US defaults.

EDGAR 는 DART 와 같은 panel read/backbone 을 쓰되 공개 진입점의 기본 시장만 US 다.
``from dartlab.providers.edgar.panel import Panel; Panel("AAPL")`` 이 바로
``data/edgar/panel/AAPL.parquet`` 를 읽고, 소문자 재무 키는 같은 panel row payload 에서
native 로 분해한다. 대문자 finance/report 위임은 ``Company.panel`` facade 가 주입한다.
"""

from __future__ import annotations

from typing import Any

from dartlab.providers.dart.panel.panel import Panel as _DartPanel


def _panelCode(code: str, marketNs: str) -> str:
    """EDGAR ticker 는 build 저장 규칙대로 대문자 정규화."""
    return code.upper() if marketNs == "us" else code


class Panel(_DartPanel):
    """한 회사 EDGAR 공시 수평화 wide — DART ``Panel`` 과 같은 표면, US 기본."""

    _showFn: Any
    _strongFn: Any

    def __init__(
        self,
        code: str,
        *,
        marketNs: str = "us",
        periods: list[str] | None = None,
        tag: bool = True,
    ) -> None:
        panelCode = _panelCode(code, marketNs)
        super().__init__(panelCode, marketNs=marketNs, periods=periods, tag=tag)
        if marketNs == "us":
            from dartlab.providers.edgar.panel.native import readNative

            self._nativeFn = lambda statement, freq, scope, periods: readNative(
                panelCode,
                statement=statement,
                freq=freq,
                scope=scope,
                periods=periods,
            )


__all__ = ["Panel"]
