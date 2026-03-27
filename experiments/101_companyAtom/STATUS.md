# 101. CompanyAtom — 공시 데이터 극단적 압축 + 추상화 공간

## 핵심 통찰

> **CompanyAtom ≠ 압축된 sections**
> **CompanyAtom = 변화의 지도 + 원본 복원 능력**

동일한 것을 제거하면 변화가 선명해진다. 변화분은 손실이 아니라 핵심 자산.

## 실험 결과 요약

### 001: 중복률 측정 ✅

| 지표 | 값 |
|------|-----|
| Null 셀 비율 | **87.3%** |
| 텍스트 중복률 | **73.9%** |
| CAS 압축률 | **48.3%** (97MB → 50MB) |

### 002: Delta 압축 ✅ (장시간 실행)

- Delta 압축률 56.3% (원본 45MB → 20MB)
- 양극화 패턴: "거의 동일(43%)" 또는 "완전히 다름(24%)" — 중간이 얇음
- 3단 압축 시뮬레이션: 원본 97MB → CAS 50MB → Delta ~36MB → **총 62.9% 압축**

### 003: 메타 분리 + Atom 프로토타입 ✅

- Essential 메타 5개(0.33MB)면 충분. Optional 10개(4.78MB)는 전체 메타의 78%.
- Atom(CAS+Index) = 53MB (원본 97MB 대비 **45% 절감**)

### 004: Delta를 자산으로 ✅ (핵심 실험)

- 22,060 변화 블록: 사라짐 34% / 등장 31% / 문구 21% / 구조 11% / 숫자 3%
- **전체의 23.2%에 기업 변화의 100%가 담김**
- 변화 유형 자체가 메타데이터 (topic별 DNA)

### 005: 다중 기업 검증 ✅ — **업종/규모 불변 법칙**

| 지표 | 삼성전자 | 신한지주 | 현대차 | 카카오 | LG에너지 |
|------|---------|---------|--------|--------|---------|
| Null% | 87.3 | 89.2 | 89.0 | 92.6 | 82.3 |
| 중복률% | 73.9 | 75.4 | 75.4 | 70.9 | 72.0 |
| CAS압축% | 48.3 | 47.8 | 48.8 | 49.6 | 50.3 |
| 정보밀도% | 30.5 | 52.4 | 31.3 | 35.1 | 38.4 |

- **5개 기업 전부** Null 82%+, 중복 71%+, CAS 48%+ → 패턴 일반화 성립
- 금융업(신한지주): salesOrder/rawMaterial 없음, 대신 방카슈랑스/펀드상품 topic
- 신한지주 정보밀도 52.4% 최대 → 금융업이 텍스트 갱신 빈도 높음

### 006: Semantic Index ✅ — **가설 기각, 하지만 유용한 발견**

- 3차원 좌표(topic×type×magnitude) 고유 셀: 382 (22,060 블록 대비 **1.7%**)
- 키워드 추가해도 7.1% → **블록 레벨 고유 식별에는 부족**
- 키워드 커버리지: 18.1% (공시 텍스트의 82%는 키워드 사전 밖)
- **쿼리 레벨에서는 잘 동작**: "전략 전환 신호" 275건, "AI 관련 변화" 490건 (연도별 증가 추세 포착)
- 결론: 좌표계는 **탐색 진입점**으로 유효, **고유 식별자**로는 부족. textPathKey 같은 구조축 필요.

### 007: Atom 사람용 뷰 ✅

3가지 CLI 뷰 성공:
1. **기업 변화 타임라인**: 연도별 변화건수 + 유형 + 상위topic + 키워드 추이
   - 2024→2025에서 AI 키워드가 반도체 역전 (73 vs 68) → 전략 전환 가시적
2. **Topic 히트맵**: topic × period 격자 (기본/상세)
3. **단일 Topic 상세**: 변화 방향, 크기, 키워드, 미리보기까지

## 아키텍처 확정

```
[Layer 1] Content Store — CAS dedup (48% 압축, 업종 불변)
   hash로 1번만 저장, snapshot(period)로 완전 복원

[Layer 2] Change Map — 변화를 1급 시민으로
   5종 유형 분류 + topic별 프로파일
   "이 회사에 무슨 일이 있었는가"의 타임라인

[Layer 3] Semantic Facet — 좌표 기반 탐색 진입점 (식별자 아님)
   topic × changeType × magnitude + 키워드/엔티티
   쿼리 레벨에서 유효, 블록 레벨 식별에는 구조축(textPathKey) 추가 필요
```

## 비유

