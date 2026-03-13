# 056 사업보고서 섹션 맵 (Section Map)

## 핵심 사상

DartLab의 근원적 가치는 **"모든 것이 비교 가능"**이다.

finance 엔진이 한 일을 떠올리면:
- 270개 종목의 XBRL 계정ID가 전부 다르다 (34,249개 변형)
- 이걸 하나의 snakeId 체계로 통일했다 (accountMappings.json)
- 결과: **어떤 회사든 같은 계정명으로 수평 비교 가능**

sections도 완전히 같은 패턴을 밟는다:
- 270개 종목의 section_title이 회사마다 미세하게 다르다
- 이걸 하나의 표준 topic 체계로 통일한다 (sectionMappings.json)
- 결과: **어떤 회사든 같은 섹션명으로 수평 비교 가능**

이것이 완성되면 DartLab은 **한국 시장 사업보고서의 완전한 구조화 맵**을 보유하게 된다.
숫자(finance) + 텍스트(sections) + 실시간(report) — 세 축이 모두 같은 시간 축 위에 정렬되어,
한 회사의 모든 정보를 하나의 수평 비교 가능한 덩어리로 제공한다.

추가 원칙:
- docs 내부 개별 파서는 최종 목적이 아니라 과도기 결과물이다.
- 최종 source of truth는 `sections`와 그 하위 `retrievalBlocks/contextSlices`다.
- table-bearing topic은 `sections -> subtopic extractor`로 다시 뽑아 `Company.show()`와 docs 메서드가 그 결과를 쓰게 한다.
- 기존 docs 파서는 archive/legacy fallback으로만 남기는 방향이 맞다.
- 현재 `Company.show()` 1차 sections 전환 완료:
  - `salesOrder`
  - `riskDerivative`
  - `segments`
  - `rawMaterial`
  - `costByNature`
- `tangibleAsset`는 sections/detailTopic만으로는 아직 legacy `movementDf` 품질을 안정적으로 대체하지 못해 archive/fallback 유지가 맞다.
- 전회사 추가 coverage 실험:
  - `052_validateAdditionalShowCoverage.py`
  - `costByNature` / `tangibleAsset`는 legacy-heavy 경로라 전수 sweep이 느리다.
  - 현재 60개 종목 checkpoint 기준 `failure 0`, 단 `015760.costByNature`는 timeout 1건으로 별도 기록되며 재검증 대상이다.

이건 단순히 "섹션 이름 통일"이 아니다.
사업보고서라는 정해진 프레임 위에서, 모든 회사의 모든 기간을 겹칠 수 있게 만드는 것이다.
사용자는 세로로 읽으면 그 연도의 전체 보고서를, 가로로 읽으면 같은 정보의 시간 변화를 본다.

---

## 1. 현황

### 완료
- sections 파이프라인: 270종목 0에러, 3,567개 기간 처리
- DataFrame 구조화: topic(행) × period(열) = 텍스트
- 사업보고서 원본 순서 보존 (majorNum + 등장순서)

### 문제점
1. **leaf title 미통일**: "회사의 법적ㆍ상업적 명칭" vs "회사의 법적, 상업적 명칭" → 별도 행
2. **table_only 누락**: 테이블 90%+ 섹션이 sections DataFrame에서 빠짐
3. **FINANCE_ENGINE_COVERED skip**: III장 재무 섹션의 텍스트 서술 부분이 사라짐
4. **소분류 표기 차이**: "(제조서비스업)사업의 개요" vs "사업의 개요" — 업종 접두사
5. **연도별 구조 변화**: 1999~2025년 사이 사업보고서 양식이 여러 번 개정됨

---

## 2. 설계

### 2-1. 데이터 구조

**parquet 원본 컬럼:**
```
section_order (int)     — 섹션 순서
section_title (str)     — "I. 회사의 개요", "1. 회사의 연혁" 등
section_content (str)   — HTML 제거된 텍스트 + 마크다운 테이블
```

**대분류 (12장) — 전 종목 동일 (DART 규정):**
```
I.    회사의 개요
II.   사업의 내용
III.  재무에 관한 사항
IV.   이사의 경영진단 및 분석의견
V.    회계감사인의 감사의견 등
VI.   이사회 등 회사의 기관에 관한 사항
VII.  주주에 관한 사항
VIII. 임원 및 직원 등에 관한 사항
IX.   계열회사 등에 관한 사항
X.    대주주 등과의 거래내용
XI.   그 밖에 투자자 보호를 위하여 필요한 사항
XII.  상세표 (부속명세서)
```

**소분류 — 회사마다 다름, 표준화 필요:**
- I장: 5종, 90%+ 커버
- II장: 25종 (업종 접두사 변형 포함), 핵심 7개가 77~92%
- III장: 10종, 핵심 8개가 68~93%
- V장: 2종이 90%+, 나머지 noise
- VI장: 3종이 90%+
- VIII장: 2종이 89~91%
- XI장: 4종이 39~90%
- XII장: 79종 (회사별 고유 상세표), 핵심 3개가 91%+

**총 고유 소분류: 176종 (270종목 최신 사업보고서 기준)**

### 2-2. 매핑 파이프라인

finance의 accountMappings.json과 동일한 패턴:

```
원본 section_title
  ↓ 대분류(로마숫자) 파싱 → chapter 결정
  ↓ 소분류(숫자) 파싱 → subNum 결정
  ↓ 접두사 제거: "(제조서비스업)", "(금융업)" 등
  ↓ 공백/특수문자 정규화: "ㆍ" → ",", 연속공백 제거
  ↓ sectionMappings.json 조회 → 표준 topicId
  ↓ 미매핑 → 원본 유지 (but 로깅)
```

**sectionMappings.json 구조:**
```json
{
  "회사의 법적ㆍ상업적 명칭": "companyLegalName",
  "회사의 법적, 상업적 명칭": "companyLegalName",
  "(제조서비스업)사업의 개요": "businessOverview",
  "사업의 개요": "businessOverview",
  ...
}
```

topicId는 camelCase 영문 (snakeId와 같은 패턴).
label은 별도 dict: `{"companyLegalName": "회사의 법적·상업적 명칭", ...}`

### 2-3. 학습 사이클 (finance와 동일)

```
1. 전종목 스캔 → 미매핑 section_title 수집
2. 빈도 분석 → 같은 의미인 변형 그룹핑
3. 자동 규칙 적용 (공백 정규화, 접두사 제거, SequenceMatcher)
4. 수동 검토 → sectionMappings.json 업데이트
5. 매핑률 측정 → 반복
```

목표: **매핑률 95%+ (finance의 97%와 유사한 수준)**

### 2-4. Company 프레임 (registry 연동)

registry.py의 DataEntry에 `chapter` 필드 추가:

```python
@dataclass(frozen=True)
class DataEntry:
    ...
    chapter: int = 0       # 사업보고서 장 번호 (I=1, II=2, ..., XII=12)
    chapterSub: int = 0    # 장 내 소분류 순서
```

매핑 예시:
| 모듈 | chapter | chapterSub |
|------|---------|------------|
| companyOverview | 1 | 1 |
| companyHistory | 1 | 2 |
| shareCapital | 1 | 4 |
| business | 2 | 1 |
| productService | 2 | 2 |
| IS/BS/CF | 3 | 2~5 |
| dividend | 3 | 6 |
| mdna | 4 | 0 |
| audit | 5 | 1 |
| boardOfDirectors | 6 | 1 |
| majorHolder | 7 | 0 |
| employee | 8 | 1 |
| executivePay | 8 | 2 |
| affiliateGroup | 9 | 0 |
| contingentLiability | 11 | 1 |
| sanction | 11 | 3 |

KRCompany.all()이 chapter → chapterSub 순서로 정렬:
```
I장: companyOverview → companyHistory → shareCapital → ...
II장: business → productService → salesOrder → rnd → ...
III장: IS → BS → CF → fsSummary → dividend → bond → ...
IV장: mdna
V장: audit → internalControl
...
```

### 2-5. sections DataFrame의 위치

sections DataFrame은 **전체 사업보고서 텍스트의 수평 비교 뷰**다.
정량 모듈(IS, dividend 등)이 "숫자를 뽑는 도구"라면,
sections는 "텍스트를 정렬하는 도구"다.

둘은 겹치지 않는다:
- 정량 모듈이 커버하는 섹션 → sections에서 "(finance/report 엔진이 정량 처리)" 표시
- 나머지 텍스트 → sections가 담당

향후: table_only 섹션도 메타데이터(테이블 헤더, 행수)를 sections에 포함할지 검토

---

## 3. 실험 계획

### 재정의된 목표

056의 목표는 단순한 `section_title` 통일이 아니다.

- 사업보고서의 공통 chapter 틀을 기준으로
- 최근 연도/상세 기업이 가진 더 세분화된 경계를 추출하고
- 그 세분화된 섹션 안의 긴 텍스트를 다시 의미 단위로 쪼개어
- 전 기업을 하나의 canonical report map 위에 정렬하는 것이다.

즉 056은 세 단계로 진행된다.

1. boundary extraction
2. coarse-to-fine alignment
3. semantic atomization

최종 목표 구조:

```text
chapter
  -> canonicalSection
    -> canonicalSubsection
      -> semanticUnit
```

### 실험 001: 전종목 section_title 빈도표
- 270종목 × 전 기간 parquet에서 section_title 전수 추출
- (chapter, subNum, title) 빈도표 → 표준 후보 식별
- 연도별 양식 변화 추적 (1999→2015→2025)

### 실험 002: boundary 후보 추출
- 최근 연도 상세 기업의 세분화된 하위 섹션 목록 추출
- 2021 -> 2022처럼 세분화가 급증한 전환 구간 비교
- chapter별 canonical boundary 후보 목록 생성
- coarse 보고서가 어떤 boundary를 합쳐서 표현하는지 단서 확보

### 실험 003: semantic unit 후보 추출
- 세분화된 섹션 내부의 의미 단위 경계 패턴 탐색
- 가/나/다, bullet, 괄호 번호, 표 전후 설명 등을 경계 단서로 수집
- 정보 유형 후보 정의: 시장/경쟁/고객/원가/리스크/전략/투자/생산/계약
- canonicalSubsection 아래 semanticUnit 초안 생성

### 실험 004: sections DataFrame 매핑 적용
- pipeline.py에서 canonical boundary 체계 적용
- 적용 전/후 수평 매칭률 비교
- 세분화 전/후 보고서가 같은 canonicalSection 축에 정렬되는지 검증

### 실험 005: registry chapter 매핑
- 각 DataEntry에 chapter/chapterSub 할당
- KRCompany.all() 정렬 검증
- guide() 출력이 사업보고서 순서와 일치하는지 확인

### 실험 006: 커버리지 측정
- 원본 section_content 총 글자수 vs canonical map이 담은 글자수
- skip된 영역 + table_only 영역의 비율
- 정량 모듈과의 중복/누락 분석
- semanticUnit 분해 후 정보 손실 여부 점검

---

## 4. 파일 구조

```
experiments/056_sectionMap/
├── STATUS.md                    ← 이 파일
├── 001_titleFrequency.py        ← 전종목 section_title 빈도표
├── 002_boundaryCandidates.py    ← boundary 후보 추출
├── 003_semanticUnits.py         ← semantic unit 후보 추출
├── 004_applyMappings.py         ← DataFrame 적용 테스트
├── 005_registryChapter.py       ← registry chapter 매핑
└── 006_coverageMeasure.py       ← 커버리지 측정
```

**프로덕션 배치 대상:**
```
src/dartlab/engines/dart/docs/sections/
├── mapper.py          ← NEW: sectionMappings.json 기반 매핑
├── mapperData/
│   └── sectionMappings.json  ← NEW: 표준 topic 매핑 데이터
├── pipeline.py        ← 수정: mapper 적용
├── chunker.py         ← 수정: table_only/skip 전략 재검토
└── types.py           ← 유지

src/dartlab/core/
├── registry.py        ← 수정: DataEntry에 chapter 필드 추가
└── ...

src/dartlab/company.py ← 수정: all() 정렬 순서를 chapter 기반으로
```

---

## 5. 성공 기준

