# Review

analysis 결과와 credit 블록을 블록-템플릿으로 조립한 6막 서사 보고서.
analysis/credit 품질이 올라가면 review 품질도 올라간다.

| 항목 | 내용 |
|------|------|
| 레이어 | L2 |
| 진입점 | `c.review()`, `c.reviewer()` |
| 소비 | analysis + credit (블록식 조합) |
| 생산 | ai(reviewer), 사용자(터미널/HTML/마크다운/JSON), 블로그 보고서 |
| 출력 | rich, html, markdown, json |

## 단일 진입점

- **`c.review()` / `c.reviewer()`** 로 접근한다 (Company-bound)
- review는 analysis 결과와 credit 블록을 소비하여 보고서로 조립한다

## API

```python
c.review()              # 전체 보고서
c.review("수익구조")     # 단일 섹션
c.review(template="auto")  # 스토리 템플릿 자동 판별 + 강조 블록
c.reviewer()            # review + AI 종합의견
c.reviewer(guide="반도체 사이클 관점에서 평가해줘")
```

4개 출력 형식: `rich`(터미널), `html`, `markdown`, `json`

## 아키텍처

```
catalog.py          단일 진실의 원천 (블록 메타 + 섹션 메타 + 순서)
  ├── templates.py  섹션별 설정 (visibleKeys, helper, aiGuide) + 7개 스토리 템플릿
  ├── builders.py   analysis calc* → Block 리스트 변환 (narrate 호출)
  ├── narrate.py    Conditional Narrative Assembly — 임계값 중앙 관리 + 해석 문장
  ├── registry.py   buildBlocks() / buildReview() 조립 + emphasize 반영
  │     └── blockMap.py  BlockMap — 사용자 친화 블록 사전
  ├── publisher.py  블로그 보고서 발간 파이프라인
  ├── renderer.py   Rich 콘솔 렌더링
  ├── formats.py    HTML / Markdown / JSON 렌더링 + 6막 헤더 + 막 결론
  ├── blocks.py     Block 타입 (Heading, Table, Text, Flag, Metric) + emphasized 필드
  └── section.py    Section dataclass
```

## catalog.py — 단일 진실의 원천

- `_BLOCKS` 리스트 = 블록 정의 + 렌더링 순서
- `SECTIONS` 리스트 = 섹션 정의 + 렌더링 순서
- **key는 불변** — 한번 등록된 key는 영구 유지
- **label은 자유** — 사용자 표시명은 언제든 변경 가능
- **리스트 정의 순서 = 렌더링 순서** (list로 순서 보장)
- catalog label 하나 바꾸면 전체 렌더링이 따라간다
- builders.py에 하드코딩된 HeadingBlock title은 **0개**

## BlockMap — 사용자 친화 블록 사전

```python
b = c.blocks()
b["매출 성장률"]      # 한글 label
b["growth"]          # 영문 key
b.growth             # attribute (tab-complete)
b                    # 섹션별 카탈로그 테이블
```

오타 시 `KeyError: 'grwth' — 혹시: growth?`

## 블록 추가 절차

1. `catalog.py`: `_BLOCKS`에 BlockMeta 추가
2. `builders.py`: builder 함수 작성, `_meta(key).label`로 title
3. `registry.py`: `buildBlocks()` 안에 추가
4. `templates.py`: 섹션의 `visibleKeys`에 key 추가

**라벨 변경**: catalog.py label만 변경. 끝. 전부 자동 반영.
**순서 변경**: catalog.py _BLOCKS 위치만 이동. 끝.

## DART/EDGAR 통합 동작

review는 Company-bound — DART/EDGAR 자동 분기.

### 통화 포맷
- `company.currency` → `_REVIEW_CURRENCY` contextvars 자동 설정
- KRW: 조/억 포맷 (예: "매출 39.2조원")
- USD: $B/$M 포맷 (예: "Revenue $394.3B")
- `review/registry.py::buildBlocks()`에서 자동 적용

### EDGAR review 동작

```python
c = Company("AAPL")
c.review()               # 전체 6막 보고서 (USD 포맷)
c.review("수익구조")      # 단일 섹션
c.reviewer()             # review + AI 종합의견
```

6막 서사 구조, 블록 카탈로그, 4개 출력 형식 전부 EDGAR에서 동일 동작.

