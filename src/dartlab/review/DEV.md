# review 패키지 -- 블록 관리 체계

## 아키텍처

```
catalog.py          단일 진실의 원천 (블록 메타 + 섹션 메타 + 순서)
  |
  +-- templates.py  섹션별 설정 (visibleKeys, helper, aiGuide)
  +-- builders.py   analysis calc* 결과 -> Block 리스트 변환
  |
  +-- registry.py   buildBlocks() / buildReview() 조립
  |     |
  |     +-- blockMap.py  BlockMap -- 사용자 친화 블록 사전
  |
  +-- renderer.py   Rich 콘솔 렌더링
  +-- formats.py    HTML / Markdown / JSON 렌더링
  +-- section.py    Section dataclass
  +-- blocks.py     Block 타입 (Heading, Table, Text, Flag, Metric)
  +-- layout.py     ReviewLayout 설정
  +-- utils.py      포맷팅 유틸
```

## 핵심 규칙

### catalog.py -- 블록/섹션 단일 진실의 원천

- `_BLOCKS` 리스트 = 블록 정의 + 렌더링 순서
- `SECTIONS` 리스트 = 섹션 정의 + 렌더링 순서
- **key는 불변** -- 한번 등록된 key는 변경/재사용 금지
- **label은 자유** -- 사용자 표시명은 언제든 변경 가능
- **리스트 정의 순서 = 렌더링 순서** (dict가 아닌 list로 순서 보장)

### 라벨 관통 경로

```
catalog.py (label 정의)
  -> builders.py (_meta(key).label로 HeadingBlock title 생성)
    -> renderer/formatter (block.title 렌더링)
      -> 사용자 눈에 표시
```

catalog label 하나 바꾸면 전체 렌더링이 따라간다.
builders.py에 하드코딩된 HeadingBlock title은 0개.

### 한글 label 역인덱스

- `_LABEL_TO_KEY`: 한글 label -> 영문 key 역매핑 (catalog.py)
- `resolveKey(keyOrLabel)`: 영문 key 또는 한글 label -> key 반환
- `_suggest(query)`: 오타 시 difflib.get_close_matches로 유사 블록 제안

### BlockMap -- 사용자 친화 블록 사전

`blocks(company)` 또는 `buildBlocks(company)`가 반환하는 객체.

기능:
- `b["매출 성장률"]` -- 한글 label로 접근
- `b["growth"]` -- 영문 key로 접근
- `b.growth` -- attribute 접근 (tab-complete)
- `b` 찍으면 -- 섹션별 카탈로그 테이블 출력
- `b["<TAB>"]` -- Jupyter에서 한글 label 포함 자동완성
- 오타 시 -- `KeyError: 'grwth' -- 혹시: growth?`

dict 프로토콜 완전 호환: `keys()`, `values()`, `items()`, `get()`, `in`, `len()`, `iter()`

### templates.py -- 섹션별 표시 설정

- `_SECTION_CONFIG`: 섹션별 `visibleKeys`, `helper`, `aiGuide`
- `visibleKeys: None` = 섹션 전체 블록 표시
- `visibleKeys: [...]` = 명시된 블록만 표시
- `_buildTemplates()`: catalog SECTIONS 순서로 TEMPLATES dict 자동 생성
- 순서/title/partId는 전부 catalog에서 파생 -- templates.py에서 하드코딩 금지

### builders.py -- 블록 빌더 함수

- 각 함수: `analysis.financial.*.calc*()` 결과 dict -> Block 리스트 반환
- HeadingBlock title: 반드시 `_meta(key).label`로 catalog에서 가져옴
- 하드코딩된 title 0개 (grep `HeadingBlock("` 결과 0건이어야 함)
- builder 함수명과 catalog key 매핑은 registry.py에서 관리

### registry.py -- 조립기

