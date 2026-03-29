"""Deprecation warning 체계.

사용법:
    from dartlab.core.deprecation import deprecated

    @deprecated("0.8.0", alternative="show(topic)")
    def oldMethod(self):
        ...

    # 또는 함수 내부에서 직접 호출
    warnDeprecated("oldFunc", "0.9.0", alternative="newFunc()")
"""

from __future__ import annotations

import functools
import warnings


class DartlabDeprecationWarning(FutureWarning):
    """dartlab API deprecation 경고.

    FutureWarning 하위 클래스이므로 기본적으로 사용자에게 표시된다.
    (DeprecationWarning은 개발자용으로 기본 숨김)
    """


def warnDeprecated(
    name: str,
    removeVersion: str,
    *,
    alternative: str | None = None,
) -> None:
    """deprecation 경고 발생."""
    msg = f"'{name}'은 {removeVersion}에서 제거 예정입니다."
    if alternative:
        msg += f" 대신 '{alternative}'을 사용하세요."
    warnings.warn(msg, DartlabDeprecationWarning, stacklevel=3)


def deprecated(
    removeVersion: str,
    *,
    alternative: str | None = None,
):
    """deprecation 데코레이터.

    Args:
        removeVersion: 제거 예정 버전 (예: "0.9.0").
        alternative: 대체 API 안내 문자열.

    Example:
        @deprecated("0.9.0", alternative="show('배당')")
        def dividend(self): ...
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            warnDeprecated(fn.__qualname__, removeVersion, alternative=alternative)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
