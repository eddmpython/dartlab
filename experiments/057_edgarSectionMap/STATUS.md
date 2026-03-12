# 057 EDGAR 섹션 맵

## 목적

EDGAR docs를 DART `056_sectionMap`과 같은 철학으로 수평 비교 가능한 topic 체계로 정리한다.
다만 EDGAR는 DART처럼 제도화된 장 체계가 아니라 `10-K`, `10-Q`, `20-F`의 item 구조를 그대로 살린다.

핵심 목표는 다음 세 가지다.

- `10-K`, `10-Q`, `20-F`의 section title / item title 전수조사
- source-native item 구조를 보존한 canonical topic map 설계
- 향후 `sections` 파이프라인에서 period x topic 텍스트 비교가 가능하도록 준비

## 현재 전제

- 로더는 `loadData(stockCode, category="edgarDocs")` 기준으로 동작
- 로컬에 없으면 GitHub Release, 없으면 SEC API에서 `2009년부터` 직접 수집
- 수집 후보 universe는 `data/edgar/listedUniverse.parquet`
- 1차 모집단은 `is_exchange_listed == True` 종목

## 핵심 차이

### DART 056
- 공통 chapter I~XII 틀이 이미 존재
- 회사별 소분류 차이만 정규화하면 됨

### EDGAR 057
- 공통 chapter 틀보다 filing form별 item 체계가 핵심
- `10-K`, `10-Q`, `20-F`를 같은 topicId로 억지 통합하면 정보 손실 가능성 큼
- 우선은 form-native canonical map이 맞다

## 진행 순서

1. universe 정의
2. 다운로드 커버리지 확인
3. `10-K`, `10-Q`, `20-F`별 title frequency 전수조사
4. item 경계 안정성 평가
5. canonical topic 후보 설계
6. sectionMappings 초안 작성

## 실험 파일

- `001_universeSurvey.py`
  - listed universe, 현재 docs 보유 수, 로컬 커버리지 확인
- `002_downloadFirst2000.py`
  - exchange listed 2,000개를 2009년부터 배치 수집
- `003_titleFrequency.py`
  - form_type별 section_title 전수 빈도표
- `004_itemCoverage.py`
  - filing별 section 수, Full Document 비율, 구조 안정성 측정
- `005_boundaryCandidates.py`
  - form-native canonical topic 초안 생성
- `006_buildCanonicalRowTable.py`
  - period별 canonical row 학습 테이블 생성
- `007_fastHorizontalizeFromTable.py`
  - canonicalRows 기반 빠른 horizontalization 확인
- `008_deploymentReadiness.py`
  - 패키지 sections 파이프라인 무에러 점검

## 현재 판단

- `10-K`, `10-Q`, `20-F` 모두 item 기반 section map으로 갈 수 있다
- 현재 병목은 split 자체가 아니라 long-tail title 흡수와 table fidelity 감시다
- `056_sectionMap` 기준으로 보면 EDGAR는 `pipeline + mapper` 최소형은 넘었고, 이제 package contract 정리 단계다

## 실행 결과 (2026-03-12)

### 001_universeSurvey.py 완료

- listed universe total: `10,416`
- exchange listed: `7,525`
- otc: `2,561`
- 초기 1차 후보 고정본: `data/edgar/docsCandidates2000.parquet`

결론:
- 057의 1차 모집단은 exchange listed 7,525개다.
- 실제 장기 수집과 section map teacher pool은 이 중 2,000개 배치부터 시작한다.

### 002_downloadFirst2000.py 진행 중

- 백그라운드 배치 수집 프로세스 실행 중
- 현재 로컬 docs와 progress는 실행 시점에 따라 계속 증가
- 재시작 가능하도록 `output/downloadFirst2000.progress.jsonl`에 ticker별 상태를 누적 기록
- 10-Q split 로직 반영 후 구형 `Full Document` parquet는 되돌리고 재수집 중

결론:
- 057은 정적 샘플이 아니라 수집이 진행되는 동안 점진적으로 실험을 갱신하는 방식으로 간다.

### 003_titleFrequency.py 완료

- 최신 실행 시점 docs files: `7`
- rows: `2,719`
- forms: `10-K`, `10-Q`, `20-F`

핵심 결과:
- 10-K unique titles: `25`
- 10-K top10 coverage: `47.55%`
- 10-Q unique titles: `11`
- 10-Q full document ratio: `0%`
- 20-F unique titles: `31`

