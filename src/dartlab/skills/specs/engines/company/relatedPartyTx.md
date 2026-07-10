---
id: engines.company.relatedPartyTx
title: Company Related Party Transactions
kind: curated
scope: builtin
status: observed
category: engines
purpose: 관계자 거래 판독 — 관계자 거래 (RPT). 공정거래법 §26 chaebol disclosure threshold 100억 원 (2024-01-01 시행). 2025 FTC 데이터 top-10 chaebol = 193 조 원 = 전체 disclosed RPT 의 70%. chaebol inter-affiliate 거래 graph 의 raw input.
whenToUse:
  - 관계자 거래
  - RPT
  - 계열사 거래
  - 특수관계자
  - 공정거래법 26
  - 100억 RPT
  - 지급보증
  - 매출 거래
  - 매입 거래
  - 자산 양수도
  - chaebol RPT
  - inter-affiliate
  - 대규모기업집단현황공시
inputs:
  - 종목코드
outputs:
  - RelatedPartyTxResult (guarantees / revenue / etc DataFrame list)
  - DART 사업보고서 rceptNo + section sourceRef
capabilityRefs:
  - Company.panel
knowledgeRefs:
  - engines.company
  - engines.company.koreanDisclosure
  - engines.company.governance
sourceRefs:
  - dartlab://skills/engines.company.relatedPartyTx
requiredEvidence:
  - target
  - rceptNo
  - section
  - sourceRef
expectedOutputs:
  - 거래 분류 별 list (guarantees · revenue · 자산 양수도 · 임원 거래)
  - 거래 상대방 · 금액 · 기간 · 조건
  - chaebol inter-affiliate 거래 흐름 (affiliateGroup 와 join 시)
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
  - threshold 10억 원으로 답변 (구 룰 — 2024-01-01 부터 100억 원)
  - 단일 회사 RPT 만 인용 + chaebol 전체 흐름 무시 (RPT 의 핵심 = inter-affiliate)
  - RPT 본문 narrative (목적/조건) 생략 후 금액만 인용
  - K-IFRS 1024 footnote 만 보고 공정거래법 §26 대규모기업집단현황공시 누락
forbidden:
  - rceptNo 또는 section paragraph 의 sourceRef 없이 RPT 금액 인용 금지
  - threshold 10억 원 답변 금지 (2024-01-01 부터 100억 원 — 10배 차이)
  - chaebol 전체 흐름 무시 후 단일 회사 RPT 결론
examples:
  - 삼성전자 관계자 거래 - `c.panel("특수관계자")`
  - 삼성그룹 RPT 흐름 - `c.panel("특수관계자")` 를 계열사마다
  - 100억 이상 지급보증 - `c.panel("특수관계자")` 지급보증 섹션
  - 매출 거래 inter-affiliate - `c.panel("특수관계자")` 매출 거래 섹션
  - SK이노베이션 자산 양수도 RPT - `c.panel("특수관계자")` 자산 양수도 섹션
  - 현대차그룹 chaebol RPT graph - `c.panel("특수관계자")` 를 계열사마다 모아 graph 구축
procedure:
  - 종목코드 - Company 객체 생성
  - c.panel("특수관계자") 호출
  - 거래 분류 별 DataFrame 확인 (guarantees · revenue · etc)
  - chaebol graph 구축 시 affiliateGroup 와 join (모든 계열사 단위)
  - rceptNo + section sourceRef 답변 본문 인용
---

## 공개 호출 방식

```python
import dartlab

c = dartlab.Company("005930")

# 특수관계자 거래 본문 (지급보증 · 매출 거래 · 자산 양수도 등)
c.panel("특수관계자")
```

## 호출 동작

- target = DART 종목코드 (KOSPI/KOSDAQ). 한국 공시 한정.
- DART 사업보고서 의 관계자 거래 섹션 자동 파싱.
- K-IFRS 1024 footnote + 공정거래법 §26 대규모기업집단현황공시 둘 다 source.
- threshold 100억 원 (2024-01-01 시행). 이전 (10억 원) 룰 = 폐기. 답변 시 정확한 시행 일자 인용 필수.
- 반환 = 항목 x 기간 격자의 특수관계자 구획 행(지급보증 · 매출 거래 · 자산 양수도).
- chaebol inter-affiliate 거래 graph 구축 시 dartlab.providers.dart.docs.finance.affiliate 와 join (단일 회사 X · 그룹 전체).

## 대표 반환 형태

```
RelatedPartyTxResult:
  guarantees : pl.DataFrame  # 지급보증
    거래상대방 : str          # 계열사명
    거래종류 : str            # "지급보증"
    금액 : Int64              # 백만 원
    기간 : str
    조건 : str                # 금리 · 담보 · 만기 narrative
  revenue : pl.DataFrame     # 매출 거래
    거래상대방 : str
    거래종류 : str            # "매출" / "매입"
    금액 : Int64
  (기타 거래 분류 별 DataFrame)
```

## 기본 검증

- 모든 RPT 금액 claim 은 DART 사업보고서 rceptNo + section paragraph 의 sourceRef 에 묶는다.
- threshold 100억 원 (2024-01-01) 정확히 인용 — 구 룰 (10억 원) 답변 금지.
- chaebol inter-affiliate 거래 분석 시 단일 회사 X · affiliateGroup 와 join 한 그룹 전체 흐름 확인.
- RPT 본문 narrative (목적 · 조건 · 금리 · 담보) 생략 후 금액만 답변 금지 — 메커니즘 추적 evidence 동반.
- Company.relatedPartyTx() docstring 변경 시 본 skill 의 capabilityRefs · examples · 반환 형태 동기화.
- 2025 FTC 데이터: top-10 chaebol = 193 조 원 = 전체 disclosed RPT 의 70% 비중 — 이 statistic 인용 시 출처 (FTC 2025 보고서) 명시.
