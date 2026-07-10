---
id: recipes.fundamental.quality.forensics.ownershipDisparityMap
title: 지분율 괴리도·순환출자·차등의결권 진단
category: recipes
kind: recipe
scope: builtin
status: curated
graphTier: L1.5
cluster: incubator.forensics
purpose: 지배주주의 *현금흐름권* (배당 받을 권리) vs *의결권* (지배력) 괴리도, 순환출자·피라미드 지배구조 깊이, 차등의결권·복수의결권·황금주 활용을 공시·사업보고서·지분율 본문으로 정량 분해하는 L1.5 절차. 트리거 — '지분율 괴리', '순환출자', '피라미드 지배구조', '차등의결권', '지주사 전환 지배권 강화'.
whenToUse:
  - 지배주주 의결권 vs 배당권 분리
  - 순환출자 고리 정량
  - 피라미드 깊이 측정
  - 지주사 전환 시 지배권 변화
  - 차등의결권 도입 (벤처기업법 2023~)
  - 황금주 옵션 잔존
  - 해외 상장 차등의결권 (알리바바·구글)
linkedSkills:
  - recipes.fundamental.quality.forensics.index
  - recipes.fundamental.quality.forensics.controllingPowerJudgment
  - recipes.fundamental.quality.forensics.treasuryStockUsage
  - recipes.fundamental.quality.forensics.mergerRatioFairness
  - engines.company
inputs:
  - Company.panel 주주현황 / 지분율 / 특수관계자
  - Company.panel 계열회사 / 종속기업 / 관계기업
  - Company.filings (지분 변동·합병·분할·지주사 전환)
  - scan governance (지분율·사외이사·감사)
outputs:
  - 지배주주 의결권 vs 배당권 매트릭스
  - 순환출자 그래프 (피라미드 깊이)
  - 차등의결권·황금주 활용 ledger
  - 지주사 전환 시 지배권 변화 ledger
capabilityRefs:
  - Company.panel
  - Company.filings
  - scan
toolRefs:
  - EngineCall
  - RunPython
sourceRefs:
  - dartlab://skills/recipes.fundamental.quality.forensics.ownershipDisparityMap
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - 의결권 vs 배당권 괴리도
  - 순환출자 그래프 + 피라미드 깊이
  - 차등의결권·황금주 활용 ledger
  - 엔진 승격 후보 메모

forbidden:
  - 지분율 괴리 = 부정 단정 시 *국가별 제도 차이* (한국 차등의결권 벤처기업법 2023~ vs 미국 듀얼클래스 일반화) 명시 누락 금지.
  - 순환출자 = 위법 단정 시 *공정거래법 2014~ 금지* 시점 + 기존 보유분 *해소 의무* 별도 명시.
  - 피라미드 깊이 평가 시 *간접 지분율 계산* 방법 (곱셈 vs 단순 합) 모호 금지.
  - 차등의결권 도입 시 *국내 벤처기업법 (2023 시행) 제한 조건* (비상장 + 일정 요건) 명시 누락 금지.
  - 한 시점 지분율 만 보고 단정 — 시계열 변동 + 동행 사건 (지주사 전환·합병) 동시 평가.
failureModes:
  - 지분율 = 의결권 단정 — *우선주·자기주식 의결권 제외* 무시
  - 피라미드 깊이 측정 시 *간접 지분율* 곱셈 누락
  - 순환출자 = 위법 단정 시 *2014 이전 보유분 grandfather* 무시
  - 지주사 전환 = 지배권 강화 단정 시 *주주환원·지배구조 단순화* 정상 목적 무시
  - 차등의결권 = 부정 단정 시 *벤처기업 인재 유치·장기경영* 정상 목적 무시
  - 우선주 무의결권 = 지배권 강화 도구 단정 시 *배당 우선권* 정상 목적 혼동
examples:
  - 알리바바 차등의결권 미국 상장 (4 권)
  - 구글·메타 듀얼클래스 (DeepDive)
  - 한국 재벌 피라미드 (삼성·SK·LG·현대차 등)
  - 순환출자 해소 사례 (2014 공정거래법 개정 후)
  - 지주사 전환 사례 (LG·SK·CJ·롯데)
  - 황금주·우선주 활용 사례
  - 손정의 알리바바 지분 vs 마윈 지배권 (4 권)
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
  description: "주주현황·계열회사·지분율 본문 부재 시 괴리도 정량화 불가 — *사업보고서 지분율 섹션 + 계열회사 현황 fetch 후 재호출* 한계 명시. 또한 *차등의결권 도입 시점* (벤처기업법 2023) 명시 없이 한국 일반 기업 차등의결권 단정 보류."
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

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.panel("IS"|"BS"|"CF")`, `Company.filings`, `scan.quality`, `scan.audit`, `scan.disclosureRisk` 는 엔진 호출로 근거를 먼저 확보한다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildEvidenceForensicsMemo` 로 묶는 **RunPython fallback** 절차다 — 지분 불일치 — falsifier.

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
    table=memo["tables"]["falsifierLedger"],
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

*의결권 vs 배당권 괴리 + 순환출자 고리 + 피라미드 깊이 + 차등의결권 활용 + 지주사 전환 효과* 한 문장.

