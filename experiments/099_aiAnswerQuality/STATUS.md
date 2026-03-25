# 099 AI 답변 품질 향상

## 목표
세계 RAG/LLM 기법을 조사하고, 실험으로 검증 후 순차 흡수하여 AI 답변 품질을 대대적으로 향상한다.

## baseline (097 실험)
| 지표 | 값 |
|------|-----|
| overall | 8.95 |
| hallucination rate | ~20% |
| tool param accuracy | ~50% |
| 직접 검증 양호율 | 53% |

## 실험 목록
| # | 파일 | 내용 | 기법 | 상태 |
|---|------|------|------|------|
| 001 | toolFewShot.py | tool 호출 few-shot 예시 삽입 | Tool-Use Grounding (Gorilla/ToolBench) | ✅ 완료 (가설 기각) |
| 002 | toolRouteHint.py | 시스템 측 결정론적 도구 추천 | Adaptive RAG + Tool Grounding | ✅ 완료 (가설 채택) |
| 003 | adaptiveContextTier.py | 질문 복잡도 기반 tier | Adaptive RAG (Jeong 2024) | ✅ 완료 (부분 채택) |
| 004 | routeHintExpanded.py | Route Hint 15건 확장 검증 | 002 확장 A/B | ✅ 완료 (가설 채택) |
| 005 | e2eToolSelection.py | E2E tool 선택 + 답변 품질 종합 검증 | selectTools hasCompany + 한국어 강제 | ✅ 완료 (채택) |
| 006 | serverResolveE2E.py | 서버 resolve 경로 E2E 종목 해석 | strip_particles + COMMON_ALIASES | ✅ 완료 (채택) |
| 007 | enumBaseline.py | Enum + Super Tool 스키마 정합성 | topicLabels + dynamic enum | ✅ 완료 (채택) |
| 008 | superToolE2E.py | Super Tool E2E 비교 (96개→8개) | 7 Super Tool dispatcher | ✅ 완료 (채택) |
| 009 | superToolLiveE2E.py | 라이브 AI 답변 품질 E2E | ollama qwen3:4b/8b 실제 답변 | ✅ 완료 (가설 기각) |

## 001 결과 — Few-Shot (기각)

- few-shot 예시만으로 tool parameter 정확도 개선 불가
- "경영진 분석"→"executive" 편향을 few-shot V1/V2 모두 극복 실패
- 프롬프트 토큰 ~500 증가에도 품질 저하 없음 (가설2만 채택)

## 002 결과 — Tool Route Hint (채택)

| topic | Baseline tools | Hint tools | B답변 | H답변 |
|-------|---------------|------------|------|------|
| fsSummary | get_data("fsSummary") | get_data("IS"), get_data("BS"), get_data("ratios") ✅ | 628자 | 2024자 |
| executivePay | get_report_data("executive") ✅ | get_report_data("executive") ✅ | 1690자 | 2150자 |
| mdnaOverview | show_topic("executive") ❌ | show_topic("mdnaOverview") ✅ | 1749자 | 540자 |

- tool parameter 정확도: Baseline 33% → Hint 100% (3/3)
- 001에서 극복 불가한 "경영진→executive" 편향을 결정론적 매핑으로 완전 해결
- 흡수 대상: ROUTE_HINTS 테이블 → tools/selector.py 또는 analyze() context 주입

## 003 결과 — Adaptive Context Tier (부분 채택, 역설적 발견)

- 복잡도 스코어링 정상 동작: simple(1-2)→skeleton, medium-complex(3+)→focused
- **full tier는 대기업에서 OOM** — focused가 실질적 상한
- **역설적 발견**: focused tier(풍부한 context)가 오히려 답변 악화
  - skeleton + tool 5개 = 5439자 vs focused + tool 0개 = 1436자
  - tool calling > 사전 context 주입 — skeleton + 적극적 tool calling이 최적 전략
- **결론**: context tier 동적 변경은 ROI 낮음. 002 Tool Route Hint 흡수가 우선

## 004 결과 — Route Hint 확장 검증 (채택)

