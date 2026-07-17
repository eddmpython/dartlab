# `.github/scripts/` — GitHub Actions 전용 파이프라인 스크립트

GitHub Actions workflow (`.github/workflows/*.yml`) 가 호출하는 Python 스크립트들. 도메인 동사별 sub-dir 로 분류.

repo 의 `scripts/` (build/dev/audit 도구) 와 *별개* — `.github/scripts/` 는 *Actions runner 에서만* 호출된다.

## 디렉터리 구조

```
.github/scripts/
├── _hfRetry.py             # HF API retry helper (sub-dir 5 개가 sys.path parent 로 접근)
├── sync/                   # HF ↔ 로컬 양방향 sync
├── prebuild/               # derived artifact build
├── meta/                   # 메타 데이터 (corp/kind list refresh)
├── search/                 # search index build
└── ops/                    # operational (monitor / plan)
```

## 도메인별 스크립트 + 호출 workflow

### sync/ — HF ↔ 로컬 양방향 sync · 외부 API 수집

| 스크립트 | 역할 | 호출 workflow |
|---|---|---|
| [sync/seedFromHf.py](sync/seedFromHf.py) | HF→로컬 idempotent seed (size 다른 파일 다운로드) | `dataSync.yml`, `dataPrebuild.yml`, `deploy-landing.yml` |
| [sync/syncRecent.py](sync/syncRecent.py) | DART list.json 기반 정기공시 누락분 수집 + HF 업로드 트리거 | `dataSync.yml` |
| [sync/syncData.py](sync/syncData.py) | 88분기 차집합 full collect (heavy fallback) | `dataSync.yml` (workflow_dispatch full 모드) |
| [sync/syncNewStocks.py](sync/syncNewStocks.py) | KindList 신규 상장 종목 초기 수집 | `dartNewStocks.yml` |
| [sync/uploadData.py](sync/uploadData.py) | `dist/changed.txt` 기반 HF 증분 업로드 (batch 300/commit) | `dataSync.yml`, `dartNewStocks.yml` |
| [sync/uploadHfReadme.py](sync/uploadHfReadme.py) | HF dataset README 갱신 | (수동) |
| [sync/bulkUploadHf.py](sync/bulkUploadHf.py) | HF 전체 폴더 일괄 업로드 | (수동, cold start) |
| [sync/buildKrxData.py](sync/buildKrxData.py) | KRX OpenAPI → 연도별 raw parquet + HF push | `buildKrxData.yml` |
| [sync/buildKrxIndexData.py](sync/buildKrxIndexData.py) | KRX 지수 OHLCV bulk 수집 + HF push | `buildKrxIndexData.yml` |
| [sync/buildMacroData.py](sync/buildMacroData.py) | FRED/ECOS 카탈로그 → HF macro 벌크 parquet | `macroData.yml` |
| [sync/buildMacroCycle.py](sync/buildMacroCycle.py) | analyzeCycle → `macro/cycle/{kr,us}.json` HF push (KR/US phase 분석) | `macroData.yml` |
| [sync/prebuildValuation.py](sync/prebuildValuation.py) | valuation snapshot parquet 빌드 + HF 업로드 (Naver API) | `valuationSnapshot.yml` |
| [sync/buildAllFilingsRecent.py](sync/buildAllFilingsRecent.py) | 비정기공시 메타를 `dart/allFilings/byCode/{prefix}_recent.parquet`로 증분 빌드하고 manifest와 90일 피드를 원자 배포 | `originalSync.yml`, `allFilingsBackfill.yml` |
| [sync/buildGovData.py](sync/buildGovData.py) | gov 주가/지수 date 샤드 + `gov/prices/recent.parquet`(스파크라인) + `company/{code}` derive | `buildGovPriceData.yml`·`buildGovIndexData.yml` |

### prebuild/ — derived artifact build (parquet → JSON / aggregate)

| 스크립트 | 역할 | 호출 workflow |
|---|---|---|
| [prebuild/prebuildData.py](prebuild/prebuildData.py) | DART scan prebuild parquet 빌드 + HF 업로드 | `dataPrebuild.yml` |
| [prebuild/buildIndustryMap.py](prebuild/buildIndustryMap.py) | 산업지도 시각화 JSON (atlas/industries/companies) | `mapBuild.yml` |
| [prebuild/buildFinanceJson.py](prebuild/buildFinanceJson.py) | finance.parquet → dashboards/finance.json (전 상장사 5Y) | `mapBuild.yml` |
| [prebuild/buildQuartersJson.py](prebuild/buildQuartersJson.py) | finance.parquet → dashboards/quarters.json (분기 시계열) | `mapBuild.yml` |
| [prebuild/buildMetaJson.py](prebuild/buildMetaJson.py) | dashboards/meta.json (engines + 블로그 + thesis) | `mapBuild.yml` |
| [prebuild/buildMacroJson.py](prebuild/buildMacroJson.py) | macro.cycle → dashboards/macro.json | `mapBuild.yml` |
| [prebuild/buildStoryManifest.py](prebuild/buildStoryManifest.py) | story SSOT → static/story/manifest.json | `mapBuild.yml` |

### meta/ — 메타 데이터 refresh

| 스크립트 | 역할 | 호출 workflow |
|---|---|---|
| [meta/updateKindList.py](meta/updateKindList.py) | KRX KIND 상장목록 발행 (`corpList.parquet`) — gather SSOT `getKindList` 위임 (별도 크롤 0) | `kindlist.yml` |
| [meta/updateDartList.py](meta/updateDartList.py) | OpenDART CORPCODE 발행 (`dartList.parquet`) — gather SSOT `loadCorpCodes` 위임 (별도 파싱 0) | `kindlist.yml` |
| [meta/buildCorpProfile.py](meta/buildCorpProfile.py) | OpenDART companyInfo prefetch → `corpProfile.parquet` (acc_mt SSOT). 매일 incremental, missing 만 호출 | `kindlist.yml` |

