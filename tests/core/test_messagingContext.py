"""사용자 메시지 runtime context의 credential 실패 계약."""

from __future__ import annotations

import builtins
from types import SimpleNamespace

import pytest

from dartlab.core.messagingContext import Context

pytestmark = pytest.mark.unit


def test_hasDartKey_missingProviderIsFalse(monkeypatch) -> None:
    """정상적인 provider 미등록 상태만 False로 표현한다."""
    monkeypatch.setattr("dartlab.core.credentials.getCredentialProvider", lambda _name: None)

    assert Context().hasDartKey is False


def test_hasDartKey_internalImportFailurePropagates(monkeypatch) -> None:
    """필수 core import 실패를 key 미설정으로 캐시하지 않는다."""
    realImport = builtins.__import__

    def failCredentials(name, *args, **kwargs):
        if name == "dartlab.core.credentials":
            raise ImportError("simulated credentials import failure")
        return realImport(name, *args, **kwargs)

    context = Context()
    monkeypatch.setattr(builtins, "__import__", failCredentials)

    with pytest.raises(ImportError, match="simulated credentials import failure"):
        _ = context.hasDartKey
    assert context._dart_key is None


def test_hasDartKey_providerFailurePropagatesWithoutCache(monkeypatch) -> None:
    """provider 저장소 오류를 키 미설정으로 축약하거나 cache하지 않는다."""

    class Provider:
        def check(self):
            raise RuntimeError("simulated provider failure")

    monkeypatch.setattr("dartlab.core.credentials.getCredentialProvider", lambda _name: Provider())
    context = Context()

    with pytest.raises(RuntimeError, match="simulated provider failure"):
        _ = context.hasDartKey
    assert context._dart_key is None


def test_hasDartKey_successfulResultIsCached(monkeypatch) -> None:
    """성공적으로 계산한 credential 상태만 세션 cache에 저장한다."""
    checks = 0

    class Provider:
        def check(self):
            nonlocal checks
            checks += 1
            return SimpleNamespace(configured=True)

    monkeypatch.setattr("dartlab.core.credentials.getCredentialProvider", lambda _name: Provider())
    context = Context()

    assert context.hasDartKey is True
    assert context.hasDartKey is True
    assert checks == 1
