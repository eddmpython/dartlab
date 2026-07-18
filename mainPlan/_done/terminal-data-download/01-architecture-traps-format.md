# 01 · 아키텍처 · 다섯 함정 · 형식 결정

## 아키텍처 — render 진실 직렬화

**핵심**: 차트가 *실제로 그리는 봉*을 내보낸다 = `chart.getDataList()`.

- klinecharts v9 인스턴스는 `PriceChart.svelte:67 let chart = $state<any>(null)` 로 컴포넌트 스코프에 있고 `:332 mod.init(node)` 로 생성, `:464 c.applyNewData(out.map(toK), ...)` 로 봉을 적용한다. v9 typings: `getDataList(): KLineData[]`, `KLineData = {timestamp:number, open, high, low, close, volume?, turnover?}`.
- `getDataList()` 는 (a) `priceSource` LRU eviction 과 무관하게 차트 자신의 적용 배열을 들고 있고, (b) 리플레이 절단을 반영하고, (c) 현재 tf(`ctl.tf` D/W/M/Q/Y 집계)와 변환(`ctl.adj` 수정주가 / `ctl.candleStyle==='ha'`)을 반영한다.
- **CRITICAL**: `KLineData` 에는 `.t` 가 없고 `timestamp` 가 ms-epoch 다 → 직렬화기는 `timestamp → YYYYMMDD` 재정형(=`toMs(:133)` 역) 필수. 봉이 `Candle.t` 를 들고 있다고 가정 금지.
- **재사용**: `rt`(`:64 useDartLabRuntime()`, 재호출 금지), `srcText()(:1161)`, `onSnapshot` 배선(`:1178 ChartMenus`/`:1238 ChartRibbon`). 버튼은 `snapshot()(:1166)` 을 *배치·출처 문자열*에서 미러하되 **파일명 날짜 출처에서 갈린다**(아래 함정 2).
- **SSOT 청결**: origin URL 을 만들지 않고 re-fetch 도 없다 — CSV 는 순수 메모리 차트 객체에서 만든다. 그래서 데이터-워크벤치 SSOT 를 위반하지 않는다(ViewerStudio parquet passthrough·`panelLoad.ts` 의 raw hfUrl 우회와 *다르다*).
- 실제 규모: 신규 직렬화기 ~18줄 + 자식당 버튼 1개 + 게이트. 퍼블릭 surface·백엔드 0·라이브러리 0(BOM 작성기 재사용).

## 다섯 함정 (순진한 구현이 빠짐 — 전부 해소·테스트)

### 함정 1 — 백필 절단 (body) · FATAL

`displaySeries()`/`loaded()`/`candles` prop 직렬화는 *무성 절단*을 낳는다. 메커니즘(검증):

- 정상 경로의 차트 데이터는 `seedCandles`(`priceSource.ts:118` — "gov 회사별 parquet 전체이력")로 전체 이력이 캐시·prop 에 심긴다. 2년 슬라이스(`loadInitialOHLCV:93`, 현재+직전 연도)는 *회사 파일 부재/레거시 폴백*이지 정상 경로가 아니다.
- 그러나 좌측 팬/MAX 기간 백필(`loadOlderYear`, `priceSource.ts:127-138`)은 더 오래된 연도를 `rec.candles = mergeDedup(rows, rec.candles)`(`:134`)로 **캐시·차트에만** 더하고 **`candles` prop 은 갱신하지 않는다**. → 백필 후 차트(`getDataList`)는 prop 보다 *더 많이* 들고 있다.
- 추가로 `priceSource` 는 `CACHE_CAP=16`(`:18`, `setCache` 오래된 항목 제거 `:21-24`) LRU 라 다수 회사 탐색 시 캐시가 갈리지만, render 진실은 캐시·prop 둘 다와 분리된 *차트 자신의 적용 배열*이다.

