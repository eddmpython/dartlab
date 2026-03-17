# Topic Roadmap

이 문서는 블로그의 다음 글 후보를 `카테고리별 우선순위`, `검색 의도`, `시리즈 연결`, `공식 출처` 기준으로 정리한 운영 문서다.

원칙:

- 기존 글과 겹치지 않아야 한다.
- 검색 의도가 분명해야 한다.
- 시리즈로 이어질 수 있어야 한다.
- 공식 자료로 뒷받침되는 주제를 우선한다.
- 각 글은 완성형 본문 + SVG 기본 5개 기준으로 준비한다.

## 현재 블로그 공백

현재 블로그는 다음 축은 강하다.

- DART / EDGAR 전체 구조
- 사업보고서 읽기 (사업의 내용, 감사보고서, KAM, CEO 말 vs 숫자)
- 대주주 / 특수관계인 / 임원 보수 / 주주환원 / 주총 / 지배구조
- 생산능력 / 건설중인자산 / 감가상각
- 매출채권 / 대손충당금
- 파이썬 재무제표 분석 / OpenDART 주요사항보고서 / XBRL·주석 다운로드

반면 아래 축은 아직 비어 있거나 약하다.

- 13F 같은 개별 form 실전 해석
- 유상증자, CB/BW, 자기주식, 합병/분할 같은 기업 이벤트 공시 실전 해석
- 우발부채, 소송 공시
- 재고, 영업현금흐름, 손상차손 같은 후속 이익의 질
- Risk Factors / MD&A 교차 읽기
- corp_code부터 filing 원문까지 이어지는 DART 수집 설계

## 우선순위 큐

## 다음 생산 배치

- `029 Risk Factors와 MD&A를 같이 읽는 법`
- `030 재고자산과 평가손실 읽는 법`
- `031 corp_code부터 filing 원문까지 DART 수집 파이프라인 설계`

준비 문서:

- `blog/_reference/WRITING_QUEUE.md`
- `blog/_reference/028-031-writing-pack.md`
- `blog/_reference/017-020-source-checklist.md`

## 새 시리즈 확정

### 기업 이벤트·자금조달 읽기 시리즈

- 시리즈 id: `corporate-actions-and-financing`
- 포지션:
  - DART 강점을 가장 잘 살릴 수 있는 다음 확장축
  - 단순 제도 설명이 아니라 `희석`, `자금조달`, `지배력 이동`, `후속 공시 추적`을 같이 읽는 실전형 시리즈
- 이유:
  - 기존 시리즈와 겹치지 않으면서 검색 의도가 분명하다
  - `주요사항보고서`, `지분공시`, `자기주식`, `합병/분할`을 하나의 해석 흐름으로 묶기 좋다
  - 대주주·지배구조 시리즈와도 자연스럽게 내부 링크를 만들 수 있다

예상 첫 묶음:

- `032 유상증자 공시 읽는 법`
- `033 전환사채와 BW 공시 읽는 법`
- `034 자기주식 취득·처분·소각 공시 읽는 법`
- `035 합병·분할 공시 읽는 법`
- `036 최대주주 변경과 경영권 이동 신호 읽는 법`

### 1순위: 바로 써야 하는 주제

#### 1. Risk Factors와 MD&A를 같이 읽는 법

- 카테고리: `02-report-reading`
- 시리즈: `report-reading-foundations`
- 검색 의도:
  - `md&a 읽는 법`
  - `risk factors 해석`
- 핵심:
  - 리스크 항목과 경영진 설명을 분리하지 않고 같이 읽는다.

#### 2. 재고자산과 평가손실 읽는 법

- 카테고리: `03-financial-interpretation`
- 시리즈: `working-capital-and-earnings-quality`
- 검색 의도:
  - `재고자산 증가`
  - `재고평가손실`
- 핵심:
  - 수요 둔화, 원가 압력, 재고 축적, 평가손실 가능성

#### 3. corp_code부터 filing 원문까지 DART 수집 파이프라인 설계

- 카테고리: `04-data-automation`
- 시리즈: `data-automation`
- 검색 의도:
  - `dart corp_code`
  - `opendart pipeline`
- 핵심:
  - corp_code, 검색, 원문 파일, 접수번호 추적의 연결 구조

### 2순위: 블로그 깊이를 더 올리는 주제

#### 4. EDGAR Next 이후 무엇이 달라졌나