## 스토리 템플릿 체계

기업 특성에 따라 보고서의 강조점을 자동 조정한다.

### 7개 템플릿

| 템플릿 | 판별 조건 | 강조 블록 |
|--------|----------|----------|
| 사이클 | 영업이익률 CV > 0.4 | 부문매출, 마진, CAPEX, 운전자본, ROIC Tree |
| 프랜차이즈 | CV < 0.15, 마진 > 10% | 마진, 현금품질, 배당, 스코어카드 |
| 턴어라운드 | 최근 3년 내 적자→흑자 | 마진, 레버리지, 부실판별, CF |
| 성장 | CAGR > 15% | 성장추이, CAGR, ROIC, 매출전망 |
| 자본집약 | PPE/자산 > 40% | CAPEX, OCF분해, 자산구조, Penman |
| 지주 | 지분법/영업 > 30% | 영업외분해, 지분추이, 배당, 자산 |
| 현금부자 | 순현금 + 현금/자산 > 20% | 자금원천, Penman, 배당, FCF사용처 |

### 템플릿 구조

각 템플릿은 `templates.py`의 `STORY_TEMPLATES` dict에 정의:

```python
"사이클": {
    "description": "...",
    "emphasize": {...},       # 강조 블록 set → ★ 마크
    "keyQuestions": [...],    # 핵심 질문 4개
    "actFocus": {...},        # 막별 관전 포인트
    "industryContext": "...", # 업종 맥락 (AI 참조)
    "peerAxes": [...],        # 비교 축
}
```

- `detectTemplate(company)` — 재무 데이터로 자동 판별
- `detectTemplates(company)` — 복수 매칭 (예: 사이클 + 자본집약)
- 새 템플릿 추가: dict 하나 추가 + detectTemplate에 판별 조건 추가

### emphasize 동작

`registry.py::buildReview(template="auto")`에서:
1. `detectTemplate()` 호출 → 템플릿 판별
2. `STORY_TEMPLATES[template]["emphasize"]` 로드
3. 블록 조립 시 해당 key의 블록에 `Block.emphasized = True`
4. `formats.py`에서 `★` 마크 표시

## Conditional Narrative Assembly (narrate.py)

AP통신/Arria NLG 패턴. 데이터 값의 변화율/수준/추세에 따라 해석 문장을 조건 분기.
AI 없이 100% 결정론적, 환각 0%.

### 임계값 중앙 관리

```python
# narrate.py
_THRESHOLDS = {
    "margin_delta": [(5, "대폭 확대"), (1, "개선"), (-1, "보합"), (-5, "하락"), (None, "급락")],
    "debt_ratio": [(50, "매우 안정적"), (100, "안정적"), ...],
    ...
}
```

기준을 바꾸면 모든 해석 문장이 자동 반영.

### narrate 함수 9개

| 함수 | 적용 블록 | 해석 내용 |
|------|----------|----------|
| narrateGrowth | growth | YoY + CAGR 방향성 |
| narrateMargin | marginTrend | 마진 변화 + 수준 + 추세 |
| narrateCashFlow | cashFlowOverview | CF 패턴 + FCF 방향 |
| narrateCashQuality | cashQuality | OCF/NI 현금 전환 판정 |
| narrateLeverage | leverageTrend | 부채비율 수준 + 추세 |
| narrateDistress | distressScore | Z-Score 구간 판정 |
| narrateROIC | roicTimeline | ROIC vs WACC 가치 창출/파괴 |
| narrateValuation | valuationSynthesis | 저/적정/고평가 + 안전마진 |
| narrateConcentration | concentration | HHI 집중도 판정 |

### 막 결론 (buildActSummary)

각 막이 끝날 때 1-2문장 결론 자동 생성. 사용한 thread는 재사용하지 않아 6막 전부 고유.

## 보고서 발간 (publisher.py)

review 보고서를 블로그 포스트로 자동 발간.

### API

```python
from dartlab.review.publisher import publishReport, publishBatch

publishReport("005930")               # 단일 기업
publishReport("005930", template="사이클")  # 템플릿 수동 지정
publishBatch(["005930", "000660"])     # 배치 (순차, 메모리 안전)
```

### 발간 경로

