# 06 · Progress Ledger — 결정·상태·NEXT

상태: v0.1 (2026-06-28 작성). 끊긴 세션은 §NEXT 만 읽고 재개. 내용 복제 금지 — 결정·상태·열린 질문만.

## 1. 확정 결정 (전문 패널 토론 + 적대 교차검증 후)

| 크럭스 | 결정 | 기각 |
|---|---|---|
| 보안 게이트 방향 | **public allowlist 단일화** | deny-list — private 6종이 same-repo 라 토큰 차단 안 먹음, news prefix 혼재로 blanket deny 가 공개 오차단 |
| 노출 대상 | public:True **⊋** 표형 화이트리스트 | "public:True 전부 자동 미러" — contentIndex(검색인덱스)·edgarDocs(좀비)·landing JSON 은 표 아님 |
| 날짜샤드 종목 슬라이스 | MVP 제외, 회사파일 라우팅 | `filter`/`code` — `request.ts:33-34` read 후 JS prune, 326MB 전량 디코드 OOM |
| Tier2 hfProxy 재사용 | retry/CORS/path정규화만 재사용, 변환·allowlist 신규 | "형제 라우트 0줄 재사용" — hfProxy 는 순수 fetch(parquet 디코드 0, `worker.js:19`) |
| 무게이트 passthrough | 변환 라우트에 allowlist 게이트 신규 부착 | hfProxy `/hf` 무게이트 복제 — allFilings 이미 샘 |
| cap 단위 | **셀(cols×rows)** | 행 단위 — IMPORTDATA 한도 ~50k셀, 17-col 5천행=8.5만셀 초과 |
| truncated 신호 | HTTP 헤더 전용 | CSV 본문 주석행 — IMPORTDATA 가 데이터로 파싱·오염 |
| 기본 포맷 | **TSV** 기본 + CSV 병행 | CSV 단독 — 한국 Excel 콤마 로케일 충돌 |
| 포맷 채널 | 확장자 단일 결정 | `sep`/`format` 쿼리 override — 이중 채널 군더더기 |

## 2. 코드 실측으로 확인된 load-bearing 사실

- `infra/workers/hfProxy/worker.js` — 순수 fetch(`:19` nodejs_compat 불필요, parquet 디코드 0), UPSTREAM=`dartlab-data` 단일(`:21`), retry/CORS/2층 캐시. `/hf` passthrough 는 **allowlist 전무**(`:327` 부근).
- `src/dartlab/core/dataConfig.py` `DATA_RELEASES` — private 6종(allFilings·edgarScan·stemIndex·edinet·edinetDocs·aiKnowledge) **`repo` override 없음 = same repo**. 전용 private repo 는 dartOriginal·newsNaver* 뿐. contentIndex=public 이나 BM25 검색인덱스(표 아님).
- `ui/packages/runtime/src/data/fetch/request.ts` — `requestParquetRows`(columns/rowStart/rowEnd=진짜 prune, filter=read 후 JS 술어 `:33-34`). 브라우저·워커 동일 reader.
- `ui/packages/surfaces/src/viewer/lib/xlsx/buildWorkbook.ts` — 진짜 OOXML(병합·Number coerce·honest-gap). table-export Phase2a 산물, 재사용 대상.
- `ui/packages/runtime/src/data/origins/registry.ts:76-110` — 워커 origin 패턴(resolve/configured/cache). csvWorker 동형 등록처.

## 3. 문서 상태

| 문서 | 상태 |
|---|---|
| README · 00 · 01 · 02 · 03 · 04 · 05 · 06 | ✅ v0.1 |

## 4. 워크스페이스 변동

- 신규 폴더 `mainPlan/data-download-center/`(8 문서). 코드 변경 0(PRD만).

## 5. Phase 체크리스트

