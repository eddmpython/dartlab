# Gather

외부 시장 데이터 수집. 공시 데이터와 시장 데이터를 연결.

| 항목 | 내용 |
|------|------|
| 레이어 | L1 |
| 진입점 | `dartlab.gather()`, `c.gather()` |
| 소비 | 외부 API (Naver, Yahoo, FRED, ECOS, Google News) |
| 생산 | analysis, macro가 gather 데이터를 소비 (주가, 매크로) |
| 축 | 4축: price, flow, macro, news |

## 4축

```python
# DART (한국)
dartlab.gather("price", "005930")              # 주가 OHLCV
dartlab.gather("price", "KOSPI")               # 코스피 지수
dartlab.gather("flow", "005930")               # 외국인/기관 수급
dartlab.gather("macro")                        # 거시지표 (ECOS + FRED)
dartlab.gather("news", "삼성전자")              # 뉴스

# EDGAR (미국) — Company-bound 시 market="US" 자동 전달
c = Company("AAPL")
c.gather("price")                             # Yahoo/FMP
c.gather("macro")                             # FRED
c.gather("news")                              # Google News RSS
```

### 시장 지수 심볼

| 심볼 | 별칭 | 소스 | 시장 |
|------|------|------|------|
| KOSPI | 코스피 | 네이버 차트 API | KR |
| KOSDAQ | 코스닥 | 네이버 차트 API | KR |
| KPI200 | 코스피200 | 네이버 차트 API | KR |

Company-bound: `c.gather("price")` — 종목코드/market 재전달 불필요. EdgarCompany는 `market="US"` 자동 전달.

## 데이터 소스

| 축 | KR 소스 | US 소스 | 캐시 |
|------|---------|---------|------|
| price | Naver → Yahoo fallback | Yahoo → FMP fallback | 메모리 TTL |
| flow | Naver/KRX | — (KR 전용) | 메모리 TTL |
| macro | ECOS + FRED | FRED | Parquet + 30분 TTL |
| news | Google News RSS | Google News RSS | GatherCache |

**flow는 KR 전용**: 외국인/기관 수급 데이터는 KRX에서만 제공. EDGAR ticker에서 `c.gather("flow")`는 None 반환.

## 주요 모듈

| 모듈 | 역할 |
|------|------|
| price.py | 주가 OHLCV |
| flow.py | 수급 시계열 |
| macro.py | FRED/ECOS 거시지표, 변화율 계산, 리샘플링 |
| news.py | 뉴스 검색 |
| search.py | 웹 검색 (Tavily API) |
| consensus.py | 컨센서스 |
| ownership.py | 주주 정보 |
| listing.py | 종목 리스팅 + fuzzy search |
| resilience.py | Circuit breaker |

## 소비 경로

gather 매크로 데이터를 두 엔진이 소비한다:

- **macro(L2)**: `dartlab.macro()` — 시장 레벨 매크로 해석 (사이클/금리/자산/심리/유동성). Company 불필요. → ops/macro.md
- **analysis(L2)**: `c.analysis("financial", "매크로민감도")` — 기업별 외생변수 회귀. Company-bound.

## 외생변수 체계 (analysis 연동)

`core/finance/exogenousAxes.py` — 6축 28개 지표, 143개 업종 매핑.
`gather/macro.py`로 데이터 수집 → `calcMacroRegression`에서 소비.

## 관련 코드

- `src/dartlab/gather/` — 19개 모듈
- `src/dartlab/gather/ecos/` — 한국은행 ECOS
- `src/dartlab/gather/fred/` — FRED
