"""
실험 ID: 015
실험명: Final Eval — 전체 실험 결과 종합 및 프로덕션 흡수 로드맵

목적:
- 001~014 실험 결과를 종합하여 대형 오픈소스 도약 로드맵 도출
- 각 실험의 핵심 발견을 프로덕션 흡수 우선순위로 정리

가설:
1. 14개 실험에서 검증된 패턴만으로도 AI 계층의 근본적 개선이 가능하다

방법:
1. 각 실험의 핵심 수치 정리
2. 프로덕션 흡수 난이도/임팩트 매트릭스
3. 권장 구현 순서 도출

결과:
=== Wave 1: Eval 기반 ===
- 001: 50 QA golden set 완성 (5개사×10유형)
- 002: 5차원 채점기 상관 0.97 (목표 0.7+ 달성)
- 003: baseline — claude 2.64/5.0, ollama 2.40/5.0 (개선 여지 큼)
- 004: API 키 미설정으로 미실행 (ollama로 대체 가능)
- 005: skeleton 100tok, focused 1,490tok, full 2,251tok. _topics 36% 최대

=== Wave 2: 핵심 3축 ===
- 006: topics 요약 93%절감, report 1줄 96%절감, 조합 시 56% 절감
- 007: qwen3 structured output 100% 성공, llama3.2는 스키마 미준수
- 008: llama3.2 tool calling 100%, qwen3 80%, gemma2 미지원
- 009: Ollama agent_loop 종단 성공 (5개 도구 제한 시)

=== Wave 3: 플러그인 + 에이전트 ===
- 010: 39개 도구, 8카테고리, Company필요 44%, dict→str 패턴 통일
- 011: @tool 데코레이터 완벽 동작, ToolRuntime 호환 확인
- 012: qwen3 planning 도구선택 100%, 평균 4.7 steps

=== Wave 4: MCP + 검증 ===
- 013: 39/39 도구 MCP 변환 성공, 서버 ~34줄
- 014: regex 검증 커버리지 0%, structured 100% (극적 차이)

결론:
■ 즉시 흡수 가능 (검증 완료, 난이도 낮음):
  1. OllamaProvider.complete_with_tools() — 008+009에서 /v1/ 경로 검증
  2. @tool 데코레이터 + ToolPluginRegistry — 011에서 완벽 동작 확인
  3. Context 압축 (topics 요약 + report 1줄) — 006에서 56% 절감 검증

■ 단기 구현 (1-2주):
  4. MCP 서버 — 013에서 변환 로직 검증, SDK 설치만 하면 ~34줄
  5. Structured Output — 007에서 qwen3 100% 확인, providers에 complete_structured() 추가
  6. Plan-and-Execute agent — 012에서 100% 정확도, agent.py에 함수 추가

■ 중기 개선:
  7. Validation V2 — 014에서 structured 기반 100% 커버리지 확인
  8. Eval CI 통합 — 001-002를 engines/ai/eval/에 흡수, pytest 연동
  9. 소형 모델 도구 제한 전략 — 009에서 5개 제한 필요성 확인

■ 모델별 최적 역할:
  - llama3.2 (3B): tool calling 전용 (정확도 100%, 속도 3.5s)
  - qwen3 (8B): structured output + planning (스키마 100%, 계획 100%)
  - gemma2: tool calling 미지원 → Tier 1 pipeline만

실험일: 2026-03-20
"""

if __name__ == "__main__":
    print("=" * 60)
    print("실험 015: Final Eval — 종합 및 로드맵")
    print("=" * 60)

    findings = [
        ("001 goldenDataset", "50 QA pair", "완료"),
        ("002 scoringRubric", "상관 0.97", "완료"),
        ("003 baselineBenchmark", "claude 2.64, ollama 2.40", "완료"),
        ("004 contextAblation", "API 키 미설정", "미실행"),
        ("005 tokenBudgetProfile", "full 2,251tok, _topics 36%", "완료"),
        ("006 compressionStrategy", "전략 1+2 = 56% 절감", "완료"),
        ("007 structuredSchema", "qwen3 100%, llama3.2 스키마 미준수", "완료"),
        ("008 ollamaToolCall", "llama3.2 100%, gemma2 미지원", "완료"),
        ("009 ollamaAgentLoop", "5도구 제한 시 성공", "완료"),
        ("010 registryAnalysis", "39도구, 8카테고리", "완료"),
        ("011 toolPluginApi", "@tool 완벽 동작", "완료"),
        ("012 planAndExecute", "도구선택 100%", "완료"),
        ("013 mcpBridge", "39/39 변환, ~34줄", "완료"),
        ("014 validationV2", "regex 0% vs structured 100%", "완료"),
    ]

    print("\n=== 실험 결과 요약 ===")
    completed = sum(1 for _, _, s in findings if s == "완료")
    print(f"완료: {completed}/14")
    for name, result, status in findings:
        mark = "✓" if status == "완료" else "✗"
        print(f"  {mark} {name:>30}: {result}")

    print("\n=== 프로덕션 흡수 우선순위 ===")
    priorities = [
        (1, "OllamaProvider.complete_with_tools()", "008+009", "낮음", "높음"),
        (2, "@tool 데코레이터 + ToolPluginRegistry", "011", "낮음", "높음"),
        (3, "Context 압축 (topics+report)", "006", "낮음", "중간"),
        (4, "MCP 서버", "013", "중간", "높음"),
        (5, "Structured Output (complete_structured)", "007", "중간", "높음"),
        (6, "Plan-and-Execute agent", "012", "중간", "중간"),
        (7, "Validation V2 (structured 기반)", "014", "낮음", "중간"),
        (8, "Eval CI 통합", "001-002", "낮음", "낮음"),
        (9, "소형 모델 도구 제한", "009", "낮음", "중간"),
    ]

    print(f"{'#':>2} {'항목':>40} {'근거':>10} {'난이도':>6} {'임팩트':>6}")
    for num, item, basis, difficulty, impact in priorities:
        print(f"{num:>2} {item:>40} {basis:>10} {difficulty:>6} {impact:>6}")

    print("\n=== 모델별 최적 역할 ===")
    print("  llama3.2 (3B): tool calling 전용 — 정확도 100%, 3.5s")
    print("  qwen3 (8B):    structured + planning — 스키마 100%, 계획 100%")
    print("  gemma2 (9B):   Tier 1 pipeline만 — tool calling 미지원")
    print("  claude:        전체 기능 — baseline 2.64/5.0")