좋은 결론 예시:
- "삼성그룹 케이스 — 지배주주 직접 지분 X%, 그룹 의결권 (계열사 우호 지분 합산) Y%. 의결권 / 배당권 = M 배 (괴리). 피라미드 깊이 K 단계 (지배주주 → A → B → C → 삼성전자). 자기주식 잔액 Z%. 순환출자 잔존 없음 (2014 이후 해소). 차등의결권 미도입 (벤처기업법 미적용). *피라미드 깊이 [높음] + 의결권 괴리 [큼] [conf:75]*. counter — 한국 일반 기업은 차등의결권 미허용 환경이라 *지분 < 의결권* 패턴이 *제도적 구조* 의 산물 측면 별도 메모."

금지:
- 우선주·자기주식 의결권 제외 미고려.
- 한국 차등의결권 단정 시 벤처기업법 2023 시행 + 비상장 한정 조건 미명시.

### 2. 핵심 근거 수집

`requiredEvidence: skillRef + target + tableRef + valueRef + dateRef + sourceRef + executionRef` 필수.

- **target** (stockCode).
- **sourceRef**: 사업보고서 주주현황·계열회사·특수관계자 섹션 + 지주사 전환 공시 + 지분 변동 공시.
- **tableRef** (4+ 표):
  1. **의결권 vs 배당권 매트릭스** — 지배주주·특수관계자 직접 지분 / 의결권 / 배당권 / 우선주 / 자기주식 분리
  2. **피라미드 그래프** — 지배주주 → 계열사 A → 계열사 B → 대상 회사 (간접 지분율 곱셈)
  3. **순환출자 고리** — 계열사 간 상호 지분 매트릭스 (2014 이전 보유분 vs 신규)
  4. **차등의결권·황금주 ledger** — 도입 시점·조건·잔존 (한국 벤처기업법 2023~ 적용 여부)
- **valueRef**: 직접 지분 %, 의결권 %, 배당권 %, 의결권/배당권 비율, 피라미드 깊이, 자기주식 %.
- **dateRef**: 지분 변동일·지주사 전환일·차등의결권 도입일.
- **executionRef**: RunPython 으로 간접 지분 곱셈 + 의결권 합산 계산.

### 3. 메커니즘 분석

지분율 괴리도 진단 = *의결권 vs 배당권 + 피라미드 깊이 + 순환출자 + 차등의결권 4 차원 동시 검증*:

```mermaid
graph LR
  SHAREHOLDER["지배주주 본인"] --> DIRECT["직접 지분"]
  SHAREHOLDER --> AFFIL["계열사 보유 지분<br/>(특수관계자)"]
  DIRECT --> VOTING["의결권 합계"]
  AFFIL --> VOTING

  DIRECT --> DIVIDEND["배당권"]
  AFFIL_INDIRECT["간접 지분율<br/>(계열사 지분 × 본인 계열사 지분)"] --> DIVIDEND_INDIRECT["간접 배당권"]

  VOTING --> GAP["의결권 / 배당권 ratio"]
  DIVIDEND --> GAP
  DIVIDEND_INDIRECT --> GAP

  SHAREHOLDER --> LAYER1["계열사 A"]
  LAYER1 --> LAYER2["계열사 B"]
  LAYER2 --> LAYER3["대상 회사"]
  LAYER3 --> DEPTH["피라미드 깊이"]

  AFFIL --> CIRCLE["순환출자 매트릭스"]
  CIRCLE --> LEGAL["2014~ 신규 금지<br/>+ 기존 해소 의무"]

  DUAL["차등의결권"] --> KR_LIMIT["한국 — 벤처기업법 2023~<br/>비상장 한정"]
  GOLDEN["황금주"] --> KR_LIMIT

  TREASURY["자기주식"] --> VOTE_REMOVE["의결권 제외"]
  TREASURY --> POWER["지배권 강화 수단"]
```

**5 패턴 정량 신호**:

| 패턴 | 신호 | 임계 | 가중치 |
|---|---|---|---|
| **의결권 / 배당권 괴리** | 의결권 / 배당권 비율 | ≥ 2 배 | high |
| **피라미드 깊이** | 지배주주 → 대상 회사 단계 수 | ≥ 4 단계 | high |
| **간접 지분율** | 본인 계열사 지분 × 계열사 대상 지분 | ≤ 15% (간접) | medium |
| **자기주식 활용** | 자기주식 / 발행주식 | ≥ 10% | medium |
| **순환출자 잔존** | 2014 이후 신규 발생 | 발생 | high |
| **순환출자 해소** | 2014 이전 보유분 해소 진행 | 미해소 잔존 | medium |
| **차등의결권 (한국)** | 벤처기업법 2023~ 적용 여부 | 비상장 + 요건 충족 | high |
| **황금주 보유** | 거부권 보유 잔존 | 발생 | high |

### 4. 반례·한계

