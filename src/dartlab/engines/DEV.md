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

## Company 핵심 사상 (2026-03-17 확정)

### sections = 전체 지도

`c.sections`가 회사의 전체 구조를 담는 **유일한 지도**다.

- docs 수평화 (topic × period) 위에 finance/report를 **같은 topic 안에 끼워넣음**
- chapter 순서 유지 (I~XII장)
- source 컬럼으로 docs/finance/report 구분
- 별도 index/profile 불필요 — sections 자체가 index

```
│ chapter │ topic           │ blockType │ blockOrder │ source  │ 2024   │
│ I       │ companyOverview │ text      │ 0          │ docs    │ 서술문 │
│ I       │ companyOverview │ table     │ 1          │ docs    │ 마크다운│
│ III     │ BS              │ table     │ 0          │ finance │ None   │
│ VII     │ dividend        │ text      │ 0          │ docs    │ 서술문 │
│ VII     │ dividend        │ table     │ 8          │ report  │ None   │
```

### show(topic, block) — sections 기반

show()는 **항상 sections 기반**으로 동작한다. 다른 경로 없음.

- `show(topic)` → 블록 목차 DataFrame (block, type, source, preview)
- `show(topic, N)` → 해당 blockOrder의 실제 데이터 DataFrame
  - source=docs → sections 원본 (text) 또는 수평화 (table)
  - source=finance → finance DataFrame (BS/IS/CF 등)
  - source=report → report DataFrame (dividend/employee 등)

### 테이블 수평화 4개 레이어

```
Layer 0: sections pipeline (완성)
  원본 parquet → topic × period 수평화, blockType 분리

Layer 1: cell parser (tableParser.py)
  단일 셀 마크다운 → 서브테이블별 구조화 파싱
  multi_year: 기수→연도 변환, 당기 값 추출
  key_value/matrix: 항목 × 값

Layer 2: block horizontalizer (_horizontalizeTableBlock)
  기간별 파싱 결과 merge → 항목×기간 매트릭스
  접미사 정규화 (부문 제거), 숫자 항목 필터, 이력형 감지

Layer 3: show() composer
  text + 수평화 table을 blockOrder 순서로 조합
```

### 현재 품질 상태 (2026-03-17)

**잘 되는 것:**
- dividend, companyOverview, shareCapital, rawMaterial, salesOrder 등 핵심 topic
- 283종목 에러 0

**table None (정상 스킵):**
- financialNotes/consolidatedNotes: K-IFRS 주석 — 구조 특수, 별도 처리 필요
- 연간 데이터 없는 블록, 유효 서브테이블 없는 블록

**유지보수 필요:**
- audit: 기수 포함 항목명 (제55기(당기)) — 매퍼로 해결
- boardOfDirectors: 이력형 테이블 감지 조정
- 괄호 내용 차이 (DS부문(메모리,SYS.LSI,DP) vs DS부문(메모리,SystemLSI,DP))
- matrix multi-column 값 구조 유지

### 매퍼 체계 (4개)

같은 패턴: 학습 → 매퍼 JSON → 수평화/표준화.

1. **accountMappings.json** — 계정명 → snakeId (finance)
2. **sectionMappings.json** — section_title → topic (sections)
3. **tableParser** — 구조 기반 테이블 파싱 (코드, 완성)
4. **itemMappings** — topic별 표준 항목 매핑 (미구현, 실험에서 패턴 수집 후)

## DART Company 구조

```python
c.sections          # 전체 지도 (docs + finance + report)
c.show("topic")     # 블록 목차
c.show("topic", N)  # 실제 데이터
c.topics            # topic 목록
c.trace("topic")    # source provenance
c.docs.sections     # pure docs 수평화
c.finance.BS/IS/CF  # finance 바로가기
c.report            # report API
```

## EDGAR Company 구조

```python
c.sections          # 전체 지도 (docs + finance)
c.show("topic")     # 블록 목차
c.show("topic", N)  # 실제 데이터
c.topics            # topic 목록
c.trace("topic")    # source provenance
c.docs.sections     # pure docs 수평화
c.finance.BS/IS/CF  # finance 바로가기
```

DART/EDGAR 동일 인터페이스. CompanyProtocol로 보장.

상세 문서:
- `src/dartlab/engines/dart/DEV.md`
- `src/dartlab/engines/edgar/DEV.md`
