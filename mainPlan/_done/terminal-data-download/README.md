# Terminal Data Download — 데이터 다운로드 PRD Index

상태: PRD v7 (코드 전수 재검증 확정, 2026-06-19). 전문 에이전트 다기 토론(5라운드) → 적대 반증으로 결론 *역전* → 보정 합성(2라운드, 심사단 100/100) → 최종 레드팀 3 major 정정 흡수. 본 README + 3 문서가 SSOT(메모리=포인터).

범위: 터미널이 로드해 보여 주는 데이터를 사용자가 **파일로 내려받는** 기능. "그 데이터를 모두 다운로드"를 해부한 결과 — 대부분은 *이미 작동*하고, 진짜 빈 곳은 **딱 하나**다.

---

## 한 줄 결정

별도 "다운로드 센터"·번들·zip·매니페스트·Export 프레임워크를 **만들지 않는다**. 코드 전수 재검증 결과 "데이터 모두 다운로드"는 공시뷰어(ViewerStudio)가 *이미 터미널 안에서* 공시수평화 CSV·재무제표 Excel·parquet 원본·전체 데이터셋 링크를 퍼블릭 floor 에서 제공 중이고, 비어 있는 단 하나는 **가격 차트가 보는 시계열을 PNG 이미지로만 내보내고 텍스트(행) 포맷이 없다**는 것뿐이다. 그래서 본 PRD 의 산출물 = **PriceChart 에 「표(CSV)」 버튼 1개**(스냅샷 'S' 버튼 대칭) — `chart.getDataList()`(차트가 실제로 그리는 봉, render 진실)를 기존 `csvExport.ts` 작성기로 데이터-only BOM CSV 로 직렬화하고, 출처는 파일명 + 이미 화면에 떠 있는 `srcText()` 주석으로 단다. `subject!=='index'` 게이트 + HA/리플레이 모드 비활성 확정.

---

## "모두"의 실제 해부

| 도메인 | 형식 | 상태 | 거처 |
|---|---|---|---|
| 공시 수평화표 | CSV | ✅ **이미 ship** | `ViewerStudio.svelte:272 downloadPanelCsv` → `dataExport.panelToCsv` |
| 재무제표 (IS·BS·CF·CIS) | .xls (멀티시트) | ✅ **이미 ship** | `ViewerStudio.svelte:275 downloadFinanceExcel` → `dataExport.financeToExcel` |
| panel·재무제표 원본 | .parquet (passthrough) | ✅ **이미 ship** | `ViewerStudio.svelte:266/267 + :497/499` `<a href={hfUrl(...)} download>` |
| 전체 데이터셋 (모든 회사) | HF 링크 | ✅ **이미 ship** | `ViewerStudio.svelte:268/:501` `huggingface.co/datasets/eddmpython/dartlab-data` |
| **가격 OHLCV 시계열** | **CSV** | ❌ **빈 곳 = 본 PRD** | PNG(`snapshot.ts`)만 있음 → **데이터 egress 0** |
| 뉴스 | — | ⛔ 사적 네이버 archive·재배포권 0 | egress 없음 |
| macro·screener | — | ❓ OPEN QUESTION (v9 차트 인스턴스 핸들 미확인) | 본 PRD 미포함 |

ViewerStudio 는 `RightStack.svelte:29 import → :787 mount ViewerOverlay → ViewerOverlay.svelte:2,29` 로 **터미널을 떠나지 않고 도달**한다("한몸두입구"). 즉 터미널 사용자는 이미 *가격 OHLCV 텍스트 하나만 빼고* 모든 도메인을 내려받을 수 있다.

---

## 핵심 결정 요약 (v7)

