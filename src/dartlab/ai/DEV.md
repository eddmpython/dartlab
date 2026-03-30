# AI Engine Development Guide

## 설계 사상

### dartlab AI = 전 기능의 자연어 인터페이스 (2026-03-29 재정의)

**AI의 근본 = 편의성.**

AI가 하는 것: 데이터수집, 리서치비서, 일반비서, 기업분석, 시장분석, 앞으로 들어올 dartlab 모든 기능을 다 해준다.
Company든 sections든 scan이든 analysis든 — 사용자에게 어려운 모든 것을 AI가 대신 알고, 추천하고, 분석하고, 제시한다.

### AI의 눈 = CAPABILITIES + 독스트링

- **CAPABILITIES.md** = dartlab 전체 기능맵 (generateSpec.py가 코드에서 자동 수집)
- 5 surface: Python API, CLI, Server, Data Modules, AI Tools
- 각 기능의 독스트링이 AI에게 뭘 제공하고 뭘 받고 뭘 리턴하는지 기술
- CAPABILITIES가 정확하면 AI는 그걸 보고 모든 기능을 쓸 수 있다
- 새 레이어(viz 등)가 추가돼도 CAPABILITIES만 갱신하면 AI가 자동 활용

### 진입점

- **ask** = AI의 유일한 진입점. 모든 질문/요청이 ask로 들어온다
- **chat** = ask를 감싼 REPL. ask와 별개 개념이 아님

### 엔진과 AI의 관계

**AI가 분석의 전 과정을 주도한다.**
- AI가 질문을 이해하고, 필요한 도구를 선택하고, 분석 흐름을 설계한다
- dartlab 엔진(analysis, scan, gather, review 등)은 AI가 호출하는 **도구**다
- AI가 도구 결과를 조합해서 계산, 판단, 해석, 보고서까지 수행한다

**핵심**: AI가 주도한다 → 엔진은 도구다.

### Analysis Briefing 아키텍처

```
질문 → Intent 분류 → Analysis Briefing(2,000-8,000토큰) → LLM 해석(1회) → 자기 검증 → [보충 도구]
```

- **Analysis Briefing**: 질문 유형에 맞는 엔진 함수를 사전 실행하여 풍부한 분석 결과를 LLM에 전달
- **Provider 평등**: tool calling 없는 provider도 동일한 분석 품질 달성
- **도구는 보충**: 사전계산에 없는 정보만 도구로 조회 (explore, gather, openapi, research 4개)
- **자기 검증**: LLM 답변의 수치가 브리핑과 일치하는지 자동 확인

#### 구현 위치

- `context/briefing.py`: compact map + pipeline 통합 → Analysis Briefing 생성
- `runtime/pipeline.py`: 16개 러너 + L2 엔진 (기존 구현 재활용)
- `runtime/core.py`: briefing 기반 컨텍스트 조립

### 속도 원칙

**LLM roundtrip을 줄이는 것이 속도다.**
- 더 많은 데이터를 미리 조립해서 1회에 끝내는 것이 빠르다
- 도구 호출을 병렬화하는 것보다, 애초에 호출이 필요 없게 만드는 것이 빠르다

### 사용자 원칙

- **접근성**: `dartlab ask "005930" "영업이익률 추세는?"` — ask가 전부
- **신뢰성**: AI가 도구를 통해 가져온 숫자는 원본 기반. 검증 레이어가 일관성을 확인한다
- **투명성**: 어떤 데이터를 봤는지(includedEvidence), 어떤 도구를 썼는지(tool_call) 항상 노출

### 품질 검증 기준선 (2026-03-27)

ollama qwen3:4b 기준 critical+high 35건 배치 결과:

| 지표 | 값 | 비고 |
|------|-----|------|
| avgOverall | 7.33 | gemini fallback 수정 후 재측정 (수정 전 5.98) |
| routeMatch | 1.00 | intent 분류 + 라우팅 완벽 |
| moduleUtilization | 0.75 | 일부 eval 케이스 정합성 문제 포함 |
| falseUnavailable | 0/35 | "데이터 없다" 거짓 응답 없음 |

