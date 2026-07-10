---
id: recipes.fundamental.quality.forensics.mergerRatioFairness
title: 합병비율·소수주주 보호 점검 (forensics)
category: recipes
kind: recipe
scope: builtin
status: curated
graphTier: L1.5
cluster: incubator.forensics
purpose: 합병·분할·자기주식 처분에서 합병가액·합병비율의 적정성, 소수주주 squeeze-out 여부, NAV/시장가/공정가 산정 방식 차이를 공시 원문 + 재무제표 원표만으로 진단하는 L1.5 절차. 트리거 — '합병비율 적정', '소수주주 보호', 'squeeze out', 'NAV 평가'.
whenToUse:
  - 합병비율 적정성
  - 소수주주 보호
  - squeeze out 의심
  - NAV 공정가 평가 차이
  - 자기주식 처분 합병 활용
  - 인적분할 물적분할
  - 지주회사 전환 합병
inputs:
  - 합병 공시 본문 (DART 합병·분할 사항·주요사항보고서)
  - 합병 대상사 재무제표 (BS·IS 최근 5 년)
  - 합병가액 산정 외부평가기관 보고서
outputs:
  - 합병비율 산정식 분해
  - NAV 대비 / 시장가 대비 / DCF 대비 차이
  - 소수주주 이익 침해 가능성 신호
  - 외부평가 가정 (할인율·성장률) 확인 ledger
capabilityRefs:
  - Company.panel
  - Company.filings
toolRefs:
  - EngineCall
  - RunPython
sourceRefs:
  - dartlab://skills/recipes.fundamental.quality.forensics.mergerRatioFairness
linkedSkills:
  - recipes.fundamental.quality.forensics.index
  - recipes.fundamental.quality.forensics.noteSignalExtractor
  - recipes.fundamental.quality.forensics.eventToStatementMatcher
  - recipes.fundamental.quality.forensics.accountTraceLedger
  - recipes.fundamental.valuation.check
  - engines.company
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - 합병비율 산정 방식 + 외부평가 가정 ledger
  - 소수주주 squeeze-out 가능성 신호 + counter evidence
  - 엔진 승격 후보 메모

forbidden:
  - 합병비율 적정 단정 시 최소 3 가지 평가 방식 (NAV · 시장가 · DCF) 비교 누락 금지.
  - 외부평가 보고서의 할인율·성장률·multiple 가정 명시 누락 금지.
  - 합병 시점의 합병당사회사 시장가 평균 기간 (1 개월 / 1 주일 / 1 일) 차이 인식 없이 비율 평가 금지.
  - 자기주식 처분 + 합병 결합 케이스에서 대주주 지분 변동 정량 누락 금지.
  - 소수주주 squeeze-out 단정 시 최소 1 개 정량 신호 (NAV 대비 10%+ 할인 등) 부재 금지.
failureModes:
  - 합병비율을 *시장가 대비* 만 보고 적정 판단 — NAV / DCF 차이 무시
  - 외부평가 보고서가 *모회사 의뢰* 임을 인지 못 함 (이해상충)
  - 합병 직전 자기주식 처분으로 *대주주 지분 변동* 위장 무인지
  - 합병 후 ROE / 이익 희석 ($EPS$ 분기 추세) 미검증
  - 합병가액 산정 시 *최근 5 년 평균* vs *최근 1 년 평균* 차이 정량 X
examples:
  - 삼성물산-제일모직 합병비율 적정성 (NAV vs 시장가)
  - SK C&C-SK 합병 자기주식 활용
  - 두산밥캣 인수가 PPA 영업권 손상
  - CJ 합병·분할 사례
  - 인적분할 신주 배정 비율
gap:
  primary:
    - company
    - analysis
  secondary:
    - story
testUniverse:
  market: KR
  asOfPolicy: latest
falsifier:
  description: "합병 공시 본문 또는 외부평가 보고서 (할인율·성장률·multiple 가정) 가 부재하면 적정성 판정 불가 — *공시 원문 확인 후 재호출* 한계 명시."
lastUpdated: '2026-05-20'
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

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.panel("IS"|"BS"|"CF")`, `Company.filings`, `scan.quality`, `scan.audit`, `scan.disclosureRisk` 는 엔진 호출로 근거를 먼저 확보한다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildEvidenceForensicsMemo` 로 묶는 **RunPython fallback** 절차다 — 합병비율 공정성 — event-statement 매칭.

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