- 15건 전체 coverage: 100% (모든 질문에 키워드 매칭)
- 5건 핵심 질문 A/B:
  - **nameAccuracy**: 83.3% → 100% (+16.7%)
  - **paramAccuracy**: 16.7% → 100% (**+83.3%**)
- fsSummary 답변 10.6배 증가 (190자→2010자) — IS/BS/ratios 정확 호출
- 002(3건)+004(5건) 총 8건에서 일관된 효과 확인 → **흡수 확정**

## 005 결과 — E2E Tool 선택 + 답변 품질 (채택)

### 근본 원인
- selectTools()에서 meta 카테고리 +30점 보너스 → company 있어도 meta 도구가 top5 독점
- show_topic 9위, get_data 10위 → LLM이 meta 도구만 호출 → "corp가 필요합니다" 에러

### 패치 결과
- `hasCompany=True`일 때 company/finance +30, meta +5로 변경
- show_topic 1위, get_data 2~3위로 이동 (전 질문 일관)

### E2E 테스트 (8건, ollama qwen3:4b)

| 카테고리 | tool calls | 답변 | 한국어 | 평가 |
|---------|-----------|------|--------|------|
| 재무 | get_data(IS,BS,ratios) | 2852자 | O | **완벽** |
| 경영진 | show_topic(mdnaOverview), get_insight, compute_ratios | 828자 | O* | **완벽** |
| 배당 | get_report_data(dividend) | 818자 | O* | **완벽** |
| 리스크 | show_topic(riskFactor) | 24자 | X | topic 미존재 |
| 사업 | (context만) | 1020자 | O | △ tool 미호출 |
| 기본대화 | (없음) | 49자 | O | 정상 |
| 편의성 | list_modules + get_data 7건 | 1942자 | O* | 과잉호출 |
| 복합 | show_topic, list_topics | 211자 | O | 양호 |

*한국어 프롬프트 강화 후 개선

### 핵심 수치
- tool 정확도: Route Hint 매칭 4건 전부 100% (재무/경영진/배당/리스크)
- 한국어: 50% → ~87% (프롬프트 강화 후)
- 에러: 0/8

## 흡수 완료

| 실험 | 흡수 내용 | 수정 파일 | 상태 |
|------|---------|---------|------|
| 002+004 | ROUTE_HINTS + buildToolRouteHint() | `tools/routeHint.py` (신규), `runtime/core.py` (주입) | ✅ 완료 |
| 003 | 복잡도 기반 tier 승격 | 보류 (ROI 낮음) | ⏸ |
| 005 | selectTools hasCompany + 한국어 강제 + merge model 리셋 | `selector.py`, `agent.py`, `system_base.py`, `types.py` | ✅ 완료 |

### 흡수 상세 (002+004)
- **신규 파일**: `src/dartlab/engines/ai/tools/routeHint.py`
  - ROUTE_HINTS: 21개 키워드 → 추천 도구+args 매핑 테이블
  - `buildToolRouteHint()`: 질문에서 키워드 매칭 → 힌트 텍스트 생성
- **수정 파일**: `src/dartlab/engines/ai/runtime/core.py`
  - 모든 provider에서 user_content 앞에 Route Hint 주입
- **테스트**: `tests/test_ai_context_routing.py`에 4건 추가 (전체 통과)

### 흡수 상세 (005)
- **`src/dartlab/engines/ai/tools/selector.py`**: `hasCompany` 파라미터 추가. company 있으면 company/finance/analysis/valuation +30, meta +5
- **`src/dartlab/engines/ai/runtime/agent.py`**: selectTools 호출에 `hasCompany=company is not None` 전달 (3곳)
- **`src/dartlab/engines/ai/conversation/templates/system_base.py`**: 한국어 답변 강제 — "[필수] 한국어 질문에는 반드시 한국어로만 답변"
- **`src/dartlab/engines/ai/types.py`**: LLMConfig.merge()에서 provider 변경 시 model 리셋
- **`src/dartlab/engines/ai/providers/oauth_codex.py`**: Plus/Pro 자동 감지, rate limit 리셋 시간 표시

## 006 결과 — 서버 Resolve E2E (채택)

