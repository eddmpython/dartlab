# Self-AI — dartlab 자체 AI 진화 엔진

dartlab의 AI가 외부 LLM 의존에서 벗어나 자체 금융분석 전문 AI로 진화하는 시스템.
코드를 생성하고, sandbox에서 실행하고, 실행 결과로 학습하는 ACG(Action Code Generation) 폐쇄 루프.

| 항목 | 내용 |
|------|------|
| 레이어 | L3 (ai/ 하위) |
| 패키지 | `src/dartlab/ai/selfai/` |
| 의존 | ai/runtime, ai/tools, audit, CAPABILITIES |
| 생산 | 에러 패턴 DB, 스킬 라이브러리, 학습 데이터, LoRA 가중치 |

## 아키텍처

```
질문 → [Output Validator] → [Skill Library few-shot 주입] → LLM → 코드 생성
                                                                    ↓
                                                              sandbox 실행
                                                                    ↓
                                                    [Reflexion] ← 에러 발생 시
                                                         ↓
                                                 error_patterns.db 검색
                                                         ↓
                                                 복구 힌트 + correct_code 주입
                                                         ↓
                                                    LLM 재시도
```

## Phase 로드맵

| Phase | 기간 | 핵심 | 상태 |
|-------|------|------|------|
| 1 | 3일 | Reflexion + Error Pattern DB | **완료** |
| 2 | 1주 | Skill Library + Output Validator + Few-Shot | **완료** |
| 3 | 1개월 | 초소형 도구 라우터 + Ollama qwen3:1.7b | **동작 중** (16/16=100%) |
| 4 | 3개월 | MoE-LoRA + Task Arithmetic | 대기 |
| 5 | 6개월~ | Agent0 자율 진화 + Curriculum | 대기 |

## Phase 1: Reflexion + Error Pattern DB

에러 발생 시 유사 에러의 올바른 코드를 주입. 가중치 변경 없음.

### 패키지 구조
```
src/dartlab/ai/selfai/
├── __init__.py
├── reflexion.py          -- enrich_error_feedback()
├── error_patterns.py     -- SQLite 에러 패턴 DB
└── audit_analyzer.py     -- audit 데이터 → error_patterns.db
```

### error_patterns.db

```sql
error_pattern (
    id, error_type, error_signature, wrong_code, correct_code,
    tool_name, frequency, last_seen
)
```

### core.py 통합 지점

`_streamWithCodeExecution()` 528~534줄 에러 피드백에 `enrich_error_feedback()` 삽입.

## Phase 2: Skill Library + Output Validator + Few-Shot

### 패키지 구조
```
src/dartlab/ai/selfai/
├── ...Phase 1...
├── skill_library.py      -- 성공 코드 저장/검색 (SQLite, 8개 seed)
├── output_validator.py   -- 코드 실행 전 정적 의미 검증 (11개 규칙)
└── few_shot.py           -- 질문→스킬 매칭 → 프롬프트 동적 주입
```

### core.py 통합 지점

1. `_buildSystemPromptParts()` 후 — few-shot 블록 동적 주입
2. `_streamWithCodeExecution()` 코드블록 감지 후 — output validator로 실행 전 차단

### Output Validator 규칙 (11개)

| 규칙 | 차단 대상 |
|------|----------|
| analysis 1인자 | `c.analysis("수익성")` → 2인자 필수 |
| macro keyword arg | `macro(topic=...)` → 위치인자만 |
| c.sections 접근 | 409MB 메모리 위험 |
| review 남용 | 분석에서는 analysis 우선 |
| scan join | 타임아웃 위험 |
| Polars .empty/.iterrows/.sort_values/.to_dict | pandas 혼용 차단 |
| import dartlab | 중복 import |
| requests 직접 사용 | newsSearch/webSearch 사용 |

### 초기 에러 패턴 (audit에서 추출)

