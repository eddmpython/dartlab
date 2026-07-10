---
id: recipes.fundamental.quality.forensics.goodwillImpairmentCheck
title: 영업권 손상검사 정량 (forensics)
category: recipes
kind: recipe
scope: builtin
status: curated
graphTier: L1.5
cluster: incubator.forensics
purpose: 인수 후 누적 영업권의 손상검사 적정성을 영업권/자산·영업권/시총 비율 + CGU 별 회수가능액 vs 장부가 + 손상검사 가정 (할인율·성장률) + 인수 segment 영업이익 추세 4 차원으로 진단하는 L1.5 절차. 트리거 — '영업권 손상', '인수 후 사후평가', 'PPA 결과', '인수 segment 이익 악화'.
whenToUse:
  - 영업권 손상검사
  - PPA 사후평가
  - 인수 segment 이익 악화
  - 무형자산 손상
  - M&A 후 영업권 비중
inputs:
  - Company.panel BS (영업권 · 무형자산)
  - 사업보고서 주석 (영업권 손상검사 가정)
  - 부문 (segment) IS 시계열
outputs:
  - 영업권/총자산 · 영업권/시총 비율
  - CGU 별 손상검사 가정 ledger
  - 인수 segment 영업이익 추세
  - 손상 위험 점수
capabilityRefs:
  - Company.panel
  - Company.filings
toolRefs:
  - EngineCall
  - RunPython
sourceRefs:
  - dartlab://skills/recipes.fundamental.quality.forensics.goodwillImpairmentCheck
linkedSkills:
  - recipes.fundamental.quality.forensics.index
  - recipes.fundamental.quality.forensics.noteSignalExtractor
  - recipes.fundamental.quality.forensics.mergerRatioFairness
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
  - 영업권 비중 ledger
  - CGU 별 손상검사 가정 추적
  - 손상 위험 점수 + counter evidence

forbidden:
  - 영업권 손상 단정 시 *CGU 별 손상검사 가정 (할인율·성장률)* 명시 누락 금지.
  - 영업권/총자산 비율만 보고 *손상 위험* 단정 — *인수 segment 영업이익 추세* 동행 필수.
  - 손상검사 가정 (할인율) 이 *변경 없이 5 년 이상 유지* 시 검증 없이 적정 단정 금지.
  - 인수 segment 영업이익 마이너스 + 영업권 손상 0 인 *모순* 인식 없이 결론 금지.
  - 손상검사 *민감도 분석 (할인율 ±50bp / 성장률 ±100bp)* 미명시 시 의견 단정 금지.
failureModes:
  - 영업권/총자산 임계 (15%+) 만 보고 *모든 회사* 동일 기준 적용
  - CGU 별 분해 없이 *연결 영업권 합계* 만 검사
  - 손상검사 가정 (할인율) 부재 시 *적정* 단정
  - 인수 segment 영업이익 악화 → 영업권 손상 0 의 *지연* 무인지
  - 사업보고서 주석 미참조
examples:
  - 두산밥캣 영업권 손상검사 추적
  - STX유럽 인수 후 영업권 손상
  - 카카오 M&A 영업권 누적
  - CJ ENM 인수 segment 손상 위험
  - 동양생명·푸르덴셜 영업권
gap:
  primary:
    - company
    - analysis
  secondary:
    - industry
testUniverse:
  market: KR
  asOfPolicy: latest
falsifier:
  description: "영업권 잔액 또는 사업보고서 주석 (손상검사 가정) 이 부재하면 손상 위험 판정 불가 — *주석 본문 확인 후 재호출* 명시."
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

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.panel("IS"|"BS"|"CF")`, `Company.filings`, `scan.quality`, `scan.audit`, `scan.disclosureRisk` 는 엔진 호출로 근거를 먼저 확보한다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildEvidenceForensicsMemo` 로 묶는 **RunPython fallback** 절차다 — 영업권 손상 — 계정 추적.

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
    table=memo["tables"]["accountTraceLedger"],
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

*영업권/총자산·시총 비율 + CGU 별 손상검사 가정 + 인수 segment 영업이익 추세 + 손상 위험 점수* 한 문장.

