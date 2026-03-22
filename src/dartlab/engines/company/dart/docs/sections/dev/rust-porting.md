# sections Rust 포팅 가이드

> 이 문서는 `sections/pipeline.py` 핵심 로직을 Rust(pyo3-polars)로 마이그레이션하기 위한
> 인터페이스 명세, 의존 관계, 로직 상세를 기록한다.

## 실측 프로파일 (2026-03-20, 삼성전자 기준)

| 구간 | 시간 | 비율 | Rust 대상 |
|------|------|------|----------|
| DataFrame 조립 (dict 누적 → pl.DataFrame) | 1,468ms | 50.6% | Phase 3 |
| _expandStructuredRows (textStructure 파싱) | 714ms | 24.6% | Phase 2 |
| _reportRowsToTopicRows (상태 머신) | 576ms | 19.8% | Phase 2 |
| ├─ _splitContentBlocks 단독 | 318ms | 11.0% | Phase 1 |
| iterPeriodSubsets (selectReport) | 220ms | 7.6% | 비대상 |
| loadData (parquet I/O) | 145ms | 5.0% | 비대상 |
| mapSectionTitle 체인 | 3.7ms | 0.1% | Phase 1 (병목 아니지만 합성용) |

다종목: 2.4~3.2초/종목 (행 6,851~13,967 × 컬럼 63~70)

---

## 포팅 원칙

1. **변하지 않는 것만 Rust로 굳힌다** — 스키마 진화 중인 메타는 Python에 남김
2. **bottom-up**: 잎 함수 → 합성 함수 → 파이프라인 순서
3. **Python fallback 유지**: Rust 빌드 실패 시 Python 구현으로 자동 대체
4. **테스트 동일성**: Python 구현과 Rust 구현의 출력이 byte-identical

---

## Phase 1: 잎 함수 (순수 문자열 처리)

### 1-1. `_splitContentBlocks(content: str) -> list[(str, str)]`

**위치**: pipeline.py:196-241
**실측**: 318ms/종목 (11%)
**안정성**: 완전 안정 — 2개월+ 변경 없음

**로직**:
```
입력: 마크다운 텍스트 (text + table 혼합)
출력: [(blockType, blockText), ...] 순서 보존

규칙:
1. "|"로 시작하는 줄 → table
2. 나머지 → text
3. 빈 줄이 table 중간에 나오면 table 블록 종료
4. 빈 줄이 text 중간에 나오면 buffer에 추가 (줄바꿈 유지)
5. text↔table 전환 시 이전 블록 flush
6. 결과에서 빈 블록 제거
```

**Rust 인터페이스**:
```rust
fn split_content_blocks(content: &str) -> Vec<(String, String)>
// blockType: "text" | "table"
// blockText: 해당 블록의 원문 (strip된 상태)
```

**의존**: 없음 (순수 문자열)

---

### 1-2. `_detect_heading(line: str) -> Option<(int, str, bool)>`

**위치**: textStructure.py:149-193
**안정성**: 완전 안정

**로직**:
```
입력: 한 줄의 텍스트
출력: (level, label_text, is_structural) 또는 None

매칭 우선순위 (첫 매칭 반환):
1. [텍스트] 또는 【텍스트】    → level 1 (temporal marker면 structural=false)
2. I. II. III. (로마숫자)       → level 1
3. 1. 2. 3. (아라비아숫자)      → level 1
4. 가. 나. 다. (한글)           → level 2
5. (1) (2) (숫자 괄호)         → level 3
6. (가) (나) (한글 괄호)       → level 4
7. ① ② ③ (원문자)             → level 4
8. (텍스트) (짧은 괄호, ≤48자) → level 3 (noise 패턴 제외)

제외 조건:
- 빈 줄, "|"로 시작 (table), 120자 초과
- noise 패턴: "단위", "주1", "참고", "출처", "비고"
```

**Rust 인터페이스**:
```rust
fn detect_heading(line: &str) -> Option<(u8, String, bool)>
```

**의존**: `_is_temporal_marker()`, `_normalize_heading_text()` (둘 다 순수 regex)

---

### 1-3. `_normalize_heading_text(text: str) -> str`

**위치**: textStructure.py:77-86
**안정성**: 완전 안정

