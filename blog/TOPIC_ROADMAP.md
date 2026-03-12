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
- 사업보고서 읽기
- 사업의 내용 해석
- 생산능력 / 건설중인자산 / 감가상각
- 파이썬 재무제표 분석

반면 아래 축은 아직 비어 있거나 약하다.

- 8-K, 20-F, 13F 같은 개별 form 실전 해석
- 감사보고서, KAM, 우발부채, 소송 공시
- 운전자본과 이익의 질
- OpenDART 주요사항보고서 / XBRL / 원문 다운로드 실전 활용

## 우선순위 큐

### 1순위: 바로 써야 하는 주제

#### 1. 8-K item map 읽는 법

- 카테고리: `01-disclosure-systems`
- 시리즈: `edgar-reading`
- 이유: 기존 EDGAR 글의 다음 심화편으로 가장 자연스럽다.
- 검색 의도:
  - `8-k 뜻`
  - `8-k item`
  - `8-k 읽는 법`
  - `8-k 언제 나오나`
- 글 핵심:
  - 8-K를 단순 이벤트 공시가 아니라 `item 번호 기반 이벤트 지도`로 읽는다.
  - 어떤 item이 재무적으로 중요한지 우선순위를 준다.
  - 10-Q / 10-K 후속 반영까지 시간축으로 연결한다.
- SVG 기본안:
  - item map
  - event-to-financial impact
  - filing timing ladder
  - high-signal vs low-signal card
  - follow-up checklist
- 공식 출처:
  - SEC Forms Index
  - SEC Form 8-K guidance / C&DI

#### 2. 사업보고서에서 감사보고서와 KAM 읽는 법

- 카테고리: `02-report-reading`
- 시리즈: 신규 `audit-and-governance-reading`
- 이유: 현재 블로그에 없는 강한 축이고, 실제 투자 판단에 도움이 크다.
- 검색 의도:
  - `감사의견 보는 법`
  - `핵심감사사항 읽는 법`
  - `KAM 투자`
- 글 핵심:
  - 적정의견 여부보다 `핵심감사사항`, 계속기업, 내부통제, 추정 민감도를 읽는다.
  - 숫자 변화보다 먼저 회계 리스크를 확인하는 프레임을 제시한다.
- SVG 기본안:
  - audit opinion branch
  - KAM anatomy
  - accounting estimate heatmap
  - red flag scorecard
  - 10-minute checklist
- 공식 출처:
  - 금융감독원 / DART 감사보고서 안내
  - KAM 관련 감독기관 자료

#### 3. 매출채권과 대손충당금 읽는 법

- 카테고리: `03-financial-interpretation`
- 시리즈: 신규 `working-capital-and-earnings-quality`
- 이유: 설비투자 시리즈 다음 묶음으로 가장 자연스럽다.
- 검색 의도:
  - `매출채권 증가`
  - `대손충당금 해석`
  - `이익의 질 보는 법`
- 글 핵심:
  - 매출 성장이 현금으로 회수되는지 본다.
  - 회수 지연, 채널 밀어내기, 낙관적 충당금 가정을 구분한다.
- SVG 기본안:
  - revenue-to-cash bridge
  - receivable aging map
  - allowance pressure curve
  - good vs bad receivable growth
  - checklist
- 공식 출처:
  - 사업보고서 / 주석 / 감사보고서
  - 회계기준 주석 공시 구조

#### 4. OpenDART로 주요사항보고서 읽는 법

- 카테고리: `04-data-automation`
- 시리즈: `data-automation`
- 이유: 공식 API 가이드상 활용 범위가 넓고, 현재 블로그에 직접 다룬 글이 없다.
- 검색 의도:
  - `주요사항보고서 api`
  - `오픈다트 주요사항보고서`
  - `자산양수도 공시 api`
- 글 핵심:
  - 어떤 주요사항보고서를 API로 잡을 수 있는지 범주화한다.
  - 어떤 사건은 API만으로 충분하고 어떤 사건은 원문까지 내려가야 하는지 구분한다.
- SVG 기본안:
  - event taxonomy
  - API-to-filing flow
  - severity ladder
  - watch dashboard
  - failure mode card
- 공식 출처:
  - OpenDART 개발가이드
  - OpenDART 주요사항보고서 주요정보 가이드

### 2순위: 시리즈 확장 가치가 큰 주제

#### 5. 20-F와 10-K는 무엇이 다른가

- 카테고리: `01-disclosure-systems`
- 시리즈: `edgar-reading`
- 검색 의도:
  - `20-f 10-k 차이`
  - `fpi sec 공시`
- 핵심:
  - FPI, 6-K, 업데이트 리듬, IFRS/US GAAP 차이

#### 6. Risk Factors와 MD&A를 같이 읽는 법

- 카테고리: `02-report-reading`
- 시리즈: `report-reading-foundations`
- 검색 의도:
  - `md&a 읽는 법`
  - `risk factors 해석`
- 핵심:
  - 리스크 항목과 경영진 설명을 분리하지 않고 같이 읽는다.

#### 7. 재고자산과 평가손실 읽는 법

- 카테고리: `03-financial-interpretation`
- 시리즈: `working-capital-and-earnings-quality`
- 검색 의도:
  - `재고자산 증가`
  - `재고평가손실`
