# 03 · Tier 2 — CF Worker parquet→CSV 온더플라이 (실측 게이트)

> 회사당 flat 파일·series 한정. CLAUDE.md 런타임-불가 실측→승인 규칙 정합 — 회사파일 CF 실측 후 착수.

## 정신

Cloudflare Worker 가 요청 시점에 HF parquet 를 hyparquet 로 디코드해 CSV/TSV 로 흘려보낸다. **CSV 사본을 HF 에 굽지 않는다**(no-build). Excel·Google Sheets 가 이 URL 을 라이브로 빨아들인다.

## 적용 범위 = 회사당 flat 파일·series 한정

CF Worker 는 128MB/CPU 한도가 있다. parquet 전량 디코드 비용이 그 안에 들어가는 파일만 Tier2 변환 대상:

- **Tier2 가능(flat 회사당/series)**: `dart/finance` · `dart/panel` · `dart/report` · `research/brokerage` · `edgar/panel` · `edgar/financeStmt` · `edgar/prices/company` · `edgar/tickers` · `gov/prices/company` · `gov/indices/index` · `macro/fred` · `macro/ecos` · `macro/customs`.
- **Tier2 불가(날짜샤드·대형) → 413 + `tier1Url`**: `krx/prices` · `gov/prices/date` · `gov/indices/date` · `edgar/finance`(벌크) · `dart/scan` · `edgar/meta`. 노출은 하되(Tier1 로) 라이브 URL 은 거부.

날짜샤드에서 한 종목을 원하면 → 회사파일(`gov/prices/company/{code}`)로 라우팅 안내. `filter`/`code` 파라미터를 안 만드는 이유(`request.ts:33-34` filter=read 후 JS prune → 326MB 전량 디코드 OOM) → [00 비범위](00-product-prd.md).

## hfProxy 재사용 범위 vs 신규

기존 `infra/workers/hfProxy/worker.js` 실측:

- `worker.js:19` — "nodejs_compat 불필요(순수 fetch)". **parquet 디코드 전무**. → Tier2 의 hyparquet 디코드 + `nodejs_compat` + WASM 메모리는 **최대 비용 신규 항목**. "형제 라우트 0줄 재사용"은 거짓.
- **재사용(O)**: 403/429/5xx backoff 재시도 · CORS(ALLOW_ORIGIN echo + localhost dev) · path 정규화(`replace(/^\/+/,'')` + `..` strip) · 2층 캐시(206 브라우저캐시 / 전체GET 엣지캐시).
- **신규(X)**: allowlist 게이트 · hyparquet 디코드 · CSV/TSV emit · 셀cap 헤더 신호 · schema footer 프로브.

## 보안 — public allowlist 단일화 (deny-list 폐기)

게이트 = **"정규화된 path 가 빌드타임 emit 한 노출 화이트리스트 dir 중 하나로 시작하지 않으면 404"**. 미포함 = 자동 차단.

### 왜 allowlist 만 안전한가 (실측 근거 — 핵심 제약)

private dir 6종은 `repo` override 가 **없다** → 공개 `dartlab-data` 와 **같은 repo·같은 UPSTREAM**(`worker.js:21`):

| dir | public | repo override | 차단 방법 |
|---|---|---|---|
| `dart/allFilings` | False | 없음 (same repo) | **코드 allowlist 만** |
| `edgar/scan` | False | 없음 (same repo) | **코드 allowlist 만** |
| `dart/stemIndex` | False | 없음 (same repo) | **코드 allowlist 만** |
| `edinet/finance`·`edinet/docs` | False | 없음 (same repo) | **코드 allowlist 만** |
| `ai/knowledge` | False | 없음 (same repo) | **코드 allowlist 만** |
| `original/dart/docs` | False | `dartlab-dart-original` | 미포함 + 토큰 미부여(이중) |
| `news/private/naver*` | False | `dartlab-news-private` | 미포함 + 토큰 미부여(이중) |

토큰 물리차단이 same-repo 6종에 **안 먹는다**. 코드 allowlist 가 유일 방어다 — deny-list 는 "작고 안정" 전제가 코드로 깨져 폐기(news prefix 도 public/private 혼재라 blanket deny 가 공개 RSS 오차단).

### 경로 주입·passthrough 차단

- `{id}` 정규식 `^[A-Za-z0-9._-]+$`(traversal·절대 URL 차단). 워커는 `{고정 repo}/resolve/main/{화이트리스트 dir}/{검증 id}.parquet` 만 조립.
- **hfProxy `/hf/` 무게이트 passthrough(`worker.js:327` 부근) 복제 금지** — 그건 allowlist 전무라 `allFilings`·`edgar/scan` 이 이미 샌다. CSV 워커 변환·schema 라우트엔 allowlist 게이트를 **신규 부착**.
- `schema.json`·`/v1/` 도 동일 allowlist 통과(footer range-read 로 private 스키마/존재 누설 차단).
- UPSTREAM = `dartlab-data` 단일, private repo 토큰 미부여.

## 노출 화이트리스트 = `DATA_RELEASES` → 빌드타임 emit

노출 = `public:True` **이면서** 표형(tabular) downloadable 인 dir 만(`public:True` 전부 아님).

- **포함(18)**: `dart/panel` · `dart/finance` · `dart/report` · `dart/scan` · `research/brokerage` · `edgar/panel` · `edgar/finance` · `edgar/financeStmt` · `edgar/meta` · `edgar/prices/company` · `edgar/tickers` · `krx/prices/company` · `krx/indices` · `gov/prices/company` · `gov/indices/index` · `macro/fred` · `macro/ecos` · `macro/customs`.
- **노출 제외(public:True 지만 표 아님/좀비/nested)**: `dart/contentIndex`(BM25 CSR 검색 인덱스) · `edgar/docs`(deprecated 좀비) · `edgar/sections`(nested `{ticker}/{period}`) · `news/public/**`(nested) · `landing/map`·`landing/dashboards`(JSON asset).

## origins 레지스트리 등록

`ui/packages/runtime/src/data/origins/registry.ts` 에 `newsWorker`/`marketFilingsWorker` 동형(`registry.ts:76-110` 패턴):

```ts
// OriginId 유니온에 'csvWorker' 추가
const CSV_PROXY = ((viteEnv?.VITE_DARTLAB_CSV_PROXY) ?? '').replace(/\/+$/, '');
csvWorker: {
  resolve: (path) => `${CSV_PROXY}/v1/${path}`,
  defaultCache: { scope: 'memory', ttlMs: 60 * MIN, maxEntries: 64 },
  configured: () => Boolean(CSV_PROXY),
}
```

- env 미설정 → `configured()=false` → Tier2 비활성, UI 가 Tier1 만 노출 = dev=퍼블릭 기준 무중단.
- 앱 내 모든 Tier2 URL 생성은 이 origin `resolve` 경유(직접 조립·자체 Map 금지, uiDataWiring 가드 준수).

## drift 가드 (필수)

`tests/audit/csvWorkerAllowlist`(가칭) — Python `DATA_RELEASES`(public 플래그·표형 화이트리스트) ↔ 워커 emit 상수 동기화 CI 검증(drift 0, blocking 권장). 새 public 카테고리는 SSOT 한 줄로 양 티어 자동 노출, 새 private 은 미포함 자동 차단. → [05](05-validation-and-rollback.md).

## 위치

`infra/workers/dataCsv/`(가칭) 신규 워커 권장 — hfProxy 의 무게이트 `/hf` passthrough 와 한 파일 공존은 위험(게이트 격리). 최종 워커 분리/증설 + 도메인 = 운영자 결정 → [06 openDecisions](06-progress-ledger.md).
