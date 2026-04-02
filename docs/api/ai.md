---
title: AI
---

# AI — 적극적 분석가

dartlab 엔진(analysis, scan, gather, credit)을 도구로 조합하여
질문에 최적화된 분석 흐름을 스스로 설계하고 실행한다.

## 사용법

```python
import dartlab

# 자유 질문
dartlab.ask("삼성전자 재무건전성 분석해줘")
dartlab.ask("코스피 시장 동향은?")

# 종목 바인딩
dartlab.chat("005930", "배당 추세를 분석하고 이상 징후를 찾아줘")

# provider 지정
dartlab.ask("분석해줘", provider="gemini")
dartlab.ask("분석해줘", provider="oauthCodex")
```

## Provider

| Provider | 무료 | 모델 |
|----------|:---:|------|
| gemini | ✓ | Gemini 2.5 Pro/Flash |
| groq | ✓ | LLaMA 3.3 70B |
| cerebras | ✓ | LLaMA 3.3 70B |
| mistral | ✓ | Mistral Small |
| openai | 유료 | GPT-4o |
| ollama | 로컬 | 모델 선택 |
| oauthCodex | OAuth | GPT-5.4 |

## 설정

```bash
dartlab setup              # 대화형 설정
dartlab setup gemini       # Gemini API 키 설정
dartlab status             # provider 상태 확인
```

## AI가 사용하는 도구

AI는 코드를 생성하고 실행하여 답을 찾는다:

```python
# AI가 내부적으로 실행하는 코드 예시
c = dartlab.Company("005930")
r = c.analysis("financial", "수익성")     # 수익성 데이터
cr = c.credit(detail=True)               # 신용평가 데이터
news = newsSearch("삼성전자", days=7)     # 최근 뉴스
# → AI가 결과를 읽고 인과 해석을 직접 구성
```

## AI 분석 원칙

- **6막 서사 구조**: 사업이해 → 수익성 → 현금 → 안정성 → 자본배분 → 전망
- **인과 연결**: 숫자 나열이 아니라 "왜"를 설명
- **코드 투명성**: AI가 실행한 코드를 사용자에게 보여줌
- **교차 검증**: 재무 + 뉴스, IS + CF + BS 조합
