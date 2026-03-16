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
- `show(topic, period?)` : 실제 payload
- `trace(topic, period?)` : source provenance

**show(topic) 로직:**
1. finance topic(BS/IS/CF/CIS/SCE) → finance DataFrame
2. report topic → report DataFrame
3. sections topic → **단일 DataFrame**. 모든 기간 그대로. 기간 자르지 않음.
   - text 행: blockType="text", 항목=null, 기간 컬럼에 서술문 그대로
   - table 행: blockType="table", 항목=파싱된 행 라벨, 기간 컬럼에 셀 값
   - markdown을 파싱해서 행×열로 풀어서 text 행과 합친다
   - 반환형은 항상 DataFrame | None. ShowResult 사용하지 않음.

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

Svelte UI에서 sections를 직접 렌더링한다. 파이썬 모듈이 아니라 프론트엔드다.

**테이블** (blockType=table):
- sections 그대로 렌더링. 기간별 수평 테이블.

**텍스트** (blockType=text):
- 원문 전체를 보여주지 않는다. 3가지 뷰:
  1. **변화 지점** — 어느 기간에 무엇이 바뀌었는지 (sectionsDiff → entries)
  2. **변화 과정** — 기간별 추가/삭제 흐름 (topicDiff → added/removed/kept)
  3. **최종 상태** — 현재 텍스트에서 변경된 부분 표시

데이터 레이어: `common/docs/diff.py` (완성)
- `sectionsDiff(sections)` → 전체 변화 감지 (hash 기반)
- `topicDiff(sections, topic, from, to)` → 줄 단위 diff (difflib)

렌더링 레이어: Svelte UI (서버 제공)
- 변경 하이라이트, 기간 간 비교, 접기/펼치기
- 서버(FastAPI) UI에서 제공
- AI 분석에도 diff 컨텍스트를 기반으로 설명/요약

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

- `c.index` : finance + docs 통합 수평화 보드 (blockType 표시)
- `c.show(topic)` : finance → DataFrame, docs → ShowResult(text, table)
- `c.trace(topic)` : source provenance
- `c.topics` : 전체 topic 목록
- `c.docs`
  - `sections` (blockType 분리), `filings`, `show` → ShowResult
- `c.finance`
  - `BS`, `IS`, `CF`, `CIS`, `ratios`, `ratioSeries`, `timeseries`
- `c.report`
  - 향후 (SEC API 정형 데이터)
- `c.profile`
  - `sections` — docs spine + finance merge layer (구현 완료)

레거시 파서 없음. sections 수평화가 유일한 기초 경로.

## 매퍼 체계 (3개)

같은 패턴: 학습 → 매퍼 JSON → 수평화/표준화.

1. **accountMappings.json** — 계정명 → snakeId (finance)
2. **sectionMappings.json** — section_title → topic (sections)
3. **tableMappings.json** — 테이블 헤더 → 타입 + 항목 표준화 (미구현)

3번이 완성되면 show()에서 table을 finance처럼 항목 × period DataFrame으로 반환 가능.

상세 문서:
- `src/dartlab/engines/dart/DEV.md`
- `src/dartlab/engines/edgar/DEV.md`