production 모델(openai/gemini) 측정은 API 키 확보 후 진행 예정. factual accuracy는 production 모델에서만 유의미.

주요 failure taxonomy:
- **runtime_error**: provider 설정 정합성 (해결됨)
- **retrieval_failure**: eval 케이스 expectedModules와 실제 컨텍스트 빌더 매핑 간극
- **generation_failure**: 소형 모델 한계 (production 모델에서 재측정 필요)

---

## Source Of Truth

- 데이터 source-of-truth: `src/dartlab/core/registry.py`
- AI capability source-of-truth: `src/dartlab/core/capabilities.py`

## 현재 구조 원칙

- `core.analyze()`가 AI 오케스트레이션의 단일 진입점이다.
- `tools/registry.py`는 capability 정의를 runtime에 바인딩하는 레이어다.
- `server/streaming.py`, `mcp/__init__.py`, UI SSE client는 capability 결과를 소비하는 adapter다.
- Svelte UI는 source-of-truth가 아니라 render sink다.
- OpenDART 최근 공시목록 retrieval도 `core.analyze()`에서 company 유무와 무관하게 같은 경로로 합류한다.

## 패키지 구조

- `runtime/`
  - `core.py`: 오케스트레이터
  - `events.py`: canonical/legacy 이벤트 계약
  - `pipeline.py`: pre-compute pipeline
  - `post_processing.py`: navigate/validation/auto-artifact 후처리
  - `standalone.py`: public ask/chat bridge
  - `validation.py`: 숫자 검증
- `conversation/`
  - `dialogue.py`, `history.py`, `intent.py`, `focus.py`, `prompts.py`
  - `suggestions.py`: 회사 상태 기반 추천 질문 생성
  - `data_ready.py`: docs/finance/report 가용성 요약
- `context/`
  - `builder.py`: structured context build
  - `snapshot.py`: headline snapshot
  - `company_adapter.py`: facade mismatch adapter
  - `dartOpenapi.py`: OpenDART filing intent 파싱 + recent filing context
- `tools/`
  - `registry.py`: tool/capability binding (`useSuperTools` 플래그로 모드 전환)
  - `runtime.py`: tool execution runtime
  - `selector.py`: capability 기반 도구 선택 + Super Tool 전용 prompt 분기
  - `plugin.py`: external tool plugin bridge
  - `coding.py`: coding runtime bridge
  - `recipes.py`: 질문 유형별 선행 분석 레시피
  - `routeHint.py`: 키워드→도구 매핑 (Super Tool 모드에서 deprecated)
  - `superTools/`: **Super Tool dispatcher** (현재 8개, 목표: 4축 정렬 + 데이터 + 외부 = 10개)
  - `defaults/`: 기존 101개 도구 등록 (레거시 모드에서 사용)
- `providers/support/`
  - `codex_cli.py`, `cli_setup.py`, `ollama_setup.py`, `oauth_token.py`
  - provider 구현이 직접 쓰는 CLI/OAuth 보조 계층

루트 shim 모듈(`core.py`, `tools_registry.py`, `dialogue.py` 등)은 제거되었다. 새 코드는 반드시 하위 패키지 경로(`runtime/`, `conversation/`, `context/`, `tools/`, `providers/support/`)를 직접 import한다.

## Super Tool 아키텍처

101개 도구를 Super Tool dispatcher로 통합. 모든 provider에서 기본 활성화.

### 핵심 원칙: 수퍼툴 = dartlab 축

**수퍼툴 이름은 dartlab 4축 이름과 일치해야 한다.** AI가 호출하는 것 = 사용자가 호출하는 것.

- `scan` 수퍼툴 → `dartlab.scan(axis)` 공개 API와 1:1
- `analysis` 수퍼툴 → `c.analysis(axis)` 공개 API와 1:1
- `review` 수퍼툴 → `c.review(section)`, `blocks(c)` 공개 API와 1:1
- `explore`/`finance` → Company 데이터 조회 (기존 유지)

