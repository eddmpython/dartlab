---
id: operation.dataDownloadCenter
title: 데이터 다운로드 센터 (공개 parquet · 시트·코드 라이브 서빙)
kind: curated
scope: builtin
status: observed
category: operation
purpose: 공개 HF parquet 데이터를 비-python 소비자(구글시트·엑셀·curl·브라우저)가 슬라이스·라이브 API 로 쓰게 하는 서빙 층 운영 SSOT. Tier1 브라우저 직독 다운로드 + Tier2 Cloudflare Worker 온더플라이 CSV/TSV, 런타임 변환은 워커·브라우저 공유(베이크 0). 트리거 '데이터센터', '데이터 다운로드', '라이브 API', 'IMPORTDATA'.
whenToUse:
  - 데이터 다운로드 센터
  - 데이터센터
  - /data
  - 라이브 데이터 API
  - IMPORTDATA
  - 구글시트 데이터
  - 엑셀 parquet
  - CSV API
  - 데이터 슬라이스 다운로드
inputs:
  - 데이터셋 dir (예 dart/finance · gov/prices/company · macro/fred)
  - 종목코드 또는 시리즈 id
  - 변환 종류 (raw · 재무제표 · 주가 보조지표 · 경제지표 보조지표)
outputs:
  - xlsx/csv 다운로드 (Tier1 브라우저)
  - CSV/TSV 라이브 URL (Tier2 워커, 시트·엑셀·Python·curl)
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: limited
knowledgeRefs:
  - engines.dataHub
  - operation.architecture
  - operation.ui
  - runtime.dataAvailabilityCheck
sourceRefs:
  - dartlab://skills/operation.dataDownloadCenter
failureModes:
  - 큰 파일(날짜샤드·panel 본문)을 Tier2 라이브 변환으로 시도 (CF 128MB 초과로 413)
  - private dir 을 노출 대상으로 오인 (public 플래그 SSOT 위반)
  - CSV 사본을 HF 에 굽기 (런타임-SSOT 규칙 위반, 온더플라이만)
forbidden:
  - public 아닌 dir 을 다운로드 센터에 노출
  - 변환 결과를 별도 parquet 로 베이크 (런타임 공유만)
  - 결손을 0 으로 채우기 (honest-gap 빈 셀 유지)
lastUpdated: '2026-07-01'
---

## 역할

데이터 다운로드 센터는 dartlab 공개 데이터(HuggingFace `eddmpython/dartlab-data` 의 parquet)를 python 을 쓰지 않는 소비자가 **슬라이스·라이브**로 가져가게 하는 서빙 층이다. `engines.dataHub`(수집·프리빌드·업로드 파이프라인)의 반대편, 소비 층에 해당한다. 랜딩 `/data` 표면 + Cloudflare Worker `dartlab-data-csv` 로 구성된다.

핵심 원칙: **CSV 사본을 굽지 않는다.** HF parquet 이 SSOT 이고 브라우저·워커가 요청 시점에 직독·변환한다(런타임-SSOT, `operation.architecture`).

## 정신 모델 (거울 URL)

HF parquet 경로를 그대로 비추고 확장자만 바꾼다.

```
HF   …/resolve/main/{dir}/{id}.parquet
API  https://{worker}/v1/{dir}/{id}.{csv|tsv}
```

워커가 아는 유일한 데이터 지식 = `dartlab.core.dataConfig.DATA_RELEASES` 의 `public` 플래그에서 도출한 노출 화이트리스트(`downloadCatalog()`). 새 public·flat·표형 카테고리는 코드 0 으로 자동 노출, private 은 자동 차단된다.

## 2 티어

| 티어 | 백엔드 | 범위 | 방식 |
|---|---|---|---|
| Tier1 브라우저 | 0 | 노출 dir 전부(날짜샤드 포함) | parquet 직독 → xlsx/csv (buildWorkbook·csvExport 재사용) |
| Tier2 워커 | Cloudflare Worker 1개 | 회사·시리즈 flat 파일 | parquet → CSV/TSV 온더플라이 (IMPORTDATA·Power Query) |

Tier2 부적격(날짜샤드·전종목 대형)은 413 + Tier1 안내로 정직하게 떨어뜨린다.

## URL 계약

