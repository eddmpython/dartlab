---
id: recipes.fundamental.quality.forensics.lboFairnessAudit
title: LBO 차입매수 적정성·재무부담 진단
category: recipes
kind: recipe
scope: builtin
status: curated
graphTier: L1.5
cluster: incubator.forensics
purpose: 차입매수 (LBO·Leveraged Buyout) 거래에서 *인수가 산정 적정성* + *인수 SPC·SPAC 부채 구조* + *피인수 회사 재무 부담 (Net Debt/EBITDA·이자보상비율·DSCR)* + *합병 후 영업권 손상 가능성* + *사모펀드 의무상환 일정* 5 차원을 IS·BS·CF + 인수 공시 + 합병 공시로 분해하는 L1.5 절차. 트리거 — 'LBO', '차입매수', '사모펀드 인수', 'SPC 합병', '인수 부채 부담', '인수 후 부실'.
whenToUse:
  - LBO 차입매수 진단
  - 사모펀드 인수 적정성
  - SPC·SPAC 합병 후 부채 부담
  - 인수가 산정 적정성
  - 인수 후 영업권 손상 위험
  - PEF (사모펀드) 의무상환 일정
  - 차입매수 후 배당·자사주 환원 패턴
  - 두산주류·하이마트·금호아시아나·보고펀드 류 사례
linkedSkills:
  - recipes.fundamental.quality.forensics.index
  - recipes.fundamental.quality.forensics.mergerRatioFairness
  - recipes.fundamental.quality.forensics.goodwillImpairmentCheck
  - recipes.fundamental.quality.forensics.hybridSecurityClassification
  - recipes.fundamental.quality.forensics.eventToStatementMatcher
  - recipes.fundamental.quality.ebitdaCashBridge
  - engines.company
  - engines.credit
inputs:
  - Company.panel BS (이자부 부채·차입금·사채 시계열)
  - Company.panel IS (영업이익·이자비용·EBIT·EBITDA)
  - Company.panel CF (영업현금흐름·CAPEX·FCF·배당)
  - Company.filings (인수·합병·SPC 설립·차입 공시)
  - Company.panel notes 차입금 (만기·금리·담보)
outputs:
  - LBO 거래 구조 분해 ledger
  - 인수가 산정 적정성 (EV/EBITDA + DCF) ledger
  - 피인수 회사 부채부담 비율 시계열
  - 합병 후 영업권 손상 가능성 점수
  - 의무상환 일정 vs FCF 매칭
capabilityRefs:
  - Company.panel
  - Company.filings
toolRefs:
  - EngineCall
  - RunPython
sourceRefs:
  - dartlab://skills/recipes.fundamental.quality.forensics.lboFairnessAudit
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - LBO 거래 구조 + 부채부담 + 의무상환 ledger
  - 인수가 적정성 + 영업권 손상 가능성 점수
  - 엔진 승격 후보 메모

forbidden:
  - LBO 부채 부담 단정 시 *Net Debt/EBITDA + 이자보상비율 + DSCR* 3 종 동시 평가 누락 금지.
  - 인수가 적정 단정 시 *EV/EBITDA + DCF + peer 비교* 3 평가 방식 누락 금지.
  - 사모펀드 의무상환 일정 평가 시 *PEF 펀드 만기 + 회사 FCF 회수 기간* 동행 평가 누락 금지.
  - 합병 후 영업권 손상 단정 시 *시너지 가정* (매출·원가 절감) 신뢰도 별도 검증 의무.
  - 단일 시점 (인수 직후) 만 보고 단정 — 인수 후 3~5 년 시계열 동시 평가.
failureModes:
  - 인수가 = EV/EBITDA 만으로 적정 단정 — DCF·peer 비교·시너지 가정 무시
  - 부채 부담 평가 시 *PEF 운용 부채* 와 *피인수 회사 부채* 혼동
  - 합병 후 영업권 손상 = 시너지 부정확 단정 시 *외부 환경 변화* (다운사이클·환율) 반례 무시
  - 의무상환 일정 평가 시 *상환 vs 차환* 옵션 동행 평가 누락
  - PEF 매각 시점 = 차익 실현 단정 시 *피인수 회사 재무 부담* 후속 부채 이전 무시
  - 합병 직후 자사주 매입·배당 = 정상 환원 단정 시 *부채 상환 능력 약화* 동행 평가 누락
