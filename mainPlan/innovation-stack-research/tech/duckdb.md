# DuckDB 조사 원장

- **우리 현재 사용**: 예. cross-company scan 의 backend 옵션. pin `duckdb>=1.0,<2`. 실사용 lock 버전 1.5.3 (조사 시점 최신 1.5.x).
- **주 사용처**: `src/dartlab/scan/io/cross.py` 의 `DuckDbCrossScan`. `DARTLAB_CROSS_SCAN_ENGINE=duckdb` 또는 large dataset 검출 시 fallback. `scanClass.py::docsSections`가 `engine` 인자로 dispatch.
- **마지막 조사일**: 2026-07-06
- **현재 결정**: 채택 (호환 backend). 단 우리가 붙인 "OOC god mode" 주석은 현 구현과 불일치(아래 병목 참고). 진짜 혁신 레버는 source manifest/parquet path 를 DuckDB 가 직접 `read_parquet` 하는 source-native OOC arm. 2026-07-07 `tests/_attempts/crossScanOoc/` 실측으로 **집계(group by) 경로 부분 GO**: native peak RSS 가 행수와 무관하게 ~88MB 로 평평(10M 에서 polars 328MB 의 1/3.7), 결과 동등성 EQUAL. 전종목 집계 OOM 해제 실증. 단 졸업 전 설계 과제 남음(path 기반 surface·sourceRef 보존·실그룹 cardinality·join). DuckLake/Iceberg lakehouse 는 기각. VARIANT/GEOMETRY 신타입은 현재 불필요(보류).

---

## 병목 (재확인, 2026-06-17 부터 이어짐)

현 `DuckDbCrossScan.aggregate()` 경로: (1) Polars LazyFrame 을 `collect(engine="streaming")` (2) 결과 DataFrame 을 DuckDB in-memory connection 에 등록 (3) `SELECT * FROM lf` 후 Polars 반환. 즉 DuckDB 가 Parquet 를 직접 읽으며 filter/projection pushdown 과 spill 을 담당하는 구조가 아님. 따라서 현 DuckDB 경로는 OOC baseline 이 아니라 compatibility wrapper 다. 이 사실은 조사할 때마다 재확인됨.

---

## 조사 이력

### 2026-07-07 (crossScanOoc 실측, source-native arm)

- `tests/_attempts/crossScanOoc/` 에 3 팔(polars streaming / 현 DuckDbCrossScan 재현 / source-native `read_parquet`) 마이크로 벤치 작성 + 실행. 합성 parquet 4 파일, 100k~10M 행, projection/filter/groupby, subprocess 격리 peak RSS.
- 결과: group by 에서 native peak RSS ~88MB 로 행수 무관하게 평평(polars 는 10M 에서 328MB). filter 완만 우위. projection(전행 반환)은 native 불리. 현 DuckDbCrossScan 은 전 케이스 최악(이중 materialize) = 원장의 "현 경로는 OOC 아님" 실증. 동등성 전부 EQUAL.
- 판정: 집계 경로 부분 GO. 전종목 집계 OOM 해제 근거 확보. 상세/표 = `tests/_attempts/crossScanOoc/README.md`.
- 남은 과제(졸업 전): path 기반 surface(현 `aggregate(lf)` 는 LazyFrame 수신), sourceRef/manifest 보존, 실그룹 cardinality(회사코드 수천) 재측정, join 미측정.

### 2026-07-06 (DuckDB 1.5.3, 우리 pin 과 동일 = 최신)

조사 경로: MCP WebSearch (공식 announce·docs·GitHub·DuckLake). WebFetch 본문 요약은 당시 API 529 과부하로 스니펫 기반 확인.

**카테고리별 관찰**

1. Cross-scan / source-native OOC Parquet SQL (우리 P0 레버)
   - 변화 없음. DuckDB 는 여전히 `read_parquet(...)` 로 파일/경로 리스트를 직접 scan + filter/projection pushdown + disk spill 가능.
   - Hive 파티션 parquet 를 디스크/오브젝트 스토리지에서 직접 쿼리 가능(분석과 적재 분리).
   - 판단: P0 유지, 미구현. `DuckDbCrossScan` 옆에 source manifest/path 를 받는 내부 arm 을 두고 `read_parquet` 를 직접 수행하는 설계는 `01-priority-stack-register` A 항목 그대로 유효. 착수 전 `_attempts/crossScanOoc` 에서 Polars streaming vs source-native DuckDB 의 peak RSS/시간/결과 동등성 실측 필요.

2. Parquet 읽기 / httpfs / S3 / HTTP range
   - Parquet read/write + filter/projection pushdown 안정. `httpfs` 로 HTTP(S)/S3 Parquet 를 `read_parquet` 로 읽기 가능(public read 는 HTTP Range 핵심).
   - 판단: 우리 HF parquet 직독 및 #1(source-native scan)·#3(브라우저)의 토대. 별도 결정 불요, 기존 방향 유지.