| 지표 | 현재 | 목표 |
|------|------|------|
| leaf title 매핑률 | 측정 안됨 | 95%+ |
| 삼성전자 topic 행 수 | 329 | ~200 (중복 통합) |
| 전종목 처리 에러 | 0 | 0 유지 |
| 사업보고서 원본 커버리지 | 측정 안됨 | 90%+ (텍스트 기준) |
| Company.all() 순서 | 모듈순 | 사업보고서 장순 |

---

## 6. 의존성

- finance 매핑 경험 (accountMappings.json, synonymLearner 패턴)
- parquet 원본 데이터 270종목
- sections 파이프라인 (완성됨)
- registry 구조 (수정 예정)

---

## 7. 실행 결과 (2026-03-11)

### 001_titleFrequency.py 완료

- 실행 파일: `experiments/056_sectionMap/001_titleFrequency.py`
- 스캔 파일 수: 270
- 총 `section_title` 행 수: 160,853
- 고유 `section_title` 수: 494
- Top10 소분류 커버리지: 23.20% (37,321 / 160,853)

핵심 관찰:
- 대분류 파싱 결과 `UNKNOWN` 비중이 큼(116,604행). 이는 로마숫자 장 제목이 아닌 하위목차(`1.`, `2.`...) 행이 다수 포함되기 때문.
- 소분류 상위 빈도는 재무/임원/주주/연혁 계열 항목에 집중.
- 다음 단계는 UNKNOWN 군집 문자열 정규화보다, 최근 연도 상세 기업의 boundary 추출에 집중해야 한다.

추가 관찰:
- 삼성전자 사업보고서는 2021년 31개 섹션에서 2022년 47개 섹션으로 급격히 세분화되었다.
- 따라서 056은 title normalize 실험보다 `2021 -> 2022` 전환 구간에서 canonical boundary를 추출하는 방식이 더 적절하다.

### 002_boundaryCandidates.py 완료

- 실행 파일: `experiments/056_sectionMap/002_boundaryCandidates.py`
- 2021 사업보고서 section 수: 31
- 2022 사업보고서 section 수: 47
- 추가된 boundary 후보 수: 24

핵심 후보:
- II장: `1. 사업의 개요`, `2. 주요 제품 및 서비스`, `3. 원재료 및 생산설비`, `4. 매출 및 수주상황`, `5. 위험관리 및 파생거래`, `6. 주요계약 및 연구개발활동`, `7. 기타 참고사항`
- V장: `1. 외부감사에 관한 사항`, `2. 내부통제에 관한 사항`
- XI장: `2. 우발부채 등에 관한 사항`, `3. 제재 등과 관련된 사항`, `7. 증권의 발행을 통한 자금조달에 관한 사항`
- XII장: `1. 연결대상 종속회사 현황(상세)`, `2. 계열회사 현황(상세)`, `3. 타법인출자 현황(상세)`, `4. 연구개발실적(상세)`

결론:
- 삼성전자 2022 사업보고서는 chapter 유지 + 하위 경계 세분화 패턴을 명확히 보여준다.
- 056의 canonical boundary teacher 샘플로 삼성전자 2022를 활용할 수 있다.

### 003_semanticUnits.py 완료

- 실행 파일: `experiments/056_sectionMap/003_semanticUnits.py`
- 분석 섹션: `1. 사업의 개요`, `4. 매출 및 수주상황`, `5. 위험관리 및 파생거래`, `6. 주요계약 및 연구개발활동`

패턴 관찰:
- `1. 사업의 개요` → `☞` 안내문 중심 (`guide_arrow=2`)
- `4. 매출 및 수주상황` → `가.` 6개, `(1)` 8개, 테이블행 77개
- `5. 위험관리 및 파생거래` → `가.` 3개, `(1)` 6개, 테이블행 38개
- `6. 주요계약 및 연구개발활동` → `가.` 4개, 테이블행 91개, `☞` 1개

결론:
- 세분화된 section 내부에도 추가 semantic unit 경계가 반복적으로 존재한다.
- 다음 단계는 title 매핑이 아니라 `가./나.`, `(1)/(2)`, 표 전후 설명, 안내문(`☞`)을 이용한 내부 분해 규칙 검증이다.

### 004_boundaryMapDraft.py 완료

- 실행 파일: `experiments/056_sectionMap/004_boundaryMapDraft.py`
- 삼성전자 2022 사업보고서를 기준으로 chapter별 canonical boundary draft 생성 완료

초안 결과:
- I장: 5개
- II장: 7개
- III장: 8개
- V장: 2개
- VI장: 3개
- VIII장: 2개
- XI장: 3개
- XII장: 4개

핵심 해석:
- 삼성전자 2022는 056의 boundary teacher 샘플로 충분할 정도로 세분화가 뚜렷하다.
- 다만 IV/VII/IX/X처럼 삼성전자 데이터만으로는 세부 boundary가 비어 있는 장이 있어, 다음 단계는 다른 기업을 함께 대조해 공통 boundary를 보강해야 한다.

### 005_crossCompanyBoundary.py 완료

- 실행 파일: `experiments/056_sectionMap/005_crossCompanyBoundary.py`
- 비교 기업 수: 10개

핵심 결과:
- I장 공통 boundary: 5/5가 10개 기업 모두 일치
- II장 공통 boundary: 7개 core가 8개 기업에서 동일하게 반복
- III장 공통 boundary: `2. 연결재무제표`를 제외하면 거의 전 기업 공통
- V장: 2개 모두 10개 기업 공통
- VI장: 3개 중 2개는 10개 기업 공통, 감사제도는 9개 기업 공통
- XI장: 3개 core가 10개 기업 공통
- XII장: 상위 3개 상세표는 10개 기업 공통, `4. 연구개발실적(상세)`는 5개 기업 공통

해석:
- 삼성전자 2022 draft는 상당 부분 범용 canonical boundary로 확장 가능하다.
- 다만 II장 업종 접두사 변형(`(금융업)`, `(제조서비스업)`)과 XII장 상세표는 업종별/회사별 보정 계층이 필요하다.

### 006_coarseToFineProjection.py 완료

- 실행 파일: `experiments/056_sectionMap/006_coarseToFineProjection.py`
- 삼성전자 2021 coarse 보고서를 2022 fine boundary 위로 역투영한 결과, fine-only row 24개 확인

chapter별 fine-only 후보:
- I장: `5. 정관에 관한 사항`
- II장: `1~7` 전체가 fine-only
- III장: `6. 배당`, `7. 자금조달`, `8. 기타 재무`
- V장: `1. 외부감사`, `2. 내부통제`
- VI장: `3. 주주총회 등에 관한 사항`
- XI장: `2. 우발부채`, `3. 제재`, `4. 작성기준일 이후 주요사항`
- XII장: `1~4` 상세표 전체

해석:
- coarse 연도는 최신 fine boundary의 상위 묶음으로 충분히 투영 가능하다.
- 특히 II/XI/XII장은 coarse-to-fine projection의 대표 사례로 볼 수 있다.

### 007_boundaryCoverage.py 완료

- 실행 파일: `experiments/056_sectionMap/007_boundaryCoverage.py`

chapter별 평균 커버리지:
- I: 1.00
- II: 0.80
- III: 0.99
- V: 1.00
- VI: 0.97
- VIII: 1.00
- XI: 1.00
- XII: 0.88

해석:
- I/III/V/VI/VIII/XI장은 canonical boundary로 바로 쓰기에 충분히 안정적이다.
- II/XII장은 업종/상세표 특성 때문에 변형 흡수 규칙이 추가로 필요하다.

### 008_semanticPatternCoverage.py 완료

- 실행 파일: `experiments/056_sectionMap/008_semanticPatternCoverage.py`

패턴 커버리지:
- `가./나.` heading: 8/10
- `(1)/(2)` 번호 패턴: 8/10
- 표 row (`|`): 8/10
- `☞` 안내문: 1/10

해석:
- semantic unit 분해는 특정 기업 전용이 아니라 범용 규칙으로 설계 가능하다.
- 특히 `가./나.`, `(1)/(2)`, 표 전후 텍스트는 2차 경계 추출의 핵심 신호다.

### 009_industryAwareNormalization.py 완료

- 실행 파일: `experiments/056_sectionMap/009_industryAwareNormalization.py`
- II장 exact avg coverage: 0.80
- II장 normalized avg coverage: 0.80

해석:
- 현재 대표 10개 샘플에서는 업종 접두사 제거만으로 평균 커버리지가 추가 상승하지 않았다.
- 이는 II장의 차이가 단순 접두사 문제가 아니라 업종별 boundary 자체 차이도 포함함을 시사한다.

### 010_tableAwareSemanticUnits.py 완료

- 실행 파일: `experiments/056_sectionMap/010_tableAwareSemanticUnits.py`

섹션별 table ratio:
- `4. 매출 및 수주상황`: 0.77 (text 23 / table 77)
- `5. 위험관리 및 파생거래`: 0.49 (text 39 / table 38)
- `6. 주요계약 및 연구개발활동`: 0.83 (text 19 / table 91)

해석:
- 대표 섹션 다수가 표 중심이며, 동시에 표 전후 설명 텍스트가 모두 존재한다.
- 따라서 semanticUnit와 tableMeta를 분리 저장하는 구조가 필요하다.

### 011_projectionScore.py 완료

- 실행 파일: `experiments/056_sectionMap/011_projectionScore.py`

chapter별 projection score:
- I: 0.80
- II: 0.00
- III: 0.62
- V: 0.00
- VI: 0.67
- VIII: 1.00
- XI: 0.00
- XII: 0.00

해석:
- 2021 coarse 보고서를 2022 fine map에 그대로 exact 투영하면 II/V/XI/XII 장은 사실상 실패한다.
- 즉 coarse-to-fine projection에는 chapter 내부의 상위-하위 boundary 관계를 명시하는 별도 규칙 계층이 필요하다.

### 추가 관찰: 현재 sections 추출 속도/수평화 상태

- `sections('005930')` 실행 시간: 약 3.08초
- 결과 shape: `(329, 106)`

해석:
- 속도 자체는 실사용 가능한 수준이다.
- 현재 병목은 추출 속도보다 수평화 품질이다. 같은 의미가 다른 topic으로 갈라지고, coarse/fine 연도 차이와 표/텍스트 혼합 때문에 수평 비교 품질이 아직 거칠다.

### 012_boundaryHierarchy.py 완료

- 실행 파일: `experiments/056_sectionMap/012_boundaryHierarchy.py`

핵심 결과:
- coarse -> fine 계층 초안 생성 완료
- 예시:
  - II장 coarse 없음 -> fine children 7개 전체
  - III장 coarse 6개 -> fine children `배당`, `자금조달`, `기타 재무`
  - XI장 coarse 없음 -> fine children `우발부채`, `제재`, `작성기준일 이후 주요사항`
  - XII장 coarse 없음 -> fine children `연결대상 종속회사`, `계열회사`, `타법인출자`, `연구개발실적`

해석:
- exact match가 아니라 boundary hierarchy(부모-자식 관계)를 두면 coarse/fine 연도 정렬이 가능해진다.

### 013_tableMetaSplit.py 완료

- 실행 파일: `experiments/056_sectionMap/013_tableMetaSplit.py`

분리 결과:
- `4. 매출 및 수주상황`: before 5 / table 87 / after 8
- `5. 위험관리 및 파생거래`: before 13 / table 62 / after 2
- `6. 주요계약 및 연구개발활동`: before 2 / table 108 / after 0

해석:
- 표 중심 섹션은 `narrative-before`, `table`, `narrative-after` 3분 구조로 안정적으로 분리 가능하다.
- 따라서 semanticUnit와 tableMeta를 별도 열/구조로 저장하는 설계가 유효하다.

## 9. 현재까지의 결론

- 먼저 section boundary 수준으로 수평화하고
- 그 다음 fine boundary로 세분화하며
- 마지막으로 내부 semantic unit와 tableMeta까지 나누는 계층형 접근이 가장 현실적이다.
- Polars 기반으로도 현재 수준의 집계/투영/커버리지 측정은 충분히 빠르게 수행 가능하다.

### 014_hierarchyProjectionDf.py 완료

