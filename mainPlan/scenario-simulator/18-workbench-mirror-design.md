# 18. 거울 작업대 (Mirror Workbench) 설계 확정 + 개념확립 실측

> 2026-07-22 superseded. 범용 정본은 `mainPlan/unified-data-workbench/`와
> `src/dartlab/data/`다. 순수 shape folding은 `data.factorKernel`로 이관했고,
> 실사용자가 없던 `simulate.mirror` 물질화 드라이버는 제거했다. 아래 내용은 설계 이력이다.

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

5. **지연 물질화 end-to-end** (`materialize.py`): 반사 -> 선택 -> 공개계약 호출 -> 접기 가 실제 엔진
   데이터로 끝까지 돈다. `scan.ratio("roe")` 0.7초 · `scan.ratio("debtRatio")` 0.7초 ·
   `scan.account("retained_earnings")` 0.4초 -> **정규 롱 50,220행**. 삼성전자 2025 = ROE 10.36% ·
   부채비율 29.94% · 이익잉여금 402.14조. 없는 축 호출은 값을 지어내지 않고 `contractError` 갭 1행.
6. **실측으로 잡은 결함 1** (2026-07-07): wide 반환은 항목 정보가 열에 없어, 카탈로그 축의 요청 item 을
   넘기지 않으면 roe 와 debtRatio 가 둘 다 `item="ratio"` 로 찍혀 **구분 불능**이었다. `foldToCanonical`
   에 `item` 인자 추가로 정정. 데모가 없었으면 조용히 오염될 결함.

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

## §8. 정정 : capability 가 이미 선언한다 (제안 철회, 2026-07-07 실측)

운영자 지적 "capability 가 있는데 왜 그게 필요하지". **답 = 필요 없다. §2~§7 이 제안한 엔진 `_guide()`
extraColumns 확장과 `laneHint` 신설은 재발명이었다. 철회한다.**

**실측 증거** (`declared.py`): 축 엔트리 `_AxisEntry` 는 이미 `returnType`·`targetRequired`·`targetParam`·
`listFn` 을 선언한다. 문제는 `_injectAxisRegistriesLive` 가 `label`/`description` 만 남기고 **나머지를
버리는 것**이다. 그래서 declared 가 0/125 로 보였다.

| 엔진 | 축 | returnType | targetRequired | listFn |
|---|---|---|---|---|
| scan | 27 | **27** | 3 | **3** (account·ratio·note) |
| gather | 18 | 0 | 9 | 0 |
| quant | 48 | 0 | 0 | 0 |
| macro | 15 | 0 | 0 | 0 |
| industry | 9 | 0 | 0 | 0 |
| credit | 8 | 0 | 0 | 0 |

버려지던 선언을 싣기만 하면:
- **declared(returnType) 0/125 -> 27/125**
- **선언만으로 lane 확정 26/125.** `laneHint` 불필요 = lane 은 `returnType` + `listFn` 의 **순수함수**
  (listFn 보유 + DataFrame = 카탈로그 원자 = 척추 / DataFrame + target 불요 = 단면 / dict = shape 마무리).
- 척추로 뽑힌 3축 = `scan.account`·`scan.ratio`·`scan.note` = scanAccount docstring 이 "원자" 라 부른 바로 그것.

**정정된 할 일 (새 메커니즘 0)**:
1. `_injectAxisRegistriesLive` 가 선언 필드를 **버리지 않게** 한다 (단일 함수, capability SSOT 내부).
2. 나머지 5엔진은 새 표면이 아니라 **같은 `_AxisEntry.returnType` 을 채운다** (엔진 저자가 `label` 을
   쓰는 그 자리. 축 등록 시 1회).
3. 작업대의 `ENTITY_KEYS` 하드코딩도 철회 대상. capability 계약의 `evidenceSchema.targetKeys`
   (`종목코드`/`stockCode`/`code`) 와 `periodKeys`·`valueKeys`·`unit` 이 이미 SSOT 다.

**교훈(반복 재발)**: 새 메커니즘을 제안하기 전에 기존 자산을 전수 확인하라 (MEMORY §4). 이 세션에서만
세 번 반복됐다: 손 6계정(카탈로그 860종 실재) · "사전빌드 필요"(런타임 벡터로 됨) · guide 확장(선언 실재).

## §9. 잔여 + 승인 대기

