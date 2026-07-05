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

## P0 실측 기록

2026-07-05 운영자 지시로 P0 즉시 착수 (시범 규모 없이 2016~ 전종목, EDGAR 포함, 메모리가드 체크). 상세·스크립트 = `tests/_attempts/shortlist/` (README + weeklyLoopKr/Us.py, gitignore 로컬 샌드박스). 핵심 수치는 본 원장이 영속 기록.

- [x] KR 데이터: gov/prices 2015~2026 로컬 완비. 6.67M행·3,402종목 로드 0.8초
- [x] 주간 예측→판독→개선 루프 KR 전종목 2016~2026: **543주 전 루프 3.7초** (`weeklyLoopKr.py`). price reader v0 edge 0 (board100 hit 0.428 = base, Q5-Q1 +0.06%/주) = 정직한 기준선
- [x] 개선 사이클 1 (KR 수정주가 근사, 1,164종목 보정): 무변화 → 가설 기각 기록
- [x] US EDGAR: HF 에 가격 4,122·panel 7,391·financeStmt 6,442 실재. **전 4,122 수령·재실측 완료**: 사용가능 2,210 (54%), 열화 1,913 (46%) 전수 확정 → G9=재bake 복구 패스로 재정의. US 루프 546주(평균 유니버스 1,734) 8.4초, board100 +0.49%/주·Q5-Q1 +1.40%/주 전 연도 양(+) **단 생존편향 상방 왜곡 명시** (현재 유니버스 bake 라 폐지사 부재. KR 0 vs US + 격차의 유력 설명 후보)
- [x] Company 메모리가드: 30사 순차 panel 루프 RSS ~900MB 정체 (peak 922MB). "1사당 200~500MB 무한 누적" 미재현 → 순차 한정 완화 근거 확보 (병렬 미검증, CLAUDE.md 문구 변경은 운영자 결정)
- [ ] event/fund reader 의 과거 PIT 재현 실측 (rcept_dt 기반) = 다음 사이클
- [ ] text/뉴스 종목 태깅 커버리지 실측 = 다음 사이클