*합병비율 산정식 분해 + 3 평가 방식 (NAV/시장가/DCF) 비교 + 소수주주 squeeze-out 가능성* 한 문장.

좋은 결론 예시:
- "삼성물산-제일모직 1:0.35 합병비율 — NAV 대비 삼성물산 -X% 할인, 시장가 대비 ±Y%, DCF 대비 -Z%. 합병 직전 1 개월 시장가 평균이 NAV 의 60% 수준이라 *소수주주 squeeze-out 우려 [conf:60]*. 외부평가 외부평가기관이 그룹 자문 빈도 큰 곳임 — 이해상충 가능성 별도 [counter evidence]."

금지:
- 단일 평가 방식 (시장가) 만으로 적정 단정.
- 외부평가 보고서 가정 (할인율·성장률) 미명시.

### 2. 핵심 근거 수집

`requiredEvidence: skillRef + target + tableRef + valueRef + dateRef + sourceRef + executionRef` 필수.

- **target** + **counter** (합병 양쪽 stockCode).
- **sourceRef**: 합병 공시 본문 (DART 주요사항보고서 / 합병결정·합병계약서·외부평가기관 보고서). 보고서 외부 출처 / 평가기관명·평가일·평가범위 명시.
- **tableRef** (4+ 표):
  1. **합병비율 산정** — 합병주체 1 주 당 대상 X 주, 산정 시점 시장가 평균 (1 개월·1 주일·1 일), NAV·DCF 결과
  2. **3 방식 비교** — NAV 대비 / 시장가 대비 / DCF 대비 합병비율 차이 %
  3. **외부평가 가정** — 할인율·성장률·multiple·평가범위·평가기관·평가일·이해상충 여부
  4. **자기주식 변동** — 합병 직전 6 개월 자사주 취득·처분·소각 시계열 + 대주주 지분 변동
- **valueRef**: NAV (자본총계·자본금·자본잉여금), 합병가액, 시장가 평균, 외부평가 결과.
- **dateRef**: 합병결정일·합병기일·평가일·시장가 평균 기간.
- **executionRef**: RunPython 으로 3 방식 비교 계산.

### 3. 메커니즘 분석

합병비율 적정성 = *3 평가 방식 (NAV/시장가/DCF) 일관성 + 외부평가 가정 검증 + 자기주식 + 대주주 지분 변동 동행 확인*:

```mermaid
graph LR
  ANNOUNCE["합병 공시"] --> RATIO["합병비율 (예 - 1:0.35)"]
  ANNOUNCE --> METHOD["산정 방식<br/>① NAV (자본총계/주식수)<br/>② 시장가 평균 (1M·1W·1D)<br/>③ DCF (외부평가 보고서)"]
  
  RATIO --> COMPARE["3 방식 차이 비교"]
  METHOD --> COMPARE
  
  COMPARE --> NAV_GAP["NAV 대비 ±X%"]
  COMPARE --> MKT_GAP["시장가 대비 ±Y%"]
  COMPARE --> DCF_GAP["DCF 대비 ±Z%"]
  
  NAV_GAP --> SUS["squeeze-out 가능성<br/>NAV 대비 10%+ 할인 시 신호"]
  MKT_GAP --> SUS
  DCF_GAP --> SUS
  
  TREASURY["합병 직전 6M 자사주 변동"] --> SUS
  EVAL["외부평가 보고서<br/>할인율·성장률·평가기관"] --> VERIFY["가정 검증"]
  VERIFY --> SUS
```

**평가 방식 정의**:

| 방식 | 산식 | dartlab 데이터 |
|---|---|---|
| **NAV** | 자본총계 / 주식수 | `Company.panel("BS").자본총계` + `Company.panel("BS").주식수` |
| **시장가** | 합병 직전 1M / 1W / 1D 평균 | `Company.gather("price")` 시계열 |
| **DCF** | 외부평가 보고서 (할인율·성장률·multiple) | 공시 본문 `Company.filings("합병")` |
| **PER multiple** | 산업 평균 × EPS | `Company.analysis(valuation, 가치평가).relativeValuation` |

**squeeze-out 신호 정량**:

| 신호 | 임계 | 가중치 |
|---|---|---|
| 시장가 평균 대비 NAV 할인폭 | ≥ 30% | high |
| 합병 직전 6M 시장가 ±20% 이상 변동 | 발생 | high |
| 자기주식 처분 vs 합병 결합 | 동시 발생 | high |
| 외부평가 의뢰자 = 모회사 / 그룹 자문 빈도 큼 | 발생 | medium |
| 합병 직전 자사주 매수 1 개월 내 | 발생 | medium |
| 합병 후 ROE / EPS 즉시 희석 | 동행 | low |

