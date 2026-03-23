# Engines Development Guide

이 문서는 `src/dartlab/engines/` 하위 엔진 구조를 설명하는 내부 개발 문서다.

## 레이어 (5-Pillar 구조)

```
engines/
├── common/      # L0: 공유 유틸 (protocols, finance, docs)
├── company/     # L1: 데이터 소스 → Company 객체
│   ├── dart/    # 한국 DART
│   ├── edgar/   # 미국 EDGAR
│   └── edinet/  # 일본 EDINET
├── gather/      # L2: 외부 수집 (naver/yahoo/fred/listing)
├── analysis/    # L2: 분석 모듈 통합
│   ├── sector/  # WICS 섹터 분류
│   ├── insight/ # 7영역 등급
│   ├── rank/    # 시장 순위
│   ├── esg/     # ESG 분석
│   ├── supply/  # 공급망
│   ├── event/   # 이벤트 스터디
│   ├── watch/   # 공시 변화 감지
│   └── analyst/ # 밸류에이션 합성
└── ai/          # L3: LLM 분석 (5 providers)
```

의존 방향:
- 루트 facade (`dartlab.Company`) -> 엔진 본체
- 엔진 본체 -> 루트 facade 금지
- L2 analysis -> L1 company (lazy import만)
- L3 ai -> L1 + L2 (모두 소비)

## Company 핵심 사상 (2026-03-18 확정)

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

## Compare 제거 원칙 (2026-03-18 확정)

- 공개 진입점은 `Company` 하나로 수렴한다.
- 루트 `dartlab.Compare`와 엔진별 `Compare`는 사용처가 없으면 유지하지 않는다.
- 기업 간 비교가 다시 필요해지면 기존 `Compare` 추상화를 복원하지 않고 `Company` 기반 API 위에서 새로 설계한다.
- 뷰어의 table 정렬/표시 문제를 `Compare` 개념으로 설명하지 않는다.

## 엔진 추가 규칙

1. **새 엔진 폴더 생성 전 기존 엔진에 모듈로 추가할 수 있는지 먼저 검토**
2. 같은 계층(L1/L2/L3)의 같은 성격 기능은 하나의 엔진 아래 모듈로 구성
3. 엔진 폴더 1개 = 500줄짜리 파일이 아니라 의미 있는 도메인 단위
4. 새 L2 분석 기능 → `analysis/` 아래 모듈로 추가
5. 새 외부 수집 소스 → `gather/domains/` 아래 파일로 추가
6. 새 국가 데이터 소스 → `company/` 아래 엔진으로 추가
7. `spec.py` 필수: 새 모듈 추가 시 `spec.py` 작성 → `ai/spec.py`에 등록
   - 현재 spec.py 보유: sector, insight, rank, esg, supply, event, watch (7/8 모듈)
   - analyst 모듈은 spec.py 미구현 — 향후 추가 필요
8. 기존 5-Pillar 구조(common/company/gather/analysis/ai)를 넘는 6번째 기둥은 만들지 않는다

## 상세 문서

- `engines/company/DEV.md` — L1 데이터 소스 통합
- `engines/company/dart/DEV.md` — DART 본체
- `engines/company/edgar/DEV.md` — EDGAR 본체
- `engines/analysis/DEV.md` — L2 분석 모듈 통합
- `engines/gather/DEV.md` — L2 외부 수집
- `engines/ai/DEV.md` — L3 LLM 분석
- `engines/common/finance/DEV.md` — 재무 분석 유틸
- `engines/common/docs/DEV.md` — 문서 공통 유틸