**로직**:
```
1. stripSectionPrefix (숫자/한글/로마 접두사 제거)
2. [] 【】 괄호 제거
3. (텍스트) 짧은 괄호 → 내부 텍스트만
4. "ㆍ" → "·"
5. 다중 공백 → 단일 공백
6. 후행 구두점 제거 (-–—:：;,)
```

**Rust 인터페이스**:
```rust
fn normalize_heading_text(text: &str) -> String
```

**의존**: `stripSectionPrefix` (regex 1개)

---

### 1-4. `_heading_key(text: str) -> str`

**위치**: textStructure.py:90-94
**안정성**: 완전 안정

**로직**:
```
1. _normalize_heading_text 호출
2. "·" "ㆍ" 제거
3. 비단어 문자 전부 제거 ([^0-9A-Za-z가-힣])
```

**Rust 인터페이스**:
```rust
fn heading_key(text: &str) -> String
```

---

### 1-5. `normalizeSectionTitle(title: str) -> str`

**위치**: mapper.py:96-105
**안정성**: 완전 안정 (99.95% 매핑률)

**로직**:
```
1. stripSectionPrefix (잎 번호 접두사 제거)
2. 업종 접두사 제거: "(금융업)" 등
3. stripSectionPrefix 재적용
4. 로마숫자 접두사 제거
5. "ㆍ" "·" → ","
6. 다중 공백 제거
7. 후행 구두점 제거
```

**Rust 인터페이스**:
```rust
fn normalize_section_title(title: &str) -> String
```

---

### 1-6. `mapSectionTitle(title: str) -> str`

**위치**: mapper.py:120-128
**안정성**: 완전 안정

**로직**:
```
1. normalizeSectionTitle 호출
2. sectionMappings.json HashMap 조회 (182개 매핑)
3. 매핑 있으면 반환
4. 없으면 _PATTERN_MAPPINGS 85개 regex 순차 매칭
5. 첫 매칭 반환, 없으면 normalized 그대로 반환
```

**Rust 인터페이스**:
```rust
struct SectionMapper {
    mappings: HashMap<String, String>,  // sectionMappings.json
    patterns: Vec<(Regex, String)>,     // _PATTERN_MAPPINGS
}

impl SectionMapper {
    fn map_title(&self, title: &str) -> String
}
```

---

### 1-7. `parseMajorNum(title: str) -> Option<int>`

**위치**: chunker.py
**안정성**: 완전 안정

**로직**:
```
로마숫자 접두사 (I. II. ... XII.) → 1~12 정수
없으면 None
```

**Rust 인터페이스**:
```rust
fn parse_major_num(title: &str) -> Option<u8>
```

---

### 1-8. `_semantic_segment_key(labelKey, topic) -> str`

**위치**: textStructure.py:112-130
**안정성**: 안정

**로직**:
```
1. "@"로 시작하면 그대로 반환
2. topic별 alias dict 조회 (_TOPIC_SEGMENT_ALIASES)
3. "에관한사항" 접미사 제거
4. "종속기업"/"종속회사" → "종속사"
5. businessOverview: "영업의개황" → "영업현황"
6. mdna: "환율변동영향" → "환율변동"
```

**Rust 인터페이스**:
```rust
fn semantic_segment_key(label_key: &str, topic: &str) -> String
```

---

## Phase 2: 합성 함수

### 2-1. `parseTextStructureWithState(text, sourceBlockOrder, topic, initialHeadings)`

**위치**: textStructure.py:196-315
**실측**: _expandStructuredRows 714ms의 대부분
**안정성**: 안정 (heading 패턴 체계 확정)

**로직**:
```
입력: 텍스트 블록, 초기 heading stack
출력: (nodes[], finalStack)

상태 머신:
- stack: [{level, label, key, semanticKey}, ...] heading 계층
- bodyLines: 현재 body 버퍼
- segmentOrder: 증가 카운터

줄 순회:
1. 빈 줄 → body 버퍼에 빈 줄 추가
2. _detect_heading 성공 → flush_body() + heading node 생성
   - structural heading → stack에서 같은/하위 level pop + push
   - non-structural (marker/alias) → stack 변경 없이 node만 추가
3. heading 아님 → body 버퍼에 추가
4. 마지막 flush_body()

각 node dict:
  textNodeType, textStructural, textLevel,
  textPath, textPathKey, textParentPathKey,
  textSemanticPathKey, textSemanticParentPathKey,
  segmentOrder, segmentKeyBase, text
```