- **`_injectAxisRegistriesLive` 가 선언 필드를 버리지 않게 하는 단일 함수 수정** (capability SSOT 내부).
  근거 숫자 = §8 (0/125 -> 27/125). 이 변경은 `capabilities()` 산출을 바꾸므로 skill 산출물 동기화
  (`artifactSync --check`) 동행 필요 = 운영자 승인 사안. 옛 제안(guide extraColumns 6엔진 횡단)은 철회됨.
- 졸업 게이트 잔여: Step3 지연 물질화 데모 -> 덕지덕지 제거 -> 클린코드 -> 9섹션 docstring -> 본진.
  본진 위치는 새 엔진 신설이 아니라 기존 `scan`/`reference` 하위 (운영자 토론).
- **검증 전 성공주장 금지**: 본 문서의 설계는 개념확립(§3)까지만 실증됐다. 전 축 물질화·CI 게이트는 미빌드.

## §10. 구현 확정 (2026-07-07, 6안 x 2심사 + 종합 wf_92b5ae40)

**채택 = F(순서) + E(정규화) + D(ratchet 강제). A(중앙 alias 표)·B(Protocol) 기각.**

- **A 기각**: alias 표는 두 번째 SSOT 라 drift 한다. 실측으로 `credit.axis`·`quant.multiStock` 이 A 의
  alias 7행 어디에도 없어 착수 즉시 자기 게이트가 RED.
- **B 기각**: `runtime_checkable` Protocol 은 6 dataclass 에 약 22 property 를 강제해 부채원장(선언
  없는 축은 없는 대로)과 정면충돌.

**§2 정규화 확정 (alias 표 없음, collapse 없음)**: `_injectAxisRegistriesLive` 한 곳에서 ignore 아닌
필드를 **엔진 네이티브 이름 그대로** 캐리한다. `stockRequired` 는 `stockRequired` 로, `targetType` 은
`targetType` 으로. 접지 않으므로 alias 표가 존재하지 않고, 새 엔진이 새 필드명을 써도 조용히 버려지지
않는다. lane·universeScope 같은 **파생 의미는 저장하지 않고 소비측 순수함수**로 계산.

**PR1 실측 (완료)**: `declared` **0/125 -> 125/125**. 필드 분포 group 56 · stockRequired 48 ·
multiStock 48 · targetRequired 45 · returnType 27 · targetType 27 · hidden 27 · act 15 · targetParam 5 ·
listFn 3. 전부 JSON-safe primitive. 예) `scan.account` = {targetParam: snakeId, targetRequired: True,
returnType: DataFrame, listFn: scanAccountList} = 카탈로그 원자(척추)를 추정 없이 식별.
`quant.altman` = {stockRequired: False} = **벌크 안전을 선언으로 안다** (per-company 추측 불필요).
동행 테스트 `tests/reference/test_capabilityDeclared.py` 5건 green (조용한 누락 0 · 척추 3축 선언 ·
False 보존 · 키 불변 · 비-dataclass 가드).

## §11. 실측으로 기각된 내 주장 3건 (문서 자체 정정)

1. **"artifactSync 6 JSON 동기화 승인 게이트 필요"** (§9 옛 기술) = **부정확**. 실증(2026-07-07):
   `artifactSync --write` 를 돌리면 agent/catalog/web.json 3개가 실제로 drift 한다. 그러나 **내 변경을
   stash 하고 돌려도 같은 3개가 똑같이 drift** 한다 = **기존 부채이지 `declared` 추가의 기여는 0**.
   근거: `deriveArtifacts` 는 `listSkills()`(SkillSpec `.md`) 파생이고 `loadCapabilities()` 를 부르지
   않는다. 따라서 PR1 은 artifactSync 를 동행하지 않는다(남의 부채를 내 PR 에서 고치지 않는다).
   기존 drift 는 별도 "정리: 산출물 동기화" 사안이며 운영자 수동 관리 규칙을 따른다.
2. **"simulate = L2.5 라 기존 가드가 강제"** = **거짓**. `tests/architecture/test_import_direction_layers.py`
   의 `LAYERS` dict 에 `simulate` 가 **없다**. L2.5 배치는 현재 기계 검증도 강제도 안 되는 미매핑 상태다.
   물질화 드라이버 PR 이 `"dartlab.simulate": 2` 를 등록해야 하며, root facade 호출이 import-direction
   테스트를 오탐시키는지는 **미검증**.
3. **"손테이블은 `_AXIS_REGISTRIES` 하나"** = **불완전**. `builder.py:620` 에 `_CALLABLE_MODULE_MAP`
   (scan·macro·quant·industry **4개뿐**, gather·credit 누락 = 이미 drift 중) 이라는 **둘째 손테이블**이
   있다. 새 엔진은 두 곳을 손편집해야 한다. 자동흡수는 **새 축엔 기계 보증, 새 엔진엔 2 손테이블**로
   부분적이다 (과장 금지).

