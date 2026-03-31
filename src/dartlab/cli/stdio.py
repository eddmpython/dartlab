"""`dartlab chat --stdio` -- JSON Lines protocol for VSCode extension.

stdin: JSON line requests
stdout: JSON line events
Claude Code / Codex pattern: child process spawn + stdio.

Protocol:
    -> {"id":"1","type":"ask","question":"000660 실적","company":"000660"}
    <- {"id":"1","event":"meta","data":{"company":"SK하이닉스","stockCode":"000660"}}
    <- {"id":"1","event":"chunk","data":{"text":"..."}}
    <- {"id":"1","event":"done","data":{}}
    -> {"type":"status"}
    <- {"event":"status","data":{"provider":"oauth-codex","model":"gpt-5.3","ready":true}}
    -> {"type":"ping"}
    <- {"event":"pong","data":{}}
    -> {"type":"setProvider","provider":"gemini","model":"gemini-2.5-flash"}
    <- {"event":"providerChanged","data":{"provider":"gemini","model":"gemini-2.5-flash"}}
    -> {"type":"listTemplates"}
    <- {"event":"templates","data":{"templates":[{"name":"가치투자","description":"...","source":"builtin"}]}}
    -> {"type":"ask","question":"분석","modules":["가치투자","리스크점검"]}
    -> {"type":"exit"}
"""

from __future__ import annotations

import json
import sys
from typing import Any

# Session state
_sessionProvider: str | None = None
_sessionModel: str | None = None


def _emit(obj: dict[str, Any]) -> None:
    """Write one JSON line to stdout."""
    try:
        line = json.dumps(obj, ensure_ascii=False)
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Surrogate 등 인코딩 문제 시 ensure_ascii=True로 fallback
        line = json.dumps(obj, ensure_ascii=True)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def _handleAsk(msg: dict[str, Any]) -> None:
    """Process ask message -- stream core.analyze() events as JSON lines."""
    from dartlab.ai.runtime.core import analyze

    reqId = msg.get("id", "")
    question = msg.get("question", "")
    company = msg.get("company")
    history = msg.get("history")
    provider = msg.get("provider") or _sessionProvider
    model = msg.get("model") or _sessionModel

    if not question:
        _emit({"id": reqId, "event": "error", "data": {"error": "No question provided"}})
        return

    # Resolve company -- from explicit field, or auto-detect from question
    c = None
    company_hint = company or question
    if company_hint:
        # Try explicit company field first, then auto-detect from question
        import re

        code_match = re.search(r"\b(\d{6})\b", company_hint)
        if code_match:
            try:
                from dartlab import Company
                c = Company(code_match.group(1))
            except (ValueError, OSError):
                pass

        if c is None and company:
            # Try company name search (only if explicit company was given)
            try:
                from dartlab.core.resolve import searchCompany
                results = searchCompany(company)
                if results:
                    from dartlab import Company as C2
                    c = C2(results[0].get("stockCode", results[0].get("corp_code", "")))
            except Exception:
                pass

    kwargs: dict[str, Any] = {}
    if provider:
        kwargs["provider"] = provider
    if model:
        kwargs["model"] = model
    if history:
        kwargs["history"] = history

    # 모듈 프롬프트
    modules = msg.get("modules")  # list[str] | None
    template = msg.get("template")  # str | None (하위호환)
    if modules:
        from dartlab.ai.patterns import get_modules

        _tmplText = get_modules(modules)
        if _tmplText:
            kwargs["_templateText"] = _tmplText
    elif template:
        from dartlab.ai.patterns import get_template

        _tmplText = get_template(template)
        if _tmplText:
            kwargs["_templateText"] = _tmplText

    emittedDone = False
    try:
        for event in analyze(c, question, **kwargs):
            _emit({"id": reqId, "event": event.kind, "data": event.data})
            if event.kind == "done":
                emittedDone = True
    except KeyboardInterrupt:
        _emit({"id": reqId, "event": "error", "data": {"error": "Interrupted"}})
    except Exception as exc:
        _emit({"id": reqId, "event": "error", "data": {"error": str(exc)}})

    if not emittedDone:
        _emit({"id": reqId, "event": "done", "data": {}})


def _handleStatus(_msg: dict[str, Any]) -> None:
    """Return provider status with available providers list."""
    try:
        from dartlab.core.ai.profile import get_profile_manager
        from dartlab.core.ai.providers import _PROVIDERS

        profile = get_profile_manager().load()
        provider = _sessionProvider or profile.default_provider or "none"
        model = _sessionModel or getattr(profile, "model", None) or ""

        providers = []
        for pid, spec in _PROVIDERS.items():
            if not spec.public:
                continue
            providers.append(
                {
                    "id": spec.id,
                    "label": spec.label,
                    "freeTier": spec.freeTierHint or "",
                }
            )

        _emit(
            {
                "event": "status",
                "data": {"provider": provider, "model": model, "ready": True, "providers": providers},
            }
        )
    except Exception as exc:
        _emit(
            {
                "event": "status",
                "data": {"provider": "none", "model": "", "ready": False, "providers": [], "error": str(exc)},
            }
        )


def _handleListTemplates(_msg: dict[str, Any]) -> None:
    """Return available analysis templates/modules."""
    try:
        from dartlab.ai.patterns import list_templates

        templates = list_templates()
        _emit({"event": "templates", "data": {"templates": templates}})
    except Exception as exc:
        _emit({"event": "templates", "data": {"templates": [], "error": str(exc)}})


def _handleSetProvider(msg: dict[str, Any]) -> None:
    """Change provider/model for this session."""
    global _sessionProvider, _sessionModel
    _sessionProvider = msg.get("provider") or _sessionProvider
    _sessionModel = msg.get("model") or _sessionModel
    _emit(
        {
            "event": "providerChanged",
            "data": {"provider": _sessionProvider, "model": _sessionModel},
        }
    )


def run() -> None:
    """stdio REPL loop. Exits on stdin EOF or exit message."""
    import io
    import dartlab

    # Force UTF-8 on Windows cp949 environments
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stdin.encoding and sys.stdin.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")

    dartlab.verbose = False

    _emit({"event": "ready", "data": {"version": _getVersion()}})

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            _emit({"event": "error", "data": {"error": f"Invalid JSON: {line[:100]}"}})
            continue

        msgType = msg.get("type", "")

        if msgType == "ask":
            _handleAsk(msg)
        elif msgType == "status":
            _handleStatus(msg)
        elif msgType == "ping":
            _emit({"event": "pong", "data": {}})
        elif msgType == "setProvider":
            _handleSetProvider(msg)
        elif msgType == "listTemplates":
            _handleListTemplates(msg)
        elif msgType == "exit":
            break
        else:
            _emit({"event": "error", "data": {"error": f"Unknown type: {msgType}"}})


def _getVersion() -> str:
    try:
        import dartlab

        return dartlab.__version__
    except Exception:
        return "unknown"