**Rust 인터페이스**:
```rust
struct HeadingState {
    level: u8,
    label: String,
    key: String,
    semantic_key: String,
}

struct TextNode {
    node_type: String,      // "heading" | "body"
    structural: bool,
    level: u8,
    path: Option<String>,
    path_key: Option<String>,
    parent_path_key: Option<String>,
    semantic_path_key: Option<String>,
    semantic_parent_path_key: Option<String>,
    segment_order: u32,
    segment_key_base: String,
    text: String,
}

fn parse_text_structure(
    text: &str,
    source_block_order: u32,
    topic: &str,
    initial_headings: &[HeadingState],
) -> (Vec<TextNode>, Vec<HeadingState>)
```

**의존**: Phase 1의 1-2, 1-3, 1-4, 1-6, 1-8 전부

---

### 2-2. `_reportRowsToTopicRows(subset, contentCol) -> list[dict]`

**위치**: pipeline.py:244-338
**실측**: 576ms (이 중 _splitContentBlocks 318ms)

**로직**:
```
상태 머신:
- currentMajorNum: 현재 장 번호
- pendingChapter: 보류된 장 제목 행
- topicBlockCounts: (chapter, topic) → 다음 blockOrder

행 순회:
1. parseMajorNum 성공 → 이전 pendingChapter flush + 새 pending 보류
2. majorNum 없고 currentMajorNum도 없으면 skip
3. 일반 행 → pendingChapter flush + _registerContent 호출
   _registerContent:
     a. chapter 결정 (chapterFromMajorNum)
     b. topic 결정 (mapSectionTitle)
     c. _splitContentBlocks로 text/table 분리
     d. 각 block을 dict로 emit
```

**Rust 인터페이스**:
```rust
struct TopicRow {
    chapter: String,
    topic: String,
    block_type: String,
    block_order: u32,
    source_block_order: u32,
    text: String,
    major_num: u8,
    order_seq: u32,
    source_topic: String,
}

fn report_rows_to_topic_rows(
    titles: &[String],
    contents: &[String],
    mapper: &SectionMapper,
) -> Vec<TopicRow>
```

---

### 2-3. `_expandStructuredRows(rows) -> list[dict]`

**위치**: pipeline.py:341-460

**로직**:
```
1. projection 있으면 (majorNum, orderSeq, sourceBlockOrder) 정렬
2. 각 row에 대해:
   - table → 텍스트 구조 메타 null + segmentKey 설정
   - text → parseTextStructureWithState() 호출
     - 반환된 nodes를 개별 row로 확장
     - heading state를 topic별로 유지
3. 마지막에 occurrence 카운팅:
   - (topic, segmentKeyBase) 기준 순차 번호 부여
   - segmentKey = "{segmentKeyBase}|occ:{N}"
```

---

## Phase 3: DataFrame 조립

**실측**: 1,468ms (50.6%)

현재 Python dict 누적 패턴:
```python
topicMap: dict[(topic, segmentKey), dict[period, text]]
rowOrder: dict[(topic, segmentKey), dict[orderInfo]]
rowMeta: dict[(topic, segmentKey), dict[metadata]]
# ... 5개 더

# 최종 조립 (pipeline.py:1588-1673)
dataColumns = {col: [] for col in schema}
for key in sorted_keys:
    dataColumns["topic"].append(...)
    dataColumns["blockType"].append(...)
    for period in validPeriods:
        dataColumns[period].append(topicMap[key].get(period))
result = pl.DataFrame(dataColumns, schema=...)
```

**Rust 대안**: 전체 루프를 Rust에서 돌리고 Arrow RecordBatch로 반환
```rust
fn build_sections_dataframe(
    period_rows: HashMap<String, Vec<TopicRow>>,  // periodKey → rows
    valid_periods: Vec<String>,
    // ... config
) -> PyResult<PyDataFrame>  // pyo3-polars
```

---

## 의존 관계 DAG