examples:
  - 두산주류 인수 (롯데칠성, EBITDA·OCF·인수가격 적정성)
  - 하이마트 LBO (유진→롯데, 영업권 회계처리 변경)
  - 금호아시아나·대우건설 인수 (LBO 차입매수·풋옵션 우발)
  - 보고펀드 LG실트론 투자 실패 (사모펀드 손실)
  - 두산밥캣 인수 (인수가 적정성·PPA 영업권 손상)
  - 오비맥주 KKR/AEP 인수 (LBO·세무 분쟁)
  - 코웨이 사모펀드 인수·재매각 (PEF 운용)
gap:
  primary:
    - company
    - credit
  secondary:
    - story
testUniverse:
  market: KR
  asOfPolicy: latest
falsifier:
  description: "인수 공시 본문 (EV·EBITDA 산정 기초·SPC 구조) 또는 차입금 주석 (만기·금리·담보) 부재 시 LBO 적정성 판정 불가 — *DART 합병·인수 공시 + 차입금 주석 fetch 후 재호출* 한계 명시. PEF 펀드 만기·매각 시점도 외부 데이터 (펀드 운용 보고서) 필요."
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

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.panel("IS"|"BS"|"CF")`, `Company.filings`, `scan.quality`, `scan.audit`, `scan.disclosureRisk` 는 엔진 호출로 근거를 먼저 확보한다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildEvidenceForensicsMemo` 로 묶는 **RunPython fallback** 절차다 — LBO 공정성 — 엔진 후보.

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

*LBO 거래 구조 + 인수가 적정성 + 부채부담 (Net Debt/EBITDA·이자보상·DSCR) + 의무상환 일정 + 합병 후 영업권 손상 가능성* 한 문장.

좋은 결론 예시:
- "하이마트 LBO 케이스 — 유진그룹 인수가 X 조원 / EBITDA Y = M 배 (EV/EBITDA). 인수 SPC 차입 N 조원 → 피인수 회사 합병 후 Net Debt/EBITDA = K 배 (LBO 기준 ≥ 5 배 위험). 이자보상비율 EBIT/이자 = L 배 (< 2 배 위험). PEF 펀드 만기 Z 년 → FCF 회수 기간 W 년 (만기 < 회수 기간 시 차환 의존). 합병 후 영업권 P 조원 → 시너지 가정 (매출 +Q%) 신뢰도 별도. *LBO 부채 부담 [높음] + 영업권 손상 위험 [중간] [conf:70]*. counter — 롯데 인수 후 재무 안정화 (롯데 캐시 백업) 으로 부담 완화."

금지:
- EV/EBITDA 단독으로 인수가 적정 단정.
- 합병 후 영업권 손상 = 시너지 부정확 단정 시 외부 환경 반례 누락.

### 2. 핵심 근거 수집

`requiredEvidence: skillRef + target + tableRef + valueRef + dateRef + sourceRef + executionRef` 필수.

- **target** (stockCode).
- **sourceRef**: 인수·합병 공시 (DART 주요사항보고서) + 차입금 주석 (만기·금리·담보) + PEF 운용 보고서 (가능 시 외부).
- **tableRef** (5+ 표):
  1. **LBO 거래 구조** — 인수자 (PEF·전략적 투자자) / 인수 SPC 명 / SPC 차입 규모 / 합병 시점 / 합병 후 차입 이전 여부
  2. **인수가 적정성** — EV/EBITDA + DCF + peer 비교 3 방식 동시 평가
  3. **피인수 회사 부채부담 시계열** — Net Debt/EBITDA · 이자보상비율 (EBIT/이자) · DSCR (OCF/이자+상환원금)
  4. **의무상환 일정 vs FCF 매칭** — 만기별 상환 의무 vs 연도별 FCF
  5. **합병 후 영업권** — PPA 영업권 잔액 + 손상검사 결과 + 시너지 가정 (매출·원가) ledger
- **valueRef**: EV/EBITDA multiple, Net Debt/EBITDA, 이자보상비율, FCF, 영업권 잔액.
- **dateRef**: 인수일·합병일·차입 만기일·PEF 펀드 만기일.
- **executionRef**: RunPython 으로 3 방식 평가 + 시계열 회귀 계산.

### 3. 메커니즘 분석

