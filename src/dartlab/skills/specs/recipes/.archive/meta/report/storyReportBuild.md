---
id: recipes.meta.report.storyReportBuild
title: story 보고서 조립 (분석 14 축 + 인과 + 종합 보고)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: 회사 종합 보고서를 14 축 분석 + 6 막 인과 + story 섹션 조립으로 만드는 절차. review 엔진의 표준 출력. 트리거 — '보고서 작성', '기업 이야기 조립', 'story 빌드'.
whenToUse:
  - 종합 보고서
  - story 보고서
  - 회사 종합 분석 보고
  - 14 섹션 보고서
  - 인과 분석
  - 분석 보고서 작성
  - 회사 분석 종합 글
linkedSkills:
  - engines.company
  - engines.story
  - engines.analysis
toolRefs:
  - EngineCall
  - RunPython
requiredEvidence:
  - skillRef
  - tableRef
  - dateRef
  - executionRef
  - sourceRef
visualRefs:
  - "engines.viz.kpiRibbon"
  - "engines.viz.evidenceCoverage"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "종합 보고서 첫 화면은 engines.viz.kpiRibbon으로 KPI 4~8개만 묶고 각 카드에 period·evidenceRef를 붙인다."
  - "근거 충족도는 engines.viz.evidenceCoverage로 검산/한계 섹션에만 배치하고 결론 차트처럼 해석하지 않는다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

forbidden:
  - 투자 추천 같은 단정 본문 금지 — analysis 결과 그대로 표현.
  - 부분 섹션 호출 시 다른 섹션 추측 금지 — 그 섹션 한정.
  - 인과 가중치 / scorecard 없이 단편 섹션 단정 금지.
  - 보고서 본문 인용 시 출처 ref 누락 금지.
failureModes:
  - 14 섹션 중 일부 결손 시 silent skip
  - causal weights 임의 가정 vs 실제 모델 가중치 차이
  - 부분 섹션 (예 — 수익구조 만) 결과를 전체 회사 종합으로 오인
  - 산업 / 시장 환경 미반영한 회사 단독 결론
  - story narrative 의 사실 + 해석 경계 모호
examples:
  - 삼성전자 14 섹션 종합 보고서
  - 신한지주 부분 섹션 (수익구조)
  - causal weights + scorecard 결합
  - story 보고서 + 출처 ref
gap:
  primary:
    - story
    - analysis
lastUpdated: '2026-05-13'
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")

scorecard = c.analysis("financial", "종합평가")
story_full = c.story()
story_section = c.story("수익구조")
causal = c.story()  # 6 막 서사 (causalWeights 는 내부 산출물이라 계약이 아니다)
```

## 호출 동작

14 축 분석 종합평가 → causal 가중치 → story 14 섹션 조립 → 보고서 markdown 출력. 개별 섹션만 필요하면 story(section) 으로 부분 호출.

1. 회사 진입
2. analysis("financial", "종합평가") — 14 축 등급 종합
3. causalWeights() — 인과 가중치
4. story() — 14 섹션 보고서 조립 (또는 story(section) 부분)
5. 결과 markdown 본문 + 핵심 ref 합산

## 대표 반환 형태

- `tableRef` 1+ 개 (scorecard 14 축)
- 답변 본문에 markdown 14 섹션 (또는 부분 섹션)
- `dateRef` 1 개

## 연계 절차

1. engines.company — 회사 진입
2. engines.analysis — 14 축 종합평가
3. engines.story — 인과 가중치
4. engines.story — 14 섹션 보고서

## 기본 검증

- 보고서 본문 인용 시 출처 ref (각 섹션 → tableRef + valueRef) 명시.
- 부분 섹션 호출 시 그 섹션 한정 — 다른 섹션 추측 X.
- 인과 가중치는 "왜 이 섹션이 중요한가" 의 정량 근거.
- "투자 추천" 같은 단정 본문 X — analysis 결과를 그대로 표현.
