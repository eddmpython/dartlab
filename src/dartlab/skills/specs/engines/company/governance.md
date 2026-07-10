---
id: engines.company.governance
title: Company Governance
kind: curated
scope: builtin
status: observed
category: engines
purpose: 지배구조 판독 — 기업지배구조보고서 (15 핵심지표) · 이사회 구성 · 감사위원회 · 최대주주 분석. 사외이사 비율 · CEO/Chair 분리 · 누적투표제 등 미국 proxy 가 표준화하지 못한 한국 지배구조 깊이.
whenToUse:
  - 지배구조
  - 기업지배구조보고서
  - 사외이사
  - 이사회 구성
  - 감사위원회
  - 최대주주
  - CEO Chair 분리
  - 누적투표제
  - corporate governance
  - K-ESG
  - 15 핵심지표
inputs:
  - 종목코드 또는 ticker
  - 선택 period (분기/연도)
outputs:
  - dict (board · auditCommittee · majorHolder · disclosure 15 핵심지표)
  - DART rceptNo + section sourceRef
capabilityRefs:
  - Company.analysis
  - Company.story
knowledgeRefs:
  - engines.company
  - engines.company.koreanDisclosure
  - engines.company.disclosureEvent
sourceRefs:
  - dartlab://skills/engines.company.governance
requiredEvidence:
  - target
  - period
  - rceptNo
  - section
  - sourceRef
expectedOutputs:
  - 15 핵심지표 yes/no
  - 미준수 사유 narrative
  - 사외이사 비율 추세
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
  - 한국 기업지배구조보고서 (KOSPI ≥ 1 조 원 AUM 강제) 의 15 핵심지표 양식을 미국 proxy 의 CD&A 와 혼동
  - 사외이사 비율을 NEO-5 만으로 산출 (한국은 전체 등기/미등기 임원 disclosure)
  - rceptNo 인용 없이 governance 본문을 인용
forbidden:
  - DART rceptNo 또는 section ref 없이 지배구조 분석 결론을 내지 않는다
  - 15 핵심지표의 yes/no 만으로 결론짓지 않고 미준수 narrative 까지 확인한다
examples:
  - 삼성전자 사외이사 비율 5 년 추세 - `c.analysis("governance", "지배구조")` 기간 반복
  - POSCO 15 핵심지표 yes/no + 미준수 사유 - `c.analysis("governance", "지배구조")` governanceFlags
  - 카카오 CEO Chair 분리 여부 - `c.analysis("governance", "지배구조")` boardComposition
  - 셀트리온 최대주주 변경 이력 - `c.analysis("governance", "지배구조")` ownershipTrend
  - LG화학 감사위원회 독립성 - `c.analysis("governance", "지배구조")` boardComposition
  - NAVER 누적투표제 도입 - `c.analysis("governance", "지배구조")` governanceFlags
procedure:
  - 종목코드 → Company 객체 생성
  - c.analysis("governance", "지배구조") 호출 (선택 period)
  - 15 핵심지표 dict 확인 + 미준수 narrative 추적
  - 사외이사/감사위/최대주주 sub-key 별 추가 분석
  - rceptNo + section sourceRef 답변 본문 인용
---

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")

# 지배구조 분석 (이사회 구성 · 감사위원회 독립성 · 최대주주 · 15 핵심지표)
c.analysis("governance", "지배구조")

# 지배구조 서사 보고서
c.story(type="governance")
```

## 호출 동작

- target = 종목코드 (KOSPI/KOSDAQ) 또는 ticker (EDGAR). 한국 강제: KOSPI 시가총액 ≥ 1 조 원 기업은 기업지배구조보고서 의무.
- period 미명시 = 최신 보고서. 명시 = 해당 회계연도 보고서.
- 반환 dict 의 key 4 종 (board · auditCommittee · majorHolder · disclosure).
- 15 핵심지표 disclosure key 안에 yes/no boolean + 미준수 narrative string.
- DART OpenAPI 의 corp_outline + corp_report 조합으로 추출. rceptNo + section 보존.

## 대표 반환 형태

```
{
  "board": {
    "totalDirectors": int,
    "outsideDirectors": int,
    "outsideRatio": float,
    "ceoChairSeparated": bool,
    "members": [{"name": str, "role": str, "isOutside": bool, ...}]
  },
  "auditCommittee": {
    "totalMembers": int,
    "outsideMembers": int,
    "independenceScore": float
  },
  "majorHolder": {
    "topHolder": str,
    "topHolderRatio": float,
    "treasuryRatio": float,
    "foreignRatio": float
  },
  "disclosure": {
    "indicator1_boardIndependence": {"compliant": bool, "narrative": str, "rceptNo": str},
    ...
    "indicator15_cumulativeVoting": {"compliant": bool, "narrative": str, "rceptNo": str}
  }
}
```

## 기본 검증

- 답변의 사외이사 비율 · CEO/Chair 분리 · 누적투표제 등 수치 claim 은 모두 rceptNo + section paragraph 에 묶인다.
- 15 핵심지표 yes/no 만 답변 본문에 박지 말고 미준수 narrative 도 같이 인용 (한국 corporate governance code 의 explain-or-comply 원칙).
- KOSPI < 1 조 원 기업은 governance 보고서 미의무 → 본 skill 의 fallback = Company.disclosure(category="기업지배구조") · 결과 None 처리.
- 지배구조 분석 축 변경 시 본 skill 의 examples · 반환 형태 동기화.
- 외부 본문 (DART 원본 narrative) 은 wrapExternalInResult 의 untrusted marker 강제.
