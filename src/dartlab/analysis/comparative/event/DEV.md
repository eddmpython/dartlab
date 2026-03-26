# Event — 공시 이벤트 스터디

## 구조

```
event/
├── study.py    # CAR/BHAR 계산, t-test 검정
├── price.py    # gather 인프라 기반 가격 데이터 수집
├── types.py    # EventStudyResult, EventImpact
└── spec.py     # 메타데이터
```

## 핵심 설계

- **Market Adjusted Model**: 공시 발표일 전후 비정상 수익률 측정
- **CAR** (Cumulative Abnormal Return): 누적 비정상 수익률
- **BHAR** (Buy-and-Hold Abnormal Return): 보유 기간 비정상 수익률
- **t-test**: 통계적 유의성 검정 (p-value)
- **이벤트 윈도우**: 발표일 기준 [-5, +5] 거래일 (기본값)

## 주가 데이터 소스

- 개별종목 히스토리: `gather/history.py` fallback 체인 (naver → yahoo_direct → fmp)
- 시장 벤치마크: `gather/domains/yahoo_direct.py` v8 chart API (KOSPI ^KS11, S&P ^GSPC)
- yfinance 의존성 없음

## Company 부착

- `c.eventStudy()` → EventStudyResult (method, lazy import)

## 안정성

- Tier 3 (Experimental)