**금지 사항:**
- 수퍼툴 이름과 dartlab 축 이름이 다른 것 (market≠scan, analyze≠analysis)
- 수퍼툴 action이 공개 API에 없는 내부 함수를 직접 호출하는 것
- 새 축/모듈 추가 시 수퍼툴에 수동 동기화를 잊는 것

### 모델 요구사항
- **최소**: tool calling 지원 + 14B 파라미터 이상 (예: qwen3:14b, llama3.1:8b-instruct)
- **권장**: GPT-4o, Claude Sonnet 이상 — tool calling + 한국어 + 복합 파라미터 동시 처리
- **부적합**: 8B 이하 소형 모델 (qwen3:4b/8b) — action dispatch 패턴을 이해하지 못함, hallucination 다발
- 실험 009 검증 결과: qwen3:4b tool 정확도 33%, qwen3:8b 0%. 소형 모델은 tool calling AI 분석에 사용 불가.

### 활성화 조건
- **모든 provider에서 Super Tool 기본 활성화** (`_useSuperTools = True`)
- `build_tool_runtime(company, useSuperTools=False)`로 레거시 모드 수동 전환 가능
- Route Hint(`routeHint.py`)는 deprecated — Super Tool enum description이 대체

### Super Tool 목록 (목표 구조)

**4축 정렬 수퍼툴:**
| Tool | 역할 | dartlab 공개 API | action |
|------|------|-----------------|--------|
| `scan` | 전종목 횡단 분석 | `dartlab.scan(axis)` | governance, workforce, capital, debt, cashflow, audit, insider, quality, account, ratio, digest, network |
| `analysis` | 단일기업 14축 분석 | `c.analysis(axis)` | 수익구조, 자금조달, 자산구조, 현금흐름, 수익성, 성장성, 안정성, 효율성, 종합평가, 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성 |
| `review` | 분석 결과 구조화 | `c.review(section)`, `blocks(c)` | blocks, section, full |

**데이터 조회 수퍼툴:**
| Tool | 역할 | action |
|------|------|--------|
| `explore` | Company docs 조회 | show, topics, trace, diff, info, filings, search |
| `finance` | Company 재무 데이터 | data, modules, ratios, growth, yoy, anomalies, report, search, quality, decompose |

**외부 연동 수퍼툴:**
| Tool | 역할 | action |
|------|------|--------|
| `gather` | 주가/컨센서스/매크로 | price, consensus, history |
| `openapi` | DART/EDGAR 직접 API | dartCall, searchFilings, capabilities |
| `research` | 웹검색/뉴스 | search, news, read_url, industry |
| `system` | 시스템 메타 | spec, features, searchCompany, dataStatus, suggest |
| `chart` | 차트 생성 | navigate, chart |

### 마이그레이션: market → scan + gather

현재 `market` 수퍼툴의 12개 action을 분리한다:
- scan 12축 (governance~network) → `scan` 수퍼툴로 이동
- 주가/컨센서스/히스토리 → `gather` 수퍼툴로 이동
- 단일기업 financials/ratios → `finance` 수퍼툴에 이미 있음 (중복 제거)

### 마이그레이션: analyze → analysis

현재 `analyze` 수퍼툴의 action을 재구성한다:
- insight/audit/distress → `analysis` 수퍼툴의 해당 축으로 통합
- sector/rank → `scan` 수퍼툴 또는 `analysis` 수퍼툴 내 comparative action
- valuation → `analysis` 수퍼툴 내 action
- research → `research` 수퍼툴로 이동 (이미 별도 존재)

### 동적 enum
- `explore.target`: company.topics에서 추출 (삼성전자 기준 53개) + 한국어 라벨
- `finance.module`: scan_available_modules에서 추출 (9개) + 한국어 라벨
- `finance.apiType`: company.report.availableApiTypes에서 추출 (24개) + 한국어 라벨
- enum description에 `topicLabels.py`의 한국어 라벨과 aliases 포함

