---
id: engines.company.notesDetail
title: Company K-IFRS Notes Detail
kind: curated
scope: builtin
status: observed
category: engines
purpose: 주석 세부항목 판독 — K-IFRS 주석 세부항목 (리스 약정 · 우발채무 · 퇴직급여 가정 · 파생 등 23 NOTES_KEYWORDS). audit-grade citation 의 핵심 evidence layer. footnote-grade Q&A 의 raw 데이터 (Bloomberg/FactSet 미보유 영역).
whenToUse:
  - 주석
  - K-IFRS 주석
  - footnote
  - 리스 약정
  - 우발채무
  - 퇴직급여
  - 퇴직급여 가정
  - 파생
  - 파생금융상품
  - contingent liability
  - 금융자산
  - 금융부채
  - 차입금
  - 신종자본증권
  - 영업권
  - 무형자산
inputs:
  - 종목코드
  - keyword (NOTES_KEYWORDS 23 종 중 하나)
  - period (y 연간 또는 q 분기 또는 h 반기, default y)
outputs:
  - NotesDetailResult (corpName + tables dict)
  - DART 정기보고서 docs rceptNo + section sourceRef
capabilityRefs:
  - Company.panel
knowledgeRefs:
  - engines.company
  - engines.company.koreanDisclosure
  - engines.company.audit
sourceRefs:
  - dartlab://skills/engines.company.notesDetail
requiredEvidence:
  - target
  - keyword
  - period
  - rceptNo
  - section
  - sourceRef
expectedOutputs:
  - keyword 별 최근 5 년 historical panel
  - NotesPeriod (year · kind · items · unit)
  - 표 본문 line-item 추출
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
  - NOTES_KEYWORDS 23 종 밖 keyword 호출 (직접 호출 X · None 반환)
  - 연간 답변에 분기 비교 (period 인자 무시)
  - 5 년 panel 전체 dump (답변 본문 상위 3~5 년만 인용)
  - 주석 양식 분기별 미세 변경 (XBRL tag rename) 회귀 가드 누락
forbidden:
  - rceptNo 또는 section paragraph 의 sourceRef 없이 주석 line-item 인용 금지
  - 주석 본문 narrative 는 wrapExternalInResult untrusted marker 강제
examples:
  - 삼성전자 리스 약정 - c.panel("주석") 에서 리스 섹션
  - LG에너지솔루션 우발채무 5 년 - c.panel("주석") 에서 우발채무 섹션
  - 셀트리온 퇴직급여 가정 - c.panel("주석") 에서 퇴직급여 섹션
  - 현대차 파생금융상품 - c.panel("주석") 에서 파생 섹션
  - LG화학 영업권 손상 - c.panel("주석") 에서 영업권 섹션
procedure:
  - 종목코드 - Company 객체 생성
  - keyword 결정 (NOTES_KEYWORDS 23 종 중 하나)
  - c.panel("주석") 또는 c.panel(섹션명) 호출
  - tables dict 의 keyword 별 NotesPeriod list 확인
  - 최근 5 년 historical panel 추적 + line-item 본문 추출
  - rceptNo + section sourceRef 답변 본문 인용
---

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")

# 주석 본문 전체 (항목 x 기간 격자의 주석 구획)
c.panel("주석")

# 섹션명으로 좁히기
c.panel("재고")
```

## 호출 동작

- target = DART 종목코드 (KOSPI/KOSDAQ). 한국 K-IFRS 한정.
- keyword = NOTES_KEYWORDS 23 종 중 하나 (리스 · 우발 · 퇴직급여 · 파생 · 금융자산 · 금융부채 · 차입금 · 영업권 · 무형자산 · 신종자본증권 등).
- period = "y" 연간 (default) · "q" 분기 · "h" 반기.
- 최근 5 년 자동 추출 (year 내림차순).
- 주석 표 line-item 본문 parser 결과. 단위 (백만 원 · 천 원) auto-normalize.
- 미박힘 keyword 또는 데이터 부족 시 None 반환.
- 표 본문 narrative = wrapExternalInResult 의 [EXTERNAL CONTENT START] marker 자동.

## 대표 반환 형태

```
NotesDetailResult:
  corpName : str
  tables : dict[str, list[NotesPeriod]]
    (key = keyword 정규형, value = 분기별/연간별 NotesPeriod list)
  NotesPeriod:
    year : str               # "2025"
    kind : str               # "annual" / "quarterly" / "semi-annual"
    items : pl.DataFrame     # line-item 표 (계정 · 값 · 비교)
    unit : float             # 1.0 (백만 원 기준) 또는 0.001 (천 원)
    rceptNo : str            # DART filing 접수번호
    sourceRef : dict         # {url, page, paragraph}
```

## 기본 검증

- 모든 주석 line-item 수치 claim 은 DART 정기보고서 rceptNo + section paragraph 의 sourceRef 에 묶는다.
- 5 년 panel 전체 dump 금지 — 답변 본문 상위 3~5 년만 인용 + 추세 narrative 동반.
- NOTES_KEYWORDS 23 종 밖 keyword 호출 시 None 반환 — 답변 본문에서 "데이터 없음" 명시 (추정 금지).
- 주석 양식 분기별 미세 변경 (XBRL tag rename · 항목 통합) 인지 — narrative drift 비교 시 회귀 가드 강제.
- 주석 파서(providers/dart) 변경 시 본 skill 의 examples · 반환 형태 동기화.
- 주석 본문 narrative 인용 시 wrapExternalInResult 의 untrusted marker 자동 박힘 확인 (외부 본문 untrusted tier).
