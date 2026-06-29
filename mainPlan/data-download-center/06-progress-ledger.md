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

- [ ] **Phase 0 — 스캐폴드**: `DATA_RELEASES` → 노출 화이트리스트 빌드타임 emit 상수 + drift 가드 테스트(`tests/audit/csvWorkerAllowlist`). 변환 전 SSOT 게이트부터.
- [ ] **Phase 1 — Tier1 다운로드(MVP 척추)**: `lab/data-center` 프로토타입, `requestParquetRows` 직독 → `buildWorkbook`/`csvExport` 재사용, 링크빌더 UX. 백엔드 0.
- [ ] **Phase 2 — 졸업**: 스크린샷 눈검수 후 `/data` 승격, 운영자 명시 push 승인.
- [x] **Phase 3 — Tier2 워커 + 실측 게이트 (코드·로컬증명 완료, 배포 운영자 결정 대기)**: `infra/workers/dataCsv` 구현 — `/v1/{dir}/{id}.{csv|tsv}?cols=&tail=&head=&freq=` + `/v1/`카탈로그 + `schema.json` + allowlist 게이트(allowlist.js) + footer 예산 가드 + 셀cap 헤더 + 에러모델(400/404/405/413/502). 로컬 node 로 13 케이스 end-to-end PASS(BOM·en-US숫자·honest-gap·한글 stem·413 dateShard·404 private 누설0·400+available·HEAD). **실측 결론(배포 호스트 게이트)**: 디코드 RSS = gov/prices/company 70MB · dart/finance 119MB · macro/fred 210MB · **dart/panel 927MB**(본문). footer `total_uncompressed_size`×6 ≈ 실측 RSS(panel 추정 932MB vs 측정 927MB 일치). **CF Workers 128MB(전 플랜 고정)는 큰 파일 불가** → 작은 회사파일만 라이브. 전 카탈로그 라이브 = **~1GB 서버리스 함수**(같은 핸들러). `cols` 투영이 메모리 탈출구(panel 본문 제외 927→80MB). `tail`/`head` 는 단일 row-group 이라 메모리 안 줄임(슬라이스만). → 미결정 #1 호스트·#2 플랜 = ~1GB 서버리스 권장. drift 가드 `test_worker_allowlist_in_sync` 추가.
- [ ] **Phase 4 — 배선**: `csvWorker` origin 등록 + `VITE_DARTLAB_CSV_PROXY` env. (워커 변환·셀cap·카탈로그·schema 는 Phase 3 완료 — 남은 건 호스트 배포 + UI origin 배선뿐.)
- [ ] **Phase 5 — 후속(MVP 외)**: 날짜샤드 Tier2(CF 한도 통과 시)·`freq` OHLCV-aware 집계·`/v1/{dir}/index.json` HF tree 열거·passthrough 격상 검토.

## 6. 열린 질문 (운영자 결정)

1. **워커 도메인/라우트** — 새 전용 워커(`infra/workers/dataCsv`, 게이트 격리 권장) vs hfProxy `/v1/` 증설(인프라 1개 절감이나 무게이트 passthrough 공존 위험). placeholder=`*.workers.dev`.
2. **CF Worker 플랜** — 무료(10ms CPU, 콜드 디코드 위험) vs 유료(50ms~30s). Tier2 비용 결정.
3. **CELL_CAP 수치** — Sheets ~50k셀 / Excel / 워커CPU 중 어디 맞추나. 회사파일 1회 실측 후(예 45,000).
4. **Tier2 첫 대상 dir** — flat 13종 중 MVP 우선순위(dart/finance·macro/fred·gov/prices/company 부터?).
5. **`/data-center` → `/data` 졸업 시점** — 스크린샷 눈검수 + 운영자 명시 push 승인.
6. **drift 가드 blocking vs 경고** — 권장 blocking(보안 경계 SSOT).

## 7. NEXT

**Phase 3 코드·로컬증명 완료(`infra/workers/dataCsv`).** 남은 게이트 = 운영자 호스트 결정(미결정 #1·#2): **CF 128MB(작은 파일만 라이브) vs ~1GB 서버리스(전 카탈로그, 권장)**. 호스트 정해지면 → 배포(`wrangler deploy` 또는 서버리스) → Phase 4 UI origin 배선(`csvWorker`+`VITE_DARTLAB_CSV_PROXY`). follow-up: macro/* 단일 시리즈 `series=` 필터 결정(단일 벌크 observations.parquet 라 post-decode 필터 안전).

## 8. 화해 상태

- table-export(구현됨): `buildWorkbook` 재사용만, 침범 0.
- terminal-data-download: 가격 OHLCV CSV, 공존(본문 주석행 금지 함정 공유).
- viewer `DataDownloadMenu`: 그대로, 격상은 "나중".