- 조사 제거(`strip_particles`) + `COMMON_ALIASES` 확장
- resolve 정확도: 12/12 (100%) — "하이닉스의", "삼전의", "엔솔은", "카뱅을" 등 모두 정확 매칭
- 서버 `try_resolve_company`와 코어 `resolve_from_text` 양쪽 모두 동일 동작

## 007-008 결과 — AI 도구 아키텍처 전면 재설계 (채택)

### Phase 1: Enum + 한국어 라벨
- `topicLabels.py`: 70개 topic × 한국어 라벨 + aliases
- `show_topic`: 동적 topic enum (삼성전자 기준 53개)
- `get_data`: 동적 module enum (9개)
- `get_report_data`: 동적 apiType enum (24개)

### Phase 2: Super Tool 통합
- **96개 → 8개** (7 super tool + 1 plugin)
- `explore`: 공시 탐색 (show/topics/trace/diff/info/filings/search)
- `finance`: 재무 데이터 (data/modules/ratios/growth/yoy/anomalies/report/search)
- `analyze`: 심층 분석 (insight/sector/rank/esg/valuation/changes/audit)
- `market`: 시장 데이터 (price/consensus/history/screen)
- `openapi`: DART/EDGAR API (dartCall/searchFilings/capabilities)
- `system`: 메타 정보 (spec/features/searchCompany/dataStatus/suggest)
- `chart`: UI/차트 (navigate/chart)

### Phase 3: Route Hint → enum 흡수
- ollama(Super Tool 모드)에서 Route Hint 비활성화 — enum description이 대체
- `buildToolPrompt`에 Super Tool 전용 분석 절차 생성

### Phase 4: 동적 topic 검색
- `explore(action='search', keyword='비용')` → fsSummary, consolidatedNotes 정확 반환
- topicLabels aliases + sections 본문 양쪽 검색

### 수정 파일
| 파일 | 변경 |
|------|------|
| `engines/common/topicLabels.py` | **신규** — 70개 topic 한국어 라벨 + aliases |
| `engines/ai/tools/defaults/company.py` | show_topic 동적 enum |
| `engines/ai/tools/defaults/finance.py` | get_data/get_report_data 동적 enum |
| `engines/ai/tools/superTools/` | **신규** — 7개 Super Tool dispatcher |
| `engines/ai/tools/registry.py` | useSuperTools 플래그 |
| `engines/ai/tools/selector.py` | Super Tool 전용 분석 절차 |
| `engines/ai/runtime/core.py` | ollama → Super Tool 자동 활성화, Route Hint 조건부 비활성화 |
| `engines/ai/runtime/run_modes.py` | _run_agent에 useSuperTools 전달 |

## 009 결과 — Super Tool 라이브 E2E (가설 기각)

### qwen3:4b
| 질문 | 기대 | 실제 | 평가 |
|------|------|------|------|
| 재무제표 요약 | finance(data,IS/BS) | system×5 → hallucination | ❌ |
| 배당 현황 | finance(report,dividend) | finance(report,dividend) ✅ → chart 에러 | △ |
| 리스크 요인 | explore(show,riskDerivative) | system(dataStatus)×2 → 영어 답변 | ❌ |
| 안녕하세요 | 도구없음 | (없음) ✅ | ✅ |

- tool 정확도: 33%, 한국어: 75%

### qwen3:8b (latest)
| 질문 | 기대 | 실제 | 평가 |
|------|------|------|------|
| 재무제표 요약 | finance(data,IS) | finance(data,sections) — wrong module | △ |
| 리스크 요인 | explore(show,riskDerivative) | (없음) → hallucination | ❌ |
| 배당 현황 | finance(report,dividend) | explore(topic='dividend') — action 누락 | ❌ |

- tool 정확도: 0%, 한국어: 100%

### 핵심 발견
1. Super Tool enum/라벨만으로는 소형 모델(4b/8b)의 tool calling 품질 개선 불가
2. action dispatch 패턴(explore → action → target)을 소형 모델이 이해 못함
3. 도구 없이 답변 생성 → 100% hallucination (허위 수치)
4. **다음 단계**: Plan-Execute 패턴(시스템이 질문 분류 → 도구 계획 생성 → 순차 실행) 또는 14b+ 모델 필수
