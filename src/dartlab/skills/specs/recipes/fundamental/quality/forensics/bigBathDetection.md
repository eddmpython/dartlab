---
id: recipes.fundamental.quality.forensics.bigBathDetection
title: 빅 배스 (Big Bath) 회계처리 탐지
category: recipes
kind: recipe
scope: builtin
status: curated
graphTier: L1.5
cluster: incubator.forensics
purpose: 신임 경영자 취임·구조조정·인수합병 직후 대규모 일회성 손실 (손상차손·충당금·재고폐기·구조조정 비용) 을 한꺼번에 인식해 다음 분기 인위적 회복 (이익 점프) 을 만드는 빅 배스 패턴을 IS·BS 시계열 + 경영자 변경 timestamp + 손상차손 주석으로 진단하는 L1.5 절차. 트리거 — '빅 배스', 'big bath', '취임 직후 대규모 손실', '손상차손 일시 집중', '구조조정 충당금'.
whenToUse:
  - CEO·CFO 교체 직후 분기
  - 대규모 손상차손 일회성 인식
  - 인수합병 직후 PPA 손상
  - 영업권 손상 한꺼번에 인식
  - 구조조정 충당금 일시 적립
  - 재고·매출채권 일괄 폐기
  - 이연법인세자산 대규모 손상
linkedSkills:
  - recipes.fundamental.quality.forensics.index
  - recipes.fundamental.quality.forensics.goodwillImpairmentCheck
  - recipes.fundamental.quality.forensics.eventToStatementMatcher
  - recipes.fundamental.quality.forensics.accountTraceLedger
  - recipes.fundamental.quality.forensics.noteSignalExtractor
  - recipes.fundamental.quality.forensics.workingCapitalPressureMap
  - recipes.fundamental.quality.forensics.mergerRatioFairness
  - engines.company
inputs:
  - Company.panel IS (분기·연도 — 일회성 손실 시계열)
  - Company.panel BS (충당부채·이연법인세자산·영업권)
  - Company.panel notes 손상차손·구조조정 (가능 시)
  - Company.filings (경영자 변경·구조조정·합병 timestamp)
outputs:
  - 일회성 손실 시계열 ledger
  - 경영자 변경 ↔ 손실 인식 timing 매트릭스
  - 빅 배스 신호 점수
  - 차기 분기 인위적 회복 패턴 ledger
capabilityRefs:
  - Company.panel
  - Company.filings
toolRefs:
  - EngineCall
  - RunPython
sourceRefs:
  - dartlab://skills/recipes.fundamental.quality.forensics.bigBathDetection
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - 일회성 손실 시계열 + 경영자 변경 timing 매트릭스
  - 빅 배스 신호 점수
  - 차기 분기 인위적 회복 ledger
  - 엔진 승격 후보 메모

forbidden:
  - 일회성 손실 = 빅 배스 단정 시 경영자 변경·구조조정·합병 *촉발 사건* 동행 검증 누락 금지.
  - 손상차손 인식 = 부적정 단정 시 *외부 환경 변화* (산업 침체·환율·유가) 반례 검토 누락 금지.
  - 차기 분기 회복 = 인위적 단정 시 *실제 매출 회복* 또는 *영업현금흐름 회복* 동행 확인 의무.
  - 손상차손 단일 분기 잔액만 보고 단정 — 회사 평균 분기 손실 vs 당기 손실 ratio 동행 평가.
  - 한 항목 (예 영업권) 만 보고 단정 — *손상 항목 cluster* (재고·매출채권·이연법인세) 동시 검증.