LBO 적정성 진단 = *거래 구조 + 인수가 + 부채부담 + 의무상환 + 영업권 5 차원 동시 검증*:

```mermaid
graph LR
  ACQ["인수자 (PEF·전략적 투자자)"] --> SPC["인수 SPC 설립"]
  SPC --> BORROW["SPC 차입 (대규모)"]
  ACQ --> EQUITY["자기자본 출자 (소액)"]
  BORROW --> ACQUIRE["피인수 회사 지분 100%"]
  EQUITY --> ACQUIRE

  ACQUIRE --> MERGE["합병 (SPC + 피인수 회사)"]
  MERGE --> DEBT_TRANSFER["SPC 차입이 피인수 회사 부채로 이전"]
  DEBT_TRANSFER --> POST_BS["합병 후 BS — 부채 급증"]

  POST_BS --> NDE["Net Debt / EBITDA"]
  POST_BS --> ICR["이자보상비율 EBIT / 이자"]
  POST_BS --> DSCR["DSCR = OCF / (이자 + 원금)"]

  EV["인수가 EV"] --> APPRAIS["EV / EBITDA + DCF + peer"]
  EBITDA_REF["EBITDA"] --> APPRAIS

  MERGE --> GOODWILL["PPA 영업권"]
  GOODWILL --> IMPAIR["손상검사"]
  SYNERGY["시너지 가정<br/>매출·원가"] --> IMPAIR

  PEF_MATURITY["PEF 펀드 만기"] --> EXIT["매각 시점"]
  FCF["연도별 FCF"] --> RECOV["FCF 회수 기간"]
  EXIT --> COMP_TIMING["만기 vs 회수 비교"]
  RECOV --> COMP_TIMING

  NDE --> SCORE["LBO 위험 점수"]
  ICR --> SCORE
  DSCR --> SCORE
  IMPAIR --> SCORE
  COMP_TIMING --> SCORE
```

**5 패턴 정량 신호**:

| 패턴 | 신호 | 임계 | 가중치 |
|---|---|---|---|
| **인수가 적정** | EV/EBITDA vs peer 평균 | ±50% 이상 차이 | high |
| **인수가 적정** | DCF·peer·EV/EBITDA 3 방식 분산 | ≥ 30% | medium |
| **부채부담** | Net Debt / EBITDA | ≥ 5 배 | high |
| **부채부담** | 이자보상비율 (EBIT/이자) | < 2 배 | high |
| **부채부담** | DSCR = OCF / (이자 + 원금) | < 1.5 배 | high |
| **의무상환 매칭** | PEF 펀드 만기 vs FCF 회수 기간 | 만기 < 회수 (차환 의존) | high |
| **합병 후 영업권** | 영업권 / 자본총계 | ≥ 30% | medium |
| **시너지 가정 신뢰** | 합병 후 매출 / 시너지 가정 | < 70% / 3Y | high |
| **환원 패턴** | 합병 후 1~2Y 자사주·배당 (PEF 환원) | 발생 + 부채 동시 증가 | medium |

### 4. 반례·한계

- **Falsifier**: 인수 공시 본문 또는 차입금 주석 부재 시 LBO 적정성 판정 불가 — *DART 합병·인수 공시 + 차입금 주석 fetch 후 재호출*.
- **PEF 운용 정보 비공개**: 사모펀드 (PEF) 펀드 만기·매각 일정·LP·GP 구조는 *비공개* 가 다수 → 외부 보고서·언론·운용사 공시 별도 fetch 필요. dartlab L1/L1.5 범위 일부 한정.
- **시너지 가정 자기실현 어려움**: 인수가 산정 시 시너지 가정 (매출 +X% / 원가 절감 -Y%) 은 *예측* 이지 *fact* 아님. 합병 후 3~5 년 실현률 별도 검증.
- **롯데·SK 등 대기업 인수 시 캐시 백업**: 전략적 투자자 (대기업) 인수의 경우 *그룹 캐시 백업* 으로 부채부담 완화 가능. 단순 Net Debt/EBITDA 만으로 위험 단정 금지.
- **합병 직전 자사주 처분·발행**: 합병 직전 *자사주 처분* 또는 *신주 발행* 으로 인수자 지분 강화 가능. 거래 구조 본문 확인 필수.
- **외부 환경 변화**: 인수 후 다운사이클·환율·금리 충격 시 EBITDA 급감 → LBO 부담 자동 격상. 인수 책임 vs 환경 책임 분리 어려움.
- **차환 (refinancing) 옵션**: PEF 펀드 만기 < FCF 회수 기간이라도 *차환* (refinancing) 으로 만기 연장 가능. 차환 시장 환경 (금리·신용시장) 별도 평가.
- **인수가 < 시장가 케이스**: 부실 자산 인수 (저점 매수) 인 경우 EV/EBITDA peer 비교가 잘못된 기준 — DCF 또는 NAV 적용.

