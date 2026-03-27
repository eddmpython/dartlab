# 102_krxPrice — KRX/시장 가격 데이터 수집 실험

## 실험 목록

| ID | 실험명 | 상태 | 결과 |
|----|--------|------|------|
| 001 | KRX 개별 종목 OHLCV 직접 호출 | 기각 | KRX 로그인 필수화(2026-02-27)로 비로그인 OHLCV 불가 |
| 002 | 네이버 API 전체 시장 스냅샷 | 채택 | 0.81초에 4238종목 수집, close/changePct/volume/tradingValue/marketCap |

## 핵심 발견

### KRX data.krx.co.kr 정책 변경
- 2026-02-27부터 `dbms/MDC/STAT/*` 경로 로그인 필수
- `dbms/comm/finder/*` (종목검색)만 비로그인 허용
- pykrx도 깨진 상태 (PR #282 미머지)
- 회원가입(무료) + 세션 로그인으로 우회 가능하나 별도 실험 필요

### 네이버 전체 시장 스냅샷
- `m.stock.naver.com/api/stocks/marketValue/{KOSPI|KOSDAQ}` 엔드포인트
- pageSize=100 고정, 비동기 병렬로 44 요청 → 1초 이내
- 제공: ticker, name, close, changePct, volume, tradingValue, marketCap
- 미제공: open, high, low (완전한 OHLCV 아님)
- 장중 실시간 반영

## 다음 단계
- 002 결과를 `gather/` 또는 `market/`에 흡수할지 사용자 판단 대기
- KRX 로그인 세션 기반 OHLCV는 별도 실험으로 분리
