"""execute_code Super Tool -- dartlab 코드 실행 dispatcher.

LLM이 dartlab Python 코드를 생성 → DartlabCodeExecutor로 안전 실행.
CAPABILITIES 기반 코드 생성의 실행 엔드포인트.
"""

from __future__ import annotations

from typing import Any, Callable


def registerCodeTool(registerTool: Callable, *, company: Any | None = None) -> None:
    """execute_code Super Tool 등록."""

    stockCode = None
    if company is not None:
        stockCode = getattr(company, "stockCode", getattr(company, "ticker", None))

    def executeCode(code: str = "", **_kw) -> str:
        """dartlab Python 코드를 안전하게 실행한다."""
        if not code.strip():
            return "[오류] 실행할 코드가 없습니다. code 파라미터에 Python 코드를 전달하세요."

        try:
            from dartlab.ai.tools.coding import DartlabCodeExecutor

            executor = DartlabCodeExecutor()
            return executor.execute(code, stockCode=stockCode)
        except (ImportError, OSError, RuntimeError, TypeError, ValueError) as e:
            return f"[오류] 코드 실행 실패: {e}"

    registerTool(
        "execute_code",
        executeCode,
        "dartlab Python 코드를 안전하게 실행합니다. CAPABILITIES의 API를 직접 호출.\n"
        "\n"
        "사용 시점:\n"
        "- 복합 조건 필터링/비교가 필요할 때\n"
        "- 기존 도구로 불가능한 커스텀 분석이 필요할 때\n"
        "- 여러 dartlab API를 조합해야 할 때\n"
        "\n"
        "Guide:\n"
        "- 'ROE 10% 이상 + 부채비율 100% 이하 종목 찾아줘' -> scan + polars 필터링 코드 생성\n"
        "- '삼성전자와 SK하이닉스 5년 매출 비교 테이블' -> 두 Company 생성 + IS 합산 코드\n"
        "- import dartlab 하나로 시작. CAPABILITIES 참조.\n"
        "\n"
        "제약:\n"
        "- subprocess/os/sys/socket 등 금지 (보안)\n"
        "- 허용 모듈: dartlab, polars, numpy, pandas, math, json, datetime 등\n"
        "- 최대 실행 시간: 60초\n"
        "- print()로 결과를 출력해야 LLM이 확인 가능\n"
        "\n"
        "반환: 코드 실행 결과 (stdout). 오류 시 에러 메시지.",
        {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "실행할 dartlab Python 코드. import dartlab으로 시작.",
                },
            },
            "required": ["code"],
        },
        category="global",
        questionTypes=("종합", "투자"),
        priority=50,
    )
