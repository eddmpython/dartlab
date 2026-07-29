"""dartlab 중앙 로거.

라이브러리 내부 진행/진단 메시지는 전부 ``logging`` 경유 — 사용자가 log 레벨·핸들러
를 자유롭게 제어. CLI 전용 사용자 출력 (cli/commands/*) 은 여전히 ``print`` 유지.

기본 동작::

    import dartlab  # stderr 에 INFO 레벨 dartlab 메시지 자동 출력

Silence (자동화/CI 에서)::

    import logging
    logging.getLogger("dartlab").setLevel(logging.WARNING)

Verbose::

    logging.getLogger("dartlab").setLevel(logging.DEBUG)

사용 (라이브러리 내부 코드)::

    from dartlab.core.logger import getLogger
    log = getLogger(__name__)
    log.info("다운로드 시작: %s", label)
    log.warning("재시도 %d/%d", attempt, maxRetries)
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console
    from rich.progress import Progress

_ROOT_NAME = "dartlab"
_DEFAULT_CONFIGURED = False
_RICH_INSTALLED = False
_console: Console | None = None
_errConsole: Console | None = None
_progress: Progress | None = None
# installRichHandler 가 외부 logger 까지 흡수할 대상 — propagate=False + 같은 handler.
_EXTERNAL_LOGGERS = ("huggingface_hub", "urllib3", "httpx", "httpcore", "filelock")


def _ensureUtf8Stream() -> None:
    """Windows 기본 stdout/stderr cp949 인코딩을 UTF-8 로 재구성 (가능한 경우).

    한글·이모지가 포함된 로그·가이드 출력이 Windows 터미널에서 ``UnicodeEncodeError``
    없이 표시되도록 한다. TextIOWrapper.reconfigure 를 지원하지 않는 환경
    (Python 3.6 이하, 이미 다른 wrapper) 에서는 조용히 스킵.
    """
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            enc = (getattr(stream, "encoding", "") or "").lower()
            reconfigure = getattr(stream, "reconfigure", None)
            if enc and enc not in {"utf-8", "utf8"} and callable(reconfigure):
                reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, OSError, ValueError):
            # 리다이렉트된 스트림·서브프로세스 파이프 등 reconfigure 불가 — 무시.
            pass


def _ensureDefaultHandler() -> None:
    """root ``dartlab`` 로거에 기본 stderr 핸들러 부착 (최초 1회).

    사용자가 이미 핸들러를 붙였으면 아무것도 하지 않는다 (idempotent).
    propagate=True 유지 — pytest caplog / 사용자 root logger 훅 이 dartlab
    레코드를 볼 수 있도록. 중복 출력은 root 가 별도 핸들러 설정했을 때만
    발생하며, 그 경우 사용자가 ``dartlab`` 핸들러를 따로 관리해야 한다.
    """
    global _DEFAULT_CONFIGURED
    if _DEFAULT_CONFIGURED:
        return
    _ensureUtf8Stream()
    root = logging.getLogger(_ROOT_NAME)
    if root.handlers:
        _DEFAULT_CONFIGURED = True
        return

    handler = logging.StreamHandler(sys.stderr)
    # 간결한 포맷 — 메시지 본문에 [dartlab] 프리픽스·레벨 이미 녹아있음
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    # 사용자가 이미 setLevel 호출했으면 (NOTSET=0 아님) 존중. 아니면 INFO.
    if root.level == logging.NOTSET:
        root.setLevel(logging.INFO)
    # propagate=True (default) 유지 — caplog 가 dartlab.* 레코드를 캡처 가능.
    _DEFAULT_CONFIGURED = True


def getLogger(name: str | None = None) -> logging.Logger:
    """dartlab 네임스페이스 로거.

    Capabilities:
        dartlab root logger의 기본 stderr handler를 보장하고 모듈별 logger를 반환한다.
    AIContext:
        다운로드, provider fetch, Guard 실행 등 라이브러리 내부 진단 메시지를 사용자
        설정 가능한 logging 흐름에 남기는 표준 entry point다.
    Guide:
        라이브러리 코드는 print 대신 ``getLogger(__name__)``를 사용한다. CLI 사용자
        출력만 별도 print를 허용한다.
    When:
        모듈 로거가 필요하거나 Windows 터미널 한글 로그 인코딩을 안전하게 맞춰야 할 때.
    How:
        _ensureDefaultHandler를 먼저 호출한 뒤, name이 dartlab prefix를 갖는지에 따라
        root 또는 하위 logger 이름을 만든다.

    Parameters
    ----------
    name : str | None
        모듈명 (보통 ``__name__``). None 이면 root ``dartlab`` 로거.

    Returns
    -------
    logging.Logger
        ``dartlab`` 또는 ``dartlab.<name>`` 로거. 기본 핸들러 부착됨.
    Requires:
        표준 logging 모듈과 sys.stderr가 사용 가능해야 한다.
    Raises:
        없음. stream 재구성 실패는 내부에서 무시한다.
    Example:
        >>> log = getLogger("example")
        >>> log.name
        'dartlab.example'
    SeeAlso:
        _ensureDefaultHandler: root logger handler 초기화.
        _ensureUtf8Stream: Windows UTF-8 stream 보정.
    """
    _ensureDefaultHandler()
    if name is None or name == _ROOT_NAME:
        return logging.getLogger(_ROOT_NAME)
    if name.startswith(_ROOT_NAME + "."):
        return logging.getLogger(name)
    # __name__ 이 "dartlab.providers.dart.company" 같이 완전 경로인 경우
    if name.startswith(_ROOT_NAME):
        return logging.getLogger(name)
    return logging.getLogger(f"{_ROOT_NAME}.{name}")


# ── 출력 채널 SSOT (rich Console + Progress) ──────────────


def getConsole() -> Console:
    """공용 rich Console (stdout) — 모든 CLI/Progress/Live 가 공유."""
    global _console
    if _console is None:
        from rich.console import Console as _Console

        _console = _Console()
    return _console


def getErrConsole() -> Console:
    """공용 rich Console (stderr) — 오류·경고 전용."""
    global _errConsole
    if _errConsole is None:
        from rich.console import Console as _Console

        _errConsole = _Console(stderr=True)
    return _errConsole


def getProgress() -> Progress:
    """공용 rich.Progress singleton — 다운로드/수집 진행 바.

    같은 Console 을 공유하여 Live/Progress 가 동일 frame buffer 위에서
    경합 없이 갱신된다. 호출처는 ``with getProgress() as p:`` 형태로 사용.
    """
    global _progress
    if _progress is None:
        from rich.progress import BarColumn, MofNCompleteColumn, TextColumn, TimeRemainingColumn
        from rich.progress import Progress as _Progress

        _progress = _Progress(
            TextColumn("[cyan]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=getConsole(),
            transient=False,
        )
    return _progress


def installRichHandler(*, level: int = logging.INFO) -> None:
    """CLI 부트스트랩 — dartlab + 외부 로거를 rich Console 로 흡수.

    Capabilities:
        dartlab root logger 와 외부 라이브러리 logger 의 handler 를 RichHandler
        로 교체하고, huggingface_hub 의 내장 tqdm 진행률 바를 차단한다.
    Args:
        level: dartlab root logger 의 기본 레벨 (외부 로거는 WARNING 고정).
    Example:
        >>> from dartlab.core.logger import installRichHandler
        >>> installRichHandler()  # idempotent
    Returns:
        None. 호출 시 전역 _RICH_INSTALLED 플래그가 True 로 고정된다.
    Guide:
        ``dartlab.cli.main.main`` 진입 직후 1 회만 호출. import 만 한 노트북
        사용자는 호출하지 않으므로 기본 stderr handler + HF 본래 tqdm 그대로.
    SeeAlso:
        getConsole · getProgress · getLogger.
    Requires:
        rich 라이브러리. huggingface_hub 는 optional.
    AIContext:
        4 갈래 출력 채널을 한 Console 로 모으는 SSOT 진입점.
    """
    global _RICH_INSTALLED
    if _RICH_INSTALLED:
        return
    _RICH_INSTALLED = True

    from rich.logging import RichHandler

    handler = RichHandler(
        console=getConsole(),
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        show_time=False,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))

    # (1) dartlab root logger — 기존 stderr StreamHandler 교체.
    _ensureUtf8Stream()
    root = logging.getLogger(_ROOT_NAME)
    root.handlers = [handler]
    if root.level == logging.NOTSET:
        root.setLevel(level)

    # (2) huggingface_hub 내장 tqdm 차단 — 외부 logger 부착 *전* 에 호출해
    # huggingface_hub.utils 의 self-attach (StreamHandler 추가) 가 먼저 끝나도록 한다.
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    try:
        from huggingface_hub.utils.tqdm import disable_progress_bars
    except ModuleNotFoundError as exc:
        if not (exc.name or "").startswith("huggingface_hub"):
            raise
    else:
        disable_progress_bars()

    # (3) 외부 로거 — import 없이 handler를 먼저 부착한다. 대부분의 라이브러리는
    # handler가 이미 있으면 자체 StreamHandler를 추가하지 않으므로 cold import 비용과
    # 선택 의존성 오류를 만들지 않으면서 중복 출력을 막는다.
    for extName in _EXTERNAL_LOGGERS:
        extLog = logging.getLogger(extName)
        extLog.handlers = [handler]
        extLog.propagate = False
        extLog.setLevel(logging.WARNING)


# ── Structured event log (T1-1, 운영 관측성 KPI) ──────────────


_LEVEL_MAP: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "warn": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def logEvent(level: int | str, event: str, /, **fields: object) -> None:
    """Structured event log — extra dict 강제 entry point.

    Capabilities:
        snake_case event name + 구조화된 key/value 필드를 logger.log 의 extra=
        로 전달. metrics workflow 가 grep 으로 event/field 추출 + 시계열 산출.
    Args:
        level: int (logging.INFO 등) 또는 str ("info", "warn", "error" 등).
        event: snake_case event 식별자 (예: "company_show_start", "scan_complete").
        **fields: 구조화 데이터. JSON 직렬화 가능 값만 (str/int/float/bool/None).
    Example:
        >>> from dartlab.core.logger import logEvent
        >>> logEvent("info", "company_show_start", code="005930", source="dart")
        >>> logEvent("warning", "scan_memory_high", peak_mb=1900, threshold_mb=1800)
    Returns:
        None.
    Guide:
        새 핵심 흐름 진입/탈출/메트릭은 plain logger.info 대신 logEvent. 기존
        logger.info(...) 호출은 점진 마이그레이션 (T1-1 트랙, 50+ call site).
    SeeAlso:
        getLogger: 표준 logging.Logger 반환.
        withMemoryBudget: 함수 반환 시점 RSS delta 검증.
        OomTripwire: 절대 RSS background 감시.
    Requires:
        없음. logging 표준 모듈만.
    Raises:
        ValueError: 잘못된 level 문자열.
    AIContext:
        Observability SLO (T1-4) 측정 + metrics workflow (T1-2) 산출의 단일
        진입점. 본 API 사용 비율 ≥ 90% 가 운영 점수 (KPI F.1) 의 가장 큰
        가중 (40%).
    """
    if isinstance(level, str):
        levelInt = _LEVEL_MAP.get(level.lower())
        if levelInt is None:
            raise ValueError(f"unknown level: {level!r}")
    else:
        levelInt = int(level)

    _ensureDefaultHandler()
    log = logging.getLogger(_ROOT_NAME)
    # event 자체를 message 본문으로, fields 는 extra 로 전달
    # → 표준 logging.Formatter 는 message 만 출력, JSON formatter 는 extra 도 직렬화.
    log.log(levelInt, event, extra={"event": event, "fields": fields} if fields else {"event": event})
