---
id: operation.dataLineage
title: Data Lineage — raw → parquet → axis 매핑 SSOT
kind: curated
scope: builtin
status: drafted
category: operation
purpose: dartlab 데이터 lineage SSOT — raw source (DART/EDGAR/KRX) → parquet (`data/{provider}/`) → engine axis 매핑 표. 데이터 변경 시 영향 범위 추적 + schema migration 사전 검토.
whenToUse:
  - data lineage
  - 데이터 흐름
  - raw to parquet
  - schema migration
  - 영향 범위
inputs:
  - source 또는 parquet 또는 axis 식별자
outputs:
  - upstream / downstream 매핑
  - 영향 범위 list
toolRefs: []
knowledgeRefs:
  - operation.architecture
  - operation.docsBuilderRefactor
sourceRefs:
  - dartlab://skills/operation.dataLineage
requiredEvidence:
  - skillRef
  - executionRef
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: limited
  webAi:
    status: limited
  pyodide:
    status: limited
linkedSkills:
  - operation.architecture
  - operation.docsBuilderRefactor
---

## 4 layer

```
L0: raw source
   원본 백업 store (data/original/, gather.original, 로컬 백업·HF 미공개·.gitignore) — 가공 0 ground truth
     dart/docs/{code}/{rcept}.zip (정기, panel/sections/refScan 입력)
     dart/allFilings 는 월별 parquet 가 SSOT (원본 zip 저장 안 함)
     EDGAR full-submission text 는 저장하지 않고 SEC 에서 메모리 fetch 후 panel build 에 즉시 전달
   EDGAR companyfacts/bulk XBRL (HF dataset eddmpython/dartlab-data/edgar/)
   KRX OpenAPI (HF dataset eddmpython/dartlab-data/krx/)
   ↓
L1: parquet (정규화)
   data/dart/finance/*.parquet  (BS/IS/CF/CIS/SCE × snake_id)
   data/dart/panel/{code}.parquet (contentRaw/content 본문; DART read SSOT)
   data/edgar/finance/*.parquet
   data/edgar/panel/{ticker}.parquet (보드 + native payload 단일 artifact)
   data/gov/prices/date/*.parquet (공공데이터포털 일별 전종목 — date/company 샤딩)
   ↓
L2: in-memory
   Company.panel(...) — BoundedCache
   scan(...) — heap 가드 maxTargets=5
   ↓
L3: axis / recipe
   engines.* (15 카테고리 × N axis)
   recipes.* (220+ recipe)
```

