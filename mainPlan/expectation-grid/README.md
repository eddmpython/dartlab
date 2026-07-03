# Expectation Grid : 기대치 격자 (시뮬레이터 검증척추 선행 건설) PRD Index

상태: 완전 설계 v0.1 (2026-07-03 작성. 운영자 goal 접수 후 scenario-simulator 문서군 5종 + 코드 자산 실측 정찰 기반). **P1~P6 착수는 운영자 승인 대기** (승인 필요 3건 = 00 §9).
범위: dartlab 모든 엔진이 작은 기대치(expectation)를 공통 계약으로 발행하고, 발행 시점에 봉인된 레코드가 사후 자동 채점되어 성적표로 쌓이는 시스템. `mainPlan/scenario-simulator/` 의 검증척추(00 §8c 위협 C)를 시뮬레이터 조립보다 먼저 짓는다.

---

## 한 줄 결정

이 플랜은 "예측기"를 만들지 않는다. 이미 존재하는 예측 능력(macro BVAR fan · revenueForecast v3/v4 · credit 등급 · proforma)이 내는 출력을 **발행 시점에 불변 봉인하고, 실제값이 도착하면 자동 채점해, 그 성적을 있는 그대로 공개하는 원장**을 만든다. 핵심 명제: *트랙레코드는 과거로 돌아가 만들 수 없다. 오늘 시작한 쪽만 가질 수 있는 시간 해자다.*

## scenario-simulator 와의 접점 (이 플랜의 존재 이유)

| 시뮬 플랜 근거 | 내용 | 본 플랜의 역할 |
|---|---|---|
| 00 §8c 위협 C | 시그니처를 증명할 검증 루프가 정확히 미빌드·최난이도 | 그 검증 루프 자체를 제품으로 선행 건설 |
| 00 §8b KEEP 순서 ① | "recordForecast write-end 는 코드 소량, 조립보다 먼저 박아라" | 그 순서의 실행 |
| 09 §10.2 fatal② P9a/b/c | DATA_RELEASES 키 + env resolver + recordForecast facade = "지금 빌드 가능" | P1·P3 이 티켓 이행을 포함 |
| 03 §4.4 G16 | coverage·PIT·CRPS·skill 게이트, write-end 라이브 + N≥8분기 후 active | P2~P6 채점기가 이 명세 그대로 |
| 03 §9.3 A7 defer | 공개 Brier 리더보드는 write-end 라이브 + N분기 + held-out 전 금지 | 성적표 v0 공개 범위가 이 게이트 준수 (02 §6) |

## 문서 지도

1. [00-product-prd.md](00-product-prd.md) : 판정 · 비전 · 원칙 · 산출물 · 범위 · 성공 기준 · goal 대비 정정 2건 · **승인 필요 3건**
2. [01-architecture-and-contract.md](01-architecture-and-contract.md) : 배치 확정(import 방향 증명) · ExpectationSpec 계약 · 신설 파일/함수 · 저장 설계 · 기존 자산 매핑
3. [02-scoring-and-honesty.md](02-scoring-and-honesty.md) : 채점 수학 · naive 기준선 · 표본 게이트 · vintage 봉인 · backfill 규약 · A7/G16 정합
4. [03-implementation-phases.md](03-implementation-phases.md) : P0~P6 단계별 파일/함수/테스트/AC/롤백
5. [04-progress-ledger.md](04-progress-ledger.md) : 진행원장

## 완성 정의 (goal 원문 그대로)

P6 까지 빌드되고, 최소 1회 실제 채점 사이클(예측 발행 → 실제값 도착 → 성적표 갱신)이 실데이터로 증명된 상태.