- Git `.git/objects` = Content Store
- Git tree/commit = Atom Index
- Git `diff` = Change Map
- `atom.snapshot("2024")` = `git checkout`
- `atom.changes("2023", "2024")` = `git diff` + 유형 분류
- `atom.query("AI 관련 변화")` = Semantic Facet 필터

### 008: changes 프로토타입 ✅

- sections → changes 변환: 첫 호출 4.6초, 이후 1.4초
- changes DataFrame(preview): 22,060행 × 10열 = **4.9MB**
- Polars filter/group_by 그대로 사용 가능

### 009: dict(CAS) vs DataFrame ✅

| 방식 | 메모리 | 필터 | 텍스트접근 |
|------|--------|------|-----------|
| CAS(dict) | 24.5MB | 2.0ms | **0.1ms** |
| DF(원본) | 51.7MB | **0.2ms** | 1.7ms |
| DF(preview) | **4.9MB** | **0.2ms** | sections에서 |

- CAS는 AI용(원본 텍스트 효율적 제공)에 필요
- DF(preview)는 사람용 부산물로 가능

## 최종 방향

**`c.changes`의 본래 목적: AI가 쓰기 좋은 압축된 공간**

```
현재 AI 경로: sections(97MB) → contextSlices(아무거나 잘라서) → LLM
목표 AI 경로: sections → changes(CAS + 메타) → 변화 블록만 → LLM
              바뀐 23%만 정확히, 변화 유형 태그와 함께 넘김
```

구조:
- CAS (Content Store) — AI에게 변화 원본을 효율적으로 제공
- 변화 유형 분류 — AI 컨텍스트에 태그로 같이 넘김
- 사람용 부산물 — preview DataFrame, 타임라인/히트맵 뷰 (만들면서 쓸만하면 남김)

### 010: changes 벡터화 ✅

- Polars unpivot + hash + shift().over()로 Python 루프 완전 대체
- **0.15초** (루프 1.9초 대비 12x 빠름)
- 22,060행 × 11열, 4.14MB — 행수·유형 분포 루프와 완전 일치
- 핵심 패턴: wide→long unpivot → null-safe hash/len → shift().over() 인접비교 → 벡터화 분류
- 주의: UInt32 뺄셈 오버플로우 → Int64 캐스트 필수

### 011: 전 종목 changes 프리빌드 ✅

- 5종목 샘플: 변환 0.05~0.24초, changes 1.8~6.0MB
- **전 종목 추정**: 2,548종목, 빌드 ~6.7분, 메모리 ~5.4GB
- **parquet+zstd 저장 시 추정 ~350MB** (원본 7.88GB 대비 4.4%)
- 저장 포맷 승자: parquet+zstd (압축률 93.4%), parquet+lz4 (읽기 최속)
- **AI 컨텍스트 밀도 2배**: 같은 16,000자에 changes 90블록 vs sections 45topic 정적텍스트

### 012: changes → AI 컨텍스트 품질 비교 ✅

- 같은 16K자 예산에서 changes가 **질적으로 압도적**
  - 현재: 45 topic 정적 원문 (변화 여부 불명)
  - changes: 84 변화블록 + 유형태그 + 크기 + preview
- Context Caching: 31% 비용 절감 (출력 토큰이 지배적이라 입력 캐시만으로는 한계)
- **횡단 질의 15ms**: 5종목 15만행, structural 순위/AI 키워드/appeared 급증 즉시 필터
- 핵심: AI가 "뭘 분석할지" 찾는 시간 제거 → 해석에 집중

### 013: 전 종목 횡단 분석 ✅ — **50종목 실증**

- 50종목 1,797,434행, 디스크 **31.9MB**, 메모리 464MB
- **횡단 질의 7종 전부 66ms 이내** (Polars 네이티브)
- 즉시 답이 나오는 질의 예시:
  - "structural 변화 1위는?" → 034730(SK이노) 1469건
  - "AI 키워드 1위는?" → 267250(현대중공업) 1009건
  - "ESG 추이는?" → 2021년 급증 (1.9배), 이후 안정
- AI 컨텍스트: 순위표+상세 2,832자/1,784토큰 (예산의 18%)
- 전 종목 추정: 디스크 1.6GB, 메모리 23GB → scan_parquet 또는 그룹별 로드 필요

### 014: 전 종목 프리빌드 ✅ — **5분, 47MB, 2535종목**

- Company 로드 없이 raw parquet 직접 → **5.1분에 전 종목 완료**
- 1,949,166행, 디스크 **47.2MB** (원본 7.88GB의 0.6%)
- 로드 0.16초, 횡단 질의 전부 **157ms 이내**
- Level 1 한계: appeared/disappeared 미감지 (section_order 불일치)

