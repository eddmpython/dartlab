# 01 · API 계약 — URL·파라미터·포맷·에러·자기기술

> 구현자 SSOT. 이 문서만 보고 워커·surface 를 짤 수준으로 구체화. 모호함 0.

## 1. URL 문법

```
https://{DATA_WORKER_HOST}/v1/{dir}/{id}.{ext}[?params]
```

- `{DATA_WORKER_HOST}` — 운영자 결정 placeholder(예 `dartlab-data.<sub>.workers.dev`). 실재 도메인 환각 금지 → [06 openDecisions](06-progress-ledger.md).
- `{dir}` — `DATA_RELEASES` 의 `dir` 값 **그대로**(예 `dart/finance`, `macro/fred`, `gov/prices/company`). HF 경로의 거울.
- `{id}` — parquet 파일 stem. **정규식 가드 `^[A-Za-z0-9._-]+$`**(path traversal·절대 URL passthrough 차단). 6자리 종목코드 / ticker / series 명 / 날짜.
- `{ext}` — `csv` | `tsv`. **확장자가 포맷을 단일 결정**(`format`/`sep` 쿼리 override 채널 없음).

워커는 결코 임의 HF URL 을 프록시하지 않는다 — `{고정 repo}/resolve/main/{화이트리스트 dir}/{검증 id}.parquet` 만 조립한다.

### 추측가능성 입증 (docs 0)

| 아는 것 | 추측한 URL |
|---|---|
| `…/resolve/main/dart/finance/005930.parquet` | `https://{host}/v1/dart/finance/005930.tsv` |
| FRED 시계열 DGS10 | `https://{host}/v1/macro/fred/DGS10.tsv` |
| gov 회사 OHLCV 최근 250행 | `https://{host}/v1/gov/prices/company/005930.csv?tail=250` |
| EDGAR 재무 특정 컬럼 | `https://{host}/v1/edgar/financeStmt/AAPL.tsv?cols=period,account,value` |

차단 예(404, 존재 누설 회피): `/v1/dart/allFilings/…` · `/v1/edgar/scan/…` · `/v1/original/…` · `/v1/dart/stemIndex/…`

## 2. 쿼리 파라미터 (MVP 최소집합 — 4개)

| 이름 | 의미 | pushdown | 예시 |
|---|---|---|---|
| `cols` | 컬럼 투영(쉼표구분, 출력 순서 결정). 미존재 컬럼 = 400 + 가용 목록 | hyparquet `columns` (진짜) | `?cols=date,close,volume` |
| `tail` | 최근 N행 (시계열·panel 기본 친화) | `rowStart`/`rowEnd` (진짜 prune) | `?tail=250` |
| `head` | 최초 N행 (`tail` 과 상호배타, 둘 다 = 400) | `rowStart`/`rowEnd` (진짜 prune) | `?head=500` |
| `freq` | 시계열 다운샘플 `d`\|`w`\|`m`\|`q`\|`y`, **last-of-period 단일 규칙**. 미지정 = 원본 빈도 | read 후 집계 | `?freq=m` |

미지정 시 — 회사당 작은 파일은 통째, 셀cap 초과 시 `tail` 자동 적용 + 절단 신호(§4).

**제외 파라미터(killList, 근거 → [00 비범위](00-product-prd.md))**: `filter`/`code`, `from`/`to`, `shape=wide`, `limit`/`offset`/pagination, `format`/`sep`.

## 3. 응답 포맷

- **TSV (기본 권장, `.tsv`)** — `Content-Type: text/tab-separated-values; charset=utf-8`. **UTF-8 BOM(`EF BB BF`) 선두 필수**. 탭 구분 = 한국 Excel 로케일(소수점 콤마·세미콜론 list-separator) 충돌 0.
- **CSV (`.csv`)** — `Content-Type: text/csv; charset=utf-8` + BOM. RFC4180 인용(`csvExport.ts` `escapeCell` 거울: `["\n\r,]` 있으면 `"`로 감싸고 `"`→`""`). Google Sheets IMPORTDATA 친화.
- **공통 헤더** — `Access-Control-Allow-Origin: *`(public 데이터) · `Cache-Control: public, max-age=3600`(Sheets ~1h 캐시 정렬, parquet 불변→변환결과 사실상 불변) · `Content-Disposition: attachment; filename="{id}.{ext}"`.
- **숫자 정직성** — parquet 네이티브 타입 보존. 숫자 컬럼은 따옴표 없는 raw 숫자 + **en-US invariant(점 소수, 천단위 구분자 0)** → Excel/Sheets 가 진짜 Number 파싱. 콤마·괄호음수·△ 정규화는 sync ETL 책임(원천이 이미 numeric), 전송층 책임 아님.
- **결손 = 빈 셀**(honest-gap, `buildWorkbook` null→`''` 규약 일치). **0 대체 절대 금지**.

## 4. 크기 한도 신호 (silent 절단 0)

- cap 단위 = **셀(cols × rows)**, 행 아님. IMPORTDATA 한도가 ~50,000셀이라 17-col 파일에서 5,000행 = 85,000셀로 초과한다. 워커 상수 `CELL_CAP`(예 45,000), **카테고리별 분기 0**.
- 미지정 + 셀cap 초과 시 — rows 자동 축소(최근 행 우선 = tail) + 신호.
- **신호 채널 = HTTP 헤더 전용**:
  - `X-DartLab-Capped: true`
  - `X-DartLab-Total-Rows: {n}`
  - `X-DartLab-Cells-Returned: {n}`
  - `X-DartLab-Hint: add ?tail=… | ?cols=… | ?freq=m to widen`
- **CSV/TSV 본문 주석행 금지** — IMPORTDATA 가 데이터로 파싱·숫자열 오염.
- 헤더를 IMPORTDATA 가 못 보는 한계는 **링크빌더가 메운다** — 받을 셀수/전체/넓히는 파라미터를 미리 계산해 화면 표시 → [02](02-tier1-download.md), [04](04-spreadsheet-integration.md).

## 5. 자기기술 엔드포인트 (docs 없이 탐색, 2개)

1. **`GET /v1/`** (또는 `/v1/index.json`) → 카탈로그. 노출 화이트리스트 각 엔트리 `{dir, label, shardKind: "company"|"series", examplePath, tier2: true|false}` 배열 + URL 문법 한 줄. 워커 빌드타임 **정적 상수**(`DATA_RELEASES` 미러, 데이터 아닌 메타라 no-build 무관).
2. **`GET /v1/{dir}/{id}/schema.json`** → 그 파일 parquet footer 만 range-read → `{columns:[{name,type}], rows, rowGroups}`. `cols`/`tail` 추측용. **반드시 동일 allowlist 게이트 통과**(private 스키마·존재 누설 차단). 미매치 = 404.
- 모든 응답에 `Link: <…/v1/>; rel="index"` 헤더.
- **제외(MVP)**: `/v1/{dir}/index.json`(HF tree 파일 열거) — `dart/panel` ~9만·gdelt ~6만 파일 dir 에서 429/비용. 후속.

## 6. 에러 모델

| 상태 | 조건 | 바디 |
|---|---|---|
| 400 | `cols` 미존재 컬럼 / `head`+`tail` 동시 / 잘못된 `freq` | `{error, available_columns?:[...], hint}` JSON |
| 404 | dir 이 노출 화이트리스트 미매치 (private·미존재 **둘 다**) | `not found` (존재 누설 회피, 차이 노출 0) |
| 405 | GET/HEAD/OPTIONS 외 메서드 | — |
| 413 | Tier2 대상 외(날짜샤드·nested) URL 호출 | `{error:"too large for live API — use browser download (Tier1) or company file", hint, tier1Url}` JSON |
| 502/503 | HF upstream 403/429/5xx (재시도 후) | hfProxy retry 패턴 거울 |
