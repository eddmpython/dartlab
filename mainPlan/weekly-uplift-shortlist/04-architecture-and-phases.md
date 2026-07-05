# 04. 아키텍처와 단계 : 배치 · 파일/함수 · 테스트 · 롤백

## 1. 배치 결정 (v0.5, 운영자 방향) : 자체판독 분산 + simulate 수집 + 얇은 L3 파생 뷰

### 1.0 판독은 누가 내고, 누가 모으는가

- **판독 발행 = 각 엔진 자신** (외부 어댑터 아님). "verb 출력 → 방향 의견" 변환은 도메인
  로직이므로 그 엔진이 소유해야 스펙·테스트·docstring 규율이 같은 변경에서 동행한다
  (엔진 로직 재구현 금지 = 공동 작업대 원칙). L1.5 데이터 작업대(scan·frame)가 자기 축에서
  1회씩, L2 엔진(quant·analysis·credit·macro·industry)이 1회씩 자체판독을 낸다.
- **수집·봉인·채점 = simulate (L2.5)**. `expectationCycle` 은 이미 L2 verb 를 순회 호출해
  봉인·채점하는 유일 collector 다 (`issueMacro` 동형). `issueReadings` 는 그 확장이다.
  story 는 append-only 원장·채점 수학과 무관한 산문 조합기라 수집처가 아니다.
- **파생 뷰(메타 결합·board100/top10) = 얇은 L3 `shortlist`**. ledger+성적표를 직독해
  결합·깔때기만 수행. 판독 어댑터 0 (v0.4 의 readers/ 13종 폐기).
- **계약 위치 = L0 `core/reading.py`**. L1.5 형제 cross-import 금지 때문에 synth 에 두면
  scan/frame 이 import 불가. 전 층이 하향 import 가능한 core 가 유일 정답.

### 1.1 층별 역할 지도

```
L0   core/reading.py          EngineReading frozen dataclass (계약 SSOT)
L1   providers·gather         원자료만 (판독 없음, 수집 엔진 정체성 유지)
L1.5 scan.reading(asOf,...)   자기 축(orders·capital·insider·financial·disclosureRisk...) 자체판독
L1.5 frame.reading(...)       정기보고서 노트/정성 변화 자체판독
L2   quant.reading(...)       가격축(PRICE)·alphas(FUND)·텍스트축(TEXT)·forecast 자체판독
L2   analysis/credit.reading  재무 인과(FUND)·위험(FUND-risk) 자체판독
L2   macro/industry.reading   레짐·산업 틸트 (CONTEXT, 시장·산업 레벨)
L2.5 simulate.issueReadings   전 엔진 reading verb 순회 호출 → 전량 봉인 → scoreDue → 성적표
L3   shortlist (thin)         메타 결합 + board100/top10 파생 뷰 + CLI
L3   story                    top10 dossier 산문 (shortlist 산출 소비, 원장 비접촉)
L4   ai/mcp                   소비자 (EngineCall)
```

### 1.2 import 방향 증명

```
scan/frame (L1.5)   : import core.reading (L0)                ▼ 하향 OK (L1.5 형제 비접촉)
L2 엔진 5종          : import core.reading (L0)                ▼ 하향 OK
simulate (L2.5)      : import scan·frame(L1.5) + L2 5종        ▼ 하향 OK (issueMacro 선례)
shortlist (L3)       : import simulate(ledger 읽기) + core     ▼ 하향 OK
story (L3 동층)      : shortlist 직접 import ✗ 금지. dossier 는 산출물 DataFrame 입력으로 수령
```

- lint-imports 계약: shortlist 레이어 행 추가 (L3, story 와 동층·상호 import 금지) +
  core.reading 의 상향 import 0 게이트.

### 1.3 공개 계약 (v0)

```python
import dartlab

result = dartlab.shortlist()                    # 이번 주 (기본 market="KR", horizon=5거래일)
result.readings                                 # 전종목 x reader 판독 (00 §3.0 스키마)
result.board                                    # board100 (00 §3.1)
result.top                                      # top10 + dossier dict list
result.scorecard                                # reader 성적표 (수축 추정 + 미검증 라벨)
result.coverage                                 # reader 별 커버리지·기권 리포트

dartlab.shortlist(market="US")                  # EDGAR 유니버스 (활성 reader 만, 나머지 기권)
dartlab.shortlist(asOf="2026-07-03")            # 재현 실행 (같은 asOf = 같은 결과)
dartlab.shortlist(seal=True)                    # ledger 봉인 동반 (기본 False, 명시 발행)
```

## 2. 신설·수정 파일 · 함수 (본진 배치 시점 기준)