**해소**: `chart.getDataList()` 직렬화(render 진실), `loaded()`/`displaySeries()`/`candles` prop 절대 금지.
**테스트**: 회사 로드 → MAX 기간/좌측 팬 백필로 `getDataList().length > candles.length` 유발 → 내보낸 행 수 == `getDataList().length` 단언. (주의: "17개사 LRU eviction" 단독 테스트는 회사 재진입 시 재-seed 로 prop/getDataList 가 다시 수렴해 *divergence 를 재현 못 하므로* 버그 직렬화기에도 PASS 한다 — 반드시 백필 divergence 를 유발하는 테스트라야 함정을 잡는다.)

### 함정 2 — 파일명 절단 (filename) · FATAL

`snapshot()(:1167)` 은 ymd 를 `candles[candles.length-1].t`(= prop)에서 도출한다. CSV 파일명이 이를 재사용하면 백필/eviction 후 prop 마지막 날짜(예: `_20230401_`)가 body 마지막 행(예: 2026, `getDataList` 유래)과 모순 — 내용은 옳은데 3년 묵은 날짜로 *오라벨*된 같은 절단 거짓.

**해소**: 파일명 `lastYmd` 를 직렬화기가 `getDataList()` *마지막 봉*에서 도출(`bars[last].timestamp` ms→YYYYMMDD). `snapshot()` ymd 재사용 금지.
**테스트**: 파일명 날짜 == body 마지막 행 날짜 == `getDataList` 마지막 봉.

### 함정 3 — index 잘못된 출처표시

`subject==='index'` 일 때 `CenterStack.svelte`(`ui/packages/surfaces/src/terminal/panels/CenterStack.svelte`)가 `rt.index.series` 를 *같은 `candles` prop* 에 싣는다(PriceChart 마운트 `:477`). 그래서 `getDataList()` 는 *비어 있지 않은 전체 지수 시계열*을 반환 — CSV 가 생성되지만 `GOV_ATTRIBUTION`(`contracts/price.ts:23`, KRX 주가 출처)으로 *지수 위에* 오라벨된다.

**해소**: 빈값이 아니라 **명시 `subject!=='index'` 게이트**(출처 불일치 제외). index 데이터는 prop 으로 실제로 존재하므로 "빈 CSV 라서 안 됨"이 아니라 "출처 불일치라서 막음"이 맞는 이유.
**테스트**: index 차트 + 비어 있지 않은 `rt.index.series` → 버튼 *미렌더*.

### 함정 4 — Heikin-Ashi 합성봉 + 리플레이 절단 (두 fork) · 확정 = DISABLE

- (a) HA 모드(`ctl.candleStyle==='ha'`)에서 `getDataList()` 봉은 *합성*이다 — 평범한 OHLCV 로 내보내면 미묘한 거짓(라벨은 pandas 에서 보이지 않아 오용 유발).
- (b) 리플레이(`ctl.replay.on`) 중 reapply 가 view 를 리플레이 커서까지 절단하므로 `getDataList()` 는 컷까지만 반환 — 리플레이 중 클릭은 *무성 절단 파일*(함정 1 류).

**확정 결정(v7, plan-deep 게이트 — 미결 출하 금지)**: 둘 다 **DISABLE**.
- HA: `ctl.candleStyle==='ha'` 면 「표(CSV)」 비활성(합성봉을 OHLCV 로 파는 것은 데이터 거짓; 보이지 않는 라벨로 막느니 끈다).
- 리플레이: `ctl.replay.on` 이면 비활성(리플레이 중 반쪽 시계열 = 부분 export FATAL 류; 사용자는 리플레이를 빠져나와 다시 내보내면 된다).
- 두 "disable" 결정은 테스트도 단일 "버튼 비활성" 단언으로 수축시킨다.
**테스트**: HA 모드 → 비활성; 리플레이 ON → 비활성.

### 함정 5 — 거래대금 1e8 단위 거짓

