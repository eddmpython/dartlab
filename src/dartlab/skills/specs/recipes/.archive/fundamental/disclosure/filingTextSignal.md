---
id: recipes.fundamental.disclosure.filingTextSignal
title: 8-K / 사업보고서 비정상 키워드 빈도 → predictionSignal feature
category: recipes
kind: recipe
scope: builtin
status: drafted
purpose: 최근 365 일 공시 본문에서 "going concern" / "의견거절" / "거짓서명" / "계속기업" 같은 위험 키워드 빈도가 trailing 3y baseline 대비 z-score ≥ 2 이면 비정상 신호. predictionSignal feature 로 입력. Loughran-McDonald sentiment 의 일반 dictionary 와 다른 anomaly-on-rare-keywords 접근. search/edgar ↔ analysis 격리 메우는 조합. 트리거 — 'filing text signal', '공시 키워드 anomaly', '사업보고서 위험 신호'.
whenToUse:
  - filing text signal
  - 공시 키워드 anomaly
  - 위험 키워드 빈도
  - going concern signal
linkedSkills:
  - engines.gather
  - engines.search
  - engines.analysis
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
  - "engines.viz.evidenceCoverage"
  - "engines.viz.tableBackedChart"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "근거 충족도는 engines.viz.evidenceCoverage로 검산/한계 섹션에만 배치하고 결론 차트처럼 해석하지 않는다."
  - "표 기반 순위·추세는 engines.viz.tableBackedChart만 사용하고 tableRef/evidenceBinding이 없으면 차트 대신 검산 표로 낮춘다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

gap:
  primary:
    - search
    - analysis
  secondary:
    - gather
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
  description: "anomaly z > 2 인 종목의 forward 90d drawdown 이 base 종목보다 크지 않으면 신호 무효"
  pythonCheck: |
    assert forward_90d_drawdown(z_high) > forward_90d_drawdown(z_low)
expectedNovelty:
  - keywordZScore
  - anomalyFlag
forbidden:
  - 단일 키워드 빈도 1 회 등장만으로 신호 단정 금지.
  - rare 키워드 dictionary 가 회사 산업 별 baseline 다름 — universal dictionary 강행 X.
failureModes:
  - 한국 공시 본문 OCR / parsing 품질이 회사 별 차이 — 키워드 매칭 누락.
  - 보일러플레이트 (감사보고서 표준 문구) 가 안전 공시에서도 등장 — false positive.
examples:
  - 삼성전자 365 일 공시 anomaly z
  - HMM going concern 빈도 추세
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

try:
    calendar = c.filings()
except Exception as exc:
    calendar = {"error": str(exc)}
try:
    change = c.analysis("disclosureChange")
except Exception as exc:
    change = {"error": str(exc)}
bs = c.panel("BS", freq="Y")

if isinstance(calendar, pl.DataFrame) and not calendar.is_empty():
    filing_rows = calendar.head(5).to_dicts()
elif isinstance(calendar, list) and calendar:
    filing_rows = calendar[:5]
else:
    filing_rows = [{"calendar": compact(calendar), "change": compact(change)}]

emit_result(
    table=filing_rows,
    values={"target": target, "filingSampleCount": len(filing_rows), "hasDisclosureChange": compact(change)["type"] != "NoneType"},
    date=latest_period(bs),
)
```

## 호출 동작

1. `c.gather("collect", days=365)` — 최근 365 일 공시 list.
2. `c.gather("collect", days=1095)` — 3 년 baseline.
3. 위험 키워드 list (going concern / 의견거절 / 거짓서명 / etc) 빈도 측정.
4. z-score = (recent - baseline_yearly) / Poisson stdev 근사.
5. z ≥ 2 인 키워드 anomaly flag.

## 대표 반환 형태

`pl.DataFrame` — 키워드 별 row:
- `keyword : str`
- `recentCount : int` — 최근 365 일 등장 횟수
- `baselineYearly : float` — 3y 평균 (연간 환산)
- `keywordZScore : float`
- `anomalyFlag : bool` — z ≥ 2

## 연계 절차

1. 본 recipe → 키워드 별 anomaly z-score.
2. anomalyFlag = True 키워드 ≥ 2 → `engines.analysis` 의 input feature.
3. 동시 발현 → `recipes.fundamental.disclosure.toneToStoryRisk` 와 결합 — story.risk 자동 발행 트리거.

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