> **L1 = ETL 스테이지 분할** (수집 일원화). raw source → parquet 사이의 L1 은 두 책임으로
> 갈린다 — **gather = Extract** (DART/EDGAR 네트워크 fetch → raw zip/json/bytes 또는 메모리 text record; client·키풀·
> submissions/facts/docs/bulk/universe/FTS 전담), **providers = Transform+Load** (raw → parquet
> build + parquet → DataFrame read; HTTP 클라이언트 import 0). providers build 가 fetch 를
> 트리거해야 하면 core DIP seam(`core.dartClient`/`edgarClient` 등) 으로 위임한다. 상세
> [operation.architecture](dartlab://skills/operation.architecture) L1 표 + `test_providers_no_network`.

> **수집 오케스트레이션 SSOT = `dartlab.pipeline`** (L4 sink). fetch(gather)→build(providers)
> →upload(HF) 조합을 in-library 로 모아 로컬 `dartlab sync [stage]` 와 CI
> `python -m dartlab.pipeline <stage>` 가 동일 진입점을 호출한다. category→stage 레지스트리
> (finance/report/docs/sections/panel/krx/macro/news/edgar…). panel→HF 는 refDf 부재 시
> design-in graceful skip(게이트 없음). 옛 `.github/scripts/sync/*` 는 점진 흡수.

## 매핑 표

| source | provider | parquet | axis 영향 |
|---|---|---|---|
| DART finance | dart/ | bs/is/cf/cis/sce | analysis 22 + credit + quant 일부 |
| DART panel text | dart/ | panel contentRaw/content | search + panel deep dive |
| DART panel | dart/ | panel/{code}/{period} (14-col) + _index + _label | 공시 수평화 보드 (회사내·회사간) |
| EDGAR companyfacts XBRL | edgar/ | finance/* | edgar finance 대문자 topic |
| EDGAR full-submission text | edgar/ | panel/{ticker}.parquet | 공시 수평화 보드 + 소문자 native 재무 키 |
| KR OHLCV (공공데이터포털) | gov/ | prices/date/{YYYY} + prices/company/{code} | quant 30+ + scan + 차트 |
| KR 지수 (공공데이터포털) | gov/ | indices/date/{YYYY} + indices/index/{key} | benchmarkMap + macro |
| KRX events | krx/ | events/* | _adjustPrice (split/dividend) |
| 한은 macro | macro/ | (외부 API) | macro 12 axis |

### panel 수집 2-트랙 (공시 수평화)

```
(A) 로컬 zip 트랙 — 전수·재빌드 (양식 era 변경·택소노미 갱신 시 SSOT)
    DART API → data/original/dart/docs/{code}/*.zip (로컬 전용·HF skip)
             → buildPanel(gather, lxml/zip) → data/dart/panel/{code}/{period}.parquet

(B) online 1패스 트랙 — 증분·신규분기 (디스크 zip 0)
    DART filings rcept → streamZipBytes(gather, 메모리) → buildPanelFromStream(gather)
                       → data/dart/panel/{code}/{period}.parquet   (A 와 바이트 동형)

공통: 정렬키 = core.panel.canonicalKey (native ACLASS scope-strip, 손 매핑 0)
      → buildIndex(_index.parquet) + buildLabel(_label.parquet) → HF push(SYNC_CATEGORY=panel)
      → providers Panel/compare read (scan_parquet, 콜드 <1s)
```

> zip 원본은 local-only(HF skip, 3층 가드). online(B)은 zip 을 디스크에 만들지조차 않으므로
> refScan(zip 전수 스캔) 불가 → 항상 HF seed ``panelXbrlRef`` 를 refDf 로 주입. 전수 재빌드·
> 양식 era 변경 대응은 영구히 zip 트랙(A) 책임.

### EDGAR panel 수집 (US)

```
SEC daily-index/submissions → full-submission text 메모리 fetch
                            → providers.edgar.panel.build
                            → data/edgar/panel/{ticker}.parquet
```

EDGAR 는 `data/original/edgar/docs/*.txt` 를 만들지 않는다. native 재무 cell 도 별도
`panelCell` artifact 없이 panel row `contentRaw` payload 안에 보존하고 read-time 에 분해한다.
소문자 `c.panel("is"/"bs"/"cf"/"ratios")` 는 이 payload 를 읽는 native 경로이고,
대문자 `c.panel("IS"/"BS"/"CF"/"RATIOS")` 는 companyfacts finance 경로다.

## 갱신 절차

1. source 변경 → L1 parquet rebuild (sync workflow).
2. parquet schema 변경 → migration 절차 (별 spec).
3. L2 cache invalidation (`BoundedCache.clear`).
4. L3 axis 영향 확인 → 본 매핑 표 갱신.
5. **panel 양식 era 변경** → zip 트랙(A) 전수 재빌드. **택소노미(ACLASS) 갱신** → canonicalKey
   규칙 검토 + refScan→HF seed `panelXbrlRef` 교체(online B 는 seed ref 만 갱신).

## 강행 룰

1. lineage 표 source ↔ parquet ↔ axis 1:N 매핑 명시.
2. 새 source 추가 → 본 spec 동시 갱신.
3. schema migration → backward compat 또는 명시 break.

## 기본 검증

- 모든 parquet 의 source / provider 추적 가능.
- 모든 axis 의 input parquet 추적 가능.
- migration 시 영향 범위 사전 명시.