- `buildBlocks(company)` -> `BlockMap` 반환
- `buildReview(company, section)` -> `Review` 반환
- `_safe(fn)`: 개별 블록 계산 실패 시 빈 리스트 반환 (전체 중단 방지)

## 블록 추가 절차

1. **catalog.py**: `_BLOCKS` 리스트에 `BlockMeta(key, label, section, description)` 추가
2. **builders.py**: builder 함수 작성, `_meta(key).label`로 title 설정
3. **registry.py**: `buildBlocks()` 안에 `b[key] = _safe(lambda: ...)` 추가
4. **templates.py**: 해당 섹션의 `visibleKeys`에 key 추가 (None이면 자동 포함)

## 블록 제거 절차

1. **catalog.py**: `_BLOCKS`에서 해당 BlockMeta 제거
2. **builders.py**: builder 함수 제거
3. **registry.py**: `buildBlocks()`에서 해당 라인 제거
4. **templates.py**: `visibleKeys`에서 해당 key 제거

## 라벨 변경 절차

1. **catalog.py**: 해당 BlockMeta의 `label` 문자열만 변경
2. 끝. builders/renderer/formatter 전부 자동 반영.

## 순서 변경 절차

1. **catalog.py**: `_BLOCKS` 리스트에서 해당 BlockMeta의 위치만 이동
2. 끝. templates/registry 전부 자동 반영.

## 섹션 구성

### 1부: 사업구조 분석

| 섹션 | partId | 블록 수 |
|------|--------|---------|
| 수익구조 | 1-1 | 10 |
| 자금조달 | 1-2 | 9 |
| 자산구조 | 1-3 | 5 |
| 현금흐름 | 1-4 | 3 |

### 2부: 재무비율 분석

| 섹션 | partId | 블록 수 | calc 파일 |
|------|--------|---------|-----------|
| 수익성 | 2-1 | 4 | analysis/financial/profitability.py |
| 성장성 | 2-2 | 3 | analysis/financial/growthAnalysis.py |
| 안정성 | 2-3 | 4 | analysis/financial/stability.py |
| 효율성 | 2-4 | 3 | analysis/financial/efficiency.py |
| 종합평가 | 2-5 | 3 | analysis/financial/scorecard.py |

2부 calc 함수는 모두 `company.finance.ratioSeries` → `(data, years)` 패턴을 사용한다.
종합평가만 예외: `company.insights`(grading.py)와 `company.annual`(scoring.py)도 소비.

## 검증 명령

```bash
# 하드코딩 title 잔존 확인 (0건이어야 함)
grep -n 'HeadingBlock("' src/dartlab/review/builders.py

# ruff
uv run ruff check src/dartlab/review/
uv run ruff format --check src/dartlab/review/

# 유닛 테스트
bash scripts/test-lock.sh tests/ -m "unit" -v --tb=short
```

## 파일별 책임 요약

| 파일 | 책임 | 수정 빈도 |
|------|------|----------|
| catalog.py | 블록/섹션 정의, 순서, 라벨, 역인덱스 | 블록 추가/라벨 변경 시 |
| blockMap.py | 사용자 친화 블록 사전 (한글 접근, repr, suggest) | 거의 안 바뀜 |
| templates.py | 섹션별 visibleKeys, helper, aiGuide | 표시 설정 변경 시 |
| builders.py | calc 결과 -> Block 리스트 변환 | 블록 추가/변경 시 |
| registry.py | buildBlocks/buildReview 조립 | 블록 추가/제거 시 |
| blocks.py | Block 타입 정의 | 새 블록 타입 필요 시 |
| renderer.py | Rich 콘솔 렌더링 | 렌더링 스타일 변경 시 |
| formats.py | HTML/Markdown/JSON 출력 | 출력 형식 변경 시 |
| section.py | Section dataclass | 거의 안 바뀜 |
| layout.py | ReviewLayout 설정 | 레이아웃 옵션 변경 시 |
| utils.py | fmtAmt 등 포맷팅 | 포맷 규칙 변경 시 |
