"""`dartlab chat --stdio` -- JSON Lines 프로토콜로 VSCode extension과 통신.

stdin에서 JSON line을 읽고, core.analyze() 이벤트를 JSON line으로 stdout에 쓴다.
Claude Code / Codex extension과 동일한 child process + stdio 패턴.

Protocol:
    -> stdin:  {"id":"1","type":"ask","question":"000660 실적","company":"000660"}
    <- stdout: {"id":"1","event":"meta","data":{"company":"SK하이닉스","stockCode":"000660"}}
    <- stdout: {"id":"1","event":"chunk","data":{"text":"..."}}
    <- stdout: {"id":"1","event":"done","data":{}}
    -> stdin:  {"type":"status"}
    <- stdout: {"event":"status","data":{"provider":"oauth-codex","ready":true}}
    -> stdin:  {"type":"exit"}
"""

from __future__ import annotations

import json
import sys
from typing import Any


def _emit(obj: dict[str, Any]) -> None:
    """stdout에 JSON line 하나를 쓴다."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _handleAsk(msg: dict[str, Any]) -> None:
    """ask 메시지 처리 -- core.analyze() 이벤트를 JSON line으로 변환."""
    from dartlab.ai.runtime.core import analyze

    reqId = msg.get("id", "")
    question = msg.get("question", "")
    company = msg.get("company")
    history = msg.get("history")
    provider = msg.get("provider")
    model = msg.get("model")

    if not question:
        _emit({"id": reqId, "event": "error", "data": {"error": "No question provided"}})
        return

    # Company 해석
    c = None
    if company:
        try:
            from dartlab import Company

            c = Company(company)
        except (ValueError, OSError):
            # 검색으로 재시도
            try:
                from dartlab.core.resolve import searchCompany

                results = searchCompany(company)
                if results:
                    from dartlab import Company as C2

                    c = C2(results[0].get("stockCode", results[0].get("corp_code", "")))
            except Exception:
                pass

    # kwargs 조립
    kwargs: dict[str, Any] = {}
    if provider:
        kwargs["provider"] = provider
    if model:
        kwargs["model"] = model
    if history:
        kwargs["history"] = history

    try:
        for event in analyze(c, question, **kwargs):
            _emit({"id": reqId, "event": event.kind, "data": event.data})
    except KeyboardInterrupt:
        _emit({"id": reqId, "event": "error", "data": {"error": "Interrupted"}})
    except Exception as exc:
        _emit({"id": reqId, "event": "error", "data": {"error": str(exc)}})


def _handleStatus(_msg: dict[str, Any]) -> None:
    """provider 상태를 반환한다."""
    try:
        from dartlab.core.ai.profile import get_profile_manager

        profile = get_profile_manager().load()
        _emit(
            {
                "event": "status",
                "data": {
                    "provider": profile.default_provider or "none",
                    "ready": True,
                },
            }
        )
    except Exception as exc:
        _emit({"event": "status", "data": {"provider": "none", "ready": False, "error": str(exc)}})


def run() -> None:
    """stdio REPL 루프. stdin EOF 또는 exit 메시지로 종료."""
    import dartlab

    dartlab.verbose = False  # suppress print() logs that would corrupt JSON protocol

    # ready 신호
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
        elif msgType == "exit":
            break
        else:
            _emit({"event": "error", "data": {"error": f"Unknown message type: {msgType}"}})


def _getVersion() -> str:
    try:
        import dartlab

        return dartlab.__version__
    except Exception:
        return "unknown"
