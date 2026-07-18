# 00 · 제품과 범위

## 사용자 스토리 (한 문장, 선두)

`/terminal` 에서 회사 가격 차트를 보던 분석가가 **지금 보고 있는 그 가격 시계열을 Excel/pandas 에 붙여 넣을 CSV 로** 원한다. 그러나 오늘 그 차트는 **PNG 이미지로만** 내보낸다(`snapshot.ts:5` `chart.getConvertPictureUrl(true,'png','#0b0e14')` → 픽셀). 즉 가격 OHLCV 시계열은 **데이터 egress 가 0**이다 — 본 PRD 는 그 빠진 「표(CSV)」 버튼 하나를 더한다.

## "데이터를 모두 다운로드"는 이미 대부분 작동한다

요청 문구 "그 데이터를 모두 다운로드"를 코드로 전수 해부한 결과, 터미널 사용자는 이미 회사별 데이터 대부분을 *터미널을 떠나지 않고* 내려받는다. 공시뷰어 본체 `ViewerStudio.svelte` 가 퍼블릭 floor(백엔드 0)에서:

- `:272 downloadPanelCsv` → `viewer/lib/dataExport.ts:32 panelToCsv` → `{회사}_공시수평화.csv`
- `:275 downloadFinanceExcel` → `dataExport.ts:68 financeToExcel` → `{회사}_재무제표_연간연결.xls` (IS/BS/CF/CIS 멀티시트 SpreadsheetML, 라이브러리 0)
- `:266/267 + :497/499` parquet passthrough — `<a href={hfUrl('dart/panel/{code}.parquet' | 'dart/finance/{code}.parquet')} download>` (raw HF 바이트, 작성기 불요)
- `:268/:501` 전체 데이터셋 링크 — `huggingface.co/datasets/eddmpython/dartlab-data` (모든 회사·공개)

도달 경로: `RightStack.svelte:29 import → :787 mount ViewerOverlay → ViewerOverlay.svelte:2,29` 가 ViewerStudio 를 임베드 lazy-mount("한몸두입구의 터미널 입구"). **사용자를 여기로 안내하라 — 공시·재무·원본·bulk 는 어떤 것도 다시 짓지 않는다.**

## 유일한 빈 곳 = 가격 OHLCV 행-egress

진짜 순-신규 도메인은 **단 하나**: 가격 OHLCV 시계열의 텍스트(행) 내보내기. PNG 스냅샷은 이 시계열의 *기존 export 가 아니다* — `snapshot.ts:5` 가 만드는 것은 캡션 띠를 합성한 *픽셀 래스터*라서 pandas/Excel 에 못 읽힌다. 따라서 가격 CSV 는 "두 번째 직렬화 포맷"이 아니라 **가격 시계열의 첫 데이터 egress**다(전 코드 통틀어 `getDataList` 호출 0건 = 본 직렬화기가 그 첫 사용).

## "모두"의 정의

```
데이터 모두 다운로드
  = 공시 CSV + 재무 .xls + 원본 parquet + 전체 데이터셋   (전부 ViewerStudio 가 이미 ship)
  + 가격 OHLCV CSV                                        (본 PRD = 유일하게 빠진 한 칸)
```

"모두"는 *빠진 한 도메인을 더해* 닫는다 — 새 번들/zip surface 로 닫지 않는다.

## 범위 (In)

- PriceChart.svelte 에 「표(CSV)」 액션 1개: `chart.getDataList()`(klinecharts v9 인스턴스 `:67`/적용 `:464`)를 `csvExport.ts toCsv/downloadCsv` 로 데이터-only BOM CSV 직렬화.
- 기존 `onSnapshot` 식 prop 로 `ChartMenus(:1178)`·`ChartRibbon(:1238 전체화면)` 에 배선 — `onSnapshot={snapshot}` 와 동일 패턴.
- 직렬화기가 각 `KLineData{timestamp(ms),open,high,low,close,volume?}` → `t(YYYYMMDD)/o/h/l/c/v` 재정형. 파일명 마지막 날짜는 **`getDataList()` 마지막 봉**에서 도출(prop·`snapshot()` ymd 아님).
- 출처 = 파일명 + 이미 떠 있는 `srcText()(:1161)` 화면 주석 재사용.
- `subject!=='index'` render 게이트. HA 모드·리플레이 모드 비활성(→ [01](01-architecture-traps-format.md) fork 확정).

## 범위 (Out — KILL)

