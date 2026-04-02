"""guide readiness 단위 테스트 — ReadyStatus, ReadinessResult, checkers."""

import pytest

pytestmark = pytest.mark.unit

from dartlab.guide.readiness import (
    ReadinessIssue,
    ReadinessResult,
    ReadyStatus,
    _checkAi,
    _checkMcp,
    _checkServer,
    listFeatures,
)

# ══════════════════════════════════════
# ReadyStatus enum
# ══════════════════════════════════════


class TestReadyStatus:
    def test_values(self):
        assert ReadyStatus.READY.value == "ready"
        assert ReadyStatus.PARTIAL.value == "partial"
        assert ReadyStatus.NOT_READY.value == "not_ready"
        assert ReadyStatus.UNKNOWN.value == "unknown"

    def test_members(self):
        names = {m.name for m in ReadyStatus}
        assert names == {"READY", "PARTIAL", "NOT_READY", "UNKNOWN"}


# ══════════════════════════════════════
# ReadinessIssue
# ══════════════════════════════════════


class TestReadinessIssue:
    def test_construction(self):
        issue = ReadinessIssue(
            kind="missing_key",
            message="API 키 없음",
            fixAction="dartlab setup",
        )
        assert issue.kind == "missing_key"
        assert issue.message == "API 키 없음"
        assert issue.fixAction == "dartlab setup"
        assert issue.severity == "error"

    def test_custom_severity(self):
        issue = ReadinessIssue(kind="k", message="m", fixAction="f", severity="warning")
        assert issue.severity == "warning"


# ══════════════════════════════════════
# ReadinessResult
# ══════════════════════════════════════


class TestReadinessResult:
    def test_ok_when_ready(self):
        r = ReadinessResult(feature="test", status=ReadyStatus.READY)
        assert r.ok is True

    def test_ok_when_partial(self):
        r = ReadinessResult(feature="test", status=ReadyStatus.PARTIAL)
        assert r.ok is True

    def test_not_ok_when_not_ready(self):
        r = ReadinessResult(feature="test", status=ReadyStatus.NOT_READY)
        assert r.ok is False

    def test_not_ok_when_unknown(self):
        r = ReadinessResult(feature="test", status=ReadyStatus.UNKNOWN)
        assert r.ok is False

    def test_guide_text_ready(self):
        r = ReadinessResult(feature="ai", status=ReadyStatus.READY)
        text = r.guideText()
        assert "사용 가능" in text
        assert "ai" in text

    def test_guide_text_not_ready(self):
        r = ReadinessResult(
            feature="ai",
            status=ReadyStatus.NOT_READY,
            issues=[
                ReadinessIssue(
                    kind="no_provider",
                    message="Provider 없음",
                    fixAction="설치하세요",
                )
            ],
        )
        text = r.guideText()
        assert "사용 불가" in text
        assert "Provider 없음" in text
        assert "설치하세요" in text

    def test_default_empty_issues(self):
        r = ReadinessResult(feature="x", status=ReadyStatus.READY)
        assert r.issues == []
        assert r.context == {}


# ══════════════════════════════════════
# listFeatures
# ══════════════════════════════════════


class TestListFeatures:
    def test_returns_list(self):
        features = listFeatures()
        assert isinstance(features, list)

    def test_built_in_features_registered(self):
        """내장 checker들이 등록되어 있다."""
        features = listFeatures()
        for name in ["data", "ai", "dart_key", "finance", "server", "mcp", "review", "ask"]:
            assert name in features, f"{name} checker가 등록되지 않았다"


# ══════════════════════════════════════
# _checkServer
# ══════════════════════════════════════


class TestCheckServer:
    def test_ready_when_installed(self, monkeypatch):
        """fastapi, uvicorn 모두 설치되면 READY."""

        original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if name in ("fastapi", "uvicorn"):
                return type("module", (), {})()
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)
        result = _checkServer()
        assert result.status == ReadyStatus.READY
        assert result.issues == []

    def test_not_ready_when_missing(self, monkeypatch):
        """fastapi 없으면 NOT_READY."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "fastapi":
                raise ImportError("no fastapi")
            if name == "uvicorn":
                raise ImportError("no uvicorn")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)
        result = _checkServer()
        assert result.status == ReadyStatus.NOT_READY
        assert len(result.issues) >= 1
        assert any("pip install" in i.fixAction for i in result.issues)


# ══════════════════════════════════════
# _checkMcp
# ══════════════════════════════════════


class TestCheckMcp:
    def test_ready_when_installed(self, monkeypatch):
        """mcp 패키지가 있으면 READY."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "mcp":
                return type("module", (), {})()
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)
        result = _checkMcp()
        assert result.status == ReadyStatus.READY

    def test_not_ready_when_missing(self, monkeypatch):
        """mcp 패키지가 없으면 NOT_READY."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "mcp":
                raise ImportError("no mcp")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)
        result = _checkMcp()
        assert result.status == ReadyStatus.NOT_READY
        assert result.issues[0].kind == "missing_mcp"


# ══════════════════════════════════════
# _checkAi
# ══════════════════════════════════════


class TestCheckAi:
    def test_ready_with_provider(self, monkeypatch):
        """provider가 감지되면 READY."""

        # mock the lazy import inside _checkAi
        fake_detect = type("mod", (), {"auto_detect_provider": staticmethod(lambda: "gemini")})()
        monkeypatch.setitem(
            __import__("sys").modules,
            "dartlab.guide.detect",
            fake_detect,
        )
        result = _checkAi()
        assert result.status == ReadyStatus.READY
        assert result.context.get("detected_provider") == "gemini"

    def test_not_ready_no_provider(self, monkeypatch):
        """provider 없으면 NOT_READY."""
        import sys

        fake_detect = type("mod", (), {"auto_detect_provider": staticmethod(lambda: None)})()
        monkeypatch.setitem(sys.modules, "dartlab.guide.detect", fake_detect)

        fake_hints = type("mod", (), {"onKeyRequired": staticmethod(lambda k: "키를 발급받으세요")})()
        monkeypatch.setitem(sys.modules, "dartlab.guide.hints", fake_hints)

        result = _checkAi()
        assert result.status == ReadyStatus.NOT_READY
        assert len(result.issues) == 1
        assert result.issues[0].kind == "no_provider"

    def test_not_ready_import_error(self, monkeypatch):
        """AI 모듈 import 실패 시 NOT_READY."""
        import sys

        # detect 모듈이 없는 상태 시뮬레이션
        monkeypatch.delitem(sys.modules, "dartlab.guide.detect", raising=False)

        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "dartlab.guide.detect":
                raise ImportError("no detect")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)
        result = _checkAi()
        assert result.status == ReadyStatus.NOT_READY
        assert any("pip install" in i.fixAction for i in result.issues)
