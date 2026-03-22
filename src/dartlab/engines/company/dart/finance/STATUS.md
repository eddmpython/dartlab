# financeEngine 현황

## 개요
OpenDART 재무제표 parquet에서 시계열을 추출하고, 표준계정 매핑 후 재무비율을 계산하는 엔진.

## 파일 목록

| 파일 | 역할 |
|------|------|
| `__init__.py` | public API export |
| `mapper.py` | 계정명 → snakeId 매핑 (XBRL 태그 + 한글명) |
| `pivot.py` | 원본 parquet → 시계열 dict 피벗 + 동의어 병합 + 연도별/누적 집계 |
| `extract.py` | getLatest, getTTM, getAnnualValues, getRevenueGrowth3Y 값 추출 |
| `ratios.py` | ROE, ROA, 마진, 부채비율, FCF 등 비율 계산 |
| `mapperData/accountMappings.json` | 표준계정 + 동의어 매핑 테이블 (34,175개) |

## 매핑 구조

1. **ID_SYNONYMS + CORE_MAP** (mapper.py) — XBRL ID 동의어 + 핵심 계정 오버라이드
2. **ACCOUNT_NAME_SYNONYMS** (mapper.py) — 한글 계정명 동의어 통합
3. **accountMappings.json** (mapperData/) — 한글 계정명 → snakeId (34K개, standardAccounts + learnedSynonyms 통합)
4. **SNAKE_ALIASES** (pivot.py) — 동의어 시계열 병합 (`sales` → `revenue` 등)

## API

### 시계열 빌드
| 함수 | 반환 | 설명 |
|------|------|------|
| `buildTimeseries(stockCode, fsDivPref="CFS")` | (series, periods) | 분기별 standalone |
| `buildAnnual(stockCode, fsDivPref="CFS")` | (series, years) | 연도별 |
| `buildCumulative(stockCode, fsDivPref="CFS")` | (series, periods) | 분기별 누적 |

### 값 추출
| 함수 | 설명 |
|------|------|
| `getTTM(series, sjDiv, snakeId)` | 최근 4분기 합 (IS/CF) |
| `getLatest(series, sjDiv, snakeId)` | 최신 non-null 값 (BS) |
| `getAnnualValues(series, sjDiv, snakeId)` | 전체 시계열 리스트 |
| `getRevenueGrowth3Y(series)` | 매출 3년 CAGR (%) |

### 비율 계산
| 함수 | 설명 |
|------|------|
| `calcRatios(series, marketCap=None)` | RatioResult (ROE, ROA, 마진, 부채, FCF 등) |

### Company 통합
| 접근자 | 설명 |
|--------|------|
| `c.timeseries` | 분기별 standalone (CFS) |
| `c.annual` | 연도별 (CFS) |
| `c.cumulative` | 분기별 누적 (CFS) |
| `c.ratios` | 재무비율 (CFS) |
| `c.getTimeseries(period, fsDivPref)` | 커스텀 조회 (q/y/cum × CFS/OFS) |
| `c.getRatios(fsDivPref)` | 커스텀 비율 (CFS/OFS) |

## fsDivPref 파라미터
- `"CFS"` — 연결재무제표 (기본값). 없으면 OFS fallback
- `"OFS"` — 별도재무제표. 없으면 CFS fallback

## 검증 결과 (삼성전자 005930, 2024)

| 지표 | CFS | OFS |
|------|-----|-----|
| Revenue | 300.9T | 209.1T |
| ROE | 8.29% | 5.19% |
| Debt Ratio | 27.40% | 20.67% |

## 완료

- [x] Company 통합 (property + getTimeseries/getRatios 메서드)
- [x] 분기별/연도별/누적 시계열 API
- [x] 연결/별도 재무제표 분리 조회
- [x] finance parquet GitHub Release 4-shard 업로드 (2,743 종목)
- [x] 테스트 import 경로 일괄 수정 (61/61 PASSED)

## TODO

- [ ] 다른 종목 추가 검증 (은행, 보험 등 업종별)
- [ ] financeEngine 전용 테스트 파일 작성
- [ ] 밸류에이션 멀티플 업종 평균 비교
- [ ] 매퍼 미매핑 계정 통계/리포트
- [ ] 비율 시계열 (ROE/ROA 등 분기별 추이)
