# 05. 구현 및 검증 장부

## 1. 최종 구조

내부 폴더와 단방향 import 규율은 유지했다. 공개 제품 흐름은 다음으로 고정했다.

```text
공시 원문 -> Company와 Panel -> Analysis, Credit, Industry, Quant, Macro
                            -> Story, Report, Simulate, Ask
여러 기업 -> Scan과 Screener
```

다섯 렌즈를 하나의 종합점수로 합치지 않는다. 각 렌즈가 독립적인 결론, 근거, 시점, 결손과 반증 조건을 반환한다.

## 2. 공통 계약

SSOT는 `src/dartlab/synth/lensContract.py`다.

- `identity`, `time`, `status`, `conclusion`, `confidence`
- `drivers`, `evidence`, `assumptions`, `gaps`, `scenarios`, `falsifiers`
- 엔진별 의미를 보존하는 `payload`
- `asOf`, `dataAsOf`, `knowledgeBoundary` 시간 경계 검증
- `usable`인데 evidence가 없거나, 제한 상태인데 gaps가 없는 결과 차단
- 기존 결과의 target, market, asOf와 `blockRefs` 정합성 검증

UI 계약은 `ui/packages/contracts/src/lensProduct.ts`가 같은 의미를 소비한다.

## 3. 다섯 대표 제품

| 렌즈 | 대표 축 | 구현 위치 | 제품 중심 |
|---|---|---|---|
| Analysis | `종합평가` | `analysis/financial/representative.py` | 이익, 현금, 회복력, 품질의 최소 충분 계산과 위험 |
| Credit | `등급` | `credit/product.py` | dCR 등급, 동인, 하방 스트레스, tripwire와 divergence |
| Industry | Company 무인자 | `industry/product.py` | 가치사슬 위치, peer 근거, profit pool, 관계 최신성 |
| Quant | `괴리` | `quant/product.py` | 펀더멘털 변화, 기대 프록시, 가격 반응의 불일치 |
| Macro | `전파` | `macro/transmission/_product.py` | 거시 관측에서 산업, 회사 재무, 가치 레버까지의 경로 |

기존 무인자 가이드와 세부 축은 삭제하거나 숨기지 않았다. 대표 축 결과에 `product`를 additive하게 붙여 상세 능력과 호환성을 모두 유지했다.

## 4. 상위 워크플로

### Story와 Report

- `story/lensProducts.py`가 같은 Company 세션에서 필요한 대표 제품을 한 번씩만 수집하고 캐시한다.
- 공개 bundle에서 내부 원본 `results`를 제거한다.
- Story JSON, Markdown과 ReportModel이 `lensProducts`, `lensSummary`, `lensGaps`를 소비한다.
- Story와 Report는 렌즈 숫자와 사실을 다시 계산하지 않는다.

### Simulate

- `SimulationResult`가 `lensProducts`와 `assumptionLedger`를 보존한다.
- 결정론 DriverSheet 입력과 렌즈의 맥락 가정을 구분한다.
- 렌즈 시나리오는 `appliedToDriverSheet=false`로 기록되어 결정론 해시를 바꾸지 않는다.

### Ask

- EngineCall이 dataclass를 구조적으로 직렬화한다.
- 대표 제품의 직접 `valueRef`, `dateRef`, `executionRef`를 만든다.
- Ask는 정적 엔진 import나 별도 점수 계산 없이 기존 도구 결과를 설명한다.

### Scan과 Screener

- screen JSON과 생성된 TypeScript preset이 같은 정의를 소비한다.
- 조건별 `passed`, `failed`, `unknown`을 구분하고 결손을 탈락으로 위장하지 않는다.
- Python과 UI conformance fixture, URL 저장과 재실행, 결과 설명과 export를 연결했다.

## 5. Terminal과 공개 발행

- `DartLabRuntime.lens`를 public, local, fake runtime 모두에 필수 포트로 배선했다.
- 로컬은 `/api/company/{code}/lenses`에서 Python 엔진 bundle을 직접 소비한다.
- 공개 Terminal은 `landing/lenses/{code}.json`에 발행된 같은 bundle만 읽는다.
- 브라우저에서 제품 점수나 결론을 재구현하지 않는다.
- 미발행 종목은 임의 판단 대신 `대표 렌즈 제품 미발행`을 표시한다.
- Terminal은 3개와 2개의 두 줄 배열로 다섯 렌즈를 독립 표시하며 기존 브라우저 합성 `종합 판정`을 제거했다.
- `pipeline/lensArtifacts.py`와 `landing/_scripts/buildLensProducts.py`가 JSON 직렬화, 내부 원본 제거, 최소 제품 수와 성공률을 검증한다.
- `.github/workflows/lensProductsBuild.yml`이 scan SSOT의 전 상장사를 24개 shard로 계산하고 완전성 검증 뒤 한 번에 발행한다. `--code`는 단일 종목 실측과 복구에만 사용한다.

공개 artifact는 전 상장사 coverage를 강제한다. 제품 계산에 실패한 회사도 파일 자체를 누락하지 않고 다섯 렌즈의 구조화된 blocked 결손으로 발행하며, 브라우저에서 의미가 다른 fallback을 계산하지 않는다.