3. WASM (브라우저)
   - DuckDB-WASM 이 브라우저에서 SQL inspection, OPFS 캐시, local import 가능. 최신 stable wasm client 1.5.3 대(문서 기준).
   - 판단: `Browser Parquet Workbench`(P0) 후보의 한 축. hyparquet 와 비교 실측 대상. UI `data/fetch`+`origins` SSOT 아래로만 연결, raw fetch 금지.

4. 스토리지 포맷 / DuckLake / Iceberg (lakehouse)
   - DuckLake: SQL+Parquet 기반 오픈 lakehouse 포맷(메타데이터는 catalog DB, 데이터는 Parquet). DuckLake 1.0 존재. 1.5.3 에 DuckDB-Iceberg 신기능(2026-05-29).
   - 판단: 기각. `innovation-stack-research/02` Kill List "Lakehouse 과잉 도입"과 일치. 우리는 HF manifest + source catalog + content index manifest 로 이미 더 가볍게 해결. 재검토 조건: 정기 대용량 write/version 관리 workload 가 생길 때만.

5. 신 타입 (VARIANT / GEOMETRY)
   - VARIANT: Snowflake 영감의 semi-structured 타입(2025 부터 Parquet 지원, DuckDB Parquet reader 지원). GEOMETRY: 빌트인 지오 타입. friendly CLI 도 1.5.0 신규.
   - 판단: 보류(현재 불필요). 지리 데이터 없음(GEOMETRY 무관). VARIANT 는 반정형 노트/JSON 성 데이터에 잠재 가치이나 지금 도입 이유 없음. 재검토 트리거: 노트/공시 반정형 필드를 열 단위로 다뤄야 하는 요구가 나오면 VARIANT 검토.

6. 버전 / pin / LTS 정책
   - 1.5.0 "Variegata" 2026-03-09 출시. 우리 실사용 1.5.3 은 조사 시점 최신 1.5.x. 2.0 없음, pin `<2` 안전.
   - 1.4.0 LTS "Andium" 은 2026-09 EOL 예정.
   - 판단: pin `>=1.0,<2` + 1.5.3 유지. 안정성 우선이 필요하면 LTS 라인 옵션이 있으나, 현재 1.5.x 로 문제 없음.

**본 자료 (sources)**

- DuckDB 1.5.0 "Variegata" announce (friendly CLI·VARIANT·GEOMETRY·1.4 LTS EOL 2026-09): https://duckdb.org/2026/03/09/announcing-duckdb-150
- DuckDB News (1.5.3 DuckDB-Iceberg 2026-05-29 등): https://duckdb.org/news/
- GitHub Releases: https://github.com/duckdb/duckdb/releases
- VARIANT 타입 docs: https://duckdb.org/docs/current/sql/data_types/variant
- DuckLake (오픈 lakehouse 포맷): https://github.com/duckdb/ducklake
- Parquet overview / httpfs / S3 (2026-06-17 조사분, 유효): https://duckdb.org/docs/current/data/parquet/overview , https://duckdb.org/docs/current/guides/network_cloud_storage/http_import , https://duckdb.org/docs/lts/core_extensions/httpfs/s3api
- DuckDB-WASM overview: https://duckdb.org/docs/current/clients/wasm/overview

**결정 및 근거 (2026-07-06)**

- 호환 backend 채택 유지. 버전은 최신(1.5.3)으로 이미 정렬됨, 상향 불요.
- P0 레버는 여전히 source-native `read_parquet` OOC arm. 미구현. 착수 전 `_attempts/crossScanOoc` 실측이 게이트(Polars streaming 대비 peak RSS 개선 + 결과 동등성 + sourceRef/manifest 보존이 통과 조건).
- 기각 유지: DuckLake/Iceberg lakehouse(과잉), VARIANT/GEOMETRY(현재 불필요).
- 금지 재확인: `DuckDbCrossScan` 주석만 고치고 OOC 해결로 홍보 금지, public API 에 SQL 문자열 직접 노출 금지.

### 2026-06-17 (이전 스냅샷, innovation-stack-research 00~04)

- "DuckDB 도입"이 아니라 "source-native DuckDB scan"으로 명명(D1). 현 의존성에 이미 DuckDB 있음.
- 현 `DuckDbCrossScan` 은 Polars collect 이후 DuckDB 등록이라 OOC claim 약함 확인.
- Decision Matrix: DuckDB source-native OOC = Impact 5 / Fit 5 / Risk 3 = P0 실측.
- 기각: Iceberg/lakeFS/full metadata catalog server(lakehouse 과잉), Spark/Ray/Dask/Daft 전면 도입.