- 실행 파일: `experiments/056_sectionMap/014_hierarchyProjectionDf.py`
- 결과 shape: `(34, 4)`
- 스키마: `chapter / coarseBoundary / fineBoundary / projectionKind`

해석:
- coarse/fine boundary 관계를 Polars DataFrame으로 직접 표현할 수 있음이 확인되었다.
- 이는 canonical map을 코드 레벨에서 DataFrame 중심으로 다루는 설계가 가능하다는 의미다.

### 015_semanticUnitExtractor.py 완료

- 실행 파일: `experiments/056_sectionMap/015_semanticUnitExtractor.py`
- 샘플 섹션(`5. 위험관리 및 파생거래`)에서 semantic unit row 7개 추출
- 스키마: `chapter / section / subsection / unitType / unitLabel / text`

해석:
- `가./나.` 및 `(1)/(2)` 경계를 기준으로 semantic unit row를 Polars-friendly하게 뽑을 수 있다.
- 표는 제외하고도 설명문 단위 수평화가 가능한 구조가 확인되었다.

### 016_canonicalMapPrototype.py 완료

- 실행 파일: `experiments/056_sectionMap/016_canonicalMapPrototype.py`
- 결과 shape: `(7, 8)`
- 스키마: `period / chapter / section / subsection / semanticUnit / unitType / text / tableRows`

해석:
- hierarchy + semantic unit + tableMeta(tableRows)를 한 DataFrame prototype으로 통합할 수 있음이 확인되었다.
- 즉 최종 sections 엔진 리팩터링은 nested object가 아니라 Polars DataFrame 중심으로도 충분히 가능하다.

## 10. 현재 설계 판단

- 먼저 section boundary를 수평화하고
- 그 다음 fine boundary를 hierarchy로 연결하고
- 마지막으로 semantic unit와 tableMeta를 추가하는 방식이 가장 현실적이다.
- 이 접근은 현재 데이터 특성(연도별 세분화 차이, 표/텍스트 혼합, 업종 변형)에 가장 잘 맞는다.
- Polars는 이 구조를 실험 단계에서 다루기에 충분한 성능과 표현력을 보여주고 있다.

### 017_integratedCanonicalPrototype.py 완료

- 실행 파일: `experiments/056_sectionMap/017_integratedCanonicalPrototype.py`
- 결과 shape: `(11,620, 9)`
- period 수: 27개 (삼성전자 전 연간 사업보고서)
- projectionKind 분포:
  - `coarse_chapter`: 7,684
  - `exact`: 3,936

해석:
- boundary, hierarchy, semantic unit, table meta를 하나의 Polars DataFrame prototype으로 통합하는 것이 실제로 가능함이 확인되었다.
- 현재는 exact보다 coarse_chapter가 더 많으므로, 다음 단계는 coarse를 fine boundary 아래로 더 잘 투영하는 규칙을 강화하는 것이다.

## 11. 현재 최종 판단

- 네가 말한 방식, 즉 **섹션별로 먼저 수평화하고 그 안을 계속 세부적으로 나누는 방식**이 가장 맞다.
- 그리고 이 방식은 Polars로 충분히 구현 가능한 수준까지 이미 실험으로 올라왔다.
- 이제 남은 건 방향 검증이 아니라, canonical map 규칙을 더 정교하게 만드는 엔지니어링 단계다.

### 018_integratedMapUpdater.py 완료

- 실행 파일: `experiments/056_sectionMap/018_integratedMapUpdater.py`
- 전체 최신 사업보고서 기준 스캔 기업 수: 229
- 전체 row 수: 8,557

핵심 결과:
- chapter별 high-confidence canonical candidate를 전체 기업에서 동시에 누적 생성 가능
- 후보 수:
  - I: 5
  - II: 7
  - III: 8
  - V: 2
  - VI: 3
  - VIII: 2
  - XI: 3
  - XII: 4

예시 커버리지:
- I장 `1. 회사의 개요`, `2. 회사의 연혁`, `5. 정관에 관한 사항` → 229/229
- II장 core 7개 → high-confidence 후보로 유지
- XII장 `1. 연결대상 종속회사 현황(상세)`, `2. 계열회사 현황(상세)`, `3. 타법인출자 현황(상세)` → 229/229

해석:
- 전체 parquet를 동시에 스캔해서 canonical map 후보를 누적 생성하는 updater 방식이 실제로 가능함이 확인되었다.
- 즉 056은 특정 회사 분석을 넘어서, 데이터가 누적될수록 canonical map이 더 정교해지는 구조로 갈 수 있다.

### 019_generateSectionMappingsDraft.py 완료

- 실행 파일: `experiments/056_sectionMap/019_generateSectionMappingsDraft.py`
- 후보 수: 34

핵심 결과:
- chapter별 high-confidence canonical candidate를 `normalizedTitle -> topicId` 초안으로 변환 가능
- 예:
  - `5. 정관에 관한 사항 -> articlesOfIncorporation`
  - `4. 주식의 총수 등 -> shareCapital`
  - `3. 제재 등과 관련된 사항 -> sanction`
  - `1. 연결대상 종속회사 현황(상세) -> subsidiariesDetail`

추가 관찰:
- 일부 항목은 아직 한글 topicId로 남는다 (`회사의개요`, `회사의연혁`, `자본금변동사항`).
- 즉 다음 단계에서 title -> stable english topicId 사전을 더 보강하면 sectionMappings 초안을 실제 프로덕션 데이터로 발전시킬 수 있다.

### 020_finalizeTopicIds.py 완료

- 실행 파일: `experiments/056_sectionMap/020_finalizeTopicIds.py`
- canonical 후보 34개에 대해 stable english topicId 세트 정리 완료

핵심 결과:
- `companyOverview`, `companyHistory`, `capitalChange`, `shareCapital`
- `businessOverview`, `productService`, `rawMaterial`, `salesOrder`, `riskDerivative`
- `audit`, `internalControl`, `boardOfDirectors`, `shareholderMeeting`
- `subsequentEvents`, `subsidiaryDetail`, `affiliateGroupDetail`, `investmentInOtherDetail` 등

해석:
- 이제 high-confidence canonical 후보는 대부분 stable english topicId로 고정 가능하다.

### 021_buildSectionMappingsJsonDraft.py 완료

- 실행 파일: `experiments/056_sectionMap/021_buildSectionMappingsJsonDraft.py`
- JSON draft mapping 수: 34

해석:
- `normalizedTitle -> topicId` 형태의 실제 `sectionMappings.json` 초안 직렬화가 가능함을 확인했다.
- 056은 이 시점부터 실험이 아니라 draft data generation 단계로 넘어갈 수 있다.

### 022_compareOldSectionsVsCanonical.py 완료

- 실행 파일: `experiments/056_sectionMap/022_compareOldSectionsVsCanonical.py`
- 기존 `sections('005930')` topic 수: 329
- canonical prototype row 수: 11,620
- canonicalSection 수: 42
- semanticUnit 수: 1,344

해석:
- 기존 sections는 leaf title 329개 수준의 거친 수평화다.
- canonical prototype은 row 수는 늘어나지만, canonicalSection 축은 42개로 안정화되고 그 아래 semanticUnit 1,344개로 구조화된다.
- 즉 비교 축은 더 안정적이고, 정보 밀도는 더 높아진다.

### 023_writeActualSectionMappingsDraft.py 완료

- 실행 파일: `experiments/056_sectionMap/023_writeActualSectionMappingsDraft.py`
- 실제 draft 파일 생성 완료:
  - `experiments/056_sectionMap/output/sectionMappings.draft.json`
- mapping 수: 34
- raw coverage: 0.963

해석:
- canonical 후보는 실제 draft 파일로 안정적으로 저장 가능하다.
- 최신 사업보고서 raw title 기준으로도 96.3% 커버되므로, 지금 단계의 draft는 실질적인 출발점으로 쓸 수 있다.
- 다음 개선 포인트는 coverage 확대보다, 남은 3.7%의 예외 패턴을 어떤 규칙으로 흡수할지 정하는 것이다.

### 024_uncoveredTitles.py 완료

- 실행 파일: `experiments/056_sectionMap/024_uncoveredTitles.py`
- uncovered rows: 316
- uncovered unique titles: 109

예외 유형 분포:
- `genericMatter`: 135 rows / 7 titles
- `detailExpansion`: 70 rows / 59 titles
- `other`: 58 rows / 18 titles
- `statusVariant`: 38 rows / 18 titles
- `metricDetail`: 14 rows / 6 titles
- `expertConfirmation`: 1 row / 1 title

상위 예외:
- `1. 공시내용 진행 및 변경사항` (101개 기업)
- `2. 영업의 현황`
- `4. 연구개발실적(상세)`
- `4. 영업설비`
- `5. 재무건전성 등 기타 참고사항`

해석:
- 남은 3.7%는 랜덤 노이즈가 아니라 소수의 반복 유형으로 수렴한다.
- 다음 개선은 전면 재설계가 아니라, `공시내용 진행 및 변경사항`, `영업의 현황`, 상세표 확장류를 흡수하는 예외 규칙 몇 개를 추가하면 된다.

### 025_hardcodedExceptionCoverage.py 완료

- 실행 파일: `experiments/056_sectionMap/025_hardcodedExceptionCoverage.py`
- baseline coverage: 0.963
- hardcoded coverage: 0.980
- delta: +0.017
- 추가 하드코딩 예외 수: 7

해석:
- section 매핑도 account 매핑과 마찬가지로 `기본 정규화 + 하드코딩 예외` 조합이 효과적이다.
- 상위 예외 7개만 추가해도 raw coverage가 96.3% -> 98.0%로 상승했다.
- 따라서 다음 단계는 예외 패턴을 더 확장하기보다, 이 하드코딩 예외를 draft 파일에 실제로 병합하는 것이다.

### 026_finalizeSectionMappingsDraft.py 완료

- 실행 파일: `experiments/056_sectionMap/026_finalizeSectionMappingsDraft.py`
- 최종 draft 파일 생성 완료:
  - `experiments/056_sectionMap/output/sectionMappings.final.draft.json`
- final mapping 수: 41
- final raw coverage: 0.980

해석:
- 056 실험은 이제 실제로 사용할 수 있는 `sectionMappings` 최종 초안 파일까지 도달했다.
- coverage 98.0% 수준이면 다음 단계는 추가 실험보다, 이 draft를 실제 엔진 spike에 연결해보는 작업이 더 가치 있다.

### engine spike 연결 확인

- production spike 파일 추가:
  - `src/dartlab/engines/dart/docs/sections/mapper.py`
  - `src/dartlab/engines/dart/docs/sections/mapperData/sectionMappings.json`
- `pipeline.py`에서 leaf title -> mapped topic 적용

검증:
- `sections('005930')` 실행 시간: 약 3.3초
- shape: `(324, 106)`
- canonical topic 확인:
  - `companyOverview`
  - `companyHistory`
  - `businessOverview`
  - `salesOrder`
  - `riskDerivative`
  - `audit`
  - `shareholderMeeting`
  - `subsequentEvents`
  - `subsidiaryDetail`

해석:
- 최종 draft 매핑이 실제 sections 엔진 spike에 연결되었고, canonical topic이 실데이터에서 바로 출력되기 시작했다.

### 027_validateMappedSections.py 완료

- 실행 파일: `experiments/056_sectionMap/027_validateMappedSections.py`

올바른 비교 기준:
- raw `section_title`가 아니라, 실제 `sections()`가 사용하는 `chunk leaf path` 기준으로 비교

결과:
- raw topic 수: 210
- mapped topic 수: 206
- reduction rate: 0.019
- canonical topic 수: 21

해석:
- 현재 매핑은 삼성전자 기준 chunk leaf topic을 210 -> 206으로 소폭 압축했다.
- 그러나 중요한 건 단순 개수 감소보다, `businessOverview`, `salesOrder`, `riskDerivative`, `audit`, `shareholderMeeting` 같은 canonical topic이 실제로 생성되기 시작했다는 점이다.
- 즉 1차 매핑은 성공했지만, 아직 세부 leaf 예외를 더 흡수해야 topic 축 압축 효과가 크게 나타난다.

### 실제 JSON 누적 반영