## 6. 문서 정보구조

- 루트 README 첫 제품 설명을 레이어에서 `공시에서 판단까지` 흐름으로 교체했다.
- 다섯 렌즈를 같은 형식의 질문, 대표 호출, 결과로 설명한다.
- Story, Simulate, Ask를 사실 엔진이 아닌 조합 워크플로로 설명한다.
- 내부 L0부터 L4 규율은 루트 `ARCHITECTURE.md`로 이동했다.
- 레이어 번호는 import 규율이지 제품 등급이나 학습 순서가 아니라고 명시했다.

## 7. 검증 기록

### 자동 검증

- Lens contract와 다섯 대표 제품 단위 테스트
- Story, Report, Simulate, Ask 집중 회귀
- Scan screen Python과 TypeScript conformance
- UI contracts TypeScript 검사
- UI surfaces Svelte 검사 0 errors
- Story Skill OS lint
- 공개 artifact 원자 저장, private results 제거와 제품 하한 테스트
- 서버 lens route의 private results 제거 테스트
- 공개 scan과 industry 결과에서 자동 선정한 40개 기업 성숙도 캘리브레이션

### 최종 감사

- `dartlabGuard strict --scope l0-l15 --providers dart,edgar`: 1,581개 파일, 규칙 실패 0, 외부 게이트 6개 전부 통과
- Company facade 보호 원장은 기존 17건을 그대로 유지했고 신규 아키텍처 부채는 0
- 변경 Python 전체 `ruff check`와 `git diff --check` 통과
- UI Contracts TypeScript 검사 통과
- UI Surfaces와 Local App Svelte 검사 각각 0 errors, 기존 warnings만 존재
- Runtime 전체 TypeScript 검사는 기존 `ipoReportSource.test.ts:25` 오류 1건, Landing 전체 검사는 기존 `richMarkdown.ts:91` 오류 1건만 남음. 이번 렌즈 변경 경로는 통과
- Scan preset 생성물 check, Skill OS lint, workflow YAML parse 통과
- 전 상장사 선택 dry-run은 중복 없는 2,808개 종목, 24개 shard 각각 117개로 확인
- shard 분할, 완전 coverage 병합, 계산 실패 결손 artifact 테스트 통과
- 최종 렌즈 관련 통합 회귀 225개 통과
- 40개 기업 캘리브레이션은 40/40 계산, hard issue 0, 모든 품질과 성능 gate 통과

### 실데이터와 실렌더

2026-07-18 삼성전자 `005930` 기준:

| 렌즈 | 상태 | 대표 결론 | confidence | evidence | gaps |
|---|---|---|---:|---:|---:|
| Analysis | usable | 재무 기반 보통 | 100.0 | 6 | 0 |
| Credit | usable | dCR-AA | 95.0 | 6 | 1 |
| Industry | usable | 반도체, 전공정 FAB | 86.7 | 6 | 2 |
| Quant | usable | 괴리 판단 보류 | 65.0 | 3 | 1 |
| Macro | partial | 거시 역풍 경로 우세 | 70.0 | 6 | 3 |

- 공개 JSON 43,524 bytes, product 5개, `noComposite=true`
- 로컬 Terminal에서 5개 행과 각 상태, 시점, evidence와 gap 수 렌더 확인
- 기존 `종합 판정` DOM 항목 0개 확인
- 현재 Company 전체 계산은 약 70초이며, 40개 기업군에서는 중앙값 81.1초, p95 103.8초, 최대 1.48GB를 기록했다.
- 실제 렌더를 보고 1행 5열을 3개와 2개 두 줄 구조로 조정

## 8. 운영 불변조건

1. 새 렌즈 제품은 `validateLensProduct`를 통과해야 한다.
2. UI가 Python 엔진의 결론이나 score를 다시 계산하면 안 된다.
3. Story와 Report가 하위 사실을 다시 계산하면 안 된다.
4. Simulate의 렌즈 맥락이 DriverSheet를 암묵적으로 바꾸면 안 된다.
5. 공개 bundle에 내부 `results`를 포함하면 안 된다.
6. 다섯 렌즈를 하나의 종합점수로 합치면 안 된다.
7. 미발행과 결손을 정상값이나 중립점수로 대체하면 안 된다.
8. README 전면에 레이어 번호를 사용자 학습 순서로 되돌리면 안 된다.
9. `confidence.score`를 예측 확률로 설명하면 안 된다. 이는 엔진별 방법으로 계산한 근거 충족도다.
10. 대표 제품이 전체 시장 parquet를 먼저 materialize하면 안 된다. 필터와 projection을 collect보다 앞에 둔다.

## 9. 다기업 제품 성숙도 캘리브레이션

### 기업군 선정

`tests/calibration/lensProductCalibration.py`가 공개 `dartlab.scan`과 `dartlab.industry` 결과만 사용해 기업군을 자동 선정한다. 수동으로 성공 기업을 고르지 않는다.

