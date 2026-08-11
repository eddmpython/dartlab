---
id: operation.sixActsAnalysis
title: 6 막 인과 서사 분석 절차
category: operation
purpose: 종목 분석을 6 막 인과 구조로 묶는 운영 절차. analysis · credit · macro · quant · industry 5 분석엔진을 story 조합기로 결합한다. AI/엔진 prompt 어디에도 모든 질문에 6 막 강제 X — 기업 분석 한정.
whenToUse:
  - 6 막 분석
  - 종합 보고서
  - "왜 마진이 이 수준인가"
  - "왜 이 회사 신용도가 이 등급인가"
  - 인과 추적
  - causal analysis
  - "스토리 보고서"
procedure:
  - 1 막 — 거시 (macro) — 이 회사가 속한 사이클·금리·환율·원자재 결정 인자
  - 2 막 — 산업 (industry) — 동종 산업 구조·성장률·peer 위치
  - 3 막 — 정량 (quant) — 31 축 7 그룹 요인 점수 (밸류·모멘텀·퀄리티 등)
  - 4 막 — 재무 (analysis) — 수익성·안정성·성장성·현금흐름 비율
  - 5 막 — 신용 (credit) — AAA~D 등급 + PD + 핵심 약점
  - 6 막 — 결론 (story) — 5 막의 인과를 한 줄로 묶기 + 가장 큰 리스크/기회 명시
examples:
  - "삼성전자 6 막 분석 보고서 만들어줘"
  - "이 회사 왜 영업이익률이 떨어지는지 인과로 보여줘"
  - "종합 평가 c.story()"
  - "스토리 보고서 출력"
expectedOutputs:
  - Story 객체 (6 막 텍스트 + 막별 evidence ref)
  - 막별 tableRef · valueRef · webRef
  - 각 막의 1 차 출처 (DART filing · EDGAR · FRED · 산업 데이터)
  - 결론 1 막의 한 줄 요약 + 핵심 risk/opportunity 3 개
requiredEvidence:
  - target (분석 대상 종목)
  - period (분석 기준 시점)
  - macroRef (1 막 거시 변수)
  - industryRef (2 막 산업 데이터)
  - quantRef (3 막 요인 점수)
  - analysisRef (4 막 재무 비율)
  - creditRef (5 막 등급)
  - storyRef (6 막 결론)
  - executionRef
  - sourceRef
failureModes:
  - 6 막 골격 강제로 분석 대상 부적합 (예 비상장 · 신생 회사 → 5 막 데이터 부족)
  - 막 사이 인과 연결 없이 5 분석 결과 *나열* 만
  - 6 막을 *모든 질문* 에 적용 (단순 수치 질의에도 6 막 보고서 출력 X)
  - 결론 1 막이 5 막 요약 *복붙* (인과 묶음 누락)
forbidden:
  - 단순 수치 질의 ("매출 얼마") 에 6 막 보고서 출력
  - 비기업 분석 (산업 자체 · 거시 자체) 에 6 막 적용
  - 5 분석 결과를 *나열* 만 하고 인과 연결 없음
  - 결손 데이터를 0 으로 채워 막을 *완성된 척*
knowledgeRefs:
  - engines.story
  - engines.analysis
  - engines.credit
  - engines.macro
  - engines.quant
  - engines.industry
  - operation.content
linkedSkills:
  - engines.panel
sourceRefs:
  - dartlab://skills/operation.sixActsAnalysis
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: supported
    notes: []
status: observed
lastUpdated: '2026-08-09'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

# 6 막 인과 서사 — 기업 분석 한정

## 무엇을 하나

종목 하나를 거시 → 산업 → 정량 → 재무 → 신용 → 결론 6 막 인과로 묶는다. 단순 수치 나열 (대시보드) 과 다른 결 — 숫자가 *왜* 그 수준인지 5 단계 위 (거시) 부터 *역방향* 으로 추적해 마지막 막에서 한 줄로 묶는다.

dartlab 의 두 번째 사상 — **숫자를 나열하면 대시보드가 되지만, 숫자의 인과를 연결하면 스토리가 된다** — 의 실행 표면.

**중요**: 본 절차는 기업 분석에만 적용한다. 단순 수치, 산업, 거시 질문에는 6막을 강제하지 않으며 UI와 AI prompt의 적용 범위는 `operation.content`를 따른다.

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")
story = c.story()                 # 6 막 자동
print(story.act(1))               # 1 막 거시
print(story.act(6))               # 6 막 결론
```

또는 dartlab.ask 자연어:

```python
dartlab.ask("삼성전자 종합 분석해줘")
# → LLM 이 자율적으로 c.story() 호출 → 6 막 답
```

## 막별 호출 매핑

| 막 | 엔진 | 입력 | 핵심 산출 |
|---|---|---|---|
| 1 — 거시 | `engines.macro` | 산업 · 시점 | 사이클 위상 · 금리 · 환율 · 원자재 |
| 2 — 산업 | `engines.industry` | 산업 코드 | 산업 성장률 · peer 분포 · 진입장벽 |
| 3 — 정량 | `engines.quant` | 종목 · 시점 | 31 축 요인 점수 · 7 그룹 종합 |
| 4 — 재무 | `engines.analysis` | 종목 · 기간 | 수익성 · 안정성 · 성장성 · 현금흐름 |
| 5 — 신용 | `engines.credit` | 종목 · 시점 | 등급 (AAA~D) · PD · 핵심 약점 3 개 |
| 6 — 결론 | `engines.story` | 1~5 막 ref | 인과 묶음 한 줄 + 핵심 risk/opportunity 3 |

## 인과 연결 절차

각 막은 *다음 막의 원인* 이어야 한다:

- 1 막 (사이클 후반) → 2 막 (산업 성숙기) → 3 막 (모멘텀 약화) → 4 막 (영업이익률 압박) → 5 막 (신용도 단기 안정) → 6 막 (장기 risk 우위).

결론 1 막은 *5 막 요약* 이 아니라 *5 막의 인과를 한 줄로 묶기*. "수익성 약화는 산업 성숙기 + 사이클 후반의 동시 압력이고, 신용도는 현금흐름 견고함으로 단기 방어되지만 장기 capex 부담이 핵심 risk".

## evidence 묶음 — Ref 검산 강제

각 막의 모든 수치는 ref 동행:
- `macroRef` — FRED · 한국은행 · 산업통상자원부
- `industryRef` — DART 산업 분류 · 매출 비중
- `quantRef` — 요인 회귀 결과
- `analysisRef` — DART filing 표 (`tableRef`)
- `creditRef` — 신용 모델 출력
- `storyRef` — 6 막 텍스트 자체

ref 없는 막은 출력 차단 (GATE).

## 다음 단계

- 막별 깊이 분석: `engines.analysis` · `engines.credit` · `engines.macro` · `engines.quant` · `engines.industry`.
- 여러 종목 6 막 비교: [engines.panel](/skills/engines.panel) 의 `dartlab.compare` + 막별 결합.
- 6 막을 카루셀 · 블로그 · 영상 콘텐츠로: `sns/CAROUSEL_DESIGN.md` · `blog/BLOG.md`.

## 무엇을 하지 *않는가*

- 단순 수치 질의에 6 막 강제 (대시보드 형식으로 답).
- 비기업 분석에 6 막 적용.
- 5 막 *나열* 만 (인과 연결 누락) 으로 6 막 결론 도출.
- 결손 채움으로 막을 *완성된 척* (NaN 유지가 정공법).

근본: `engines.story` · `engines.company` · `runtime.workbenchEvidenceFlow` "evidence 검산" · `operation.architecture`.