- 파일: `src/dartlab/engines/dart/docs/sections/mapperData/sectionMappings.json`
- 추가 반영 예외:
  - `3. 파생상품거래 현황 -> riskDerivative`
  - `예측정보에 대한 주의사항 -> cautionaryStatement`
  - `개요 -> mdnaOverview`
  - `재무상태 및 영업실적 -> financialConditionAndResults`
  - `유동성 및 자금조달과 지출 -> liquidityAndCapitalResources`
  - `그 밖에 투자의사결정에 필요한 사항 -> otherInvestmentDecisionMatters`
  - `【 대표이사 등의 확인 】 -> ceoConfirmation`

재검증 결과:
- 최신 사업보고서 전체 기준 coverage: `0.990`
- uncovered rows: `85`
- uncovered unique normalized titles: `77`

남은 예외 특성:
- 대부분 XII장 company-specific 상세표 (`지적재산권`, `수주상황`, `주유소 부동산 세부내역` 등)
- 즉 공통 섹션보다 회사 특화 detailed appendix에 수렴한다.

### 028_clusterRemainingTitles.py 완료

- 실행 파일: `experiments/056_sectionMap/028_clusterRemainingTitles.py`
- rows: `85`
- uniqueTitles: `77`

패턴 군집화 결과:
- `appendixDetail`: 36
- `appendixIp`: 16
- `appendixOther`: 12
- `appendixOrder`: 10
- `appendixFacilities`: 6
- `other`: 5

해석:
- 현재 남은 미흡수 title은 대부분 XII장 appendix/detail 계열이다.
- 따라서 공통 sectionMappings는 거의 수렴했고, 이후 확장은 공통 section 추가보다 appendix/detail 계층 설계가 더 중요하다.

### 029_deploymentReadiness.py 완료

- 실행 파일: `experiments/056_sectionMap/029_deploymentReadiness.py`
- 대표 10개 기업에서 sections() 실행 검증 완료

결과:
- 10개 기업 모두 `status=ok`
- 평균 실행 시간: `1.387초`
- 평균 topic 수: `217.3`
- canonical hit 평균: `6.0 / 6.0`

해석:
- 현재 production spike는 대표 기업 묶음에서 에러 없이 동작한다.
- 핵심 canonical topic이 다기업에서 실제로 출력되므로, 공통 section 매핑은 실전 배치 준비 수준으로 볼 수 있다.

### 공백 제거 정규화 반영

- 파일: `src/dartlab/engines/dart/docs/sections/mapper.py`
- `normalizeSectionTitle()`에서 section title 공백을 단일화가 아니라 **전부 제거**하도록 수정

재검증:
- 최신 사업보고서 전체 기준 coverage: `0.990` (유지)
- uncovered rows: `85`
- uncovered unique normalized titles: `75`
- 대표 10개 기업 평균 topic 수: `217.3 -> 209.3`

해석:
- 커버리지 수치는 같지만, 공백 흔들림이 있던 title들이 더 잘 합쳐져 topic 축이 실제로 줄었다.
- 즉 section title 정규화에서는 공백 제거가 더 적절하다.

### 030_similaritySuggestions.py 완료

- 실행 파일: `experiments/056_sectionMap/030_similaritySuggestions.py`

핵심 관찰:
- 일부 미흡수 title은 기존 key와 유사도가 충분히 높아 추천 후보로 활용 가능
  - `매출및수주상황(상세) -> 매출및수주상황 (0.778)`
  - `연구개발실적 -> 연구개발실적(상세) (0.750)`
  - `신용파생상품거래현황(상세) -> 파생상품거래현황 (0.727)`
  - `연구개발담당조직(상세) -> 연구개발실적(상세) (0.727)`

해석:
- similarity는 자동 확정 규칙으로 쓰기보다, 수동 검토용 추천 계층으로 사용하는 것이 적절하다.
- 공통 section 정규화 + 하드코딩 예외로 대부분 흡수하고, 남은 예외는 similarity 추천을 보고 sectionMappings에 누적하는 흐름이 적합하다.

### 031_finalOperationalValidation.py 완료

- 실행 파일: `experiments/056_sectionMap/031_finalOperationalValidation.py`

최종 운영 판정 수치:
- coverage: `0.990`
- uncovered rows: `85`
- uncovered unique titles: `75`
- appendix/detail 비중: `0.976`
- 대표 10개 기업 평균 실행 시간: `1.240초`
- 대표 10개 기업 성공률: `1.000`
- 평균 canonical hit: `6.000 / 6`

최종 결론:
- 공통 section mapping은 **운영 가능한 수준**으로 판단한다.
- 남은 미흡수의 97.6%가 appendix/detail 계열이므로, 현재 공통 section map의 주된 리스크는 core section 누락이 아니다.
- 따라서 공통 section map은 현재 상태로 운영 가능하며, 이후 개선은 appendix/detail 계층 설계와 예외 누적 중심으로 진행한다.

## 13. 최종 로직

1. 전체 `docs parquet`를 동시에 보고 공통 section boundary를 추출한다.
2. `sectionMappings.json`에 **기본 정규화 + 하드코딩 예외** 방식으로 누적한다.
3. 공백은 제거하여 정규화한다.
4. similarity는 자동 확정이 아니라 **추천용 보조 계층**으로만 사용한다.
5. 남은 회사 특화 상세표는 공통 section에 무리하게 넣지 않고 appendix/detail 계층으로 분리한다.
6. production `sections()`는 이 매핑을 사용해 canonical topic을 바로 출력한다.

## 14. 운영 상태

- `src/dartlab/engines/dart/docs/sections/mapperData/sectionMappings.json`은 실제 누적 파일로 운영한다.
- 공통 section map은 실전 배치 가능 상태로 본다.
- 이후 실험은 공통 section 재설계가 아니라 appendix/detail 계층 개선에 집중한다.

## 15. sectionMap 운영 원칙 (중요)

- `sectionMappings.json`은 이제 **실제 누적 파일**로 취급한다.
- 누적 위치:
  - `src/dartlab/engines/dart/docs/sections/mapperData/sectionMappings.json`
- 운영 방식:
  1. 전체 parquet 기준으로 규칙/예외를 실험에서 검증한다.
  2. 검증된 결과만 `sectionMappings.json`에 누적한다.
  3. 실험 완료 전까지는 production 활용 확대보다 mapping 품질 개선을 우선한다.

- 핵심 원칙:
  - 공통 section은 `기본 정규화 + 하드코딩 예외` 조합으로 흡수한다.
  - 남은 회사 특화 detailed appendix는 공통 section에 무리하게 넣기보다 appendix/detail 계층으로 별도 관리한다.
  - account mapping처럼 데이터가 누적될수록 `sectionMappings.json`도 계속 진화하는 학습형 매핑으로 본다.

## 16. 실험 운영 원칙 변경

- 여기까지의 실험은 가능성 검증용으로 세분화해서 빠르게 확인했다.
- 그러나 이후 단계는 너무 잘게 쪼개지 않고, **필요한 축을 묶은 단일 통합 실험**으로 진행한다.
- 즉 다음 실험은 `boundary + hierarchy + semantic unit + table meta + projection refinement`를 한 번에 검증하는 방향으로 간다.

### 다음 단일 실험

`018_integratedEngineDraft.py`

목표:
- 현재까지 검증된 규칙을 하나의 prototype 함수/파이프라인으로 합친다.
- 입력: docs parquet 1종목 전 기간
- 출력: canonical report map DataFrame
- 포함 요소:
  - canonicalSection
  - hierarchy projection
  - semanticUnit 추출
  - tableMeta 분리
  - coarse/fine 정렬 규칙

성공 기준:
- 삼성전자 전 기간을 하나의 canonical map으로 안정적으로 생성
- 기존 `sections('005930')`보다 수평 비교 품질이 개선된 예시를 최소 3개 확인

## 17. 다음 실험 제안

### 실험 009: industry-aware normalization
- II장 업종 접두사(`(금융업)`, `(제조서비스업)`)를 canonical boundary에 흡수하는 규칙 검증

### 실험 010: table-aware semantic units
- 표 전후 설명과 표 자체를 분리해 semanticUnit + tableMeta 구조로 저장하는 규칙 검증

### 실험 011: fine map projection score
- coarse 연도가 fine boundary map 위에 얼마나 안정적으로 투영되는지 정량 점수화

### 032_normalizationAblation.py 완료

- 실행 파일: `experiments/056_sectionMap/032_normalizationAblation.py`
- 최신 사업보고서 leaf rows: `8,557`
- mapping key 수: `59`

커버리지 비교:
- `raw`: `0.9808` (uncovered 164)
- `noSpace`: `0.9808` (uncovered 164)
- `noPrefix`: `0.9845` (uncovered 133)
- `noSpaceNoPrefix`: `0.9845` (uncovered 133)
- `noSpaceNoPrefixExt`: `0.9845` (uncovered 133)

해석:
- 공백 제거 단독은 커버리지 개선 효과가 없었다.
- leaf 번호 제거(`1.`, `가.`)는 실질적인 개선(+0.37%p)을 만들었다.
- `1)`, `(1)`까지 확장 제거는 현재 데이터셋에서 추가 개선이 없었다.

### 033_decadeGranularity.py 완료

- 실행 파일: `experiments/056_sectionMap/033_decadeGranularity.py`
- 전기간 인접연도 페어(빈 set 제외): `671`

decade별 세분화 강도:
- `2000s`: meanDelta `-1.289`, weightedFineOnlyRatio `0.094972`, pos/zero/neg=`9/12/17`
- `2010s`: meanDelta `-0.530`, weightedFineOnlyRatio `0.055147`, pos/zero/neg=`15/76/9`
- `2020s`: meanDelta `2.201`, weightedFineOnlyRatio `0.106890`, pos/zero/neg=`208/257/68`

해석:
- 세분화 증가는 2020년대에서 가장 강하게 나타났다.
- 2000/2010년대는 양식 개편 구간 영향으로 증가/유지/감소가 혼재했다.
- 운영 기준에서는 2020년대 fine boundary를 기본 축으로 두고, 구연도는 projection으로 흡수하는 전략이 유효하다.

### 034_horizontalizationEvaluation.py 완료

- 실행 파일: `experiments/056_sectionMap/034_horizontalizationEvaluation.py`
- 목적:
  - section map의 목표를 단순 title 매핑이 아니라, **회사/기간 간 수평 비교 가능한 canonical report profile 구축**으로 다시 명확히 정의했다.
  - 현재 매핑이 실제로 수평화를 개선하는지 전종목/단일종목 기준으로 재검증했다.

평가 기준:
- latest annual raw coverage
- annual 인접연도 pair의 raw topic Jaccard vs mapped topic Jaccard
- positive / zero / negative pair 분포
- 단일 종목 기간별 raw topic 수 vs mapped topic 수
- 실제 merge 사례 존재 여부

전종목 결과:
- latest annual coverage: `0.990`
- uncovered rows: `85`
- uncovered unique titles: `75`
- annual pair 수: `671`
- avg raw Jaccard: `0.718562`
- avg mapped Jaccard: `0.731263`
- avg delta: `0.012701`
- positive / zero / negative: `311 / 329 / 31`

삼성전자(005930) 상세:
- 기간 수: `106`
- avg raw Jaccard: `0.697390`
- avg mapped Jaccard: `0.706289`
- avg delta: `0.008900`
- positive / zero / negative: `27 / 75 / 3`
- 실제 merge 예시:
  - `디지털 미디어` + `디지털미디어` -> `디지털미디어`

해석:
- 현재 section map은 단순 표기 통일을 넘어서, 인접 기간의 topic overlap을 실제로 소폭 개선하고 있다.
- 큰 개선폭은 아직 아니지만, 악화 pair보다 개선 pair가 훨씬 많아 방향성은 맞다.
- 특히 현재 매핑의 본질은 "기존 section을 평면적으로 묶는 것"이 아니라,
  **모든 회사의 보고서를 하나의 비교 가능한 report profile 위에 정렬하는 작업**으로 해석하는 것이 정확하다.