### search/ — search index build

| 스크립트 | 역할 | 호출 workflow |
|---|---|---|
| [search/buildSearchMain.py](search/buildSearchMain.py) | content 인덱스 월간 main compaction + 일간 누적 delta/tombstone + 변경 artifact 배포 + lite | `searchIndexBuild.yml` |
| [search/buildSkillMarket.py](search/buildSkillMarket.py) | GitHub Discussion → Skill Market 정적 인덱스 | `deploy-landing.yml` |

### ops/ — operational

| 스크립트 | 역할 | 호출 workflow |
|---|---|---|
| [ops/monitorPipeline.py](ops/monitorPipeline.py) | 파이프라인 health check (실패 잡 issue 자동 생성) | `dataAudit.yml` |
| [ops/planRealdata.py](ops/planRealdata.py) | PR diff 기반 realData 테스트 plan JSON 생성 | `ci-full.yml` |

## sub-dir 스크립트의 `_hfRetry` import 규약

4 개 스크립트 (`sync/uploadData`, `sync/prebuildValuation`, `prebuild/prebuildData`, `search/buildSearchMain`) 가 `_hfRetry` 사용. sub-dir 의 sys.path 가 부모를 못 잡으므로 다음 boilerplate:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _hfRetry import retryHfCall  # noqa: E402
```

## 런타임 소비 데이터 아티팩트 (granularity 패턴)

랜딩/터미널(`ui/packages/runtime` 어댑터)이 HF 에서 **직접 읽는** 산출물. HF dir SSOT = [`src/dartlab/core/dataConfig.py`](../../src/dartlab/core/dataConfig.py) `DATA_RELEASES`. 회사 단위 접근은 아래 두 패턴 중 하나 — **둘 다 `stock_code`(6자리)가 canonical 키**(URL `/company/{code}`, 모든 per-company 산출물 공통).

**패턴 1 — 회사별 파일 `{code}.parquet|.json`** (큰 per-company 페이로드, 통째 읽기)

| 아티팩트 | 빌더 | 런타임 소비자 |
|---|---|---|
| `dart/panel/{code}.parquet` (정기공시 + 재무패널) | panel 파이프라인 | `regularFilingsSource` |
| `dart/finance/{code}.parquet` | prebuild/prebuildData | `financeSource` |
| `gov/prices/company/{code}.parquet` | sync/buildGovData `--derive-companies` | `govPriceSource` |
| `landing/map/companies/{code}.json` | prebuild/buildIndustryMap | `relationsSource` |

**패턴 2 — 코드 파티션 또는 전역 파일 + `stock_code` 필터** (회사마다 얇은 슬라이스만 HTTP range read)

| 아티팩트 | 빌더 | 런타임 소비자 | 갱신 |
|---|---|---|---|
| `dart/allFilings/byCode/{prefix}_recent.parquet` (비정기) | sync/buildAllFilingsRecent | `nonRegularFilingsSource` | 전 이력 유지, 변경 코드 버킷만 갱신. `byCode/manifest.json`이 레이아웃 SSOT |
| `dart/scan/report/{employee,investedCompany,dividend,treasuryStock}.parquet` | prebuild/prebuildData | `reportSource` (좌측 회사패널) | 전 이력, scan prebuild |
| `metadata/corpList.parquet` (KRX KIND 상장목록) | meta/updateKindList | `productIndexSource` | 일배치 |
| `metadata/dartList.parquet` (`corp_code↔stock_code↔명`) | meta/updateDartList | gather(공시에 stock_code 부착)·검색 | 일배치 |
| `macro/{fred,ecos}/observations.parquet` | sync/buildMacroData | `macroSource` | cron |

> **`stock_code` 가 파일에 박혀 정렬돼 있어야** pushdown 필터가 된다 — `kindList`/`dartList` 같은 매핑表로 *대체 불가*. 그 둘은 `name↔corp_code↔stock_code` **해소(검색·수집 시 stock_code 부착)** 용 별도 lookup 이고, 이미 빌드된 데이터 파일을 회사별로 잘라주지는 못한다. allFilings 가 `stock_code` 키인 건 (a) pushdown 필터 키이자 (b) 패턴 1·전 UI 와 동일한 canonical 키라 일관.

**패턴 3 — 연/날짜 샤드 + 필터**: `gov/prices/date/{year}.parquet`(`priceSource`) · `gov/indices/{index/{key}|date/{year}}.parquet`(`govIndexSource`).

> **이관 주의(운영)**: `byCode/manifest.json`이 없는 첫 실행만 기존 `recent.parquet`를 읽어 코드 버킷을 만든다. 이후 cron은 이번 수집분에 등장한 버킷만 merge한다. legacy 파일은 안전한 UI 순차 배포용 fallback으로만 남고 더 이상 재생성하지 않는다.

## workflow 추가 시 (새 스크립트 정착 절차)

1. 도메인 식별 → `sync/`·`prebuild/`·`meta/`·`search/`·`ops/` 중 적절한 sub-dir 에 작성.
2. `_hfRetry` 사용 시 위 boilerplate 적용.
3. `.github/workflows/<workflow>.yml` 의 `run:` 라인에 `.github/scripts/<domain>/<name>.py` 경로 명시.
4. 본 README 의 도메인별 표에 행 추가.
