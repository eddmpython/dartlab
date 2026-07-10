---
id: start.firstAnalysisRecipe
title: 첫 회사 분석 recipe — install → quickStart → Company → Analysis
kind: recipe
scope: builtin
status: observed
category: start
purpose: dartlab 처음 마주친 사람·AI 가 환경 준비부터 첫 회사 재무 분석까지 4 단계 순서로 한 번에 통과하는 recipe. 각 단계는 별도 skill 을 가리키고, 끝나면 시장 횡단 (scan) 또는 가치평가 (valuation) 로 분기 가능.
whenToUse:
  - dartlab 처음 깔고 무엇을 해봐야 하나
  - 첫 회사 분석 절차
  - 8 분 demo
  - install 부터 분석까지 순서
  - dartlab 새 사용자 온보딩
  - 외부 LLM 첫 진입 후 무엇부터
inputs:
  - 운영체제 (Windows · macOS · Linux)
  - 분석 대상 종목코드 (한국 6 자리 또는 미국 ticker)
outputs:
  - 작동하는 dartlab 환경
  - 첫 Company 객체 + 재무제표 결과
  - 22 축 분석 중 1 축 결과
  - 다음 단계 분기 후보
linkedSkills:
  - start.installUv
  - start.quickStart
  - engines.company
  - engines.analysis
recipeSteps:
  - skillId: start.installUv
    note: uv 설치 → 가상환경 → uv add dartlab → import 검증.
  - skillId: start.quickStart
    note: Company / topics/panel / scan / ask 8 단계 walkthrough.
  - skillId: engines.company
    note: 단일 기업 facade 로 topics · panel · trace · diff · 하위 엔진 호출.
  - skillId: engines.analysis
    note: 수익성 · 성장성 · 안정성 · 가치평가 22 축 중 선택해 분석.
sourceRefs:
  - dartlab://skills/start.firstAnalysisRecipe
requiredEvidence:
  - 각 단계 완료 결과
  - 첫 Company target / period / topic
  - executionRef
  - sourceRef
expectedOutputs:
  - 첫 분석 결과
  - 다음 단계 분기 (scan · macro · story)
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
    notes:
      - 1 단계 (install) 는 로컬 Python 한정. 웹은 Colab 또는 hosted runtime 으로 우회.
  pyodide:
    status: limited
    notes:
      - install 단계는 Pyodide 적용 안 됨. 2~4 단계는 데이터 snapshot 에 따라 동작.
failureModes:
  - 1 단계 (install) 건너뛰고 바로 Company 호출
  - uv run python 대신 시스템 python 사용
  - 미국 ticker 와 한국 종목코드 혼동 (`Company("AAPL")` vs `Company("005930")`)
  - 재무 분석 결과의 결손을 0 으로 채움
forbidden:
  - 환경 검증 없이 분석 실행하지 않는다.
  - 결손값을 0 으로 대체하지 않는다.
examples:
  - dartlab 처음 깔았는데 뭐부터 해야 해
  - 8 분 안에 dartlab 으로 회사 분석 한 번 해보기
  - 처음 LLM 이 dartlab 으로 첫 분석
  - 새 사용자 온보딩 4 단계
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: "2026-05-06"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

dartlab 을 처음 만나는 사람·AI 가 **환경 준비 → walkthrough → 회사 facade → 분석 축 적용** 4 단계로 첫 결과까지 도달하는 recipe. 각 단계는 별도 skill 을 가리키고, 끝나면 다음 분기 (시장 횡단 · 매크로 · 스토리) 로 자연 이어진다.

## 무엇을 만드나

| 단계 | 산출물 |
|---|---|
| 1 | 작동하는 dartlab 환경 (uv + Python 3.12 + dartlab) |
| 2 | Company · Scan · Ask 8 단계 walkthrough 통과 |
| 3 | 단일 회사 facade — topics · panel · trace · diff |
| 4 | 22 축 중 1 축 분석 결과 (수익성 · 가치평가 · 성장성 등) |

## 연계 절차

1. start.installUv — uv 로 dartlab 환경 준비. `uv add dartlab` 후 `Company("005930")` import 검증.
2. start.quickStart — 8 단계 walkthrough 로 Company / topics / panel / scan / ask 의 호출 흐름을 한 번에 통과.
3. engines.company — 단일 기업 facade. `c.panel` · `c.panel("BS")` · `c.trace("BS")` 로 회사 격자와 source priority 이해.
4. engines.analysis — 22 분석 축 중 하나 선택 (`c.analysis("financial", "수익성")` 또는 `c.analysis("valuation", "가치평가")`).

## 단계별 핵심 호출

```python
import dartlab

# 단계 3 — 회사 facade
c = dartlab.Company("005930")
c.panel.shape                    # 항목 x 기간 격자 크기
c.panel("BS")                     # 재무상태표 (source priority 적용)
c.trace("IS")                    # 손익 데이터가 어느 출처에서 왔나

# 단계 4 — 분석 축
result = c.analysis("financial", "수익성")
print(result)
```

## 검증 게이트

각 단계가 끝났을 때 다음을 확인:

| 단계 | 검증 항목 |
|---|---|
| 1 | `uv run python -X utf8 -c "import dartlab; print(dartlab.__version__)"` 가 버전 출력 |
| 2 | `c.panel("IS")` 가 손익계산서 DataFrame 반환 |
| 3 | `c.trace("BS")` 가 finance source 선택 확인 |
| 4 | analysis 결과의 `tableRef` · `valueRef` · `dateRef` · `executionRef` 가 묶여 있음 |

## 다음 분기

4 단계까지 끝나면 다음 중 하나로:

- **시장 횡단** — `dartlab.scan("ratio", "roe")` 또는 [engines.scan](/skills/engines.scan) 에서 19 축 중 선택.
- **매크로 환경** — [engines.macro](/skills/engines.macro) 군 12 축으로 거시 위치 잡기.
- **스토리 보고서** — `c.story()` 로 구조화 보고서 + 보강은 [engines.story](/skills/engines.story).
- **가치평가 깊이** — [engines.quant](/skills/engines.quant) 의 damodaranValuation axis 로 DCF.
- **AI workflow** — [runtime.workbenchEvidenceFlow](/skills/runtime.workbenchEvidenceFlow) 로 자연어 분석.

## 다음 단계

- [start.dartlabSkillOs](/skills/start.dartlabSkillOs) — Skill OS 5 카테고리 + 검증 게이트.
- [start.useSkillsCatalog](/skills/start.useSkillsCatalog) — 검색 → 선택 → 검증 → 실행 패턴.
- [Skills 카탈로그](/skills) — 179 개 skill 검색.
