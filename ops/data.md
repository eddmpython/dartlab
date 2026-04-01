# Data

HuggingFace 데이터셋 관리, 자동 수집 파이프라인, 프리빌드, 모니터링.

| 항목 | 내용 |
|------|------|
| 레이어 | L0 (core/dataConfig, dataLoader) |
| 진입점 | `Company("005930")` 시 자동 다운로드 |
| 데이터셋 | HuggingFace `eddmpython/dartlab-data` |
| 소비 | Company, providers, scan, analysis 전체 |

## 한눈에 보기 — 자동 파이프라인

```
UTC 00:00  kindlist.yml ──────── KRX 종목 리스트 갱신
UTC 17:00  dataSync.yml ──────── DART 전종목 증분 수집 (finance/report/docs × 3 matrix)
UTC 18:00  dataSyncDaily.yml ─── 최근 7일 공시 경량 수집
           ↓ workflow_run (completed + success)
           dataPrebuild.yml ──── scan 프리빌드 → HF 업로드
UTC 20:00  dataPipeline.yml ──── 전체 파이프라인 감사 (Issue 알림)
일요일 08:00  edgarSync.yml ──── EDGAR S&P500 5배치 수집

마스터 진입점: dataPipeline.yml (full 모드 = 수집+프리빌드+감사 일괄)
```

## DATA_RELEASES (중앙 설정)

`src/dartlab/core/dataConfig.py` 한 곳에서 관리:

| 카테고리 | 경로 | 설명 | 자동 수집 |
|----------|------|------|-----------|
| docs | dart/docs | 공시 문서 (~8GB, 2500+종목) | dataSync, dataSyncDaily |
| finance | dart/finance | 재무제표 (~600MB, 2700+종목) | dataSync, dataSyncDaily |
| report | dart/report | 정기보고서 (~320MB, 2700+종목) | dataSync, dataSyncDaily |
| scan | dart/scan | 전종목 횡단분석 프리빌드 | dataPrebuild |
| allFilings | dart/allFilings | 전체 공시 원문 | 로컬 전용 |
| stemIndex | dart/stemIndex | Ngram+Synonym 역인덱스 | 로컬 전용 |
| edgarDocs | edgar/docs | SEC EDGAR 공시 문서 | edgarSync |
| edgar | edgar/finance | SEC EDGAR 재무 | edgarSync |
| edinetDocs | edinet/docs | EDINET 공시 (일본) | 로컬 전용 |
| edinet | edinet/finance | EDINET 재무 (일본) | 로컬 전용 |

새 카테고리 추가: `DATA_RELEASES`에 한 줄 + `brand.ts` data 블록 추가.

## 워크플로우 상세

### dataSync.yml — DART 전종목 증분

- **스케줄**: 매일 UTC 17:00 (KST 02:00)
- **Matrix**: finance, report, docs 3병렬
- **흐름**: 캐시 복원 → `syncData.py` (HF clone + batchCollectAll) → 해시 기반 변경 감지 → `uploadData.py` (HF + GH Release)
- **환경변수**: `DART_API_KEYS`, `HF_TOKEN`, `SYNC_CATEGORY`, `SYNC_MODE`
- **타임아웃**: 300분

### dataSyncDaily.yml — 최근 공시 경량

- **스케줄**: 매일 UTC 18:00 (KST 03:00)
- **흐름**: DART list.json → 최근 7일 정기공시 → rcept_no 비교 → 새 보고서 종목만 수집 → 카테고리별 changed.txt
- **환경변수**: `DART_API_KEYS`, `SYNC_LOOKBACK_DAYS`
- **타임아웃**: 90분

### dataPrebuild.yml — scan 프리빌드

- **트리거**: `workflow_run` (Data Sync / Daily Data Sync 완료 후 자동)
- **흐름**: 3개 캐시 복원 (finance/report/docs) → `prebuildData.py` → buildScan() → HF upload_folder
- **출력**: changes.parquet, finance.parquet, report/12개 apiType.parquet
- **타임아웃**: 120분

### edgarSync.yml — EDGAR 문서 수집

- **스케줄**: 일요일 UTC 08:00
- **Matrix**: 5배치 × 100 tickers (S&P500)
- **흐름**: `syncEdgarDocs.py` → HF 업로드 (GH Release 스킵)
- **타임아웃**: 300분

### kindlist.yml — KRX 종목 리스트

- **스케줄**: 매일 UTC 00:00 (KST 09:00)
- **흐름**: KRX KIND 크롤링 → SHA256 비교 → 변경 시만 업로드

### dataPipeline.yml — 마스터 진입점

**단일 진입점으로 전체 파이프라인 실행 + 감사.**