- [x] **Phase 0 — 스캐폴드**: `downloadCatalog()`(Python SSOT) + TS 미러 + 워커 `allowlist.js` + drift 가드(`test_download_catalog.py::test_worker_allowlist_in_sync`). public·flat·표형만 노출, private 자동 차단.
- [x] **Phase 1 — Tier1 다운로드(MVP 척추)**: `landing/src/routes/lab/data-center` 링크빌더 — 카탈로그 21셋 → 종목/시리즈 → 스키마 조회(브라우저 `readParquetRows` 직독) → 컬럼 투영·범위(tail/head/freq) → `.xlsx`/`.csv` 다운로드 + Tier2 =IMPORTDATA URL + 셀수 프리뷰. 신규 작성기 0(objectsToWorkbook·toCsv·originUrl 재사용). 검증: svelte-check 0에러, Playwright PASS(005930 xlsx 27.6KB·csv 3.8KB 실다운로드·한글 stem 13컬럼·콘솔에러 0). `998c1ab1e`.
- [ ] **Phase 2 — 졸업**: 스크린샷 눈검수(운영자) 후 `/data` 승격 + 명시 push 승인. (현재 `/lab/data-center` 격리, push 대기.)
- [x] **Phase 3 — Tier2 워커 (코드·로컬증명 완료, 무료 배포 준비)**: `infra/workers/dataCsv` 구현 — `/v1/{dir}/{id}.{csv|tsv}?cols=&tail=&head=&freq=` + `/v1/`카탈로그 + `schema.json` + allowlist 게이트(allowlist.js) + footer 예산 가드 + 셀cap 헤더 + 에러모델(400/404/405/413/502). 로컬 node 로 13 케이스 end-to-end PASS(BOM·en-US숫자·honest-gap·한글 stem·413 dateShard·404 private 누설0·400+available·HEAD). **실측 결론(배포 호스트 게이트)**: 디코드 RSS = gov/prices/company 70MB · dart/finance 119MB · macro/fred 210MB · **dart/panel 927MB**(본문). footer `total_uncompressed_size`×6 ≈ 실측 RSS(panel 추정 932MB vs 측정 927MB 일치). **호스트 = CF Worker(PRD)**. CF 128MB 메모리상: 회사 flat 파일(prices 70MB·indices·brokerage·finance 119MB) 라이브, fred observations 210MB·panel-full 927MB 는 **413→Tier1**(killList 패턴). `cols` 투영이 탈출구(panel 본문 제외 927→80MB). `tail`/`head` 는 단일 row-group 이라 메모리 안 줄임(슬라이스만). 남은 게이트 = openDecision #2 CF CPU(무료 10ms vs 유료) = 배포 후 실측·운영자 보고(05 §3). drift 가드 `test_worker_allowlist_in_sync` 추가. (⚠ 옛 기재 '~1GB 서버리스/Vercel' 은 PRD 이탈 — 철회, CF 로 재정렬.)
- [x] **Phase 4 — 배선**: `csvWorker` origin 등록(`registry.ts`) + `VITE_DARTLAB_CSV_PROXY` 게이트. 미설정 시 Tier2 비활성·Tier1 만 노출(무중단). 데이터센터가 이 origin 으로 Tier2 URL 생성. `998c1ab1e`. (남은 건 CF 배포 시 env 설정뿐.)
- [ ] **Phase 5 — 후속(MVP 외)**: 날짜샤드 Tier2(CF 한도 통과 시)·`freq` OHLCV-aware 집계·`/v1/{dir}/index.json` HF tree 열거·passthrough 격상 검토.

## 6. 열린 질문 (운영자 결정)

1. **워커 도메인/라우트** — 전용 워커(`infra/workers/dataCsv`, 게이트 격리) 구현됨. placeholder=`*.workers.dev`.
2. **CF Worker CPU 플랜** (PRD 핵심 게이트) — 메모리는 실측 확정(회사파일 128MB 안, 큰 파일 413→Tier1). 남은 건 **CPU**: 무료(10ms) vs 유료(50ms~30s). parquet 디코드 CPU 가 무료 10ms 안에 드는지 = **CF 배포 후 실측 → 운영자 보고**(05 §3). 운영자 "유료 안 함" 이면 무료 10ms 에 드는 작은 회사파일만 라이브, 못 들면 Tier1 전용.
3. **CELL_CAP** = 45,000 확정. **Tier2 대상** = isTier2(company/series). **macro 단일시리즈** = `{id}=seriesId` 구현했으나 observations 전량 디코드(210MB)라 CF 128MB 초과 → CF 에선 413. 라이브하려면 observations 시리즈별 분할(sync 측 build 변경=PRD-gap, 별도 토론·승인).
4. **`/data-center` → `/data` 졸업** — 스크린샷 눈검수 + 운영자 명시 push 승인.

## 7. NEXT

**Phase 0·1·3·4 완료 — 빌드 가능한 전부 끝.** Tier1 다운로드 surface 라이브 작동(브라우저 직독, 백엔드 0), Tier2 워커 CF-ready, origin 배선 완료. **남은 건 운영자 게이트 2개뿐**: ① **UI 스크린샷 눈검수 + 명시 push 승인**(`/lab/data-center` 커밋 `998c1ab1e` 등 UI 커밋 push 대기) → 통과 시 `/data` 졸업(Phase 2). ② **CF 워커 배포(`wrangler deploy`, 운영자 CF 로그인) + CPU 실측 보고**(05 §3, openDecision #2) → `VITE_DARTLAB_CSV_PROXY` 설정 시 Tier2 라이브 URL 활성. 배포 전엔 데이터센터가 Tier1 만 노출(무중단).

## 8. 화해 상태

- table-export(구현됨): `buildWorkbook` 재사용만, 침범 0.
- terminal-data-download: 가격 OHLCV CSV, 공존(본문 주석행 금지 함정 공유).
- viewer `DataDownloadMenu`: 그대로, 격상은 "나중".