failureModes:
  - 신임 경영자 = 빅 배스 단정 시 *외부 위기 도래* (시점 우연 일치) 반례 무시
  - 손상차손 = 회계 조작 단정 시 *합리적 손상검사* (IFRS 36) 준수 손상 혼동
  - 차기 회복 = 빅 배스 후행 단정 시 *실제 비용 감소* (구조조정 효과) 회복 무시
  - 영업권 손상 = 빅 배스 단정 시 *과거 인수가 부적정* 와 *현재 빅 배스 의도* 인과 혼동
  - 4 분기 손실 집중 = 빅 배스 단정 시 *결산일 인식 의무 사항* (감사 후 손상) 무시
examples:
  - 현대중공업 신임 경영진 취임 손실 인식 (4 권)
  - KB국민은행 회장 교체 분기 손실 (4 권)
  - 두산인프라코어 밥캣 인수 후 손상 (1 권 "먼저 맞는 매가")
  - 한국전력 4 분기 손실 집중 패턴
  - 대우조선해양 신임 사장 취임 직후 손실 (4 권 회계분식 사례 동행)
  - 인수합병 PPA 영업권 즉시 손상 패턴
  - LG디스플레이·SK하이닉스 다운사이클 손상 차이 (산업 vs 빅배스)
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
  description: "경영자 변경 timestamp 또는 손상차손 주석 부재 시 빅 배스 판정 불가 — *DART 임원변동 공시 + 주석 fetch 후 재호출* 한계 명시. 또한 *동종 업종 평균 손상률* 외부 비교 없이 빅 배스 단정 보류."
lastUpdated: '2026-05-21'
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

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.panel("IS"|"BS"|"CF")`, `Company.filings`, `scan.quality`, `scan.audit`, `scan.disclosureRisk` 는 엔진 호출로 근거를 먼저 확보한다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildEvidenceForensicsMemo` 로 묶는 **RunPython fallback** 절차다 — 빅 배스 — 일회성 손실 + 경영자 변경 ledger.

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
    table=memo["tables"]["engineCandidateMemo"],
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

*일회성 손실 분기 + 경영자 변경 timestamp + 차기 분기 회복 + 손상 cluster 동행* 한 문장.

좋은 결론 예시:
- "현대중공업 케이스 — 신임 사장 취임 D+Y 분기 손상차손 X 조원 (전년 평균 분기 손실의 N 배) + 구조조정 충당금 동시 인식. 차기 2~3 분기 인위적 회복 (영업이익 +Z% 점프) 동행. *빅 배스 패턴 [conf:70]*. counter — 조선 다운사이클 동시 발생 (산업 평균 손상률 W%) 으로 외부 환경 기여도 일부 인정. *경영자 의도 vs 산업 침체 분리 어려움* 한계 메모."

금지:
- 신임 경영자 단일 신호만으로 빅 배스 단정.
- 차기 분기 회복 = 인위적 단정 시 영업현금흐름 회복 동행 미확인.

### 2. 핵심 근거 수집

`requiredEvidence: skillRef + target + tableRef + valueRef + dateRef + sourceRef + executionRef` 필수.

- **target** (stockCode).
- **sourceRef**: 경영자 변경 공시 (DART 임원변동·주요사항보고) / 손상차손 주석 (감사보고서) / 합병·구조조정 공시.
- **tableRef** (4+ 표):
  1. **분기 일회성 손실 시계열** — 분기별 영업외비용 (손상차손·구조조정 비용·이연법인세 손상·재고·채권 손상)
  2. **경영자 변경 timing** — CEO·CFO 교체일·취임일 / 동일 분기 손실 인식 여부 / 직후 1~2 분기 패턴
  3. **손상 cluster 매트릭스** — 영업권·유형자산·무형자산·재고·매출채권·이연법인세자산 동시 인식 여부
  4. **차기 분기 회복 ledger** — 직후 2~4 분기 영업이익 / 영업현금흐름 회복 vs 평균 ratio
- **valueRef**: 일회성 손실 절대액, 평균 분기 손실 대비 배수, 차기 분기 회복 폭.
- **dateRef**: 경영자 취임일·손상 인식일·합병일·차기 분기 발표일.
- **executionRef**: RunPython 으로 손상 cluster + 회복 회귀 계산.

