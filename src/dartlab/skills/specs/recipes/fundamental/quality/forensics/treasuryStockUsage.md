---
id: recipes.fundamental.quality.forensics.treasuryStockUsage
title: 자사주 취득·처분·소각 의도 진단
category: recipes
kind: recipe
scope: builtin
status: curated
graphTier: L1.5
cluster: incubator.forensics
purpose: 자기주식 (자사주) 의 취득·처분·소각 패턴을 통해 주가 부양·지배권 강화·주식보상 활용·지주사 전환 (인적분할 후 현물출자) 등 의도를 IS·BS 시계열 + 자기주식 공시 + 지분 변동으로 진단하는 L1.5 절차. 트리거 — '자사주 매입', '자사주 소각', '자기주식 처분', '지주사 전환', '주가 부양'.
whenToUse:
  - 자사주 취득 공시
  - 자사주 처분 (제3자 / 임직원 / 합병 신주배정)
  - 자사주 소각 결정
  - 지주사 전환 (인적분할 + 현물출자) 동행
  - 주가 부양 목적 매입
  - 주식보상 활용 (RSU·스톡옵션 행사)
  - 경영권 분쟁 동행 자사주 활용
linkedSkills:
  - recipes.fundamental.quality.forensics.index
  - recipes.fundamental.quality.forensics.controllingPowerJudgment
  - recipes.fundamental.quality.forensics.executiveCompensationAudit
  - recipes.fundamental.quality.forensics.mergerRatioFairness
  - recipes.fundamental.quality.forensics.disclosureTimingAnomaly
  - engines.company
inputs:
  - Company.panel treasury / 자기주식 시계열
  - Company.panel BS (자본·자기주식 잔액)
  - Company.filings (자사주 취득·처분·소각·합병)
  - Company.panel IS (EPS·ROE 동행 효과)
  - scan capital (자사주 횡단 패턴)
outputs:
  - 자사주 변동 시계열 ledger (취득·처분·소각)
  - 의도 분류 매트릭스 (주가 부양 / 지배권 강화 / 보상 / 지주사 전환)
  - EPS·ROE 분모 효과 ledger
  - 동행 사건 timing (경영권 분쟁·합병·지주사 전환)
capabilityRefs:
  - Company.panel
  - Company.filings
  - scan
toolRefs:
  - EngineCall
  - RunPython
sourceRefs:
  - dartlab://skills/recipes.fundamental.quality.forensics.treasuryStockUsage
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - 자사주 변동 시계열 + 의도 매트릭스
  - EPS·ROE 분모 효과 ledger
  - 동행 사건 timing
  - 엔진 승격 후보 메모

forbidden:
  - 자사주 매입 = 주가 부양 단정 시 *주식보상·합병·지주사 전환* 정상 목적 반례 검토 누락 금지.
  - 자사주 처분 = 지배권 강화 단정 시 *제3자 처분 상대방* (백기사·임직원 RSU·합병 신주) 분류 누락 금지.
  - 자사주 소각 = 주주환원 긍정 단정 시 *동시 신주 발행 (전환사채·증자)* 잠재 희석 동행 확인 의무.
  - 매입 ↔ EPS 점프 단정 시 *분모 (주식수)* 와 *분자 (이익)* 효과 분리 의무.
  - 한 시점만 보고 단정 — 자사주 시계열 ≥ 3 년 + 동행 사건 시계열 동시 평가.
failureModes:
  - 자사주 매입 = 부양 단정 시 *주식보상 적립* 정상 목적 무시
  - 자사주 처분 = 백기사 단정 시 *합병 신주배정* 정상 목적 혼동
  - 자사주 소각 = 환원 단정 시 *전환사채·증자 동시 발행* 으로 실질 희석 무시
  - 지주사 전환 시 *현물출자 비율* 정확 계산 누락 → 지배권 강화 효과 misread
  - 매입 ↔ EPS 점프 단정 시 *실제 이익 증가 효과* 혼동
examples:
  - 삼성전자 자사주 매입 + 소각 (4 권)
  - SK(주) 지주사 전환 자사주 활용 (4 권)
  - 삼성물산 합병 시 자기주식 활용 (제일모직과 합병)
  - SK C&C-SK 합병 자기주식 처분 (1 권)
  - 현대모비스·현대글로비스 지주사 전환 패턴
  - 경영권 분쟁 중 자사주 우호세력 처분 (구체 사례 — 한진해운·대한항공 등)
  - 자사주 소각으로 EPS 즉시 개선 (단기 효과)
