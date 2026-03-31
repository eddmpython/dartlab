# AI

LLM 기반 적극적 분석가.
dartlab 엔진(analysis, scan, gather 등)은 AI가 호출하는 **도구**다.
AI는 이 도구를 조합해 질문에 최적화된 분석 흐름을 스스로 설계하고,
실행 과정(코드 + 결과)을 사용자에게 투명하게 보여줘서
사용자가 분석 방법 자체를 학습할 수 있게 돕는다.

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

## Audit

- 저장: `data/dart/auditAi/`
- 실제 기업에 ask/chat 실행 → 응답 품질 판단 → 프롬프트/도구 개선

## 관련 코드

- `src/dartlab/ai/` — providers, tools, runtime, memory, conversation
