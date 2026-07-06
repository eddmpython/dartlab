# scan 컴포저블 쿼리 엔진 (시그니처 스크리닝 SSOT)

> 상태: 진행 중 (2026-07-06 착수). SSOT = 본 폴더. 부모: [[scan-note-cross-section]] (note 횡단, 완료).
> 근거: 전문에이전트 4관점 패널(재무-도메인·쿼리-아키텍처·악마의변호인·통합PM) + 시니어 종합. 운영자 결정: "정공법, 끝까지."

## 배경 / 정공법 한 줄

모든 기초데이터를 자유자재로 조합해 복잡한 조건도 쉽고 빠르게 조회하는 시그니처. 착지 유스케이스: 주가 급락기 재무안전 종목 발굴. 패널 결론:
**scan = primitive 깨끗한 출력 위에서 도는 얇은 선언형 dict spec 엔진. 새로 굽지 말고(런타임 계산), raw SQL을 계약으로 노출하지 말고(조용한 오답), 저장 spec을 언어중립 JSON SSOT 한 곳으로 삼아 python·왓처·프론트가 같은 파일을 소비.**

## 패널 판정 (6 분기)

- **F1 거처**: scan=stateless 메커니즘(spec→멤버셋). 왓처=저장 spec `{id,version}` 구독 + 멤버십 diff만. 왓처 screen 재구현 0.
- **F2 굽기**: 신규 bake 0. 원천 횡단은 이미 완료(finance/report/note/valuation), 파생·시계열·상대는 쿼리시점 in-memory(~2700행=밀리초, 런타임-SSOT "정말 불가능" 실측 통과 못 함).
- **F3 표면(핵심)**: 하이브리드. 도메인 시맨틱 dict spec=계약 표면, 실행=materialize된 primitive 프레임 위 polars + 기존 `DuckDbCrossScan`(OOC substrate). **raw SQL 계약 노출 금지**(synonym·CFS/OFS·결산월환원·Q4 standalone 의미론은 Python resolver에 사는데 SQL은 이를 우회해 조용한 오답 + common_workbench 위반). 정합 locus = materialize된 primitive 컬럼.
- **F4 파생/시계열/상대**: 폐쇄 vocabulary 명명 AST(문자열 eval 금지) + 단위 전파, L1.5 scan. `_RATIO_DEFS {numer,denom,pct}` 패턴 확장.
- **F5 저장 spec**: 경량 JSON `screens/*.json`(accountMappings급 config), recipe/skill 재사용 안 함. 프리셋 8종 강제 흡수 금지(등급축 미모델링 회귀 위험).
- **F6 소비**: JSON 레지스트리를 python·왓처·프론트가 동일 SSOT로. PM 실측: 퍼블릭 터미널이 이미 스크리닝 3~4중 재구현(metrics.ts + ScreenBuilder setPreset + evalCond + duckdb-wasm) 하는데 아무도 python spec 소비 안 함 → 진짜 언락은 언어중립 JSON.

## 실측 그라운딩 (2026-07-06, flagship 정정)

계정 snakeId 실존 확인: `cash_and_cash_equivalents`·`shortterm_borrowings`·`operating_profit`·`interest_expenses`·`cash_flows_from_operating_activities`·`net_income`·`depreciation_amortization`·`bonds`/`shortterm_bonds`/`current_portion_of_bonds`·`longterm_borrowings`/`current_portion_of_longterm_borrowings`. 비율: debtRatio·currentRatio·equityRatio·operatingCfMargin 존재, **icr 없음(파생 필수)**. krx 지표 31종(sma/ema/rsi/roc12/momentum10...), **return3m 없음** → 급락 조건은 roc12/momentum10. EBITDA proxy = operating_profit + depreciation_amortization.

## 1. 목표 / 범위 (4 단계)

- **Phase 1 (본 사이클, bake/registry/language 0)**: `executeScreenSpec`에 optional `define` AST(계정간 산술 + 단위전파 + spec-로컬 meta 우선조회) + note를 `_catalog`에 additive 등재(concept 등재, 항목은 on-demand 주소 `note.<concept>@<account>`). `define` 없는 기존 spec 회귀 0. 하락장 안전 스크린 ~80% 표현.
- **Phase 2**: `screens/*.json` JSON SSOT + flagship spec + 복합축 field 승격(debt.riskGrade·audit.opinion·quality.ocfToNi 정규화 shim) + 왓처 구독.
- **Phase 3**: period-보존 loader `_loadFieldSeries`(병행) + trend(YoY/CAGR/N년 slope/all-positive)·percentile(업종 백분위/z-score). 업종 sector join 선provision.
- **Phase 4**: 퍼블릭 scan 뷰가 `screens/*.json` 렌더 + live 계산. TS 3~4중 정의 붕괴. 운영자 눈검수 격리(자동push 금지).