gap:
  primary:
    - company
    - analysis
  secondary:
    - scan
testUniverse:
  market: KR
  asOfPolicy: latest
falsifier:
  description: "자사주 변동 공시 또는 처분 상대방 정보 부재 시 의도 판정 불가 — *DART 자기주식취득·처분 공시 fetch 후 재호출* 한계 명시. 또한 *경영권 분쟁 timing* 명시 없으면 지배권 강화 단정 보류."
lastUpdated: '2026-08-09'
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
visualRefs:
  - "engines.viz.evidenceCoverage"
  - "engines.viz.mermaidDiagram"
  - "engines.viz.tableBackedChart"
---

## 공개 호출 방식

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.panel("IS"|"BS"|"CF")`, `Company.filings`, `scan.quality`, `scan.audit`, `scan.disclosureRisk` 는 엔진 호출로 근거를 먼저 확보한다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildEvidenceForensicsMemo` 로 묶는 **RunPython fallback** 절차다 — 자기주식 사용 — event-statement.

```python
import dartlab
from dartlab.synth.evidenceForensics import buildEvidenceForensicsMemo

target = "005930"  # KOSPI/KOSDAQ 종목코드
c = dartlab.Company(target)

statements = {}
for topic in ("IS", "BS", "CF"):
    try:
        statements[topic] = c.panel(topic, freq="Y")
    except TypeError:
        statements[topic] = c.panel(topic)
    except Exception:
        pass

sectionTexts = {}
for topic in ("businessOverview", "riskFactors", "mdna", "notesDetail"):
    try:
        sectionTexts[topic] = str(c.panel(topic))[:20000]
    except Exception:
        pass

try:
    disclosure = c.filings()
    events = disclosure.head(20).to_dicts() if hasattr(disclosure, "head") else list(disclosure)[:20]
except Exception:
    events = []

scanRows = []
for axis in ("quality", "audit", "disclosureRisk"):
    try:
        df = dartlab.scan(axis)
        rows = df.head(3).to_dicts() if hasattr(df, "head") else []
        for row in rows:
            row["axis"] = axis
        scanRows.extend(rows)
    except Exception:
        pass

memo = buildEvidenceForensicsMemo(
    target=target,
    market=str(getattr(c, "market", "KR")),
    companyName=str(getattr(c, "corpName", target)),
    statements=statements,
    sectionTexts=sectionTexts,
    events=events,
    scanRows=scanRows,
)

emit_result(
    table=memo["tables"]["eventToStatementMatcher"],
    values={
        "target": target,
        "riskScore": memo["headline"].get("riskScore"),
        "signalCount": memo["headline"].get("signalCount"),
    },
    date=memo.get("asOf", "latest"),
    sources=memo["sources"],
)
```

## 호출 동작 — 5 단 분석 구조

### 1. 결론 도출

*자사주 변동 시계열 + 의도 분류 + EPS/ROE 분모 효과 + 동행 사건 timing* 한 문장.

좋은 결론 예시:
- "삼성전자 자사주 매입 X 조원 (직전 5 년 누적), 소각 Y 조원 / 매입 (소각률 Z%). 매입 시점 평균 주가 P0 vs 발표 직전 1M 주가 -N%. 매입 후 4 분기 EPS +M% (분모 효과 약 K%p, 분자 효과 약 L%p). 동행 사건 — 지주사 전환 검토 / 주주환원 정책 공시. *주주환원 + EPS 부양 혼합 의도 [conf:70]*. counter — 자회사 주식보상 적립 부분 (RSU 발행 동행) 별도 검토."

금지:
- 단일 신호 (취득 OR 처분 OR 소각) 만으로 의도 단정.
- EPS 점프 = 자사주 효과 단정 시 분모/분자 분리 누락.

### 2. 핵심 근거 수집

`requiredEvidence: skillRef + target + tableRef + valueRef + dateRef + sourceRef + executionRef` 필수.