- 따라서 이후 핵심 과제는 mapping 자체보다,
  큰 섹션 내부를 `canonicalSection -> canonicalSubsection -> semanticUnit` 계층으로 더 세분화해
  실제 비교 가능한 정보 단위까지 표준화하는 것이다.

### 035_globalMappingPolarsEval.py 완료

- 실행 파일: `experiments/056_sectionMap/035_globalMappingPolarsEval.py`
- 목적:
  - 전종목 mapping 상태 점검을 heavy stock loop가 아니라 **Polars lazy 전용 평가**로 분리했다.
  - mapping 생성/업데이트 단계에서 빠르게 coverage와 미매핑 분포를 확인할 수 있게 했다.

결과:
- latest annual leaf rows: `8,551`
- mapping key 수: `58`
- coverage: `0.990294`
- uncovered rows: `83`
- uncovered unique titles: `74`

chapter별 coverage:
- `I / II / III / IV / V / VI / VIII / XI` 모두 `1.0`
- 남은 미매핑은 사실상 `XII`에 집중
  - `XII` coverage: `0.924477`
  - uncovered rows: `83`

대표 uncovered:
- `주유소부동산세부내역(상세)`
- `지적재산권보유현황(상세)`
- `경영상의주요계약(상세)`
- `생산설비의현황(상세)`
- `수주상황(상세)`

해석:
- 공통 core section map은 거의 수렴했고, 남은 gap은 대부분 appendix/detail 계열이다.
- 따라서 전종목 mapping 갱신 루프는 이 스크립트를 기본 대시보드로 쓰는 것이 적절하다.

### 036_stockSemanticProfileView.py 완료

- 실행 파일: `experiments/056_sectionMap/036_stockSemanticProfileView.py`
- 목적:
  - 단일 종목 기준으로 period-level 수평화 상태와,
    그 다음 단계인 semantic unit 분해 결과를 한 번에 확인하는 뷰를 만들었다.

삼성전자(`005930`) 결과:
- period rows: `105`
- 2025 annual semantic profile에서 큰 section의 textChars / semanticUnits를 직접 확인 가능
- 예:
  - `사업부문별현황`: `textChars 13,233`, `semanticUnits 4`
  - `영업실적`: `5,004`, `2`
  - `주요재무위험관리`: `2,577`, `4`

해석:
- stock-level에서는 이제 "row 수가 줄었는가"만 볼 게 아니라,
  어떤 큰 section이 다음 단계 세분화 대상인지 바로 고를 수 있다.
- 즉 section map 다음 단계는 이미 분명하며,
  **큰 canonical section 내부를 semantic unit 축으로 표준화하는 작업**으로 넘어가면 된다.

### prefix 정규화 규칙 확장

- section 및 semantic unit 앞번호 제거 규칙을 확장했다.
- 적용 범위:
  - `1.`, `1)`, `(1)`
  - `가.`, `가)`
  - `①`
- 반영 위치:
  - `src/dartlab/engines/dart/docs/sections/mapper.py`
  - `src/dartlab/engines/dart/docs/sections/pipeline.py`
  - 관련 실험 스크립트

검증:
- `tests/test_sections_mapper.py` 통과 (`6 passed`)

해석:
- 큰 section과 내부 semantic unit 모두에서 앞번호/기호는 비교 축에 불필요한 noise다.
- 따라서 canonical report map 단계에서는 번호기호를 먼저 제거하는 것이 맞다.

### 037_riskDerivativeSemanticCanon.py 완료

- 실행 파일: `experiments/056_sectionMap/037_riskDerivativeSemanticCanon.py`
- 목적:
  - 공통 canonical section 하나를 골라 내부 semantic unit까지 stable id로 올릴 수 있는지 검증
  - section map 다음 단계인 `canonicalSection -> semanticUnit` 표준화 prototype 생성

결과:
- matched section rows: `216`
- companies: `216`
- semantic rows: `1,790`
- canonical hit ratio: `0.329050`
- canonical semantic id 수: `10`

대표 semantic ids:
- `marketRisk`: `114 rows / 101 companies`
- `creditRisk`: `109 / 105`
- `liquidityRisk`: `110 / 105`
- `capitalRisk`: `89 / 82`
- `interestRateRisk`: `61 / 58`
- `derivativesAndStructuredTrades`: `60 / 58`

삼성전자(`005930`) 예시:
- `재무위험관리정책` -> `riskManagementPolicy`
- `신용위험` -> `creditRisk`
- `유동성위험` -> `liquidityRisk`
- `자본위험` -> `capitalRisk`
- `파생상품 및 풋백옵션 등 거래 현황` -> `derivativesAndStructuredTrades`

남은 주요 unknown:
- `root`
- `금융위험관리`
- `위험관리`
- `외환위험`
- `자본관리`

해석:
- section map 다음 단계는 실제로 가능하며, `riskDerivative`는 semantic canonicalization의 첫 번째 프로덕션 후보로 볼 수 있다.
- 아직 hit ratio가 높지는 않지만, core risk profile 축은 이미 여러 회사에서 안정적으로 반복된다.
- 이후에는 topic별로 이런 semantic synonym을 누적해 canonical report profile을 더 깊게 구축하는 방식이 맞다.

### 038_scanHorizontalRetable.py 완료

- 실행 파일: `experiments/056_sectionMap/038_scanHorizontalRetable.py`
- 목적:
  - 전체 docs parquet를 `scan_parquet()`로 읽고, `company / period / canonical topic` 기준으로 직접 수평화하는 retable prototype 생성
  - 최신 annual fine topic을 teacher row로 삼아 과거 coarse period의 backfill 후보를 계산

구조:
- 입력: 전회사 전기간 docs parquet
- 변환:
  - `stockCode`
  - `period`
  - `chapter`
  - `normalizedTitle`
  - `canonicalTopic`
- 출력:
  - `topic x period` pivot
  - latest annual teacher topic
  - coarse-to-fine backfill candidate table

삼성전자(`005930`) 결과:
- latest annual teacher topic 수: `35`
- `topic x period` pivot 생성 확인
- backfill candidate 계산 확인

대표 backfill 후보:
- `shareholderMeeting`: `87 periods`
- `articlesOfIncorporation`: `85`
- `employee`: `81`
- `dividend`: `64`
- `fundraising`: `64`

해석:
- 056의 본체는 title 매핑 이후, **전기간 section을 period column 기준으로 다시 펴는 retable 엔진**임이 분명해졌다.
- 최신 annual의 fine topic이 teacher row가 되고, 과거/분기 coarse period는 같은 chapter text를 source로 삼아 채워 넣는 구조가 현실적이다.
- 따라서 이후 실험은 Jaccard 중심 검증보다, 이 retable 위에 semantic unit projection/backfill 규칙을 올리는 방향으로 가는 것이 맞다.

### 039_buildCanonicalRowTable.py 완료

- 실행 파일: `experiments/056_sectionMap/039_buildCanonicalRowTable.py`
- 목적:
  - 전회사 전기간 docs를 한 번 스캔해 canonical row 학습 테이블을 parquet로 저장

결과:
- output:
  - `experiments/056_sectionMap/output/canonicalRows.parquet`
- rows: `111,849`
- companies: `270`
- periods: `107`
- topics: `311`

해석:
- 이제 단일 종목 수평화는 원본 docs 전체를 다시 스캔하지 않고, 이 학습 테이블을 참조하는 구조로 갈 수 있다.

### 041_buildChapterSourceTable.py 완료

- 실행 파일: `experiments/056_sectionMap/041_buildChapterSourceTable.py`
- 목적:
  - coarse-to-fine backfill을 위해 period별 chapter 원문 source 테이블을 별도로 저장

결과:
- output:
  - `experiments/056_sectionMap/output/chapterSources.parquet`
- rows: `29,571`
- companies: `270`
- periods: `107`
- chapters: `13`

해석:
- canonical row 테이블과 chapter source 테이블을 분리해 두는 방식이 빠른 운영 구조에 더 적합하다.

### 040_fastHorizontalizeFromTable.py 완료

- 실행 파일: `experiments/056_sectionMap/040_fastHorizontalizeFromTable.py`
- 목적:
  - 학습 테이블만 읽어 단일 종목 `topic x period` 수평화를 빠르게 생성

삼성전자(`005930`) 결과:
- row 수: `3,018`
- latest annual teacher topic 수: `35`
- `topic x period` pivot 즉시 생성 확인

해석:
- 운영 경로는 이제 분명하다.
  - 학습 테이블 생성
  - 단일 종목은 학습 테이블만 읽어 즉시 수평화

### 042_chapterIIProjection.py 완료

- 실행 파일: `experiments/056_sectionMap/042_chapterIIProjection.py`
- 목적:
  - chapter II의 구연도 coarse topic을 최신 fine topic 축으로 projection

사용한 coarse -> fine 규칙:
- `주요제품및원재료등` -> `productService`, `rawMaterial`
- `매출에관한사항` -> `salesOrder`
- `연구개발활동` -> `majorContractsAndRnd`
- `기타투자의사결정에필요한사항` -> `riskDerivative`, `otherReference`

삼성전자(`005930`) 결과:
- chapter II rows: `449`
- teacher fine topics: `7`
- projection recovered periods:
  - `majorContractsAndRnd`: `38`
  - `otherReference`: `38`
  - `productService`: `38`
  - `rawMaterial`: `38`
  - `riskDerivative`: `38`
  - `salesOrder`: `38`
  - `businessOverview`: `0`

해석:
- 첫 번째 실질 projection 규칙이 실제로 fine topic 빈 칸을 채우기 시작했다.
- 즉 056의 핵심은 mapping 이후, **coarse topic을 fine topic으로 내려 꽂는 projection rule을 누적하는 것**이다.
- 다음 단계는 chapter II의 coarse row를 통째로 복사하는 수준을 넘어서, 내부 semantic unit를 분해해 fine topic에 더 정밀하게 배정하는 것이다.

### 044_buildProfileTable.py 완료

- 실행 파일: `experiments/056_sectionMap/044_buildProfileTable.py`
- 목적:
  - 전회사 전기간 section row의 구조/텍스트 특징을 한 테이블에 모아 학습용 profiler table 생성

결과:
- output:
  - `experiments/056_sectionMap/output/sectionProfileTable.parquet`
- rows: `116,505`
- companies: `270`
- periods: `107`
- topics: `311`

포함 특징:
- `textChars`
- `tableLineCount`
- `headingCount`
- `hasMajorHeading`
- `hasMinorHeading`
- keyword flags:
  - `kwProduct`
  - `kwRawMaterial`
  - `kwSales`
  - `kwRnd`
  - `kwRisk`
  - `kwFunding`

해석:
- 이제 projection rule과 semantic rule 탐색은 원본 parquet 직접 탐색보다, profiler table 위에서 수행하는 구조로 전환 가능하다.

### 045_projectionCandidates.py 완료

- 실행 파일: `experiments/056_sectionMap/045_projectionCandidates.py`
- 목적:
  - profiler table 기반으로 coarse topic -> fine topic projection 후보를 자동 추출

삼성전자(`005930`) chapter II 후보 예시:
- `경영상의주요계약등` -> `majorContractsAndRnd`
- `파생상품등에관한사항` -> `riskDerivative` 후보 포함

해석:
- profiler table을 기반으로 projection 후보를 자동 추천받고,
  고신뢰 후보만 rule table에 반영하는 방식이 현실적이다.
- 즉 앞으로의 워크플로우는
  1. profiler table 생성
  2. candidate 추출
  3. 검증된 projection rule 누적
  4. fast horizontalize에서 즉시 반영
  형태로 고정하는 것이 맞다.

### 2026-03-12 레거시 sectionMappings 확장

- 목적:
  - semantic projection 전에, exact title로 흡수 가능한 레거시 한국어 section title을 먼저 canonical topic으로 편입
  - `canonicalRows.parquet`와 `sectionProfileTable.parquet`의 topic cardinality를 줄여 학습/운영 속도를 개선