```
blog/05-company-reports/{순번}-{종목코드}-{기업명}/index.md
```

### frontmatter 구조

```yaml
---
title: "삼성전자 — 사이클의 파도 위에서"
date: 2026-04-04
category: company-reports
series: company-reports
stockCode: "005930"
corpName: "삼성전자"
storyTemplate: "사이클"
grade: "dCR-AA+"
---
```

### 보고서 구성

```
frontmatter
보고서 헤더 (템플릿명, 섹터, 데이터 기준)
요약 카드 (결론 + 강점 + 경고)
스토리 템플릿 핵심 질문
재무 순환 서사

# 제1막: 이 회사는 뭘 하는가
  > 핵심 질문 + 관전 포인트
  ★ 강조 블록 + 해석 문장 + 테이블
  **1막 결론**

> 1→2 전환 문장

# 제2막 ~ 제6막 (동일 패턴)

credit 보고서 링크 (있으면)
면책
```

### 정기 발간 체계

| 유형 | 주기 | 트리거 | 대상 |
|------|------|--------|------|
| 정기 보고서 | 분기 | 사업보고서 공시 후 2주 | KOSPI 시총 상위 30 |
| 이벤트 보고서 | 수시 | 실적 서프라이즈, 등급 변동 | 해당 종목 |
| 신규 커버리지 | 수시 | 사용자 요청 또는 신규 상장 | 개별 |

### credit과의 관계

- review 보고서에서 credit은 5막(안정성) 안의 **한 섹션**
- 상세 12섹션 분석은 credit 독립 보고서(04-credit-reports)로 링크
- 두 보고서는 독립 발간. credit publisher ≠ review publisher

### _registry.json

발간된 보고서 목록. publisher가 자동 관리.

```json
[{"stockCode": "005930", "corpName": "삼성전자", "order": 4, "template": "사이클", ...}]
```

## 6막 렌더링 (formats.py)

### 6막 헤더

각 막의 첫 섹션 앞에 자동 삽입:

```markdown
# 제1막: 이 회사는 뭘 하는가
> **핵심 질문**: 매출의 원천은 무엇이고 얼마나 빨리 성장하는가?
> **이 기업의 관전 포인트**: 부문별 매출 변동 진폭 + 재고 사이클
```

### 6막 전환 문장

데이터 기반 인과 연결 (narrative.py::buildActTransitions):

```
1→2: "매출 333.6조에서 영업이익률 13.1% — 이 마진의 원천은?"
2→3: "순이익 45.2조 → 영업CF 85.3조 (189%) — 이익이 현금으로 뒷받침되는가?"
```

## 품질 검증

- 빈 섹션, 중복 표시, 극단값 비율(수만%), 맥락 없는 경고 체크
- 공개 샘플: `docs/samples/{종목코드}.md` (10개)
- `grep -n 'HeadingBlock("' src/dartlab/review/builders.py` → 0건이어야 함
- 해석 문장 30개+ 확인 (narrate 함수 9개 × 커버리지)
- 막 결론 6개 전부 고유 확인
- Polars 박스 아트 0개, 과학 표기법 0개

## 관련 코드

| 파일 | 역할 |
|------|------|
| `src/dartlab/review/catalog.py` | 블록/섹션 메타, 순서 (단일 진실의 원천) |
| `src/dartlab/review/templates.py` | 섹션 설정 + 7개 스토리 템플릿 |
| `src/dartlab/review/narrate.py` | 해석 문장 생성 (임계값 중앙 관리) |
| `src/dartlab/review/builders.py` | calc* → Block 변환 + narrate 호출 |
| `src/dartlab/review/registry.py` | buildBlocks/buildReview 조립 + emphasize |
| `src/dartlab/review/publisher.py` | 블로그 보고서 발간 |
| `src/dartlab/review/formats.py` | 6막 헤더 + 막 결론 + 마크다운/HTML/JSON |
| `src/dartlab/review/narrative.py` | 7개 인과 패턴 감지 + 6막 전환 문장 |
| `src/dartlab/review/blocks.py` | Block 타입 (emphasized 필드 포함) |
| `src/dartlab/review/summary.py` | 요약 카드 + 섹션 요약 |
| `src/dartlab/review/presets.py` | 관점별 프리셋 5개 |
