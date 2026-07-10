---
id: recipes.fundamental.quality.forensics.auditorIndependenceHistory
title: 회계감사인 독립성·이력 진단
category: recipes
kind: recipe
scope: builtin
status: curated
graphTier: L1.5
cluster: incubator.forensics
purpose: 회계감사인 (회계법인) 의 계속 감사기간, 강제교체 (Mandatory Auditor Rotation) 준수, 비감사 서비스 (자문) 동시 수행 비중, 감사인 변경 timestamp 와 회사 사건 (합병·분식·구조조정) 의 동행 패턴을 공시·사업보고서 본문으로 진단하는 L1.5 절차. 트리거 — '감사인 변경', '감사인 독립성', '강제교체', '한정의견', '비감사 보수 비중'.
whenToUse:
  - 감사인 변경 공시
  - 계속 감사기간 6 년 초과
  - 강제교체 준수
  - 비감사 보수 비중 큰 회계법인
  - 한정·부적정 감사의견 이력
  - 감사인 변경 ↔ 사건 (합병·분식 적발) 동행
  - 회계법인 분쟁 (저축은행 사태·분식 회계 처벌)
linkedSkills:
  - recipes.fundamental.quality.forensics.index
  - recipes.fundamental.quality.forensics.noteSignalExtractor
  - recipes.fundamental.quality.forensics.disclosureTimingAnomaly
  - recipes.fundamental.quality.forensics.bigBathDetection
  - recipes.fundamental.quality.forensics.eventToStatementMatcher
  - engines.company
inputs:
  - Company.panel 감사인 / 감사보수 / 사업보고서 감사관련 섹션
  - Company.filings (감사인 변경·감사의견·정정)
  - Company.panel notes 감사보고서 (의견·강조사항·핵심감사사항)
  - scan disclosureRisk / governance (감사인 횡단)
outputs:
  - 감사인 변경 시계열 ledger
  - 계속 감사기간 + 강제교체 준수 체크
  - 비감사 보수 비중 시계열
  - 감사의견 이력 (한정·부적정·강조사항·KAM)
  - 동행 사건 timing 매칭
capabilityRefs:
  - Company.panel
  - Company.filings
  - scan
toolRefs:
  - EngineCall
  - RunPython
sourceRefs:
  - dartlab://skills/recipes.fundamental.quality.forensics.auditorIndependenceHistory
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - 감사인 변경 시계열 + 강제교체 준수 ledger
  - 비감사 보수 비중 시계열
  - 감사의견 이력 매트릭스
  - 동행 사건 timing
  - 엔진 승격 후보 메모

forbidden:
  - 감사인 변경 = 부정 신호 단정 시 *강제교체 의무* (외부감사법 9 조) 준수 정상 변경 반례 검토 누락 금지.
  - 비감사 보수 비중 큼 = 독립성 약함 단정 시 *법규상 허용 범위* (외부감사법 9 조의 4) 명시 누락 금지.
  - 한정의견 = 분식 단정 시 *감사 범위 제한* (회사 외 요인) vs *회계 부실* 분류 누락 금지.
  - 감사인 = 회계법인 단정 시 *법인 내 담당 파트너* 변경도 별도 신호 메모.
  - 한 시점만 보고 단정 — 감사인 시계열 ≥ 5 년 + 동행 사건 시계열 동시 평가.
failureModes:
  - 감사인 변경 = 부정 신호 단정 시 *강제교체* (6 년 의무) 정상 변경 무시
  - 계속 감사기간 길음 = 정상 단정 시 *친밀도 위험* 무시
  - 비감사 보수 = 독립성 약함 단정 시 *세무·자문 정상 영업* 혼동
  - 한정의견 = 분식 단정 시 *감사 범위 제한* (해외 자회사 등) 혼동
  - 핵심감사사항 (KAM) 다수 = 부정 단정 시 *복잡한 사업 구조* 정상 사유 무시
examples:
  - 쌍용자동차 안진회계법인 한정의견 사례 (4 권)
  - 대우조선해양 삼일/삼정 분식 사례 (4 권)
  - 중국고섬 한영회계 분식 적발 (4 권)
  - 저축은행 사태 회계법인 책임 (3 권)
  - 네오세미테크 우회상장 회계법인 책임 (3 권)
  - 외환위기 시기 회계법인 책임 부각
  - 강제교체 도입 후 6 년 초과 사례 (제도 도입 전후)
  - 신외감법 도입 후 주기적 지정제 (2018 이후)
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
  description: "감사인 정보 (회계법인명·계속 감사기간·비감사 보수) 또는 감사의견 본문 부재 시 독립성 판정 불가 — *DART 사업보고서 감사 섹션 + 감사인 변경 공시 fetch 후 재호출* 한계 명시. 또한 *강제교체 적용 시점* (신외감법 2018 ~) 명시 없이 변경 = 부정 단정 보류."
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

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.panel("IS"|"BS"|"CF")`, `Company.filings`, `scan.quality`, `scan.audit`, `scan.disclosureRisk` 는 엔진 호출로 근거를 먼저 확보한다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildEvidenceForensicsMemo` 로 묶는 **RunPython fallback** 절차다 — 감사인 독립성 — 주석 패턴.

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
    table=memo["tables"]["noteSignalExtractor"],
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