### 한국어 라벨 source of truth
- `core/topicLabels.py`: 70개 topic × 한국어 라벨 + 검색 aliases
- UI의 `topicLabels.js`와 동일 매핑 + AI용 aliases 추가

## UI Action 계약

- canonical payload는 `UiAction`이다.
- render payload는 `ViewSpec` + `WidgetSpec` schema를 기준으로 한다.
- widget id(`chart`, `comparison`, `insight_dashboard`, `table`)는 UI widget registry에 등록된 것만 사용한다.
- 허용 action:
  - `navigate`
  - `render`
  - `update`
  - `toast`
- canonical SSE UI 이벤트는 `ui_action` 하나만 유지한다.
- auto artifact도 별도 chart 이벤트가 아니라 canonical `render` UI action으로 주입한다.
- Svelte 측 AI bridge/helper는 `src/dartlab/ui/src/lib/ai/`에 둔다. `App.svelte`는 provider/profile 동기화와 stream wiring만 연결하는 shell로 유지한다.

## Provider Surface

- 공식 GPT 구독 계정 경로는 두 개다.
  - `codex`: Codex CLI 로그인 기반
  - `oauth-codex`: ChatGPT OAuth 직접 연결 기반
- 공개 provider surface는 `codex`, `oauth-codex`, `openai`, `ollama`, `custom`만 유지한다.
- `claude` provider는 public surface에서 제거되었다. 남은 Claude 관련 코드는 legacy/internal 용도로만 취급한다.
- provider alias(`chatgpt`, `chatgpt-oauth`)는 더 이상 공개/호환 surface에 두지 않는다.
- ask/CLI/server/UI는 같은 provider 문자열을 공유해야 하며, 새 GPT 경로를 추가할 때는 이 문서와 `core/ai/providers.py`, `server/api/ai.py`, `ui/src/App.svelte`, `cli/context.py`를 같이 갱신한다.

## Shared Profile

- AI 설정 source-of-truth는 `~/.dartlab/ai_profile.json`과 공통 secret store다.
- `dartlab.llm.configure()`는 메모리 전용 setter가 아니라 shared profile writer다.
- profile schema는 `defaultProvider + roles(analysis, summary, coding, ui_control)` 구조다.
- UI는 provider/model을 localStorage에 저장하지 않고 `/api/ai/profile`과 `/api/ai/profile/events`를 통해 동기화한다.
- API key는 profile JSON에 저장하지 않고 secret store에만 저장한다.
- OAuth 토큰도 legacy `oauth_token.json` 대신 공통 secret store로 이동한다.
- Ollama preload/probe는 선택 provider가 `ollama`일 때만 적극적으로 수행한다. 다른 provider가 선택된 상태에서는 상태 조회도 lazy probe가 기본이다.
- OpenDART 키는 provider secret store로 흡수하지 않고 프로젝트 `.env`를 source-of-truth로 유지한다.

## Company Adapter 원칙

- AI 레이어는 `company.ratios` 같은 facade surface를 직접 신뢰하지 않는다.
- headline ratio / ratio series는 `src/dartlab/ai/context/company_adapter.py`로만 접근한다.
- facade와 엔진 surface mismatch를 발견하면 AI 코드 곳곳에서 분기하지 말고 adapter에 흡수한다.

## Ask Context 정책

