# 18. 거울 작업대 (Mirror Workbench) 설계 확정 + 개념확립 실측

> v1.0 (2026-07-07). 운영자 지시 "작업대를 완전히 처음부터 다시 세운다. 정공법으로. 장기 유지보수를
> 손으로 하지 않는 방향, 확대되는 것을 자동흡수 가능하게." 6설계 x 2적대심사 + 종합(wf_6c13f3f9).
> 개념확립 데모 = `tests/_attempts/workbench_mirror/` (mirror.py + demo.py, 값 물질화 0).
> 엔진 지도 = 17. 시뮬레이터 사상 = 16.

---

## §1. 폐기 선언 (직전 실패)

`tests/_attempts/workbench/full.py` (10레인) **폐기**. 사인:
- 엔진을 부르지 않고 `simulate/table.py` 내부 리더와 `data/*.parquet` 경로를 직접 팠다 (공개계약 위반).
- 레인 10개를 **손으로 적었다** (확장 시 손 유지보수).
- 계정을 **손으로 6개 골랐다**. 실제 카탈로그는 860종이었고 전수를 돌리니 649종이 실데이터였다.
  그 탓에 "Altman Z 는 계정이 없어 불가"라는 **오답**까지 냈다 (retained_earnings 2793종목 실재).

교훈 = 손 선별은 능력을 숨긴다. 등재는 전수, 도태는 측정.

## §2. 확정 설계 = 거울 작업대 (Mirror Workbench)

**심장**: 작업대는 카탈로그를 소유하지 않는다. 엔진의 자기서술을 매 실행 **거울처럼 반사**한다.
세 부품 순수 합성:

| 부품 | 하는 일 | 자동흡수 |
|---|---|---|
| `reflectCatalog` | 기존 자산 `_injectAxisRegistriesLive` 로 6엔진 축 레지스트리 라이브 반사 | 새 축 등록 = 다음 반사에 자동 등장 |
| `classifyLane` | declared 필드 우선, 없으면 shape morphology 추정 + **AMBIGUOUS 표면화** | 레인 손목록 0 (순수함수) |
| `foldToCanonical` | shape family(~6) 별 어댑터로 단일 tidy 롱 접기 | 접기 분기가 O(shape)이지 O(축) 아님 |

**정규 스키마** (결손 0 대체 금지, 등급은 valueText):
`(engine, axis, item, entity, entityName, period, value:F64, valueText:Utf8, lane, status, gapReason)`

**레인 판정** (축 이름표 아님, 구조 순수함수): yearWide=척추 / entityMetric=단면(문자 우세면 정적) /
envDict·envFrame=환경 / scoreDict=단면 / scalar=환경스칼라 / nested·graph=격리.

## §3. 개념확립 실측 (2026-07-07, demo.py)

1. **반사**: **125축 / 6엔진** (quant 48·scan 27·gather 18·macro 15·industry 9·credit 8) 을 작업대측
   손 축목록 0 으로 획득.
2. **가이드 lossy 실증**: **`declaredLane` 보유 축 = 0/125.** 즉 현재 전 축이 morphology fallback 이다.
   이 숫자가 엔진 `_guide()` extraColumns 확장의 근거다 (`core/utils/axisGuide.py:18` 에 훅 실재 확인).
3. **접기**: 이질 7형태(KR wide 한글열·US wide 영문열·envDict·scoreDict·entityMetric·스칼라·중첩)가
   **22행 11열 단일 정규 롱**으로. 레인 분포 spine 10·static 4·env 3·crossSection 5.
4. **갭 방출**: 중첩 dict(`industry.edges`) -> `nonTabular` 격리 (**환경 레인 유출 0행**). 역할불명 컬럼
   (`시장구분`) -> `unknownColumnRole` 시끄럽게 방출. declared unit 부재 축(`valuation`·`governance`)
   -> `AMBIGUOUS` 표면화. **조용한 삼킴 0.**

5. **지연 물질화 end-to-end** (): 반사 -> 선택 -> 공개계약 호출 -> 접기 가 실제 엔진
   데이터로 끝까지 돈다.  0.7초 ·  0.7초 ·
    0.4초 -> **정규 롱 50,220행**. 삼성전자 2025 = ROE 10.36% ·
   부채비율 29.94% · 이익잉여금 402.14조. 없는 축 호출은 값을 지어내지 않고  갭 1행.
6. **실측으로 잡은 결함 1** (2026-07-07): wide 반환은 항목 정보가 열에 없어, 카탈로그 축의 요청 item 을
   넘기지 않으면 roe 와 debtRatio 가 둘 다  로 찍혀 **구분 불능**이었다. 
   에  인자 추가로 정정. 데모가 없었으면 조용히 오염될 결함.

## §4. 자동흡수의 정직한 범위 (과대포장 정정)

심사 12렌즈 만장일치 정정: **"새 엔진 = 코드 0행"은 거짓.**