추가한 mapping 예시:
- `배당에관한사항등` -> `dividend`
- `자본금변동상황` / `자본금변동사황` -> `capitalChange`
- `회사의목적` -> `articlesOfIncorporation`
- `임원및직원의현황` -> `employee`
- `우발채무등` -> `contingentLiability`
- `결산일이후에발생한중요사항` -> `subsequentEvents`
- `제재현황` -> `sanction`
- `신고및공시사항요약` -> `disclosureChanges`
- `계열회사등의현황` -> `affiliateGroup`
- `최대주주등과의거래내용` -> `relatedPartyTx`
- `주주(최대주주등제외),임원,직원및기타이해관계자와의거래내용` -> `relatedPartyTx`

검증:
- `tests/test_sections_mapper.py`: `7 passed`

재학습 결과:
- `canonicalRows.parquet`
  - rows: `111,704`
  - companies: `270`
  - periods: `107`
  - topics: `300`
- `sectionProfileTable.parquet`
  - rows: `116,505`
  - companies: `270`
  - periods: `107`
  - topics: `300`

해석:
- 고정형 레거시 title을 먼저 mapper로 흡수하니, learned table의 topic 수가 `311 -> 300`으로 줄었다.
- 이 단계는 projection rule이 처리할 대상을 “진짜 coarse/fine 문제”로 좁혀 주기 때문에 필수다.

### 2026-03-12 fast horizontalize recovered 집계 수정

- 대상 파일:
  - `experiments/056_sectionMap/040_fastHorizontalizeFromTable.py`

수정 내용:
- `projected_backfill_summary()`의 recovered 계산을 `bool sum` 방식에서
  `teacher_grid anti observed -> inner projected` 방식으로 변경
- 목적:
  - 실제 projection row가 존재하는데도 `recoveredPeriods=0`으로 보이던 집계 오류 제거

삼성전자(`005930`) 확인 결과:
- chapter II projected summary
  - `majorContractsAndRnd`: observed `18`, recovered `38`
  - `productService`: observed `18`, recovered `38`
  - `rawMaterial`: observed `18`, recovered `38`
  - `salesOrder`: observed `18`, recovered `38`
  - `riskDerivative`: observed `18`, recovered `28`
  - `businessOverview`: observed `55`, recovered `0`
  - `otherReference`: observed `18`, recovered `0`

해석:
- projection row는 실제로 fine topic 빈 칸을 채우고 있었고, 문제는 집계 로직이었다.
- 이제 `fast horizontalize`에서 “학습 테이블 기반 즉시 수평화 + recovered cell 수치 확인”이 가능해졌다.

### 2026-03-12 현재 상태 요약

- latest annual global mapping coverage:
  - rows: `8,551`
  - mapping keys: `71`
  - coverage: `0.990294`
- chapter coverage:
  - `I`, `II`, `III`, `IV`, `V`, `VI`, `VIII`, `XI`는 `1.0`
  - uncovered는 대부분 `XII` appendix/detail에 집중

현재 남은 주요 레거시:
- `I`: `의결권현황`
- `VI`: `주식사무`, `최근6개월간의주가및주식거래실적`, `주식의분포`, `주주의분포`
- `VIII`: `주주총회의사록요약`
- `XI/XII`: appendix/detail 성격 title

다음 단계:
- 고정형으로 흡수 가능한 레거시는 mapper에 추가
- 큰 chapter coarse row는 projection rule로 확장
- semantic split이 필요한 큰 section은 별도 canonicalSubsection/semanticUnit 규칙으로 분해

### 2026-03-12 production package 반영

- 반영 파일:
  - `src/dartlab/engines/dart/docs/sections/artifacts.py`
  - `src/dartlab/engines/dart/docs/sections/runtime.py`
  - `src/dartlab/engines/dart/docs/sections/profileData/projectionRules.chapterII.json`
  - `src/dartlab/engines/dart/docs/sections/profileData/sectionProfileTable.parquet`
  - `src/dartlab/engines/dart/docs/sections/pipeline.py`

핵심 변경:
- `Company.sections()`가 사용하는 production pipeline에 learned-rule runtime을 연결했다.
- 실험 산출물 전체를 runtime에 그대로 싣지 않고, 실제 즉시 수평화에 필요한 compact artifact만 패키지 data로 포함했다.
- 포함 artifact:
  - `projectionRules.chapterII.json`
  - `sectionProfileTable.parquet`

production 동작:
1. 현재 종목 docs parquet를 읽는다.
2. chunk 기반으로 `(chapter, topic, text)` row를 만든다.
3. latest annual을 teacher로 사용해 fine topic 축을 잡는다.
4. chapter II coarse topic을 learned projection rule로 fine topic에 backfill한다.
5. direct projection source topic은 최종 output row에서 숨긴다.

반영된 projection:
- `매출에관한사항` -> `salesOrder`
- `연구개발활동` -> `majorContractsAndRnd`
- `경영상의주요계약등` -> `majorContractsAndRnd`
- `파생상품등에관한사항` -> `riskDerivative`
- `주요제품및원재료등` -> heading 기반 `productService` / `rawMaterial` 분해 + fallback

패키지 설정:
- `pyproject.toml`에 hatch build include를 추가해 `json/parquet` package data를 wheel/sdist에 포함하도록 설정

검증:
- `tests/test_sections_mapper.py`
- `tests/test_sections_runtime.py`
- 합계 `10 passed`

사용자 진입점 확인:
- `Company('005930').sections` 정상 반환
- 반환 shape: `(296, 106)`
- chapter II canonical fine topic 확인:
  - `salesOrder`: `56` periods
  - `majorContractsAndRnd`: `33` periods
  - `riskDerivative`: `46` periods

해석:
- 056 실험 결과가 이제 production `sections` path에 실제로 들어갔다.
- 아직 모든 legacy/coarse section이 흡수된 것은 아니지만,
  “학습된 rule을 패키지에 싣고 보고서 읽을 때 즉시 수평화”하는 기본 골격은 production화되었다.

### 2026-03-12 package build / 추가 legacy 흡수 확인

빌드 검증:
- `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m build --no-isolation`
  - `dartlab-0.4.0.tar.gz`
  - `dartlab-0.4.0-py3-none-any.whl`
  - 정상 생성 확인
- wheel/sdist 내부에 아래 package data 포함 확인
  - `docs/sections/mapperData/sectionMappings.json`
  - `docs/sections/profileData/projectionRules.chapterII.json`
  - `docs/sections/profileData/sectionProfileTable.parquet`

추가 exact mapping:
- `임원의현황` -> `employee`
- `직원의현황` -> `employee`
- `노동조합의현황` -> `employee`
- `주주총회의사록요약` -> `shareholderMeeting`
- `전문가와의이해관계` -> `expertConfirmation`
- `의결권현황` -> `shareCapital`
- `주식의분포` -> `shareCapital`
- `주주의분포` -> `shareCapital`

재확인:
- `Company('005930').sections`
  - `shareCapital`: `71` periods
  - `shareholderMeeting`: `102` periods
  - `salesOrder`: `56` periods
  - `majorContractsAndRnd`: `33` periods
  - `riskDerivative`: `46` periods

해석:
- package 배포 자체는 더 이상 막힌 상태가 아니다.
- 이제 남은 일은 빌드/배포 인프라보다, 잔여 legacy title과 coarse section을 얼마나 더 canonical 축으로 흡수하느냐이다.

### 2026-03-12 leaf legacy 추가 흡수 + wheel smoke

추가 exact mapping:
- `매출실적` -> `salesOrder`
- `수주상황` -> `salesOrder`
- `판매경로 등` -> `salesOrder`
- `판매방법 및 조건` -> `salesOrder`
- `판매전략` -> `salesOrder`
- `생산능력, 생산실적, 가동률` -> `rawMaterial`
- `연구개발실적` -> `majorContractsAndRnd`

삼성전자(`005930`) 재확인:
- `salesOrder`: `105` periods
- `majorContractsAndRnd`: `82` periods
- `rawMaterial`: `68` periods
- raw leaf row 제거 확인:
  - `매출실적` -> 없음
  - `수주상황` -> 없음
  - `연구개발실적` -> 없음
  - `판매경로등` -> 없음
  - `판매방법및조건` -> 없음
  - `판매전략` -> 없음

wheel smoke:
- wheel을 `/tmp/dartlab-wheel-unpack`에 풀고 `src` 경로를 제거한 상태에서 `import dartlab` 성공
- 즉 package 자체 import와 packaged sections data 접근은 정상
- fresh env 실행 시 막힌 지점은 코드가 아니라 네트워크/bootstrap
  - `Company('005930')` -> KRX KIND 종목명 조회 네트워크 필요
  - `sections('005930')` -> 로컬 docs parquet가 없으면 GitHub Release 다운로드 필요

해석:
- package 품질 관점에서 현재 남은 실전 배치 이슈는 `sections runtime` 자체보다, fresh 환경의 외부 데이터 bootstrap 경로다.
- canonical map 품질은 계속 개선 중이고, 특히 sales/rnd/rawMaterial 축의 leaf legacy는 의미 있는 수준으로 정리됐다.

### 2026-03-12 세분화 canonical row 추가 확장

추가 exact mapping:
- `지적재산권관련` -> `intellectualProperty`
- `환경관련규제사항` -> `environmentRegulation`
- `사업부문별현황` -> `segmentOverview`
- `사업부문별요약재무현황` -> `segmentFinancialSummary`
- `주요제품등의가격변동현황` / `주요제품등의가격변동추이` -> `productPriceTrend`
- `주요원재료등의가격변동추이` -> `rawMaterialPriceTrend`
- `투표제도` -> `shareholderMeeting`
- `이사회구성개요` / `이사회내의위원회` / `이사의독립성` -> `boardOfDirectors`
- `감사위원회교육실시계획` / `감사위원회위원의인적사항및사외이사여부` / `감사위원회위원의독립성` / `감사위원회주요활동내역` -> `auditSystem`
- `회사의법적,상업적명칭` / `본사의주소,전화번호및홈페이지` -> `companyOverview`
- `연구개발조직및운영` -> `majorContractsAndRnd`

삼성전자(`005930`) 핵심 row 재확인:
- `salesOrder`: `105`
- `majorContractsAndRnd`: `82`
- `rawMaterial`: `68`
- `productPriceTrend`: `68`
- `intellectualProperty`: `66`
- `environmentRegulation`: `66`
- `segmentOverview`: `66`
- `segmentFinancialSummary`: `66`
- `boardOfDirectors`: `67`
- `auditSystem`: `102`
- `shareholderMeeting`: `102`

전종목 latest annual 점검:
- mapping keys: `94`
- coverage: `0.99041`
- uncovered는 실질적으로 `XII` detail/appendix에 집중

현재 삼성전자 잔여 top raw row:
- `중소기업해당여부`
- `신용평가에관한사항`
- `소수주주권`
- `경영권경쟁`
- `계열회사에관한사항`

해석:
- core section horizontalization은 상당수 정리됐고, 이제 잔여 row는 점점 회사 프로파일/지배구조 세부사항 쪽으로 이동했다.
- 다음 단계는 broad section 정리가 아니라, 남은 governance/profile 세부 row를 새 canonical topic으로 승격할지, 기존 축에 흡수할지 판단하는 작업이다.

### 2026-03-12 core canonicalization 추가 압축

추가 exact mapping:
- 회사/프로필:
  - `회사의현황` / `신규사업에관한내용` -> `companyOverview`
  - `조직개편` -> `companyHistory`
  - `기업집단및소속회사의명칭` -> `affiliateGroup`
- 위험/리스크:
  - `시장위험` -> `marketRisk`
  - `신용위험` -> `creditRisk`
  - `유동성위험` -> `liquidityRisk`
  - `자본위험관리` -> `capitalRisk`
  - `환율변동영향` / `환위험관리대책` / `재무위험관리정책` / `주요재무위험관리` / `공정가치측정` / `리스크관리에관한사항` / `파생상품` / `파생상품계약체결현황` / `파생상품및풋백옵션등거래현황` / `파생상품및위험관리정책에관한사항` -> `riskDerivative`
- 감사/제재:
  - `회계감사인의감사의견등` / `회계감사인의변경` / `감사인(공인회계사)의감사의견등` / `감사의견` / `감사절차요약` / `당해사업연도의감사절차요약` / `당해사업연도의분기감사(또는검토)절차요약` / `연결재무제표에대한감사인의감사의견등` -> `audit`
  - `당해사업연도감사(내부감사)의감사의견등` -> `auditSystem`
  - `한국거래소등으로부터받은제재현황` -> `sanction`