- 후보 2,768개
- 최종 40개
- primary 산업 34개와 미분류 1개 범주
- 수익성, 성장, 부채, 가치평가, 시가총액의 5분위와 scan coverage를 함께 덮음
- 기업마다 새 프로세스에서 다섯 대표 제품을 계산하고 계약, 상태 정직성, 유용성, 판단력, 시간과 메모리를 검사

### 수정 전과 수정 후

| 항목 | 수정 전 | 수정 후 |
|---|---:|---:|
| 계산 완료 | 40/40 | 40/40 |
| hard issue | 2 | 0 |
| Analysis usable | 39 | 39 |
| Credit usable | 35 | 36 |
| Industry usable | 38 | 38 |
| Quant usable | 1 | 31 |
| Macro usable | 40 | 26 |
| 최대 peak RSS | 8,333.9MB | 1,484.3MB |
| p95 실행시간 | 93.6초 | 103.8초 |
| 최종 gate | 실패 | excellent |

Macro usable 감소는 회귀가 아니다. 회사 직접 근거가 전체 전달경로의 절반 미만이면 `partial`로 낮추도록 상태 과장을 제거한 결과다. p95 증가는 2개 격리 워커 동시 실행의 경합을 포함하지만 180초 기준 안에 있다.

### 실제로 발견하고 고친 문제

1. Quant가 연결손익계산서 `CIS`를 제외해 40개 중 38개에서 펀더멘털 근거를 잃고 있었다. `IS`와 `CIS`를 모두 읽도록 수정했다.
2. Quant 기대 프록시가 1,315만 행의 finance parquet를 먼저 전부 적재했다. 연간, 연결, 2개 연도, 순이익 계정을 lazy filter한 뒤 collect하도록 바꿔 개별 Quant peak RSS를 7,536.0MB에서 344.4MB로 95.4% 줄였다.
3. 7개 가격행뿐인 기업에서 EMA, RSI, ATR, ADX, Supertrend가 기간 인덱스를 넘었다. 짧은 시계열은 정렬된 NaN 결과로 정직하게 반환하도록 보강했다.
4. Analysis 대표 제품이 18개 하위 계산을 중복 실행했다. 결론에 필요한 이익, 현금, 회복력, 품질 6개 계산으로 줄이고 관측 동인에서 시나리오를 직접 만들도록 바꿨다.
5. Macro는 회사 근거 edge가 하나만 있어도 usable이었다. 회사 근거 coverage 50%를 usable 하한으로 고정했다.

### 최종 상태 분포

| 렌즈 | usable | partial | blocked | nonblocked 유용성 |
|---|---:|---:|---:|---:|
| Analysis | 39 | 1 | 0 | 100% |
| Credit | 36 | 4 | 0 | 100% |
| Industry | 38 | 0 | 2 | 95% |
| Quant | 31 | 9 | 0 | 100% |
| Macro | 26 | 14 | 0 | 100% |

최종 결과는 40/40 계산, 실패 0, hard issue 0, review issue 3이다. review issue는 Analysis와 Credit 결론의 긴장을 사람이 검토하도록 남긴 교차 렌즈 경고이며 계약 실패가 아니다. build, contract, utility, decisiveness, latency, memory, performance gate가 모두 통과했다.

## 10. 최종 판정과 다음 우선순위

### 판정

현재 정의한 Lens Product gate 기준에서 아키텍처는 훌륭한 수준이다. 다섯 엔진격 폴더와 공개 렌즈 구분은 과하지 않다. 실제 과잉은 Analysis의 중복 계산과 Quant의 전시장 materialization처럼 대표 제품 내부 실행 경로에 있었고, 구조를 줄이지 않고도 제거됐다.

따라서 방향은 다음으로 고정한다.

1. 폴더 구조와 다섯 공개 렌즈를 유지한다.
2. README와 UI에서는 레이어가 아니라 공시에서 판단까지의 흐름으로 설명한다.
3. 축 수나 새 엔진 수를 늘리기 전에 개별 렌즈의 대표 질문, 근거, 결손, 반증과 실행비용을 강화한다.
4. 다섯 렌즈를 단일 점수로 합치지 않고 충돌 자체를 검토 대상으로 보존한다.
5. 전 상장사 공개 발행은 사전 계산 artifact로 제공하고 브라우저에서 재계산하지 않는다.

### 남은 제품 강화 순서

1. Quant 실제 애널리스트 컨센서스: 현재 40/40이 명시적 unsupported다. 프록시를 실제 컨센서스로 가장하지 않는 상태에서 정식 데이터 계약을 추가한다.
2. Macro 회사 직접 근거: 금리, 환율, 유가, 수요 경로별 회사 evidence binding을 늘려 partial 14건을 줄인다.
3. Industry 수요와 가격결정력: 40/40 미모델링 상태이므로 갱신시점과 출처가 있는 명시 모델을 만든다.
4. Credit 공시리스크: 39/40 결손인 축을 실제 제재, 감사, 정정공시 근거에 연결한다.
5. Industry 관계 금액 coverage: 38/40이 부분 근거이므로 거래관계 방향뿐 아니라 금액과 관측시점을 보강한다.

이 다섯 항목이 개선되기 전에는 새 공개 엔진이나 대표 축을 추가하지 않는다.
