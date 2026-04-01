# 107 — disclosureRisk (공시 변화 리스크 탐지)

## 목적

changes.parquet(47MB, 195만행)에서 선행 리스크 시그널을 추출하여
기존 scan 축이 못 보는 위험을 잡아내는 새 축과 추가 시그널을 검증.

## 실험 목록

| 파일 | 상태 | 내용 | 핵심 결과 |
|---|---|---|---|
| 001_signalTest.py | 완료 | 단년도 5시그널 유효성 | 유효 3/4 → scan 축 흡수 완료 |
| 002_riskKeyword.py | 완료 | 리스크 키워드 신규 등장 | **전 키워드 유효** — 횡령/배임/과징금 audit 안전 67% |
| 003_timeSeries.py | 완료 | 시계열 패턴 (만성+가속) | 만성 우발부채 유효(768건), 가속 미달 |
| 004_strategyChange.py | 완료 | 전략 변화 (정관+경영진단) | 정관변경 역방향 유효(성장 신호), 경영진단 미달 |

## 전체 시그널 유효성 종합

| 시그널 | 판정 | 흡수 대상 | 비고 |
|---|---|---|---|
| contingentDebt (단년도) | 유효 | disclosureRisk 축 | 흡수 완료 |
| auditStruct (3건+) | 유효 | disclosureRisk 축 | 흡수 완료 |
| affiliateChange | 유효 | disclosureRisk 축 | 흡수 완료 |
| bizPivot | 유효 | disclosureRisk 축 | 흡수 완료 |
| **리스크 키워드 신규 등장** | **유효** | disclosureRisk 축 추가 | 횡령/배임/과징금/손해배상/소송 |
| **만성 우발부채 (3년+)** | **유효** | disclosureRisk 축 추가 | 연수 정보 강화 |
| 정관변경 | 역방향 유효 | growth 보조 (별도 검토) | 성장 신호 |
| changeIntensity | 미달 | 제외 | 대기업 효과 |
| acceleratingChange | 미달 | 제외 | 대기업 효과 |
| 경영진단 변화 | 미달 | 제외 | 변별력 부족 |
| 임원/직원 구조변화 | 참고 | 제외 | 독립 변별력 부족 |

## 현재 흡수 상태

- scan/disclosureRisk 축: 단년도 4시그널 흡수 완료 (001 결과)
- **추가 흡수 대기**: 리스크 키워드 신규 등장 + 만성 우발부채 연수 (002, 003 결과)

## 현황

- 2026-04-01 실험 4건 모두 완료