- **PNG ≠ 데이터 export (범주 교정)**: `snapshot.ts:5` 는 `chart.getConvertPictureUrl(true,'png',...)` 로 *픽셀* 래스터를 만든다 — pandas/Excel 에 못 읽힌다. 가격 CSV 는 "두 번째 포맷"이 아니라 **가격 시계열의 *첫* 데이터 egress**다.
- **render 진실 직렬화**: `displaySeries()`/`loaded()`/`candles` prop 이 아니라 `chart.getDataList()`(klinecharts v9 인스턴스, `PriceChart.svelte:67/:464`) 를 직렬화한다. 이유 = 좌측 팬/MAX 기간 백필(`loadOlderYear`, `priceSource.ts:127-138`)이 더 오래된 연도를 *캐시·차트에만* append 하고 **`candles` prop 은 갱신하지 않으므로**, prop/loaded 를 쓰면 차트가 17년을 그리는데 CSV 는 짧게 새는 무성 절단이 난다. → [01](01-architecture-traps-format.md) 함정 1.
- **다섯 함정 박제**: ① 백필 시 prop 절단(body) ② 파일명 날짜를 `snapshot()` 의 stale prop ymd 로 재사용한 절단(filename) ③ index 차트 잘못된 출처표시 ④ Heikin-Ashi 합성봉 + 리플레이 절단 ⑤ 거래대금 1e8 단위 거짓. 전부 해소·테스트 동행. → [01](01-architecture-traps-format.md).
- **SSOT 청결**: 가격 CSV 는 *메모리 차트 객체*를 직렬화하고 origin URL 을 만들지 않으므로 데이터-워크벤치 SSOT 를 위반하지 않는다. ViewerStudio parquet passthrough·`panelLoad.ts` 의 raw hfUrl/자체 Map 우회(TKT-EXP-1/2)는 *모범이 아니라 별도 부채*다 — 따라 하지 않는다.
- **재발명 0**: 작성기는 `scan/csvExport.ts:27 toCsv` + `:36 downloadCsv`(BOM·RFC4180·null=빈셀) 재사용. 6번째 CSV 작성기 신설 금지(현재 5종 분산 = TKT-EXP-3 부채).
- **덕지덕지 0**: 드로어·dialog·zip·매니페스트·Port/ExportInput·bulk 버튼 전부 KILL. 순 산출 = 버튼 1개 + ~18줄 직렬화기.

---

## 문서 지도

1. [00-product-and-scope.md](00-product-and-scope.md) — 사용자 스토리, 이미 ship 된 것의 지도, "모두" 정의, 범위 in/out, 차별점, **산출물 무게 고지**, 개발자·PM 이중 평가.
2. [01-architecture-traps-format.md](01-architecture-traps-format.md) — `getDataList()` render 진실 직렬화, **다섯 함정 + 해소**, 형식·파일명·출처 결정, HA/리플레이/index fork 확정, 재사용 자산, 경계·SSOT 청결.
3. [02-validation-and-ledger.md](02-validation-and-ledger.md) — 테스트 매트릭스, 롤백, 부채 티켓 3종, OPEN QUESTION, 결정 로그·토론·점수 이력·NEXT·착수 게이트.

---

## 설계 원칙 (전 문서 관통)

- **이미 있는 걸 다시 짓지 않는다.** 공시·재무·parquet·bulk 는 ViewerStudio 가 이미 한다 — 사용자를 그리 안내하고, 본 PRD 는 *유일하게 빈* 가격 egress 한 칸만 채운다.
- **render 진실만 내보낸다.** 차트가 그리는 봉(`getDataList`)을 내보낸다 — 캐시 fallback prop 이 아니라. 보이는 것과 파일이 어긋나면 그건 거짓이다.
- **무성 절단·단위 거짓·합성봉 금지.** 백필 절단·리플레이 절단·HA 합성봉·거래대금 1e8 스케일은 전부 *함정*으로 박제하고 비활성/라벨로 막는다. 결손 = 빈셀(0 금지).
- **출처는 보존하되 파일을 깨지 않는다.** `#` 주석 선두행은 pandas/Excel 파싱을 깨뜨린다 — 출처는 파일명 + 화면 `srcText()` 주석(stockanalysis/Koyfin 패턴).
- **작다는 걸 숨기지 않는다.** 산출물은 버튼 1개다. PRD 의 값은 줄 수가 아니라 *이미 ship 지도 + 다섯 함정 + KILL + 부채 티켓*의 영속 기록 — 다음 세션이 재발명·재조사하지 않게.
- **공개 surface.** 커밋 자율, **push 는 운영자 명시 승인("푸시해"·"올려") 후에만** + 스크린샷 눈검수 필수.

---

## 의존성·착수 조건

- **독립 착수 가능.** table-export·ui-platform-refactor 와 무충돌(가격 차트 surface 만 건드림, Port 0). 착수 = 운영자 go.
- **선결**: [02](02-validation-and-ledger.md) 의 OPEN QUESTION 2종(HA/리플레이 fork 는 v7 에서 DISABLE 로 확정·박제, macro/screener 는 미해결 유지) 외 재조사 불필요 — 본 문서만 보고 구현 가능.