## 2. 영향 파일 / 함수 (Phase 1)

- `src/dartlab/scan/builders/kr/report/fields.py`: `_computeDerived(spec)` + `_topoSortDefines` + `_evalDefineNode` + `_resolveOperand` + `_deriveUnit` 신규. `executeScreenSpec` 진입부에서 derived 계산해 spec 사본에 stash. `_loadFieldValues`/`_fieldMeta`가 `@name`(파생) + `note.<concept>@<account>`(노트) 해소. `_conditionFrame`이 spec 전달.
- `src/dartlab/scan/builders/kr/report/fieldCatalog.py`: `_noteCatalogRows()` 신규(SCAN_NOTE_CONCEPTS 개념당 1행, source="note", 항목 on-demand). `_catalog()`에 additive.
- `tests/scan/test_screen_define.py` 신규: 파생 AST(sub/div/mul/add·단위전파·topo·cycle·undefined·@ref 체인·회귀 0) + note field 해소.
- SKILL.md scan screen 섹션에 define 문법 추가.

## 3. 데이터 계약 / 문법 (Phase 1)

```json
{ "define": {
    "netCash":      {"op":"sub","left":"finance.account.cash_and_cash_equivalents","right":"finance.account.shortterm_borrowings"},
    "netCashToCap": {"op":"div","left":"@netCash","right":"krx.marketCap"},
    "icr":          {"op":"div","left":"finance.account.operating_profit","right":"finance.account.interest_expenses"} },
  "where": [ {"field":"@netCashToCap","op":">","value":0.3}, {"field":"@icr","op":">","value":3},
             {"field":"finance.ratio.debtRatio","op":"<","value":100},
             {"field":"finance.account.cash_flows_from_operating_activities","op":">","value":0} ],
  "sort": {"field":"@netCashToCap","desc":true}, "limit":40 }
```
규율: (a) `_fieldMeta`가 `define`을 `_catalog`보다 먼저 조회(파생 leaf/결과에도 단위·연산자 검증). (b) 단위대수 `_deriveUnit`: add/sub 동일단위 강제, div 동일→"배"(무차원)·상이→lu/ru, 리터럴=무차원, div-by-zero→null. (c) define 위상정렬 + 순환/미정의 즉시 ValueError. (d) 연산 vocabulary 폐쇄(add/sub/mul/div + field passthrough), 문자열 eval 금지. (e) note: `note.<concept>@<account>` = scan/note/<concept>.parquet 필터 후 종목별 최신 valueNum. concept만 catalog 등재.

## 4. 테스트 / 게이트

- 신규 unit(test_screen_define): 파생 정확·단위전파·에러(순환/미정의/단위불일치/미정의연산)·@ref 다단·note 해소·**회귀(define 없는 spec 동일)**.
- dartlabGuard strict l0-l15(구조미러·4계층) + publicApiCoverage(screen 축 불변) + productSmoke quick.
- 4계층: fields.py(L1.5 scan) → scanAccount(L1)/scan.note(L1.5) 합법.

## 5. 롤백 / 리스크 + 이중평가

- 롤백: fields/fieldCatalog revert + 테스트 삭제. `define` optional이라 기존 `scan("screen", spec)` 순수 additive, 회귀 0.
- 리스크: (a) 파생 leaf가 report(문자열)면 _numericExpr 강제. (b) note @account 이름은 회사별 표기차(account 정규화명 사용). (c) 단위전파 미스매칭은 ValueError로 조기 차단(조용한 오답 회피). (d) inner-join 유니버스 축소는 의도된 동작(계산 불가 종목 제외).
- 개발자 평가: 기존 `_RATIO_DEFS` 선언형 패턴 확장, eval 없음, 실행은 기존 polars/DuckDbCrossScan 재사용, additive 회귀 0.
- PM 평가: flagship이 한 spec으로 표현 = 시그니처 증명. JSON SSOT는 Phase 2에서 왓처·프론트 3자 소비 언락.

