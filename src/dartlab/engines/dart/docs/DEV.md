# DART Docs Development Guide

상세 문서:
- `src/dartlab/engines/dart/docs/dev/sections.md`
- `src/dartlab/engines/dart/docs/dev/learning.md`

## sections 핵심 원칙

- `sections`가 docs source of truth다.
- markdown/table 경계를 버리지 않는다.
- 같은 topic 안의 원문 block 순서를 `blockOrder`로 보존한다.
- 셀에는 요약이 아니라 해당 기간의 원문 payload를 유지한다.
- table-heavy topic은 `sections`에서 다시 추출한다.
- 기존 docs 개별 parser는 archive/legacy fallback로 남긴다.

### 텍스트 구조 계층 원칙 (2026-03-18)

- 텍스트의 `소제목 레벨`, `headingPath`, `segment`, `paragraph` 복원은 viewer 임시 규칙이 아니라 `sections` 계층 책임이다.
- raw `sections`는 계속 `topic × blockType × blockOrder × period` source-of-truth로 유지한다.
- 그 위에 `sections` 파생 계층으로 `text structure` 또는 `textSegments`를 만든다.
  - `section title mapper`: 장/절 제목을 topic으로 매핑
  - `text heading splitter`: body 내부의 `가.`, `1.`, `(1)`, `①` 등 소제목 레벨 복원
  - `segment matcher`: 기간 간 같은 텍스트 segment 정렬
  - `paragraph splitter`: segment 내부 비교 단위 복원
- viewer는 위 구조를 소비해 렌더링만 담당한다. viewer 안에서 문서 구조를 다시 해석하는 로직은 임시 보정으로 보고 점진적으로 제거한다.

## viewer.py — 공시뷰어 presentation layer

### textDocument 계층 (2026-03-18)

- `viewerBlocks()`는 여전히 원자 블록 단위(`text`, `structured`, `raw_markdown`, `finance`, `report`)를 반환한다.
- 그 위에 `viewerTextDocument()`를 추가하여 **텍스트 전용 타임라인 문서**를 만든다.
- 기본 단위는 `body text block`이다.
  - `heading` 블록은 다음 `body` 블록의 section header로 흡수한다.
  - body 앞머리의 짧은 heading line도 현재는 viewer 단계에서 구조 anchor로 분리하지만, 장기적으로는 `sections text structure`로 이동한다.
  - 테이블/정형 블록은 textDocument에서 제외하고 하단 별도 구역에서 렌더링한다.
- `textDocument` 책임:
  - `PeriodRef` canonical period (`2024`, `2024Q1`)
  - section별 `latest` snapshot
  - section별 `timeline[]`
  - period별 `views[label] = { body, prevPeriod, diff }`
- 초기 UI는 `latest` 원문만 보여준다.
- timeline click 시 그 section만 `선택 period vs 직전 동주기` diff를 원문 위치에 맞춰 렌더링한다.
- `blocks`는 raw/non-text source layer, `textDocument`는 현재의 fully-renderable text layer다.
- 다만 `heading 추출`, `segment 분리`, `paragraph 분리`는 장기적으로 viewer가 아니라 `sections` 파생 계층으로 승격한다.

### 품질 검증 체크리스트 (매 변경 시 필수)

#### 1. 데이터 검증
- [ ] 삼성전자 companyOverview, businessOverview, salesOrder, dividend에서 viewerBlocks() 실행
- [ ] 삼성전자 companyOverview, businessOverview에서 viewerTextDocument() 실행
- [ ] text 블록: heading(소제목) vs body(서술형) 분류 정확한지
- [ ] heading 블록이 독립 본문으로 노출되지 않고 다음 body section header로 흡수되는가
- [ ] stale section에 최신 보유 period와 배지가 함께 노출되는가
- [ ] timeline이 절대 기간 라벨(2024, 2024Q1)만 쓰는가
- [ ] 클릭 시 선택 period와 직전 동주기만 비교하는가
- [ ] diff가 문서 순서대로 `same/removed/added` 위치를 보존하는가
- [ ] digest: 같은 유형 비교인지 (연간↔연간, Q1↔Q1), 숫자 추출이 의미 있는지
- [ ] structured 테이블: 기간 정렬, null 컬럼 제거
- [ ] finance 블록: scale/unit 정확

#### 2. 사용자 관점 검증
- [ ] 기간 라벨 일관성 (축약 금지, 2024/2024Q1 형식 통일)
- [ ] 첫 화면이 최신 원문만 보여주는가
- [ ] timeline을 눌렀을 때만 diff가 열리는가
- [ ] 텍스트가 body block 중심 보고서처럼 읽히는가 (섹션 헤더↔메타↔timeline↔본문)
- [ ] 기본 화면에 block별 raw 기간 선택기가 노출되지 않는가
- [ ] sticky 헤더와 겹치는 요소 없는가
- [ ] 호버/팝업 가려지지 않는가
- [ ] 전체화면 모드 정상 동작

### text 블록 분류 기준

| 분류 | 조건 | 처리 |
|------|------|------|
| heading | 3줄 이하 + 80자 미만 + 제목 패턴 | 제목 렌더링만, 변경 추적 없음 |
| body | 그 외 | digest + blame 적용 |

### 기간 라벨 규칙

- **모든 곳에서 동일 형식**: 2024, 2024Q1, 2024Q2, 2024Q3
- 축약 금지: `'24`, `24Q1` 등 사용하지 않음
- 사업보고서 = 연간 (2024), 분기/반기보고서 = 2024Q1/Q2/Q3

### digest 규칙

- 같은 보고서 유형 간 비교 (연간↔연간, Q1↔Q1)
- heading 블록에는 digest 생성하지 않음
- body 앞머리 inline heading도 diff/digest에서 제외
- 숫자 변경: 컨텍스트 포함 ("종속회사 232개 → 228개")
- 추가/삭제: 최대 3건, 나머지 "외 N건"