- 카테고리: `01-disclosure-systems`
- 시리즈: `edgar-reading`
- 검색 의도:
  - `edgar next`
  - `edgar filing changes`
- 핵심:
  - filer access, 계정 관리, 제출 프로세스 변화

#### 5. 우발부채와 소송 공시 읽는 법

- 카테고리: `02-report-reading`
- 시리즈: `audit-and-governance-reading`
- 검색 의도:
  - `우발부채 해석`
  - `소송 공시 읽는 법`
- 핵심:
  - 충당부채 전 단계 신호, 문구 강도, 손익 반영 시차

#### 6. 영업현금흐름이 순이익을 부정할 때

- 카테고리: `03-financial-interpretation`
- 시리즈: `working-capital-and-earnings-quality`
- 검색 의도:
  - `영업현금흐름 순이익 차이`
  - `cash flow earnings quality`
- 핵심:
  - 운전자본, 일회성, 회수 지연, 선수금/매입채무 의존

#### 7. EDGAR 원문 + JSON + XBRL을 같이 쓰는 수집 설계

- 카테고리: `04-data-automation`
- 시리즈: `data-automation`
- 검색 의도:
  - `edgar json xbrl`
  - `edgar filing pipeline`
- 핵심:
  - submissions JSON, filing 원문, XBRL 원문을 같이 쓰는 구조

### 다음 시리즈 배치: 기업 이벤트·자금조달 읽기 시리즈

#### 8. 유상증자 공시 읽는 법

- 카테고리: `01-disclosure-systems`
- 시리즈: `corporate-actions-and-financing`
- 검색 의도:
  - `유상증자 공시 읽는 법`
  - `유상증자 투자 위험`
- 핵심:
  - 자금 사용 목적, 할인율, 기존 주주 희석, 후속 일정 확인

#### 9. 전환사채와 BW 공시 읽는 법

- 카테고리: `01-disclosure-systems`
- 시리즈: `corporate-actions-and-financing`
- 검색 의도:
  - `전환사채 공시 읽는 법`
  - `bw 공시 해석`
- 핵심:
  - 전환가액 조정, 리픽싱, 잠재 희석, 조달 조건의 질

#### 10. 자기주식 취득·처분·소각 공시 읽는 법

- 카테고리: `01-disclosure-systems`
- 시리즈: `corporate-actions-and-financing`
- 검색 의도:
  - `자기주식 취득 소각 차이`
  - `자사주 공시 읽는 법`
- 핵심:
  - 취득과 소각의 차이, 처분 가능성, 주주환원 신호의 진정성

#### 11. 합병·분할 공시 읽는 법

- 카테고리: `01-disclosure-systems`
- 시리즈: `corporate-actions-and-financing`
- 검색 의도:
  - `합병 공시 읽는 법`
  - `회사 분할 공시 해석`
- 핵심:
  - 거래 목적, 교환비율, 사업 재편 논리, 소수주주 관점 체크포인트

#### 12. 최대주주 변경과 경영권 이동 신호 읽는 법

- 카테고리: `02-report-reading`
- 시리즈: `corporate-actions-and-financing`
- 검색 의도:
  - `최대주주 변경 공시 읽는 법`
  - `경영권 변경 신호`
- 핵심:
  - 거래 상대방, 자금 출처, 담보·콜옵션 구조, 후속 공시 추적

## 카테고리별 운영 방향

### 01-disclosure-systems

다음 순서로 간다.

1. `EDGAR Next 이후 무엇이 달라졌나`
2. `Form 13F를 어떻게 읽어야 하나`

운영 원칙:

- 제도 설명에서 끝내지 않는다.
- 항상 `실전 읽기 순서`와 `후속 form 연결`까지 다룬다.

### 02-report-reading

다음 순서로 간다.

1. `Risk Factors와 MD&A를 같이 읽는 법`
2. `우발부채와 소송 공시 읽는 법`

운영 원칙:

- 텍스트 해석 글은 비교표와 체크리스트를 반드시 넣는다.
- 숫자보다 먼저 문구와 리스크 강도를 읽는 흐름을 유지한다.

### 03-financial-interpretation

다음 순서로 간다.

1. `재고자산과 평가손실 읽는 법`
2. `영업현금흐름이 순이익을 부정할 때`
3. `손상차손 읽는 법`
4. `운전자본이 이익의 질을 바꾸는 방식`