*감사인 변경 시계열 + 강제교체 준수 + 비감사 보수 비중 + 감사의견 이력 + 동행 사건 timing* 한 문장.

좋은 결론 예시:
- "대우조선해양 케이스 — 감사인 시계열 (삼일 X 년 → 삼정 Y 년). 강제교체 의무 (신외감법 2018 ~ 주기적 지정제) 적용 시점부터 N 년 준수. 비감사 보수 / 총 보수 = Z% (법규 한도 W% 비교). 감사의견 — Y 년 한정의견 (감사 범위 제한 — 대우조선해양 사례). 핵심감사사항 (KAM) ≥ K 개 (복잡한 공사진행기준 회계). 분식 적발 시점 D vs 감사인 교체 시점 E (간격 M 분기). *감사인 독립성 [중간] + 한정의견 이력 [있음] [conf:60]*. counter — 분식 책임은 회사·감사 양쪽 분담 (4 권 회계와법 사례 참조)."

금지:
- 감사인 변경 단일 신호만으로 부정 단정.
- 강제교체 적용 시점 (신외감법 2018) 미명시.

### 2. 핵심 근거 수집

`requiredEvidence: skillRef + target + tableRef + valueRef + dateRef + sourceRef + executionRef` 필수.

- **target** (stockCode).
- **sourceRef**: 사업보고서 감사 섹션 (감사인명·감사보수·비감사 보수) + 감사인 변경 공시 + 감사보고서 (의견·강조사항·KAM).
- **tableRef** (4+ 표):
  1. **감사인 변경 시계열** — 회계법인명 / 시작 사업연도 / 종료 사업연도 / 계속 감사기간 / 변경 사유 (강제교체 / 자율 / 지정)
  2. **감사 보수 시계열** — 감사보수 / 비감사 보수 / 비감사 비중 / 법규 한도 비교
  3. **감사의견 이력** — 사업연도별 의견 (적정 / 한정 / 부적정 / 의견거절) + 강조사항 + 핵심감사사항 (KAM) 개수·주제
  4. **동행 사건 timing** — 감사인 변경 timestamp ↔ 합병·분식 적발·구조조정·CEO 변경 시점
- **valueRef**: 계속 감사기간 (연), 비감사 보수 비중 %, 한정의견 발생 횟수, KAM 개수.
- **dateRef**: 감사인 변경일·감사의견 발표일·동행 사건일.
- **executionRef**: RunPython 으로 변경 시계열 + 동행 timing 회귀.

### 3. 메커니즘 분석

감사인 독립성 진단 = *변경 시계열 + 강제교체 준수 + 비감사 보수 비중 + 감사의견 이력 + 동행 사건 timing 5 차원 동시 검증*:

```mermaid
graph LR
  CHANGE["감사인 변경"] --> DURATION["계속 감사기간"]
  CHANGE --> REASON["변경 사유<br/>강제 / 자율 / 지정"]

  DURATION --> ROT_CHECK["강제교체 준수<br/>신외감법 2018~ 주기 지정"]

  FEE["감사 보수"] --> RATIO["비감사 비중<br/>비감사 / 총 보수"]
  RATIO --> LIMIT["법규 한도 비교"]

  OPINION["감사의견 이력"] --> QUAL["한정·부적정·의견거절 횟수"]
  OPINION --> EMP["강조사항"]
  OPINION --> KAM["핵심감사사항 KAM"]

  EVENT["동행 사건<br/>합병·분식 적발·CEO 변경"] --> CHANGE_TIME["감사인 변경 timestamp"]
  CHANGE_TIME --> TIMING_GAP["사건 vs 변경 간격"]

  ROT_CHECK --> SCORE["독립성 점수"]
  LIMIT --> SCORE
  QUAL --> SCORE
  KAM --> SCORE
  TIMING_GAP --> SCORE
```

**5 패턴 정량 신호**:

| 패턴 | 신호 | 임계 | 가중치 |
|---|---|---|---|
| **계속 감사기간** | 동일 회계법인 연속 감사 | ≥ 9 년 (강제교체 전 + 친밀도 위험) | medium |
| **강제교체 준수** | 신외감법 2018~ 주기적 지정제 위반 | 발생 | high |
| **비감사 보수** | 비감사 / 총 보수 | ≥ 50% | high |
| **한정의견** | 사업연도별 한정·부적정·의견거절 | 1 회 이상 / 10Y | high |
| **KAM 다수** | 핵심감사사항 개수 | ≥ 5 개 / 사업연도 | medium |
| **동행 사건** | 합병·분식 적발 D-3 ~ D+12M 내 감사인 변경 | 발생 | high |
| **담당 파트너 변경 빈도** | 담당 파트너 변경 (법인 동일) | 매년 변경 | low |