- 자금조달/배당/투자:
  - `최근3사업연도배당에관한사항` -> `dividend`
  - `공모자금사용내역` / `이익참가부사채에관한사항` -> `fundraising`
  - `타법인출자현황` -> `investmentInOtherDetail`
- 이사회/주주/정관:
  - `이사회제도에관한사항` / `기타이사회가필요하다고인정하는위원회` -> `boardOfDirectors`
  - `연결대상종속기업개황` -> `subsidiaryDetail`
  - `최대주주의개요` / `최대주주의최대주주의개요` / `회사의최대주주(그의증권거래법상특수관계인을포함한다)` / `최대주주의변동을초래할수있는특정거래` -> `majorHolder`
  - `자회사가영위하는목적사업` / `회사가영위하지아니하는목적사업` -> `articlesOfIncorporation`
- 사업/연구개발/환경:
  - `판매경로및판매방법등` -> `salesOrder`
  - `연구개발활동의개요` -> `majorContractsAndRnd`
  - `법규상의규제에관한사항` -> `environmentRegulation`
- 재무주석:
  - `범주별금융상품` / `유형자산` / `재무상태` / `금융부채` / `금융자산` / `중요한회계정책및추정에관한사항` -> `financialNotes`
- 기타:
  - `중요한소송사건등` -> `materialLitigation`
  - `견질또는담보용어음,수표현황` -> `pledgedNotesAndChecks`
  - `다양한종류의주식` -> `shareClassDiversity`
  - `영업실적` -> `businessStatus`

runtime 보강:
- `runtime.extractSemanticUnits()` 추가
- `segmentOverview`, `segmentFinancialSummary`, `riskDerivative`에 대해 major heading 기반 semantic unit 분리 훅 제공
- 기본 `sections()` 반환 형식은 그대로 `topic x period` DataFrame 유지

검증:
- `pytest tests/test_sections_mapper.py tests/test_sections_runtime.py -q` -> `11 passed`
- 삼성전자(`005930`) 재확인:
  - `audit`: `45`
  - `auditSystem`: `104`
  - `boardOfDirectors`: `102`
  - `companyHistory`: `105`
  - `companyOverview`: `104`
  - `dividend`: `73`
  - `executivePay`: `57`
  - `financialNotes`: `28`
  - `fundraising`: `16`
  - `investmentInOtherDetail`: `24`
  - `majorHolder`: `58`
  - `riskDerivative`: `89`
  - `sanction`: `18`
- 삼성전자 잔여 top raw는 이제 주로 semantic label 또는 appendix 성격:
  - 사업부문명: `반도체`, `정보통신`, `디지털미디어`, `생활가전`
  - 세부표/문장형: `유가증권매수또는매도내역`, `또한당사는환경안전관련법규준수를위해...`

전종목 latest annual 재확인:
- mapping keys: `188`
- coverage: `0.99041`
- chapter `I/II/III/IV/V/VI/VIII/XI`: `1.0`
- uncovered는 계속 `XII` detail/appendix에만 집중

해석:
- core canonical section map은 사실상 완료 단계다.
- 지금 남은 미정리 row는 broad section 문제가 아니라 `semantic unit` 또는 `appendix/detail` 문제다.
- 이후 고도화 포인트는 `segmentOverview` 하위 사업부문명과 `riskDerivative` 내부 세부 리스크 축을 semantic row로 내리는 일이다.

### 2026-03-12 package-ready view helper 승격 + 시계열 정렬 고정

패키지 helper 추가:
- `src/dartlab/engines/dart/docs/sections/views.py`
  - `periodSortKey`, `sortPeriods`
  - `buildMarkdownBlocks`, `buildMarkdownWide`
  - `retrievalBlocks`, `contextSlices`
  - `splitMarkdownBlocks`, `splitContextText`
- `src/dartlab/engines/dart/docs/sections/__init__.py`에서 아래 helper export
  - `retrievalBlocks`
  - `contextSlices`
  - `buildMarkdownBlocks`
  - `buildMarkdownWide`
  - `sortPeriods`

정렬 규칙:
- period 정렬은 모든 wide 결과물에서 동일하게 `최신순` 고정
- 같은 연도 내부 순서:
  - `YYYY`
  - `YYYYQ3`
  - `YYYYQ2`
  - `YYYYQ1`
- `pipeline.sections()`도 같은 규칙으로 반환 컬럼 정렬

실험 wrapper 정리:
- `046/047/048/049`는 중복 구현 제거
- 모두 package helper만 호출하는 얇은 CLI wrapper로 정리

semantic 확장:
- `runtime.semanticTopicForLabel()`에 segment/risk semantic key 추가
  - segment:
    - `segmentSemiconductor`
    - `segmentIct`
    - `segmentDigitalMedia`
    - `segmentHomeAppliance`
    - `segmentDisplay`
    - `segmentHarman`
    - `segmentOther`
  - risk:
    - `marketRisk`
    - `creditRisk`
    - `liquidityRisk`
    - `capitalRisk`
    - `fxRisk`
    - `interestRateRisk`
    - `fairValueRisk`
    - `derivativeExposure`

검증:
- `pytest tests/test_sections_mapper.py tests/test_sections_runtime.py -q` -> `14 passed`
- `046` 삼성전자(`005930`) preview 컬럼이 최신순으로 정렬됨
  - `2025`, `2025Q3`, `2025Q2`, `2025Q1`, `2024`, ...
- `048` semantic topic summary:
  - `derivativeExposure 72`
  - `marketRisk 52`
  - `capitalRisk 51`
  - `liquidityRisk 43`
  - `creditRisk 36`
- `049` context slice 생성 정상
  - shape: `159,332 x 11`

해석:
- 이제 `sections` 계열 산출물은 package helper 하나를 기준으로 일관된 정렬/분해 규칙을 공유한다.
- 사람용 preview, retrieval block, LLM용 context slice가 분리되었고, 같은 canonical/runtime 규칙 위에서 동작한다.
- 다음 고도화는 segment semantic row 흡수율을 높여 `반도체/정보통신/디지털미디어/생활가전` 같은 raw semantic label을 줄이는 일이다.

### 2026-03-12 semantic 잔여 추가 흡수 + retrieval 메타 보강

추가 exact mapping:
- segment semantic:
  - `반도체` -> `segmentSemiconductor`
  - `정보통신` -> `segmentIct`
  - `디지털미디어` -> `segmentDigitalMedia`
  - `생활가전` -> `segmentHomeAppliance`
- 투자/계열:
  - `유가증권매수또는매도내역` -> `investmentInOtherDetail`
  - `출자및출자지분처분내역` -> `investmentInOtherDetail`
  - `관계기업및자회사의지분현황` / `관계회사및자회사의지분현황` -> `affiliateGroupDetail`
- 배당/자금조달:
  - `최근5사업연도의배당에관한사항` -> `dividend`
  - `이익참가부사채` -> `fundraising`
- 감사/제재:
  - `결산감사` -> `audit`
  - `행정기관의제재현황` -> `sanction`

retrieval/context 메타 추가:
- `views.py`
  - `periodOrderValue`
  - `isBoilerplateTopic`
  - `blockPriority`
- `retrievalBlocks`
  - `periodOrder`
  - `isBoilerplate`
  - `blockPriority`
- `contextSlices`
  - `periodOrder`
  - `isBoilerplate`
  - `blockPriority`

검증:
- `pytest tests/test_sections_mapper.py tests/test_sections_runtime.py -q` -> `15 passed`
- 삼성전자(`005930`) `sections` shape:
  - 이전 `207`
  - 현재 `199`
- raw top에서 segment raw label 제거 확인:
  - `정보통신`, `디지털미디어`, `반도체`, `생활가전` 제거
- 현재 상위 raw는 semantic/detail 위주:
  - `환경및종업원등에관한사항`
  - `주식선택권의부여및행사현황`
  - `임원배상책임보험가입현황`
  - `참고사항`
  - `중간감사`
  - `자산손상인식`

해석:
- segment semantic row는 mapper 단계에서도 의미 있는 수준으로 흡수되기 시작했다.
- `sections()` raw 잔여는 이제 broad section보다 finer profile/note/detail 성격이 강하다.
- retrieval/context는 정렬과 우선순위 메타를 갖추었고, 다음 단계는 남은 semantic/detail raw를 계속 줄이는 일이다.

### 2026-03-12 broad legacy 2차 흡수 + 정규화 강화

정규화 강화:
- `mapper.normalizeSectionTitle()`
  - `·`를 `,`로 통일
  - 제목 끝의 `-`, `:`, `;`, `,` 같은 trailing punctuation 제거
- 효과:
  - `회사의법적·상업적명칭`
  - `유동성위험-`
  같은 변형 title을 exact mapping으로 더 잘 흡수

추가 exact mapping:
- 회사개요/연혁:
  - `본사의주소,전화번호,홈페이지주소`
  - `회사의본점소재지및그변경`
  - `설립일자및존속기간`
  - `상호의변경`
  - `합병등에관한사항`
  - `합병등을한경우그내용`
  - `합병등의사후정보`
- 계열/최대주주:
  - `기업집단의개요`
  - `계열회사의현황`
  - `계열회사등관리조직현황`
  - `최대주주상세`
  - `최대주주(법인또는단체)의기본정보`
  - `최대주주개요`
  - `최대주주의최대주주관련사항`
- 감사/내부통제:
  - `회계감사인과의비감사용역계약체결현황`
  - `감사용역체결현황`
  - `감사위원회의주요활동내역`
  - `감사위원회`
  - `내부통제유효성감사`
  - `내부통제`
- 위험/환경:
  - `회사의위험관리정책`
  - `위험관리관련추진사항`
  - `위험관리방식및조직`
  - `환경보호정책및현황`
  - `녹색경영현황`
  - `관련법령상규제내용`
- 영업/원재료/세그먼트:
  - `판매경로,방법및전략`
  - `판매경로및판매전략`
  - `주요원재료의매입처및원재료공급시장과공급의안정성`
  - `생산능력및생산능력의산출근거`
  - `생산설비의현황등`
  - `사업부문별재무정보`
  - `각사업부문별산업분석`
- 신규 canonical topic 승격:
  - `listingStatus`
  - `managementChange`
  - `shortSwingProfit`
  - `stockAdministration`
  - `stockPriceTrend`

검증:
- `pytest tests/test_sections_mapper.py tests/test_sections_runtime.py -q` -> `16 passed`
- 대표 종목군 raw 잔여 재점검:
  - 삼성전자 `005930`: `199 -> 144`
  - SK하이닉스 `000660`: `228 -> 197`
  - NAVER `035420`: `68 -> 48`
  - 현대차 `005380`: `88 -> 75`
  - LG화학 `051910`: `84 -> 61`
- 삼성전자 상위 raw 잔여:
  - `“가”호또는“나”호와유사한거래`
  - `자사주펀드`
  - `영업양수,도계약`
  - `특기사항요약`
  - `재고자산의실사내역등`
- 대표 종목군 공통으로 남는 건 이제 broad section보다는 문장형 예외, 특수 거래표, 상세 appendix 성격이 강함

해석:
- core section horizontalization은 production 품질에 거의 근접했고, broad legacy title은 대다수 canonical row로 흡수되었다.
- 현재 남은 raw는 회사 특화 문장형 라벨, 표 세부행, appendix/detail 조각이 중심이다.
- 다음 고도화는 exact mapping 확장보다 `semantic/detail projector`와 table-aware block 분해 정밀화가 더 중요하다.

### 2026-03-12 table-aware semantic 보강 + 반복 raw 추가 흡수

추가 구현:
- `runtime.py`
  - `semanticTopicForBlock()` 추가
  - markdown table의 첫 번째 셀 label을 읽어 semantic topic을 추론하는 `_tableLeadCells()` 추가
  - `audit`, `auditSystem`, `majorHolder`, `environmentRegulation`, `majorContractsAndRnd` block에 대해 label/body 기반 semantic fallback 추가