- 핵심:
  - 수요 둔화, 원가 압력, 재고 축적, 평가손실 가능성

#### 8. XBRL 재무제표 원문과 주석 다운로드 파이프라인

- 카테고리: `04-data-automation`
- 시리즈: `data-automation`
- 검색 의도:
  - `opendart xbrl`
  - `주석 일괄다운로드`
- 핵심:
  - JSON API, 원문, XBRL, 주석 다운로드를 한 파이프라인으로 연결한다.

### 3순위: 블로그 깊이를 더 올리는 주제

#### 9. EDGAR Next 이후 무엇이 달라졌나

- 카테고리: `01-disclosure-systems`
- 시리즈: `edgar-reading`
- 검색 의도:
  - `edgar next`
  - `edgar filing changes`
- 핵심:
  - filer access, 계정 관리, 제출 프로세스 변화

#### 10. 우발부채와 소송 공시 읽는 법

- 카테고리: `02-report-reading`
- 시리즈: `audit-and-governance-reading`
- 검색 의도:
  - `우발부채 해석`
  - `소송 공시 읽는 법`
- 핵심:
  - 충당부채 전 단계 신호, 문구 강도, 손익 반영 시차

#### 11. 영업현금흐름이 순이익을 부정할 때

- 카테고리: `03-financial-interpretation`
- 시리즈: `working-capital-and-earnings-quality`
- 검색 의도:
  - `영업현금흐름 순이익 차이`
  - `cash flow earnings quality`
- 핵심:
  - 운전자본, 일회성, 회수 지연, 선수금/매입채무 의존

#### 12. corp_code부터 filing 원문까지 DART 수집 파이프라인 설계

- 카테고리: `04-data-automation`
- 시리즈: `data-automation`
- 검색 의도:
  - `dart corp_code`
  - `opendart pipeline`
- 핵심:
  - corp_code, 검색, 원문 파일, XBRL, 주석 다운로드의 연결 구조

## 카테고리별 운영 방향

### 01-disclosure-systems

다음 순서로 간다.

1. `8-K item map 읽는 법`
2. `20-F와 10-K는 무엇이 다른가`
3. `EDGAR Next 이후 무엇이 달라졌나`
4. `Form 13F를 어떻게 읽어야 하나`

운영 원칙:

- 제도 설명에서 끝내지 않는다.
- 항상 `실전 읽기 순서`와 `후속 form 연결`까지 다룬다.

### 02-report-reading

다음 순서로 간다.

1. `감사보고서와 KAM 읽는 법`
2. `Risk Factors와 MD&A를 같이 읽는 법`
3. `우발부채와 소송 공시 읽는 법`
4. `주주총회소집공고와 보수공시 읽는 법`

운영 원칙:

- 텍스트 해석 글은 비교표와 체크리스트를 반드시 넣는다.
- 숫자보다 먼저 문구와 리스크 강도를 읽는 흐름을 유지한다.

### 03-financial-interpretation

다음 순서로 간다.

1. `매출채권과 대손충당금 읽는 법`
2. `재고자산과 평가손실 읽는 법`
3. `영업현금흐름이 순이익을 부정할 때`
4. `손상차손 읽는 법`
5. `운전자본이 이익의 질을 바꾸는 방식`

운영 원칙:

- `설비투자 해석 시리즈` 다음 묶음은 `운전자본·이익의 질 시리즈`로 연결한다.
- 손익계산서만 보지 말고 주석, 현금흐름표, 회전 지표를 같이 읽는다.

### 04-data-automation

다음 순서로 간다.

1. `OpenDART 주요사항보고서 API 활용법`
2. `XBRL 재무제표 원문과 주석 다운로드 파이프라인`
3. `corp_code부터 원문까지 DART 수집 구조`
4. `EDGAR 원문 + JSON + XBRL을 같이 쓰는 수집 설계`

운영 원칙:

- 단순 endpoint 소개가 아니라 `무엇이 되고 무엇이 안 되는지`를 분명히 쓴다.
- 예제는 실무 파이프라인 단위로 구성한다.

## 시리즈 정의 확장안

기존 시리즈:

- `dart-foundations`
- `edgar-reading`
- `report-reading-foundations`
- `fixed-cost-and-capex`
- `financial-context`
- `data-automation`

추가 예정 시리즈:

- `working-capital-and-earnings-quality`
- `audit-and-governance-reading`

## 다음 실제 작성 순서

1. `8-K item map 읽는 법`
2. `감사보고서와 KAM 읽는 법`
3. `매출채권과 대손충당금 읽는 법`
4. `OpenDART 주요사항보고서 읽는 법`
5. `20-F와 10-K는 무엇이 다른가`
6. `재고자산과 평가손실 읽는 법`

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

- 완료:
  - `013-8k-item-map`
  - `014-audit-report-and-kam`
  - `015-receivables-and-allowance`
  - `016-opendart-material-events`
- 다음 후보:
  - `20-F와 10-K는 무엇이 다른가`
  - `Risk Factors와 MD&A를 같이 읽는 법`
  - `재고자산과 평가손실 읽는 법`
  - `XBRL 재무제표 원문과 주석 다운로드 파이프라인`
