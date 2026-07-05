# 04. 아키텍처와 단계 : 배치 · 파일/함수 · 테스트 · 롤백

## 1. 배치 결정 (A1) : 신설 L3 모듈 `src/dartlab/shortlist/`

### 1.1 왜 기존 거처가 안 되는가

| 후보 거처 | 탈락 사유 |
|---|---|
| scan (L1.5) | 합성에 quant·macro·credit(L2) 출력이 필요. L1.5 → L2 상향 import 는 4계층 단방향 위반 |
| quant (L2) | quant → scan import 는 명시 금지 계약 (scanBacktest 스펙 "역방향" 룰). scan 축 결과가 필수 입력 |
| simulate (L2.5) | simulate 는 시뮬레이션·기대 원장 코어. 스크리너 도메인을 넣으면 정체성 오염. 봉인 collector 만 simulate 에 추가(A2)하고 발행자는 밖에 |
| story (L3) | story 는 보고서 산문 조합기. 주기 실행·수치 산출물·ledger 발행은 다른 산출물 계약. dossier 산문만 story 에 위임 |
| ai/tools (L4) | 엔진 능력이지 AI 도구가 아님. AI 는 후속으로 이 verb 를 EngineCall 로 소비 |

### 1.2 import 방향 증명

```
shortlist (L3, story 형제)
  ├─ import scan (L1.5)        : 축 결과 DataFrame        ▼ 하향 OK
  ├─ import quant (L2)         : 신호·forecast·replay      ▼ 하향 OK
  ├─ import macro/credit/industry/analysis (L2)            ▼ 하향 OK
  ├─ import simulate (L2.5)    : issueShortlist collector  ▼ 하향 OK
  ├─ import gather/listing (L1): 유니버스·lazy fetch       ▼ 하향 OK
  └─ import story (L3 동층)    : ✗ 금지. dossier 산문은 역방향(story 가 shortlist 산출물을
                                 입력 DataFrame 으로 받음) 또는 shortlist 자체 표 출력으로 해결
```

- L1.5 4형제 cross import 규칙 비접촉 (L1.5 를 수정하지 않음).
- lint-imports 계약에 shortlist 레이어 행 추가 (L3, story 와 동층·상호 import 금지).

### 1.3 공개 계약 (v0)

```python
import dartlab

result = dartlab.shortlist()                    # 이번 주 board100 + top10 (기본 horizon="1w")
result.board                                    # DataFrame (00 §3.1 스키마)
result.top                                      # DataFrame + dossier dict list
result.coverage                                 # family/신호 커버리지 리포트
result.regime                                   # 적용된 레짐 프리셋 + 판정 근거 refs

dartlab.shortlist(asOf="2026-07-03")            # 재현 실행 (같은 asOf = 같은 결과)
dartlab.shortlist(seal=True)                    # ledger 봉인 동반 (기본 False, 명시 발행)
```

## 2. 신설 파일 · 함수 (본진 배치 시점 기준)

| 파일 | 핵심 함수/클래스 | 역할 |
|---|---|---|
| `shortlist/__init__.py` | `shortlist()` 진입 + `__all__` | 공개 verb SSOT |
| `shortlist/registry.py` | `SignalSpec`, `SIGNAL_REGISTRY` | 신호 선언 정본 (02 §2) |
| `shortlist/harvest.py` | `harvestBulk(asOf)`, `harvestLazy(codes)` | S1 수확 (벌크 우선 + 2-패스 lazy) |
| `shortlist/composite.py` | `rankSignals(df)`, `compose(df, weights)` | S2~S3 정규화 + 선형 결합 |
| `shortlist/weights.py` | `famaMacbethWeekly(panel)`, `shrinkWeights(coefs, lam)`, `purgedWalkForward(...)` | W1 가중 학습 + 검증 (02 §5, numpy-only) |
| `shortlist/gates.py` | `applyHygiene(df)`, `redFlags(df)`, `confluence(df)` | S0 위생 + S5 게이트 |
| `shortlist/board.py` | `buildBoard(asOf)`, `BoardResult` | S4 조립 + 스키마 계약 |
| `shortlist/runbook.py` | `runWeekly(asOf, seal)` | 주간 실행 + 스냅샷 저장 + 봉인 호출 |
| `simulate/expectationCycle.py` (확장) | `issueShortlist(board, asOf)` | ledger 봉인 (simulate 유일 writer 유지) |
| `cli` 서브커맨드 | `dartlab shortlist [--asof --seal]` | 운영 진입점 (P2) |

레지스트리·게이트의 임계값(0.80, k≥3, shrinkage λ·부호안정성 임계)은 `registry.py` 상수 선언 한 곳에만 둔다. 학습된 발행 가중은 fold·protocol 메타와 함께 `data/shortlist/weights_*.parquet` 로 봉인 (재현 가능).

## 3. 테스트 계획 (src ↔ tests 미러 규약)