```
/v1/{dir}/{id}.{csv|tsv}?cols=&tail=&head=&freq=
/v1/{dir}/{id}/schema.json      # footer 만 (cols/tail 추측용)
/v1/                            # 자기기술 카탈로그 (url_syntax·params·datasets)
```

- `cols` 컬럼 투영(출력 순서 겸용) · `tail`/`head` 행 슬라이스 · `freq` 다운샘플(d/w/m/q/y, last-of-period).
- 숫자는 en-US invariant, 결손은 빈 셀(0 대체 금지), 선두 UTF-8 BOM, CRLF. 기본 TSV(한국 Excel 콤마 로케일 회피) + CSV 병행.
- 셀(cols×rows) cap 초과 시 최근행 우선 자동 tail + `X-DartLab-Capped` 헤더 신호(본문 주석행 금지, IMPORTDATA 오염 방지).

## 런타임 변환 (워커·브라우저 공유 SSOT)

raw 슬라이스 외에 런타임 변환 3종을 라이브로 제공한다. 워커가 브라우저와 **동일 변환 함수를 esbuild 번들로 공유**한다(베이크 0, 런타임-SSOT).

| 변환 | 함수 | 입력 dir | URL |
|---|---|---|---|
| 재무제표 | `financeSource.bundleFromRows` | dart/finance(KR)·edgar/financeStmt(US) | `/v1/finance/{code}.csv?stmt=IS&freq=quarter` |
| 주가 보조지표 | `priceIndicators.priceWithIndicators` | gov/prices/company(KR)·edgar/prices/company(US) | `/v1/priceInd/{code}.csv` |
| 경제지표·지수 보조지표 | `priceIndicators.valueWithIndicators` | macro/fred·ecos·customs·gov/indices/index | `/v1/valueInd/{dir}/{id}.csv` |

- KR/US 는 code 모양으로 자동 분기한다(6자리=KR, 그 외=US 티커, `resolveMarket` SSOT). 재무·주가 동일 규칙.
- 재무제표 stmt = IS/BS/CF/CIS/SCE/RATIOS, freq = quarter/annual/ttm.
- 보조지표는 MA5/20/60·RSI14·MACD·볼린저(+주가는 거래량이평·ATR). 지표는 시간순 전제라 date 오름차순 정렬 후 계산한다.

## 보안 (public allowlist SSOT)

노출 경계 = `DATA_RELEASES` 의 `public` 플래그 단일 SSOT. private dir 은 공개 repo 와 same-repo 라 토큰 차단이 안 먹으므로 **코드 게이트(allowlist)가 유일 방어선**이다. `{id}` 정규식(`유니코드 글자/숫자/._-`)으로 경로주입·절대 URL passthrough·`..` 를 차단한다.

## 메모리 예산 (413 게이트)

CF Worker 는 128MB 고정이라 큰 파일은 못 올린다. parquet footer 의 컬럼별 압축해제 크기 합으로 **디코드 전에** 예산을 검사해, 초과하면 413 으로 Tier1 을 안내한다(killList 패턴). 실측 RSS: gov/prices/company 70MB · dart/finance 119MB · macro/fred observations 210MB · dart/panel 본문(contentRaw) 927MB. `cols` 투영이 탈출구(panel 본문 제외 시 927 → 80MB). 회사·시리즈 flat 파일은 작아 라이브, 날짜샤드·전종목·본문 거대분은 Tier1.

## 진입점

- 사용자: 랜딩 `/data` (데이터셋 미리보기·다운로드[가공 + 원본 parquet]·HF 파일브라우저 탐색·라이브 API 스니펫 시트/엑셀/Python/curl).
- 워커 자기기술: `/v1/` 카탈로그 · `/v1/{dir}/{id}/schema.json`.
- 코드: `infra/workers/dataCsv/`(worker.js · allowlist.js · dist esbuild 번들) · `landing/src/routes/data/+page.svelte`.

## 검증

- drift 가드: `tests/core/test_download_catalog.py::test_worker_allowlist_in_sync` (Python `downloadCatalog()` ↔ 워커 allowlist 동기 강제).
- UI: svelte-check 0 에러 + Playwright(다운로드 실파일·라이브 API 헤더).
- 워커: `infra/workers/dataCsv` esbuild dist → wrangler deploy(비대화식, `.env` 토큰). 로컬 증명은 `node dev.mjs`.
- 상세 설계·결정 로그·완료 기록(현역 런북): `mainPlan/_done/data-download-center/`.