### 4. 반례·한계

- **Falsifier**: 합병 공시 본문 또는 외부평가 보고서 부재 시 적정성 판정 불가 — *공시 원문 확인 후 재호출*.
- **NAV 의 한계**: 회계 장부가 ≠ 실제 가치. 토지·무형자산은 *역사적 원가* 라 NAV 가 저평가될 수 있음. 부동산 비중 큰 회사일수록 NAV 과소.
- **외부평가 이해상충**: 평가기관이 모회사 자문 빈도 큰 곳이면 *친 모회사 가정* 가능. 평가기관 history 별도 확인.
- **합병 직전 주가 인위 조작 가능성**: 합병 발표 직전 자사주 매수·매도로 시장가 평균 왜곡. 합병 발표 직전 6M 거래 패턴 확인.
- **합병 시너지 가정**: DCF 모델이 *합병 시너지* (매출 증가·원가 절감) 를 가정한 경우 신뢰도 낮음. 합병 전 두 회사 standalone 도 함께 검증.
- **소수주주 보호 법규**: 한국 상법 522 조 (반대주주 매수청구) · 외부평가 의무 시점 등 법적 요건 별도. 본 절차는 *정량 신호* 만.

### 5. 후속 모니터링

| 신호 | 임계 | 조치 |
|---|---|---|
| 합병 후 EPS 회복 | 4 분기 내 -10% 이내 | 합병 시너지 가정 검증 |
| 합병 후 ROE 변동 | ±5%p 이상 변동 | 자본 효율 검증 |
| 영업권 손상 | 합병 후 3 년 내 발생 | PPA 가정 부정확 신호 |
| 반대주주 매수청구 행사 비율 | 발행주식 5%+ | 소수주주 불만 정량 |
| 외부평가기관 history | 모회사 자문 빈도 추적 | 이해상충 메모 |

## 대표 반환 형태

- `tableRef:merger:ratio_breakdown` — 합병비율 산정식 분해
- `tableRef:merger:three_method_compare` — NAV/시장가/DCF 비교
- `tableRef:merger:external_eval_assumptions` — 외부평가 가정 ledger
- `tableRef:merger:treasury_timeline` — 자기주식 변동 시계열
- `valueRef:merger:nav_gap_pct` — NAV 대비 합병비율 차이
- `valueRef:merger:squeeze_out_score` — squeeze-out 신호 점수
- `sourceRef:merger:disclosure_id` — 합병 공시 id
- `executionRef:merger:calc_id` — RunPython 실행 id

## 연계 절차

- 영업권 손상검사 → `recipes.fundamental.quality.forensics.goodwillImpairmentCheck`
- 사건 ↔ 재무 매칭 → `recipes.fundamental.quality.forensics.eventToStatementMatcher`
- 계정 추적 → `recipes.fundamental.quality.forensics.accountTraceLedger`
- 주석 신호 (계속기업·정정) → `recipes.fundamental.quality.forensics.noteSignalExtractor`
- valuation 깊이 → `recipes.fundamental.valuation.check`

재호출 트리거: "합병비율 적정성", "삼성물산 제일모직 합병", "SK C&C SK 합병", "NAV 대비 squeeze out".

## 기본 검증

- 합병 양쪽 stockCode 명시.
- 3 평가 방식 (NAV / 시장가 / DCF) 모두 정량 비교.
- 외부평가 가정 (할인율 / 성장률 / 평가기관 / 평가일) 최소 4 종 명시.
- 자기주식 + 대주주 지분 변동 시계열 ≥ 6 개월.
- falsifier — 공시 본문 부재 시 결론 보류.

## AI 직접 사용 방식

1. `ReadSkill` 에서 합병·분할 질문이면 본 recipe 선정.
2. 합병 양쪽 stockCode 확인 — 사용자 명시 또는 공시 검색.
3. `Company.panel` BS/IS 최근 5 년 양쪽.
4. `Company.filings("합병")` 공시 본문 — 가능 시.
5. RunPython 으로 NAV/시장가/DCF 3 방식 계산.
6. squeeze-out 신호 점수 산출.
7. 답변에 *3 방식 비교 표 + 외부평가 가정 ledger + 자기주식 시계열* 3 셋 + 반례·한계 필수.