| 확대 축 | 손 비용 | 근거 |
|---|---|---|
| 새 계정 (860 -> 900) | **0 (진짜 무손)** | 작업대가 목록 미보유. 엔진 listFn 이 카탈로그 소유 |
| 기존 엔진 내 새 축 | **0** | 엔진 저자가 자기 dispatch 위해 이미 등록. 반사가 집어감 |
| 새 엔진 | **O(엔진) = 1행** | `builder.py:275` `_AXIS_REGISTRIES` 튜플 1행 + 그 엔진 `_guide` extraColumns |
| 새 shape 원형 | **O(상수) = 드묾** | shape family ~6, lane 규칙 5. 미분류는 AMBIGUOUS/gap 으로 강제 표면화 |

**즉 자동흡수 = "데이터 차원 확대에 대해 손 O(1)".** 손이 0 이 되는 게 아니라 **엔진 소유 레지스트리로
이사**한다. `_AXIS_REGISTRIES` 6-튜플은 유일하게 남는 O(엔진) 손이며, 이미 한 번 깨진 이력이 그 파일
docstring 에 박제돼 있다 ("`_AXIS_REGISTRY` 가 scan/__init__ -> scan/router 로 옮겨가며 scan 축 누락").
제거하지 않고 **정직 인정 + 재사용**한다 (재발명 금지, MEMORY §4).

## §5. 계약 강제 (기계 차단, 손 규율 아님)

1. **호출 원시연산 3형태만**: `dartlab.{engine}()` (가이드) · `dartlab.{engine}("{axis}")` (무target 목록)
   · `dartlab.{engine}("{axis}", item, ...)` (물질화). parquet·내부리더로 셀이 등재될 진입점 구조적 부재.
2. **AST 린트 게이트** (`tests/audit/` 상주 예정): 작업대 모듈에서 `scan_parquet`·`read_parquet`·
   `.parquet` 리터럴·`table.`·`Company(`·`_AXIS_REGISTRY` 직독 토큰 발견 시 PR 차단. **최상위 허용
   방식 금지** (`from dartlab.scan.router import _AXIS_REGISTRY` 가 통과하는 구멍) = 명시 blocklist.
3. **Company 물리 배제**: declared `universeScope="perCompany"` 축은 벌크 순회에서 `perCompanyExcluded`
   로 제외. 금지 규칙이 아니라 선언된 scope 로 배제된다.

## §6. 비용 전략 (사전빌드 0)

분류비용과 데이터비용을 분리. **프로브는 축별 1회지 항목별이 아니다** (D 설계의 자멸 회피).
- 반사 = 메모리 dict, ms. 값 0.
- 레인 확정 = 축당 대표 프로브 1회. 860 전수를 프로브 단계에 태우지 않는다.
- 물질화 = 질의가 (engine, axis, item, universe, freq, market) 를 고를 때만 지연 collect + BoundedCache.
- **실측 비용**: 계정 860종 전수 = 18.9분(ok 649·empty 148·fail 2, 1,230,780행) / 비율 13종 = 10.6초
  (133,948행). 이 전수는 **운영자 명시 승인 배치에서만**. 암묵 실행 금지.
- **US 17,367 파일 글롭** = 엔진의 가속 parquet 경로 부재 = **엔진 갭**. 작업대는 사본을 굽지 않고
  `costTag=slow` + `gapReason=noBulkPath` 로 표면화해 엔진 소유자에게 회부 (무승인 빌드 금지).

## §7. 혁신 판정: known-pattern (정직)

12심사 만장일치. 재료 전부 기지: GraphQL introspection · dbt catalog · information_schema reflection ·
Feast on-demand feature view · Ibis 지연 IR · tidy data/melt · entry_points plugin registry.
비자명한 조합 3 (발명 아님): (1) shape(닫힌 ~6) 와 catalog(열린 자동) 의 개폐 경계를 엔진 가이드에 그어
어댑터 수가 O(축)이 아니라 O(형태)로 붕괴 (2) lane 을 declared 역할 순수함수로 + morphology 는 AMBIGUOUS
fallback (3) gap 을 행으로 방출해 coverage 강등에 먹임. **relabeling 을 novel 로 포장하지 않는다.**

## §8. 잔여 + 승인 대기

- **엔진 `_guide()` extraColumns 확장**(returnType·targetRequired·universeScope·laneHint·unit)은 6엔진
  횡단 변경 = **운영자 승인 사안**. 무단 착수 금지. 근거 숫자 = declaredLane 0/125 (§3).
- 졸업 게이트 잔여: Step3 지연 물질화 데모 -> 덕지덕지 제거 -> 클린코드 -> 9섹션 docstring -> 본진.
  본진 위치는 새 엔진 신설이 아니라 기존 `scan`/`reference` 하위 (운영자 토론).
- **검증 전 성공주장 금지**: 본 문서의 설계는 개념확립(§3)까지만 실증됐다. 전 축 물질화·CI 게이트는 미빌드.