### 3. 메커니즘 분석

빅 배스 진단 = *경영자 변경 + 손상 cluster + 차기 회복 + 외부 환경 반례 4 차원 동시 검증*:

```mermaid
graph LR
  EXEC["경영자 변경 timestamp"] --> EVENT_Q["취임 분기 (Q0)"]
  EVENT_Q --> LOSS_Q["Q0 손실 인식"]
  EVENT_Q --> LOSS_Q1["Q0+1 손실 인식"]

  LOSS_Q --> CLUSTER["손상 cluster<br/>영업권·유형·무형·재고·채권·이연세"]
  LOSS_Q1 --> CLUSTER

  CLUSTER --> RATIO["평균 분기 손실 대비 배수<br/>X / avg(Q-4..Q-1)"]

  EVENT_Q --> RECOVER_Q["Q0+2~Q0+4 회복"]
  RECOVER_Q --> NI_BUMP["영업이익 점프"]
  RECOVER_Q --> OCF_VERIFY["영업현금흐름 회복<br/>실제 vs 회계 분리"]

  EXTERNAL["외부 환경 반례<br/>산업 평균 손상률·환율·유가"] --> COUNTER["반례 검증"]

  RATIO --> SCORE["빅 배스 점수"]
  NI_BUMP --> SCORE
  OCF_VERIFY --> SCORE
  COUNTER --> SCORE
```

**6 패턴 정량 신호**:

| 패턴 | 신호 | 임계 | 가중치 |
|---|---|---|---|
| **경영자 변경 timing** | CEO·CFO 취임 분기 (Q0) 손실 인식 | Q0 또는 Q0+1 분기 발생 | high |
| **손상 cluster** | 동시 손상 항목 종류 | ≥ 3 종 (영업권·유형·재고 등) | high |
| **손실 배수** | Q0 손실 / 평균 분기 손실 (Q-8 ~ Q-1) | ≥ 5 배 | high |
| **차기 회복** | Q0+2~Q0+4 영업이익 점프 | 평균 분기 +30% 이상 | medium |
| **회복 진정성** | 영업현금흐름 (OCF) 회복 vs 영업이익 회복 | OCF 회복 < 영업이익 회복 → 회계 회복 신호 | high |
| **외부 환경 반례** | 동종 업종 평균 손상률 | 회사 손상률 / 업종 평균 ≥ 2 배 → 빅 배스 격상 | medium |

### 4. 반례·한계

- **Falsifier**: 경영자 변경 timestamp 또는 손상차손 주석 부재 시 빅 배스 판정 불가 — *DART 임원변동 공시 + 주석 fetch 후 재호출*.
- **외부 위기 동시 발생**: 신임 경영자 취임이 *위기 도래로 인한 교체* 인 경우 (조선·해운·정유 다운사이클) 시점 일치는 우연 + 실제 손상 합리성. 경영자 의도 vs 산업 침체 분리 어려움.
- **IFRS 36 손상검사 의무**: 결산일 손상 인식은 *법적 의무* (IFRS 36 회수가능액 비교) 라 4 분기 손실 집중 자체가 빅 배스 신호로 보기 어려운 경우 多.
- **실제 비용 감소 회복**: 차기 분기 회복이 *구조조정 효과* (인건비·임차료 감소) 라면 인위적 회복 아님. OCF 동행 회복 시 진정성 높음.
- **합병 PPA 영업권 즉시 손상**: 합병 직후 영업권 손상은 *과거 인수가 부적정* 회귀 가능성 큼. 이 경우 *과거 의사결정* 책임이지 *현재 빅 배스 의도* 와 다름.
- **이연법인세자산 손상 특수성**: 미래 과세소득 회복 가능성 평가 (IAS 12) 라 회계 추정 영역. 회복 시점 다시 환입되는 회계 처리 자체가 정상.
- **재고·매출채권 일괄 폐기**: 산업 정상 cycle (패션·반도체 재고 폐기) 인 경우 빅 배스 아님. 평균 분기 폐기율 대비 검증.

