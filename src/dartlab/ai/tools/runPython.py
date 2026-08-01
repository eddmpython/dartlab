"""Constrained Python execution tool for DartLab analysis.

안전 장치:
- 실행 시간 한도: env DARTLAB_RUNPYTHON_TIMEOUT_SEC (기본 60). 별 thread에서 실행하고
  사용자 Python bytecode는 trace deadline으로 중단한다. 네이티브 확장 호출은 반환을 강제할 수 없다.
- import, built-in, 파일, 환경 접근은 runpythonGuard의 fail-closed allowlist를 적용한다.
- emit_result 누락 안내: emitted 가 비면 GATE 가 차단할 것이라는 hint 메시지.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import textwrap
import threading
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import Any

from dartlab.ai.contracts import Ref

from .engineCall import _jsonableResult
from .formatting import shortText
from .runpythonGuard import _assertSafeAst, _safeBuiltins
from .types import ToolResult

logger = logging.getLogger(__name__)

_TIMEOUT_SEC = float(os.environ.get("DARTLAB_RUNPYTHON_TIMEOUT_SEC", "60"))
_OUTPUT_STREAM_BYTES = 64 * 1024
_TABLE_REF_BYTES = 32 * 1024
_VALUE_REF_BYTES = 4 * 1024
_REF_ITEM_CAP = 50


_BLOCK_KEYWORDS = (
    "def ",
    "class ",
    "for ",
    "while ",
    "if ",
    "elif ",
    "else:",
    "try:",
    "except",
    "finally:",
    "with ",
)


class _BoundedStringIO(StringIO):
    """stdout/stderr가 메모리를 무제한 점유하지 않도록 UTF-8 byte 상한을 둔다."""

    def __init__(self, maxBytes: int) -> None:
        super().__init__()
        self.maxBytes = maxBytes
        self.usedBytes = 0
        self.truncated = False

    def write(self, value: str) -> int:
        """출력 예산 안에서 문자열을 기록하고 원래 길이를 반환한다."""
        text = str(value)
        encoded = text.encode("utf-8")
        remaining = max(0, self.maxBytes - self.usedBytes)
        if len(encoded) <= remaining:
            self.usedBytes += len(encoded)
            super().write(text)
            return len(text)
        if remaining:
            fragment = encoded[:remaining].decode("utf-8", errors="ignore")
            self.usedBytes += len(fragment.encode("utf-8"))
            super().write(fragment)
        self.truncated = True
        return len(text)

    def getvalue(self) -> str:
        """누적 출력과 필요한 경우 잘림 표지를 반환한다."""
        value = super().getvalue()
        return value + ("\n...[output truncated]" if self.truncated else "")


def _tryUnindentFallback(code: str) -> str | None:
    """단일 statement series 코드면 모든 줄 lstrip — IndentationError 자동 복구.

    블록 키워드 (def/for/if/...) 가 있으면 들여쓰기가 *의미 있다* — 안전상 None.
    LLM 이 1 줄만 잘못 indent 한 경우 (사용자가 본 ` df = dartlab.scan(...)`) 정상화.
    """
    if any(kw in code for kw in _BLOCK_KEYWORDS):
        return None
    stripped = "\n".join(line.lstrip() for line in code.split("\n"))
    if stripped == code:
        return None  # 변화 없음 — 다시 try 의미 X.
    return stripped


def _lastTracebackLine(tracebackText: str) -> str:
    """traceback 마지막 비어있지 않은 줄 (보통 `ExceptionName: message`) 반환.

    UI 답변 헤더·summary 에 한 줄 진단 노출용. 추출 실패 시 빈 문자열.
    """
    text = (tracebackText or "").strip()
    if not text:
        return ""
    for line in reversed(text.splitlines()):
        s = line.strip()
        if not s:
            continue
        # 너무 길면 자름 — UI summary 한 줄 가독성.
        return s[:240]
    return ""


def _diagnoseErrorHint(tracebackText: str) -> str:
    """LLM 코드 결함 분류 — 자주 보이는 polars / pandas / dartlab API 패턴.

    LLM 다음 turn 에 같은 실수 안 하게 *짧은 한국어 hint* 반환. 매칭 안 되면 빈 문자열.
    """
    text = tracebackText or ""
    # polars projection 시 같은 출력 컬럼명 두 번 — agent 가 alias 강제 rename 시 자주.
    if "duplicate output name" in text or "DuplicateError" in text:
        return (
            "동일 컬럼명을 select 안에서 두 번 사용 — scan/show 결과 컬럼은 rename 없이 그대로 select. "
            "alias 가 필요하면 *기존 이름과 다른* 이름만 부여."
        )
    # 컬럼 미존재 — agent 가 추측한 컬럼명이 실제 결과와 불일치.
    if "ColumnNotFound" in text or "not found" in text.lower():
        return "컬럼명 불일치 — df.columns 로 실제 이름 먼저 확인 후 select."
    # IndentationError — leading space (이미 dedent 시도하지만 mixed indent 는 못 잡음).
    if "IndentationError" in text or "TabError" in text:
        return "코드 들여쓰기 결함 — 모든 라인을 0 indent 에서 시작 (def/for/if 본체만 4-space 들여쓰기)."
    # SyntaxError — 일반.
    if "SyntaxError" in text:
        return "Python 구문 오류 — 코드 수정 후 재시도."
    # NameError — 미정의 변수 (보통 import 누락).
    if "NameError" in text:
        return "정의되지 않은 이름 — import 또는 사전 변수 선언 누락. 사용 가능: dartlab, pl, normalizeColumn, columnsFor, availableTopics."
    # AttributeError on dartlab — 잘못된 API 이름.
    if "AttributeError" in text and "dartlab" in text:
        return "dartlab 모듈에 없는 속성 호출 — ReadCapability 로 정확한 API 이름 확인."
    return ""


def runPython(code: str, *, runId: str | None = None) -> ToolResult:
    """sandboxed Python 실행 — stdout/stderr 캡처 + emit_result 결과 수집."""
    stdout = _BoundedStringIO(_OUTPUT_STREAM_BYTES)
    stderr = _BoundedStringIO(_OUTPUT_STREAM_BYTES)
    emitted: dict[str, Any] = {}

    def emitResult(*args: Any, **kwargs: Any) -> None:
        """Result emitter. 전체 payload를 EngineCall과 같은 128KiB 예산으로 제한한다."""
        rawPayload: dict[str, Any] = {}
        for arg in args:
            if isinstance(arg, dict):
                rawPayload.update(arg)
            else:
                rawPayload.setdefault("values", {})
                if isinstance(rawPayload["values"], dict):
                    rawPayload["values"][f"value_{len(rawPayload['values'])}"] = arg
        for k, v in kwargs.items():
            rawPayload[k] = v
        payload = _jsonableResult(rawPayload)
        if not isinstance(payload, dict):
            payload = {"result": payload}
        emitted.clear()
        emitted.update(payload)
        print("DARTLAB_RESULT_JSON=" + json.dumps(payload, ensure_ascii=False, default=str))

    # sandbox guard — write 가능 mode 의 open 은 안전 경로 prefix 로 제한.
    # 차단 호출 (os.system / subprocess.run 등) 은 exec 직전 AST 검사로 거부.
    globals_dict: dict[str, Any] = {
        "emit_result": emitResult,
        "__builtins__": _safeBuiltins(),
    }
    container: dict[str, Any] = {}
    deadline = time.monotonic() + _TIMEOUT_SEC

    def _timeoutTrace(frame: Any, _event: str, _arg: Any) -> Any:
        """사용자 Python loop가 timeout 뒤 daemon thread로 남지 않게 중단한다."""
        if frame.f_code.co_filename != "<string>":
            return None
        if time.monotonic() >= deadline:
            raise TimeoutError(f"RunPython execution exceeded {_TIMEOUT_SEC:.0f}s")
        return _timeoutTrace

    def _runner() -> None:
        try:
            import polars as pl

            import dartlab
            from dartlab.ai.tools.columnAlias import (
                availableTopics,
                columnsFor,
                normalizeColumn,
            )

            globals_dict.update(
                {
                    "dartlab": dartlab,
                    "pl": pl,
                    # 컬럼 정규화 헬퍼 — 한국어 / snake / alias → 표준 snake_id.
                    "normalizeColumn": normalizeColumn,
                    "columnsFor": columnsFor,
                    "availableTopics": availableTopics,
                }
            )
            # textwrap.dedent — *공통* leading whitespace 만 제거. mixed-indent
            # (한 줄만 indent 된 LLM 결함) 는 못 잡음 → IndentationError fallback 으로
            # 처리: 블록 키워드 없으면 모든 줄 lstrip 해서 재시도.
            normalized_code = textwrap.dedent(str(code or "")).strip()
            # AST sandbox guard — destructive shell/import 호출 거부.
            _assertSafeAst(normalized_code)
            with redirect_stdout(stdout), redirect_stderr(stderr):
                sys.settrace(_timeoutTrace)
                try:
                    try:
                        exec(normalized_code, globals_dict, globals_dict)  # noqa: S102
                    except IndentationError:
                        fallback = _tryUnindentFallback(normalized_code)
                        if fallback is None:
                            raise
                        _assertSafeAst(fallback)
                        exec(fallback, globals_dict, globals_dict)  # noqa: S102
                finally:
                    sys.settrace(None)
        except TimeoutError:
            logger.warning("run_python timed out (runId=%s)", runId or "local", exc_info=True)
            container["timeout"] = True
        except Exception:  # noqa: BLE001
            logger.debug("run_python captured execution failure", exc_info=True)
            container["error"] = traceback.format_exc()

    start = time.monotonic()
    threadName = f"dartlab-runpython-{runId or 'local'}"
    thread = threading.Thread(target=_runner, daemon=True, name=threadName)
    thread.start()
    thread.join(timeout=_TIMEOUT_SEC)
    timedOut = thread.is_alive()
    if timedOut:
        # Python bytecode loop는 trace deadline에서 곧 종료된다. 짧게 회수해 timeout
        # 반환 뒤 CPU를 계속 점유하는 daemon thread를 남기지 않는다. 네이티브 확장
        # 내부에서 멈춘 경우에는 이 대기 뒤에도 timeout으로 fail-closed 반환한다.
        thread.join(timeout=0.2)
    if timedOut or container.get("timeout") is True:
        duration = int((time.monotonic() - start) * 1000)
        return ToolResult(
            False,
            f"run_python timeout ({_TIMEOUT_SEC:.0f}s)",
            refs=[
                Ref(
                    id=f"execution:{runId or 'local'}:timeout",
                    kind="executionRef",
                    title="python execution timeout",
                    source="run_python",
                    payload={"durationMs": duration, "timeoutSec": _TIMEOUT_SEC},
                )
            ],
            data={"stdout": stdout.getvalue(), "stderr": stderr.getvalue(), "durationMs": duration},
            error="python_execution_timeout",
        )
    if "error" in container:
        duration = int((time.monotonic() - start) * 1000)
        logger.warning(
            "run_python failed (runId=%s, %dms)\n--- code ---\n%s\n--- traceback ---\n%s",
            runId or "local",
            duration,
            (code or "")[:1500],
            container["error"],
        )
        # 흔한 모델 코드 결함 → 다음 turn 에 같은 실수 안 하게 hint 부착.
        # 단순 substring 매칭 — 정밀도보다 다음 attempt 의 가이드성 우선.
        traceback_text = container["error"]
        hint = _diagnoseErrorHint(traceback_text)
        errorLine = _lastTracebackLine(traceback_text)
        summary = "run_python 실행 실패"
        if errorLine:
            summary = f"run_python 실행 실패 — {errorLine}"
        elif hint:
            summary = f"run_python 실행 실패 — {hint}"
        return ToolResult(
            False,
            summary,
            refs=[
                Ref(
                    id=f"execution:{runId or 'local'}:failed",
                    kind="executionRef",
                    title="python execution failed",
                    source="run_python",
                    payload={
                        "durationMs": duration,
                        "stderr": traceback_text,
                        "hint": hint,
                        "errorLine": errorLine,
                    },
                )
            ],
            data={
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue(),
                # 실제 exception traceback — UI 가 errorBody 로 펼침. data.stderr (스트림 캡처)
                # 은 raise 시 비어있어서 user 가 진단 못 함 → 별도 필드 노출.
                "traceback": traceback_text,
                "errorLine": errorLine,
                "durationMs": duration,
                "hint": hint,
            },
            error="python_execution_failed",
        )
    duration = int((time.monotonic() - start) * 1000)
    refs = [
        Ref(
            id=f"execution:{runId or 'local'}:{duration}",
            kind="executionRef",
            title="python execution",
            source="run_python",
            payload={
                "durationMs": duration,
                "stdout": shortText(stdout.getvalue(), limit=4000),
                "stderr": shortText(stderr.getvalue(), limit=4000),
                "preview": shortText(json.dumps(emitted, ensure_ascii=False, default=str), limit=4000),
            },
        )
    ]
    table_value = emitted.get("table")
    if "table" in emitted and table_value is not None:
        # 빈 DataFrame/list 도 tableRef 를 생성 — recipe 가 schema 만 들고 "행 0" 를
        # 표현한 결과 (insufficient data 등) 는 valid evidence. evidence 누락이 아닌
        # 실 결과 표현이므로 scorecard 의 evidenceCompleteness 가 정확히 측정되도록.
        refs.append(
            Ref(
                id=f"table:{runId or 'local'}:python",
                kind="tableRef",
                title="python table result",
                source=refs[0].id,
                payload={"rows": _jsonableResult(table_value, maxBytes=_TABLE_REF_BYTES)},
            )
        )
    values_raw = emitted.get("values")
    if isinstance(values_raw, dict) and values_raw:
        values = values_raw
        unitsRaw = emitted.get("units")
        units = unitsRaw if isinstance(unitsRaw, dict) else {}
        for key, value in list(values.items())[:_REF_ITEM_CAP]:
            refs.append(
                Ref(
                    id=f"value:{runId or 'local'}:{key}",
                    kind="valueRef",
                    title=str(key),
                    source=refs[0].id,
                    payload={
                        "key": key,
                        "value": _jsonableResult(value, maxBytes=_VALUE_REF_BYTES),
                        "unit": units.get(key),
                    },
                )
            )
    # date= 키가 명시적으로 emit 됐다면 (None 이라도) dateRef 를 항상 만든다 —
    # recipe 가 'date 정보를 추적한다' 는 의도. None 인 경우 'unavailable' 로
    # 명시 — scorecard 가 evidence "선언 + 미가용" 을 정확히 측정하도록.
    has_date_key = "date" in emitted or "dateRef" in emitted
    date_value = emitted.get("date") or emitted.get("dateRef")
    if has_date_key:
        date_str = str(date_value) if date_value else "unavailable"
        refs.append(
            Ref(
                id=f"date:{runId or 'local'}:{date_str[:32]}",
                kind="dateRef",
                title=date_str,
                source=refs[0].id,
                payload={"value": date_str, "specified": date_value is not None},
            )
        )
    sources_raw = emitted.get("sources") or emitted.get("sourceRefs")
    if isinstance(sources_raw, dict):
        sources_iter = [sources_raw]
    elif isinstance(sources_raw, list):
        sources_iter = []
        for item in sources_raw:
            if isinstance(item, dict):
                sources_iter.append(item)
            elif isinstance(item, str) and item:
                # 다수 recipe 의 관행: sources=["dartlab://..."] 또는 ["url..."] 문자열 목록.
                # dict 래핑 — id/title 동일, url 처럼 보이면 url 도 채움.
                wrapped: dict[str, Any] = {"id": item, "title": item}
                if "://" in item:
                    wrapped["url"] = item
                sources_iter.append(wrapped)
    else:
        sources_iter = []
    for idx, source_payload in enumerate(sources_iter[:_REF_ITEM_CAP]):
        source_id = str(source_payload.get("id") or f"source_{idx}")
        safe_id = re.sub(r"[^A-Za-z0-9_.:-]+", "_", source_id)[:96]
        refs.append(
            Ref(
                id=f"source:{runId or 'local'}:{safe_id}",
                kind="sourceRef",
                title=str(source_payload.get("title") or source_id),
                source=source_payload.get("url") or refs[0].id,
                payload=source_payload,
            )
        )
    summary = "run_python 실행 완료"
    if not emitted:
        summary += " (emit_result 호출 없음 — GATE 가 차단할 가능성)"
    return ToolResult(
        True,
        summary,
        refs=refs,
        data={"stdout": stdout.getvalue(), "stderr": stderr.getvalue(), "result": emitted, "durationMs": duration},
    )