- `views.py`
  - `retrievalBlocks()`가 `semanticTopicForLabel()` 대신 `semanticTopicForBlock()` 사용
  - `splitMarkdownTable()` 추가
  - `contextSlices()`가 table block은 header-preserving chunk로 자르도록 변경

추가 exact mapping:
- 감사/내부통제:
  - `감사인`
  - `외부감사인과의비감사용역계약체결현황`
  - `당해사업연도의감사(검토)절차요약`
  - `당해사업연도의연결감사(검토)절차요약`
  - `교육실시계획`
  - `교육실시현황`
  - `감사위원회의인적사항`
  - `감사위원회에관한사항`
  - `내부통제구조의평가`
- 연구개발/환경/원재료:
  - `연구개발담당조직`
  - `배출권거래제관리업체지정`
  - `생산설비의현황`
- 세그먼트/지분/종속:
  - `디지털및생활가전`
  - `주식소유현황`
  - `외국지주회사의자회사현황`

검증:
- `pytest tests/test_sections_mapper.py tests/test_sections_runtime.py -q` -> `18 passed`
- 대표 종목군 raw 잔여 재점검:
  - 삼성전자 `005930`: `144 -> 141`
  - SK하이닉스 `000660`: `190 -> 189`
  - NAVER `035420`: `47` 유지
  - 현대차 `005380`: `75 -> 73`
  - LG화학 `051910`: `60 -> 57`
- 삼성전자 상위 raw 잔여:
  - `“가”호또는“나”호와유사한거래`
  - `영업양수,도계약`
  - `자사주펀드`
  - `전기말`
  - `매출채권관련대손충당금설정방침`
- retrieval semantic summary 예시:
  - 삼성전자 `auditSystem 816`, `audit 702`, `majorHolder 592`, `majorContractsAndRnd 192`
  - SK하이닉스 `majorHolder 1884`, `auditSystem 961`, `audit 867`

해석:
- broad raw는 거의 사라졌고, 남은 것은 특수 거래문구, 표 내부 세부항목, 회사 특화 문장형 제목이 중심이다.
- `retrievalBlocks/contextSlices`는 이제 text뿐 아니라 table block도 semantic topic을 붙이며 쪼갠다.
- 다음 완성 단계는 exact mapping을 더 늘리는 것보다, 남은 문장형/표세부를 semantic/detail projector로 흡수하는 쪽이 핵심이다.

### 2026-03-12 `sections()` 무손실 전환

핵심 변경:
- `pipeline.sections()`를 `chunkRows()` 기반 text-only 병합에서 raw section markdown 병합으로 전환
- 이제 `topic x period` wide cell은 `section_content` 원문 markdown를 그대로 보존한다
- chapter II projection은 유지하되, projection 대상 text도 원문 markdown 그대로 복제한다
- `chunker`는 여전히 retrieval/semantic 분해용으로 남아 있지만, `sections()` 생성 시 table markdown를 버리지 않는다

추가 구현:
- `runtime.semanticTopicForBlock()` 추가
  - heading label뿐 아니라 markdown table 첫 컬럼 label로 semantic topic 추론
- `views.splitMarkdownTable()` 추가
  - table slice를 header-preserving chunk로 분해
- `retrievalBlocks()`는 `semanticTopicForBlock()` 사용
- `contextSlices()`는 table block이면 `splitMarkdownTable()`로 분할

검증:
- 새 회귀 테스트 추가:
  - `tests/test_sections_pipeline.py`
  - `sections()`가 markdown table을 실제로 보존하는지 확인
- 전체 검증:
  - `pytest tests/test_sections_mapper.py tests/test_sections_runtime.py tests/test_sections_pipeline.py -q`
  - 결과: `19 passed`
- 삼성전자 `005930` 확인:
  - `sections` shape: `(96, 107)`
  - `salesOrder` cell 안에 markdown table 구분자 `|` 보존 확인
  - retrieval semantic summary는 유지:
    - `auditSystem 816`
    - `audit 702`
    - `majorHolder 592`
    - `majorContractsAndRnd 192`

해석:
- 이제 `sections()` 자체도 더 이상 “비교용 text-only 손실 view”가 아니다.
- wide view, retrieval blocks, context slices가 모두 같은 raw markdown를 공유하는 방향으로 정렬되었다.
- 남은 과제는 broad mapping이 아니라, raw 문장형/표 세부행을 semantic/detail projector로 더 내려서 information-preserving horizontalization을 완성하는 것이다.

### 2026-03-12 wide canonicalization 복구

추가 exact mapping:
- `financialNotes`
  - `회계정보에관한사항`
  - `유가증권명세서`
  - `주요채권명세서`
  - `사채명세서`
  - `장기차입금명세서`
  - `단기차입금명세서`
  - `주요채무명세서`
  - `예금등명세서`
- `disclosureChanges`
  - `주요경영사항신고내용의진행상황등`
  - `주요경영사항신고내용및그진행상황`
- `affiliateGroup`
  - `관계회사등의현황`
- `companyHistory`
  - `합병전,후의재무제표`
- `companyOverview`
  - `국내및해외주요사업장현황(상세)`

추가 suppression:
- `runtime.projectionSuppressedTopics()`
  - chapter II split source인 `주요제품및원재료등`도 최종 wide view에서 숨김

검증:
- `pytest tests/test_sections_mapper.py tests/test_sections_runtime.py tests/test_sections_pipeline.py -q`
  - 결과: `19 passed`
- 대표 종목군 raw 잔여 재점검:
  - 삼성전자 `005930`: `96 -> 82`
  - SK하이닉스 `000660`: `91 -> 81`
  - NAVER `035420`: raw 없음
  - 현대차 `005380`: raw 없음
  - LG화학 `051910`: raw 없음

현재 상단 raw 성격:
- 삼성전자 / SK하이닉스에 남는 것은
  - `재고자산명세서`
  - `감가상각비등명세서`
  - `제조원가명세서`
  - `법인세등명세서`
  - `감사인의보수등에관한사항`
  같은 appendix/detail 명세서 위주

해석:
- broad section raw는 사실상 정리되었다.
- 현재 남은 것은 반복되는 appendix/detail 명세서와 일부 역사적 특수 항목이며, core horizontalization 품질은 production 수준에 근접했다.
- 마지막 단계는 이 detail appendix를 별도 appendix layer로 정식 분리할지, `financialNotes/audit` 아래 detail semantic row로 더 내릴지 결정하고 마무리하는 것이다.

### 2026-03-12 package-ready detail/source trace 마감

추가 구현:
- `runtime.py`
  - `detailTopicForTopic()` 추가
  - appendix/detail 명세서를 detail semantic key로 분리
    - `noteInventoryDetail`
    - `noteDepreciationDetail`
    - `noteManufacturingCostDetail`
    - `noteTaxDetail`
    - `noteSecuritiesDetail`
    - `noteReceivablesDetail`
    - `noteDebtDetail`
    - `noteCashDetail`
    - `auditFeeDetail`
- `views.py`
  - `retrievalBlocks()`에 `sourceTopic`, `cellKey`, `detailTopic` 컬럼 추가
  - `contextSlices()`에도 동일 메타 추가
- `README.md`
  - `Company.sections`, `Company.retrievalBlocks`, `Company.contextSlices` 사용 예시 추가
- `pyproject.toml`
  - classifier `Development Status :: 4 - Beta`로 상향

검증:
- `pytest tests/test_sections_mapper.py tests/test_sections_runtime.py tests/test_sections_pipeline.py -q`
  - 결과: `19 passed`
- `python -m build --no-isolation`
  - 결과: `dartlab-0.4.3.tar.gz`, `dartlab-0.4.3-py3-none-any.whl`
- `retrievalBlocks/contextSlices` 실제 스키마 확인:
  - `topic`
  - `sourceTopic`
  - `cellKey`
  - `semanticTopic`
  - `detailTopic`

해석:
- 이제 package runtime은
  - `sections()` = canonical wide markdown view
  - `retrievalBlocks()` = 원문 block + source trace
  - `contextSlices()` = LLM slice + source trace
  구조로 닫혔다.
- per-stock 결과를 저장하지 않아도, packaged rules와 runtime DataFrame만으로 재현 가능한 상태가 되었다.

### 2026-03-12 package closing pass

추가 구현:
- `sections()` core wide view에서 appendix/detail row를 기본 숨김 처리
- `개별재무제표에관한사항`, `연결재무제표에관한사항` 도 detail semantic layer로 분리
- `장래계획에관한사항의추진실적`, `개별재무제표에대한감사인(공인회계사)의감사의견등`, `중간감사`, `컴퓨터2000년문제의해결과관련된사항` 등 반복 raw 잔여를 흡수
- README / pyproject / changelog 를 package-facing 기준으로 정리

결과:
- core wide view는 canonical comparison 축만 남기고, appendix/detail 은 `retrievalBlocks/contextSlices` 의 `detailTopic` 메타로 회수 가능
- broad raw residual은 appendix/detail 및 특수 역사 항목 수준으로 축소
- package 메타는 `Production/Stable` 기준으로 상향

### 2026-03-12 retrieval quality closing pass

추가 구현:
- `views.py`
  - `isPlaceholderBlock()` 추가
  - `retrievalBlocks()`에 `isPlaceholder` 메타 추가
  - `contextSlices()`는 boilerplate 및 non-semantic placeholder를 기본 제외
  - `blockPriority`는 `detailTopic > semanticTopic > text > heading > table` 순으로 재정렬
- `runtime.py`
  - `detailTopicForBlock()` 추가
  - `financialNotes`, `audit` 내부 block/table row label에서 detail semantic topic을 직접 추론

검증:
- `pytest tests/test_sections_mapper.py tests/test_sections_runtime.py tests/test_sections_pipeline.py -q`
  - 결과: `21 passed`
- 대표 종목군 `005930`, `000660`, `035420`, `005380`, `051910`
  - `sections()` raw residual count: 모두 `0`
- contextSlices 실측:
  - 삼성전자 `semantic_ratio 0.0575`, `placeholder_ratio 0.000049`
  - SK하이닉스 `semantic_ratio 0.0694`, `placeholder_ratio 0.0`

해석:
- core wide view는 유지한 채 AI 입력 품질이 올라갔다.
- 현재 기본 retrieval 경로는 placeholder 노이즈를 거의 제거하고 detail/note block을 우선 회수한다.

### 2026-03-12 docs 283개 기준 detail taxonomy 보강

배경:
- `eddmpython`에서 추가 반영된 docs 13개 신규 종목을 `data/dart/docs`로 동기화한 뒤 수평화 재점검
- 신규 problem stock:
  - `006800`
  - `010140`
  - `012450`
  - `086520`
  - `086790`
  - `247540`

추가 구현:
- `mapper.py`
  - 패턴형 제목 매핑 추가
  - 금융업 상세 업무 제목, 지적재산권 보유현황(company suffix), 연구개발실적(company suffix), 수주/계약 상세 제목을 broad canonical로 흡수
- `runtime.py`
  - `detailTopicForBlock()`에 금융업/지적재산권/수주/계약 detail taxonomy 추가
  - 예:
    - `bankDepositProductDetail`
    - `bankLoanProductDetail`
    - `trustBusinessDetail`
    - `financialProductOverviewDetail`
    - `bankServiceDetail`
    - `brokerageBusinessDetail`
    - `derivativeProductDetail`
    - `ipPortfolioDetail`
    - `orderBacklogDetail`
    - `majorContractDetail`
    - `rndPortfolioDetail`

검증:
- `pytest tests/test_sections_mapper.py tests/test_sections_runtime.py tests/test_sections_pipeline.py -q`
  - 결과: `21 passed`
- 신규 problem stock residual:
  - `006800`: `0`
  - `010140`: `0`
  - `012450`: `0`
  - `086520`: `0`
  - `086790`: `0`
  - `247540`: `0`

해석:
- docs 283개 기준으로 신규 추가 종목군까지 core `sections()` raw residual이 사실상 정리되었다.
- 남은 정보는 broad raw가 아니라 detail taxonomy에서 회수되는 구조로 닫혔다.
- 현재 package 수준 기준에서 `sections()`는 core canonical 비교축, `retrievalBlocks/contextSlices`는 detail/semantic evidence layer 역할이 명확히 분리되었다.
