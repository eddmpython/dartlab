# Engines Development Guide

이 문서는 `src/dartlab/engines/` 하위 엔진 구조를 설명하는 내부 개발 문서다.

## 레이어

- 루트 facade
  - `dartlab.Company`
  - `dartlab.Compare`
- 엔진 본체
  - `dartlab.engines.dart.*`
  - `dartlab.engines.edgar.*`

의존 방향:
- 루트 facade -> 엔진 본체
- 엔진 본체 -> 루트 facade 금지

## Company 핵심 사상

4개 레이어 + 대시보드로 구성된다.

### Layer 1. sections 수평화 (뼈대)

sections가 Company의 구조적 뼈대다.
topic(행) × period(열) DataFrame으로, 한 회사의 모든 정보를 하나의 수평 구조에 담는다.
이것이 docs의 source of truth이며, 모든 비교의 기준축이 된다.

특정 기간에만 존재하는 세부 정보가 있으면 행을 내려서 세분화한다.
예: "매출현황" 아래에 2022년부터 "지역별매출" 테이블이 추가되면,
지역별매출 행을 추가하고 2020-2021은 null로 둔다.
이렇게 해야 기간 간 수평 비교가 깨지지 않는다.

### Layer 2. source 대체 (Company)

docs 뼈대 위에서, 더 강력한 수치적 데이터가 있으면 대체한다.
- `finance` (XBRL 정규화): BS/IS/CF 숫자가 docs 요약재무보다 정확하고 표준화되어 있다
- `report` (정형 API): 배당/임원/감사 등 structured disclosure가 docs 서술형보다 정형화되어 있다
- docs는 서술형/정성 정보(business, mdna, 리스크 등)에서 authoritative하다

docs.sections 자체는 pure source로 절대 변하지 않는다.
Company 레벨에서 profile.sections를 만들 때 finance/report 것으로 대체한다.

이 레이어를 index / show / trace로 접근한다:
- `index` : 전체 수평화 보드
- `show(topic, period?, raw?)` : 실제 payload
- `trace(topic, period?)` : source provenance

### Layer 3. profile (시계열 문서화)

전 기간을 하나의 문서로 볼 수 있게 구조화하는 데이터 레이어다.

정보 유형별로 시계열 표현이 다르다:
- **텍스트**: 직접적 시계열 비교가 어려우므로 diff 추적으로 변천과정을 본다.
  언제 추가(added), 삭제(removed), 수정(edited), 이동(moved), 재기재(restated)됐는지
  changeLedger가 기간별 변화를 추적하고, evidence가 원본 블록을 제공한다.
  텍스트의 모든 변천과정을 텍스트로 다 볼 수 있는 구조.
- **테이블**: 스크롤 시계열 테이블로 기간별 값을 수평 나열.
- **finance/report**: 시계열 테이블로 연도별 숫자를 수평 나열.

### Layer 4. 뷰어 (렌더링)

Layer 3의 구조화된 데이터를 실제 눈에 보이게 렌더링한다.
- 프론트엔드(Svelte): 웹 브라우저에서 예쁘게 표시
- 터미널(Rich 등): CLI에서 구조화된 출력

### 최종형: 대시보드

Layer 4 위에 차트/그래프를 포함한 대시보드를 별도 기능으로 얹는다.
시계열 테이블 + 텍스트 변천과정 + 차트 시각화를 하나의 화면에서 볼 수 있는 구조.

## DART Company 구조

- `c.docs`
  - `sections`, `retrievalBlocks`, `contextSlices`, `filings`
- `c.finance`
  - `BS`, `IS`, `CIS`, `CF`, `SCE`, `ratios`, `timeseries`
- `c.report`
  - 28개 apiType 체계, `result()`, `status()`, `extract()`, `extractAnnual()`
- `c.profile`
  - merged layer

기본 사용은 `Company(...)` 후 `index/show/trace`다.

## EDGAR Company 구조

- `c.index` : finance + docs 통합 수평화 보드
- `c.show(topic)` : finance/ratios/docs 자동 라우팅
- `c.trace(topic)` : source provenance
- `c.topics` : 전체 topic 목록
- `c.docs`
  - `sections`, `filings`, `show`
- `c.finance`
  - `BS`, `IS`, `CF`, `ratios`, `ratioSeries`, `timeseries`
- `c.report`
  - 향후 (SEC API 정형 데이터)
- `c.profile`
  - 향후 (docs + finance merge)

레거시 파서 없음. sections 수평화가 유일한 기초 경로.

상세 문서:
- `src/dartlab/engines/dart/DEV.md`
- `src/dartlab/engines/edgar/DEV.md`