### 4. 반례·한계

- **Falsifier**: 감사인 정보 또는 감사의견 본문 부재 시 독립성 판정 불가 — *DART 사업보고서 감사 섹션 + 감사인 변경 공시 fetch 후 재호출*.
- **강제교체 정상 변경**: 신외감법 (2018 ~) 주기적 지정제 도입 후 *강제 변경* 이 정상 패턴이 되어 단순 변경 빈도만으로 부정 단정 금지. *변경 사유* (강제 / 자율 / 지정) 분류 필수.
- **감사 범위 제한 한정의견**: 한정의견 사유가 *회사 회계 부실* 이 아닌 *해외 자회사 자료 미입수* 등 *감사 범위 제한* 인 경우 회사 책임 한정. 의견 본문 사유 인용 필수.
- **비감사 보수 정상 영업**: 세무·내부통제 자문 등 정상 영업 가능. 다만 *법규 한도* (외부감사법 9 조의 4) 와 *친밀도 위험* 동행 평가.
- **KAM 도입 효과**: 핵심감사사항 (KAM) 은 2017 부터 의무 도입 → 단순 개수만으로 부정 단정 금지. 회사 사업 구조 복잡도 동행 평가.
- **회계법인 분쟁 시점**: 회계법인이 *분식 책임* 으로 처벌받은 경우라도 회사 측 책임이 별도. 책임 비중은 별도 법적 판단.
- **담당 파트너 변경**: 회계법인은 동일하지만 *담당 파트너* 가 매년 바뀌면 *법인 차원* 친밀도 신호는 약해진다. 다만 사업보고서가 *파트너명* 까지 다 공시하지 않음.

### 5. 후속 모니터링

| 신호 | 임계 | 조치 |
|---|---|---|
| 계속 감사기간 | ≥ 9 년 (강제교체 전) | 친밀도 위험 ledger |
| 강제교체 준수 위반 | 발생 | 즉시 격상 |
| 비감사 보수 비중 | ≥ 50% | 독립성 [약함] |
| 한정·부적정 의견 | 1 회 이상 / 10Y | 사유 본문 인용 |
| KAM 개수 | ≥ 5 개 | 사업 복잡도 동행 평가 |
| 동행 사건 (합병·분식) | D-3 ~ D+12M | timing 매칭 ledger |
| 감사보수 vs 매출 비율 | 동종 업종 평균 대비 | 외부 비교 메모 |

## 대표 반환 형태

- `tableRef:auditor:change_timeseries` — 감사인 변경 시계열
- `tableRef:auditor:fee_timeseries` — 감사 보수 시계열
- `tableRef:auditor:opinion_history` — 감사의견 이력
- `tableRef:auditor:event_timing` — 동행 사건 timing
- `valueRef:auditor:tenure_years` — 계속 감사기간 (연)
- `valueRef:auditor:nonaudit_ratio` — 비감사 보수 비중
- `valueRef:auditor:qualified_count` — 한정·부적정 의견 횟수
- `valueRef:auditor:kam_count` — KAM 개수
- `sourceRef:auditor:report_id` — 사업보고서 id
- `sourceRef:auditor:change_disclosure_id` — 감사인 변경 공시 id
- `executionRef:auditor:calc_id` — RunPython 실행 id

## 연계 절차

- 주석 신호 (계속기업·강조사항 동행) → `recipes.fundamental.quality.forensics.noteSignalExtractor`
- 공시 timing (감사의견 정정 동행) → `recipes.fundamental.quality.forensics.disclosureTimingAnomaly`
- 빅 배스 (감사인 변경 후 손상 인식) → `recipes.fundamental.quality.forensics.bigBathDetection`
- 사건 ↔ 재무 매칭 → `recipes.fundamental.quality.forensics.eventToStatementMatcher`

재호출 트리거: "감사인 변경", "계속 감사기간", "강제교체", "한정의견 이력", "비감사 보수 비중", "회계감사인 독립성".

## 기본 검증

- 감사인 시계열 ≥ 5 년.
- 강제교체 적용 시점 (신외감법 2018) 명시.
- 비감사 보수 비중 + 법규 한도 비교.
- 감사의견 이력 (적정 / 한정 / 부적정 / 의견거절) 분류.
- 동행 사건 timing 매칭.
- falsifier — 사업보고서 감사 섹션 부재 시 판정 보류.

## AI 직접 사용 방식

1. `ReadSkill` 에서 감사인·감사의견 질문이면 본 recipe 선정.
2. target stockCode 확인.
3. `Company.panel("감사인")` 또는 사업보고서 감사 섹션 fetch.
4. `Company.filings("감사인")` 변경 timestamp + 사유.
5. `Company.filings("감사의견")` 의견·강조사항·KAM.
6. `scan("disclosureRisk")` 횡단 비교.
7. RunPython 으로 시계열 + 동행 timing 계산.
8. 답변에 *감사인 변경 + 보수 비중 + 의견 이력 + 동행 사건 timing* 4 셋 + 반례·한계 필수.
