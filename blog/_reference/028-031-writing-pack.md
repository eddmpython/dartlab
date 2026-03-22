# 028-031 Writing Pack

현재 공개 상태는 아래와 같다.

- 완료: `028 XBRL 재무제표 원문과 주석 다운로드 파이프라인`
- 다음 집필 1순위: `029 Risk Factors와 MD&A를 같이 읽는 법`
- 다음 제품 연결 1순위: `031 corp_code부터 filing 원문까지 DART 수집 파이프라인 설계`

메모:

- 기존 `028 20-F와 10-K는 무엇이 다른가` 초안은 기존 EDGAR 글과 주제 중복이 커서 `blog/_backup/028-20f-vs-10k/`로 이동했다.
- 이 문서는 현재 공개 큐인 `029~031`만 기준으로 본다.

## 현재 구조에서의 의미

- `029 Risk Factors와 MD&A를 같이 읽는 법`
  - `report-reading-foundations` 시리즈의 다음 실전 연결편이다.
  - 기존 `004`, `017`, `020`이 따로 다룬 리스크, MD&A, 숫자 검증을 한 흐름으로 묶어야 한다.
- `030 재고자산과 평가손실 읽는 법`
  - `working-capital-and-earnings-quality` 시리즈를 두 번째 글로 확장하는 핵심 포스트다.
  - `015`와 문제의식은 이어지지만, 재고 구성/회전/평가손실로 초점을 더 좁혀야 한다.
- `031 corp_code부터 filing 원문까지 DART 수집 파이프라인 설계`
  - `028`이 XBRL·주석 레이어를 다뤘다면, `031`은 검색/접수번호/원문 추적까지 포함한 수집기 구조를 다루는 글이다.
  - `002`, `016`, `028`을 이어주는 상위 파이프라인 글이 된다.

## 추천 우선순위

- 다음 집필 1순위: `029 Risk Factors와 MD&A를 같이 읽는 법`
  - 검색 의도가 선명하고, 시리즈 균형상 가장 먼저 메워야 할 빈칸이다.
- 다음 제품 연결 1순위: `031 corp_code부터 filing 원문까지 DART 수집 파이프라인 설계`
  - `028` 바로 다음 글로 묶기 좋고, OpenDART 실사용자 관점의 가치가 크다.

## 029. Risk Factors와 MD&A를 같이 읽는 법

- 카테고리: `02-report-reading`
- 시리즈: `report-reading-foundations`
- 독자 약속:
  - 리스크 문구와 경영진 설명을 따로 읽지 않고, 같은 이슈를 서로 교차검증하는 법을 익히게 만든다.
  - 다음 분기 또는 다음 연차 보고서에서 무엇을 다시 봐야 하는지까지 제시한다.
- 기존 글과의 차별화:
  - `017`은 사업보고서 전체 입문.
  - `020`은 경영진 말과 숫자의 충돌.
  - 이번 글은 `Risk Factors -> MD&A -> 다음 숫자` 연결이 핵심이다.
- 겹치면 안 되는 문단:
  - 사업보고서 전체 읽기 순서 일반론
  - CEO 말보다 숫자가 중요하다는 단선적 결론
  - 감사보고서/KAM 중심 서술
- 권장 섹션:
  1. 왜 Risk Factors와 MD&A를 같이 읽어야 하나
  2. 두 섹션의 역할 차이
  3. 반복 문구와 진짜 신호 구분
  4. MD&A가 리스크를 약화시키는지 확인하는 법
  5. 다음 보고서에서 무엇을 재확인할까
  6. 자주 틀리는 해석 4가지
  7. 체크리스트
  8. FAQ
- 내부 링크:
  - `004 reading business reports`
  - `008 business section changes judgment`
  - `014 audit report and kam`
  - `017 five things in business report`
  - `020 when numbers matter more than ceo words`
- 공식 출처:
  - SEC How to Read a 10-K
    - https://www.sec.gov/answers/reada10k.htm
  - SEC Form 10-K
    - https://www.sec.gov/files/form10-k.pdf
  - DART 기업공시 길라잡이 - 이사의 경영진단 및 분석의견
    - https://dart.fss.or.kr/info/main.do?menu=120
  - DART 보고서정보
    - https://dart.fss.or.kr/introduction/content2.do
- SVG 기본안:
  - `029-risk-to-mdna-bridge.svg`
  - `029-generic-vs-specific-risk.svg`
  - `029-management-explanation-map.svg`
  - `029-issue-escalation-ladder.svg`
  - `029-reading-checklist.svg`

## 030. 재고자산과 평가손실 읽는 법

