"""dartlab 통합 진행 표시 SSOT — rich 기반, 환경 자동 감지.

흩어진 진행 표시(``logger.getProgress`` · ``gather/edgar/bulk._RichBar`` ·
``gather/edgar/docs/fetch._makeProgress`` · ``messaging.progress``)를 대체하는 단일
facade. tqdm/alive-progress 는 도입하지 않는다 — rich(선언 의존성, pyproject) 위에
tqdm 의 강점(어디서나 표시·iterable 한 줄 감싸기)을 흡수한다.

환경 자동 감지
    - terminal (stdout.isatty)        : rich 라이브 바
    - jupyter (rich Console.is_jupyter): rich jupyter 렌더
    - marimo (stdout=marimo.*)         : rich + force_terminal (라이브 ANSI; 런타임 실측)
    - 그 외 (CI·파이프·테스트)          : 무음 — no-op. ANSI/출력 오염 0.

공개 API
    - ``track(iterable, desc=..., detailed=...)`` : tqdm 식 iterable 감싸기 (간단).
    - ``with progressBar(total, desc=..., detailed=...) as p`` : 컨트롤러
      (``advance`` / ``update(item=...)`` / ``subtask``) — 오래 걸리는 작업의 상세 진행.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from typing import Any

from .logger import getConsole

__all__ = ["track", "progressBar"]


def _detectEnv() -> str:
    """현재 출력 환경 판정 — 'marimo' | 'jupyter' | 'terminal' | 'silent'."""
    if type(sys.stdout).__module__.startswith("marimo"):
        return "marimo"
    console = getConsole()
    if getattr(console, "is_jupyter", False):
        return "jupyter"
    if getattr(console, "is_terminal", False):
        return "terminal"
    return "silent"


def _consoleFor(env: str):
    """환경별 rich Console — 마리모는 force_terminal(라이브 ANSI), 그 외 SSOT getConsole."""
    if env == "marimo":
        from rich.console import Console

        return Console(force_terminal=True)
    return getConsole()


def _newProgress(detailed: bool):
    """rich Progress 생성 — 무음 환경이면 None. detailed 면 상세 컬럼(스피너·%·경과·ETA·현재항목)."""
    env = _detectEnv()
    if env == "silent":
        return None
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )

    console = _consoleFor(env)
    if detailed:
        columns = (
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            TextColumn("{task.fields[item]}"),
        )
    else:
        columns = (
            TextColumn("[cyan]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
        )
    return Progress(*columns, console=console, transient=False)


class _Tracker:
    """진행 컨트롤러 — advance/update/subtask. 무음 환경(progress=None)이면 전부 no-op."""

    def __init__(self, progress: Any, taskId: Any) -> None:
        self._p = progress
        self._t = taskId

    def advance(self, n: int = 1) -> None:
        """진행을 n 만큼 전진."""
        if self._p is not None:
            self._p.advance(self._t, n)

    def update(self, *, item: Any = None, advance: int = 0) -> None:
        """현재 항목(detailed 컬럼) 갱신 + 선택적 전진."""
        if self._p is None:
            return
        kwargs: dict[str, Any] = {}
        if advance:
            kwargs["advance"] = advance
        if item is not None:
            kwargs["item"] = str(item)
        if kwargs:
            self._p.update(self._t, **kwargs)

    def subtask(self, label: str, total: int | None) -> _Tracker:
        """중첩 서브태스크 추가 — 같은 진행 표시에 한 줄 더(예: 테마 안의 종목)."""
        if self._p is None:
            return _Tracker(None, None)
        taskId = self._p.add_task(label, total=total, item="")
        return _Tracker(self._p, taskId)


@contextmanager
def progressBar(total: int | None, *, desc: str = "진행", detailed: bool = False) -> Iterator[_Tracker]:
    """진행 표시 컨텍스트 — 컨트롤러(_Tracker) 를 yield. 무음 환경이면 no-op 컨트롤러.

    Sig: ``with progressBar(total, *, desc="진행", detailed=False) as p``

    Capabilities: 환경 자동 감지 → rich 라이브 바(터미널/Jupyter/마리모) 또는 무음(CI/파이프/테스트).
    Args:
        total: 전체 스텝 수 (None 이면 불확정 — 스피너만).
        desc: 표시 라벨.
        detailed: True 면 스피너·%·경과·ETA·현재항목 컬럼(오래 걸리는 작업용).
    Returns:
        _Tracker — ``advance(n)`` / ``update(item=...)`` / ``subtask(label, total)``.
    Raises:
        없음 — rich 미가용/무음이면 no-op.
    Example::

        with progressBar(280, desc="테마 수집", detailed=True) as p:
            for t in themes:
                p.update(item=t.name)
                ...  # work
                p.advance()
    """
    prog = _newProgress(detailed)
    if prog is None:
        yield _Tracker(None, None)
        return
    with prog:
        taskId = prog.add_task(desc, total=total, item="")
        yield _Tracker(prog, taskId)


def track(iterable: Iterable, *, desc: str = "진행", total: int | None = None, detailed: bool = False) -> Iterator:
    """iterable 을 진행 표시로 감싼다 (tqdm 식) — 각 항목 소비 후 자동 전진.

    Sig: ``for x in track(iterable, *, desc="진행", total=None, detailed=False)``

    Capabilities: 동기/비동기 루프 공통 — 본문에서 ``await`` 해도 됨(track 은 sync iterable 만 감쌈).
    Args:
        iterable: 순회 대상. total 미지정 시 ``len()`` 시도.
        desc: 표시 라벨.
        total: 전체 수 (len 불가 iterable 용 명시).
        detailed: 상세 컬럼 여부.
    Returns:
        원본 항목을 그대로 yield 하는 generator.
    Raises:
        없음.
    Example::

        for code in track(codes, desc="수집"):
            fetch(code)
        # 비동기 루프도 가능 — 본문에서 await
        for no, name in track(selected, desc="테마"):
            await fetchStocks(no)
    """
    if total is None:
        try:
            total = len(iterable)  # type: ignore[arg-type]
        except TypeError:
            total = None
    with progressBar(total, desc=desc, detailed=detailed) as p:
        for item in iterable:
            yield item
            p.advance()