- **target** (stockCode).
- **sourceRef**: 자사주 취득·처분·소각 공시 (DART 주요사항보고서) / 자사주 임직원 처분 본문 (제3자 상대방) / 합병 신주배정 공시 (자사주 활용).
- **tableRef** (4+ 표):
  1. **자사주 변동 시계열** — 분기·연도별 취득 / 처분 / 소각 수량·금액·평균가
  2. **의도 분류 매트릭스** — 주가 부양 (매입+소각) / 지배권 강화 (제3자 처분) / 주식보상 (임직원 처분) / 지주사 전환 (현물출자)
  3. **EPS·ROE 분모 효과** — 자사주 매입 후 EPS·ROE 변화 / 분모 (주식수) 효과 vs 분자 (이익) 효과 분리
  4. **동행 사건 timing** — 경영권 분쟁·합병 발표·지주사 전환 검토일 ↔ 자사주 거래 timestamp
- **valueRef**: 누적 매입·처분·소각 금액, 소각률 (소각 / 매입), EPS 점프 폭, 분모 효과 %p.
- **dateRef**: 자사주 거래일·합병결정일·경영권 분쟁 timestamp.
- **executionRef**: RunPython 으로 EPS 분해 + 시계열 회귀.

### 3. 메커니즘 분석

자사주 의도 진단 = *변동 시계열 + 4 의도 분류 + EPS/ROE 분모 효과 + 동행 사건 timing 4 차원 동시 검증*:

```mermaid
graph LR
  ACQ["자사주 취득"] --> STOCK["자기주식 잔액"]
  DISP["자사주 처분"] --> STOCK
  BURN["자사주 소각"] --> STOCK

  ACQ --> PUMP["주가 부양?<br/>발표 직전 주가 하락 + 매입"]
  BURN --> RETURN["주주환원?<br/>매입 후 즉시 소각"]
  DISP --> POWER["지배권 강화?<br/>제3자 우호세력 처분"]
  DISP --> COMP["주식보상?<br/>임직원 RSU 처분"]
  ACQ --> HOLDING["지주사 전환?<br/>인적분할 + 현물출자"]

  STOCK --> SHARES["발행주식수 변화"]
  SHARES --> EPS["EPS 분모 효과"]
  SHARES --> ROE["ROE 분모 효과"]

  NI["순이익"] --> NUM["EPS 분자 효과"]
  EPS --> EPS_DELTA["EPS 변화 분해<br/>분모 vs 분자"]
  NUM --> EPS_DELTA

  EVENT["동행 사건<br/>합병·경영권 분쟁·지주사 전환"] --> TIMING["timing 매칭"]
  ACQ --> TIMING
  DISP --> TIMING

  EPS_DELTA --> INTENT["의도 점수"]
  PUMP --> INTENT
  RETURN --> INTENT
  POWER --> INTENT
  TIMING --> INTENT
```

**5 의도 매트릭스 신호**:

| 의도 | 신호 패턴 | 정량 임계 | 가중치 |
|---|---|---|---|
| **주가 부양** | 매입 발표 직전 1M 주가 변동 | ≤ -10% | medium |
| **주가 부양** | 매입 발표 후 1M 주가 변동 | ≥ +5% | medium |
| **주주환원 (긍정)** | 소각률 = 소각 / 매입 | ≥ 50% / 3Y | high |
| **주주환원 (긍정)** | 동행 신주 발행 (CB·증자) 잠재 희석 | 부재 | high |
| **지배권 강화** | 제3자 우호세력 처분 비중 | ≥ 30% / 처분 | high |
| **지배권 강화** | 경영권 분쟁 timestamp 동행 | 동행 | high |
| **주식보상** | 임직원 RSU·스톡옵션 행사 동행 | 동행 | medium |
| **지주사 전환** | 인적분할 + 현물출자 비율 | ≥ 50% | high |
| **EPS 분모 효과** | EPS 점프 중 분모 (주식수) 기여 | ≥ 50% | medium |

### 4. 반례·한계

