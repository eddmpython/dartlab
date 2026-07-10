---
id: recipes.meta.report.companyDeepAnalysis
title: 회사 종합 분석 (매크로 → 산업 → 회사 → 분해 → quality → valuation)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: 단일 회사의 깊이 있는 분석을 매크로 환경, 산업 위치, 회사 본질, ROE 분해, 회계 quality, 가치평가 6 단으로 엮는 절차. 마지막 valuation 단계 누락 시 종합 분석 미완료. 트리거 — '기업 깊이 분석', '6 막 종합', '단일 종목 deep dive'.
whenToUse:
  - 회사 종합 분석
  - 깊이 있는 회사 분석
  - 매크로와 회사를 같이 보고 싶을 때
  - 회사 분석 종합 보고서
  - 종목 깊이 분석
linkedSkills:
  - engines.macro
  - engines.analysis
  - engines.scan
  - engines.company
toolRefs:
  - EngineCall
  - RunPython
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - executionRef
  - sourceRef
visualRefs:
  - "engines.viz.kpiRibbon"
  - "engines.viz.financialStructureCharts"
  - "engines.viz.priceChart"
  - "engines.viz.peerMatrix"
  - "engines.viz.scenarioVisuals"
  - "engines.viz.evidenceCoverage"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "종합 보고서 첫 화면은 engines.viz.kpiRibbon으로 KPI 4~8개만 묶고 각 카드에 period·evidenceRef를 붙인다."
  - "재무제표 구조는 engines.viz.financialStructureCharts를 사용하고 IS/BS/CF 원표와 결산기·연결 기준이 맞을 때만 emit한다."
  - "가격·수급 반응은 engines.viz.priceChart로만 그리며 OHLCV 기간·벤치마크·latestAsOf가 맞지 않으면 본문 차트로 쓰지 않는다."
  - "동종 비교는 engines.viz.peerMatrix를 사용하고 universe·peerCount·metric 결손률을 답변에 함께 노출한다."
  - "stress·민감도·충격 전파는 engines.viz.scenarioVisuals를 사용하고 assumption grid 또는 수치 임계가 없으면 scenario table로 낮춘다."
  - "근거 충족도는 engines.viz.evidenceCoverage로 검산/한계 섹션에만 배치하고 결론 차트처럼 해석하지 않는다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

forbidden:
  - 6 단 절차 중 valuation 단계 (Step 6) 누락 시 종합 분석 미완료 — 절대 단정 금지.
  - peer 없는 절대값 (예 — 매출 12 조) 단독 노출 금지 — peer median / 5 년 평균 동반.
  - 단일 분기 결과를 영구 추세로 단정 금지 — 시계열 (5Y / 8Q) 동반.
  - 매크로 / 산업 / 회사 결과 연결 없이 단편적 언급 금지.
failureModes:
  - 6 단 중 일부 step 실패 시 다음 step 으로 silent skip
  - peer scan 결과 5 미만일 때 통계 의미 부족 무시
  - ROE DuPont 분해의 분모 (평균자본 vs 기말자본) 명시 누락
  - 회계 quality 점검을 단일 지표 (accruals 만) 로 단정
  - valuation peer 의 산업 동질성 검증 부족
examples:
  - 삼성전자 6 단 종합 분석
  - 신한지주 매크로 → 산업 → 회사 → quality → valuation
  - 대형 종목 deep dive
  - 6 막 인과 narrative 조립
gap:
  primary:
    - analysis
    - macro
  secondary:
    - scan
testUniverse:
  market: KR
  stockCodes:
    - "005930"
  asOfPolicy: latest
falsifier:
  description: "valuation 또는 quality 단계가 빠지면 회사 종합 분석 결론으로 사용하지 않는다."
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
---

## 공개 호출 방식