- 카테고리: `03-financial-interpretation`
- 시리즈: `working-capital-and-earnings-quality`
- 독자 약속:
  - 재고 증가를 성장 신호로만 보지 않고, 회전율과 평가손실까지 연결해 읽게 만든다.
  - 제조업과 유통업에서 어떤 조합이 위험한지 빠르게 판단하게 만든다.
- 기존 글과의 차별화:
  - `018`은 매출 증가 대비 재고/채권 압력을 넓게 다뤘다.
  - 이번 글은 재고 자체를 중심으로 `구성`, `회전`, `저가평가`, `매출총이익률`, `수요 둔화`를 묶는다.
- 겹치면 안 되는 문단:
  - 매출채권 중심 이익의 질 설명
  - CAPEX/감가상각 중심 고정비 논리
  - 성장주 일반론
- 권장 섹션:
  1. 재고는 왜 매출보다 먼저 경고를 주는가
  2. 재고 증가가 좋은 경우와 나쁜 경우
  3. 재고 구성표에서 무엇을 봐야 하나
  4. 회전율과 매출총이익률을 같이 읽는 법
  5. 평가손실은 언제 진짜 위험 신호가 되나
  6. 자주 틀리는 해석 4가지
  7. 체크리스트
  8. FAQ
- 내부 링크:
  - `010 capacity utilization capex`
  - `012 depreciation after capex`
  - `015 receivables and allowance`
  - `018 why rising sales can still be risky`
- 공식 출처:
  - IFRS Foundation IAS 2 Inventories
    - https://www.ifrs.org/issued-standards/list-of-standards/ias-2-inventories/
  - IFRS Foundation IAS 2 supporting material
    - https://www.ifrs.org/supporting-implementation/supporting-materials-by-ifrs-standards/ias-2/
  - DART 보고서정보
    - https://dart.fss.or.kr/introduction/content2.do
- SVG 기본안:
  - `030-inventory-pressure-map.svg`
  - `030-turnover-vs-margin-matrix.svg`
  - `030-write-down-warning-signals.svg`
  - `030-good-vs-bad-inventory-build.svg`
  - `030-ten-minute-checklist.svg`

## 031. corp_code부터 filing 원문까지 DART 수집 파이프라인 설계

- 카테고리: `04-data-automation`
- 시리즈: `data-automation`
- 독자 약속:
  - `corp_code -> 검색 -> rcept_no -> 원문 파일`까지 수집기의 바깥 프레임을 이해하게 만든다.
  - `028`에서 다룬 XBRL/주석 레이어를 상위 파이프라인 안에 정확히 배치하게 만든다.
- 기존 글과의 차별화:
  - `016`은 이벤트 모니터링.
  - `028`은 재무·주석 파일 파이프라인.
  - 이번 글은 검색, 식별자, 접수번호, 원문 추적, 정정공시까지 포함한 전체 수집기 설계다.
- 겹치면 안 되는 문단:
  - XBRL vs JSON 비교를 장황하게 반복
  - account mapping 내부 알고리즘 설명
  - OpenDART 전체 장단점 리뷰
- 권장 섹션:
  1. 왜 corp_code가 파이프라인의 시작점인가
  2. 검색 결과에서 기준 문서를 고르는 법
  3. rcept_no를 중심으로 원문 파일을 추적하는 구조
  4. 정정공시를 어떻게 다시 묶을까
  5. 기업 단위 watch와 batch 설계
  6. 실패하는 수집기의 공통 패턴
  7. 체크리스트
  8. FAQ
- 내부 링크:
  - `002 opendart review`
  - `016 opendart material events`
  - `028 opendart xbrl notes pipeline`
- 공식 출처:
  - OpenDART 고유번호 개발가이드
    - https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019018
  - OpenDART 공시검색 / 공시서류원본파일 개발가이드
    - https://opendart.fss.or.kr/guide/main.do
    - https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019003
  - DART 보고서정보
    - https://dart.fss.or.kr/introduction/content2.do
- SVG 기본안:
  - `031-pipeline-overview.svg`
  - `031-corp-code-map.svg`
  - `031-search-to-filing-bridge.svg`
  - `031-amendment-tracking-flow.svg`
  - `031-failure-recovery-checklist.svg`

## 공통 집필 원칙

- 첫 문단에서 독자의 실제 오해를 바로 찌른다.
- 중간부는 항상 `좋은 경우 vs 위험한 경우` 또는 `충분한 경우 vs 부족한 경우` 구조를 쓴다.
- 마지막 전 섹션은 체크리스트로 고정한다.
- FAQ는 검색형 문장으로 4~5개만 둔다.
- 공식 출처는 최소 3개, 가능하면 4개 이상 붙인다.
