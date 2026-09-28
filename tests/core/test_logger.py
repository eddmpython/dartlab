"""core/logger SSOT 단위 테스트.

dartlab.core.logger 가 output 채널 SSOT — getConsole/getProgress/installRichHandler
가 외부 logger 흡수와 HF tqdm 차단까지 한 곳에서 처리하는지 회귀 보호.
"""

from __future__ import annotations

import logging
import os

import pytest

from dartlab.core import logger as _loggerMod

pytestmark = pytest.mark.unit


@pytest.fixture
def _resetRichInstalled():
    """installRichHandler idempotent 플래그 초기화 — 테스트 간 격리.

    dartlab root 와 외부 logger (huggingface_hub, urllib3 등) 의 handlers /
    propagate / level 까지 원복해 RichHandler 가 후속 테스트의 stdout 으로 새는
    회귀 (test_emit_prints_hint) 를 차단한다.
    """
    saved = _loggerMod._RICH_INSTALLED
    targets = ("dartlab", *_loggerMod._EXTERNAL_LOGGERS)
    snapshots = {
        name: (
            logging.getLogger(name).handlers[:],
            logging.getLogger(name).propagate,
            logging.getLogger(name).level,
        )
        for name in targets
    }
    _loggerMod._RICH_INSTALLED = False
    yield
    _loggerMod._RICH_INSTALLED = saved
    for name, (handlers, propagate, level) in snapshots.items():
        lg = logging.getLogger(name)
        lg.handlers = handlers
        lg.propagate = propagate
        lg.setLevel(level)


def test_getConsole_returnsSingleton() -> None:
    """getConsole 은 같은 Console 인스턴스를 반복 반환한다."""
    c1 = _loggerMod.getConsole()
    c2 = _loggerMod.getConsole()
    assert c1 is c2


def test_getErrConsole_isStderr() -> None:
    """getErrConsole 은 stderr 전용 Console 을 반환한다."""
    c = _loggerMod.getErrConsole()
    assert c.stderr is True


def test_getProgress_returnsSingleton() -> None:
    """getProgress 는 같은 Progress 인스턴스를 반복 반환한다."""
    p1 = _loggerMod.getProgress()
    p2 = _loggerMod.getProgress()
    assert p1 is p2


def test_getProgress_sharesConsoleWithGetConsole() -> None:
    """Progress 의 Console 은 getConsole() 과 동일 인스턴스 — Live 와 충돌 방지."""
    p = _loggerMod.getProgress()
    assert p.console is _loggerMod.getConsole()


def test_installRichHandler_idempotent(_resetRichInstalled) -> None:
    """installRichHandler 는 여러 번 호출돼도 handler 가 중복 부착되지 않는다."""
    _loggerMod.installRichHandler()
    firstHandlers = logging.getLogger("dartlab").handlers[:]
    _loggerMod.installRichHandler()
    secondHandlers = logging.getLogger("dartlab").handlers[:]
    assert firstHandlers == secondHandlers


def test_installRichHandler_replacesDartlabHandler(_resetRichInstalled) -> None:
    """installRichHandler 호출 후 dartlab root logger 는 RichHandler 단일 handler."""
    from rich.logging import RichHandler

    _loggerMod.installRichHandler()
    handlers = logging.getLogger("dartlab").handlers
    assert len(handlers) == 1
    assert isinstance(handlers[0], RichHandler)


def test_installRichHandler_absorbsExternalLoggers(_resetRichInstalled) -> None:
    """외부 라이브러리 logger (huggingface_hub 등) 도 RichHandler 가 부착된다."""
    from rich.logging import RichHandler

    _loggerMod.installRichHandler()
    for extName in _loggerMod._EXTERNAL_LOGGERS:
        extLog = logging.getLogger(extName)
        assert extLog.propagate is False, f"{extName}: propagate 차단 안 됨"
        assert any(isinstance(h, RichHandler) for h in extLog.handlers), f"{extName}: RichHandler 부착 안 됨"


def test_installRichHandler_disablesHfProgressEnv(_resetRichInstalled) -> None:
    """installRichHandler 는 HF_HUB_DISABLE_PROGRESS_BARS 환경변수를 설정한다."""
    saved = os.environ.pop("HF_HUB_DISABLE_PROGRESS_BARS", None)
    try:
        _loggerMod.installRichHandler()
        assert os.environ.get("HF_HUB_DISABLE_PROGRESS_BARS") == "1"
    finally:
        if saved is None:
            os.environ.pop("HF_HUB_DISABLE_PROGRESS_BARS", None)
        else:
            os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = saved


def test_getLogger_returnsDartlabNamespaced() -> None:
    """getLogger 는 dartlab.* 네임스페이스 logger 를 돌려준다 (기존 행동 유지)."""
    log = _loggerMod.getLogger("example")
    assert log.name == "dartlab.example"


def test_cli_output_reExports_getConsole() -> None:
    """cli/services/output.getConsole 은 core.logger.getConsole 과 동일 인스턴스."""
    from dartlab.cli.services.output import getConsole as cliGetConsole

    assert cliGetConsole() is _loggerMod.getConsole()


def test_logSafe_neutralizesLineBreaksAndControlChars() -> None:
    """CR/LF·ANSI escape·U+2028 이 공백으로 바뀌어 가짜 로그 줄을 만들 수 없다."""
    assert _loggerMod.logSafe("005930\r\nFAKE\x1b[31m\u2028x") == "005930 FAKE [31m x"


def test_logSafe_neutralizesLoneSeparators() -> None:
    """단독 CR·TAB·NEL·DEL·U+2029 도 공백으로 바뀐다."""
    assert _loggerMod.logSafe("a\rb\tc\x85d\x7fe\u2029f") == "a b c d e f"


def test_logSafe_truncatesToLimit() -> None:
    """기본 200자, limit 지정 시 그 길이로 자른다."""
    assert len(_loggerMod.logSafe("a" * 500)) == 200
    assert _loggerMod.logSafe("abcdef", limit=3) == "abc"


def test_logSafe_stringifiesNonStr() -> None:
    """None·숫자·예외 객체도 str() 로 바꿔 한 줄 값으로 만든다."""
    assert _loggerMod.logSafe(None) == "None"
    assert _loggerMod.logSafe(5930) == "5930"
    assert _loggerMod.logSafe(ValueError("line1\nline2")) == "line1 line2"


def test_logSafe_keepsRecordOnSingleLine(caplog: pytest.LogCaptureFixture) -> None:
    """logSafe 로 감싼 값은 로그 레코드를 한 줄로 유지한다 (위조 줄 삽입 차단)."""
    log = _loggerMod.getLogger("test_logSafe")
    with caplog.at_level(logging.INFO, logger="dartlab.test_logSafe"):
        log.info("조회 실패: %s", _loggerMod.logSafe("005930\n[dartlab] 관리자 로그인 성공"))
    messages = [r.getMessage() for r in caplog.records if r.name == "dartlab.test_logSafe"]
    assert messages == ["조회 실패: 005930 [dartlab] 관리자 로그인 성공"]