| 에러 | wrong | correct | 빈도 |
|------|-------|---------|------|
| analysis 인자 1개 | `c.analysis("수익성")` | `c.analysis("financial", "수익성")` | 높음 |
| macro keyword arg | `macro(topic="종합")` | `dartlab.macro("종합")` | 높음 |
| 없는 키 접근 | `result["cycle"]` | `print(result.keys())` 먼저 | 높음 |
| review 남용 | `c.review("수익성")` | `c.analysis("financial", "수익성")` | 중간 |
| Polars pandas 혼용 | `df.empty` | `df.height == 0` or `len(df) == 0` | 중간 |
| sections 직접 접근 | `c.sections` | `c.show("IS")` | 낮음 |

## Phase 3: 초소형 도구 라우터 + 고속 추론

### 핵심 발견 (2026-04 조사)

- **Qwen3 1.7B**가 도구 호출 점수 **0.960** (1위). 32B 모델이 필요 없다
- **ExLlamaV2/V3**가 Ollama 대비 30~52% 빠름 (MLPerf 2026 로컬 1위)
- **xLAM-1b** (Salesforce): 1.35B로 BFCL 78.94%. 도구 호출 전용

### 2단계 아키텍처

```
[사용자 질문]
     ↓
[Stage 1: 도구 라우터] ← Qwen3 1.7B (~1.2GB, GPU에서 200+ t/s)
  → 도구 선택 + 코드 생성 (analysis/scan/macro 등)
     ↓
[Output Validator] ← Phase 2 정적 검증 (실행 전 차단)
     ↓
[DartlabCodeExecutor] ← sandbox 실행
     ↓
[Stage 2: 해석기] ← 외부 LLM (Gemini/GPT) 또는 Qwen2.5-Coder-7B
  → 실행 결과 해석 + 6막 서사 구성
```

**왜 2단계인가:**
- 도구 선택은 **패턴 매칭** — 1.7B로 충분 (0.960 정확도)
- 해석은 **추론+언어** — 큰 모델이 유리 (외부 LLM 또는 7B)
- 도구 라우터가 맞으면 해석기의 부담이 극적으로 줄어듦

### 추론 엔진: ExLlamaV2 (Ollama 대체)

| 항목 | Ollama | ExLlamaV2 |
|------|--------|-----------|
| 속도 | 기준 | **+30~52%** |
| 양자화 | GGUF Q4 | EXL2 per-layer 비트 배분 |
| API | REST | Python API (직접 통합) |
| speculative decoding | X | O |

### 모델 조합

| 역할 | 모델 | 크기 | VRAM |
|------|------|------|------|
| 도구 라우터 | Qwen3-1.7B Q4 | ~1.2GB | 2GB |
| 코드 생성 | (라우터와 동일 또는 Qwen2.5-Coder-7B) | ~4.5GB | 6GB |
| 해석기 | 외부 LLM (Gemini/GPT) 또는 로컬 7B | 가변 | 가변 |

### 패키지 구조
```
src/dartlab/ai/selfai/
├── ...Phase 1-2...
├── router/
│   ├── __init__.py       -- 도구 라우터 진입점
│   ├── model.py          -- 로컬 모델 로드/추론 (ExLlamaV2)
│   └── prompt.py         -- 라우터 전용 프롬프트
├── apigen/
│   ├── question_gen.py   -- CAPABILITIES → 질문 생성
│   ├── code_gen.py       -- 질문 + API spec → 코드 생성
│   ├── verifier.py       -- sandbox 실행 검증
│   └── dataset.py        -- SFT 데이터셋 구축
└── training/
    └── trainer.py        -- Unsloth QLoRA → GGUF/EXL2
```

## Phase 4~5

상세: `.claude/plans/merry-sauteeing-quill.md`

## 검증

| Phase | 방법 | 기준 |
|-------|------|------|
| 1 | auditAi 32개 재실행 | hasError 30%↓ |
| 2 | 32개 + 정적 검증 | 도구 오선택 50%↓ |
| 3 | holdout 100개 | 도구 정확도 90%↑ |

## 관련 코드

| 파일 | 역할 |
|------|------|
| `src/dartlab/ai/selfai/` | Self-AI 패키지 |
| `src/dartlab/ai/runtime/core.py` | 통합 지점 (에러 피드백) |
| `src/dartlab/ai/tools/coding.py` | sandbox (DartlabCodeExecutor) |
| `data/dart/auditAi/` | audit 데이터 |
| `scripts/auditAi.py` | 감사 실행기 |
