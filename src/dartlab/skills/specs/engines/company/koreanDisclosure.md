---
id: engines.company.koreanDisclosure
title: Korean Disclosure Routing
kind: curated
scope: builtin
status: observed
category: engines
purpose: 한국 DART 공시 종류별 routing SSOT — 자연어 질문 ("지배구조", "임원 보수", "관계자 거래", "사업의 내용", "주석", "공정공시", "공매도") 을 Company 의 적합 method apiRef 로 매핑한다.
whenToUse:
  - 지배구조
  - 기업지배구조보고서
  - 사외이사
  - 이사회
  - 임원 보수
  - 5억 이상 보수
  - 관계자 거래
  - 계열사 거래
  - 특수관계자
  - RPT
  - 사업의 내용
  - segment
  - 부문별 매출
  - 메모리 ASP
  - 공정공시
  - 주요사항보고
  - 주석
  - K-IFRS 주석
  - 리스 약정
  - contingent
  - 별도 vs 연결
  - parent-only
  - 공매도
  - 외국인 net-buy
  - 한도소진율
  - DART 공시
inputs:
  - 자연어 한국 공시 질문
  - 종목코드 또는 ticker
  - 선택 axis (period · kind · basis)
outputs:
  - 적합 EngineCall apiRef
  - 호출 인자 가이드
  - 관련 sub-skill 링크
capabilityRefs:
  - Company.filings
  - Company.analysis
  - Company.panel
  - Company.panel
  - Company.filings
  - Company.panel
knowledgeRefs:
  - engines.company
  - engines.company.disclosureEvent
  - engines.company.governance
  - engines.panel
  - engines.company.audit
sourceRefs:
  - dartlab://skills/engines.company.koreanDisclosure
requiredEvidence:
  - target
  - rceptNo
  - section
  - sourceRef
expectedOutputs:
  - 한국 공시 질문 분류
  - apiRef 매핑
  - 호출 인자
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: limited
failureModes:
  - DART 공시 종류를 미국 EDGAR 8-K/10-K 양식으로 잘못 매핑
  - 별도재무제표 (parent-only) vs 연결재무제표 구분 누락
  - rceptNo 인용 없이 한국 공시 본문 인용
forbidden:
  - apiRef 매핑 없이 한국 공시 질문을 일반 EngineCall 로 처리하지 않는다
  - DART rceptNo 또는 section ref 없이 한국 공시 숫자/본문을 인용하지 않는다
examples:
  - 삼성전자 사외이사 비율 - `c.analysis("governance", "지배구조")`
  - NAVER 임원 5억 이상 보수 - Company.filings(category=임원변동) + 후속 panel
  - 삼성그룹 관계자거래 100억 이상 - Company.filings(category=대규모기업집단현황공시)
  - 005930 메모리 ASP 분기 추세 - Company.panel("businessOverview") + topic query 사업의 내용
  - 셀트리온 별도 vs 연결 NI 차이 - Company.panel(IS basis=separate) + Company.panel(IS basis=consolidated)
procedure:
  - 질문에서 한국 공시 종류 키워드 식별
  - 본 표의 apiRef 매핑 적용
  - 종목코드 → Company 객체 생성
  - 매핑된 apiRef 로 EngineCall 호출
  - 결과 ref 확인 (rceptNo · section · paragraph 박혀있는지)
---

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")

# 지배구조
gov = c.analysis("governance", "지배구조")

# 공시 이벤트 (임원변동 · 주요사항)
events = c.filings()

# 사업보고서 segment narrative
narrative = c.panel("businessOverview")

# 감사보고서
audit = c.panel("감사")

# 별도 vs 연결
sep = c.panel("IS", basis="separate")
con = c.panel("IS", basis="consolidated")
```

## 호출 동작

- 자연어 한국 공시 질문 → 본 skill 의 examples 표를 보고 적합 apiRef 선택.
- 종목코드 (DART) 또는 ticker (EDGAR) 를 target 으로 고정 후 Company 객체 생성.
- 매핑된 apiRef 가 capability registry 에 박혀있는지 확인 (ReadCapability 도구).
- EngineCall(apiRef=...) 호출 — 자연어 인자 X · 매핑 apiRef 직접 호출.
- DART 공시 종류는 미국 EDGAR 양식 (8-K · 10-K) 과 1:1 매핑 X — 한국 공시 양식 (사업보고서 · 분기보고서 · 주요사항보고 · 공정공시 · 대규모기업집단현황공시) 의 한국 특화 routing 이다.

## 대표 반환 형태

| 한국 공시 종류 | apiRef | 반환 dtype | 핵심 필드 |
|---|---|---|---|
| 기업지배구조보고서 (15 핵심지표) | `c.analysis("governance", "지배구조")` | dict | board · audit · disclosure 분기 |
| 임원 변동 · 5억 이상 보수 | `Company.filings(category="임원변동")` | DataFrame | rceptNo · filedAt · title · formType |
| 사업보고서 II 항 segment narrative | `Company.panel("businessOverview")` | DataFrame | period · topic · content · sourceRef |
| 감사보고서 | `c.panel("감사")` | dict | auditor · opinion · keyAuditMatters |
| 별도재무제표 (parent-only) | `Company.panel("IS", basis="separate")` | DataFrame | account · value · period |
| 연결재무제표 | `Company.panel("IS", basis="consolidated")` | DataFrame | account · value · period · subsidiary |

각 결과는 DART rceptNo + section + paragraph 의 source chain 보존 (wrapExternalInResult).

## 기본 검증

- 한국 공시 답변은 모든 숫자 claim 을 DART filing rceptNo 와 section paragraph 에 직접 묶는다.
- 별도 vs 연결 혼동 차단 — basis 인자 명시 없이 한국 기업 NI/EBIT 비교 금지.
- 본 skill 의 examples 표에 새 한국 공시 종류가 추가될 때마다 capabilityRefs · whenToUse 동기화.
- DART 공시 종류와 EDGAR 양식 (8-K · 10-K) 의 자동 매핑 금지 — 한국 양식은 독립 SSOT.
- 답변 본문에 rceptNo 인용 없이 한국 공시 본문을 인용하지 않는다 (forbidden 강제).