좋은 결론 예시:
- "005380 (현대차) 영업권 X 조 = 총자산 Y%·시총 Z% — 임계 (15%) 이내, 손상 위험 낮음. 인수 segment Q 영업이익 4 분기 추세 +5% 안정, 손상검사 할인율 12.5% (변경 없음 3 년 유지) — 가정 변경 점검 권장 [conf:70]."
- "두산밥캣 영업권 누적 4.2 조 = 총자산 38%·시총 65% — 임계 초과. 인수 segment 영업이익 -15% 추세, 손상 0 = *지연 가능성* [conf:60]. 주석 손상검사 가정 (할인율 11%·성장률 3%) 민감도 ±100bp 분석 필요."

금지:
- 영업권 비율만 보고 *위험* 단정. *인수 segment 영업이익 추세* 동행 필수.
- CGU 별 분해 없이 연결 영업권 합계만 검사.

### 2. 핵심 근거 수집

`requiredEvidence: skillRef + target + tableRef + valueRef + dateRef + sourceRef + executionRef` 필수.

- **target**: stockCode.
- **sourceRef**: 사업보고서 주석 (영업권 손상검사 가정 명시 — 할인율·성장률·CGU 분류).
- **tableRef** (4+ 표):
  1. **영업권 시계열** — 최근 5 년 BS 영업권 · 무형자산 · 총자산 · 영업권/자산 % · 영업권/시총 %
  2. **CGU 분해** — 사업 부문별 영업권 잔액 · 손상검사 가정 (할인율·성장률·multiple) · 회수가능액 vs 장부가
  3. **인수 segment 추세** — 부문 IS 영업이익 4+ 분기 (인수 후 누적 추세)
  4. **민감도 분석** — 할인율 ±50bp / 성장률 ±100bp 시 회수가능액 변동
- **valueRef**: 영업권/자산 %·영업권/시총 %·인수 segment 영업이익 추세·민감도 결과.
- **dateRef**: BS 기준일·주석 손상검사 시점·인수 segment 분기.
- **sourceRef**: 사업보고서 주석 id · 인수 공시 id.
- **executionRef**: RunPython 계산 id.

### 3. 메커니즘 분석

영업권 손상검사 정량 = *비중 임계 + CGU 가정 추적 + segment 추세 + 민감도*:

```mermaid
graph LR
  BS["BS 영업권 시계열"] --> RATIO["영업권 비중<br/>① /총자산<br/>② /시총<br/>③ /자본총계"]
  RATIO --> THRESH["임계 비교<br/>(15% / 30% / 50%)"]
  
  NOTES["사업보고서 주석"] --> CGU["CGU 별 분해"]
  CGU --> ASSUM["가정 ledger<br/>할인율 · 성장률 · multiple"]
  ASSUM --> SENS["민감도 분석<br/>±50bp / ±100bp"]
  
  SEGMENT["부문 IS 4+ 분기"] --> TREND["인수 segment 영업이익 추세"]
  TREND --> DELAY["손상 지연 의심<br/>(이익 악화 + 손상 0)"]
  
  THRESH --> SCORE["손상 위험 점수"]
  SENS --> SCORE
  DELAY --> SCORE
```

**영업권 비중 임계** (KR 시장 기준):

| 비율 | 보통 | 주의 | 위험 |
|---|---|---|---|
| 영업권 / 총자산 | < 5% | 5~15% | > 15% |
| 영업권 / 시총 | < 10% | 10~30% | > 30% |
| 영업권 / 자본총계 | < 20% | 20~50% | > 50% |

**손상 지연 신호** (정량):

| 신호 | 임계 | 가중치 |
|---|---|---|
| 인수 segment 영업이익 YoY | -10%+ 4 분기 연속 | high |
| 영업권 손상 인식 | 인수 후 3 년+ 0 | high |
| 손상검사 할인율 변경 | 5 년+ 변동 X | medium |
| CGU 분해 부재 | 주석 미명시 | medium |
| 민감도 분석 미명시 | 주석 누락 | low |