| 테스트 | 검증 |
|---|---|
| `tests/shortlist/test_registry.py` | SignalSpec 선언 무결(family·방향·verb 경로 실재), 임계값 SSOT 단일성 |
| `tests/shortlist/test_composite.py` | rank 수학 (결측 null 보존, 방향 정렬, family null 전파, 참여<2 제외), 합성 결정성(같은 입력 = 같은 순위) |
| `tests/shortlist/test_weights.py` | Fama-MacBeth 계수 복원(합성 데이터, 알려진 계수 주입 → 회수), shrinkage·부호안정성 게이트, purged embargo 에 라벨 겹침 0 |
| `tests/shortlist/test_gates.py` | 위생 필터 로그(no-silent-cap), red-flag 각 조건, 합류 k 계산, 10 미만 발행 |
| `tests/shortlist/test_board_contract.py` | 스키마 계약(Pandera), refs/asOf 동행, 금지 어휘 grep 게이트 |
| `tests/shortlist/test_pit.py` | pitLagDays 보정, rcept_dt 기준 look-ahead 부재 (합성 fixture) |
| `tests/shortlist/test_seal_roundtrip.py` | issueShortlist 봉인 → scoreDue 채점 왕복 (ledger append-only 준수) |
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
| **P0 개념확립** (_attempts) | `tests/_attempts/shortlist/` 에서 ① gov/prices 벌크 PRICE family 전종목 계산 실측 ② 주간 PIT replay 하네스(G7) ③ 신호 상관 행렬 실측 → 등록 신호 확정(02 §2.2) ④ W1 Fama-MacBeth + purged walk-forward 학습·검증 실측 ⑤ TEXT/뉴스 태깅 커버리지 실측(G8) ⑥ FLOW lazy fetch 소요시간 실측 | 17년 replay OOS 분위 밴드 리포트(학습 가중) 재현 가능 + W0 대비 W1 스프레드 비교 + 커버리지 수치 확보 + 결과 docstring/README 기록 | 폴더 삭제 (src 비접촉) |
| **P1 골격 본진** | 졸업 게이트(모듈화·덕지덕지 제거·클린코드·9섹션 docstring) 후 registry/harvest/composite/weights/gates/board 본진 배치. PRICE+FUND+EVENT 활성, 발행 가중 = P0 학습본 봉인 | `dartlab.shortlist(asOf=...)` 가 board100 산출 + §3 테스트 green + §4 게이트 전부 통과 | `shortlist/` 제거 + 게이트 등록 원복 |
| **P2 근거 심화 + CLI** | 2-패스 lazy(FLOW·TEXT 부분 커버), conformal 게이트, top10 dossier, 금지 어휘 grep, CLI | top10 이 합류 룰 전 조건 충족 + dossier refs 완비 + 실행 <30분 | CLI/dossier 모듈만 제거 |
| **P3 봉인 라이브** | issueShortlist + 주간 채점 + 성적표 + 주간 런북 1p. 최소 1회 봉인→채점 실측 | 실데이터 왕복 1회 증명 + 미검증 라벨 동작 | collector 제거 (ledger 데이터는 append-only 보존) |
| **P4 갭 승격** | G1 수급 벌크(승인 A3) → FLOW 전종목화 · G3 실적 캘린더 · G5 시장조치 · G6 priceCluster. 각각 독립 사이클 + eventStudy 사전 근거 | 신호별 커버리지 상승이 coverage 리포트로 확인 | 신호 선언 제거 (합성기 비접촉) |
| **P5 터미널 서피스** | 별도 미니 PRD 로 분리 (UI 눈검수 + push 승인 게이트 + 공개 터미널 무중단 규약) | 별도 정의 | 별도 |

## 6. 메모리·성능 예산

- 전종목 wide 격자(약 2,800 x ~25 컬럼 x 주간)는 수십 MB 수준. 위험은 격자가 아니라 (a) Company 객체 루프, (b) gov/prices 다년 로드. 방어: PRICE 계산은 필요한 lookback(최대 60거래일 + 52주고가용 260거래일) 연도 shard 만 lazy 로드, Company 사용은 top10 dossier 10종목 순차 한정.
- 새 캐시는 BoundedCache 만. `withMemoryBudget` 예산 선언을 harvest 진입점에 부착 (narrativeRegime 선례).
- 주간 실행 완주 목표 <30분 (lazy fetch 300종목 x rate limit 이 지배 항. P0 에서 실측해 상한 재선언).

## 7. 운영 런북 (P3 산출물 골자)

1. 금요일 마감 후: `dartlab shortlist --seal` (또는 asOf 명시 재현 실행).
2. 검수: coverage 리포트·flags·red-flag 표 눈검수 (수치 조작 없이 발행/스킵만 결정).
3. 봉인 확인: ledger append 건수 = board 행수.
4. 다음 주: `scoreDue` 채점 → 성적표 갱신 확인.
5. 실패 시: 스킵 원장 기록 (03 §4). 임시 파라미터 변경 금지.