- 기본 `ask`는 cheap-first다. 질문에 맞는 최소 source만 읽고, `docs/finance/report` 전체 선로딩을 금지한다.
- 일반 `ask`의 기본 context tier는 `focused`다. `full` tier는 `report_mode=True`일 때만 허용한다.
- tool-capable provider(`openai`, `ollama`, `custom`)만 `use_tools=True`일 때 `skeleton` tier를 사용한다.
- `oauth-codex` 기본 ask는 더 이상 `full`로 떨어지지 않는다.
- `auto diff`는 `full` tier에서만 자동 계산한다. 기본 ask에서는 `company.diff()`를 선행 호출하지 않는다.
- 질문 해석은 route-first가 아니라 **candidate-module-first**다. 먼저 `sections / notes / report / finance` 후보를 동시에 모으고, 실제 존재하는 모듈만 컨텍스트에 싣는다.
- `costByNature`, `rnd`, `segments`처럼 sections topic이 아니어도 direct/notes 경로로 존재하면 `ask`가 우선 회수한다.
- 일반 `ask`에서 포함된 모듈이 있으면 `"데이터 없음"`이라고 답하면 실패로 본다. false-unavailable 방지가 기본 계약이다.
- tool calling이 비활성화된 ask에서는 `show_topic()` 같은 호출 계획을 문장으로 출력하지 않는다. 이미 제공된 컨텍스트만으로 바로 답하고, 모호할 때만 한 문장 확인 질문을 한다.
- **분기 질문 정책**: "분기", "분기별", "quarterly", "QoQ", "전분기" 등 분기 키워드가 감지되면:
  - route를 `hybrid`로 전환하여 sections + finance 양쪽 모두 포함한다.
  - `company.timeseries`에서 IS/CF 분기별 standalone 데이터를 최근 8분기만 추출하여 context에 주입한다.
  - `fsSummary`를 sections exclude 목록에서 일시 해제하여 분기 요약도 포함한다.
  - response_contract에 분기 데이터 활용 지시를 추가한다.
- **finance route sections 보조 정책**: route=finance일 때도 `businessStatus`, `businessOverview` 중 존재하는 topic 1개를 경량 outline으로 주입한다. "왜 이익률이 변했는지" 같은 맥락을 LLM이 설명할 수 있게 한다.
- **context budget**: focused=10000, full=16000. 분기 데이터 + sections 보조를 수용할 수 있는 크기.

## Persona Eval 루프

- ask 장기 개선의 기본 단위는 **실사용 로그가 아니라 curated 질문 세트 replay**다.
- source-of-truth는 `src/dartlab/ai/eval/personaCases.json`이다.
- 사람 검수 이력 source-of-truth는 `src/dartlab/ai/eval/reviewLog/<persona>.jsonl`이다.
- persona 축은 최소 `assistant`, `data_manager`, `operator`, `installer`, `research_gather`, `accountant`, `business_owner`, `investor`, `analyst`를 유지한다.
- 각 case는 질문만 저장하지 않는다.
  - `expectedRoute`
  - `expectedModules`
  - `mustInclude`
  - `mustNotSay`
  - `forbiddenUiTerms`
  - `allowedClarification`
  - `expectedFollowups`
  - `groundTruthFacts`
- 새 ask 실패는 바로 프롬프트 hotfix로 덮지 않고 먼저 아래로 분류한다.
  - `routing_failure`
  - `retrieval_failure`
  - `false_unavailable`
  - `generation_failure`
  - `ui_wording_failure`
  - `data_gap`
  - `runtime_error`
- replay runner source-of-truth는 `src/dartlab/ai/eval/replayRunner.py`다.
- 실제 replay를 검토할 때는 결과만 남기지 않고 반드시 `reviewedAt / effectiveness / improvementActions / notes`를 같이 남긴다.
- review log는 persona별로 분리한다.
  - `reviewLog/accountant.jsonl`
  - `reviewLog/investor.jsonl`
  - `reviewLog/analyst.jsonl`
- 다음 회차 replay는 같은 persona 파일을 이어서 보고, `효과적이었는지`와 `이번 개선으로 줄여야 할 failure type`을 같이 적는다.
- 개선 루프는 항상 `질문 세트 추가 → replay → failure taxonomy 확인 → AI fix vs DartLab core fix 분리 → 회귀 재실행` 순서로 간다.
- "장기 학습"은 모델 학습이 아니라 이 replay/backlog 루프를 뜻한다.
- replay에서 반복 실패한 질문 묶음은 generic ambiguity로 남기지 말고 강제 규칙으로 승격한다.
  - `부실 징후`류 질문 → `finance` route 고정
  - `영업이익률 + 비용 구조 + 사업 변화` → `IS + costByNature + businessOverview/productService` 강제 hybrid, clarification 금지
  - `최근 공시 + 사업 구조 변화` → `disclosureChanges`에 `businessOverview/productService`를 같이 회수