**손상검사 가정 검증**:
- **할인율 (WACC)** — 회사 위험 + 산업·국가 risk premium. 5 년 변동 X 면 *시장 변화 미반영* 의심.
- **영구 성장률 (g)** — 통상 1~3%. 5%+ 면 비현실적.
- **CGU 분류** — 사업 부문별 분해 명시. 연결 합계만이면 검증 약함.
- **multiple** — 산업 평균 EBITDA × — 산업 비교 가능.

### 4. 반례·한계

- **Falsifier**: 영업권 잔액 + 주석 가정 부재 시 판정 불가 — 주석 본문 확인 후 재호출.
- **회계 정책**: K-IFRS vs US GAAP 손상검사 빈도 차이. KR 은 연 1 회 의무, US 는 trigger event.
- **CGU 정의**: 회사 자체 결정. 광범위 정의 (사업 부문 = 회사 전체) 면 손상 인식 어려움.
- **민감도 비공개**: 주석에 민감도 분석 미명시 시 외부 추정 한계.
- **인수 시점 가정 vs 현 시점**: 인수 시 *시너지 가정* 이 후 사후평가에 그대로 유지되면 보수성 부족.
- **외환 환산**: 해외 종속사 영업권은 환율 영향. 환산 차이 vs 손상 분리 필요.
- **사업 부문 통합·분할**: 부문 변경 시 segment 추세 단절. 정합성 확인.

### 5. 후속 모니터링

| 신호 | 임계 | 조치 |
|---|---|---|
| 영업권/총자산 변동 | ±2%p 이상 | 인수·매각·손상 사건 확인 |
| 인수 segment 영업이익 | YoY -10% 4 분기 연속 | 손상검사 가정 재검증 권장 |
| 손상 인식 | 신규 발생 | CGU·금액·가정 변경 추적 |
| 할인율 변경 | 50bp 이상 | 시장 변화 반영 신호 |
| 영업권/시총 비율 | 30%+ 진입 | 시장이 손상 미반영 가격 의심 |
| 외부 평가기관 의견 | 의견 변경 | 손상검사 보고서 review |

## 대표 반환 형태

- `tableRef:goodwill:timeline` — 5 년 영업권 시계열
- `tableRef:goodwill:cgu_breakdown` — CGU 분해
- `tableRef:goodwill:segment_trend` — 인수 segment 추세
- `tableRef:goodwill:sensitivity` — 민감도 분석
- `valueRef:goodwill:assets_pct` — 영업권/자산 %
- `valueRef:goodwill:mkt_cap_pct` — 영업권/시총 %
- `valueRef:goodwill:impairment_score` — 손상 위험 점수
- `sourceRef:goodwill:notes_id` — 주석 id

## 연계 절차

- 합병비율 적정성 → `recipes.fundamental.quality.forensics.mergerRatioFairness`
- 주석 신호 (영업권 키워드) → `recipes.fundamental.quality.forensics.noteSignalExtractor`
- 사건 ↔ 재무 매칭 → `recipes.fundamental.quality.forensics.eventToStatementMatcher`
- 계정 추적 → `recipes.fundamental.quality.forensics.accountTraceLedger`
- 분기 변동성 → `recipes.fundamental.quality.quarterlyAnomalyDetection`

재호출 트리거: "영업권 손상 위험", "PPA 사후평가", "두산밥캣 영업권 추적", "M&A 영업권 누적".

## 기본 검증

- 영업권 5 년 시계열 + 총자산·시총 동행.
- CGU 분해 또는 부재 명시.
- 인수 segment 영업이익 4+ 분기.
- 손상검사 가정 (할인율·성장률) ≥ 2 종 명시 또는 부재 명시.
- 민감도 분석 ≥ 2 시나리오 또는 부재 명시.

## AI 직접 사용 방식

1. `ReadSkill` 에서 영업권·손상·M&A 사후평가 질문이면 본 recipe 선정.
2. `Company.panel("BS")` 5 년 + 영업권·무형자산·총자산·자본총계 행 추출.
3. `Company.panel("부문정보")` 또는 `Company.filings("영업권")` segment·주석.
4. RunPython 으로 비중 + 추세 + 민감도 계산.
5. 답변에 *영업권 시계열 + CGU 분해 + segment 추세 + 민감도* 4 셋 + 반례·한계 필수.