| 파일 | 핵심 함수/클래스 | 역할 |
|---|---|---|
| `core/reading.py` (신설) | `EngineReading` frozen dataclass + family 상수 | 판독 계약 SSOT (전 층 하향 import) |
| `scan/reading.py` (신설) | `scanReading(asOf, market)` | scan 자체판독 (자기 축들, engine="scan.<axisGroup>") |
| `frame/reading.py` (신설) | `frameReading(asOf)` | 노트/정성 변화 자체판독 |
| `quant/reading.py` (신설) | `quantReading(asOf, market)` | 가격축·alphas·텍스트축·forecast 자체판독 (벌크 우선, Company 루프 0) |
| `analysis`·`credit`·`macro`·`industry` (각 신설) | `*Reading(asOf, ...)` | 각 엔진 자체판독 (엔진별 독립 사이클로 순차 추가) |
| `simulate/expectationCycle.py` (확장) | `issueReadings(asOf, market)`, 주간 `scoreDue` 경로 | 전 엔진 reading 순회 수집 → 봉인 → 채점 (유일 writer 유지) |
| `simulate/readingScorecard.py` (신설) | `buildReadingScorecard(...)`, `shrinkProfile(...)` | engine x 시장 x 산업 x 레짐 수축 성적표 (02 §4) |
| `shortlist/__init__.py` (신설, thin L3) | `shortlist()` + `__all__` | ledger+성적표 직독 → 메타 결합·합류·게이트·board100/top10 (02 §5~6) |
| `shortlist/combine.py` | `combine(...)`, `confluence(...)`, `redFlags(...)` | 파생 뷰 수학 (판독 발행 0) |
| `cli` 서브커맨드 | `dartlab shortlist [--asof --market --seal]` | 운영 진입점 (P2) |

- 판독 내부 신호 가중 v1 승격용 `famaMacbethWeekly`/`purgedWalkForward` 는 각 엔진 reading 모듈이 소비하는 공용 수학으로 `quant/` 기존 자산 재사용 (신설 최소화).
- 임계값(중립 밴드·family 합류 수·수축 파라미터·지수 감쇠 창)은 `core/reading.py` 상수 선언 한 곳에만. 주간 메타 가중 스냅샷은 `data/shortlist/weights_{market}_{yyyy}.parquet` 봉인 (재현 가능).

## 3. 테스트 계획 (src ↔ tests 미러 규약)

| 테스트 | 검증 |
|---|---|
| `tests/core/test_reading.py` | EngineReading 계약 무결, 기권 1급 출력, 임계값 SSOT 단일성, 상향 import 0 |
| `tests/{scan,frame,quant,...}/test_reading.py` (엔진별 미러) | 자체판독별: 전종목 발행 완전성(판독/중립/기권 셋 중 하나), 기권 사유 기록, Company 미사용(벌크 경로), KR/US 시장 파라미터 |
| `tests/simulate/test_readingScorecard.py` | 채점 수학(시장 내 초과수익 부호), 수축 계층(종목←산업←전체) 복원, 표본 게이트 "미검증" 라벨 |
| `tests/shortlist/test_combiner.py` | 신뢰도 가중 결정성, 기권 제외, 참여<2 제외, 합류 k 계산, 10 미만 발행 |
| `tests/shortlist/test_weights.py` | Fama-MacBeth 계수 복원(합성 데이터), purged embargo 라벨 겹침 0 |
| `tests/shortlist/test_board_contract.py` | 스키마 계약(Pandera), refs/asOf 동행, 금지 어휘 grep 게이트, 시장 혼합 순위 부재 |
| `tests/shortlist/test_pit.py` | pitLagDays 보정, rcept_dt 기준 look-ahead 부재 (합성 fixture) |
| `tests/shortlist/test_seal_roundtrip.py` | issueReadings 봉인 → scoreDue 채점 → scorecard 갱신 왕복 (append-only 준수) |
| 기존 게이트 | `dartlabGuard --scope l0-l15` 룰7 미러, lint-imports 신규 계약, camelCase, no_emdash |

실행 규약: 단일 파일은 `bash tests/test-lock.sh tests/shortlist/... -v`, 전체는 `uv run python -X utf8 tests/run.py preflight`. fixture scope=module, 전종목 fixture 는 합성 소형 격자(실데이터 전종목 로드 금지).

## 4. CI 게이트 체크리스트 (신규 src 모듈 필수 절차)

- [ ] `tests/<src 미러 경로>` 구조 미러 (`test_structureMirror`)
- [ ] publicApi manifest 등록 + `publicApiCoverage`
- [ ] `publicApiScenarios.yml` 에 shortlist 시나리오 추가 + `productSmoke --suite quick`
- [ ] lint-imports 계약 갱신 (L3 shortlist 행)
- [ ] Skill OS: `engines.shortlist` sub-spec 신설 4단계 (lintSkill + capabilityRefs + 검색 + 동기화)
- [ ] workspaceHygiene: 신규 산출 경로는 `data/shortlist/` (DATA_RELEASES 등록), repo 루트 오염 0

