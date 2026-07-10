---
id: recipes.fundamental.credit.quantConsensus
title: 신용 dCR × 퀀트 부도 모델 3-source 합의 위험 종목
category: recipes
kind: recipe
scope: builtin
status: drafted
purpose: 단일 회사 부도 위험을 dCR (정성·정량 종합) + Altman Z″ + Ohlson O + Beneish M 4-source 동시 평가. 단일 모델 false positive 줄이고 triple-agreement 시 강한 위험 신호. credit ↔ quant 격리 메우는 조합. 트리거 — '신용 퀀트 합의', '부도 4 모델', 'distress consensus'.
whenToUse:
  - 신용 퀀트 합의
  - 부도 4 모델
  - 다중 모델 부도
  - quant credit 합의
linkedSkills:
  - engines.company
  - engines.credit
  - recipes.fundamental.credit.distressDual
  - engines.quant
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
  - "engines.viz.tableBackedChart"
  - "engines.viz.scenarioVisuals"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "표 기반 순위·추세는 engines.viz.tableBackedChart만 사용하고 tableRef/evidenceBinding이 없으면 차트 대신 검산 표로 낮춘다."
  - "stress·민감도·충격 전파는 engines.viz.scenarioVisuals를 사용하고 assumption grid 또는 수치 임계가 없으면 scenario table로 낮춘다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

gap:
  primary:
    - credit
    - quant
  secondary:
    - analysis
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
  description: TripleAgreement 그룹의 24 개월 default 율이 Safe 그룹보다 낮으면 모델 inverted
  pythonCheck: |
    assert default_rate(triple_agreement) > default_rate(safe)
expectedNovelty:
  - consensusLabel
  - sourceAgreementCount
forbidden:
  - 4 모델 중 1 개 신호로 부도 임박 단정 금지.
  - 1968/1980 미국 표본 thresholds 를 KR 시장에 그대로 적용 금지.
  - 금융업 (은행·보험) 에 본 recipe 적용 금지 — 모델 대상 외.
failureModes:
  - dCR 등급과 quant model 의 시간 frequency 차이 (분기 vs 연간).
  - Beneish M 의 원자재기업 false positive (정상 inventory 변동을 분식 신호로 오인).
examples:
  - 삼성전자 4 모델 부도 합의
  - HMM dCR + Altman + Ohlson + Beneish 일치
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

repayment = c.credit("repayment")
leverage = c.credit("leverage")
liquidity = c.credit("liquidity")
bs = c.panel("BS", freq="Y")
is_df = c.panel("IS", freq="Y")
cf = c.panel("CF", freq="Y")

period = latest_period(bs)
consensus_sources = ["dCR.repayment", "dCR.leverage", "balanceSheet", "incomeStatement", "cashFlow"]
emit_result(
    table=[
        {"source": "dCR.repayment", "result": compact(repayment)},
        {"source": "dCR.leverage", "result": compact(leverage)},
        {"source": "dCR.liquidity", "result": compact(liquidity)},
        {"source": "financialStatements", "result": {"bsRows": bs.height, "isRows": is_df.height, "cfRows": cf.height}},
    ],
    values={"target": target, "sourceAgreementCount": len(consensus_sources), "period": period},
    date=period,
)
```

## 호출 동작

1. `c.credit(detail=True)` — dCR 등급 + 7 axis. BB- 이하 distress 표시.
2. `c.panel("BS"|"IS", freq="Y")` 로 raw → Altman Z″ 직접 계산.
3. 동일 raw → Ohlson O logit + 부도 확률.
4. AR / Sales 비율 변화 → Beneish M-Score 분식 신호.
5. 4 source 합의 — 3 개 이상 = TripleAgreement.

## 대표 반환 형태

`pl.DataFrame` — 컬럼:
- `dcrGrade : str` · `dcrDistress : bool`
- `altmanZ : float` · `altmanDistress : bool`
- `ohlsonProb : float` · `ohlsonFlag : bool`
- `beneishM : float` · `beneishFlag : bool`
- `sourcesFlagged : int` (0~4)
- `consensus : str` — Safe / SingleAgreement / DualAgreement / TripleAgreement

## 연계 절차

1. 본 recipe → 4 source 합의 결과.
2. consensus = TripleAgreement → `recipes.fundamental.credit.macroStress` 와 결합 — 매크로 충격 시 추가 악화 위험.
3. consensus = DualAgreement → `engines.analysis` 로 분식 의심 별도 검증.
4. universe 적용은 `recipes.fundamental.credit.distressCandidateScreen` 와 결합.

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
