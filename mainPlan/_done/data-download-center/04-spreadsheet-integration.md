# 04 · Excel · Google Sheets 통합 — 현실 한계와 권장법

> 설계는 이론이 아니라 두 도구가 *실제로* CSV/TSV URL 을 라이브로 빨아들이는 방식에서 역산했다.

## Google Sheets (정규 경로 = IMPORTDATA)

- `=IMPORTDATA("https://{host}/v1/dart/finance/005930.csv")` 한 줄로 CSV/TSV 를 셀 격자에 라이브로 당긴다(IMPORTDATA 가 csv·tsv 둘 다 자동 인식).
- 슬라이스는 URL 쿼리로: `=IMPORTDATA("…/005930.csv?tail=250&cols=date,close")`.
- **실제 한계**: ~50,000셀/호출 · ~10MB "result too large" · 시트당 import류 함수 ~50개 · 자동 새로고침 ~1시간(워커 `max-age=3600` 과 정렬). → 워커 셀cap + `freq` 리샘플이 "첫 추측이 이미 50k셀 밑"을 보장.
- `IMPORTRANGE`(시트↔시트 전용) · `IMPORTHTML`/`IMPORTXML`(스크랩용)은 우리 URL 에 부적합 — **IMPORTDATA 가 정규 경로**.
- 권장 확장자: **`.csv`**(Sheets 가 가장 매끄럽게 먹음).

## Excel (정규 경로 = Power Query "데이터 → 웹에서")

- 데이터 → 웹에서(From Web) → URL → Text/CSV 커넥터가 표로 로드 → "모두 새로 고침"으로 라이브.
- **"라이브" ≠ 실시간 셀함수** — 자동 새로고침은 통합문서 열 때/수동/스케줄(Power BI)만. 셀 함수처럼 즉시 아님. 워크시트 1,048,576행 × 16,384열.
- **`WEBSERVICE()` 명시 비권장** — URL 2,048자 · 셀 32,767자 · 텍스트 전용이라 표 불가(단일 스칼라값만). UI 카피에 비권장 명시.
- Manage Parameters 로 `dir`/`id` 파라미터화(드릴다운) 가능.
- 권장 확장자: **`.tsv`** — 한국 Windows Excel 로케일(소수점 콤마 · list-separator 세미콜론)이 콤마-CSV 컬럼을 깨뜨린다. 탭은 로케일 중립. BOM 으로 Power Query 가 인코딩·구분자를 옳게 추론.

## "라이브" 의미 — 도구별 기대관리 (surface 카피 필수)

| 도구 | 메커니즘 | 신선도 |
|---|---|---|
| Sheets `IMPORTDATA` | CSV/TSV URL fetch | ~1시간 자동 재계산 |
| Excel Power Query | From Web 새로고침 | 열기/수동/스케줄 (실시간 아님) |
| Excel `WEBSERVICE` | (비권장) | 2KB 텍스트 한계로 표 불가 |

즉시성이 필요하면 → **Tier1 브라우저 다운로드** 안내.

## 한국 로케일·인코딩 보장 (설계 박제)

- **UTF-8 BOM** 선두 — 없으면 한글 컬럼·값 깨짐(Excel·Sheets 공통).
- **en-US invariant 숫자**(점 소수, 천단위 구분자 0) — 두 도구가 진짜 Number 로 파싱해 수식 작동.
- **TSV 기본** — 한국 Excel 콤마 로케일 충돌 회피. `.csv` 는 Sheets 명시 친화 확장자로 병행.

## 분기 가이드 (surface 카피)

| 원하는 것 | 권장 |
|---|---|
| 구글시트에서 라이브 | `.csv` URL + `=IMPORTDATA(...)` |
| 엑셀에서 라이브 | `.tsv` URL + 데이터→웹에서 |
| 한 번 받아서 작업 | Tier1 다운로드(`.xlsx`/`.csv`) |
| 거대 데이터 전량 | HF 데이터셋(벌크) |

## 링크빌더가 메우는 한계

IMPORTDATA 는 HTTP 응답 헤더(`X-DartLab-Capped` 등)를 못 본다 → 절단을 모를 수 있다. 데이터 센터 링크빌더가 선택 슬라이스의 **받을 셀수 / 전체 행수 / 넓히는 파라미터**를 미리 계산해 붙여넣기 스니펫과 함께 화면에 표시한다 → [02 링크빌더 UX](02-tier1-download.md).
