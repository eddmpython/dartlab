---
id: recipes.fundamental.quality.cashflowGovernanceDualSignal
title: 현금흐름 품질 × 거버넌스 감사 동시 적신호
category: recipes
kind: recipe
scope: builtin
status: drafted
purpose: accrual ratio (현금흐름 vs 회계이익 갭) + governance amber (이사회 독립성 / 특수관계자) + audit-change (감사인 변경) 3 신호 동시 발현 시 분식 / 회계 신뢰도 적신호. Dechow et al (2011) "Predicting Material Accounting Misstatements" 학술 결과 적용. analysis ↔ scan 격리 메우는 조합. 트리거 — '분식 의심', '회계 신뢰도', 'accrual governance audit'.
whenToUse:
  - 분식 의심 종목
  - 회계 신뢰도 적신호
  - accrual governance
  - 감사 리스크
linkedSkills:
  - engines.company
  - engines.analysis
  - engines.scan
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
  - "engines.viz.cashflowWaterfall"
  - "engines.viz.financialStructureCharts"
  - "engines.viz.evidenceCoverage"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "현금흐름·배당·자본배분 bridge는 engines.viz.cashflowWaterfall을 사용하고 CF 원표와 부호 convention을 검산한다."
  - "재무제표 구조는 engines.viz.financialStructureCharts를 사용하고 IS/BS/CF 원표와 결산기·연결 기준이 맞을 때만 emit한다."
  - "근거 충족도는 engines.viz.evidenceCoverage로 검산/한계 섹션에만 배치하고 결론 차트처럼 해석하지 않는다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

gap:
  primary:
    - analysis
    - scan
testUniverse:
  market: KR
  stockCodes:
    - "005930"
    - "000660"
    - "035420"
    - "051910"
    - "055550"
  asOfPolicy: latest
falsifier:
  description: triple flag 종목의 3y 재무재작성 (restatement) 률이 unflagged 보다 낮으면 모델 inverted
  pythonCheck: |
    assert restatement_rate(triple_flagged) > restatement_rate(unflagged)
expectedNovelty:
  - tripleFlag
  - accrualPercentile
forbidden:
  - 단일 신호 (accrual 만) 로 분식 단정 금지.
  - 감사인 변경 = 분식 단정 금지 — 정상 rotation 도 있음.
failureModes:
  - accrual ratio 가 산업 평균 (제조업 vs 서비스) 차이 무시.
  - governance amber 정의가 회사 size / industry 별 thresholds 다름.
examples:
  - 삼성전자 accrual + governance + audit triple
  - HMM 회계 신뢰도 적신호
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

earnings_quality = c.analysis("earningsQuality")
cashflow = c.analysis("cashflow")
governance = c.analysis("governance")
cf = c.panel("CF", freq="Y")

def ready(obj):
    if isinstance(obj, pl.DataFrame):
        return not obj.is_empty()
    return bool(obj)

dual_flags = [ready(earnings_quality), ready(cashflow), ready(governance)]
emit_result(
    table=[
        {"signal": "earningsQuality", "result": compact(earnings_quality)},
        {"signal": "cashflow", "result": compact(cashflow)},
        {"signal": "governance", "result": compact(governance)},
    ],
    values={"target": target, "flagCount": sum(dual_flags), "tripleFlag": all(dual_flags)},
    date=latest_period(cf),
)
```

## 호출 동작

1. `c.analysis("earningsQuality")` — accrual ratio + FCF/NI 비율.
2. `c.analysis("governance")` — 이사회 독립성 + 특수관계자 비중.
3. `dartlab.scan("audit")` — 최근 2 년 감사인 변경 여부.
4. 3 신호 boolean 결합 → triple flag.

## 대표 반환 형태

`pl.DataFrame` — 컬럼:
- `accrualRatio : float` · `highAccrual : bool`
- `fcfNiRatio : float`
- `boardIndependence : float` · `relatedPartyRatio : float` · `govAmber : bool`
- `auditChanged : bool`
- `flagCount : int (0~3)` · `tripleFlag : bool`

## 연계 절차

1. 본 recipe → triple flag 종목 식별.
2. tripleFlag = True → `recipes.fundamental.credit.quantConsensus` 와 결합 — Beneish M-score 분식 신호와 교차 검증.
3. universe 적용 → `recipes.fundamental.governance.auditNetwork` 로 cross-sectional flag.

## 기본 검증

- `ValidateRecipe(..., capture=False)` 기준으로 공개 호출 블록이 실행되어야 한다.
- `requiredEvidence`의 근거 종류가 모두 반환되어야 한다.
- target을 바꿔도 `Company("005930")` 하드코딩 가정이 남지 않아야 한다.

## AI 직접 사용 방식

1. `ReadSkill` 에서 사용자 질문과 `whenToUse`를 맞춰 이 recipe를 고른다.
2. `GetSkillBody` 로 본문 전체를 읽고 `linkedSkills` 순서대로 먼저 필요한 엔진 skill을 확인한다.
3. `## 공개 호출 방식`의 첫 Python 블록을 target만 바꿔 `ValidateRecipe(..., capture=False)`로 smoke 실행한다.
4. 실행 결과의 `skillRef`, `tableRef`, `valueRef`, `dateRef`, `executionRef` 중 누락된 근거가 있으면 답변을 작성하지 말고 호출 또는 근거 요구를 보강한다.
5. 답변은 결론, 핵심 근거, 메커니즘, 반례·한계, 후속 모니터링 순서로 작성하고 `falsifier.description`이 있으면 반례 단락에서 반드시 확인한다.