- **스케줄**: 매일 UTC 20:00 (audit 모드)
- **수동 실행**: `full` 모드 = 수집 → 프리빌드 → 감사 순차
- **3개 Job**:
  1. `collect` (full 모드만) — dataSync와 동일한 수집
  2. `prebuild` (full 모드만, collect 완료 후) — scan 프리빌드 + HF 업로드
  3. `audit` (항상) — 전체 워크플로우 상태 감사 + Issue 알림
- **감사 대상**: Data Sync, Daily Data Sync, EDGAR Data Sync, Update KindList, Data Prebuild

## CI 스크립트 역할

| 스크립트 | 호출자 | 역할 |
|----------|--------|------|
| `syncData.py` | dataSync, dataPipeline | HF clone + DART 증분 수집 + changed.txt |
| `syncRecent.py` | dataSyncDaily | 최근 7일 공시 수집 |
| `syncEdgarDocs.py` | edgarSync | EDGAR 배치 수집 |
| `uploadData.py` | dataSync, dataSyncDaily, edgarSync | HF + GH Release 업로드 |
| `prebuildData.py` | dataPrebuild, dataPipeline | scan 프리빌드 + HF 업로드 |
| `monitorPipeline.py` | dataPipeline | 워크플로우 건강 체크 + Issue 알림 |
| `updateKindList.py` | kindlist | KRX 종목 리스트 크롤링 |

## 로컬 전용 작업

자동 파이프라인에 포함되지 않는 작업:

| 작업 | 명령 | 이유 |
|------|------|------|
| scan snapshot | `buildScanSnapshot()` | 메모리 집약 (scanner 인스턴스화, 전종목 로드) |
| stemIndex 리빌드 | `rebuildIndex()` + `pushStemIndex()` | allFilings 데이터 필요 (~220초) |
| allFilings 수집 | `collectMeta()` + `fillContent()` | 대량 API 호출 |
| 단일 종목 수집 | `dartlab collect 005930` | 개발/디버깅용 |

## 수집 엔진

- `ZipDocsCollector`: ZIP(document.xml) 기반 (빠름, 권장)
- `batchCollect()` / `batchCollectAll()`: 비동기 멀티키 병렬

## 3-Layer Freshness

1. **ETag**: HF 원격 vs 로컬 비교
2. **TTL**: DART 72시간, EDGAR 24시간 경과 시 갱신
3. **API**: 최근 4분기 누락 직접 조회

## 캐싱 전략 (GitHub Actions)

- `actions/cache@v4` prefix matching 사용
- 키 패턴: `dartlab-data-{category}-{run_id}` (저장)
- 복원 키: `dartlab-data-{category}` (최신 prefix 매칭)
- 카테고리별 독립 캐시 → 병렬 matrix 가능

## 업로드 전략

| 대상 | 방식 | 배치 |
|------|------|------|
| HF (개별 파일) | `CommitOperationAdd` | 100파일/커밋 |
| HF (디렉토리) | `upload_folder` | scan 전체 |
| GH Release | `gh release upload --clobber` | 50파일/배치 |
| HF-only | edgarDocs, edinetDocs | GH Release 스킵 |

## 모니터링

- **자동**: dataPipeline.yml audit job (매일 UTC 20:00)
- **감사 대상**: 5개 워크플로우 최근 실행 상태
- **알림**: `pipeline-failure` 라벨 GitHub Issue 자동 생성
- **자동 해소**: 전부 성공 시 열린 Issue 자동 닫기
- **Step Summary**: 모든 워크플로우에 `GITHUB_STEP_SUMMARY` 작성

## 메모리/리소스 제약

| 항목 | 한도 |
|------|------|
| GitHub Actions RAM | ~7GB |
| GitHub Actions 디스크 | 14GB |
| scan 프리빌드 배치 | 200종목 단위 중간 파일 |
| 전체 캐시 합계 | ~9.2GB (finance 600MB + report 320MB + docs 8GB + scan 270MB) |
| scan snapshot | CI 부적합 (메모리 집약) |

## 관련 코드

| 파일 | 역할 |
|------|------|
| `src/dartlab/core/dataConfig.py` | DATA_RELEASES 중앙 설정 |
| `src/dartlab/core/dataLoader.py` | parquet 캐싱, HF 동기화, ETag |
| `src/dartlab/scan/builder.py` | scan 프리빌드 (changes/finance/report) |
| `src/dartlab/scan/snapshot.py` | scan snapshot (로컬 전용) |
| `src/dartlab/core/search/ngramIndex.py` | stemIndex 역인덱스 빌드/검색 |
| `src/dartlab/providers/dart/openapi/batch.py` | 배치 수집 엔진 |
| `.github/scripts/` | CI 스크립트 7개 |
| `.github/workflows/` | 워크플로우 6개 (data 관련) |
