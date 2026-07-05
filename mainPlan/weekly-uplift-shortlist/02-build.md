# 02. 빌드 : 배치 · 파일/함수 · 테스트 · 단계 · 런북

## 1. 배치 : story 동급 L3 신설 엔진 (명칭 = D1 확정 대기, 가칭 simulator)

```
L3  simulator(가칭)      한곳: 전 하위 엔진 호출 → 상 차리기 → 의견화 → 가정 sweep → 파생 뷰
L2.5 simulate            원장 부품 재사용: 봉인(issueReadings 확장)·채점(scoreDue)·append-only
L2/L1.5/L1               기존 그대로 (변경 0. 개별 데이터 작업대는 신설 금지, dossier 는 폐기됨 df41ee60e)
```

import 방향: simulator(L3) → {scan·frame(L1.5), quant·analysis·credit·macro·industry(L2),
simulate(L2.5), gather·providers(L1), core(L0)} 전부 하향 OK. story 와 동층 상호 import 금지.
lint-imports 에 L3 simulator 행 추가.

- 폐기 원칙 반영: 호출계약은 엔진 소유 verb 로만. 엔진 없는 root facade 신설 금지.
- 프론트 작업대(ui runtime data/fetch)는 유지 (본 엔진과 별개 표면).

## 2. 파일 · 함수 (본진 배치 시점)

| 파일 | 핵심 | 역할 |
|---|---|---|
| `simulator/__init__.py` | 공개 verb + `__all__` | 엔진 진입 (명칭 D1 후 확정) |
| `simulator/contract.py` | `Reading` dataclass + 임계 상수 SSOT | 01 §2 |
| `simulator/surfaces.py` | `enumerateSurfaces()` | 카탈로그 자동 열거 + 방향화 선언 레지스트리 (01 §3) |
| `simulator/table.py` | `buildTable(asOf, market)` | 상 차리기: 전종목 x 전표면 스냅 (무bake, 벌크 우선, Company 루프 0) |
| `simulator/opine.py` | `opine(table)` | 의견화: 표면별 direction/score/기권 |
| `simulator/sweep.py` | `sweepAssumptions(readings, grid)` | 가정 격자 실행 + 강건성 집계 (01 §5) |
| `simulator/board.py` | `buildBoard(...)` | board100/top10 + red-flag 게이트 + 근거 서사 조립 |
| `simulator/runweek.py` | `runWeekly(asOf, market, seal)` | 주간 루프 오케스트레이션 |
| `simulate/expectationCycle.py` (확장) | `issueReadings`·주간 `scoreDue` 경로 | 봉인·채점 (유일 writer 유지) |
| `simulate/readingScorecard.py` (신설) | 수축 성적표 (표면 x 시장 x 산업 x 레짐 x 지평 + 가정 벌) | 01 §4~5 |
| cli | `dartlab <verb> [--asof --market --seal]` | 운영 진입 (P2) |

## 3. 테스트 (src ↔ tests 미러)

| 테스트 | 검증 |
|---|---|
| `tests/simulator/test_contract.py` | Reading 무결·기권 1급·임계 SSOT 단일성 |
| `tests/simulator/test_surfaces.py` | 자동 열거 완전성(카탈로그 대비 누락 0)·방향화 선언 존재·무방향 등재 |
| `tests/simulator/test_table.py` | 전종목 완전성(판독/중립/기권 3분법)·Company 미사용·시장 파라미터 |
| `tests/simulator/test_sweep.py` | 격자 결정성·강건성(median) 선정·최고성적 인용 금지 게이트 |
| `tests/simulator/test_board.py` | 스키마(Pandera)·refs 동행·금지 어휘 grep·시장 혼합 순위 부재·10 미만 발행 |
| `tests/simulator/test_pit.py` | pitLag 보정·rcept_dt look-ahead 부재 (합성 fixture) |
| `tests/simulate/test_readingScorecard.py` | 채점 수학·수축 계층 복원·"미검증" 라벨 |
| `tests/simulate/test_seal_roundtrip.py` | issueReadings → scoreDue → 성적 갱신 왕복 (append-only) |