- **Falsifier**: 자사주 변동 공시 또는 처분 상대방 정보 부재 시 의도 판정 불가 — *DART 자기주식취득·처분 공시 fetch 후 재호출*.
- **매입 + 미소각 = 부양 의심**: 매입 후 장기간 자기주식 잔존 시 *향후 처분 옵션* 보유로 보면 잠재 dilution. 매입만으로 주주환원 단정 금지.
- **합병 신주배정 자사주 활용**: 합병 시 자기주식을 *피합병회사 주주* 에게 배정하는 케이스 — *지배권 강화* 와 *합병 정상 목적* 분리 어려움. 합병비율·외부평가 동행 검증.
- **지주사 전환 정상 목적**: 인적분할 후 현물출자 자체는 지배구조 단순화 등 정상 목적 인정. 다만 *지배권 강화 효과* (지분율 상승) 별도 정량 검증.
- **소각률 측정 시계**: 소각률 = 소각 / 매입 인데 매입 후 수년 후 소각하는 패턴이 있어 *단기 ratio* 만 보면 환원 의도 과소.
- **임직원 처분 정상 목적**: RSU와 스톡옵션 행사 처분은 정상적인 보상 목적일 수 있다. 행사 시점과 호재가 겹치면 `recipes.fundamental.quality.forensics.executiveCompensationAudit`와 결합해 검증한다.
- **공정거래법·세법 제약**: 자사주 활용은 공정거래법·세법 (특수관계자 거래) 제약이 있어 *법적 한계* 안 정상 활용도 多. 단순 패턴만으로 의도 단정 금지.

### 5. 후속 모니터링

| 신호 | 임계 | 조치 |
|---|---|---|
| 누적 매입 / 시가총액 | ≥ 5% / 3Y | 부양 의도 ledger 작성 |
| 소각률 (소각/매입) | < 30% / 5Y | 잠재 dilution 의심 |
| 제3자 처분 비중 | ≥ 30% | 지배권 강화 의심 격상 |
| 경영권 분쟁 동행 처분 | 동행 | 가중치 high |
| EPS 점프 분모 효과 비중 | ≥ 50% | 분모 game 의심 |
| 지주사 전환 동행 | 동행 | 현물출자 비율 별도 계산 |
| 동행 CB·증자 발행 | 동행 | 잠재 희석 ledger |

## 대표 반환 형태

- `tableRef:treasury:variation_timeseries` — 자사주 변동 시계열
- `tableRef:treasury:intent_matrix` — 의도 분류 매트릭스
- `tableRef:treasury:eps_decomposition` — EPS 분모/분자 분해
- `tableRef:treasury:event_timing` — 동행 사건 timing
- `valueRef:treasury:cumulative_acq` — 누적 매입 금액
- `valueRef:treasury:burn_rate` — 소각률
- `valueRef:treasury:third_party_disp_pct` — 제3자 처분 비중
- `valueRef:treasury:denom_effect_pct` — EPS 분모 효과 %
- `sourceRef:treasury:disclosure_id` — 자사주 공시 id
- `executionRef:treasury:calc_id` — RunPython 실행 id

## 연계 절차

- 실질지배력 (지분 변동 동행) → `recipes.fundamental.quality.forensics.controllingPowerJudgment`
- 임원 보수 (스톡옵션 행사 동행) → `recipes.fundamental.quality.forensics.executiveCompensationAudit`
- 합병비율 (자사주 합병 활용) → `recipes.fundamental.quality.forensics.mergerRatioFairness`
- 공시 timing (자사주 timestamp ↔ 호재) → `recipes.fundamental.quality.forensics.disclosureTimingAnomaly`

재호출 트리거: "자사주 매입 의도", "자사주 소각", "지주사 전환 자기주식", "경영권 분쟁 자사주", "EPS 분모 game".

## 기본 검증

- 자사주 변동 시계열 ≥ 3 년.
- 4 의도 분류 (부양 / 환원 / 지배권 / 보상 / 지주사) 모두 가능성 평가.
- EPS / ROE 분모 효과 분리 계산.
- 동행 사건 (합병·분쟁·지주사) timestamp 매칭.
- 소각률 (소각/매입) 명시.
- falsifier — 처분 상대방 정보 부재 시 의도 보류.

## AI 직접 사용 방식

1. `ReadSkill` 에서 자사주·자기주식 질문이면 본 recipe 선정.
2. target stockCode 확인.
3. `Company.panel("자기주식")` 또는 `Company.panel("treasury")` 변동 시계열.
4. `Company.panel("BS", freq="Q")` + `Company.panel("IS", freq="Q")` 자본·EPS 동행.
5. `Company.filings("자기주식")` 거래 timestamp + 처분 상대방.
6. `scan("capital")` 횡단 비교.
7. RunPython 으로 5 의도 매트릭스 + EPS 분해 계산.
8. 답변에 *자사주 변동 + 의도 매트릭스 + EPS 분해 + 동행 사건 timing* 4 셋 + 반례·한계 필수.
