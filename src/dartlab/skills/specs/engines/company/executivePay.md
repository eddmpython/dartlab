---
id: engines.company.executivePay
title: Company Executive Pay
kind: curated
scope: builtin
status: observed
category: engines
purpose: 임원 보수 판독 — 임원 보수 ≥ 5억 원 individual 공개 (자본시장법 §159, 2013-11-29 시행). US proxy NEO-5 와 달리 등기/미등기/퇴직 전원 공개. 급여 / 상여 / 주식매수선택권 행사이익 / 기타근로소득 / 퇴직소득 분해.
whenToUse:
  - 임원 보수
  - 5억 이상 보수
  - 임원 연봉
  - 등기임원 보수
  - 미등기임원 보수
  - 퇴직 임원 보수
  - 스톡옵션 행사
  - 상여
  - 급여 narrative
  - executive compensation
  - 임원 산정기준
inputs:
  - 종목코드
outputs:
  - ExecutivePayResult (payByType DataFrame + topPay DataFrame)
  - DART 사업보고서 rceptNo + section sourceRef
capabilityRefs:
  - Company.panel
knowledgeRefs:
  - engines.company
  - engines.company.koreanDisclosure
  - engines.company.governance
sourceRefs:
  - dartlab://skills/engines.company.executivePay
requiredEvidence:
  - target
  - rceptNo
  - section
  - sourceRef
expectedOutputs:
  - 임원 보수 종류 별 분해 (급여/상여/스톡옵션/퇴직 etc)
  - 상위 보수 임원 list (성명/직위/총액/산정기준)
  - 산정기준 narrative
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
  - 한국 individual disclosure 를 US proxy NEO-5 와 1:1 매핑 시도 (등기 만 보고 미등기 누락)
  - 산정기준 narrative 생략 후 보수 총액만 인용 (메커니즘 불명)
  - 직책 정규화 없이 회사 간 비교 (대표이사 vs 부회장 vs 사장 의미 차이 — 한국 직책 체계 고유)
forbidden:
  - rceptNo 또는 section paragraph 의 sourceRef 없이 임원 보수 수치 인용 금지
  - 상위 보수 list 전체 dump (답변 본문 상위 5~10 명만)
examples:
  - 삼성전자 임원 보수 - `c.panel("임원")`
  - 5억 이상 임원 명단 - `c.panel("임원")` 상위 보수 행
  - 퇴직 임원 보수 - `c.panel("임원")` 퇴직 보수 행
  - NAVER 미등기 임원 보수 분포 - `c.panel("임원")` 미등기 임원 행
  - 카카오 스톡옵션 행사이익 - `c.panel("임원")` 주식매수선택권 행사이익 행
  - 현대차 대표이사 산정기준 narrative - `c.panel("임원")` 산정기준 행
procedure:
  - 종목코드 - Company 객체 생성
  - c.panel("임원") 호출
  - payByType (등기/미등기/퇴직) 분해 확인
  - topPay 상위 보수 + 산정기준 narrative 추적
  - rceptNo + section sourceRef 답변 본문 인용
---

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")

# 임원 보수 본문 (등기/미등기/퇴직 분해 · 상위 보수 · 산정기준)
c.panel("임원")
```

## 호출 동작

- target = DART 종목코드 (KOSPI/KOSDAQ). 한국 공시 한정.
- DART 사업보고서 의 임원 보수 섹션 자동 파싱.
- 반환 = ExecutivePayResult dataclass — payByType DataFrame (집계) + topPay DataFrame (개별).
- 데이터 없거나 5억 미만 회사 (대부분 KOSDAQ 소형주) → None 반환.
- 산정기준 narrative (스톡옵션 행사 timing · 상여 산정 룰 등) = 보수 메커니즘 추적 evidence.

## 대표 반환 형태

```
ExecutivePayResult:
  payByType : pl.DataFrame
    구분 : str              # "등기" / "미등기" / "퇴직"
    급여 : Float64           # 백만 원
    상여 : Float64
    주식매수선택권 행사이익 : Float64
    기타근로소득 : Float64
    퇴직소득 : Float64
    기타 : Float64
  topPay : pl.DataFrame
    성명 : str
    직위 : str               # "대표이사" / "사외이사" / 등
    보수총액 : Float64       # 백만 원
    근로소득 : Float64
    퇴직소득 : Float64
    기타 : Float64
    산정기준 : str           # narrative (스톡옵션 행사 timing · 상여 룰 등)
```

## 기본 검증

- 모든 임원 보수 수치 claim 은 DART 사업보고서 rceptNo + section paragraph 의 sourceRef 에 묶는다.
- 상위 보수 list 전체 dump 금지 — 답변 본문 상위 5~10 명만 인용 + 산정기준 narrative 동반.
- 등기 vs 미등기 분리 미확인 시 답변 본문에서 "전체 임원 보수" 라 단정 X (한국 unique: 미등기/퇴직 포함 공개).
- 임원 보수 파서(providers/dart) 변경 시 본 skill 의 examples · 반환 형태 동기화.
- 한국 직책 (대표이사/부회장/사장/전무/상무/이사) 정규화 없이 회사 간 보수 비교 금지.
