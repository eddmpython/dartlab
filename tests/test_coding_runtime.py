"""coding_runtime 모듈 테스트."""

import pytest

pytestmark = pytest.mark.unit

from dartlab.ai.tools.coding import CodexCodingBackend, create_coding_runtime


def test_create_coding_runtime_registers_default_backends():
    runtime = create_coding_runtime(name="test-runtime")
    assert runtime.name == "test-runtime"
    names = runtime.list_backend_names()
    assert "codex" in names
    assert "local_python" in names


def test_codex_backend_inspect(monkeypatch):
    from dartlab.ai.providers.support import codex_cli

    monkeypatch.setattr(
        codex_cli,
        "inspect_codex_cli",
        lambda: {
            "installed": True,
            "authenticated": True,
            "configuredModel": "gpt-5.4",
            "version": "0.99.0",
            "sandboxModes": ["read-only", "workspace-write"],
        },
    )
    backend = CodexCodingBackend()
    info = backend.inspect()
    assert info["available"] is True
    assert info["configuredModel"] == "gpt-5.4"
    assert info["supportsWorkspaceWrite"] is True


def test_codex_backend_run_task_falls_back_to_supported_sandbox(monkeypatch):
    from dartlab.ai.providers.support import codex_cli

    monkeypatch.setattr(
        codex_cli,
        "inspect_codex_cli",
        lambda: {
            "installed": True,
            "authenticated": True,
            "configuredModel": "gpt-5.4",
            "version": "0.99.0",
            "sandboxModes": ["read-only"],
        },
    )
    monkeypatch.setattr(
        codex_cli,
        "run_codex_exec",
        lambda prompt, model=None, sandbox="read-only", timeout=300: (
            f"done: {prompt}",
            {"total_tokens": 42},
        ),
    )

    backend = CodexCodingBackend()
    result = backend.run_task("테스트", sandbox="danger-full-access", timeout_seconds=120)
    assert result.answer == "done: 테스트"
    assert result.sandbox == "read-only"
    assert result.usage == {"total_tokens": 42}


def test_coding_runtime_unknown_backend():
    runtime = create_coding_runtime(include_defaults=False)
    try:
        runtime.get_backend("missing")
    except KeyError as error:
        assert "등록되지 않은 coding backend" in str(error)
    else:
        raise AssertionError("KeyError가 발생해야 합니다.")