- **groundTruthFacts는 수동 하드코딩이 아니라 `truthHarvester`로 자동 생성한다.**
  - `scripts/harvestEvalTruth.py`로 배치 실행, `--severity critical,high`부터 우선 채움
  - finance 엔진에서 IS/BS/CF 핵심 계정 + ratios를 자동 추출
  - `truthAsOf` 날짜로 데이터 시점을 기록
- **결정론적 검증(라우팅/모듈)은 LLM 호출 없이 CI에서 매 커밋 검증한다.**
  - `tests/test_eval_deterministic.py` — personaCases.json의 expectedRoute/모듈/구조 무결성 검증
  - personaCases에 케이스를 추가하면 자동으로 결정론적 테스트도 실행됨
  - `@pytest.mark.unit` → `test-lock.sh` 1단계에서 실행
- **배치 replay는 `scripts/runEvalBatch.py`로 자동화한다.**
  - `--provider`, `--model`, `--severity`, `--persona`, `--compare latest` 필터
  - 결과는 `eval/batchResults/` JSONL로 저장, 이전 배치와 회귀 비교 지원
- **replaySuite()는 Company 캐시 3개 제한으로 OOM을 방지한다.**
  - 4번째 Company 로드 시 가장 오래된 캐시 제거 + `gc.collect()`

## User Language 원칙

- UI 기본 surface에서는 internal module/method 이름을 직접 노출하지 않는다.
- ask 내부 debug/meta와 eval/log에서는 raw module 이름을 유지해도 된다.
- runtime `meta` / `done`에는 raw `includedModules`와 함께 사용자용 `includedEvidence` label을 같이 실어 보낸다.
- UI evidence panel, transparency badges, modal title은 사용자용 evidence label을 우선 사용한다.
- tool 이름도 UI에서는 사용자 행동 기준 문구로 보여준다.
  - 예: `list_live_filings` → `실시간 공시 목록 조회`
  - 예: `get_data` → `재무·공시 데이터 조회`
- ask 본문도 기본적으로 사용자 언어를 쓴다.
  - `IS/BS/CF/ratios/TTM` → `손익계산서/재무상태표/현금흐름표/재무비율/최근 4분기 합산`
  - `costByNature/businessOverview/productService` → `성격별 비용 분류/사업의 개요/제품·서비스`
  - `topic/period/source` → `항목/시점/출처`

## Sections First Retrieval

- `sections`는 기본적으로 “본문 덩어리”가 아니라 “retrieval index”로 쓴다.
- sections 계열 질문은 `topics() -> outline(topic) -> contextSlices -> raw docs sections block` 순서로 좁힌다.
- `contextSlices`가 ask의 기본 evidence layer다. `outline(topic)`는 인덱스/커버리지 확인용이고, 실제 근거 문장은 `contextSlices`에서 먼저 회수한다.
- `retrievalBlocks/raw sections`는 `contextSlices`만으로 근거가 부족할 때만 추가로 연다.
- 일반 재무 질문에서는 `sections`, `report`, `insights`, `change summary`를 자동으로 붙이지 않는다.
- 배당/직원/최대주주/감사처럼 명시적인 report 질문에서만 report pivot/context를 올린다.

## Follow-up Continuity

- 후속 턴이 `최근 5개년`, `그럼`, `이어서`처럼 짧은 기간/연속 질문이면 직전 assistant `includedModules`를 이어받아 같은 분석 축을 유지한다.
- 이 상속은 아무 질문에나 적용하지 않고 `follow_up` 모드 + 기간/연속 힌트가 있을 때만 적용한다.
- 강한 direct intent 질문(`성격별 비용`, `인건비`, `감가상각`, `물류비`)은 clarification 없이 바로 `costByNature`를 회수한다.
- `costByNature` 같은 다기간 direct module이 포함되면 기간이 비어 있어도 최신 시점과 최근 추세를 먼저 답한다. 연도 기준을 먼저 다시 묻지 않는다.
