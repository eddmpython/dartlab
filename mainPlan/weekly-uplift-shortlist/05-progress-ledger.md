# 05. 진행원장

> 규약: 단계 완료·결정·실측 수치를 시간순 append. 소급 수정 금지 (정정은 새 행으로).

| 일자 | 항목 | 내용 |
|---|---|---|
| 2026-07-05 | 설계 v0.1 | PRD 문서군 6종 작성 (엔진 스펙 15종 + quant/scan/simulate 코드 실측 정찰 기반). 착수는 운영자 승인 대기 (00 §8 A1~A4) |
| 2026-07-05 | 설계 v0.2 | 운영자 지적("단순 랭크로?") 반영 정정: 고정 프리셋 가중 폐기 → 가중 사다리 W0/W1/W2 (정본 = 주간 Fama-MacBeth + shrinkage, purged walk-forward 검증, numpy-only). 신호셋 5d 지평 정합(단기 reversal·수급 지속·PEAD 조건부 추가, FUND 레벨 랭크 우대 제거). family 내 상관 중복 처리(P0 상관 실측 → 대표 등록). 02·03·04 개정 |

## 대기 중 결정

- [ ] A1 : L3 `src/dartlab/shortlist/` 신설 승인
- [ ] A2 : `simulate/expectationCycle.issueShortlist` collector 추가 승인 (expectation-grid 진행과 순서 조율)
- [ ] A3 : G1 전종목 수급 벌크 sync 신설 (P4 시점 재상정)
- [ ] A4 : naverTheme 로컬 전용 사용 범위 확인

## P0 실측 기록 (착수 후 기입)

- [ ] 17년 주간 replay 분위 밴드 리포트 경로:
- [ ] TEXT/뉴스 종목 태깅 커버리지 (전상장사 대비 %, 소형주 %):
- [ ] FLOW lazy fetch 300종목 소요시간:
- [ ] PRICE 벌크 전종목 계산 peak 메모리:
