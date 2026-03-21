"""AI 분석 이벤트 타입.

core.analyze()가 생산하는 이벤트 스트림의 단위.
소비자(코드/서버/CLI)가 이벤트를 받아서 형식을 결정한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
class EventKind:
    """이벤트 종류 상수.

    기존 분석 이벤트 + UI 제어 이벤트.
    미등록 이벤트는 소비자가 무시 → 프로토콜 확장에 안전.
    """

    # ── 기존 분석 이벤트 ──
    META = "meta"
    SNAPSHOT = "snapshot"
    CONTEXT = "context"
    CHUNK = "chunk"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    CHART = "chart"
    DONE = "done"
    ERROR = "error"
    SYSTEM_PROMPT = "system_prompt"
    VALIDATION = "validation"

    # ── UI 제어 이벤트 (신규) ──
    UI_ACTION = "ui_action"


@dataclass
class AnalysisEvent:
    """분석 이벤트 단위.

    kind:
        - "meta": 회사/모듈/연도 범위 정보
        - "snapshot": 핵심 수치 스냅샷
        - "context": 모듈별 데이터 (module, label, text)
        - "tool_call": 에이전트 도구 호출 (name, arguments)
        - "tool_result": 도구 실행 결과 (name, result)
        - "chunk": LLM 응답 텍스트 청크 (text)
        - "chart": 차트 스펙 (charts[])
        - "done": 완료 (response_meta 포함 가능)
        - "error": 에러 (error, action)
        - "system_prompt": 시스템 프롬프트 (text, userContent)
        - "validation": 숫자 검증 결과 (mismatches[])
        - "ui_action": canonical UI action payload
    """

    kind: str
    data: dict[str, Any] = field(default_factory=dict)