## Do-not-build (덕지덕지 차단, 채택)

raw SQL 계약 노출 · 파생/시계열용 신규 bake · note lineitem 수천행 평탄화 · 문자열 eval · recipe/skill 위 registry 재구축 · 프리셋 강제 흡수 · 왓처 신규 엔진 · `_latestWideValue` 대공사 · 미증명 registry에 소비자 선배선 · JSON SSOT 없는 python-only DSL.

## 운영자 결정 (정공법=끝까지 반영, Phase 2+)

- 업종 sector join(Phase 3): loadListing 업종 컬럼 provision (있으면 좋은 것 → 간다).
- 이자부채/EBITDA: 순차입금 = (shortterm+longterm_borrowings + current_portion + bonds 계열) - 현금. EBITDA = operating_profit + depreciation_amortization. curated 파생으로 제공.
- screens/*.json 거처·거버넌스: 운영자 수동 저작·review(accountMappings/Skill OS급). 거처 Phase 2 확정.
- 복합축 등급 정규화: 한글 등급 → 안정 enum shim(컬럼 드리프트 차단).

## 진행 원장

- 2026-07-06: 착수. 전문에이전트 패널 완료(5 에이전트) + 시니어 종합. 실측 그라운딩(flagship 계정 5개 정정). Phase 1 구현 시작.
- 2026-07-06: **Phase 1 완료.** `executeScreenSpec`에 `define` 폐쇄 vocabulary AST(add/sub/mul/div + field passthrough, 위상정렬, 단위전파, 0나눗셈→null, 문자열 eval 없음) + `@name` 파생 참조 해소 + note field(`note.<concept>@<항목명>`) resolver + fieldCatalog note 개념 등재(평탄화 안 함). `define` 없는 spec 회귀 0(원본 무변경).
- 2026-07-06 게이트: 신규 유닛 17 pass(파생·단위·topo·순환·미정의·div0·회귀·note) + 기존 fields 8 회귀 0 · ruff clean · publicApiCoverage OK(scanAxes 25 불변) · dartlabGuard strict l0-l15 PASS(7 rules, 외부 6 게이트, active debt 0).
- 2026-07-06 실측: flagship define(순현금=cash-단기차입, icr=영업이익/이자비용) 실 finance 데이터 통과 → 나노신소재(ICR 117.9·부채 50.9·OCF+·순현금 127.7억) 걸러짐. 좁은 이유=interest_expenses 커버리지 78종목(Phase 2 복합축 승격이 해결). 커버리지 좋은 필드(순현금+ 저부채<30%)로 8종목(LG 1.5조·SK스퀘어·LG생활건강·HMM 등) → 엔진 스케일 증명.
- 2026-07-06: **Phase 2a 완료 (JSON SSOT 키스톤).** `src/dartlab/scan/screens/*.json` 저장 스크린 config(운영자 수동 저작, accountMappings 급 거처) + `scan/screen` 에 `loadScreen`/`listScreens` + `scan("screen", id)` dispatch(프리셋 보존, 강제 흡수 안 함). flagship `financialStabilityDrawdown.json`(순현금>0 + 저부채<80 + 유동>150 + 자본>0). 패키징 `src/dartlab/**/*.json` 포함 확인.
- 2026-07-06 게이트: 신규 유닛 7(로드·목록·에러·flagship 스키마·dispatch) pass · ruff · publicApiCoverage OK · dartlabGuard strict l0-l15 PASS. 실측: `scan("screen","financialStabilityDrawdown")` 로 삼성전자(순현금 53.8조·부채 30%·유동 254%)·현대모비스·LG·SK스퀘어 등 랭킹. 언어중립 JSON SSOT = python 실행 증명, Phase 4 에서 프론트/왓처 동일 파일 소비.
- 잔여: **Phase 2b 복합축 승격**(debt.riskGrade·audit.opinion·quality.ocfToNi 정규화 shim + 컬럼 드리프트 가드, 축 스캐너 전수 정독 필요해 flagship production 품질화) / Phase 3(시계열·상대, sector join) / Phase 4(퍼블릭 UI, 눈검수) + 왓처 구독(flagship 증명 후 배선).
