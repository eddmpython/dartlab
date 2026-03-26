# Gather 엔진 — 외부 데이터 수집 통합

## 구조

```
gather/
├── __init__.py       # Gather facade (오케스트레이터)
├── http.py           # 도메인별 rate limit + persistent event loop + HTTP 클라이언트
├── cache.py          # TTL 기반 LRU 캐시 + stale-while-revalidate
├── resilience.py     # circuit breaker (3회 실패 → 60초 차단, half-open 재시도)
├── types.py          # 전체 데이터 타입 + 예외
├── market_config.py  # 시장별 설정 (KR/US 라우팅)
├── domains/          # 도메인별 소스 어댑터
│   ├── naver.py      # 네이버: 주가 + 컨센서스 + 수급 + 업종PER + 차트API 히스토리
│   ├── yahoo_direct.py # yahoo v8 chart API: 히스토리 + 컨센서스 + 배당/분할
│   └── fmp.py        # FMP: 히스토리 fallback + 컨센서스 + 업종PER
├── price.py          # 주가 fallback facade (naver → yahoo_direct)
├── history.py        # 히스토리 OHLCV fallback facade (naver → yahoo_direct → fmp)
├── consensus.py      # 컨센서스 fallback facade (market-aware: KR naver / US yahoo_direct+fmp)
├── flow.py           # 수급 시계열 facade (naver)
├── news.py           # 뉴스 수집 (Google News RSS)
├── listing.py        # KRX KIND 상장사 목록
├── ecos/             # ECOS 한국은행 경제 데이터
│   ├── client.py     # ECOS REST API 클라이언트
│   ├── catalog.py    # 지표 카탈로그 (22개 지표)
│   └── cache.py      # 로컬 캐시
└── fred/             # FRED 미국 경제 데이터
    ├── client.py     # FRED REST API 클라이언트
    ├── series.py     # 시계열 다운로드
    ├── catalog.py    # 카탈로그 조회 (50+ 지표)
    ├── transform.py  # 시계열 변환
    └── cache.py      # 로컬 parquet 캐시
```

## 핵심 원칙

1. **도메인 = 소스 파일 1개** — naver.py가 네이버에서 가져올 수 있는 모든 데이터 담당
2. **facade = fallback 로직만** — price.py는 "naver 실패 → yahoo 시도" 결정만
3. **루트가 전체 오케스트레이션** — 병렬 도메인 호출, 캐시, 에러 격리
4. **새 도메인 추가 = 파일 1개** — domains/에 모듈 추가 + 레지스트리 등록
5. **조용한 실패 금지** — 모든 API 에러는 log.warning으로 노출

## 캐시 정책

| 데이터 유형 | TTL | 이유 |
|------------|-----|------|
| 현재가 | 5분 | 장중 변동 |
| 컨센서스 | 24시간 | 일 1회 갱신 |
| 수급 | 1시간 | 장중 변동 |
| 히스토리 | 24시간 | 일봉 기준 |
| 거시지표 | 24시간 | 월간/분기 발표 |

stale-while-revalidate: 캐시 만료 + 소스 실패 시 만료된 캐시 데이터를 warning과 함께 반환.

## HTTP 정책

- 도메인별 RPM 제한 (naver 30, yahoo 5, ECOS 30, FRED 120)
- 도메인별 동시 연결 제한 (2)
- 지수 백오프 재시도 (최대 3회)
- persistent event loop — 별도 스레드에서 asyncio 루프 유지, 동기 호출에서 재사용
- User-Agent 랜덤 회전

## circuit breaker

- 3회 연속 실패 → 해당 소스 60초 차단 (open)
- 60초 후 half-open → 1회 시도, 성공 시 복구
- `resilience.py`에서 관리, facade별로 자동 적용

## fallback 체인

| 데이터 | KR | US |
|--------|----|----|
| 주가(현재가) | naver → yahoo_direct | yahoo_direct |
| 히스토리(OHLCV) | naver(차트API, 6000일) → yahoo_direct → fmp | yahoo_direct → fmp |
| 컨센서스 | naver | yahoo_direct → fmp |
| 수급 | naver | — |
| 거시지표 | ECOS (12개 고정) | FRED (25개 고정) |