## §12. 남은 PR (순서, 각 단독 되돌림)

- **PR2 부채원장 게이트**: `tests/audit/axisDeclaredCoverage.py` + baseline JSON. 미선언 집합은 축소만,
  축수 동결(엔진 탈락 = RED). 두 손테이블(`_AXIS_REGISTRIES`·`_CALLABLE_MODULE_MAP`) 완결성 단정 동행.
  신규 게이트 신설 금지 = `tests/run.py` `GATES["lint"]` 체인에 append.
- **PR3 순수 커널 졸업**: `_attempts/workbench_mirror` 의 reflect/classify/fold 를
  `reference/capability/mirror.py`(L1.5) 로. **raw 레지스트리 재반사 금지, `loadCapabilities()` 소비.**
  엔진 데이터 0 (메모리 가드).
- **PR4 물질화 드라이버**: `simulate/mirror.py`(L2.5). root facade 함수로컬 호출, BoundedCache,
  축별 1회 프로브(Company 루프 금지). `LAYERS` 등록 + `tests/audit/workbenchPurity.py`(import allowlist
  + parquet/Company denylist 이중화).
- **PR4+ (선택, 미룸)**: 5엔진 `returnType` 백필. 작업대는 이것 없이도 morphology fallback 으로 동작하니
  **필수 아님**. 성적표 숫자가 생긴 뒤 엔진별 독립 PR.

## §13. 지금 하지 말 것

중앙 alias 표 · Protocol 강제 · universeScope/laneHint 발명(이미 stockRequired·hidden 존재) ·
PR1 에 artifactSync 승인 게이트(팬텀) · 성적표 전 5엔진 백필 · materialize 를 L1.5 배치(순환) ·
전축 Company 루프 물질화(OOM) · 새 최상위 verb.

## §14. 구현 완료 (PR1~4 green, 2026-07-11)

- **PR1 (7c113f002)**: `_injectAxisRegistriesLive` 가 선언 필드를 버리지 않게. declared 0/125 -> 125/125.
  네이티브 이름 캐리(alias 표 없음). 테스트 5건. arch 44·ref 37 green.
- **부채 청산 (3f9f3d625)**: skill 산출물 stale drift 3파일(runtime/notebooks.md 갱신 미반영) 동기화.
  내 변경 무관(stash 대조), 결정론·byte-동일 검증 후 별도 "정리" 커밋.
- **PR2 (a955c9a5c)**: `tests/audit/axisDeclaredCoverage.py` 부채 원장 게이트 + baseline. 세 부채 동결
  (축수·미선언·손테이블 불일치 credit/gather). 부정테스트로 exit 2 검증. run.py lint 체인 append.
- **PR3 (0cbaf1b89)**: 순수 커널 `reference/capability/mirror.py`(L1.5) 본진. loadCapabilities 소비
  (raw 재반사 0). reflectAxes·laneOf·foldToCanonical·universeScopeOf. 테스트 7건, 엔진 데이터 0.
  9섹션 docstring(Example 실행 검증). universeScope 발명 철회 = stockRequired 선언 사용.
- **PR4 (3aeac5bb2)**: 물질화 드라이버 `simulate/mirror.py`(L2.5). 공개계약 호출만. bulkSelects(카탈로그
  무target 전개·per-company 제외)·materialize·runWorkbench(coverage 성적표). simulate LAYERS L2 등록
  (신규 위반 0 실측, Company.simulate facade 를 _FACADE_PATTERNS 등재). workbenchPurity.py AST 가드
  (parquet/Company/_AXIS_REGISTRY denylist + import allowlist) run.py append. 테스트 5건.

**자동흡수 실현**: 새 축은 declared 싣기만 = 코드 0. 새 계정(860->900)은 카탈로그 무target 전개라 코드 0.
새 엔진은 2 손테이블(PR2 가 회귀 감시). laneHint·universeScope·guide extraColumns 발명 전부 철회
(선언 실재). 정직한 크기 = 데이터 확대 O(1), 엔진 확대 O(엔진).

**잔여**: US(edgar) 물질화(glob 느림, 축별 costTag). 5엔진 returnType 백필(선택, morphology fallback
동작). 이 둘은 작업대 필수 아님 = 성적표 숫자 근거 후 독립.