### 015: finance/report 프리빌드 ✅ — **finance 실용적, report 전략 변경 필요**

| 데이터셋 | 원본 | 합산(zstd) | 행수 | 횡단질의 |
|----------|------|-----------|------|---------|
| finance-ALL | 570MB | 388MB | 22M | ~300ms |
| finance-5Y | - | **197MB** | 11.7M | ~100ms |
| finance-2Y | - | **34MB** | 2M | ~17ms |
| report-ALL | 345MB | **114MB** | 10.1M | 48초 ❌ |

- finance: 28컬럼 고정, 합산 깔끔. 5Y(197MB) 또는 2Y(34MB) 실용적
- report: apiType별 컬럼 다름 → diagonal concat로 167컬럼 폭발 → apiType별 분리 저장 필요
- **전략**: docs=changes(47MB) + finance=5Y(197MB) + report=apiType별 분리

## 실험 전체 요약

| 실험 | 핵심 수치 |
|------|----------|
| 001: 중복률 | Null 87%, 중복 74%, CAS 48% |
| 002: Delta | 56.3% 압축, 양극화 패턴 |
| 003: 메타 분리 | Essential 5개면 충분 |
| 004: Delta=자산 | **23.2%에 변화의 100%** |
| 005: 다중 기업 | 5개 업종 패턴 일반화 |
| 006: Semantic | 좌표계 식별 기각, 쿼리 유효 |
| 007: 사람용 뷰 | CLI 3종 뷰 성공 |
| 008: 프로토타입 | DataFrame 22K행, 1.4초 |
| 009: dict vs DF | DF(preview) 4.9MB 승 |
| 010: 벡터화 | **0.15초**, 12x 빠름 |
| 011: 프리빌드 | 50종목 31.9MB, 6.7분 |
| 012: AI 컨텍스트 | changes 밀도 2배, 횡단 66ms |
| 013: 50종목 횡단 | 7종 질의 전부 66ms |
| **014: 전 종목** | **5분, 47MB, 157ms** |
| 015: finance/report | finance-5Y 197MB, report apiType별 분리 |

## scan 프리빌드 프로덕션화 완료

### 구현 내용 (015 실험 후 즉시 적용)

```
data/dart/scan/                    ← 횡단 scan 전용 프리빌드
├── changes.parquet                docs changes 5Y (47.2MB, 1.9M행)
├── finance.parquet                finance 5Y (196.6MB, 11.7M행)
└── report/                        apiType별 분리 (10개, 합계 27.1MB)
    ├── majorHolder.parquet        4.2MB
    ├── executive.parquet          9.8MB
    ├── employee.parquet           2.6MB
    ├── dividend.parquet           3.0MB
    ├── treasuryStock.parquet      1.7MB
    ├── capitalChange.parquet      2.3MB
    ├── corporateBond.parquet      0.8MB
    ├── auditOpinion.parquet       1.6MB
    ├── executivePayAllTotal.parquet  0.7MB
    └── executivePayIndividual.parquet  0.4MB
```

- **scan 전체: 270.7MB** (원본 ~9GB 대비 3%)
- 빌드 시간: changes 4분 + finance 25초 + report 2분 = **~7분**
- 가속 효과: report scan 21ms, finance scan 494ms (기존 수분)

### 변경 파일

- `src/dartlab/core/dataConfig.py` — scan 카테고리 추가
- `src/dartlab/market/scan/builder.py` — 빌더 모듈 (배치 파일 방식)
- `src/dartlab/market/_helpers.py` — scan 파일 존재 시 자동 가속 (fallback 유지)
- `src/dartlab/cli/commands/collect.py` — `dartlab collect --scan` 명령어
- `src/dartlab/core/dataLoader.py` — `downloadAll("scan")` 하위 폴더 지원
- `landing/src/lib/brand.ts` — data 블록 동기화

### 사용자 경로

- 배포자: `dartlab collect --scan` → HF push
- 사용자: `downloadAll("scan")` (~270MB) → 즉시 횡단 분석 (전종목 원본 불필요)

## 다음 단계

- [ ] `c.changes` 실제 구현 (Level 2 벡터화 빌더 + lazy 캐시)
- [ ] AI context builder에 changes 경로 추가
- [x] ~~scan에 changes 축 추가~~ → `market/scan/` 모듈로 구현 완료
- [x] ~~전 종목 프리빌드 CLI~~ → `dartlab collect --scan` 완료
- [ ] HuggingFace 배포 (`data/dart/scan/` 업로드)
- [ ] buildScanSnapshot에 scan 가속 적용 (현재 _helpers만 적용)
