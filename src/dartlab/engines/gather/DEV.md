# Gather 엔진 — 외부 데이터 수집 통합

## 구조

```
gather/
├── __init__.py       # Gather facade (오케스트레이터)
├── http.py           # 도메인별 rate limit + semaphore HTTP 클라이언트
├── cache.py          # TTL 기반 LRU 캐시
├── types.py          # 전체 데이터 타입 + 예외
├── domains/          # 도메인별 소스 어댑터
│   ├── naver.py      # 네이버: 주가 + 컨센서스 + 수급 + 업종PER
│   └── yahoo.py      # yahoo: 주가 + 히스토리 (yfinance)
├── price.py          # 주가 fallback facade (naver → yahoo)
├── consensus.py      # 컨센서스 fallback facade
├── flow.py           # 수급 fallback facade
├── listing.py        # KRX KIND 상장사 목록 (구 core/kindList.py)
└── fred/             # FRED 미국 경제 데이터
    ├── client.py     # FRED REST API 클라이언트
    ├── series.py     # 시계열 다운로드
    ├── catalog.py    # 카탈로그 조회
    ├── transform.py  # 시계열 변환
    └── cache.py      # 로컬 parquet 캐시
```

## 핵심 원칙

1. **도메인 = 소스 파일 1개** — naver.py가 네이버에서 가져올 수 있는 모든 데이터 담당
2. **facade = fallback 로직만** — price.py는 "naver 실패 → yahoo 시도" 결정만
3. **루트가 전체 오케스트레이션** — 병렬 도메인 호출, 캐시, 에러 격리
4. **새 도메인 추가 = 파일 1개** — domains/에 모듈 추가 + 레지스트리 등록

## 캐시 정책

| 데이터 유형 | TTL | 이유 |
|------------|-----|------|
| 현재가 | 5분 | 장중 변동 |
| 컨센서스 | 24시간 | 일 1회 갱신 |
| 수급 | 1시간 | 장중 변동 |

## HTTP 정책

- 도메인별 RPM 제한 (naver 30, yahoo 20)
- 도메인별 동시 연결 제한 (2)
- 지수 백오프 재시도 (최대 3회)
