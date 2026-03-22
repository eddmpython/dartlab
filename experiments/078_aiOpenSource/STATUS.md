# 078_aiOpenSource — AI 계층 대형 오픈소스 도약 실험

## 개요
dartlab AI 엔진의 6가지 약점(eval 부재, 생태계 폐쇄, 로컬 LLM 제한, 비구조화 응답, MCP 미구현, 단순 에이전트)을 실험으로 검증하고 개선한다.

## 대상 기업 (5개사)
| 코드 | 기업명 | 업종 | 선정 이유 |
|------|--------|------|----------|
| 005930 | 삼성전자 | 전자 | 대형 제조업 대표 |
| 000660 | SK하이닉스 | 반도체 | 반도체 특화 |
| 105560 | KB금융 | 금융 | 금융업 특수계정 |
| 051910 | LG화학 | 화학 | 화학/소재 |
| 035720 | 카카오 | IT플랫폼 | 서비스/플랫폼 |

## 실험 현황

### Wave 1: Eval 기반
| # | 실험 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 001 | goldenDataset | 완료 | 50 QA pair, 5개사×10유형, 커버리지 86.9% (null 22/169) |
| 002 | scoringRubric | 완료 | 5차원 채점기, 수동 대비 상관 0.97 (목표 0.7+ 달성) |
| 003 | baselineBenchmark | 완료 | claude 2.64, ollama 2.40 (차이 10%), SC/AC 가장 낮음 |
| 004 | contextAblation | 실패 | Claude API 키 미설정 — 키 설정 후 재실행 필요 |

### Wave 2: 핵심 3축
| # | 실험 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 005 | tokenBudgetProfile | 완료 | skeleton 103tok, focused 1575tok, full 1900tok. _topics 36% 최대 |
| 006 | compressionStrategy | 완료 | topics 93%절감, report 96%절감, 조합 56% 절감 |
| 007 | structuredSchema | 완료 | qwen3: 파싱100% metrics100%, llama3.2: 스키마 미준수 |
| 008 | ollamaToolCall | 완료 | llama3.2: 100%정확/3.5s, qwen3: 80%/7.4s, gemma2: 미지원 |
| 009 | ollamaAgentLoop | 완료 | 핵심 5도구 제한 시 agent_loop 성공. 39개 전체는 실패 |

### Wave 3: 플러그인 + 에이전트
| # | 실험 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 010 | registryAnalysis | 완료 | 39개 도구, 8카테고리, Company필요 44%, dict→str 패턴 통일 |
| 011 | toolPluginApi | 완료 | @tool 데코레이터+schema 자동생성+ToolRuntime 호환 전부 성공 |
| 012 | planAndExecute | 완료 | qwen3 planning 도구선택 100%, 평균 4.7 steps |

### Wave 4: MCP + 검증
| # | 실험 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 013 | mcpBridge | 완료 | 39/39 MCP 변환 성공, 서버 ~34줄, SDK 설치 후 즉시 구현 |
| 014 | validationV2 | 완료 | regex 0% vs structured 100%, false positive 0% |
| 015 | finalEval | 완료 | 13/14 완료, 9개 프로덕션 흡수 항목 도출 |