- **Falsifier**: 주주현황·계열회사 본문 부재 시 괴리도 정량화 불가 — *사업보고서 지분율 섹션 + 계열회사 현황 fetch 후 재호출*.
- **한국 차등의결권 제도 차이**: 한국은 *상장사 차등의결권 미허용* 이라 일반 기업에서 차등의결권 단정 금지. 벤처기업법 2023 시행으로 *비상장 벤처* 한정 허용. 미국 (구글·메타·알리바바) 듀얼클래스 와 직접 비교 어려움.
- **순환출자 grandfather 조항**: 2014 공정거래법 개정으로 *신규 순환출자* 금지지만 *기존 보유분* 은 일정 기간 해소 의무. 단순 잔존 = 위법 단정 금지.
- **간접 지분율 계산 방법**: 피라미드 통과 시 *지분율 곱셈* 이 표준이지만 *의결권* 은 *지배 다수결* 원칙 (50% 이상 보유 시 100% 의결권 통제) 으로 곱셈 ≠ 의결권. 본 recipe 에서는 배당권 만 곱셈, 의결권은 *지배 다수결* 적용.
- **자기주식 의결권 제외**: 자기주식은 의결권 제외이지만 *처분 시* 의결권 부활. 단순 잔액 보다 *처분 가능성* 동행 평가.
- **우선주 의결권**: 한국 우선주는 *무의결권* 이 일반이라 의결권에서 제외. 단 *전환우선주* 는 전환 시 의결권 부활.
- **황금주 한국 미허용**: 한국 일반 기업 황금주 미허용. 다만 *외국 합작 회사* (예 일부 외국 자본 진출 사례) 에서 잔존 가능.
- **연결 vs 별도**: 본 recipe 는 *지배 구조 진단* 이라 별도 재무제표 (지분만) 기준. 연결 재무제표와 다를 수 있음.

### 5. 후속 모니터링

| 신호 | 임계 | 조치 |
|---|---|---|
| 의결권 / 배당권 비율 | ≥ 2 배 | 괴리도 ledger 작성 |
| 피라미드 깊이 | ≥ 4 단계 | 지배 구조 복잡도 격상 |
| 자기주식 비중 | ≥ 10% | 잠재 의결권 부활 우려 |
| 순환출자 신규 (2014~) | 발생 | 즉시 위법 의심 |
| 차등의결권 도입 | 도입 발표 | 조건 + 시점 ledger |
| 지주사 전환 | 진행 | 지배권 변화 별도 시뮬레이션 |
| 외국인 지분 변동 | ±5%p / 1Y | 경영권 분쟁 동행 확인 |

## 대표 반환 형태

- `tableRef:ownership:voting_vs_dividend` — 의결권 vs 배당권 매트릭스
- `tableRef:ownership:pyramid_graph` — 피라미드 그래프
- `tableRef:ownership:circular_matrix` — 순환출자 매트릭스
- `tableRef:ownership:dual_class_ledger` — 차등의결권·황금주 ledger
- `valueRef:ownership:voting_dividend_ratio` — 의결권/배당권 비율
- `valueRef:ownership:pyramid_depth` — 피라미드 깊이
- `valueRef:ownership:treasury_pct` — 자기주식 비중
- `valueRef:ownership:indirect_stake_pct` — 간접 지분율
- `sourceRef:ownership:shareholders_id` — 주주현황 섹션 id
- `executionRef:ownership:calc_id` — RunPython 실행 id

## 연계 절차

- 실질지배력 (의결권 합산 동행) → `recipes.fundamental.quality.forensics.controllingPowerJudgment`
- 자사주 활용 (지배권 강화 수단) → `recipes.fundamental.quality.forensics.treasuryStockUsage`
- 합병비율 (지주사 전환 동행) → `recipes.fundamental.quality.forensics.mergerRatioFairness`
- 사건 ↔ 재무 매칭 → `recipes.fundamental.quality.forensics.eventToStatementMatcher`

재호출 트리거: "지분율 괴리도", "순환출자", "피라미드 지배구조", "차등의결권", "지주사 전환 지배권".

## 기본 검증

- 직접 지분 + 의결권 + 배당권 분리.
- 우선주·자기주식 의결권 제외 처리.
- 피라미드 깊이 계산 (간접 지분 곱셈 명시).
- 순환출자 매트릭스 (2014 이전·이후 분리).
- 차등의결권·황금주 도입 여부 + 한국 제도 시점 명시.
- falsifier — 차등의결권 한국 제도 시점 (벤처기업법 2023) 명시.

## AI 직접 사용 방식

1. `ReadSkill` 에서 지분율·지배구조·순환출자 질문이면 본 recipe 선정.
2. target stockCode 확인.
3. `Company.panel("주주현황")` + `Company.panel("최대주주")` + `Company.panel("특수관계자")` 본문.
4. `Company.panel("종속기업")` + `Company.panel("관계기업")` 계열사 매핑.
5. `Company.panel("BS", freq="Y")` 자기주식·우선주 잔액.
6. `scan("governance")` 횡단 비교.
7. RunPython 으로 의결권/배당권 + 간접 지분 + 피라미드 깊이 계산.
8. 답변에 *의결권 vs 배당권 + 피라미드 그래프 + 순환출자 매트릭스 + 차등의결권 ledger* 4 셋 + 반례·한계 필수.
