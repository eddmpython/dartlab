---
id: recipes.fundamental.quality.forensics.disclosureTimingAnomaly
title: 공시 타이밍 이상 — 늑장·집중·호재 부풀리기 진단
category: recipes
kind: recipe
scope: builtin
status: curated
graphTier: L1.5
cluster: incubator.forensics
purpose: 부정적 사건의 공시 지연 (늑장공시) · 호재 공시 집중·반복 발표 · 실적 발표 직전 비공식 가이던스 · 보물선/신사업 류 일시 호재 패턴을 공시 timestamp + 본문 + 후속 정정·재공시 시계열로 진단하는 L1.5 절차. 트리거 — '늑장공시', '공시 timing', '호재 부풀리기', '어닝 서프라이즈 게임', '정정공시'.
whenToUse:
  - 공시 지연 의심
  - 호재 공시 집중 발표
  - 정정공시 패턴
  - 실적 발표 직전 비공식 가이던스
  - 일시 호재 (보물선·신사업·MOU) 반복
  - 거래정지 직전 공시 의무
  - 자율공시 vs 의무공시 선택 편향
linkedSkills:
  - recipes.fundamental.quality.forensics.index
  - recipes.fundamental.quality.forensics.noteSignalExtractor
  - recipes.fundamental.quality.forensics.eventToStatementMatcher
  - recipes.fundamental.quality.forensics.accountTraceLedger
  - recipes.fundamental.quality.forensics.controllingPowerJudgment
  - engines.company
  - engines.scan
inputs:
  - Company.filings (공시 본문·timestamp)
  - Company.panel 주요사항보고 / 자율공시 시계열
  - scan disclosureRisk (정정·지연·반복 패턴 횡단)
  - Company.panel IS / BS (공시-실적 연결)
outputs:
  - 공시 timestamp ledger (의무 vs 자율, 정정 횟수)
  - 호재·악재 균형 ledger
  - 정정공시 / 늑장공시 신호 점수
  - 어닝 서프라이즈 game 신호 (실적 발표 직전 비공식 가이던스 빈도)
capabilityRefs:
  - Company.panel
  - Company.filings
  - scan
toolRefs:
  - EngineCall
  - RunPython
sourceRefs:
  - dartlab://skills/recipes.fundamental.quality.forensics.disclosureTimingAnomaly
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - 공시 timestamp ledger + 정정·지연 빈도
  - 호재/악재 균형 + 발표 timing 분포 매트릭스
  - 늑장공시 신호 점수
  - 엔진 승격 후보 메모

forbidden:
  - 늑장공시 단정 시 의무공시 기한 (사유 발생 익일·주요사항보고 3 일 등) 근거 누락 금지.
  - 호재 공시 부풀리기 단정 시 동일 호재 *반복 공시 횟수* + *후속 매출/이익 반영* 동행 검증 누락 금지.
  - 정정공시 발생 시 *최초 공시 vs 정정 본문 차이* 명시 누락 금지.
  - 실적 발표 직전 가이던스 단정 시 *외부 소스* (IR 자료·언론·애널리스트 리포트) 별도 1 차 확인 의무.
  - 공시 timestamp 만 보고 회사 의도 단정 — *법규 기한 + 본문 변화* 동행 평가.
failureModes:
  - 공시 지연 = 늑장 단정 시 *실제 사건 발생일 vs 공시일* 차이 misread (사건 정확일 불명 가능성)
  - 호재 반복 공시 분류 시 *원공시 + 진행상황 추가 공시* 정상 패턴 무시
  - 정정공시 = 회계 부실 단정 시 *단순 typo / 첨부 누락* 정정 혼동
  - 어닝 서프라이즈 = game 단정 시 *시장 합의 추정치* (estimate) 출처 누락
  - 보물선 / 신사업 MOU 반복 = 부풀리기 단정 시 *실제 매출 발생 시점* 별도 검증 누락
examples:
  - 한화 늑장공시 (상장폐지 실질심사) — 3 권 매칭
  - 동아건설·삼애앤더스 보물선 일시 호재 (4 권)
  - 마텔 부정 뉴스 늦은 공시 (1 권)
  - 삼성전자·LG전자 어닝 서프라이즈 게임 (2 권)
  - CJ E&M 실적 발표 직전 내부정보 (4 권)
  - 신라젠·바이오 종목 임상 진행 반복 공시
  - 코인 / NFT 신사업 MOU 반복 발표 패턴
gap:
  primary:
    - company
    - scan
  secondary:
    - story
testUniverse:
  market: KR
  asOfPolicy: latest