### 5. 후속 모니터링

| 신호 | 임계 | 조치 |
|---|---|---|
| Net Debt / EBITDA | ≥ 5 배 / 3Y | 부채부담 격상 |
| 이자보상비율 | < 2 배 | 즉시 위험 |
| DSCR | < 1.5 배 | 차환 의존 격상 |
| 합병 후 영업권 손상 | 발생 / 3Y | 시너지 가정 부정확 신호 |
| 합병 후 자사주·배당 | 발생 + 부채 증가 동행 | PEF 환원 의심 격상 |
| PEF 매각 시점 | 임박 (펀드 만기 -1Y) | 매각 후 부채 이전 추적 |
| 인수가 시계열 EBITDA 추세 | -10% / 1Y | 시너지 미실현 신호 |

## 대표 반환 형태

- `tableRef:lbo:transaction_structure` — LBO 거래 구조
- `tableRef:lbo:acquisition_appraisal` — 인수가 3 방식 평가
- `tableRef:lbo:debt_burden_timeseries` — 부채부담 시계열
- `tableRef:lbo:debt_service_schedule` — 의무상환 일정 vs FCF
- `tableRef:lbo:post_merger_goodwill` — 합병 후 영업권
- `valueRef:lbo:ev_ebitda` — EV/EBITDA
- `valueRef:lbo:net_debt_to_ebitda` — Net Debt / EBITDA
- `valueRef:lbo:interest_coverage_ratio` — 이자보상비율
- `valueRef:lbo:dscr` — DSCR
- `valueRef:lbo:goodwill_to_equity` — 영업권 / 자본총계
- `sourceRef:lbo:acquisition_id` — 인수 공시 id
- `sourceRef:lbo:merger_id` — 합병 공시 id
- `executionRef:lbo:calc_id` — RunPython 실행 id

## 연계 절차

- 합병비율 적정성 → `recipes.fundamental.quality.forensics.mergerRatioFairness`
- 영업권 손상 (합병 후 시너지 부정확) → `recipes.fundamental.quality.forensics.goodwillImpairmentCheck`
- 영구채·CB·RCPS 분류 (인수 자금 조달) → `recipes.fundamental.quality.forensics.hybridSecurityClassification`
- 사건 ↔ 재무 매칭 → `recipes.fundamental.quality.forensics.eventToStatementMatcher`
- EBITDA·OCF·인수가격 bridge → `recipes.fundamental.quality.ebitdaCashBridge`

재호출 트리거: "LBO 차입매수", "사모펀드 인수", "SPC 합병 부채 이전", "Net Debt EBITDA 인수", "PEF 만기 회수 매칭".

## 기본 검증

- 인수·합병 공시 + 차입금 주석 ≥ 1 종.
- 인수가 3 방식 평가 (EV/EBITDA + DCF + peer).
- 부채부담 3 비율 (Net Debt/EBITDA + 이자보상 + DSCR).
- 합병 후 영업권 시계열 ≥ 3 년.
- PEF 펀드 만기 vs FCF 회수 기간 비교.
- falsifier — PEF 운용 비공개 한계 명시.

## AI 직접 사용 방식

1. `ReadSkill` 에서 LBO·사모펀드·차입매수 질문이면 본 recipe 선정.
2. target stockCode 확인 (피인수 회사 기준).
3. `Company.panel("BS","IS","CF",freq="Y")` 시계열 + 분기 보완.
4. `Company.filings("인수","합병")` 거래 공시.
5. `Company.panel("차입금")` 만기·금리·담보 주석.
6. RunPython 으로 3 방식 평가 + 3 비율 시계열 + 영업권 손상 계산.
7. 답변에 *거래 구조 + 인수가 평가 + 부채부담 시계열 + 의무상환 + 영업권* 5 셋 + 반례·한계 필수.
