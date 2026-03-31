# Gather

외부 시장 데이터 수집. 공시 데이터와 시장 데이터를 연결.

## 4축

```python
dartlab.gather("price", "005930")              # 주가 OHLCV
dartlab.gather("flow", "005930")               # 외국인/기관 수급
dartlab.gather("macro")                        # 거시지표
dartlab.gather("news", "삼성전자")              # 뉴스
```

Company-bound: `c.gather("price")` — 종목코드 재전달 불필요.

## 데이터 소스

| 축 | 소스 | 캐시 |
|------|------|------|
| price | Naver/Yahoo/FDR | 메모리 TTL |
| flow | Naver/KRX | 메모리 TTL |
| macro | FRED/ECOS | Parquet + 30분 TTL |
| news | Google News RSS | GatherCache |

## 주요 모듈

| 모듈 | 역할 |
|------|------|
| price.py | 주가 OHLCV |
| flow.py | 수급 시계열 |
| macro.py | FRED/ECOS 거시지표, 변화율 계산, 리샘플링 |
| news.py | 뉴스 검색 |
| search.py | 웹 검색 (Tavily → DuckDuckGo fallback) |
| consensus.py | 컨센서스 |
| ownership.py | 주주 정보 |
| listing.py | 종목 리스팅 + fuzzy search |
| resilience.py | Circuit breaker |

## 외생변수 체계 (analysis 연동)

`core/finance/exogenousAxes.py` — 6축 28개 지표, 143개 업종 매핑.
`gather/macro.py`로 데이터 수집 → `calcMacroRegression`에서 소비.

## 관련 코드

- `src/dartlab/gather/` — 19개 모듈
- `src/dartlab/gather/ecos/` — 한국은행 ECOS
- `src/dartlab/gather/fred/` — FRED