결론:
- 10-K는 item title 기반 canonical topic 설계가 가능하다.
- 10-Q도 Part/Item title 기반 canonical topic 설계가 가능하다.

### 004_itemCoverage.py 완료

- 10-K filings: `35`, median sections: `21`
- 10-Q filings: `103`, median sections: `11`, full document filing ratio: `0%`
- 20-F filings: `35`, median sections: `28`

결론:
- 10-K, 10-Q, 20-F 모두 source-native item 구조로 갈 수 있다.
- 현 단계 패키지 배치는 `10-K/10-Q/20-F structured` 조합으로 올릴 수 있다.

### 005_boundaryCandidates.py 완료

- 10-K canonical candidate: `21`
- 10-Q canonical candidate: `11`
- 20-F canonical candidate: `27`
- 결과 파일: `output/formTopicDrafts.json`

결론:
- form-native canonical topic draft를 만들 수 있는 최소 데이터가 이미 확보됐다.
- 10-K와 10-Q는 거의 완성형 teacher set이 나왔다.

### 006_buildCanonicalRowTable.py 완료

- 결과 파일: `output/canonicalRows.parquet`
- rows: `3,515`
- companies: `16`
- periods: `69`
- topics: `62`

결론:
- source-native topic 기반 canonical row 학습 테이블 생성이 가능하다.

### 007_fastHorizontalizeFromTable.py 완료

- 대표 ticker: `AAPL`
- rows: `389`
- periods: `47`
- topics: `26`

결론:
- canonical row 테이블만으로 빠른 topic x period horizontalization이 가능하다.
- 현재 topic namespace는 `10-K::Item 1. Business`, `10-Q::Full Document`처럼 source-native를 보존한다.

### 008_deploymentReadiness.py 완료

- 로컬 docs 대상 ticker: `7`
- status `ok`: `7`
- status `error`: `0`

결론:
- 현재 로컬 docs 범위에서는 EDGAR `sections()` 파이프라인이 무에러로 동작한다.
- 패키지 배치는 가능하고, 남은 과제는 실행 안정성보다 topic 품질과 수집 확대다.

### 009_generateSectionMappingsDraft.py 완료

- 20-F candidate coverage: `27/27`
- 10-Q candidate coverage: `11/11`
- 10-K candidate coverage: `21/21`

결론:
- 현재 candidate 기준 mapping coverage는 `100%`다.

### 현재 패키지 상태

- `src/dartlab/engines/edgar/docs/sections/` 초안 추가
- `sections(stockCode)`로 source-native topic x period DataFrame 생성 가능
- topic namespace는 `form_type::topicId`
- 초기 `sectionMappings.json` 반영
  - 10-K candidate `21/21` 커버
  - 20-F candidate `27/27` 커버
  - 10-Q candidate `11/11` 커버
- 테스트: `27 passed`

판단:
- 현재 수준으로도 EDGAR docs `sections`를 실험적 패키지 초안이 아니라 패키지 배치 가능한 초기 버전으로 둘 수 있다

### 012_mappingCoverageSnapshot.py 진행 중

- local docs가 늘어날 때마다 candidate/raw coverage를 자동 측정
- 최신 표본 기준 raw/candidate coverage는 전 form `100%`까지 회복 가능함을 확인
- 새 long-tail title이 나오면 `mapper.py` 정규화 또는 `sectionMappings.json`으로 즉시 흡수하는 운영 루프가 자리잡았다

결론:
- EDGAR section map은 한 번에 완결하는 방식이 아니라, 수집 확대와 동시에 mapping을 점진 흡수하는 구조로 package 운영이 가능하다.

### 013_tableFidelity.py 추가

- 목적: `055_edgarDocs`와 `056_sectionMap` 공통 이슈인 table markdown 보존을 EDGAR package invariant로 감시
- form_type별 table-containing section 비율과 table line 비중을 측정

결론:
- EDGAR docs package는 section title coverage뿐 아니라 table markdown fidelity까지 readiness 기준에 포함해야 한다.

## 현재 패키지 readiness 기준

- `loadData(..., category="edgarDocs")`는 local → release → SEC fallback으로 동작
- `sections()`는 `form_type::topicId` 기준 topic × period DataFrame을 반환
- `10-K`, `10-Q`, `20-F` 모두 structured split
- `section_content`는 text + markdown table을 함께 보존
- current local corpus 기준 `sections()` 무에러
- mapping coverage는 최신 표본에서 raw/candidate 모두 `100%` 회복 가능
