---
id: runtime.promptingPatterns
title: Prompting Patterns — 6 막 인과 + axis 카탈로그
kind: curated
scope: builtin
status: drafted
category: runtime
purpose: dartlab 답변 prompt 패턴 카탈로그 — 6 막 인과 (회사분석 한정), recipe 카탈로그 호출 시 prompt 변형, untrusted wrap 가이드, evidence GATE 통과 강행 prompt. agent.py system prompt 의 변형 SSOT.
whenToUse:
  - prompting patterns
  - 6 막 인과
  - prompt 변형
  - system prompt
  - 답변 패턴
inputs:
  - 사용자 질문 분류
  - recipe / engine axis
outputs:
  - prompt 변형 (회사분석 / 매크로 / 횡단)
toolRefs: []
knowledgeRefs:
  - runtime.workbenchEvidenceFlow
  - engines.story
sourceRefs:
  - dartlab://skills/runtime.promptingPatterns
requiredEvidence:
  - skillRef
  - executionRef
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
    status: limited
linkedSkills:
  - engines.story
  - runtime.workbenchEvidenceFlow
  - runtime.untrustedContent
---

## 분류

### 1. 회사분석 — 6 막 인과 (engines.story)

회사 단위 답변 한정. 모든 질문에 6 막을 강제하지 않는다. 회사분석 의도 (`Company.panel` / `Company.analysis`) 와 `engines.story` / `operation.sixActsAnalysis` 경로에서만 적용한다.

```
1막 — 산업 위치 (engines.industry.peers + supplyChain)
2막 — 재무 현황 (engines.analysis 22 axis)
3막 — 이익품질 (engines.analysis.forensics)
4막 — 자금조달 (engines.credit + altman)
5막 — 종합평가 (piotroski + qmj + valuation)
6막 — 시장분석 (engines.quant + scan)
```

### 2. 매크로 — axis 가이드 우선

`dartlab.macro()` 가이드 12 axis 먼저 → 사용자 의도 매칭 axis 선택 → 단위/dateRef 강행.

### 3. 횡단 (scan) — universe 정의 강행

universe 명시 (default KOSPI200 / 사용자 보유 list) → 횡단 axis 결과 정렬 → top N 인용.

### 4. recipe 호출 — 카탈로그 SSOT 인용

recipe id (`recipes.macro.qualityMacroBeta` 등) 명시 호출 → 결과의 `## 연계 절차` 다음 단계 자동 제안.

## 강행 prompt 요소

설치형 runtime의 `analysisCapsule.py`는 "이 세션에 제공된 DartLab 도구"를 사용하도록 안내한다. Codex와 Claude의 세션 직접 연결은 MCP 설치를 사용자에게 요구하지 않는다. 도구 transport와 관계없이 같은 Skill OS, EngineCall, 근거 계약을 따른다. 인증·모델·대화 기록은 사용자 CLI가 소유한다.

단순 수치 확인은 `EngineCall`의 `Company.panel`과 `PeerCompareN`에 `includeContext=false`를 지정한다. 이때 표·값·기간·공시 링크는 유지하고 신용·산업 부가 계산을 생략한다. 투자 판단 질문은 관련 분석 계약을 사용하며 기존 `includeContext=true` 동작도 유지한다. 인자 이름은 ReadSkill에 inline된 실제 callable 계약에서 확인하고 추측하지 않는다.

`ReadSkill`은 기본 세 후보의 짧은 절차와 실행 계약을 반환한다. 일반 분석에서는 operation, start,
runtime 문서를 제외하며, 개발·운영 문서 검색은 `audience="all"`로 요청한다. 본문 전문은
`GetSkillBody(skillId)`로 읽는다. API 설명과 본문을 여러 곳에 반복해서 펼치지 않는다.

native 세션에서 `EngineCall`의 표는 `data.table.tableId`, DataHub partition은 `data.tables`로
후속 계산에 연결된다. `QueryTable(tables={"t": tableId}, sql="SELECT ... FROM t")`는 같은 세션의
표 전체에서 필터, 정렬, 비율, window와 join을 실행한다. SQL은 메모리 표를 읽는 한 문장으로
제한되며, 새 원천 수집이나 파일 쓰기는 수행하지 않는다. 표의 schema, 조회 범위, 원자료 ref와
내용 hash를 보존하고 계산 결과에도 SQL과 입력 근거를 남긴다. 미리보기 행만으로 전종목 순위를
추정하지 않는다. 기간, 단위, 연결·별도 기준을 맞춰 계산한다.

후속 계산 표는 세션별 최대 8개, 표당 4 MiB로 제한한다. 닫힌 세션의 표는 해제되고 만료된
tableId는 다시 조회하도록 안내한다. QueryTable 결과가 잘리면 그 일부를 새 전체 표로 저장하지
않는다. DataHub의 partial partition은 전체 universe를 대표한다고 설명하지 않는다.

"큰 회사"처럼 비교축이 모호하면 매출, 자산, 시가총액을 구분하고 실제 선택한 기준과 비교
범위를 답변에 밝힌다. 데이터에서 확인할 수 없는 축을 추측으로 채우지 않는다.

모든 prompt 변형에 다음 4 요소 강행:

1. **단위 명시** (% / bp / index / 원).
2. **dateRef** (YYYY-MM-DD 또는 YYYY-MM).
3. **evidence GATE** (skillRef / tableRef / valueRef 묶음).
4. **untrusted wrap** (외부 본문 시 sentinel 마커).

## 안티패턴

- 모든 질문 6 막 강제 (회사분석 외 trigger 금지).
- "최신" 단어 사용 시 dateRef 누락 (search dataAsOf stale 회귀).
- recipe 호출 결과 dump (`## 연계 절차` 무시 회귀).

## 기본 검증

본 spec 패턴 변경 시 agent.py system prompt 동시 갱신 (단일 SSOT 강행).
