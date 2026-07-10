---
id: engines.company.audit
title: Company Audit (감사보고서)
kind: curated
scope: builtin
status: observed
category: engines
purpose: 감사 리스크 판독 — DART 감사보고서 (auditor opinion · key audit matters · 강조사항 · 계속기업 가정 의문) 파싱. 외부감사인 의견 + KAM (핵심감사사항) 추출로 부도 위험 사전 감지.
whenToUse:
  - 감사보고서
  - audit report
  - auditor opinion
  - key audit matters
  - KAM
  - 계속기업 가정
  - going concern
  - 강조사항
  - 부적정 의견
  - 의견거절
  - 한정 의견
  - audit firm
  - 외부감사인
inputs:
  - 종목코드 또는 ticker
  - 선택 period (회계연도)
outputs:
  - dict (auditor · opinion · keyAuditMatters · emphasisOfMatter · goingConcernFlag)
  - DART rceptNo + section sourceRef
capabilityRefs:
  - Company.panel
  - Company.story
  - scan
knowledgeRefs:
  - engines.company
  - engines.company.koreanDisclosure
  - engines.company.disclosureEvent
sourceRefs:
  - dartlab://skills/engines.company.audit
requiredEvidence:
  - target
  - period
  - rceptNo
  - section
  - sourceRef
expectedOutputs:
  - 감사인 의견 (적정/한정/부적정/의견거절)
  - 핵심감사사항 (KAM) 본문
  - 계속기업 가정 의문 boolean
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
  - K-IFRS 감사보고서 양식 (한국공인회계사회 표준) 을 US PCAOB ICFR 의견과 1:1 매핑 시도
  - KAM 본문을 표준 카테고리로 자동 분류 — KAM 은 자유 narrative 라 양식 강제 X
  - 계속기업 가정 의문 flag 만 보고 부도 예측 결론 — 실제 부도까지 평균 3~5 년 시차
forbidden:
  - DART rceptNo 또는 KAM section paragraph 의 sourceRef 없이 감사 의견을 인용하지 않는다
  - 감사보고서 narrative 는 wrapExternalInResult 의 untrusted marker 강제
examples:
  - 005930 최신 감사보고서 의견 - `c.panel("감사")` 본문에서 감사의견
  - 셀트리온 계속기업 가정 의문 flag 5 년 추세 - `c.panel("감사")` 기간별 계속기업 문단
  - 카카오 핵심감사사항 (KAM) 카테고리 분포 - `c.panel("감사")` KAM 본문
  - POSCO 외부감사인 변경 이력 - `dartlab.scan("audit")` 감사인변경 컬럼
  - LG에너지솔루션 KAM 본문 5 년 - `c.panel("감사")` 기간별 KAM 본문
  - 한진 한정 의견 종목 스크리닝 - `dartlab.scan("audit")` 감사의견 필터
procedure:
  - 종목코드 → Company 객체 생성
  - c.panel("감사") 로 감사보고서 본문 열기
  - 감사의견 확인 (적정/한정/부적정/의견거절 4 분류)
  - KAM 본문 추적 (자유 narrative)
  - 계속기업 가정 의문 확인. 있으면 추가 분석 (Company.credit · Altman Z-score)
---

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")

# 감사보고서 본문 (섹션명 검색)
c.panel("감사")

# 한 회사의 감사 서사 보고서
c.story(type="audit")

# 감사 리스크를 전상장사 횡단으로 (감사의견 · 감사인변경 · 특기사항 · 감사독립성비율)
dartlab.scan("audit")
```

## 호출 동작

- target = DART 종목코드 (KOSPI/KOSDAQ) 또는 ticker (EDGAR — 미국 audit report 도 별도 양식). 한국 감사보고서 = 한국공인회계사회 표준 양식.
- period 미명시 = 최신 회계연도. 명시 = 해당 회계연도.
- 반환 dict 의 key 5 종 (auditor · opinion · keyAuditMatters · emphasisOfMatter · goingConcernFlag).
- KAM (핵심감사사항) 은 K-IFRS 1701 도입 (2018-) 후 의무. 자유 narrative · 표준 카테고리 X.
- 외부감사인 변경 이력 = `dartlab.scan("audit")` 의 감사인변경 컬럼.

## 대표 반환 형태

```
{
  "period": "2025",
  "auditor": str,              # "삼일회계법인" 등
  "opinion": str,              # "적정" | "한정" | "부적정" | "의견거절"
  "keyAuditMatters": [
    {
      "title": str,
      "description": str,      # 자유 narrative
      "auditResponse": str,
      "rceptNo": str,
      "sourceRef": dict
    }
  ],
  "emphasisOfMatter": str | None,
  "goingConcernFlag": bool,
  "auditorChange": dict | None  # 직전 회계연도 변경 시
}
```

## 기본 검증

- 감사 의견 (적정/한정/부적정/의견거절) 의 4 분류는 한국공인회계사회 표준 SSOT. 영문 unqualified/qualified/adverse/disclaimer 와 1:1 매핑 가능하나 자유 번역 금지.
- KAM 본문은 한국어 원문 보존 (`wrapExternalInResult` untrusted marker 자동).
- goingConcernFlag = True 만으로 부도 예측 결론 X — Company.credit 의 Altman Z-score · KMV 모델 추가 호출 필수.
- 외부감사인 변경 (직전 5 년 내 2 회+) = audit shopping 신호 — Company.disclosure(category="감사인변경") 본문 추가 확인.
- 감사 파서(providers/dart) 변경 시 본 skill 의 반환 형태 동기화.