- 새 드로어/dialog/Export surface
- zip + 매니페스트 번들
- command-bus / Port / ExportInput / ExportPort 추상
- 뉴스 egress (사적 네이버)
- 결손 셀 채우기 (null 거래량 → 빈셀, 0 금지)
- bulk 다운로드 버튼 (이미 `ViewerStudio:268/:501` 링크됨)
- macro/screener CSV (v9 차트 인스턴스 핸들 **미확인** = OPEN QUESTION, 단정 제외 아님)
- ViewerStudio/panelLoad raw-hfUrl 다운로드 재배선 (TKT-EXP-1/2 = 별도 부채)
- 6번째 toCsv 작성기 (csvExport.ts 재사용; TKT-EXP-3 수렴은 범위 밖)

## 차별점

`git clone` 은 326MB 전 종목 parquet 을 *날짜키 전종목 횡단*(`gov/prices/date/{year}.parquet`)으로 줘서 사람이 쓰기 어렵다. 본 기능은 **지금 차트가 그려 놓은 바로 그 시계열** — 이 종목, 보는 기간/집계, 출처 동봉 — 을 한 클릭 텍스트로 준다. 재-fetch 0회(메모리 차트 객체 직렬화), 정적 GitHub Pages·백엔드 0. 프로 터미널(Koyfin·stockanalysis)이 시계열을 *텍스트로* 내보내는 보편 floor 를 dartlab 가격 차트가 *이미지로만* 제공 중이었고, 그 한 칸을 채운다.

## 산출물 무게 — 범위 고지

순 산출 = 「표(CSV)」 버튼 1개(`snapshot()` 대칭) + `chart.getDataList()` 위 ~18줄 직렬화기(ms→YYYYMMDD 재정형), 기존 `csvExport.ts` BOM 작성기·`rt`·`srcText()`·`onSnapshot` prop 재사용. **이건 짧은 PRD 다.** 정당성은 줄 수가 아니라: (a) 터미널 내 다운로드가 이미 ViewerStudio 로 ship 됨을 기록해 *누구도 panel/finance/raw/bulk 를 재발명하지 않게*, (b) 순진한 구현자가 빠지는 **다섯 검증된 함정**, (c) KILL 목록, (d) 부채 티켓 3종. 번들/Export 프레임워크로 부풀리지 않는다.

## 개발자 평가 (비판적)

모든 load-bearing 사실을 소스로 재검증. klinecharts v9 `KLineData` 는 `{timestamp:number,open,high,low,close,volume?,turnover?}` 로 **`.t` 없음** → 직렬화기가 `timestamp(ms)→YYYYMMDD` 재정형 필수. 백필(`loadOlderYear`, `priceSource.ts:127-138`)이 `rec.candles` 에만 더해지고 `candles` prop 은 그대로라(`:134`) prop/loaded 직렬화는 무성 절단. `snapshot()(:1167)` 의 ymd 는 prop 유래라 파일명에 재사용하면 같은 절단 거짓이 파일명에 옮는다. 거래대금은 `priceSource.ts:57` 에서 `tv=num(ACC_TRDVAL)`(원, 채워짐)인데 차트 봉 매핑이 억(1e8) 단위로 사전 스케일하므로 그대로 내보내면 단위 거짓 — OHLCV-only 로 생략. `csvExport.ts:27 toCsv(columns,records)` + `:36 downloadCsv` 는 BOM·따옴표 이스케이프·null→빈셀(`:13`) 제공 → 재사용, 6번째 작성기 금지. 구현자 필수 주의: ① 클릭 시점 `chart` non-null 확인(getDataList 최초 사용) ② `volume?` optional → undefined 는 빈셀(0 금지) ③ HA/리플레이 fork 비활성 확정 박제대로 ④ ms→YYYYMMDD 는 `toMs(:133)` 역. **재조사 없이 본 PRD 로 구현 가능.**

## PM 평가 (비판적)

PRD 가 사용자 필요(가격 시계열 CSV)로 시작하고, "모두 다운로드"가 ViewerStudio 로 이미 대부분 ship 됐음을 먼저 밝힌 뒤 순-신규를 단일 도메인으로 좁힌 것 — 이 범위 명시가 *재발명을 막는* 핵심이다. PNG≠export 교정 정확. 팀에 거는 선: ① 산출물은 버튼 1개 — ROI 정당성은 함정/이미-ship/KILL/부채 기록의 *영속성*뿐, 그게 반드시 남아야 한다. ② macro/screener 는 OPEN QUESTION 유지(v9 핸들 미확인) — 범위 재팽창 금지. ③ 공개 surface: 커밋 자율, push 는 운영자 명시 승인·스크린샷 눈검수 필수. ④ TKT-EXP-1/2/3 은 실재 부채지만 범위 밖 — 데이터-배선 리팩토링으로 부풀리려는 시도 거부. **결론: 작고 유용한 PRD 로 승인 — 번들/프레임워크 부풀림은 거부.**
