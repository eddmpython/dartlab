"""침묵 감시 규칙 자체에 대한 회귀.

일곱 계층 전수 검토가 공통으로 지적한 것이 하나 있었다. 이 가드가 넓은 catch 의
`return <상수>` 한 모양만 보는데, 실제 사고는 대부분 다른 모양이라는 것이다.

임차 갱신 실패를 `renewed = False` 로 삼켜서 일시적 저장소 오류와 소유권 상실이 같은 값이
됐고, 끝난 작업이 이유 없이 버려졌다. 검증기 반복문이 `except: continue` 로 실패를
건너뛰어서 스무 검사가 전부 죽어도 "20개 전부 통과" 가 찍혔다. 예측 실제값 조회 실패를 빈
값으로 채워서 일시적 오류가 영구 오답으로 굳었다.

세 사건 다 예외를 좁게 잡고 있었다. 좁게 잡았다는 것이 원인을 버려도 된다는 뜻은 아니다.

이 파일은 새 두 규칙이 실제로 잡는지, 그리고 원인을 남기면 통과하는지를 고정한다. 가드가
요구하는 것은 흐름 변경이 아니라 기록이라는 성질이 규칙 확장 뒤에도 유지되어야 한다.
"""

from __future__ import annotations

import ast

import pytest

from tests.audit.silentSubstitute import (
    _handlersInsideLoops,
    _isSilentAssign,
    _isSilentLoopSkip,
    _isSilentSubstitute,
)

pytestmark = [pytest.mark.unit]


def _parseOne(source: str) -> tuple[ast.Module, ast.ExceptHandler]:
    """한 번만 파싱해 트리와 handler 를 함께 준다.

    `_handlersInsideLoops` 는 객체 동일성으로 반복문 안쪽을 가린다. 소스를 두 번 파싱하면
    서로 다른 객체가 나와 늘 밖으로 판정된다. 실사용(`_scan`)은 트리 하나를 쓴다.
    """
    tree = ast.parse(source)
    handlers = [node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)]
    assert len(handlers) == 1
    return tree, handlers[0]


def _onlyHandler(source: str) -> ast.ExceptHandler:
    return _parseOne(source)[1]


_ASSIGN_SILENT = """
def renew(store):
    try:
        renewed = store.renew()
    except OSError:
        renewed = False
    return renewed
"""

_ASSIGN_LOGGED = """
def renew(store):
    try:
        renewed = store.renew()
    except OSError as exc:
        log.warning("갱신 실패 (%s)", exc)
        renewed = False
    return renewed
"""

_LOOP_SILENT = """
def check(items):
    results = []
    for item in items:
        try:
            results.append(item.value())
        except ValueError:
            continue
    return results
"""

_LOOP_LOGGED = """
def check(items):
    results = []
    for item in items:
        try:
            results.append(item.value())
        except ValueError as exc:
            log.warning("항목 실패 (%s)", exc)
            continue
    return results
"""

_LOOP_OUTSIDE = """
def check(item):
    try:
        return item.value()
    except ValueError:
        return None
"""


def testConstantAssignmentIsCaught() -> None:
    """실패를 이름에 꽂고 흐름을 이으면 읽는 쪽이 실패를 못 본다."""

    assert _isSilentAssign(_onlyHandler(_ASSIGN_SILENT)) is True


def testLoggedAssignmentPasses() -> None:
    """원인을 남기면 통과한다. 가드는 흐름 변경을 요구하지 않는다."""

    assert _isSilentAssign(_onlyHandler(_ASSIGN_LOGGED)) is False


def testNarrowExceptIsAlsoCaught() -> None:
    """좁게 잡았다는 것이 원인을 버려도 된다는 뜻은 아니다. 위 두 예시가 모두 OSError 다."""

    assert _onlyHandler(_ASSIGN_SILENT).type is not None


def testLoopSkipIsCaught() -> None:
    """모으는 반복문에서 조용히 건너뛰면 결과만 보고 결손을 알 수 없다."""

    tree, handler = _parseOne(_LOOP_SILENT)

    assert _isSilentLoopSkip(handler, _handlersInsideLoops(tree)) is True


def testLoggedLoopSkipPasses() -> None:
    """건너뛰더라도 이유를 남기면 통과한다."""

    tree, handler = _parseOne(_LOOP_LOGGED)

    assert _isSilentLoopSkip(handler, _handlersInsideLoops(tree)) is False


def testHandlerOutsideALoopIsNotALoopSkip() -> None:
    """반복문 밖 handler 까지 이 규칙으로 잡으면 오탐이 된다."""

    tree, handler = _parseOne(_LOOP_OUTSIDE)

    assert _isSilentLoopSkip(handler, _handlersInsideLoops(tree)) is False


def testOriginalReturnRuleStillWorks() -> None:
    """규칙을 넓히면서 원래 잡던 것을 놓치면 안 된다."""

    source = """
def load(path):
    try:
        return read(path)
    except Exception:
        return {}
"""

    assert _isSilentSubstitute(_onlyHandler(source)) is True


def testNonConstantAssignmentIsNotFlagged() -> None:
    """실패 경로에서 실제 대체 계산을 하는 것은 침묵이 아니다."""

    source = """
def load(path):
    try:
        value = read(path)
    except OSError:
        value = computeFallback(path)
    return value
"""

    assert _isSilentAssign(_onlyHandler(source)) is False


def testReraisingIsNotSilent() -> None:
    """다시 던지는 것은 원인을 남기는 것이다."""

    source = """
def load(path):
    try:
        value = read(path)
    except OSError:
        raise
"""

    assert _isSilentAssign(_onlyHandler(source)) is False