`priceSource.ts:57` 은 `tv = num(ACC_TRDVAL)` 로 gov parquet 의 `ACC_TRDVAL`(원, 사실상 매 거래일 *채워짐* — "자주 null"은 거짓)을 그대로 담는다. 그러나 차트 봉 매핑(`toK`)이 만/억/조 축을 위해 turnover 를 억(/1e8)으로 *사전 스케일*하므로, `getDataList()` 봉은 거래대금을 이미 1e8 로 나눈 값을 들고 있다. 봉의 turnover 를 그대로 CSV 컬럼에 쓰면 억-단위를 원으로 오라벨한 단위 거짓.

**해소**: 기본 **OHLCV-only, turnover 생략** — 이유는 "자주 null"이 아니라 *getDataList 봉이 1e8 사전나눗셈을 들고 있어서*. 후일 필요하면 `거래대금(억원)` 명시 단위 라벨 + `봉.turnover*1e8 == 원본 ACC_TRDVAL` 왕복 테스트로만.

## 형식 결정

- **컬럼**: `t,o,h,l,c,v` (getDataList 봉 → `Candle` 형태 `contracts/price.ts:4` 재정형).
- **optional 컬럼**: 기본 OHLCV-only. `r`(수정주가 등락률)은 사용자 지표가 아니고 getDataList 봉에 없음. `tv`(거래대금)는 함정 5 로 생략.
- **결손**: null 거래량 셀 → 빈셀(`csvExport.ts escapeCell:13` 이 null/undefined 를 `''` 반환), **0 절대 금지**.
- **timeframe**: `getDataList()` 가 `ctl.tf`(D/W/M/Q/Y) 반영 — 그대로("보는 것 export"), 파일명에 tf 인코딩.
- **출처**: 데이터-only CSV, `#` 선두 주석행 금지(pandas 가 `#` 를 데이터로 취급, Excel 이 컬럼 이동, 이스케이프 안 된 콤마가 유령 컬럼 분리). `GOV_ATTRIBUTION`(`price.ts:23`)은 파일명 + 화면 `srcText()` 주석으로(stockanalysis/Koyfin 패턴).
- **파일명**: `dartlab_{code}_{lastYmdFromGetDataList}_{tf}{_adj?}.csv` (HA/리플레이는 비활성이라 토큰 불요).

## 재사용 자산

| 자산 | 위치 | 용도 |
|---|---|---|
| `chart.getDataList()` | `PriceChart.svelte:67/:464` (klinecharts v9) | render 진실 봉 |
| `rt = useDartLabRuntime()` | `PriceChart.svelte:64` | 재사용(재호출 금지) |
| `srcText()` | `PriceChart.svelte:1161` (수정주가/HA/macro 주석 합성, `:1164` `· 수정주가`) | 출처 주석 |
| `onSnapshot` prop | `PriceChart.svelte:1178`(ChartMenus)/`:1238`(ChartRibbon) | 버튼 배선 |
| `GOV_ATTRIBUTION` + `Candle` | `ui/packages/contracts/src/price.ts:23 / :4` | 출처 상수·컬럼 형태 |
| `toCsv(columns, records)` + `downloadCsv` | `ui/packages/surfaces/src/scan/csvExport.ts:27 / :36` (BOM `:10`, 이스케이프 `:12`, null→`''` `:13`) | 유일 작성기(재사용) |
| `toMs` | `PriceChart.svelte:133` | ms-epoch↔YYYYMMDD 역변환 |

## 경계 · SSOT 청결

table-export(공시 테이블→.xlsx, `mainPlan/table-export`)·데이터-워크벤치 SSOT 와 **형제·비침범**. 본 PRD 는 PriceChart + 자식 크롬 2개만 건드리고 origin URL 0·Port 0. ViewerStudio/`panelLoad.ts` 의 raw-hfUrl 다운로드 패턴을 *모범으로 채택·확장하지 않는다* — 그것들은 데이터 SSOT 를 우회한다(TKT-EXP-1/2, → [02](02-validation-and-ledger.md)). 가격 CSV 가 청결한 이유는 정확히 *메모리 차트 객체를 직렬화하고 URL 을 만들지 않아서*다.