falsifier:
  description: "공시 timestamp 또는 본문 부재 시 timing 진단 불가 — *DART 원문 fetch 후 재호출* 한계 명시. 또한 *시장 합의 추정치* 외부 데이터 없으면 어닝 서프라이즈 game 판정 보류."
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

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.panel("IS"|"BS"|"CF")`, `Company.filings`, `scan.quality`, `scan.audit`, `scan.disclosureRisk` 는 엔진 호출로 근거를 먼저 확보한다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildEvidenceForensicsMemo` 로 묶는 **RunPython fallback** 절차다 — 공시 timing 이상 — event-statement 매칭.

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

*공시 timestamp 이상 + 호재·악재 균형 + 정정·반복 패턴 + 어닝 시즌 game 신호* 한 문장.

좋은 결론 예시:
- "한화 케이스 — 상장폐지 실질심사 사유 발생 D+N 일 공시 (의무공시 기한 초과). 동일 분기 호재 공시 X 건 (자율) vs 악재 공시 1 건 (의무). 정정공시 Y 회 발생, 정정 본문 핵심 숫자 변경 (매출 -Z%). *늑장공시 + 호재 부풀리기 결합 [conf:75]*. counter — 실제 사유 발생일 확정 어려움."

금지:
- 의무공시 기한 (법규) 미명시 단정.
- 호재 반복 공시 + 후속 매출 반영 비교 누락.

### 2. 핵심 근거 수집

`requiredEvidence: skillRef + target + tableRef + valueRef + dateRef + sourceRef + executionRef` 필수.

- **target** (stockCode).
- **sourceRef**: 공시 원문 (DART 주요사항보고 / 자율공시 / 정정공시). 외부 IR 자료·언론 보도 timing 별도.
- **tableRef** (4+ 표):
  1. **공시 timestamp ledger** — 공시일 / 사건 발생일 / 의무공시 기한 / 지연 일수 / 의무 vs 자율 구분
  2. **호재·악재 균형** — 분기·연도별 호재 (자율공시 多) vs 악재 (의무공시 多) 건수
  3. **정정공시 ledger** — 최초 공시일 / 정정일 / 본문 변경 핵심 (매출·이익·일정·숫자)
  4. **어닝 시즌 timing** — 잠정실적 발표일 / 확정 공시일 / 시장 합의 추정치 (있다면) vs 실제 차이
- **valueRef**: 지연 일수 평균·중앙값, 정정 횟수, 호재/악재 비율.
- **dateRef**: 분기 발표일·잠정실적일·정정일·사건 발생일.
- **executionRef**: RunPython 으로 timing 분포 + 정정 본문 차이 계산.

### 3. 메커니즘 분석

공시 타이밍 이상 진단 = *법규 기한 비교 + 호재·악재 균형 + 정정·반복 패턴 + 어닝 시즌 game 신호 4 차원 동시 검증*:

```mermaid
graph LR
  EVENT["사건 발생일"] --> KIH["의무공시 기한<br/>주요사항 D+1 / D+3"]
  EVENT --> ACT_DATE["실제 공시일"]
  KIH --> DELAY["지연 일수"]
  ACT_DATE --> DELAY

  DELAY --> LATE_SIG["늑장공시 신호<br/>기한 초과 + 거래정지 직전"]

  DISC_LOG["공시 시계열"] --> CLS["호재 vs 악재 분류"]
  CLS --> IMBAL["호재 자율 vs 악재 의무<br/>편향 비율"]

  DISC_LOG --> RPT["정정공시 빈도"]
  RPT --> DIFF["정정 본문 차이<br/>매출·이익·일정 변경"]

  EARNINGS["잠정실적일"] --> EST["시장 합의 추정치"]
  EARNINGS --> ACT["실제 발표일"]
  EST --> SURPRISE["서프라이즈 game 신호<br/>직전 가이던스 동행"]
  ACT --> SURPRISE

  LATE_SIG --> SCORE["타이밍 이상 점수"]
  IMBAL --> SCORE
  DIFF --> SCORE
  SURPRISE --> SCORE
```

**4 패턴 정량 신호**:

| 패턴 | 신호 | 임계 | 가중치 |
|---|---|---|---|
| **늑장공시** | 사건 발생일 → 공시일 지연 | 의무공시 기한 초과 | high |
| **늑장공시** | 거래정지 직전 24h 내 부정 공시 | 발생 | high |
| **호재 부풀리기** | 동일 호재 (MOU·신사업) 반복 공시 횟수 | ≥ 3 회 / 6M | medium |
| **호재 부풀리기** | 호재 공시 후 12M 내 실제 매출 반영 | < 10% | high |
| **정정공시** | 정정 본문 핵심 숫자 변경 (매출·이익) | ≥ 5% 변경 | high |
| **어닝 게임** | 잠정실적 직전 비공식 가이던스 | 발생 | medium |
| **어닝 게임** | 매 분기 시장 추정 대비 +1~3% 흑자 | 4 분기 연속 | medium |

### 4. 반례·한계