### 5. 후속 모니터링

| 신호 | 임계 | 조치 |
|---|---|---|
| 경영자 변경 후 분기 손실 배수 | ≥ 5 배 | 빅 배스 의심 격상 |
| 손상 cluster 동시 종류 | ≥ 3 종 | 패턴 ledger 작성 |
| 차기 분기 영업이익 점프 | ≥ +30% | 회복 진정성 검증 |
| OCF 회복 vs 영업이익 회복 | OCF < 영업이익 | 회계 회복 신호 격상 |
| 동종 업종 평균 손상률 비교 | 회사 / 업종 ≥ 2 배 | 빅 배스 점수 +1 |
| 환입 (Reversal) 발생 | 발생 | 과대 손상 인식 후행 신호 |

## 대표 반환 형태

- `tableRef:bigbath:quarterly_oneoff_loss` — 분기 일회성 손실 시계열
- `tableRef:bigbath:exec_change_timing` — 경영자 변경 ↔ 손실 매칭
- `tableRef:bigbath:impair_cluster` — 손상 cluster 매트릭스
- `tableRef:bigbath:post_recovery` — 차기 분기 회복 ledger
- `valueRef:bigbath:loss_multiple` — 평균 대비 손실 배수
- `valueRef:bigbath:recovery_jump_pct` — 차기 분기 영업이익 점프 %
- `valueRef:bigbath:score` — 빅 배스 종합 점수
- `sourceRef:bigbath:exec_change_id` — 임원변동 공시 id
- `sourceRef:bigbath:impair_note_id` — 손상차손 주석 id
- `executionRef:bigbath:calc_id` — RunPython 실행 id

## 연계 절차

- 영업권 손상 심층 → `recipes.fundamental.quality.forensics.goodwillImpairmentCheck`
- 사건 ↔ 재무 매칭 → `recipes.fundamental.quality.forensics.eventToStatementMatcher`
- 계정 추적 → `recipes.fundamental.quality.forensics.accountTraceLedger`
- 주석 신호 (계속기업·정정) → `recipes.fundamental.quality.forensics.noteSignalExtractor`
- 운전자본 압박 (재고·채권 손상 동행) → `recipes.fundamental.quality.forensics.workingCapitalPressureMap`
- 합병 PPA 영업권 → `recipes.fundamental.quality.forensics.mergerRatioFairness`

재호출 트리거: "신임 경영자 빅 배스", "취임 직후 손실", "손상차손 일시 집중", "구조조정 충당금 인식", "차기 회복 패턴".

## 기본 검증

- 분기 IS 시계열 ≥ 12 분기.
- 경영자 변경 timestamp 명시 (취임일·교체일).
- 손상 cluster 항목 ≥ 3 종.
- 차기 분기 영업이익 + OCF 동행 비교.
- 동종 업종 평균 손상률 외부 비교 메모.
- falsifier — 외부 환경 동시 발생 시 분리 어려움 명시.

## AI 직접 사용 방식

1. `ReadSkill` 에서 빅 배스·신임 경영자 손실 질문이면 본 recipe 선정.
2. target stockCode 확인.
3. `Company.panel("IS", freq="Q")` 분기 손익 + `Company.panel("BS", freq="Q")` 충당·영업권.
4. `Company.filings("임원변동")` 경영자 변경 timestamp.
5. `Company.panel("손상차손")` 또는 `Company.panel("충당부채")` 주석 본문.
6. RunPython 으로 6 패턴 신호 + 차기 회복 회귀 계산.
7. 답변에 *분기 손실 시계열 + 경영자 timing + 손상 cluster + 차기 회복 ledger* 4 셋 + 반례·한계 필수.
