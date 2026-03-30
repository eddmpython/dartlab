"""AI 시스템 프롬프트용 도구 카탈로그 (자동 생성).

이 파일은 scripts/generateSpec.py가 자동 생성합니다. 직접 수정 금지.
execute_code 도구 -- CAPABILITIES 기반 코드 생성 + 실행.
"""

TOOL_CATALOG = "## [필수] 도구 사용 규칙\n- **모든 수치 답변은 반드시 도구를 호출해서 실제 데이터를 가져온 뒤 답변하세요.**\n- 추측이나 일반 지식으로 숫자를 답하지 마세요. 반드시 도구로 확인 후 답변.\n- 도구 호출 없이 재무 수치를 언급하면 오답 위험이 큽니다.\n- 도구 파라미터는 아래 명시된 것만 사용하세요. 존재하지 않는 파라미터를 임의 생성하지 마세요.\n\n## 기업 비교 패턴\n두 기업의 매출/이익/비율을 비교하려면 execute_code로 코드 생성:\n```\nimport dartlab\nc1 = dartlab.Company('005930')\nc2 = dartlab.Company('000660')\nprint('삼성전자 IS:', c1.IS)\nprint('SK하이닉스 IS:', c2.IS)\n```\nCAPABILITIES의 Company API를 참조하여 비교 코드를 작성.\n"