운영 원칙:

- `설비투자 해석 시리즈` 다음 묶음은 `운전자본·이익의 질 시리즈`로 연결한다.
- 손익계산서만 보지 말고 주석, 현금흐름표, 회전 지표를 같이 읽는다.

### 04-data-automation

다음 순서로 간다.

1. `corp_code부터 원문까지 DART 수집 구조`
2. `EDGAR 원문 + JSON + XBRL을 같이 쓰는 수집 설계`

운영 원칙:

- 단순 endpoint 소개가 아니라 `무엇이 되고 무엇이 안 되는지`를 분명히 쓴다.
- 예제는 실무 파이프라인 단위로 구성한다.

## 시리즈 현황

현재 시리즈 (10개, posts.ts 정의 완료):

- `dart-foundations` (3개)
- `edgar-reading` (4개)
- `report-reading-foundations` (5개)
- `fixed-cost-and-capex` (3개)
- `financial-context` (2개)
- `data-automation` (3개)
- `working-capital-and-earnings-quality` (1개)
- `audit-and-governance-reading` (1개)
- `ownership-and-governance-reading` (6개)
- `corporate-actions-and-financing` (0개, 신규 기획 확정)

## 다음 실제 작성 순서

1. `029 Risk Factors와 MD&A를 같이 읽는 법`
2. `030 재고자산과 평가손실 읽는 법`
3. `031 corp_code부터 filing 원문까지 DART 수집 파이프라인 설계`

이 순서는 다음 기준으로 정했다.

- 검색 의도가 선명한가
- 기존 글과 자연스럽게 연결되는가
- 깊게 써도 내용 중복이 적은가
- 공식 자료로 근거를 붙일 수 있는가

## 작성 준비 체크리스트

새 글을 실제로 쓰기 전에 아래를 정리한다.

1. 카테고리와 시리즈를 확정한다.
2. 전역 포스트 번호를 예약한다.
3. 검색형 제목 1개와 설명 1개를 확정한다.
4. 공식 출처 3개 이상을 먼저 확보한다.
5. SVG 5개 기본 구성을 먼저 설계한다.
6. FAQ 4~5문항을 먼저 잡는다.
7. 체크리스트 섹션을 마지막 전 섹션으로 고정한다.

## 공식 출처 메모

EDGAR / SEC:

- SEC Forms Index  
  https://www.sec.gov/submit-filings/forms-index
- SEC How to Read a 10-K  
  https://www.sec.gov/answers/reada10k.htm
- SEC Form 13F FAQ  
  https://www.sec.gov/divisions/investment/13ffaq.htm
- SEC EDGAR Next  
  https://www.sec.gov/submit-filings/improving-edgar/edgar-next-improving-filer-access-account-management
- SEC EDGAR News & Announcements  
  https://www.sec.gov/submit-filings/edgar-news-announcements

DART / OpenDART:

- DART 보고서정보  
  https://dart.fss.or.kr/introduction/content2.do
- OpenDART 개발가이드  
  https://opendart.fss.or.kr/guide/main.do
- OpenDART 공시정보 활용마당  
  https://opendart.fss.or.kr/disclosureinfo/biz/main.do
- OpenDART 주요사항보고서 주요정보 가이드  
  https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS005

## 메모

- SEC 쪽은 `개별 form 실전 해석`이 가장 좋은 확장축이다.
- DART 쪽은 `감사보고서`, `주요사항보고서`, `원문/XBRL 활용`이 아직 비어 있다.
- 재무 해석 쪽은 다음 시리즈를 `운전자본·이익의 질`로 잡는 것이 가장 자연스럽다.

## 제작 상태

- 완료 (28개):
  - `001` ~ `021`: 초기 배치 + 1차 확장
  - `022-major-shareholder-and-related-parties`
  - `023-executive-pay-disclosure`
  - `024-shareholder-return-what-matters`
  - `025-governance-red-flags`
  - `026-how-to-read-agm-notice`
  - `027-good-vs-risky-ownership`
  - `028-opendart-xbrl-notes-pipeline`
- 다음 후보:
  - `029 Risk Factors와 MD&A를 같이 읽는 법`
  - `030 재고자산과 평가손실 읽는 법`
  - `031 corp_code부터 filing 원문까지 DART 수집 파이프라인 설계`
