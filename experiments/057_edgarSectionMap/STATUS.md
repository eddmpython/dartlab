# 057 EDGAR 섹션 맵 (v2)

## 목적

EDGAR docs를 DART `056_sectionMap`과 같은 철학으로 수평 비교 가능한 topic 체계로 정리한다.
sections 파이프라인에서 **form_type::topicId** 기준 topic × period 비교가 가능하도록 매퍼를 구축한다.

## 이전 실패 (057_edgarSectionMap_fail)

- 수집 파이프라인 4개 파편화 (002, 016, 017, 018)
- `signal.SIGALRM` Windows 미지원으로 WSL 의존
- 2,000개 목표에 31개 수집 후 중단
- output 스냅샷과 실제 데이터 불일치

## 이번 방침

1. **수집 파이프라인 1개로 통일** — subprocess ticker 격리 + timeout 600초
2. **Windows 네이티브 호환** — signal.SIGALRM 사용 금지
3. **단계별 진행** — universe 확인 → 수집 → title 전수조사 → 매퍼 구축
4. **fetch.py 그대로 사용** — signal.SIGALRM 버그는 패키지에서 이미 수정됨

## 진행 순서

1. ✅ universe 정의 + 현재 상태 확인
2. ⏳ 배치 수집 (exchange listed 7,537개, 백그라운드 진행 중 — 211/7,537)
3. ✅ title frequency 전수조사 (138개 기준)
4. ✅ sectionMappings 구축 + 매핑 커버리지 100% 달성 (109개 매핑)
5. ✅ sections 파이프라인 전종목 무에러 검증 (211개)
6. ⏳ 수집 확대 후 대규모 재검증

## 실험 파일

| 파일 | 상태 | 내용 |
|------|------|------|
| `001_universeSurvey.py` | ✅ | listed universe 7,537 exchange listed |
| `002_collectDocs.py` | ⏳ | 배치 수집 (subprocess + timeout 600초) |
| `003_monitorProgress.py` | ✅ | 수집 현황 모니터링 |
| `004_titleFrequency.py` | ✅ | form별 section_title 전수 빈도표 |
| `005_mappingCoverage.py` | ✅ | sectionMappings 커버리지 검증 |
| `006_absorbUnmapped.py` | ✅ | unmapped title 흡수 → sectionMappings.json 추가 |
| `007_pipelineValidation.py` | ✅ | sections() 파이프라인 전종목 무에러 검증 |

## 실행 결과

### 001 완료 (2026-03-13)

- listed universe total: 10,435
- exchange listed: 7,537
- local docs: 0 → 수집 시작

### 002 진행 중 (2026-03-13~)

**Phase 1: priority 30개 (완료)**
- 30/30 downloaded (JPM/BAC는 600초로 재시도 성공)
- 22,418행, 1,964 filings

**Phase 2: 전체 배치 (진행 중)**
- 211개 downloaded / 7,537개 중 (226개 처리, 일부 FAIL/timeout)
- 106,023행
- 모니터링: `python experiments/057_edgarSectionMap/003_monitorProgress.py`

### 004 완료 (2026-03-13, 138개 기준)

**10-K** (34,001행, 119 tickers)
- unique titles: **43**
- 핵심 21개: 전 종목 공통 (Item 1~16 + Signatures 등)
- long-tail 22개: wording 변형 (Item 405, 601, 8A 등) — 1~2 ticker
- Full Document: 10건 (0.03%)

**10-Q** (40,113행, 125 tickers)
- unique titles: **29**
- 핵심 11개: Part I/II × Item (Financial Statements, MD&A, Risk Factors, Exhibits 등)
- long-tail 18개: 대소문자 변형, 특이 sub-item (Item 1B 등)
- Full Document: 30건 (0.1%)

**20-F** (1,606행, 14 tickers)
- unique titles: **32**
- 핵심 27개: Item 1~19 + 16A~16K
- long-tail 5개: wording 변형 (Item 3D, 16I, 16J, 16K 등)

**40-F** (19행, 1 ticker)
- unique titles: **10**
- 표본 부족 — AG 1개뿐. structured split은 나중에.

### 005 완료 (2026-03-13, 209개 기준)

- 매핑 커버리지 **100.0%** (106,023/106,023)
- 10-K: 100.0% (31 unique titles)
- 10-Q: 100.0% (18 unique titles)
- 20-F: 100.0% (33 unique titles)
- 40-F: 100.0% (21 unique titles)

### 006 완료 (2026-03-13)

- sectionMappings.json에 36개 매핑 추가 (73→109)
- 10-K/10-Q: Part I/II 오분류 보정, pipe 잔해 정리, AAL 특이 케이스
- 20-F: Item 3D (CP-1252 en-dash 문자 처리)
- 40-F: Canadian form 전용 20개 매핑 추가
- mapper.py 정규화 강화: `_cleanPipes()`, `_normalizePartItem()`, `_DASH_CHARS_RE`

### 007 완료 (2026-03-13, 211개)

- **211개 ticker 전부 성공, 에러 0, None 0**
- topics: min=9 max=63 avg=31.7
- periods: min=1 max=69 avg=42.6
- AAPL 예시: 35 topics × 66 periods (2009~2026Q1)

### 현재 판단

- 매핑 100%, 파이프라인 무에러 — sections 수평화 기반 완성
- 10-K/10-Q/20-F/40-F 전 form 대응 완료
- 다음: 수집 확대 (현재 211/7,537) + 대규모 검증 후 안정화
