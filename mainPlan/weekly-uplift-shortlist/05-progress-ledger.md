# 05. 진행원장

> 규약: 단계 완료·결정·실측 수치를 시간순 append. 소급 수정 금지 (정정은 새 행으로).

| 일자 | 항목 | 내용 |
|---|---|---|
| 2026-07-05 | 설계 v0.1 | PRD 문서군 6종 작성 (엔진 스펙 15종 + quant/scan/simulate 코드 실측 정찰 기반). 착수는 운영자 승인 대기 (00 §8 A1~A4) |
| 2026-07-05 | 설계 v0.2 | 운영자 지적("단순 랭크로?") 반영 정정: 고정 프리셋 가중 폐기 → 가중 사다리 W0/W1/W2 (정본 = 주간 Fama-MacBeth + shrinkage, purged walk-forward 검증, numpy-only). 신호셋 5d 지평 정합(단기 reversal·수급 지속·PEAD 조건부 추가, FUND 레벨 랭크 우대 제거). family 내 상관 중복 처리(P0 상관 실측 → 대표 등록). 02·03·04 개정 |
| 2026-07-05 | 설계 v0.3 | 운영자 지시 2건 반영 구조 전환: ① "오를 기업 선정기"가 아니라 **엔진별 판독기 시뮬레이터**. 판독기 8종이 매주 전종목에 독립 의견(방향·강도·기권) 발행 → 전량 봉인 → 5거래일 뒤 엔진별 채점 → reader scorecard(시장·산업·레짐·종목, empirical-Bayes 수축) 누적. 메타 가중 = 측정된 신뢰도. 후보 100/10 은 파생 뷰. ② **EDGAR 통합**: 판독기·채점기 시장 파라미터화(KR+US), 시장 내 완결(혼합 순위 금지). US 는 fund/event/text/credit 즉시 가능, price/forecast 는 G9 선결. 갭 G9(US 가격 벌크)·G10(US flow: FINRA·13F·Form4) 추가, 승인 A5 추가. 전 문서 개정 |

## 대기 중 결정

- [ ] A1 : L3 `src/dartlab/shortlist/` 신설 승인
- [ ] A2 : `simulate/expectationCycle.issueReadings` collector 추가 승인 (expectation-grid 진행·볼륨과 조율)
- [ ] A3 : G1 KR 전종목 수급 벌크 sync 신설 (P4 시점 재상정)
- [ ] A4 : naverTheme 로컬 전용 사용 범위 확인
- [ ] A5 : G9 US 전종목 가격 벌크 백본 (P0 소스 실측 후 상정)

## P0 실측 기록 (착수 후 기입)

- [ ] KR 17년 주간 replay 판독기별 bootstrap 성적표 경로:
- [ ] text/뉴스 종목 태깅 커버리지 (전상장사 대비 %, 소형주 %):
- [ ] flow lazy fetch 300종목 소요시간:
- [ ] price reader 벌크 전종목 계산 peak 메모리:
- [ ] US fund/event reader 시범 판독 결과 (EDGAR 유니버스 커버리지):
- [ ] G9 무료 US 가격 소스 라이선스·품질 실측 (Stooq 등):
