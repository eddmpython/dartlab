# dataCsv — DartLab 라이브 데이터 API

HF parquet(공동작업대 SSOT)를 요청 시점에 **CSV/TSV 로 온더플라이 디코드**한다. 구글시트
`=IMPORTDATA(...)` · 엑셀 Power Query(데이터→웹에서)가 dartlab 데이터를 **런타임 소스로 라이브**
사용한다. CSV 사본을 HF 에 굽지 않는다(no-build, SSOT 직독). 계약 = `mainPlan/data-download-center`
01(API)·03(워커)·04(스프레드시트).

```
https://{host}/v1/{dir}/{id}.{csv|tsv}?cols=&tail=&head=&freq=
```

## 엔드포인트

| 경로 | 동작 |
|---|---|
| `GET /v1/` | 자기기술 카탈로그(노출 dir·tier2 여부·예시 경로) |
| `GET /v1/{dir}/{id}.{csv\|tsv}` | parquet → CSV/TSV. BOM·en-US 숫자·결손=빈셀 |
| `GET /v1/{dir}/{id}/schema.json` | footer 만 → `{columns,rows,rowGroups}` (cols/tail 추측용) |

파라미터: `cols`(컬럼 투영·출력순서) · `tail`(최근 N행) · `head`(최초 N행, tail 과 배타) ·
`freq`(다운샘플 d\|w\|m\|q\|y, last-of-period). 확장자가 포맷 단일 결정(`.csv`=Sheets, `.tsv`=Excel 한국 로케일).

## 호스트 = Cloudflare Worker — 메모리 실측 게이트 (PRD 05 §3)

호스트는 CF Worker(PRD 03·05·06). 디코드 메모리 = parquet 압축해제 비용. 본 워커는 footer 의 컬럼별
`total_uncompressed_size` 합 × 팽창계수로 **디코드 전에** 예산(`MAX_DECODE_BYTES`)을 검사해 초과면
413(+`cols` 안내) — CF 128MB 에 안 드는 파일은 PRD killList 패턴대로 **413→Tier1**. 실측 RSS:

| 데이터셋 | 전량 디코드 RSS | CF 128MB 메모리 |
|---|---|---|
| `gov/prices/company/{code}` (4천행) | ~70MB | ✅ |
| `gov/indices/index/{name}`·`research/brokerage/{YYYYMM}` | ~수MB | ✅ |
| `dart/finance/{code}` (1.3만행) | ~119MB | ⚠ 아슬 |
| `macro/fred/{seriesId}` (observations 33만행 전량 디코드) | ~210MB | ❌ → 413 |
| `dart/panel/{code}` (본문 포함) | ~927MB | ❌ → 413 |
| `dart/panel/{code}?cols=`(본문 제외) | ~30~80MB | ✅ (cols 투영) |

- `cols` 투영이 메모리 탈출구 — panel 본문(`contentRaw`) 제외 시 927→80MB(실측).
- **남은 게이트 = PRD openDecision #2 (CF CPU 플랜)**. 무료 CF=10ms CPU·유료=50ms~30s. parquet 디코드
  CPU 가 무료 10ms 안에 드는지는 **CF 배포 후 실측 → 운영자 보고**(PRD 05 §3). 메모리는 위 표대로 확정.

예산 추정 = 텍스트 payload(컬럼 압축해제×`DECODE_EXPANSION`) + 셀 객체 오버헤드(행수×컬럼수×`CELL_OBJ`)
두 항 — 전자가 panel(텍스트 거대), 후자가 fred(행 多 작음)를 잡는다. env(`MAX_DECODE_BYTES`·`MAX_DECODE_ROWS`·
`DECODE_EXPANSION`·`CELL_OBJ`·`CELL_CAP`)로 한 줄 조절.

## 보안

게이트 = `allowlist.js`(public·flat·표형 dir 단일). private 6종은 공개 `dartlab-data` 와 same-repo 라
토큰 차단이 안 먹는다 → **이 코드 allowlist 가 유일 방어**(미포함 dir = 404, 존재 누설 0). `{id}` 는
유니코드 글자/숫자/`._-` 만 허용(`/`·`..` 차단). SSOT drift 는 `tests/core/test_download_catalog.py`
(`test_worker_allowlist_in_sync`)가 강제.

## 로컬 개발/증명

```bash
cd infra/workers/dataCsv && npm install
npm run dev            # → http://localhost:8787/v1/
curl "http://localhost:8787/v1/gov/prices/company/005930.csv?cols=date,close&tail=10"
```

node 는 메모리가 충분해 전 카탈로그를 디코드한다(배포 호스트 메모리만 위 표대로 다름).

## 배포 — Cloudflare Worker (PRD 03·05·06)

```bash
npm run deploy   # wrangler deploy → *.workers.dev. CF 무료 128MB. 큰 파일은 413→Tier1.
```

배포 후 CF CPU 실측(무료 10ms vs 유료 플랜) → 운영자 보고(PRD 05 §3). UI 배선:
`ui/.../data/origins/registry.ts` 에 `csvWorker` origin 등록 + `VITE_DARTLAB_CSV_PROXY` env
(03-tier2-live-worker §origins). env 미설정 = Tier2 비활성(UI 가 Tier1 만 노출, dev 무중단).

## 스프레드시트 사용

| 원하는 것 | 방법 |
|---|---|
| 구글시트 라이브 | `=IMPORTDATA("https://{host}/v1/dart/finance/005930.csv?cols=bsns_year,account_nm,thstrm_amount")` (~1시간 자동 새로고침) |
| 엑셀 라이브 | 데이터→웹에서→`.tsv` URL→Text/CSV 커넥터→"모두 새로 고침" |
| 한 번 받기 | 데이터 센터 Tier1 다운로드(`.xlsx`/`.csv`) |

`IMPORTDATA` 는 ~5만셀/호출 한계 → 워커 `CELL_CAP`(기본 45,000)이 미지정 호출을 자동 tail+헤더 신호
(`X-DartLab-Capped`)로 절단. 본문 주석행 0(IMPORTDATA 오염 회피).

## macro 시계열 — {id}=seriesId (단일 시리즈)

`macro/fred·ecos·customs` 는 per-series 파일이 아니라 `observations.parquet` **단일 파일**(seriesId 컬럼으로
전 시리즈 1파일)이다. 사용자는 한 시리즈를 원하므로 워커가 `{id}=seriesId` 로 보고 observations 를 읽어
그 시리즈만 필터해 돌려준다(날짜샤드의 decode-후-prune OOM 과 달리 어차피 1파일이라 안전):

```
=IMPORTDATA("https://{host}/v1/macro/fred/DGS10.csv?cols=date,value")     # 10년물 금리 한 시리즈
GET /v1/macro/fred/manifest.csv                                            # 어떤 seriesId 가 있는지 카탈로그
```

⚠ 단, observations 전량(fred 33만행 ~210MB)을 디코드해 필터하므로 **CF 128MB 메모리에 안 든다 → CF 에선
413→Tier1**. macro 단일시리즈를 라이브로 풀려면 observations 를 시리즈별 파일로 쪼개는 sync 측 재구성
(build 변경, 별도 토론·승인)이 필요 — PRD-gap. 현재는 회사 flat 파일이 CF 라이브의 핵심. 없는 seriesId = 404.

## 알려진 follow-up

- 날짜샤드(`gov/prices/date` 등)·벌크(`krx/prices` 등)는 413 → Tier1. CF 한도 통과 시 후속(spec Phase 5).