```
Phase 1 (잎)
  parseMajorNum ────────────────────────┐
  stripSectionPrefix ──┐                │
  normalizeSectionTitle─┤                │
  mapSectionTitle ──────┘ (HashMap)      │
  _normalize_heading_text ──┐            │
  _heading_key ─────────────┤            │
  _semantic_segment_key ────┤            │
  _detect_heading ──────────┘            │
  _splitContentBlocks ──────────────────┤
                                         │
Phase 2 (합성)                           │
  parseTextStructureWithState ◄──── Phase 1 전부
  _reportRowsToTopicRows ◄──── parseMajorNum + mapSectionTitle + _splitContentBlocks
  _expandStructuredRows ◄──── parseTextStructureWithState

Phase 3 (조립)
  build_sections_dataframe ◄──── Phase 2 전부 + period 메타
```

---

## 정적 데이터 (Rust에 임베드)

| 데이터 | 크기 | 로딩 방식 |
|--------|------|----------|
| sectionMappings.json | 182개 매핑 | 빌드 타임 `include_str!` 또는 런타임 1회 로드 |
| _PATTERN_MAPPINGS | 85개 regex | `lazy_static!` 컴파일 |
| _TOPIC_SEGMENT_ALIASES | 4 topic × 5~15개 | `phf::Map` 또는 HashMap |
| _BUSINESS_OVERVIEW_COMPARABLE_ROOTS | 6개 | HashMap |
| _STRUCTURE_SLOT_ALIASES | 2 topic × 3~15개 | HashMap |
| REPORT_KINDS | 4개 튜플 | const |

---

## Rust crate 구조 (제안)

```
dartlab-core/
├── Cargo.toml
│   [dependencies]
│   pyo3 = { version = "0.22", features = ["extension-module"] }
│   polars = { version = "0.45", features = ["lazy"] }
│   pyo3-polars = "0.18"
│   regex = "1"
│   serde_json = "1"
│   once_cell = "1"          # lazy_static 대체
│   blake2 = "0.10"          # _body_anchor
│
├── src/
│   ├── lib.rs               # PyO3 모듈 진입점
│   ├── content.rs            # _splitContentBlocks
│   ├── heading.rs            # _detect_heading + _normalize + _heading_key
│   ├── mapper.rs             # SectionMapper (normalize + map + HashMap)
│   ├── structure.rs          # parseTextStructureWithState
│   ├── chunker.rs            # parseMajorNum
│   ├── topic_rows.rs         # _reportRowsToTopicRows
│   ├── expand.rs             # _expandStructuredRows
│   ├── assembly.rs           # build_sections_dataframe (Phase 3)
│   └── data/
│       └── sectionMappings.json
│
└── tests/
    ├── test_content.rs
    ├── test_heading.rs
    ├── test_mapper.rs
    └── test_structure.rs
```

---

## 검증 전략

1. **Golden test**: Python 구현으로 5종목(삼성전자/현대차/카카오/SK하이닉스/LG화학)의
   각 함수 입출력을 JSON으로 덤프 → Rust 구현의 출력과 byte-identical 비교
2. **벤치마크**: Python vs Rust 동일 입력 wall-clock 비교 (criterion.rs)
3. **회귀 방지**: Rust 빌드 실패 시 Python fallback으로 자동 전환

```python
# lib.rs 등록 후 Python 측
try:
    from dartlab_core import split_content_blocks
except ImportError:
    from dartlab.engines.dart.docs.sections.pipeline import _splitContentBlocks as split_content_blocks
```

---

## 예상 효과

| Phase | 대상 | Python | Rust 예상 | 배수 |
|-------|------|--------|----------|------|
| 1 | _splitContentBlocks | 318ms | ~10ms | 30x |
| 1 | heading 감지 체인 | ~50ms | ~2ms | 25x |
| 2 | parseTextStructureWithState | ~650ms | ~30ms | 20x |
| 2 | _reportRowsToTopicRows | ~250ms* | ~15ms | 17x |
| 3 | DataFrame 조립 | 1,468ms | ~50ms | 29x |
| **합계** | | **~2,750ms** | **~110ms** | **~25x** |

*_splitContentBlocks 제외한 나머지

종목당 3초 → **0.1초** 목표.
