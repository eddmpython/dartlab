# AI

LLM 기반 적극적 분석가.
dartlab 엔진(analysis, scan, gather 등)은 AI가 호출하는 **도구**다.
AI는 이 도구를 조합해 질문에 최적화된 분석 흐름을 스스로 설계하고,
실행 과정(코드 + 결과)을 사용자에게 투명하게 보여줘서
사용자가 분석 방법 자체를 학습할 수 있게 돕는다.

| 항목 | 내용 |
|------|------|
| 레이어 | L3 |
| 진입점 | `dartlab.ask()`, `dartlab.chat()`, `c.reviewer()` |
| 소비 | analysis, macro, scan, gather, review, Company 전체 |
| 생산 | 사용자에게 해석 + 재현 가능한 코드 제공 |
| provider | gemini, groq, cerebras, mistral, openai, ollama |

## 설계 원칙

- **AI가 분석의 전 과정을 주도** — 데이터 수집, 계산, 판단, 해석, 보고서까지 AI가 수행
- dartlab 엔진은 AI가 호출하는 도구 — AI가 도구를 조합해서 질문에 최적화된 흐름을 스스로 설계
- **CAPABILITIES-Driven**: 코드블록 자동실행. 데이터는 코드가 가져온다.
- **사용자 학습 지원** — AI가 실행하는 코드와 결과를 투명하게 보여준다. 사용자는 답만 얻는 게 아니라 분석 방법을 배운다.
- **함수 제공** — 사용자가 직접 실행할 수 있는 코드를 적극 제공한다. "이렇게 하면 됩니다"가 아니라 "이 코드를 실행하세요"다.
- **모든 provider에서 기본 기능 동작** — 도구 호출 불가 시 코드 실행으로 보충
- defaultProvider 기본 = 없음

## Provider

**무료 API 키 provider:**

| Provider | 무료 티어 | 모델 |
|----------|-----------|-------|
| `gemini` | Gemini 2.5 Pro/Flash | Gemini 2.5 |
| `groq` | 6K-30K TPM | LLaMA 3.3 70B |
| `cerebras` | 1M tokens/day | LLaMA 3.3 70B |
| `mistral` | 1B tokens/month | Mistral Small |

**유료/기타:**

| Provider | 인증 | Tool Calling |
|----------|------|:---:|
| `openai` | API key | O |
| `ollama` | 로컬 | 모델 의존 |

## API

```python
dartlab.ask("삼성전자 재무건전성 분석해줘")
dartlab.ask("분석", provider="openai", model="gpt-4o")
dartlab.chat("005930", "배당 추세를 분석하고 이상 징후를 찾아줘")
```

## Spec 관리 체계

- 각 엔진 폴더에 `spec.py` — 해당 엔진의 메타데이터 선언
- `ai/spec.py` — 총괄 수집기, 각 엔진 spec 합산
- 코드에서 자동 추출 — 수동 동기화 불필요
- `test_spec_integrity.py` — CI에서 spec-코드 불일치 검증
- `/api/spec` 엔드포인트로 MCP/외부 클라이언트도 사용 가능

## AI 분석 능력

### 도구 선택 (60+ 질문 검증)
- **개별 기업 분석**: review/analysis 축 정확 매칭 (1회 성공)
- **매크로 환경 질문**: `dartlab.macro("축")` — 시장 레벨 매크로 해석 (Company 불필요)
- **시장 비교/순위**: scan 단일 축 + filter
- **데이터 직접 조회**: show/select (배당, 매출 추이, 주석 등)
- **주석 상세**: c.notes.xxx (재고/차입금/유형자산 등 12항목)
- **실시간 이슈**: newsSearch + gather("news") 교차 검증
- **웹서치 자발 사용**: 분석 부족 시 자동으로 newsSearch/webSearch 보충

### 데이터 품질
- **마크다운 테이블 출력**: Polars 유니코드 → GFM 마크다운 자동 변환
- **원본 데이터 투명 제공**: 결과를 숨기지 않고 사용자에게 그대로 보여줌
- **analysis notes enrichment**: 자산구조/비용구조에 주석 상세 포함

### 성능
- **calc 캐시 공유**: @memoized_calc 120개 함수. analysis↔review 중복 계산 제거
  - 가치평가: 4초→0.09초 (97%↓), 매출전망: 1.5초→0.07초 (95%↓)
- **review 최대 3개 제한**: 타임아웃(60초) 방지
- **느린 축 회피**: 투자효율/가치평가/매출전망은 필요시만

### 해석 품질
- **축 정확 매칭**: "비용구조" → analysis("financial", "비용구조") (다른 축 조합 금지)
- **scan 결과 AI 판단**: 하드코딩 필터 없이 기저효과/이상치를 해석으로 설명
- **교차 검증**: 재무 + 뉴스, IS + CF + BS, notes + analysis 조합

## Audit

- 저장: `data/dart/auditAi/`
- AI audit = dartlab 최종 레이어 품질 검증
- 모든 하위 엔진(Company, sections, notes, analysis, scan, gather) 문제가 여기서 표면화
- 실행 → 분류(P/T/C/V) → 수정 → 재실행 → 기록

## 관련 코드

- `src/dartlab/ai/` — providers, tools, runtime, memory, conversation
- `src/dartlab/ai/runtime/core.py` — 시스템 프롬프트, 코드 실행, 마크다운 변환
- `src/dartlab/analysis/financial/_memoize.py` — calc 캐시 데코레이터