## 5. 단계 (각 단계 독립 출하 가능 · 롤백 = 해당 단계 파일 제거로 완결)

| 단계 | 내용 | AC (완료 판정) | 롤백 |
|---|---|---|---|
| **P0 개념확립** (_attempts) | `tests/_attempts/shortlist/` 에서 ① gov/prices 벌크 price reader 전종목 실측 ② 주간 PIT replay 하네스(G7) + 판독기별 bootstrap 성적 ③ 신호 상관 행렬 → reader 내부 신호 확정 ④ 수축 성적표 수학 검증 ⑤ text 태깅 커버리지(G8)·flow lazy 소요 실측 ⑥ **US 실측**: EDGAR 유니버스 fund/event reader 시범 판독 + G9 무료 가격 소스 라이선스·품질 실측 | KR 17년 replay 판독기별 bootstrap 성적표(시장·산업 분해) 재현 가능 + US fund/event 시범 판독 N종목 실증 + 커버리지 수치 확보 + 결과 docstring/README 기록 | 폴더 삭제 (src 비접촉) |
| **P1 골격 본진** | 졸업 게이트(모듈화·덕지덕지 제거·클린코드·9섹션 docstring) 후 core/reading + scan·quant 자체판독 + simulate 수집·성적표 + thin shortlist 본진 배치. 나머지 엔진 reading 은 독립 사이클로 순차 추가. 초기 메타 가중 = P0 bootstrap (issuedLive=False 표기) | `dartlab.shortlist(asOf=..., market="KR")` 가 readings+board100 산출 + §3 테스트 green + §4 게이트 전부 통과 | `shortlist/` 제거 + 게이트 등록 원복 |
| **P2 근거 심화 + CLI** | flow/text lazy 판독(기권 표기), forecast 게이트, top10 dossier(트랙레코드 인용), 금지 어휘 grep, CLI. US fund/event/credit reader 활성(G9 전 부분 채점 한계 명시) | top10 합류 룰 전 조건 충족 + dossier refs 완비 + 시장당 실행 <30분 | CLI/dossier 모듈만 제거 |
| **P3 봉인 라이브** | issueReadings + 주간 채점 + scorecard 갱신 + 주간 런북 1p. 최소 1회 발행→채점 실측 | 실데이터 왕복 1회 증명 + 수축·미검증 라벨 동작 | collector 제거 (ledger 데이터는 append-only 보존) |
| **P4 갭 승격** | G1 KR 수급 벌크(A3) · G3 실적 캘린더 · G5 시장조치 · G6 priceCluster · **G9 US 가격 백본(A5) → US price/forecast reader + US 전량 채점 활성** · G10 US flow. 각각 독립 사이클 + 사전 근거 | reader 커버리지 상승이 coverage 리포트로 확인 | reader/신호 선언 제거 (결합기 비접촉) |
| **P5 터미널 서피스** | 별도 미니 PRD 로 분리 (UI 눈검수 + push 승인 게이트 + 공개 터미널 무중단 규약) | 별도 정의 | 별도 |

## 6. 메모리·성능 예산

- readings 볼륨: KR ~2,800 x 8 + US ~5,000 x 활성 reader 수 ≈ 주당 4~6만 행, 연 ~3M 행. 연도 샤딩 parquet append 로 충분 (기존 ledger 규약 그대로).
- 전종목 wide 격자(수십 MB)는 문제 아님. 위험은 (a) Company 객체 루프, (b) gov/prices 다년 로드. 방어: 판독기는 필요한 lookback(최대 260거래일) 연도 shard 만 lazy 로드, Company 사용은 top10 dossier 10종목 순차 한정. readers 계약 자체가 "bulk 불가 = 기권"이라 루프 유혹을 구조로 차단.
- 새 캐시는 BoundedCache 만. `withMemoryBudget` 예산 선언을 각 reader 진입점에 부착 (narrativeRegime 선례).
- 주간 실행 완주 목표 시장당 <30분 (flow lazy fetch x rate limit 이 지배 항. P0 실측해 상한 재선언).

## 7. 운영 런북 (P3 산출물 골자)

1. 각 시장 금요일 마감 후: `dartlab shortlist --market KR --seal` (US 는 활성 reader 범위로 동일).
2. 검수: coverage·기권 리포트·red-flag 표 눈검수 (수치 조작 없이 발행/스킵만 결정).
3. 봉인 확인: ledger append 건수 = readings 행수 (기권 포함).
4. 다음 주: `scoreDue` 채점 → reader scorecard 갱신 확인 (메타 가중 자동 반영).
5. 실패 시: 스킵 원장 기록 (03 §4). 임시 파라미터 변경 금지.