실행: 단일 파일 `bash tests/test-lock.sh ...`, 전체 `uv run python -X utf8 tests/run.py preflight`.
fixture 는 합성 소형 격자 (실데이터 전종목 로드 금지, scope=module).

## 4. CI 게이트 체크리스트 (신규 src 모듈 필수)

- [ ] tests 구조 미러 (`test_structureMirror`) + lint-imports L3 행
- [ ] publicApi manifest + `publicApiScenarios.yml` 등록 + `productSmoke --suite quick`
- [ ] Skill OS `engines.<명칭>` sub-spec 4단계 (lintSkill·capabilityRefs·검색·동기화)
- [ ] workspaceHygiene: 산출 경로 `data/shortlist/` (DATA_RELEASES 등록), 루트 오염 0
- [ ] camelCase·no_emdash·docstring 9섹션 (본진 승격 시)

## 5. 단계 (각 단계 독립 출하·롤백 가능)

| 단계 | 내용 | AC | 롤백 |
|---|---|---|---|
| **P0 잔여** (_attempts) | ① allFilings 타입별 이벤트 표면 2016~ replay 실측 (KR) ② panel PIT(정정 look-ahead) 실측 ③ 표면 상관 행렬 → 수축 묶음 확정 ④ 가정 sweep 프로토타입 (격자 100벌 x 17년 시간 실측) ⑤ 뉴스 태깅 커버리지(G8) | 이벤트+재무 표면이 가격 단독 기준선(edge 0) 대비 기여를 보이는지 분위 밴드로 확인 + sweep 소요 실측 | 폴더 삭제 (src 비접촉) |
| **P1 골격 본진** | 졸업게이트 후 contract/surfaces/table/opine + issueReadings/scorecard 본진. KR 가격+이벤트+재무 표면 활성 | 공개 verb 가 readings+성적 산출 + §3 테스트 green + §4 게이트 통과 | 모듈 제거 + 게이트 원복 |
| **P2 sweep + 파생 뷰 + CLI** | 가정 격자·강건성 선정·board100/top10·사업보고서 서사·금지 어휘 grep·CLI. US 는 fund/event 표면부터 | top10 전 조건 충족 + 시장당 실행 < 30분 | sweep/board 모듈 제거 |
| **P3 라이브 봉인 운영** | 주간 발행→봉인→채점 사이클 실증 + 런북 1p. 가정 벌 라이브 봉인 포함 | 실데이터 왕복 1회 + "미검증" 라벨 동작 | collector 제거 (원장은 보존) |
| **P4 갭 승격** | G1 수급 벌크(A) · G3 실적 캘린더 · G5 시장조치 · G9 US 가격 재bake(A) · G10 US flow · 지평 다중화 활성 | 커버리지 상승이 리포트로 확인 | 표면 선언 제거 |
| **P5 UI 서피스** | 별도 미니 PRD (눈검수 + push 승인 게이트 + 공개 터미널 무중단) | 별도 | 별도 |

## 6. 예산 (P0 실측 근거)

- readings 볼륨: 전종목 x ~100 표면 x 주간 ≈ KR 주 30만 행 (연 1,500만). 연도 샤딩 parquet 충분 (17년 667만 행 로드 0.8초 실측).
- 메모리: 벌크 lazy 로드 + Company 사용은 top10 서사 10종목 순차 한정. `withMemoryBudget` 부착. 참고 실측: Company 30사 순차 RSS ~900MB 정체.
- 시간: 주간 실행 시장당 < 30분 목표 (병목 = flow lazy fetch. 판독·sweep 은 초 단위 실측).

## 7. 주간 런북 (P3 산출물 골자)

1. 시장 마감 후 실행 (`--seal`). 2. 검수 5분: 커버리지·기권·red-flag 눈검수, 개입은 발행/스킵만.
3. 봉인 건수 = readings 행수 확인. 4. 다음 주 채점 → 성적·가중 자동 갱신 확인. 5. 실패 주는
스킵 원장 기록. 임시 파라미터 변경 금지. 초기 8~12주 수동 트리거, 안정 후 cron 승격 별도 상정.