```python
import dartlab
import polars as pl

target = "005930"
c = dartlab.Company(target)

def latest_period(df):
    if hasattr(df, "columns"):
        for col in df.columns:
            if str(col)[:4].isdigit():
                return str(col)
    return "latest"

def compact(obj):
    if isinstance(obj, pl.DataFrame):
        return {"type": "DataFrame", "rows": obj.height, "columns": obj.width}
    if isinstance(obj, dict):
        return {"type": "dict", "keys": list(obj.keys())[:8]}
    return {"type": type(obj).__name__}

bs = c.panel("BS", freq="Y")
is_df = c.panel("IS", freq="Y")
ratios = c.panel("ratios")
profitability = c.analysis("profitability")
quality = c.analysis("earningsQuality")
valuation = c.analysis("valuation")

emit_result(
    table=[
        {"step": "macro", "skill": "engines.macro", "result": "read before company conclusion"},
        {"step": "company", "skill": "engines.company", "result": compact(bs)},
        {"step": "profitability", "skill": "engines.analysis", "result": compact(profitability)},
        {"step": "quality", "skill": "engines.analysis", "result": compact(quality)},
        {"step": "valuation", "skill": "engines.analysis", "result": compact(valuation)},
    ],
    values={"target": target, "bsRows": bs.height, "isRows": is_df.height, "ratioRows": ratios.height},
    date=latest_period(bs),
)
```

## 호출 동작

각 step 은 독립 capability 호출이며 실패해도 다음 step 은 진행한다. 단계마다 ref 가 누적된다.

1. `dartlab.macro()` — 금리·환율·경기 사이클 한 시점 (datasetRef + tableRef)
2. `dartlab.scan("profitability")` — peer 5~10 후보 (tableRef)
3. `Company(code).panel("BS")`/`show("IS")` — 재무제표 시계열 (tableRef + dateRef)
4. `Company.analysis("financial", "수익성")` — ROE DuPont 분해 (valueRef × N)
5. `Company.analysis("financial", "이익품질")` — 회계 quality (valueRef × N)
6. `Company.analysis("가치평가", "가치평가")` — PER·PBR·EV/EBITDA peer 비교 (valueRef × N + tableRef). 종합 분석에서 가치평가 단계 누락 = 미완료. peer 비교 없는 절대값 단독 노출 금지.

## 대표 반환 형태

총 ref:
- `tableRef` 5 개 (macro snapshot, peer scan, BS, IS, valuation peer multiple)
- `valueRef` 9+ 개 (ROE, 마진, 회전, 레버리지, 현금흐름 quality, 일회성 비중, PER, PBR, EV/EBITDA)
- `dateRef` 1 개 (분기 기준일)

## 연계 절차

1. engines.macro — 매크로 환경 (금리·환율·경기 사이클)
2. engines.scan — peer 후보 5~10 (수익성 축)
3. engines.company — 회사 진입 + show("BS") + show("IS")
4. engines.analysis — ROE DuPont 분해 (마진 × 회전 × 레버리지)
5. engines.analysis — 일회성·발생주의 점검
6. engines.analysis — PER/PBR/EV-EBITDA + peer 비교 (가치평가 axis)

## 기본 검증

- 답변에 숫자가 들어가면 valueRef 또는 tableRef 묶음 필수.
- 분기 기준은 dateRef 명시.
- peer 비교는 tableRef + 답변 본문에 evidence table 동시 노출.
- "12 조" 같은 절대값 단독 노출 금지 — peer median / 5 년 평균과 함께.

## AI 직접 사용 방식

1. `ReadSkill` 에서 사용자 질문과 `whenToUse`를 맞춰 이 recipe를 고른다.
2. `GetSkillBody` 로 본문 전체를 읽고 `linkedSkills` 순서대로 먼저 필요한 엔진 skill을 확인한다.
3. `## 공개 호출 방식`의 첫 Python 블록을 target만 바꿔 `ValidateRecipe(..., capture=False)`로 smoke 실행한다.
4. 실행 결과의 `skillRef`, `tableRef`, `valueRef`, `dateRef`, `executionRef` 중 누락된 근거가 있으면 답변을 작성하지 말고 호출 또는 근거 요구를 보강한다.
5. 답변은 결론, 핵심 근거, 메커니즘, 반례·한계, 후속 모니터링 순서로 작성하고 `falsifier.description`이 있으면 반례 단락에서 반드시 확인한다.