- **Falsifier**: 공시 timestamp 또는 본문 부재 시 timing 진단 불가 — *DART 원문 fetch 후 재호출*.
- **사건 발생일 확정 어려움**: 의무공시 기한은 *사유 발생 익일* 기준인데, "발생일" 자체가 회사 내부 판단 (이사회 결의일·계약일·인지일) 이라 외부 판정이 항상 명확하지 않다. 늑장 단정 시 *법적 기한 vs 추정 발생일* 별도 메모.
- **반복 공시의 정당성**: 신사업 MOU·R&D 진행상황은 *진행상황 자율공시* 가 정상이라 단순 횟수만 보면 정상 패턴을 부풀리기로 오판할 수 있다. *실제 매출 반영* + *공시 본문 변화* 동행 검증.
- **정정공시 = 회계 부실 ≠**: 정정공시는 typo·첨부 누락 등 단순 정정도 다수. *본문 핵심 숫자 변경 폭* 으로 분류 필요.
- **어닝 서프라이즈 game 외부 소스 의존**: 시장 합의 추정치 (FnGuide·Bloomberg 등) 는 dartlab L1/L1.5 범위 밖. 외부 소스 인용 후 판단.
- **자율공시 편향**: 호재는 자율공시·악재는 의무공시 패턴 자체가 *제도적 구조* (한국 자율공시 도입 의도) 의 산물이라 단순 편향만으로 부풀리기 단정 금지.
- **거래정지 직전 부정 공시**: 거래정지 직전 24h 신호는 강하나, 거래정지 사유 자체가 *공시 누락* 인 경우 인과 역전 (공시 → 정지 vs 정지 → 공시). 사유 별도 확인.

### 5. 후속 모니터링

| 신호 | 임계 | 조치 |
|---|---|---|
| 지연 일수 평균 | ≥ 5 영업일 | 의무공시 위반 추적 |
| 정정공시 횟수 / 분기 | ≥ 3 회 | 정정 본문 차이 ledger 작성 |
| 호재 반복 공시 후속 매출 | < 10% / 12M | 부풀리기 신호 격상 |
| 어닝 서프라이즈 연속 | 4 분기 연속 ±1~3% | 가이던스 game 추적 |
| 정정 본문 매출 변경 폭 | ≥ 10% | 회계 부실 의심 격상 |
| 거래정지 직전 부정 공시 | 발생 | 늑장공시 가중치 high |

## 대표 반환 형태

- `tableRef:timing:disclosure_log` — 공시 timestamp ledger
- `tableRef:timing:event_vs_filing_lag` — 사건 발생 → 공시 지연 일수
- `tableRef:timing:positive_negative_balance` — 호재/악재 균형
- `tableRef:timing:correction_diff` — 정정공시 본문 차이
- `tableRef:timing:earnings_surprise` — 어닝 시즌 timing
- `valueRef:timing:avg_delay_days` — 평균 지연 일수
- `valueRef:timing:correction_count_quarter` — 분기당 정정 횟수
- `valueRef:timing:anomaly_score` — timing 이상 종합 점수
- `sourceRef:timing:disclosure_id` — 공시 id
- `executionRef:timing:calc_id` — RunPython 실행 id

## 연계 절차

- 사건 ↔ 재무 매칭 → `recipes.fundamental.quality.forensics.eventToStatementMatcher`
- 주석 신호 (계속기업·정정) → `recipes.fundamental.quality.forensics.noteSignalExtractor`
- 계정 추적 → `recipes.fundamental.quality.forensics.accountTraceLedger`
- 실질지배력 (정보 비대칭 동행) → `recipes.fundamental.quality.forensics.controllingPowerJudgment`
- 영업권 손상 (호재 반복 후 손상) → `recipes.fundamental.quality.forensics.goodwillImpairmentCheck`

재호출 트리거: "한화 늑장공시", "어닝 서프라이즈 game", "공시 timing 이상", "호재 부풀리기", "정정공시 패턴".

## 기본 검증

- 공시 시계열 ≥ 3 년.
- 의무공시 기한 (법규) 본문 인용.
- 호재·악재 분류 + 분기별 건수.
- 정정공시 발생 시 *본문 차이 핵심 숫자* 명시.
- falsifier — 사건 발생일 확정 어려움 메모.

## AI 직접 사용 방식

1. `ReadSkill` 에서 공시 timing 질문이면 본 recipe 선정.
2. target stockCode 확인.
3. `Company.filings(window="3Y")` 공시 시계열.
4. `Company.panel("IS", freq="Q")` 분기 실적 — 어닝 시즌 timing 비교.
5. `scan("disclosureRisk")` 횡단 비교 — 동종 업종 평균 대비.
6. RunPython 으로 4 패턴 신호 점수 계산.
7. 답변에 *timestamp ledger + 호재·악재 균형 + 정정 차이 + 어닝 시즌 timing* 4 셋 + 반례·한계 필수.
