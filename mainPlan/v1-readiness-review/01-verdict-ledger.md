# v1.0.0 준비도 전수 검토. 판정 원장

> 이 문서는 판정과 근거만 담는다. 선언은 다루지 않는다.
> 게이트 정의 SSOT = memory `release_gate`. 그 규칙대로 본 체크리스트는 **불가 판정 도구**이고
> 가능 선언 트리거가 아니다. 전부 통과해도 "기준 충족, 선언 대기" 이상은 적지 않는다.

## 진행 방식

계층 아래에서 위로 순차 검토한다. L0 core -> L1 gather, providers -> L1.5 scan, frame, synth,
reference -> L2 analysis, macro, quant, industry, credit -> L2.5 dataHub -> L3 story, simulate ->
L4 소비자, ai, mcp. 아래층 결함이 위층 전부를 오염시키므로 순서를 지킨다.

각 계층은 네 기준으로 본다. 혁신성, 완성도, 모듈화와 구조화, 클린코드. 미달이면 리팩터링을
검토하고 추진한다.

### 계층 완료와 세션 인계 강행 방식

한 번에 한 계층만 다룬다. 아래 계층을 완료하기 전에 위 계층 감사, 수정, 최적화를 병렬로
벌이지 않는다. 전문 검토도 현재 계층 안에서만 나눈다.

**작업의 유일한 완료 단위는 레이어다.** 파일, 함수, audit 항목, 원장의 `L0-01` 같은
내부 번호는 레이어를 닫기 위한 증거 묶음일 뿐 별도 작업 단위가 아니다. 내부 파일 하나를
고쳤다는 이유로 완료 보고, 세션 인계, 사용자 `계속` 대기, 상위 레이어 이동을 하지 않는다.
현재 레이어의 모든 src와 실제 호출자를 큰 책임 흐름으로 묶어 연속 처리하고, 레이어 완료
조건을 전부 충족할 때만 다음 레이어로 이동한다.

각 계층은 다음 일곱 칸을 순서대로 닫는다.

1. 현재 범위와 실제 호출자
2. 제품 행동에서 재현된 결함
3. 결함의 근본 원인과 단일 SSOT
4. 테스트와 함께 적용한 수정
5. 실제 공개 행동, 정확성, 속도, 메모리 실측
6. Guard Index와 회귀 결과
7. 남은 부채와 완료 또는 미달 판정

발견만 했거나 게이트만 통과한 상태는 완료가 아니다. 일곱 칸의 증거를 이 원장에 기록한
뒤에만 다음 계층으로 이동한다. 구현 중에는 책임 흐름별 focused 회귀를 사용하고 공식
Guard는 현재 레이어의 source를 동결한 뒤 한 번 실행한다. Guard 뒤 source가 바뀌면 이전
결과를 폐기하고 최종본에서 한 번만 다시 실행한다. 같은 중간 상태에 Guard를 반복하지 않는다.

전문 검토는 현재 레이어 안의 큰 책임 흐름으로만 나누고 파일별 산발 감사로 쪼개지 않는다.
레이어 완료 즉시 원장 갱신, 한국어 커밋, push까지 끝낸 뒤 사용자에게 `계속`을 요구하지
않고 다음 레이어로 바로 진입한다. 긴 레이어에서는 서로 되돌릴 수 있는 응집 변경 묶음마다
커밋과 push를 할 수 있지만, 그 커밋을 레이어 완료로 오인하지 않는다.

세션 종료 시 현재 레이어, 최근 완료한 증거 묶음, **레이어 전체의 남은 완료 조건**, 다음
첫 행동을 아래 세션 인계 칸에 갱신한다. 특정 파일 하나를 진행 중인 전체 작업처럼 적지 않는다.

### 세션 인계

- 현재 계층: **L2 analysis, macro, quant, industry, credit** (진입 대기)
- 최근 완료한 레이어: **L1.5 scan/frame/synth/reference 전체 완료** (2026-07-31).
  네 형제의 전체 src와 실제 호출자를 실데이터로 대조했고, cross import는 정적·동적
  모두 0이다. 공식 Guard는 AST 룰 위반 0·신규 위반 0이며 전체 status fail의 유일한
  원인은 `providers/` 소유의 기존 providerGate 부채다(이번 세션 미변경).
  그 앞은 L0 core 완료, L1 gather/providers 완료.
- 현재 작업 단위: **L2 다섯 엔진 전체 마감**. 파일이나 함수 하나를 별도 완료 단위로
  쪼개지 않는다.
- L2 완료 조건: analysis, macro, quant, industry, credit의 전체 src와 실제 호출자를
  데이터 계약·오류 투명성·SSOT·속도·메모리 기준으로 전수 대조한다. 결함 수정과 집중
  회귀를 끝내고 source 동결 뒤 공식 Guard, 원장, 커밋, push까지 닫는다.
- 다음 첫 행동: L1.5 US coverage audit 체크포인트가 성능 차단으로 남긴
  `analysis/financial/edgarPitState`부터 연다. 한 회사 반례에서 Polars collect 7,197회와
  stock candidate 119회를 반복해 EDGAR full-state strict 전수가 15분 운영 한도를 넘긴다.
  이어 2026-07-27 L2 판정이 남긴 항목(팩터 형성 시점 look-ahead, 백테스트 샤프의 비용
  미반영, 과적합 확률 상수 1.0, Sortino 하방편차 정의, 스타일 전구간 분위수)을 같은
  방식으로 닫는다.
- 금지: 함수나 파일 하나만 끝내고 완료 보고, L3 이상 수정 선행,
  중간 source에서 공식 Guard 반복

## L1.5 scan, frame, synth, reference 순차 안정화 원장 (2026-07-30)

### 진행 증거 1. scan 공통 의미 계약

**상태: L1.5 진행 중. 레이어 완료 아님.** 공개 scan 진입점과 KR·EDGAR 재무 축의
공통 의미 계약을 첫 응집 변경으로 닫았다.

1. `market` 오타와 US 미지원 축은 더 이상 KR 자료로 내려가지 않는다. 구현하지 않은
   `asOf`는 현재 자료를 반환하지 않고 명시적으로 거절하며, EDGAR의 `**kwargs`도 알 수
   없는 옵션을 삼키지 않는다. US 결과도 공통 target 필터와 공개 컬럼 정규화를 거친다.
2. screen 상세 결과는 전체 멤버 수와 반환 수를 분리하고 `membersTruncated`를 남긴다.
   KR 외 시장과 지키지 못하는 `asOf`를 거절한다.
3. 연결 우선 규칙을 eager와 lazy 모두 회사별 SSOT로 만들었다. 실제 합본 계정 스캔,
   profitability DuckDB fallback, debt 합본에서 다른 회사의 연결 공시 때문에 별도만
   내는 회사가 사라지지 않는다.
4. 같은 연도 Q1과 Q4가 함께 있을 때 입력 행 순서에 따라 profitability와 growth가
   달라지던 비결정성을 공통 최신 기간 선택기로 막았다. growth는 최신 분기와 같은
   분기의 과거값만 CAGR로 비교한다.
5. KR과 EDGAR의 결측 계정을 0으로 바꾸던 유동성, 효율성, 현금흐름, 성장성, 수익성,
   부채, 밸류에이션, 배당, 자본 분류를 수정했다. 알려진 0 차입은 결측과 구분한다.
6. 집중 회귀 `53 passed`, 추가 scan builder 분리 실행 `45 passed`, 다음 묶음
   `73 passed`다. Ruff format과 변경 범위 lint가 통과했다. 공식 format gate도
   통과했고 lint gate는 제품 검사 전부 통과 후 기존 사용자 소유 블로그 asset 두 폴더의
   workspace hygiene에서만 실패했다.
7. 전 scan 단일 프로세스 실행은 테스트 실패 없이 118개 뒤 RSS `4,623 MB`, 더 작은
   묶음도 73개 뒤 `3,275 MB`에서 메모리 안전장치가 종료했다. 이는 L1.5 완료 증거가
   아니라 다음 최적화의 차단 근거다. profitability 실데이터도 약 5.3초와 RSS 약
   955MB가 관찰되어 one-pass group/pivot 전환 전에는 scan을 완료 판정하지 않는다.

### 진행 증거 2. reference 계정 별칭 의미 계약

**상태: L1.5 진행 중. 레이어 완료 아님.** 실제 DART 재무 패널에서 서로 다른 경제적
의미를 가진 총자본과 지배주주지분이 하나로 합쳐지던 값 유실을 reference SSOT에서 닫았다.

1. 기존 `total_equity -> owners_of_parent_equity` 연쇄는 비지배지분을 포함하는
   총자본을 지배기업 소유주지분으로 축소했다. `total_stockholders_equity`를 총자본의
   terminal canonical로 확정하고 두 계정을 별도로 보존했다.
2. 계정 별칭은 로드 시 terminal까지 평탄화한다. self edge는 제거하고 빈 key·value와
   다중 노드 순환은 즉시 `ValueError`로 드러내어 병합 순서에 따른 값 유실을 막았다.
3. 운영 SSOT 교정은 `mappingPromote.py`의 `set`과 `delete`로만 수행한다. 둘 다
   `expected` 이전 값이 실제 값과 일치할 때만 atomic write하므로 임의 JSON 수정과
   stale overwrite를 허용하지 않는다.
4. `Company("000210").panel("BS", freq="Y")` 실데이터에서 2025년 자본총계
   `4,921,075,694,028`과 지배주주지분 `4,021,543,844,050`이 별도 행으로 확인됐다.
5. mapping CLI, AccountMapper golden·구조·무결성, DART panel cell·finance fixture,
   EDGAR finance를 묶은 집중 회귀 `145 passed`와 변경 범위 Ruff가 통과했다.

다음 순서는 scan 집계를 회사별 반복 filter가 없는 one-pass 경로로 바꾸고 EDGAR 계정
batch와 공통 period를 확정하는 것이다. frame, synth, reference의 남은 전체 범위와
실제 소비자, 최종 Guard가 남았으므로 **L1.5 판정은 미완료**다.

### 진행 증거 3. scan 재무 one-pass 집계

**상태: L1.5 진행 중. 레이어 완료 아님.** 수익성과 성장성이 회사마다 전종목
DataFrame을 다시 필터하고 계정 행을 반복 순회하던 병목을 공통 벡터 집계로 교체했다.

1. 회계 숫자 정규화와 `sj_div` 계정 구분을 `aggregateAccountValues` 한 곳에 모았다.
   콤마, 괄호 음수, 삼각형 음수, 퍼센트, 결측을 Polars 식으로 처리하고 회사별 계정
   묶음을 한 번의 group 집계로 만든다.
2. 수익성의 네 비율, 비경상 의심, 등급과 성장성의 기간 pair, 세 CAGR, 등급, 패턴을
   Python 회사별 loop 없이 벡터식으로 계산한다.
3. 합본 parquet는 필요한 여덟 컬럼만 projection하고 연결 우선, 회사별 최신 연도와
   기간, 성장성의 동일 분기 join을 LazyFrame 수집 전에 수행한다. 불필요한 전체 연도와
   전체 컬럼을 Python 프로세스에 올리지 않는다.
4. 직전 구현과 동일 입력을 직접 대조했다. 수익성은 2,811개 종목과 네 비율 모두
   `0 mismatch`, 성장성은 2,493개 종목과 최신 매출, 세 CAGR, 기간 모두
   `0 mismatch`다.
5. 실데이터 수익성은 약 `5.3초 -> 1.80초`, RSS 증가는 약
   `955MB -> 224MB`로 줄었다. 성장성은 약 `6.7초 -> 2.65초`, 최종 RSS 증가는
   약 `207MB`다.
6. 숫자·계정·기간·연결 우선·DuckDB fallback·parquet 회귀 `51 passed`, 공개 scan
   축과 streaming 계약 회귀 `106 passed`, 변경 source Pyright 오류 0과 Ruff를
   통과했다.

다음 순서는 EDGAR 계정 batch와 공통 period를 확정하는 것이다. frame, synth,
reference의 남은 전체 범위와 실제 소비자, 최종 Guard가 남았으므로
**L1.5 판정은 미완료**다.

### 진행 증거 4. EDGAR 계정 batch와 회사별 기간 정합성

**상태: L1.5 진행 중. 레이어 완료 아님.** EDGAR scan 축이 필요한 계정을 각각
전종목 재조회하고, 계정별 최신 열을 같은 회사의 같은 기간인 것처럼 붙이던 결함을
bounded batch와 회사별 기간 정렬로 닫았다.

1. **범위와 실제 호출자.** provider의 `scanAccount`, 단순 비율 계산과 새 다계정
   primitive, scan builder의 `scanEdgarAccounts`, profitability와 growth 공개 축을
   한 흐름으로 대조했다. 분자와 분모, 수익성 5계정, 성장성 3계정이 같은 EDGAR
   companyfacts source를 반복 읽던 경로를 실제 전종목 호출로 재현했다.
2. **제품 결함 재현.** 계정마다 전역 최신 열을 고르면 어떤 회사에는 그 기간 값이
   없어 오래된 값이 최신값 자리에 대입됐다. 학습된 fallback tag가 공통 taxonomy
   tag보다 먼저 오거나 segment context가 연결 합계보다 먼저 선택됐고, 같은 FY filing의
   과거 비교 context도 현재 연간값으로 오인됐다. General Mills의 2024 매출은 실제
   약 `19.857B` 대신 component `2.038B`가 선택되어 매출 성장률이 약 `856%`로
   왜곡됐다. 5계정 단일 시도는 256MB와 384MB 모두 OOM 뒤 계정별 fallback으로
   내려가 `134.861초`가 걸렸다.
3. **근본 원인과 SSOT.** DART canonical 계정과 EDGAR taxonomy tag 우선순위,
   정상 annual 또는 quarter duration, 최신 종료일, filing 개정본, 회사별 현재와
   직전 기간의 owner가 분리되어 있었다. `accountMappings`의 공통 tag를 최우선
   SSOT로 삼고, provider가 context를 고른 계정 wide를 builder의 회사별 period
   rank가 정렬하도록 책임을 고정했다.
4. **수정과 테스트.** `scanAccounts`는 tag table을 한 번 만든 뒤 최대 3계정씩
   DuckDB source scan을 공유한다. 5계정은 처음부터 3+2 bounded batch로 실행해 OOM을
   유발하는 실패 시도를 없애고, 실패한 chunk만 검증된 단일 경로로 복구하며 두 원인을
   보존한다. SQL과 file-loop 모두 정상 duration, 최신 end, 공통 tag, segment fallback,
   최신 filed 순서를 적용한다. `scanEdgarAccounts`는 계정 wide를 long으로 바꿔
   회사별 최신·직전 기간에 exact join하고, 없는 최신값을 과거값으로 대체하지 않는다.
   profitability와 growth는 `1M USD` 미만 분모·기준값과 비현실적 비율을 결측으로
   분류해 작은 분모 artifact를 상위 종목으로 내보내지 않는다.
5. **공개 행동, 정확성, 속도, 메모리.** 실제 growth는 6,105종목을 `18.684초`,
   RSS 증가 약 `168.6MB`에 만들었다. profitability는 6,111종목을 fallback 없이
   `52.075초`, RSS 증가 약 `207.9MB`에 만들며 직전 `134.861초`보다 약 61% 짧다.
   결과의 절대 최대치는 영업이익률 `99.4`, 순이익률 `496.81`, ROE `488.5`,
   ROA `99.59`로 명시한 품질 상한 안이다. General Mills의 연간 매출은
   `2025 19.487B`, `2024 19.857B`, `2023 20.094B`, `2022 18.993B`로 복구됐고,
   매출 YoY `-1.87%`, 영업이익 YoY `-3.70%`, 순이익 YoY `-7.93%`다.
6. **Guard와 회귀.** 실제 DuckDB 다계정 SQL, batch 분할과 실패 fallback, context와
   tag 우선순위, 회사별 기간 정렬, 단순 비율 단일 batch, 이상치 거절을 회귀로 고정했다.
   provider와 scan 관련 집중 회귀 `62 passed`, 변경 source Pyright 오류 0,
   Ruff format과 lint가 통과했다.
7. **남은 부채와 판정.** EDGAR batch의 source scan은 계정 수에 따라 최대 3개씩
   나뉘며 이는 256MB 상한을 지키기 위한 의도된 속도·메모리 절충이다. scan의 남은
   공개 축과 raw tag 경로, frame, synth, reference 전체 범위와 실제 소비자,
   source 동결 뒤 공식 Guard가 남았다. 따라서 **L1.5 판정은 미완료**다.

### 진행 증거 5. scan 공통 I/O와 남은 KR 재무 축

**상태: L1.5 진행 중. 레이어 완료 아님.** 공통 scan artifact를 읽는 길목과
현금흐름, 품질, 유동성, 효율성, 배당추세, 밸류에이션 축을 한 응집 흐름으로 닫았다.

1. **범위와 실제 호출자.** prebuild 확보와 검증, report와 finance parquet,
   DuckDB fallback, docs cross scan, 최신 계정 집계, 여섯 공개 재무 축과
   `Scan.docsSections` 호출자를 함께 대조했다.
2. **제품 결함 재현.** 다운로드 실패와 존재하는 손상 artifact가 빈 DataFrame으로
   바뀌었고, cache 플래그가 실제 파일 유실을 가렸다. DuckDB fallback은 schema와
   query 실패도 자료 부재처럼 반환했다. cross scan의 DuckDB 엔진은 먼저 Polars로
   전체 수집한 뒤 다시 DuckDB에 올려 out-of-core가 아니었다. 남은 재무 축은 같은
   finance source를 계정마다 반복 읽고, 배당추세는 회사별 Python filter를 반복했다.
   효율성은 재고회전율 분자에 매출원가 대신 매출액을 사용했다.
3. **근본 원인과 SSOT.** 정상 부재와 손상, 공급 실패의 상태가 구분되지 않았고
   latest account와 연결 우선 규칙이 축마다 흩어져 있었다. artifact 실패는
   `ScanDataError`, 회사별 연결 우선과 최신 exact period는 `scan.io.accounts`,
   finance projection과 lazy aggregation은 `scan.io.parquet`, cross query 계약은
   `CrossScanQuery`를 단일 owner로 고정했다.
4. **수정과 테스트.** cache hit도 required artifact를 재검증하고 Pyodide lite
   artifact 생성까지 확인한다. 두 다운로드 공급자가 모두 실패하면
   `ExceptionGroup`으로 두 원인을 보존한다. 존재하는 손상 prebuild, raw parquet,
   DuckDB import, query, schema 오류는 typed failure로 전파한다. cross scan은
   Polars와 DuckDB가 parquet를 직접 읽고 predicate와 limit를 source에 push down한다.
   현금흐름, 품질, 유동성, 효율성은 단일 projection과 lazy group 집계로 전환했고
   효율성 공식은 매출원가 기준으로 교정했다. 배당추세는 회사별 최신 연도를 exact
   join하는 벡터 경로로 바꿨다. 밸류에이션은 일부 공급 실패를 표본 로그로 남기고
   전부 실패하거나 listing이 비면 명시적으로 실패하며 알려진 0 값은 보존한다.
5. **공개 행동, 정확성, 속도, 메모리.** 실제 공개 scan에서 현금흐름은
   2,811종목 `1.255초`, RSS 증가 `231.5MB`, 품질은 2,800종목 `1.305초`,
   `211.6MB`, 유동성은 2,709종목 `1.257초`, `207.7MB`, 효율성은
   2,629종목 `1.358초`, `226.7MB`다. 배당추세는 2,071종목 `0.093초`,
   RSS 증가 `155.1MB`다. eager 중간판보다 약간 느린 대신 재무 축의 RSS 증가를
   기존 약 347MB에서 514MB 범위보다 크게 낮춘 의도된 절충이다.
6. **Guard와 회귀.** 회사별 최신 기간, 연결 우선, exact 공식, 다운로드 실패,
   cache 재검증, 손상 artifact, DuckDB 직접 scan, 엔진 동치와 literal filter를
   회귀로 고정했다. 집중 및 공개 축 회귀 `133 passed`, 변경 source Pyright
   `0 errors, 0 warnings`, Ruff가 통과했다.
7. **남은 부채와 판정.** 공개 `network`가 모든 panel을 읽고 회사 쌍을 이차
   비교하는 병목, US audit의 raw finance 선행 scan, EDGAR prebuild 미사용,
   universe와 dispatcher 계약이 남았다. frame, synth, reference와 최종 Guard도
   남았으므로 **L1.5 판정은 미완료**다.

## L1 gather, providers 순차 안정화 원장 (2026-07-30)

### L1 gather/providers 전체 마감

**상태: 완료.** gather의 모든 Extract와 DART·EDGAR provider의 Transform/Load,
panel, finance/report accessor, 공개 Company 호출자를 하나의 하단 데이터 흐름으로
검증했다. 파일이나 endpoint별 수정은 이 판정의 증거일 뿐 별도 완료 단위가 아니다.

1. **범위와 실제 호출자.** gather의 공개 축, source, domain fallback, DART·EDGAR
   원문과 정형 수집, DART·EDGAR Company의 `panel`, `select`, `filings`, finance와
   report dispatcher/accessor를 범위로 잡았다. 아래 생산자에서 Company를 거쳐
   scan, analysis, credit, story로 이어지는 호출을 함께 대조했다. DART finance와
   report artifact, EDGAR companyfacts와 panel native payload가 ratios까지 이어지는
   경로를 한국 삼성전자와 미국 AAPL 실제 데이터로 호출했다.
2. **제품 결함 재현.** 뉴스·GDELT·Damodaran 공급 실패가 빈 자료처럼 보였고,
   allFilings는 원문 추출과 월별 수집 책임이 한 파일에 엉켜 재시도 가능한 실패를
   잘못 캐시했다. report topic이 panel dispatcher에 도달하지 않았고 `stockTotal`
   다중 측정값은 period를 잃었다. 존재하지 않는 기간 요청이 전체 표를 반환했으며,
   EDGAR `select`는 `freq`와 `scope`를 버렸다. DART finance artifact 실패는 docs로
   내려가 원인을 숨겼고 report accessor는 손상과 부재를 구분하지 않았다. 같은 Company의
   panel을 반복 조회할 때 DART·EDGAR 모두 무거운 artifact를 매번 다시 읽었다.
3. **근본 원인과 SSOT.** 네트워크 성공·정상 무데이터·공급 실패의 상태 계약이 source마다
   달랐고, panel dispatch와 기간 필터가 강한 topic registry를 사용하지 않았다.
   allFilings 문서 해석과 수집 orchestration도 owner가 분리되지 않았다. 공급 상태는
   gather typed error, 원문 해석은 `allFilingsDocument`, report routing은 공통 registry와
   API type, 기간 선택은 panel period helper, Company 단위 재사용은 `BoundedCache`를
   각 단일 정본으로 고정했다.
4. **수정과 테스트.** 뉴스 archive, GDELT, NewsIO, Damodaran은 정상 무데이터와 실패를
   구분해 원인을 보존한다. DART allFilings 원문 해석을 새 모듈로 분리하고 collector는
   수집과 저장만 소유하게 했다. DART·EDGAR report dispatcher와 accessor는 강한 topic을
   panel에 연결하고 artifact 손상을 원형 예외로 전달한다. `stockTotal`은 period를
   보존하고, 없는 기간은 `None` 또는 빈 결과만 반환한다. EDGAR `select`는 `freq`와
   `scope`를 끝까지 전달한다. 두 Company의 panel 재사용은 수명주기와 함께 정리되는
   bounded cache로 만들었다. source 동결 전 집중 회귀는 `134 passed`, 최종 환경 격리
   회귀는 `4 passed`다.
5. **공개 행동, 정확성, 속도, 메모리.** 삼성전자 실제 panel은 IS `36x43`, BS `63x43`,
   CF `64x43`, ratios `16x52`, dividend `2x41`, stockTotal `140x12`이며 없는
   `1900` 기간은 `None`이다. AAPL의 IS, BS, CF, ratios도 모두 비어 있지 않고
   `freq="Y"` 선택은 연간 열만 반환했다. 같은 Company에서 panel identity가 유지됐다.
   DART BS 중앙값은 `2.267 s`에서 `0.002 s`, companyOverview는 `1.859 s`에서
   `0.001 s`로 줄었다. 실데이터 작업의 process peak는 `947 MB`에서 `523.3 MB`로
   줄었고 Python heap peak는 `27.2 MB`다.
6. **Guard와 회귀.** 변경 source Ruff, formatter, compileall과 Pyright
   `0 errors, 0 warnings`가 통과했다. gather gate `8/8`, provider gate `11/11`,
   Skill OS 검증과 관련 skill 회귀 `35 passed`다. 최종 공식 Guard strict는
   1,778파일, 규칙 7/7과 cycle, architecture, folder mirror, gather, provider,
   public API 외부 게이트 6개를 모두 통과했다. 공식 preflight의 단위 테스트는
   `7076 passed, 31 skipped, 3 xfailed`, wheel 2,226파일과 설치 product smoke 4/4,
   notebook 11개, snapshot 5개, schema 16개, eval 13개, mutation 7/7이 통과했다.
   preflight 집계의 유일한 실패는 작업 전부터 있던 사용자 소유 블로그 media staging
   두 폴더를 잡은 workspace hygiene다.
7. **남은 부채와 판정.** Guard known debt 47건은 active 9건과 보호된 Company facade
   38건이다. provider/gather strict 상세 경고의 큰 Company와 handler, init, docstring
   부채는 baseline을 늘리지 않았고 일반 gate는 통과했다. EDGAR Q1~Q3 standalone 선택의
   최소 절대값 휴리스틱은 반례가 재현되지 않은 정확도 부채로 남긴다. 전역 Skill artifact
   drift는 L4 Skill OS 순서, 블로그 media staging 두 폴더는 최종 release hygiene 순서에서
   처리한다. L1 공개 데이터 흐름의 P0/P1 결함, 침묵 실패, 반복 panel 병목은 0이므로
   **L1 gather/providers를 완료 판정하고 L1.5 scan/frame/synth/reference로 이동한다.**

## L0 순차 안정화 원장 (2026-07-29)

### L0 core 전체 마감

**상태: 완료.** 아래 L0-01부터 L0-16까지의 증거와 마지막 재무비율·schema 횡단 검증을
합쳐 L0를 하나의 레이어로 닫았다. 내부 번호는 이 판정의 증거일 뿐 별도 완료 단위가 아니다.

1. **범위와 실제 호출자.** 기존 L0 원장 전체에 더해 마지막 범위는
   `core/ratios`의 모든 공개 계산·결과 모델과 DART·EDGAR Company, finance accessor,
   native panel, analysis pipeline, Excel 소비자다. DART raw schema는 실제 생산자
   `gather/dart`와 fixture 소비자까지 함께 추적했다. AST 전수 검사에서
   `calcRatios` 26개 호출 파일은 `annual`, `calcRatioSeries` 호출은 `yoyLag`를 모두
   명시했다.
2. **제품 결함 재현.** analysis 연간 4개년 값이 TTM처럼 합산됐고 EDGAR analysis는
   존재하지 않는 DART builder만 찾아 항상 자료 없음으로 끝났다. 시점과 시계열 계산이
   공식을 따로 구현해 세율, 감가상각, 성장률, 업종 마스킹이 달랐다. YTD와 분기의 비교
   간격, EDGAR 통화, 기초·기말 평균잔액이 묵시적이었고, 값이 전부 `None`인 금융 계정도
   업종 신호로 오인했다. schema 51개 중 실제 생산 경로와 맞는 것은 둘뿐이며 검증을
   켜도 예외를 warning으로 삼켰다.
3. **근본 원인과 SSOT.** 기간 basis와 비교 lag를 호출 계약에 넣지 않았고
   `calcRatios`와 `calcRatioSeries`가 같은 공식을 두 벌 소유했다. raw 계약도 실제
   생산자가 아닌 범용 core가 미래 희망 schema를 소유했다. 재무비율 공식은 단일 시점
   계산기로, DART raw 계약은 `gather/dart/schemas.py`로 소유권을 고정했다.
4. **수정과 테스트.** 1,900줄 단일 파일을 `models`, `common`, `point`, `series`,
   `market` 책임으로 분리하고 public re-export는 보존했다. 시계열은 기간별 prefix를
   같은 단일 시점 계산기에 넣어 두 번째 공식 구현을 제거했다. `annual`과 `yoyLag`,
   업종 override를 검증하고 DART·EDGAR 호출자가 통화와 기간 basis를 명시한다.
   ROE·ROA·ROIC·회전율·CCC·DuPont·Sloan은 가능한 경우 평균잔액을 쓰며, 0과 결측을
   구분하고 Piotroski 장기차입 신호와 금융업 부적용 정책을 바로잡았다. analysis는
   DART와 EDGAR builder 반환 계약을 검증하고 오류를 전파한다. schema는 실제
   `FinanceSchema`, `ReportSchema` 둘만 남기고 검증 활성화 시 import와 drift 오류를
   그대로 전달한다.
5. **공개 행동, 정확성, 속도, 메모리.** core 공식, golden oracle, DART·EDGAR finance
   accessor와 native panel까지 최종 집중 회귀 `238 passed`다. 합성 완전 입력의
   `calcRatioSeries` 실측 중앙값은 40기간 `20.11 ms`, 100기간 `72.76 ms`,
   200기간 `322.79 ms`이고 Python 추적 peak는 각각 `0.08`, `0.20`, `0.38 MiB`다.
   기간 수에 따라 메모리가 선형 증가하고 실제 연간·분기 이력 범위에는 별도 캐시나
   누적 전역 상태가 없다.
6. **Guard와 회귀.** 변경 범위 Ruff, formatter, compileall, diff hygiene가 통과했고
   Pyright는 `0 errors, 0 warnings`다. `checkSilentFail`은 1,714파일 신규 위반 0,
   core folderSize는 over-split 0·under-split 0, core 상향 import와 디렉터리 경계도
   0이다. 최종 공식 Guard
   `strict --scope l0-l15 --providers dart,edgar`는 1,775파일, 7/7 규칙과 cycle,
   architecture, folder mirror, gather, provider, public API 외부 게이트를 모두
   통과했다.
7. **남은 부채와 판정.** Guard의 known debt 47건은 L1 provider 상향 관계 9건과
   보호된 Company facade 38건으로 다음 레이어 소유다. 전역 silent substitute 262건,
   저장소 전체 타입 부채, 3개 OS release matrix는 각 소유 레이어와 최종 릴리스 검증에
   남긴다. L0 내부 구조·정확성·호출 계약·오류 투명성의 차단 부채는 0이므로
   **L0 core를 완료 판정하고 L1 gather/providers로 이동한다.**

### L0-01 복합 재무 점수 입력 완전성

**상태: 완료.** 이 항목은 복합 점수의 필수 입력 결측만 닫았다. 아래 남은 재무비율 부채와
추정 문제까지 닫았다는 뜻은 아니다.

1. **범위와 실제 호출자.** SSOT는 `core/ratios.py`다. DART의
   `providers/dart/company.py`, `builder/financeStatementBuilder.py`, `panel/cell.py`와
   EDGAR의 `accessor/financeAccessor.py`, `panel/native.py`가 같은 계산기를 쓴다.
   `analysis.financial`, `credit`, `story`, `viz`는 이미 계산된 점수를 소비하므로 위층에서
   원래 결측을 복구할 수 없다.
2. **제품 결함 재현.** 자산과 부채만 주면 Piotroski `1`, Altman `0.0`, Ohlson
   `2.298`과 부도확률 `90.87%`가 나왔다. 유동자산과 유동부채만 더 주고 손익을 전부
   비워도 Piotroski `2`, Altman `0.24`, Altman Z'' `1.73`, Ohlson 부도확률
   `87.88%`, Springate `0.2154`, Zmijewski `-0.972`가 생성됐다.
3. **근본 원인과 SSOT.** 각 공식이 필수 입력을 선언하지 않고 `or 0`으로 치환했다.
   Piotroski는 비교 기간과 자본금이 없어도 현재 수준값으로 대체하거나 1점을 공짜로
   줬다. 시점값과 시계열 계산기에 같은 대체가 두 벌로 복제돼 있었다.
4. **수정과 테스트.** Altman Z와 Z'', Ohlson, Springate, Zmijewski, Piotroski는
   공식의 필수 입력이 하나라도 없으면 `None`을 반환하게 했다. Ohlson은 영업현금흐름을
   FFO 대용치로 명시적으로 사용하고, 연간은 2개 연도, 분기는 완전한 8개 분기로 현재와
   전기 TTM을 만든다. Piotroski 시계열도 비교 기간 전에는 `None`이고 아홉 신호가
   완전할 때만 점수를 낸다. `tests/core/test_ratiosCompleteness.py`에 6개 계약 회귀를
   추가했고 기존 golden fixture에는 실제 신주 미발행 판정에 필요한 자본금을 넣었다.
5. **공개 행동, 정확성, 속도, 메모리.** 같은 희소 입력의 일곱 복합 출력은 수정 후 모두
   `None`이다. 완전 입력에서는 일곱 출력이 모두 유지되고, 분기 Ohlson은 8개 분기가
   완전할 때만 나온다. 5,000회 격리 실측에서 단일 시점은 호출당 `0.1804 ms`,
   3개년 시계열은 `0.3542 ms`였고 `tracemalloc` peak는 각각 `0.006 MiB`,
   `0.009 MiB`였다. 새 캐시나 누적 상태는 없다.
6. **Guard와 회귀.** 관련 단위 회귀 `63 passed`, Ruff와 compileall 통과,
   `silentSubstitute.py src/dartlab/core/ratios.py --strict` 신규 위반 0이다.
   Guard Index `strict --scope l0-l15`는 1,765개 파일, 7개 규칙과 cycle, architecture,
   folder mirror, gather, provider, public API 여섯 외부 게이트가 모두 통과했다.
7. **남은 부채와 판정.** 차입금과 현금 결측을 0으로 만드는 순부채, 감가상각 결측을
   무표시 추정으로 만드는 EBITDA, 시점값과 시계열 공식 중복, 시계열 자본잠식 ROE,
   Ohlson의 통화별 규모 보정은 남아 있다. 따라서 이 항목만 완료이며 **L0 전체는 미달**이다.

### L0-02 파생 재무비율 결측과 시점·시계열 일치

**상태: 완료.** 순부채, EBITDA, FCF와 양수 분모 계약을 두 계산 경로에서 하나의 의미로
맞췄다. 부실 예측 모델의 잔여 적용성은 다음 항목이다.

1. **범위와 실제 호출자.** 범위는 `core/ratios.py`의 `calcRatios`와
   `calcRatioSeries`다. DART와 EDGAR의 ratio panel은 시계열 경로를, 단일 회사 accessor와
   분석 파이프라인은 시점 경로를 사용한다. 따라서 두 경로가 다르면 같은 회사의 panel과
   분석 답이 서로 다른 숫자를 낸다.
2. **제품 결함 재현.** 순손실 `-10`, 자본 `-5`인 같은 입력에서 시점값은 ROE,
   부채비율, 순부채비율이 모두 `None`인데 시계열은 각각 `200.0`, `-2100.0`,
   `-0.0`이었다. 차입금 세 항목과 현금, 감가상각, CAPEX가 전부 없어도 순부채 `0`,
   Debt/EBITDA `0.0`, EBITDA 마진 `10.0`, FCF는 영업현금흐름과 같은 값으로 나왔다.
3. **근본 원인과 SSOT.** 시계열만 일반 백분율 함수를 사용했고, 차입금과 현금은 각
   경로에서 따로 `or 0` 합산했다. 감가상각은 유형·무형자산 비율로 추정하면서 시계열에는
   추정 여부조차 없었다. 공통 `_sumComplete`, `_calcNetDebt`, `_calcEbitdaValue`를 두고
   양쪽이 같은 완전성 규칙을 사용하게 했다.
4. **수정과 테스트.** 차입금 세 항목과 현금이 모두 있어야 순부채를, 보고된 감가상각이
   있어야 EBITDA를 계산한다. EV/EBITDA는 이미 계산된 순부채 SSOT를 재사용한다.
   FCF는 영업현금흐름과 CAPEX가 모두 있어야 하며, 명시적 CAPEX와 배당 `0`은 실제
   `0.0`으로 보존한다. 시계열 ROE, ROA, 부채비율, 자기자본비율, 순부채비율은 양수 분모
   계약을 공유한다. 새 회귀 8건과 기존 자본잠식 회귀의 실제 시계열 검증을 추가했다.
5. **공개 행동, 정확성, 속도, 메모리.** 재현한 자본잠식의 세 시계열 비율과 결측 파생값은
   수정 후 모두 `None`이다. 완전 입력에서는 시점과 시계열이 순부채비율 `30.0`,
   EBITDA 마진 `15.0`, Debt/EBITDA `3.33`, FCF `10.0`으로 일치했다. 명시적 0도
   `0.0`으로 유지됐다. 5,000회 실측은 단일 시점 `0.2009 ms/call`, 3개년 시계열
   `0.4378 ms/call`, `tracemalloc` peak 각각 `0.007 MiB`, `0.010 MiB`였다.
6. **Guard와 회귀.** core, golden, finance fixture, DART panel 조립까지 `130 passed`,
   Ruff, formatter, compileall 통과, `silentSubstitute` 신규 위반 0이다. Guard Index
   `strict --scope l0-l15`의 1,765개 파일, 7개 규칙과 여섯 외부 게이트가 모두 통과했다.
7. **남은 부채와 판정.** Beneish의 유형자산 결측 대체, Ohlson의 통화별 규모 보정,
   시점과 시계열 계산기 전체 중복은 남아 있다. 따라서 이 항목만 완료이며
   **L0 전체는 미달**이다.

### L0-03 비정규 부실·조작 모델 비발행 계약

**상태: 완료.** 이름만 원모형인 변형 점수를 계속 보정하지 않고, 공용 입력으로 원식을
재현할 수 없는 두 모델을 명시적으로 비발행하게 했다. 호환 필드는 남기되 항상 `None`이다.

1. **범위와 실제 호출자.** SSOT는 `core/ratios.py`의 `calcRatios`와
   `calcRatioSeries`다. DART와 EDGAR의 panel/accessor가 이 계산기를 함께 쓰고,
   `analysis.financial.ratios`는 옛 import 경로만 보존한다. 위층 `analysis`, `credit`,
   `story` 소비자는 두 필드가 `None`이면 신호를 내지 않는 구조이므로 공용 계산기의
   잘못된 숫자가 전 소비면으로 퍼지는 것이 핵심 위험이었다.
2. **제품 결함 재현.** 수정 전 Beneish는 완전 연간 입력에서 `-2.39`, 필수 PPE를
   제거해도 `-2.38`, 금융 archetype 강제에서도 `-2.39`를 냈다. 분기 네 개만으로도
   인접 분기를 회계연도처럼 비교해 `-2.39`를 냈다. Ohlson은 경제적으로 같은 기업을
   USD 단위로 넣으면 점수 `-1.4315`, 확률 `19.29%`, KRW 단위로 넣으면 `-4.2429`,
   `1.42%`를 내 표시 통화만으로 위험도가 뒤집혔다.
3. **근본 원인과 SSOT.** [Ohlson 1980](https://doi.org/10.2307/2490395)의 SIZE는
   `ln(total assets / GNP price-level index)`인데 구현은 통화와 연도를 무시한
   `ln(total assets / 1e6)`이었다. [Beneish 1999 원문](https://www.calctopia.com/papers/beneish1999.pdf)의
   TATA는 비현금 운전자본 증감에서 감가상각을 빼지만 구현은
   `(net profit - operating cash flow) / total assets`였다. LVGI도 원문의
   `(LTD + current liabilities) / total assets`가 아니라 총부채를 썼고,
   DEPI는 순수 감가상각 대신 감가·상각 합산값을 썼다. 원문은 회계연도 두 개와 비금융
   상장사를 대상으로 하지만 구현은 분기 TTM과 금융업에도 같은 이름을 붙였다.
4. **수정과 테스트.** 잘못된 공식과 중복 기간 조립 코드 300여 줄을 제거했다.
   `beneishMScore`, `ohlsonOScore`, `ohlsonProbability`는 소비자 호환 슬롯으로
   보존하되 공용 계산기와 시계열은 값을 발행하지 않는다. 옛 private Beneish 계산
   re-export도 제거했고 docstring의 지원 모델 목록을 실제 동작과 맞췄다.
   `tests/core/test_distressModelApplicability.py`는 완전 연간, 완전 분기, KRW, USD에서도
   비정규 점수를 내지 않는 계약을 고정한다.
5. **공개 행동, 정확성, 속도, 메모리.** 앞의 모든 재현에서 세 필드는 수정 후
   `None`이다. 나머지 복합 점수와 ratio panel은 그대로 유지된다. 5,000회 격리 실측에서
   완전 3개년 입력의 단일 시점은 `0.0767 ms/call`, 시계열은 `0.1257 ms/call`이고,
   `tracemalloc` peak는 각각 `0.0068 MiB`, `0.0120 MiB`였다. 잘못된 계산과 중복
   시계열 조립 제거로 추가 캐시나 메모리 상태도 생기지 않았다.
6. **Guard와 회귀.** core, golden, finance fixture, panel facade 범위 `134 passed`.
   Ruff, formatter, compileall, diff whitespace 검사가 통과했고 `silentSubstitute` 위반은
   0개다. Guard Index `strict --scope l0-l15 --providers dart,edgar`는 1,765개 파일,
   7개 규칙, cycle, architecture, folder mirror, gather, provider, public API 여섯
   외부 게이트를 모두 통과했다.
7. **남은 부채와 판정.** Ohlson 재활성화에는 자산 단위, 통화, 보고일, 해당 연도의
   물가지수와 모델 horizon이 필요하다. Beneish 재활성화에는 공급자 공통 의미가 보장된
   LTD, current maturities of LTD, income tax payable, 순수 감가상각, 연간 basis가
   필요하다. 이 계약 없이 같은 필드를 다시 계산하면 회귀다. SecretStore 원자성과
   교차 플랫폼 저장, Company status parquet projection, Pyodide loader, 동적 상향
   import 감시가 남아 있으므로 **L0 전체는 미달**이다.

### L0-04 SecretStore 트랜잭션·보안 backend 계약

**상태: 완료.** core 저장 계약과 L0 직접 호출자의 오류·상태 계약을 닫았다. 상위 AI
소비자의 OAuth 평문 중복 저장까지 안전해졌다는 뜻은 아니다.

1. **범위와 실제 호출자.** 정본은 `core/providers/secrets.py` 하나이며
   `ai/settings/secrets.py`는 동일 객체를 재수출하는 호환 shim이다. L0 직접 호출자는
   `core/providers/dataCredentials.py`, `core/credentials.py`이고, gather 공개 facade,
   AI profile, OAuth token, server API가 위에서 소비한다. `CredentialManager`의 AI
   단건 상태 조회와 데이터 공급자의 `getKey`, `setCredential`, `credentialStatus`까지
   같은 저장 실패가 어떤 공개 예외와 상태로 보이는지 범위에 포함했다.
2. **제품 결함 재현.** 수정 전 두 writer가 같은 파일을 동시에 갱신하면 한 키가 사라졌고
   Windows에서는 임시 파일 교체 `PermissionError`도 발생했다. 비 Windows backend는
   base64만 씌운 평문이었고, 손상 엔트리와 복호화 실패를 데이터 자격증명 호출자가
   `None`으로 삼켰다. `CredentialManager.getCredential("openai_api_key")`는 provider id로
   만든 상태표를 전체 credential 이름으로 찾아 항상 미설정으로 돌려줬다. 1차 보강본도
   keyring master 유실 후 새 값을 쓰거나 다른 빈 store를 만들면 새 master가 기존 account를
   덮어 기존 암호문을 복호화 불능으로 만들었고, 추가 필드가 있는 엔트리는 raw `TypeError`,
   저장 뒤 lock release 실패는 커밋 여부 없는 예외로 나왔다.
3. **근본 원인과 SSOT.** 파일 갱신이 잠금 없는 load-mutate-save였고 원자 교체 전에
   file fsync가 없었다. 안전한 OS backend 부재를 평문으로 낮췄으며 schema, 예외 종류,
   namespace commit 여부가 하나의 계약으로 정의되지 않았다. per-path 또는 단일 keyring
   account만으로는 master 삭제와 store 이동을 구분할 수 없었다. 저장 파일, OS master,
   bootstrap fingerprint의 세 상태를 하나의 트랜잭션 불변식으로 묶는 것이 SSOT다.
4. **수정과 테스트.** 직접 의존으로 선언한 `filelock`이 경로 정규화된 process lock과
   10초 timeout을 맡고, 쓰기는 같은 디렉터리의 임시 파일을 flush/fsync한 뒤
   `os.replace`, POSIX `0600`, directory fsync 순으로 끝낸다. read/corrupt/decrypt/backend/
   lock/write/composite typed error와 `committed`를 공개하고 이중 실패도 두 원인을 잃지
   않는다. Windows DPAPI ctypes signature는 한 번만 초기화하며 `LocalFree` 실패도 검사한다.
   macOS/Linux는 신뢰한 native keyring의 앱 전역 Fernet master를 쓰고 headless만
   `DARTLAB_SECRET_KEY`를 쓴다. master SHA-256 bootstrap sentinel을 같은 원자 저장 경로로
   남겨 sentinel 존재+master 부재 또는 fingerprint 불일치에서는 어떤 store도 새 master를
   만들지 않는다. 구버전 plain은 안전한 backend가 있을 때만 잠금 안에서 한 번에 이관한다.
   자격증명 상태는 한 번 읽고 실제 복호화 가능한 키만 표시하며, 저장 후 후처리 실패는
   `CredentialWriteError.committed`로 호출자에게 전달한다.
5. **공개 행동, 정확성, 속도, 메모리.** thread와 실제 spawn process의 서로 다른 키
   갱신은 모두 보존됐고, 별도 process가 lock을 잡은 timeout도 typed error로 끝났다.
   Windows 실제 DPAPI 32개 병렬 roundtrip이 32/32 성공했고 암호문 파일에 원문은 없었다.
   master 삭제 뒤 같은 store 쓰기·plain 이관, 다른 빈 store 쓰기·plain 이관은 store,
   sentinel, keyring account를 한 바이트도 바꾸지 않고 실패했다. 100개 암호문
   42,893 bytes 조건에서 실제 DPAPI 쓰기는 평균 `85.4848 ms`, `keys()`는
   `2.0759 ms`, 공급자 상태표는 `1.9828 ms`, `tracemalloc` peak는 `758.59 KiB`였다.
   일반적인 10~25개 store의 쓰기는 평균 `28.37~30.30 ms`였고 상태표는 공급자 수만큼
   파일을 다시 읽지 않는다.
6. **Guard와 회귀.** SecretStore, core provider, data credential, gather facade 범위
   `55 passed`, Windows에서 POSIX 전용 권한 회귀 `1 skipped`; 계층 import와 plugin
   범위 `7 passed`다. 실제 Windows DPAPI 병렬, process lock timeout, keyring 유실,
   plain 이관, atomic replace/fsync/release/cleanup 이중 실패, exact schema,
   committed 전달을 회귀로 고정했다. Ruff, Pyright 0 errors, compileall, wheel build,
   lockfile check, diff whitespace가 통과했고 변경된 세 L0 파일의 `silentSubstitute`
   위반은 각각 0개다. Guard Index `strict --scope l0-l15 --providers dart,edgar`는
   1,765개 파일, 7개 규칙, cycle, architecture, folder mirror, gather, provider,
   public API 여섯 외부 게이트를 모두 통과했다.
7. **남은 부채와 판정.** macOS Keychain과 Linux Secret Service, POSIX `0600` 및
   directory fsync 회귀는 조건부 테스트로 넣었지만 현재 Windows 세션에서는 실행하지
   못했으므로 3-OS 릴리스 CI 증빙이 남는다. `ai/providers/support/oauthToken.py`는
   SecretStore 저장 직후 access/refresh token 전체를 legacy JSON에 다시 평문 저장하고
   삭제 오류도 삼키며, server 로그아웃도 삭제 실패를 성공으로 반환한다. 이는 L4 소비자
   항목에 이월하며 전체 제품의 OAuth 안전을 아직 선언하지 않는다. Company.status parquet
   projection, Pyodide loader, 동적 상향 import 감시도 남아 있으므로 **L0 전체는 미달**이다.

### L0-05 Company.status parquet projection 안전성

**상태: 완료.** 로컬 종목 인덱스의 정확성·오류·속도·메모리 계약을 닫았다. 현행 panel이
회사명을 저장하지 않는 문제를 다른 레이어에서 추측값으로 메웠다는 뜻은 아니다.

1. **범위와 실제 호출자.** 정본은 `core/dataLoader.py::buildIndex`와 새로 분리한
   `core/dataLoaderIndex.py`다. 공개 호출자는 `providers/dart/company.py::Company.status`,
   직접 카테고리 호출자는 EDGAR docs 기반 테스트다. DART panel뿐 아니라 같은 로더를 쓰는
   finance, report, edgarDocs, edgarPanel 실데이터를 함께 확인했다. 검색 엔진의 동명
   `buildIndex`는 별도 소유자라 범위에서 제외했다.
2. **제품 결함 재현.** 현 구현은 50,993,120-byte panel 한 파일을 인덱싱하면서 본문
   `contentRaw`까지 전부 풀어 `1.5551 s`, RSS 약 `1,484,935,168 bytes`를 썼다.
   현재 로컬 panel은 2,930파일, 약 11.78GB라 공개 status가 전체 본문을 회사별로 반복
   디코딩했다. `corp`는 회사명이 아니라 종목코드인데 `corpName`으로 반환했고, 결측만 있는
   결과는 `Null` dtype으로 공개 스키마가 변했다. `year`에 null이 섞이면 정렬
   `TypeError`, 실제 report의 `제8기 1분기` 같은 값은 연도 범위로 노출됐다. 손상 parquet은
   원인 예외를 내지만 카테고리와 파일 경로가 없었다. 공개 docstring은 실제로 존재하지 않는
   panel/finance/report 보유 bool과 lastUpdated를 반환한다고 적고 있었다.
3. **근본 원인과 SSOT.** 인덱스 집계가 일반 `loadData` 정규화 경로를 재사용하면서
   `pl.read_parquet` 전체 적재, 스키마 추론, alias 선택, 진행 표시를 한 함수에 섞었다.
   최초 개선안도 후보 컬럼의 존재만 보고 결측 alias를 고정했고, `executor.map`이 전 파일의
   Future를 선제 생성했으며, Pyodide는 projection 전에 `read_bytes()`로 압축 파일 전체를
   Python heap에 복사했다. 인덱스 고정 스키마와 projection 표현식, bounded 실행, 오류
   타입을 `dataLoaderIndex.py` 하나가 소유하게 했다.
4. **수정과 테스트.** native는 `scan_parquet`에서 회사명·연도·문서 ID와 row count만
   streaming 집계한다. 최대 네 Future만 유지하는 rolling window가 입력 순서와 즉시 오류
   전파를 보장하고 부분 결과를 반환하지 않는다. 회사명, `year/period/bsns_year`, 세 문서 ID
   alias는 값 단위 nonempty coalesce를 쓰며 연도는 정규 4자리만 허용한다. `corp` 식별자는
   회사명으로 쓰지 않는다. Pyodide는 seekable file stream에서 pyarrow schema와 projection을
   읽는다. 모든 결과와 빈 결과는 같은 6-column dtype이고, `DataIndexError`가 category,
   path, chained cause를 보존한다. 오래전에 분리된 정규화 함수의 호출자 0 wrapper와
   Company의 미사용 import도 제거했다. 새 core 회귀 9건과 공개 caller 회귀 1건을 추가했다.
5. **공개 행동, 정확성, 속도, 메모리.** 최종 실데이터 전수 결과는 panel
   `2,930파일/9.7130s/104,761 docs/2005~2026`, finance
   `2,932/6.9320s/87,299/2015~2026`, report
   `2,939/7.6362s/91,854/2015~2026`, edgarDocs
   `7,070/17.4117s/244,812/2009~2026`, edgarPanel
   `1,261/6.1266s/41,377/2008~2026`다. 최대 panel 한 파일의 최종 native 경로는
   `0.065710s`, RSS 증가 약 `26,722,304 bytes`로 구 구현보다 약 23.7배 빠르고 피크
   증가는 약 55.6배 작았다. 같은 파일의 Pyodide projection은 `0.0399s`, RSS 증가 약
   `22,695,936 bytes`였다. 20,000개 합성 파일의 bounded scheduler peak는 전문 검토에서
   구 `executor.map` 36.74MiB 대비 6.25MiB로 줄었다.
6. **Guard와 회귀.** 집중 공개·core 회귀 `11 passed`, 인접 loadData cache/predicate/IPC
   회귀 `15 passed`다. Ruff, formatter, compileall, 변경 파일 Pyright 0, wheel build와
   신규 모듈 포함, lockfile, diff whitespace가 통과했다. 변경된 세 소스의
   `silentSubstitute --strict`는 각각 0개다. Guard Index
   `strict --scope l0-l15 --providers dart,edgar`는 1,766개 파일, 7개 규칙과 cycle,
   architecture, folder mirror, gather, provider, public API 여섯 외부 게이트를 모두
   통과했다. 전문 에이전트의 최초 major 3건을 수정한 뒤 재검토 blocker/major는 0개다.
7. **남은 부채와 판정.** 현행 panel schema의 `corp`는 종목코드이므로
   `Company.status().corpName`은 거짓 이름 대신 null이다. 회사명 결합은 L1 공개 제품
   계약에서 로컬·오프라인 source를 명시해 결정한다. heavy EDGAR fixture는 별도 데이터
   의존이라 합성 회귀로 같은 계약을 검증했다. 저장소 전체 Pyright는 이번 파일 밖의 기존
   전 레이어 부채 `1,801 errors/96 warnings`로 실패하며 해당 레이어 순서에 기록해
   처리한다. 일반 Pyodide fetch/read 무결성과 동적 상향 import 감시가 남아 있으므로
   이 항목만 완료이고 **L0 전체는 미달**이다.

### L0-06 Pyodide dataLoader 읽기·fetch 무결성

**상태: 완료.** 브라우저 cache의 projection, 무결성, 원자 교체, 오류 분류와 공개 옵션
전달을 닫았다. 브라우저 밖의 gather 수집이나 상위 엔진 품질까지 닫았다는 뜻은 아니다.

1. **범위와 실제 호출자.** 정본은 `core/dataLoaderPyodide.py`와 공개 dispatch인
   `core/dataLoader.py::loadData/readParquetSafe`다. L0의 `dataLoaderIndex`도 같은 seekable
   parquet open SSOT를 재사용한다. 현재 L0 계약을 실제로 소비하는 직접 경계만 확인했다.
   DART/EDGAR panel의 `providers/dart/panel/read.py`, scan prebuild, KRX 회사명 목록의
   `gather/krx/listing/registry.py`이며, 상위 레이어 일반 감사로 범위를 넓히지 않았다.
2. **제품 결함 재현.** `PAR1...PAR1`만 닮은 26-byte 손상 payload가 정상 cache로
   저장됐고 PyArrow는 곧바로 `ArrowInvalid`를 냈다. 이미 손상된 cache는 fetch를 한 번도
   시도하지 않은 채 파일을 계속 남겼다. `columns=["year"]`도 parquet read에는 projection이
   전달되지 않았다. 50,993,120-byte 실제 panel에서 전체 `read_bytes + read()`는
   `3.3925s`, RSS peak 증가 `3,092.9MiB`였다. 공개 `loadData`의 Pyodide 분기는
   `predicate`, `refresh`, `asOf`를 버렸고 EDGAR 기본 `sinceYear=2009`도 적용하지 않았다.
   회사명 목록은 Pyodide에서 비활성인 `pl.read_parquet` 경로를 썼으며 실패를 로그 없이
   빈 목록으로 바꿔 세션 cache에 고정했다. broad Arrow/Exception catch는 OOM도 손상으로
   오인해 재다운로드하거나 빈 결과로 낮출 수 있었다.
3. **근본 원인과 SSOT.** path parquet open이 세 군데서 `read_bytes()`와 `BytesIO`로
   복제됐고 fetch는 magic 8 bytes만 본 뒤 최종 경로에 직접 썼다. 구조 손상,
   네트워크 실패, Arrow 용량·미지원, OOM의 예외 의미가 분리되지 않았다. 공개 함수의
   네이티브와 Pyodide 인자 계약도 dispatch에서 갈라졌다. seekable open/projection,
   구조 검증·동일 디렉터리 원자 교체, 손상만 1회 복구하는 정책을
   `dataLoaderPyodide.py` 하나의 SSOT로 모았다.
4. **수정과 테스트.** `openParquetFile/readParquetFrame`이 path는 file stream으로,
   메모리 payload만 `BytesIO`로 열고 요청 열과 필터 보조열만 읽는다. 다운로드는 고유한
   sibling temp에 쓴 뒤 footer와 모든 column chunk 경계를 검증하고 `replace`한다.
   기존 정상 cache는 검증 실패 때 그대로 보존한다. `ArrowInvalid/OSError`만 손상으로
   분류해 최대 한 번 재조달하고, 재실패·`local_only`의 손상 cache는 제거한다.
   `ArrowMemoryError/MemoryError`와 `ArrowCapacityError` 등 비손상 오류는 fetch·삭제 없이
   전파한다. `predicate`, `refresh`, `asOf`, EDGAR 기본 연도를 공개 dispatch에서 보존하고,
   root 열을 확정할 수 없는 predicate는 정확성을 위해 full read로 강등한다.
   `DARTLAB_NO_REFRESH`는 기존 cache 갱신만 막고 최초 다운로드는 허용한다. 회사명 목록은
   Arrow SSOT를 쓰며 실패를 기록하고 빈 결과를 cache하지 않는다. core, index, registry,
   panel 직접 호출자에 26개 회귀를 추가했다.
5. **공개 행동, 정확성, 속도, 메모리.** 같은 50,993,120-byte 실제 panel의 최종 공개
   Pyodide loader projection은 `45,822 x 1`을 `0.0261s`, RSS peak 증가 `8.8MiB`로
   읽었다. 구 경로보다 약 130배 빠르고 peak 증가는 약 351배 작다. 전체 구조 검증은
   `0.02304s`였다. Node Pyodide `0.27.5`에 이번 wheel을 실제 설치해 Emscripten FS에서
   정상 원자 저장, 손상 replacement 거부와 기존 cache byte 보존, temp 정리,
   `local_only + sinceYear + columns + predicate`를 실행했고 `(1, 1, Int32)`로 통과했다.
   전문 검토의 6개 실제 데이터 범주 30개 표본에서도 구조 validator 오탐은 0이었다.
6. **Guard와 회귀.** dataLoader, index, freshness, cache, predicate, IPC, scan parquet,
   scan prebuild, panel, KRX registry 인접 범위 `98 passed`다. Ruff, formatter,
   compileall, 변경 파일 Pyright `0 errors`, wheel build, `uv lock --check`, diff whitespace가
   통과했고 변경 소스 5개의 `silentSubstitute --strict` 신규 위반은 각각 0개다.
   Guard Index `strict --scope l0-l15 --providers dart,edgar`는 1,766개 파일, 7개 규칙과
   cycle, architecture, folder mirror, gather, provider, public API 여섯 외부 게이트를
   모두 통과했다. 전문 재검토 결과 blocker/major는 0개다.
7. **남은 부채와 판정.** 실제 Pyodide FS와 Arrow 경로는 확인했지만 browser의
   `pyfetch -> XHR -> open_url` 네트워크 tier는 JSPI·CORS가 있는 실제 Chromium
   release smoke에서 다시 확인해야 한다. `IDBFS syncfs`는 이 로더가 아니라 runtime
   영속화 계층 책임이다. 동시 fetch는 고유 temp로 충돌을 막았으나 기본 Pyodide가
   단일 스레드라 별도 병렬 E2E는 두지 않았다. 동적 상향 import 감시와 기존 L0 구조
   부채가 남아 있으므로 이 항목만 완료이며 **L0 전체는 미달**이다.

### L0-07 동적 상향 import 감시와 composition 경계

**상태: 완료.** L0가 구체 상위 구현을 문자열로 알고 있던 경로와 Guard 사각을 닫았다.
core 내부 배치 부채까지 이전했다는 뜻은 아니며 다음 항목부터 하나씩 처리한다.

1. **범위와 실제 호출자.** 범위는 113개 `core` 모듈의 정적·동적 import graph,
   `pluginDiscovery`와 13개 module registry seam, DI factory 4개, root
   `composition.py`, palette·renderer·plugin loader다. 실제 호출자는 credential,
   DART/EDGAR fetch·build, disclosure, gather, HTML/chart renderer, insider, listing,
   loader, panel table과 finance/quant/industry/macro accessor의 getter다. 위층 구현
   자체는 수정하지 않고 이 L0 seam과 root 배선까지만 확인했다.
2. **제품 결함 재현.** `importlib.import_module`, alias `import_module`,
   `__import__`, `_KNOWN_*` 상수 목록으로 만든 최소 core source를 기존 Guard와
   coreBoundary가 모두 0건으로 통과시켰다. 실제 core에는 실행 가능한 상위 모듈 문자열
   22개, 고유 concrete 대상 18개가 있었다. `discoverOnce`는 callback 성공 전 완료를
   표시하고 내부 `ImportError`를 선택 의존성처럼 삼켜, 한 번 실패한 registry가 다음
   호출에서도 복구되지 않았다. 조건문 아래 함수 본문을 module eager로 오인해 이미
   존재하던 L1 상향 관계 10개·22호출점도 숨겼다.
3. **근본 원인과 SSOT.** 구현 모듈 표가 core seam마다 복제됐고, 정적 import 전용 AST
   검사·cycle 검사·별도 계층표가 서로 다른 정책을 가졌다. `di.py`, sink, 변수 경로를
   예외로 두면 concrete dependency를 숨겨도 통과하는 구조였다. 구체 구현 경로는 root
   composition 한 곳, import 의미와 실행 phase는 Guard Index 한 곳이 소유하도록 했다.
4. **수정과 테스트.** `composition.py`의 module/factory 표가 17개 registry key를
   주입하고 core seam은 자기 key만 요청한다. bootstrap은 성공 뒤에만 완료되고, 실패
   예외를 그대로 전파해 재시도하며, 재진입은 종료하고 동시 최초 호출은 같은 한 번의
   성공을 기다린다. 실행 중 callback 교체·reset은 거부한다. caller-owned generic
   동적 loader는 `pluginDiscovery.py`, `plugins.py` 두 경로만 허용한다. palette는
   순수 L0 SSOT로 내리고 viz는 동일 객체를 재수출한다. logger는 외부 패키지를 강제
   import하지 않고 handler를 선등록한다. 사용되지 않던 BS/IS/CF concrete DataEntry
   경로도 제거했다. Guard는 alias·상수·`__import__`, eager/lazy/type-only,
   composition 선언 표를 인덱싱하고 source·baseline parse 실패를 fail-closed로 바꿨다.
5. **공개 행동, 정확성, 속도, 메모리.** 새 process에서 13개 module registry와
   4개 DI factory를 전부 호출해 구현체 17/17이 등록됐다. palette 호환 경로는 L0의
   list/dict/function 객체와 identity가 같다. root 등록은 구현을 강제 import하지 않으며
   기존 root 경로가 이미 올리는 2개를 제외한 concrete target 12개는 최초 getter까지
   지연된다. registry 17개의 얕은 크기는 약 `4,577 bytes`다. 1,768파일 Guard Index
   첫 parse `17.988116s` 뒤 같은 process 재사용은 `0.000507s`로 약 35,472배 빨랐다.
   동일 strict pytest 접점은 중복 AST subprocess 제거 전 `225.99s`, 최종 `122.07s`로
   약 46% 단축됐고 공식 CLI strict는 `113.3s`였다.
6. **Guard와 회귀.** 실제 core 동적 기록은 승인된 caller-owned unresolved 2건뿐이고
   concrete 상향 위반 0, 전체 module-eager 역방향 0, composition concrete edge 14건,
   top-level cycle 0이다. 관련 architecture/core/provider/CLI/viz 회귀는
   `102 passed, 1 skipped`, strict JSON 회귀 `1 passed`다. 공식 Guard는
   1,768파일, 7개 규칙과 cycle, architecture, folder mirror, gather, provider,
   public API 여섯 gate를 모두 통과했다. 변경 파일 Pyright는 0 errors이고 Ruff,
   compileall, diff whitespace도 통과했다. core 전수 `silentSubstitute`는 기존 baseline
   7건과 정확히 일치해 신규 위반은 0건이다.
7. **남은 부채와 판정.** coreBoundary에는 숨기지 않은 residency 4건이 남는다:
   `_entries`, `messaging.py`, `observability/`, `parse/`. 다음 단일 항목은
   `_entries`만 다룬다. 정확한 phase 판정으로 새로 보인 상위 구현 부채 4관계
   (`gather/accessors -> company`, DART `scanAggregator -> scan`,
   DART `scanAccount -> scan`, EDGAR `terminalStmt -> viz`)는 9호출점으로 baseline에
   기록했으며 L1 순서 전에는 수정하지 않는다. Company 공개 파사드의 추가 6관계도
   보호 원장에 기록했다. `silentSubstitute` 기존 7건은 residency 4건 뒤 별도 L0 단일
   항목으로 닫으며 이번 경계 변경에 섞지 않는다. 따라서 L0-07만 완료이고
   **L0 전체는 미달**이다.

### L0-08 `core/_entries` residency와 registry 호출자 경계

**상태: 완료.** provider import가 없는 공용 metadata catalog는 L0에 남기고, DART와
Company에만 의미가 있는 alias·filter·routing을 실제 소유자로 내보냈다. 플러그인 전체
lifecycle과 상위 소비자의 오류 정책까지 닫았다는 뜻은 아니다.

1. **범위와 실제 호출자.** 범위는 `core/_entries` 7개 모듈, `core/dataEntry.py`,
   `core/registry.py`와 직접 호출자인 DART Company·notes·builder, plugin 등록,
   CLI module 목록, server data API, Excel/viz source다. 2026-05-11의
   `_entries = L4` denylist와 다음 날의 L0 복귀 커밋, 활성 panel extraction PRD까지
   시간순으로 대조했다. 전문 독립 검토도 같은 결론을 냈다.
2. **제품 결함 재현.** 기존 registry는 plugin alias `annual.IS`가 내장 canonical 이름을
   가로챘고 `unregisterEntry("annual.IS")`가 내장 catalog를 29개에서 28개로 지웠다.
   `source` 인자는 버려졌고 여러 mutable 전역 index를 lock 없이 순차 재구축했다.
   Company 전용 `getModuleEntries()`는 실제 내장 route를 0개 돌려주면서도 L0가 그
   filter를 소유했고, DART business alias 21개는 registry에 없는 이름을 가리켰다.
   호출자 0인 AI index builder와 `DataEntry` 필드도 함께 상주했다.
3. **근본 원인과 SSOT.** 오래된 denylist는 공유 metadata를 L4 UI entry로 오인했고,
   불변 선언, runtime mutation, DART alias, Company/notes filter, AI 표현을 한 registry에
   섞었다. 파생 index 각각이 상태여서 어느 하나도 전체 registry의 원자 snapshot이
   아니었다. L0의 정본은 provider-import-free 선언과 consumer-neutral typed snapshot,
   DART 이름 정본은 `providers/dart/topicStandard.py`, Company 실행 filter는
   `providers/dart/company.py`로 확정했다.
4. **수정과 테스트.** category catalog와 합산 catalog를 모두 tuple로 만들고,
   frozen `_RegistryState` 하나가 entry·category·alias·source의 `MappingProxyType`
   index를 함께 게시하게 했다. 쓰기는 `RLock` 아래 전체 후보 검증 후 한 번에 교체하고
   읽기는 한 snapshot을 lock 없이 본다. batch 등록, source 단위 원자 교체·제거,
   provenance 조회, 내장 제거 차단, canonical/alias 충돌 차단을 추가했다. Company·notes
   filter와 DART alias를 소유자로 옮기고, 호출자 0인 `ColumnMeta`, AI·column·relation
   필드와 AI builder를 제거했다. 직접 호출자 품질 훅이 드러낸 기존 `Company.topics`
   복잡도 27은 동작을 바꾸지 않는 두 조립 helper로 분리해 본체 3, helper 16/10으로
   낮췄다. 원자 rollback·동시 등록·불변 조회·소유 경계 회귀를 새로 추가했다.
5. **공개 행동, 정확성, 속도, 메모리.** 내장 entry 29개와 category 5개,
   notes key 12개, 내장 Company 동적 module 0개가 전과 같다. Company finance는 기존
   명시 route를 유지하고 `board/cashflow/tangible/relatedParty`는 각각 기존 canonical로
   해소된다. 100만 회 `getEntry`는 `0.161 µs/call`로 구 구현 `0.459 µs`보다 약
   2.85배 빨랐고, 29개 list 사본은 `0.222 µs/call`, registry 전체 근사 상주 크기는
   `20.08 KiB`다.
6. **Guard와 회귀.** registry·plugin·architecture 범위 `43 passed, 1 skipped`,
   Company·CLI·server 직접 소비자 범위 `132 passed, 2 skipped`, 최종 Company helper
   포함 재검증 `77 passed, 1 skipped`다. 변경 L0와 새 경계 파일 Pyright 0 errors,
   Ruff, formatter, compileall, diff whitespace, camelCase/docstring, changed-only
   quality gate가 통과했다. `registry.py`와 `_entries`의 `silentSubstitute` 신규 위반은
   0개다. 공식 Guard는 1,768파일, 7/7 규칙과 cycle, architecture, folder mirror,
   gather, provider, public API 여섯 gate를 모두 통과했다. `coreBoundary`의 `_entries`
   부채는 제거됐고 다음 세 경로만 정직하게 남는다.
7. **남은 부채와 판정.** plugin rediscover는 data entry·tool·engine·loaded metadata를
   하나의 transaction으로 아직 묶지 않아 stale 상태와 공개 약속 불일치가 남으며 L4에서
   닫는다. notes dispatch의 runtime 확장 계약과 `notes.py`의 넓은 예외→`None`은 L1,
   server extractor 실패 삼킴은 해당 소비자 순서로 이월한다. `company.py` 전체 Pyright
   기존 8건도 이번에 새로 만든 경계 밖의 L1 원장 대상이다. 다음 단일 항목은
   `core/messaging.py`이고 그 뒤 `observability/`, `parse/`, core 무음 대체 baseline
   7건을 각각 따로 닫는다. 따라서 L0-08만 완료이며 **L0 전체는 미달**이다.

### L0-09 `core/messaging.py` residency와 전송 경계

**상태: 완료.** L0에는 계층 공통 메시지의 format, emit, progress primitive만 남기고
도메인 안내와 오류 해석은 기존 소유 모듈을 호출자가 직접 사용하게 했다. 메시징 하위
모듈 전체와 관측 계층까지 완료했다는 뜻은 아니다.

1. **범위와 실제 호출자.** 범위는 `core/messaging.py`, catalog와 직접 import하는
   외부 source 29개 파일이다. L0 data loader, L1 gather와 DART·EDGAR provider,
   L1.5 scan, Company와 CLI·server·viz가 같은 표면을 썼다. 2026-05-11에 추가된
   `messaging.py = 상위 계층` denylist와 이후 facade 분리 이력도 시간순으로 대조했다.
   전문 독립 검토는 공통 primitive의 L0 잔류와 상위 정책의 직접 소유 import가 맞으며,
   native의 이중 로그는 완료 전 막아야 한다고 판정했다.
2. **제품 결함 재현.** 기존 `emit()` 한 번은 사용자 문구 뒤에 `message_emit`라는
   두 번째 가시 로그를 남겼다. catalog 세 문구가 이미 `[dartlab]`을 포함해 logger
   prefix와 중복됐고, 구조화 발행 import 실패는 성공으로 삼켰다. focused split 뒤에도
   facade는 format·emit·progress 외에 Company 안내, provider key, share, exception
   정책까지 19개 이름을 재수출해 메시징 모듈 7개를 즉시 적재했다. 오래된 denylist와
   상향 import 예외도 이미 사라진 facade 구조를 계속 부채로 기록했다.
3. **근본 원인과 SSOT.** 사용자 메시지와 관측 이벤트를 별도 로그 두 건으로 표현했고,
   표현 prefix를 catalog와 transport가 함께 소유했다. focused owner로 분리된 함수도
   호환 facade에서 다시 합쳐 경계가 복원되지 않았다. 문구 정본은 catalog의 prefix 없는
   template, L0 전송 정본은 `messaging.py`의 세 primitive, 안내·오류 정책 정본은 각각
   `messagingHandlers.py`, `messagingErrors.py`로 확정했다.
4. **수정과 테스트.** facade의 공개 이름을 `emit`, `format`, `progress` 셋으로 줄이고
   내부 formatter만 비공개 이름으로 참조한다. analysis·CLI·server·viz와 guide 테스트는
   필요한 owner를 직접 import한다. native 구조화 정보는 별도 이벤트를 발행하지 않고
   사용자 로그 한 레코드의 `extra`에 `event`와 `fields`로 붙이며 Pyodide에는 일반
   레코드만 남긴다. 전송 실패를 잡지 않아 원인 예외를 그대로 전달한다. catalog의 중복
   prefix 세 건, stale core denylist와 상향 import 예외 두 건도 제거했다.
5. **공개 행동, 정확성, 속도, 메모리.** 실제 native `emit()`은
   `[dartlab] ✓ 다운로드 완료 (1MB)` 한 건만 기록했고 같은 레코드에
   `event=message_emit`, key와 kind가 붙었다. Pyodide도 사용자 레코드 한 건이며 관측
   필드는 없다. 공개 이름은 19개에서 3개, 즉시 적재 messaging 모듈은 7개에서 4개로
   줄었다. `format()` 100만 회는 `1.031 µs/call`, 결과를 보유하지 않은 10만 회
   `tracemalloc` peak는 `9.15 KiB`였고 새 cache나 누적 상태는 없다.
6. **Guard와 회귀.** 메시징·guide·architecture·server 범위 `62 passed`, L0 loader
   직접 소비자 `58 passed`, analysis·CLI·viz 직접 소비자 `20 passed`, 최종 메시징
   계약 `7 passed`다. Ruff, formatter, core Pyright 0 errors, compileall, Bandit,
   diff whitespace, camelCase/docstring, changed-only quality gate가 통과했다.
   `messaging.py`의 `silentSubstitute`는 0건이다. 공식 Guard는 1,768파일, 7/7 규칙과
   cycle, architecture, folder mirror, gather, provider, public API 여섯 gate를 모두
   통과했다. `coreBoundary`에는 다음 순서인 `observability/`, `parse/` 두 건만 남는다.
7. **남은 부채와 판정.** 1.0.0 전 facade의 옛 상위 re-export를 쓰던 외부 사용자는
   owner 모듈로 옮겨야 하는 clean break다. 호환 재수출을 되살리면 L0 경계 회귀다.
   `messagingContext.hasDartKey`의 기존 무음 대체는 별도 L0 항목에서 다룬다. 다음 단일
   항목은 `core/observability/`이고 그 완료 전 `parse/`로 넘어가지 않는다. 따라서
   L0-09만 완료이며 **L0 전체는 미달**이다.

### L0-10 매핑 관측 writer와 후보 평가 경계

**상태: 완료.** L0에는 account SSOT가 생산하는 관측 append와 writer-reader 공통 lock만
남기고, 후보 평가와 staging 소비는 `reference/mapping` 소유로 확정했다. 매핑 승격
권한은 기존 review와 promote 절차에 그대로 남겼다. `core/parse`나 기존 core 무음 대체
부채까지 닫았다는 뜻은 아니다.

1. **범위와 실제 호출자.** 기존 `core/observability` 두 모듈의 생산 호출자는 DART
   finance의 legacy pivot과 Arrow pivot 둘뿐이고, 유일한 소비자는
   `reference/mapping/mappingLedgerCompact.py`였다. stable/public API 호출자는 0이며
   호환 facade도 없었다. 독립 검토와 git 이력 대조 결과 범용 observability가 아니라
   account mapping 학습 sidecar였으므로 writer는 `core/accounts/mappingLedger.py`,
   신호와 strict reader는 `reference/mapping`이 맞다고 확정했다.
2. **제품 결함 재현.** 기존 `readAll`은 정상 JSON, 손상 JSON, scalar `42` 세 줄에서
   손상 줄을 조용히 버리고 scalar를 `list[dict]`에 섞었다. 후반 record가 잘못된 batch는
   앞 record만 파일에 남길 수 있었다. `mappings`가 존재하지 않는 `ghost_snake`를
   가리키면 `autoEligible=True`가 됐다. 표준계정 3,143개와 mappings 34,622개에서 신호
   평가는 그룹당 `386.829 ms`, 10만 행 `readAll`은 peak `75.06 MiB`였다. ENV ON의
   append OSError는 두 pivot 모두 warning으로 바꿔 데이터 성공처럼 반환했다.
3. **근본 원인과 SSOT.** writer와 reader가 process lock 없이 같은 NDJSON을 다뤘고,
   reader가 전체 파일 materialize와 광범위 JSON 오류 무시를 함께 수행했다. S3와 S5는
   그룹마다 표준계정 전부를 다시 정규화하고 완전 Levenshtein을 돌렸다. S4는 결과
   snakeId가 standardAccounts에 존재하는지 확인하지 않았다. 관측, 후보 판정, prod 승격의
   세 권한이 잘못된 core 폴더에 섞여 있던 것이 공통 원인이었다.
4. **수정과 테스트.** append는 파일을 열기 전에 batch 전체 schema와 JSON 직렬화를
   검증하고, writer-reader 공통 `filelock` 뒤에 append, flush, fsync를 수행한다. lock
   timeout은 `MappingLedgerLockError`로 전파한다. compactor는 경로와 줄 번호를 보존하는
   strict iterator로 JSON object, 필수 문자열, timezone ISO8601, 양의 정수를 검증한다.
   stockCode와 sjDiv는 set으로 집계한다. 평가기는 korName, NFD jamo, suffix, 정규화 mapping
   index를 한 번 만들고 bounded Levenshtein만 계산한다. ghost S4는 별도 breakdown에
   남기되 제안과 auto eligibility에서 hard reject한다. 두 pivot의 OSError catch를 제거했다.
   옛 core 경로와 shim은 삭제하고 테스트도 실제 owner로 이동했다.
5. **공개 행동, 정확성, 속도, 메모리.** ENV OFF는 append 0과 기존 pivot 결과를 그대로
   보존한다. ENV ON 저장 실패는 legacy와 Arrow 모두 원인 OSError를 호출자에게 전달한다.
   10만 행, `15.068 MiB` ledger를 strict streaming group할 때 `2.379 s`, tracemalloc
   peak `0.038 MiB`였고 결과는 한 그룹으로 정확히 집계됐다. 재사용 index 생성은
   `51.086 ms`, 이후 평가는 그룹당 `0.400457 ms`로 기존보다 약 966배 빨랐다. comparable
   10만 행 Python 추적 peak는 약 1,975배 줄었다.
6. **Guard와 회귀.** writer, 신호, compactor, 두 pivot 오류 경계 `67 passed`, DART
   pivot parity와 account SSOT golden `40 passed`, Skill artifact 회귀 `35 passed`다.
   새 세 모듈 docstring 4-section strict, Ruff, formatter, 변경 모듈 Pyright 0 errors,
   Bandit, camelCase, diff whitespace가 통과했다. `checkSilentFail`은 1,707파일 신규
   위반 0, `silentSubstitute`는 baseline 안 통과했고 옛 `readAll` 항목을 삭제했다.
   공식 Guard는 1,767파일, 7/7 규칙과 cycle, architecture, folder mirror, gather,
   provider, public API 여섯 gate를 모두 통과했다. `coreBoundary` 잔여는
   `observability/`, `parse/` 두 건에서 `parse/` 한 건으로 줄었다.
7. **남은 부채와 판정.** prod `accountMappings.json`의 기존 ghost mapping 자체를
   정리한 것은 아니며 이번 변경은 새 ghost 제안만 차단한다. staging parquet의 write
   transaction과 review/promote 전체 안정화는 해당 reference 소유 항목에서 다시 본다.
   다음 단일 항목은 `core/parse/`이고 그 완료 전 기존 core 무음 대체 6건으로 넘어가지
   않는다. 따라서 L0-10만 완료이며 **L0 전체는 미달**이다.

### L0-11 DART viewer parser residency와 HTML evidence 경계

**상태: 완료.** `core/parse/`를 없애고 DART 전용 parser와 provider 독립 표 renderer의
owner를 분리했다. 이 판정은 DART viewer와 공용 표 변환 경계만 닫았다는 뜻이며 gather
전체 HTTP 수집을 완료했다는 뜻은 아니다.

1. **범위와 호출자.** `core/parse/dartViewerPage.py`의 실제 생산 호출자는
   `gather/dart/viewer.py` 한 곳뿐이었고 stable/public 호출자는 0이었다. 주석이 주장한
   providers caller는 존재하지 않았다. `tableToMarkdown`만 EDGAR docs에 거의 같은
   구현이 있었고, DART index의 node/viewDoc 해석은 KR viewer 전용이었다. 따라서 DART
   parser는 `gather/dart/viewerPage.py`, 공용 표 grid는 `core/htmlMarkdown.py`가
   owner다. 기존 `core/render.py`와 이름이 충돌하는 package 안은 교차 검토에서
   차단했고 top-level 단일 모듈로 확정했다.
2. **실제 결함 재현.** 필드가 일부만 있는 node와 double-quote `viewDoc`는 둘 다
   `[]`로 사라졌다. node 응답 접수번호와 요청 접수번호 불일치도 검사하지 않았다.
   viewer URL은 HTTP였고, 중첩 표는 내부 행과 cell을 다시 읽어 중복 출력했으며
   `colspan=5000`을 그대로 materialize했다. inline text는 단어가 붙었다.
   `limit=1`도 index 뒤 모든 section을 fetch한 후 한 행만 잘랐고, `docMeta`도 모든
   본문을 받은 뒤 height만 읽었다. index 오류는 `DocumentNotFoundError`로 오분류되고
   section 오류는 warning 후 continue, 50자 미만 본문은 무음 삭제됐다. 깨진 decoding도
   replacement 문자로 진행했다.
3. **owner와 SSOT.** node/viewDoc tokenizer, 접수번호 검증, URL 조립, DART HTML 정제는
   gather DART 소유로 이동했다. span 확장, 중첩 행 제외, pipe escape, 256열과 100만
   cell 안전 한계는 `core/htmlMarkdown.py` 한 곳이 소유하며 BeautifulSoup와 lxml은
   같은 grid renderer에 연결되는 얇은 adapter만 가진다. EDGAR는 iXBRL 정제 정책을
   그대로 유지하면서 공용 BeautifulSoup adapter를 사용한다. 옛 core import shim은
   stable caller가 없어 만들지 않았다.
4. **근본 수정.** bounded assignment tokenizer가 node1/node2 순서와 single-quote,
   double-quote, escape를 처리한다. 구조 흔적이 있는데 필드가 없거나 중복되고, node가
   충돌하거나 접수번호가 다르면 `ViewerPageParseError`로 즉시 실패한다. URL은 HTTPS와
   `urlencode`로 조립한다. 표는 rowspan과 colspan을 bounded grid로 만들고 중첩 행을
   한 번만 읽는다. DART section은 lxml tree로 변환한다. index와 section의
   `SourceUnavailableError`를 원형 전파하고, 빈 section은 title, order, URL이 있는
   typed error로 실패시킨다. 짧은 정상 본문은 보존한다. `limit`은 section GET 전에
   자르고 `docMeta`는 index 한 번만 읽는다. 자체 생성 client는 성공과 실패 모두 닫는다.
5. **공개 행동, 정확성, 속도, 메모리.** 2026-05-15 삼성전자 분기보고서
   `20260515002181`의 105,493-byte index를 58개 section으로 안정적으로 해석했고 URL
   전부가 HTTPS였다. 최대 section은 HTTP 1,249,851 bytes였고 정규 text 224,990자를
   만들었다. 옛 중첩 표 중복 출력은 3,085,996자였으므로 13.7배 팽창을 제거했다.
   대형 section 변환 median은 `2.1504 s`에서 `0.6625 s`로 약 3.25배 빨라졌고 Python
   추적 peak는 `42.8183 MiB`에서 `1.9963 MiB`로 약 21.4배 줄었다. index parser는
   median `4.8141 ms`, p95 `6.6446 ms`였다. 같은 58-section 문서에서 `limit=1`의
   요청 수는 59회에서 2회, `docMeta`는 59회에서 1회가 된다.
6. **Guard와 회귀.** public gather axis, DART facade/viewer, 공용 표, EDGAR docs와
   기존 EDGAR HTML golden을 포함한 광범위 회귀 `163 passed`, mirror 분리 뒤 최종
   focused 회귀 `63 passed`다. 새 모듈 Pyright 0 errors, Ruff, formatter, Bandit,
   docstring 4-section과 gather 9-section, 변경 파일 silent-fail, diff whitespace가
   통과했다. `core.parse` stale import는 0이며 `coreBoundary`도 위반 0이다. 공식 Guard는
   1,767파일, 7/7 규칙과 cycle, architecture, folder mirror, gather 8/8,
   provider 11/11, public API 여섯 외부 gate를 모두 통과했다.
7. **남은 부채와 판정.** 전체 문서의 `limit=None`은 DART rate policy 아래 section을
   순차 fetch한다. 병렬화와 retry 비용은 L1 gather 전체 순서에서 실측한다. 광범위 EDGAR
   foundation 파일의 별도 21실패는 누락 fixture, 삭제된 experiment, 기존 API 불일치로
   재현됐으며 이번 표 golden 두 건은 통과했다. 전역 folderSize는 기존
   `core/_entries` over-split 한 건을 별도로 보고하므로 숨기지 않고 L0 잔여 판정에
   보존한다. 다음 단일 항목은 core 무음 대체 baseline 6건이다. 따라서 L0-11만 완료이며
   **L0 전체는 미달**이다.

### L0-12 core 정상 부재와 실패 경계

**상태: 완료.** core의 실제 무음 대체 6건을 전수 판정해 정상 부재 2건과 제품 실패
4건을 분리했다. 이 판정은 core 전체 복잡도와 미테스트 공개 표면까지 닫았다는 뜻이
아니다.

1. **범위와 실제 호출자.** 범위는 `credentialLifecycle.checkLifecycle`,
   `credentials.snapshot`, `dataAudit.readLineage`,
   `dataLoader._fetchRemoteEtagAndSize`, `messagingContext.hasDartKey`,
   `progress.track` 여섯 함수와 lifecycle loader다. `checkLifecycle`,
   `snapshot`, `readLineage`, `track`은 저장소 안 생산 호출자가 없는 operator/public
   utility이고, lineage writer는 KRX sync가 사용한다. remote metadata는 freshness,
   ETag sidecar, 최초 다운로드와 refresh가 소비한다. `hasDartKey`는
   `messagingFormatting`의 key 유무별 안내 선택을 결정한다. 독립 전문 검토도 같은
   호출 그래프와 판정에 합의했다.
2. **제품 결함 재현.** 손상 lifecycle JSON과 손상 lineage line은 각각 `[]`가 됐고,
   malformed `Content-Length`는 `("same", 0)`으로 바뀌어 ETag가 같으면 손상 파일을
   fresh로 오판할 수 있었다. 필수 `core.credentials` import 실패도 `False`로 cache돼
   패키징 오류가 "DART key 없음" 안내가 됐다. 하루 미만 전에 만료된 key는 정수 절삭
   때문에 expired가 아니었다. 후속 호출자 검토에서는 엄격한 size parser가 ETag-only
   저장까지 막아 성공한 최초·refresh payload를 삭제할 수 있는 회귀도 구현 완료 전에
   발견해 차단했다. 반면 배포 metadata 부재의 `unknown`과 길이 없는 iterable의
   `total=None`은 정상 optional 상태였다.
3. **owner와 SSOT.** 공통 원칙은 "부재는 데이터, 실패는 제어 흐름"이다. lifecycle
   loader와 expiry parser가 JSON, UTF-8, root, `issuedAt`, `expiresAt`, timezone,
   발급·만료 순서를 한 번 검증한다. lineage는 `_parseRecordedAt` 하나를 writer와
   reader가 공유하고, reader가 file·line 위치를 보존한다. remote HEAD의 HTTPS,
   Authorization, response close는 `_fetchRemoteHeaders`가 한 번 소유하고 ETag
   projection과 strict size projection을 분리한다. provider 미등록만 정상 `False`이고
   내부 import와 check 실패는 원형 전파한다.
4. **근본 수정과 테스트.** lifecycle 파일 부재만 빈 상태로 두고 read·decode·JSON·entry
   손상은 `CredentialLifecycleReadError` 또는 `CredentialLifecycleCorruptError`로
   실패시켰다. `math.floor`로 최근 만료를 `-1/expired`로 고쳤다. lineage 디렉터리
   부재만 빈 목록이고 파일·UTF-8·JSON·timestamp 손상은 `LineageReadError`로 실패하며
   부분 목록을 반환하지 않는다. offset이 다른 timestamp도 실제 instant로 정렬하고
   명시한 historical `recordedAt`은 보존하되 writer에서 먼저 검증한다. 원격 size는
   ASCII decimal만 허용하고 빈 `X-Linked-Size`는 `Content-Length`로 내려간다. ETag-only
   저장은 size 오류와 독립시켜 성공 payload를 보존한다. HEAD 응답은 성공·파싱 실패 모두
   닫고 non-HTTPS URL은 요청 전에 거부한다. snapshot은 conditional distribution 조회,
   track은 `Sized` protocol로 정상 부재를 예외 없이 표현한다. hasDartKey는 성공한 bool만
   cache한다.
5. **공개 행동, 정확성, 속도, 메모리.** 같은 재현은 이제 각각 path·key·line이 있는
   typed error, strict size `ValueError`, 원형 `ImportError`, broken `__len__`
   `TypeError`로 끝난다. 최초와 refresh payload 보존, ETag sidecar, explicit
   recordedAt roundtrip을 회귀로 고정했다. 유효 lineage 20,000건은 median
   `193.766 ms`, Python 추적 peak `10.770 MiB`; 유효 credential 2,000건은
   `11.606 ms`, `1.071 MiB`였다. 이전 permissive 구현보다 각각 `66.139 ms`와
   `2.019 MiB`, `3.767 ms`와 `0.092 MiB`가 늘었으며, fail-closed 검증 비용은
   lineage record당 약 `3.31 µs`, credential당 약 `1.88 µs`다. file별 임시 목록은
   만들지 않고 line streaming을 유지한다.
6. **Guard와 회귀.** core·메시징·Pyodide loader·KRX sync writer까지 직접 소비자
   회귀 `200 passed`다. 변경 source Pyright 0 errors, Ruff, formatter, Bandit,
   compileall, camelCase, 변경 파일 silent-fail, diff whitespace가 통과했다.
   `readLineage` 복잡도는 25에서 11로 낮췄고 core `silentSubstitute` 실제 위반과
   baseline은 모두 0이다. 전역에는 상위 레이어의 실제 262건과 이미 고쳐졌지만 해당
   레이어 순서를 기다리는 stale baseline 11건이 남는다. 공식 Guard는 1,767파일,
   7/7 규칙과 cycle, architecture, folder mirror, gather, provider, public API 여섯
   외부 gate를 모두 통과했다.
7. **남은 부채와 판정.** changed-only quality gate는 이번 함수가 아니라 기존
   `dataLoader.loadData` 복잡도 37 하나로 실패한다. 전역 folderSize의 기존
   `core/_entries` over-split과 core 미테스트 공개 표면도 남아 있다. 다음 단일 항목은
   중앙 I/O 경계인 `loadData` orchestration을 호출자부터 조사한다. 따라서 L0-12만
   완료이고 **L0 전체는 미달**이다.

### L0-13 중앙 dataLoader 요청·artifact·IPC 복구 경계

**상태: 완료.** `loadData` orchestration과 native/Pyodide 요청 계약, canonical parquet
확정·복구 경계를 닫았다. 이 항목은 데이터 artifact를 읽고 확보하는 L0 경계만 다뤘으며,
각 provider가 만드는 재무·문서 내용의 의미 품질까지 승인한 것은 아니다.

1. **범위와 실제 호출자.** 공개 진입점은 `core/dataLoader.py::loadData`이고
   `newsRss`의 `MARKET/day` 중첩 shard, DART `finance/report/panel`, SEC bulk
   `edgar`, SEC 문서 `edgarDocs`, KRX·정부·거시 HF category와 native/Pyodide runtime이
   같은 경계를 쓴다. 직접 소비자는 news·macro bulk gather, DART report accessor와
   finance pivot, EDGAR identity/docs accessor·loader·section pipeline이고, 위의
   Company·panel·ratio 소비자는 여기서 반환한 frame을 사용한다. category 확보 호출자는
   generic HF downloader, `EdgarBulkLoader`, `EdgarDocsLoader` 세 갈래다. 독립 전문 검토가
   같은 호출 그래프와 실패 경계를 읽기 전용으로 재검토했다.
2. **제품 결함 재현.** `stockCode="../outside"`가 category 밖 parquet을 읽었고,
   native `local_only`는 cache 부재에도 generic download 또는 EDGAR provider를
   호출했다. 미지원 refresh가 runtime마다 다르게 auto로 강등됐고, 요청 projection 열이
   전부 없으면 전체 frame을 반환했다. 정상 canonical보다 최신인 손상 `.arrow`가
   읽기를 막았으며, 다운로드·refresh payload는 parquet 검증 전에 canonical로 확정돼
   손상 파일이 기존 정상본을 덮을 수 있었다. 첫 보강 뒤 독립 재검토에서는 footer와
   schema가 살아 있는 zstd data-page 손상이 publish gate를 통과하고, schema가 다른
   유효 IPC가 canonical 열을 누락하거나 전체 frame을 대체하며, 잘못된 predicate의 손상
   판별이 108 MB·100만 행 canonical 전체를 eager materialize하는 세 P1을 추가 재현했다.
   재조달 공급자가 임의 예외를 내면 최초 손상 원인이 사라졌고 ETag 저장 실패도
   `pass`로 무관측이었다.
3. **owner와 SSOT.** `dataLoaderContract.py`가 refresh 행렬, shard containment,
   year filter와 projection 계약을 native/Pyodide 공통으로 소유한다. 일반 category는
   `auto | force_check | local_only`, native `edgarDocs`만 `force_rebuild`를 추가하며
   정책을 core에서 bool로 축약하지 않는다. `dataLoaderNative.py`는 IPC 선택, schema
   parity, physical query, canonical 무결성 판별과 정확히 한 번의 재조달을 소유한다.
   `dataLoader.py`는 category별 확보 orchestration만 맡고, 다운로드 artifact는 고유
   staging 경로에서 검증된 뒤에만 atomic replace한다. canonical parquet가 정본이고
   `.arrow`는 언제든 폐기할 수 있는 파생 가속물이다.
4. **근본 수정과 테스트.** 절대·drive·`..`·비정규 segment는 데이터 경로 생성 전에
   거부하고 합법 중첩 shard만 category root 아래로 resolve한다. `local_only`는 모든
   category에서 network 0회이며 cache 부재를 `FileNotFoundError`로 낸다. all-missing
   또는 빈 projection과 year 열 없는 `sinceYear`는 `DataQueryError`로 실패한다.
   download·refresh는 process/time 고유 staging을 쓰고 Polars 65,536행 batch iterator로
   모든 row group과 data page를 끝까지 decode한 후 replace해 기존 canonical을 보존한다.
   IPC는 canonical과 schema가 완전히 같을 때만 쓰며 손상·불일치·query 실패에서는 같은
   query plan을 canonical에 한 번 적용하고, 성공하면 경고와 함께 mirror를 제거한다.
   두 artifact가 실패하면 두 원인을 note로 보존하고, canonical 손상은 무효화 후
   network 허용 시 한 번만 재조달한다. 재조달의 모든 일반 예외는 최초 손상 note를
   붙인 원형 그대로 전파한다. ETag sidecar 실패는 best-effort 흐름을 유지하되 category,
   stockCode, path, 예외 종류를 경고로 남긴다.
5. **공개 행동, 정확성, 속도, 메모리.** 실제 로컬 projection median은 finance
   `13,074 x 5`가 `4.772 ms`, report `5,839 x 3`이 `3.808 ms`, 경량 panel
   `67,993 x 3`이 `4.065 ms`, EDGAR docs `919 x 6`이 `29.805 ms`였다.
   50만 행 synthetic에서 predicate+projection parquet query는 median `13.763 ms`,
   p95 `22.883 ms`, Python 추적 peak `0.0045 MiB`; full-decode publish 검증은
   median `9.527 ms`, p95 `16.296 ms`, peak `0.0066 MiB`였다. 검증과 query 오류
   판별은 결과 전체를 만들지 않고 최대 65,536행 batch만 유지한다. 같은 synthetic의
   zstd IPC 전체 읽기는 median `47.070 ms`, p95 `54.479 ms`, peak `0.0046 MiB`로
   측정했다.
6. **Guard와 회귀.** request·freshness·IPC·Pyodide·EDGAR provider 집중 회귀
   `98 passed`, 실제 직접 소비자 회귀 `43 passed`, import-direction `5 passed`,
   core 상향 import `2 passed`다. 변경 source Pyright 0 errors, Ruff/formatter,
   Bandit, Vulture, compileall, camelCase, diff whitespace가 통과했다.
   `loadData` 복잡도는 37에서 `A(4)`로 낮아졌고 새 모듈 최대는 12다. 변경 source
   7개·공개 함수 38개의 coverage gate 신규 누락은 0, core boundary 위반은 0,
   전역 `silentSubstitute` 262건은 기존 baseline 안이다. 공식 Guard
   `strict --scope l0-l15 --providers dart,edgar`는 1,769개 파일, 7/7 규칙과
   cycle, architecture, folder mirror, gather, provider, public API 여섯 외부 gate를
   모두 통과했다.
7. **남은 부채와 판정.** 전체 `testCoverageGate --all`은 공개 함수마다 모든 테스트를
   다시 읽는 전수 알고리즘 때문에 10분 이상 CPU를 사용해 중단했고, 변경 source 한정
   동일 `runGate`로 38개 공개 함수의 신규 누락 0을 확인했다. 저장소 전체 coverage
   baseline 노후화는 기존 Q5 부채다. zstd 압축 IPC는 실제 mmap으로 열리지 않아 Polars가
   일반 read로 강등하므로, artifact 생성기의 압축·배포·저장공간 계약은 해당 owner
   계층에서 별도 실측해야 한다. 전역 folderSize에는 `core/_entries` 372 LoC 과분할과
   core 대형 파일 부채가 남는다. 다음 단일 항목은 기존 순서대로 `core/_entries`
   과분할이며, 따라서 L0-13만 완료이고 **L0 전체는 미달**이다.

### L0-14 DataEntry 내장 카탈로그 과분할 제거

**상태: 완료.** L0-08에서 확정한 DataEntry residency와 registry 동작은 바꾸지 않고,
축소된 내장 metadata의 낡은 물리 과분할과 재도입 경계만 닫았다.

1. **범위와 실제 호출자.** 범위는 `core/_entries` 7개 모듈, `core/dataEntry.py`,
   `core/registry.py`, 직접 import·재수출·활성 설계 문서다. 생산에서 `_entries`를
   직접 읽는 곳은 registry 하나뿐이고, Company, DART notes, plugin, CLI, server,
   viz는 모두 registry snapshot을 소비한다. runtime plugin이 먼저 registry를
   import해도 builtin 초기화 뒤에 등록되며, `registry.DataEntry` 재수출도 공개된
   기존 표면이다. 독립 전문 검토가 전체 소비자와 등록 순서를 다시 대조해 누락 0,
   P0/P1/P2 잔여 0으로 판정했다.
2. **제품·구조 결함 재현.** `_entries`는 1,098 LoC·69개 entry였을 때 7파일 분할됐지만,
   공개 표면 정리 뒤 372 LoC·29개 entry로 줄었어도 7개 category 모듈과 합산 모듈,
   dataclass, registry의 9모듈 구조가 남았다. L0-08 한 변경이 이 9파일을 함께 건드린
   것이 수정 분산의 실제 증거였고, `folderSize --strict`도 유일한 over-split으로
   보고했다. 15개 cold subprocess에서 catalog+registry chain 중앙값은 `9.043 ms`,
   관련 module residency는 9개였다.
3. **owner와 SSOT.** `dataEntry.py`는 frozen `DataEntry` 타입과 provider-import-free
   선언형 builtin tuple만 소유하고, `registry.py`는 validation, provenance,
   immutable snapshot, atomic source replacement, builtin·alias 충돌 보호만 소유한다.
   둘을 registry 한 파일로 합치면 약 570 LoC에서 선언과 transaction이 다시 섞이므로
   2파일이 최소 clean boundary다. 빈 disclosure tuple은 원래도 snapshot에 entry를
   추가하지 않았으므로 삭제 대상이다.
4. **수정과 테스트.** finance 6, report 3, notes 12, raw 2, analysis 6의 29개 entry를
   기존 순서 그대로 `_BUILTIN_ENTRIES` 한 tuple로 옮기고 category 파일 6개와 합산
   `__init__`을 삭제했다. 모든 DataEntry 필드와 extractor attribute target을 HEAD와
   직접 비교해 29/29 exact semantic equal을 확인했다. 이름·순서·category 수와
   routing 필드, extractor target의 compact fingerprint, `registry.DataEntry`
   identity를 회귀로 고정했다. `coreBoundary`의 `_entries` allowlist를 제거해 같은
   과분할 재도입을 차단했고, source와 활성 extraction PRD의 경로 설명도 새 SSOT로
   갱신했다.
5. **공개 행동, 속도, 메모리.** Company, panel, notes, plugin을 포함한 직접 소비자
   100개 회귀가 모두 통과했고 이름·순서·source·alias·runtime transaction 행동은
   동일하다. 15회 cold 실측에서 catalog+registry chain 중앙값은 `9.043 ms`에서
   `4.500 ms`로 약 50.2% 줄고 관련 module은 9개에서 2개로 줄었다. isolated retained
   allocation은 `139,194 B`에서 `122,068 B`로 약 17 KB, module shallow size는
   `5,560 B`에서 `1,440 B`로 줄었다. registry 조회는 L0-08의 `0.161 µs/call`에서
   `0.084 µs/call`, list copy는 `0.222 µs/call`에서 `0.152 µs/call`로 줄었다.
   전체 `import dartlab` 시간과 RSS 차이는 변동폭 안이므로 개선으로 주장하지 않는다.
6. **Guard와 회귀.** 관련 회귀 `100 passed`, 최종 catalog 집중 회귀 `34 passed`,
   구현 source Pyright 0 errors, Ruff/formatter, Bandit, Vulture, compileall,
   camelCase, diff whitespace, quality gate가 통과했다. core `silentSubstitute`는
   actual·baseline 모두 0이고 `coreBoundary --strict` 위반 0, top-level cycle 0이다.
   `folderSize`의 over-split은 1건에서 0건이 됐다. 최종 diff 뒤 실행한 공식 Guard
   `strict --scope l0-l15 --providers dart,edgar`는 1,762개 파일, 7/7 규칙과 cycle,
   architecture, folder mirror, gather, provider, public API 여섯 외부 gate를 모두
   통과했다.
7. **남은 부채와 판정.** 전역 folderSize에는 기존 under-split 네 건
   `extractionCatalog.py` 1,256 LoC, `memory.py` 862 LoC, `ratios.py` 1,900 LoC,
   `schemas.py` 848 LoC가 정확히 남는다. 다음 단일 항목은 출력 순서의 첫 항목인
   `extractionCatalog.py`다. 따라서 L0-14만 완료이고 **L0 전체는 미달**이다.

### L0-15 추출 카탈로그 계약·SSOT·분할 부족 안정화

**상태: 완료.** 88개 concept의 순서와 metadata는 보존하면서 provider 대칭 타입,
직렬화, parity, alias, 중복 거부 계약을 바로잡고 1,256 LoC 정적 manifest를 최소
책임 경계로 분리했다.

1. **범위와 실제 호출자.** 범위는 옛 `core/extractionCatalog.py`와 직접 생산 호출자
   8곳이다. `frame/inventory.py`, `frame/narrative.py`, `simulate/profile.py`,
   `dataHub/catalog/discovery.py`, DART panel의 `narrativeMetric.py`와 `panel.py`,
   KR scan builder의 `notes.py`와 `report/build.py`가 조회 API를 소비한다. 88개
   concept은 financialStatement 6, note 35, governance 10, capital 4, workforce 7,
   debt 6, segment 2, narrative 11, filingMeta 7이고, 상위 호출자는 census만 했으며
   이번 L0 항목에서 행동을 수정하지 않았다. 독립 전문 검토도 생산 호출자와 manifest
   identity를 재검증해 P0/P1/P2 잔여를 모두 0으로 판정했다.
2. **제품·구조 결함 재현.** `ExtractionConcept.dart`는 `DartSource | None`인데
   US-only 8개 row에는 `HonestNull`이 들어가 Pyright가 오류를 냈고, 이 8개 모두의
   `toDict()`는 `surface` 접근에서 `AttributeError`로 실패했다. parity는 provider
   지원 상태에 `"narrative"`를 섞어 `both 56 / dartOnly 14 / narrative 11 /
   edgarOnly 7`로 분류했고 `edgar.cybersecurity`도 잘못 셌다. `catalogSummary()`는
   EDGAR-side HonestNull 20개만 보고 DART-side 8개를 누락했다. 미등록
   `note.shareBasedComp`도 alias로 공개됐고 conceptId와 alias index는 중복을
   마지막 값으로 조용히 덮었다. `DartSource.dispatch`는 생산·소비가 한 곳도 없고
   모든 row에서 `None`인 죽은 schema였다.
3. **owner와 SSOT.** `models.py`가 provider 대칭 source·HonestNull·concept 타입과
   validation·직렬화를, `noteManifest.py`가 재무제표·note·EDGAR tag 선언을,
   `disclosureManifest.py`가 공시·서사 선언을, `catalog.py`가 SEC Item taxonomy,
   manifest 조립, fail-fast index와 immutable 조회를 소유한다. `__init__.py`는 기존
   public symbol만 재수출한다. 이 경계로 선언과 조회 로직을 분리하되 5모듈 이상으로
   잘게 쪼개지 않았고, 소비되지 않는 `dispatch`는 호환 hack 없이 제거했다.
4. **수정과 테스트.** DART와 EDGAR 양쪽에 같은 `source | HonestNull | None`
   계약을 적용하고 허용 surface, 빈 key/reason, category, axis, value type,
   registered/narrative 제약을 import 시점에 검증한다. provider parity는
   `both | dartOnly | edgarOnly | none` 네 상태만 사용한다. category·parity·concept·
   alias index는 `MappingProxyType`과 tuple로 고정하고 conceptId나 서로 다른
   canonical alias의 중복은 즉시 `ValueError`로 실패한다. alias는 registered note만
   소유한다. 옛 manifest에서 죽은 `dispatch`만 제외한 88개 모든 필드와 순서를 exact
   비교했고 digest `3f4e8d14b2be6b3bd7b6c3158d28b281857a2c36e6f1ac674c1579fd1c824d09`,
   public type identity, 동일 객체 조회를 회귀로 고정했다. 활성 설계 문서의 옛 파일
   경로도 새 SSOT로 갱신했다.
5. **공개 행동, 정확성, 속도, 메모리.** 모든 88개 concept이 예외 없이 provider
   대칭 dict로 직렬화되고 parity는 `60 / 20 / 8 / 0`, HonestNull은 DART 8,
   EDGAR 20, 합집합 28로 정확히 공개된다. 미등록 note alias는 이제 `None`이고
   등록 alias와 SEC Item 역색인은 보존된다. 100만 회 단독 실측에서 전체 list 조회는
   `0.458 -> 0.286 µs`, category 조회는 `2.344 -> 0.159 µs`로 약 14.7배 빨라졌다.
   `getConcept`은 `0.053 -> 0.072 µs`, alias 조회는 `0.053 -> 0.073 µs`로 각각
   약 0.02 µs 느려졌으나 절대값은 0.1 µs 미만이다. catalog 추적 retained allocation은
   약 `89.3 KiB -> 76.3 KiB`로 줄었다. 12회 cold import 중앙값은
   `5.249 -> 7.589 ms`로 약 2.34 ms 느려졌고 facade self time은 `0.574 ms`다.
   manifest 검증과 모듈 경계의 import 비용을 숨기지 않으며 lazy 전역이나 캐시 hack은
   추가하지 않았다.
6. **Guard와 회귀.** catalog와 직접 소비자 회귀 `55 passed`, L0 import-direction
   회귀 `2 passed`, Pyright 0 errors, Ruff/formatter, compileall, Bandit, Vulture,
   camelCase, 엄격 4·9-section docstring, quality gate, `silentSubstitute`,
   diff whitespace가 통과했다. `coreBoundary --strict` 위반 0이고 `folderSize`의
   over-split은 0, under-split은 기존 3개만 남는다. 최종 diff 뒤 전문 에이전트가
   읽기 전용으로 완주한 공식 Guard
   `strict --scope l0-l15 --providers dart,edgar`는 1,766개 파일, 7/7 규칙과 cycle,
   architecture, folder mirror, gather, provider, public API 여섯 외부 gate를 모두
   통과했다. 알려진 부채 47건은 active 9, protected Company 38로 기존 원장과 일치한다.
7. **남은 부채와 판정.** provider의 `_CATEGORY_TAGS`와 SEC Item taxonomy mirror가
   L0 catalog를 직접 소비하도록 수렴하는 작업은 L1 owner 순서로 이월하며 이번에
   상향 수정하지 않았다. 전역 folderSize에는 `memory.py` 862 LoC, `ratios.py`
   1,900 LoC, `schemas.py` 848 LoC 세 under-split이 남는다. 다음 단일 항목은 출력
   순서의 첫 항목인 `memory.py`다. 따라서 L0-15만 완료이고 **L0 전체는 미달**이다.

### L0-16 메모리 cache·IPC·memoization·OOM 수명주기 안정화

**상태: 완료.** 옛 862 LoC 단일 파일의 공개 import 호환성은 유지하면서 cache,
OS RSS 관측, 계산 memoization, OOM guard를 최소 책임 경계로 분리하고 실제 호출자의
원자성·상한·오류 전파 계약을 닫았다.

1. **범위와 실제 호출자.** 옛 `core/memory.py`는 OS RSS 측정, `BoundedCache`,
   `memoizedCalc`, 함수 예산, background OOM 감시와 죽은 profiling API를 한 파일에
   섞었다. 생산 import census는 87파일 99곳, `memoizedCalc` 소비 61파일과 실제
   decorator 144개, 직접 `BoundedCache` 생성 8곳, DART·EDGAR·EDINET Company context
   3곳이다. 직접 생성자는 core TTL cache, DART·EDGAR Company, DART Notes·Report,
   event study, news sentiment, server price event이며 모든 생성자와 2단계 조회 호출자를
   추적했다. 전문 검토는 실제 특수 signature와 Company 재진입까지 독립 재현했다.
2. **제품·안전 결함 재현.** `memoizedCalc`가 추가 위치 인자를 거부해
   `_latestAnnualVal(company, stmt, accountName)`와
   `calcBreakdown(company, sub, basePeriod=...)`가 `TypeError`였고, 서로 다른 module의
   동명 `calcMacroSensitivity`가 같은 key를 썼다. cache 조회가 `in` 뒤 item을 읽어
   eviction race가 있었고, 기존 key 갱신은 pressure를 검사하지 않았다. `pressureMb`를
   무시하고 작은 max를 pressure에서 키웠으며 pinning은 resident 상한을 깨뜨렸다.
   emergency 직후 `clear`하면 1초 cooldown 동안 max가 30으로 복구되어 지속 3,000MB
   표본에서 resident 20개가 다시 쌓였다. IPC는 disk 값을 읽지 않거나 pop·clear 뒤
   부활했고, DataFrame을 일반 값으로 바꿔도 stale 파일이 남았으며 정규화 path 충돌과
   zstd의 가짜 mmap이 있었다. cache 생성만으로 임시 폴더를 만들던 결과 이 환경에는
   과거 `dartlab-cache-*` 폴더 10,156개가 남아 있었다. OomTripwire join timeout은
   살아 있는 thread 참조를 잃었고 sampler·exiter 실패와 Company cleanup 실패를
   삼켰다. 같은 Company 중첩 진입은 첫 watcher를 덮어써 영구 daemon thread를 남겼다.
3. **owner와 SSOT.** `memory/cache.py`는 generic `CachePolicy`, bounded LRU, exact-key
   IPC와 atomic lookup/build를, `metrics.py`는 Windows psapi와 Linux procfs RSS를,
   `memoization.py`는 signature·owner·semantic key를, `guards.py`는 retained RSS
   budget, OomTripwire, `MemoryScope`와 종료 오류 보존을 소유한다. `memory/__init__.py`는
   기존 공개 경로의 facade다. core의 EDGAR 전용 상수는 최종 제거했고 EDGAR Company만
   generic policy에 정확한 `_sections` key를 주입한다. DART와 일반 cache는 빈 정책이다.
4. **수정과 테스트.** `BoundedCache.lookup`과 `lookupCache`로 저장된 `None`과 miss를
   한 번의 조회로 구분하고, accessor 생성과 memoized 계산은 key별 `getOrCreate`
   single-flight를 쓴다. pressure는 insert·update·IPC reload 모두에서 주입 임계와
   절대 fatal/emergency tier를 적용하고 max를 절대 늘리지 않는다. cooldown은 GC만
   제한하며 축소 max와 eviction은 항상 적용한다. IPC 폴더는 최초 exact-key DataFrame
   때만 만들고 digest filename, uncompressed Arrow, staging 뒤 atomic replace,
   mmap reload, pop·clear·타입 변경 무효화를 사용한다. `memoizedCalc`는 임의 signature,
   truthy overrides 우회, owner namespace와 의미 인자 digest를 보존한다. `MemoryScope`는
   Company별 watcher 하나를 소유해 중첩 진입을 fail-fast하고 정상 종료 뒤 순차 재사용,
   종료 실패 뒤 active 유지와 재시도를 강제한다. 본문·tripwire·cleanup 예외는 단일
   예외 또는 `BaseExceptionGroup`으로 모두 보존한다. 죽은 `profileCall`,
   `memoryGuard`와 그 전용 property test를 제거하고 protocol·README·logger의 거짓
   silent/native-heap 계약을 현재 행동으로 맞췄다.
5. **공개 행동, 정확성, 속도, 메모리.** 실제 특수 decorator 둘과 동명 함수 둘은
   올바른 값과 분리 key를 내며, `None` cache, dict 주입, IPC write/reload/pop/clear,
   손상 fallback, path 충돌, Company 중첩·순차·종료 실패 행동을 회귀로 고정했다.
   지속 3,000MB 표본에서 emergency clear 직후에도 `_max=3`, resident 3 이하이다.
   같은 process의 옛 구현 대비 median은 `get 0.60066 -> 0.59275 µs`,
   item `0.61143 -> 0.50805 µs`, 10만 set `383.910 -> 267.775 ms`,
   IPC write `83.243 -> 52.140 ms`, IPC read
   `592.795 -> 26.262 ms`로 read가 약 22.6배 빨라졌다. lazy constructor 별도 실측은
   `649.622 -> 5.434 µs/instance`로 약 119.5배 줄었다. 대신 50만 행 임시 IPC는
   `1,091,940 -> 8,001,428 B`로 약 7.33배 커졌다. 이 파일은 EDGAR Company의 exact
   `_sections` 한 세대만 소유하며 speed와 임시 저장공간의 명시적 tradeoff다.
6. **Guard와 회귀.** 최종 집중 회귀는 `64 passed, 1 skipped, 3 deselected`이고,
   직접 변경 호출자 묶음은 DART 112, EDGAR·EDINET 26, 분석·소비자 49,
   cache·context 24로 `211 passed, 1 skipped`다. 변경 테스트와 memory package
   Pyright 0 errors, Ruff, compileall, Vulture, diff whitespace가 통과했고 Radon
   평균은 A(3.32), C 이상 block은 0이다. 정확 coverage gate는 공개 함수·method
   19개 중 누락 0, `checkSilentFail` 위반 0, `coreBoundary --strict` 위반 0이다.
   core folderSize는 over-split 0이며 기존 under-split은 `ratios.py`,
   `schemas.py` 두 건만 남는다. 전문 최종 검토는 차단 결함 0과 wheel의 memory
   5모듈 포함을 확인했다. 동결된 최종 diff 뒤 공식 Guard
   `strict --scope l0-l15 --providers dart,edgar`는 1,770파일, 7/7 규칙과 cycle,
   architecture, folder mirror, gather, provider, public API 여섯 외부 gate를 모두
   통과했다. 알려진 부채 47건은 active 9, protected Company 38로 원장과 일치한다.
7. **남은 부채와 판정.** Windows에서 외부가 기존 mmap DataFrame을 보유한 채 같은
   IPC를 덮어쓰면 `os.replace`가 실패할 수 있으며 이때 warning 뒤 정확한 heap 값으로
   fallback해 그 세대의 disk 성능 이점만 잃는다. macOS RSS는 현재 지원하지 않아
   `-1.0`으로 측정 불가를 명시하며 release platform CI 증빙으로 남긴다. 과거 버전이
   만든 10,156개 임시 폴더는 소유권을 추측해 삭제하지 않았고 새 구현은 생성과 회수를
   정확히 제한한다. 다음 단일 항목은 `ratios.py` 1,900 LoC이고 그 뒤가
   `schemas.py` 848 LoC다. 따라서 L0-16만 완료이며 **L0 전체는 미달**이다.

## 정량 판정 (2026-07-27 실측)

체크리스트 여섯 중 셋을 지금 잴 수 있다. 셋 다 미달이다.

| 항목 | 기준 | 실측 | 판정 |
|---|---|---|---|
| Q2 헬퍼 파일 수 | 6 이하 | **16** | 미달 |
| Q3 F 등급 함수 (복잡도 31+) | 150 이하 | **163** | 미달 |
| Q5 공개 함수가 전부 미테스트인 파일 | 0 | **193** | 미달 |

Q5 는 원래 "0% coverage 파일 0 개" 다. 커버리지 실행 대신 공개 함수 전부가 테스트 참조 0 인
파일로 근사했다. 실제 0% 보다 좁은 집합이라 실제 미달 폭은 이 숫자보다 크다.

Q1(routing SSOT 통합), Q4(realData 30% 단축), Q6(외부 venv 종합 smoke)은 별도 실행이 필요해
아직 재지 않았다.

### 세부

**Q2 헬퍼 16 개.** analysis 다섯, valuation 둘, credit, gather, macro 둘, forecast, insight 등.
게이트가 요구하는 것은 개수 줄이기가 아니라 소비자가 하나뿐인 헬퍼를 소비 파일로 흡수하고
중복 formatter, validator 를 한 곳으로 모으는 것이다.

**Q3 F 등급 163 개.** 최악은 `synth/strategyRules.py::evaluateStrategies` 164,
`analysis/forecast/_revenueForecastCore.py::forecastRevenue` 149, `simulate/world.py::_checkInputs`
124 다. E 등급(21~30)이 296 개, C~D(11~20)가 1,216 개다.

**Q5 미테스트 파일 193 개.** quant 49, analysis 28, scan 19, macro 19, ai 18, core 14 다.
공개 함수가 가장 많은 미테스트 파일은 `core/indicators/volume.py` 11 개다. 여기가 L0 라서
가장 먼저 닫아야 할 자리다.

## 계층별 판정

| 계층 | 상태 |
|---|---|
| L0 core | 완료 (2026-07-29~30) |
| L1 gather, providers | 완료 (2026-07-30) |
| L1.5 scan, frame, synth, reference | 완료 (2026-07-31) |
| L2 analysis, macro, quant, industry, credit | 순차 안정화 진입 대기 (과거 판정 미달) |
| L2.5 dataHub | L0 완료 전 재검토 대기 (과거 판정 미달) |
| L3 story, simulate | L0 완료 전 재검토 대기 (과거 판정 미달) |
| L4 소비자, ai, mcp | L0 완료 전 재검토 대기 (과거 판정 미달) |

## 현재 판정

**v1.0.0 선언 불가.** 정량 세 항목이 미달이고, 일곱 계층 전수 검토 결과 일곱 계층 모두 미달이다.

## L0 core 판정 (2026-07-27)

전문 에이전트 둘이 구조와 코드품질을 나눠 훑었다. **둘 다 미달 판정**이다.

구조 쪽 근거는 이 계층이 자기 기반 추상의 두 번째 사본을 만들고 첫 번째를 끝내 지우지
않았다는 것이다. `SecretStore` 가 둘, plugin 발견 체계가 둘(같은 entry point group 을
각자 읽는다), `getDefaultProvider` 가 둘, `CredentialStatus` 가 둘, Altman Z 가 둘이었다.
호출자 0 인 코드가 약 2,000 줄로 계층의 9% 다.

코드품질 쪽 근거는 L0 이 "값 없음" 을 그럴듯한 숫자로 바꿔 내보낸다는 것이다. 예외가
아니라 잘못된 값으로 나타나기 때문에 위층에서는 원인을 볼 수 없다.

### 닫은 것

| 결함 | 증상 | 상태 |
|---|---|---|
| `resolveLatestPeriod` | 이 모듈이 만드는 표준형 '2024-Q1' 을 못 읽어 최신 기간이 실행마다 달랐다 | 수정 |
| `isClose` | NaN, None, 문자열이 전부 통과. 값 빠진 대차대조표가 항등식 검증을 통과 | 수정 |
| `toDecimal` | 문서는 ValueError 를 약속하는데 다른 예외가 샜다 | 수정 |
| `vsma` 결측 오염 | %D, KDJ 세 출력, stochRsi %D 가 전 구간 NaN. 계산이 죽어 있었다 | 수정 |
| 자본잠식 비율 | 적자 기업 ROE 가 +200% 로 수익성 랭킹 상단에 올랐다 | 수정 |
| CCC 판정 | 재고 0 인 회사가 미산출로 떨어지고, 시점과 시계열 경로가 서로 다른 답 | 수정 |
| 신선도 확인 실패 | 실패를 "확인했고 최신" 으로 기록해 침묵이 스스로 연장 | 수정 |
| plugin 메타 | 보강한 kind, schema 가 버려져 조회 표면이 언제나 비어 있었다 | 수정 |
| `help` 안내 경로 | `dartlab.plugins.listPlugins` 가 실재하지 않아 AttributeError | 수정 |
| `core/secrets.py` | 구현체와 끝내 만나지 못한 추상. 호출자 0 | 삭제 |

미테스트였던 L0 모듈 여섯에 회귀를 세웠다. 거래량 지표 11 함수, 가격 지표 3, DataFrame
판정 2, TTL 캐시, 기간 표기, 십진 변환이다.

### 남긴 것과 이유

`financeDocAccessor` seam 은 등록 호출이 0 이라 영원히 None 을 돌려주고 소비자 여섯의
첫 분기가 죽어 있다. 동작은 이미 동일하므로 정리 대상이지 결함이 아니다.

두 plugin 체계가 같은 entry point group 을 각자 읽는 문제는 외부 플러그인 계약을 바꾸는
일이라 운영자 결정 사안이다.

당시에는 `core/schemas.py`의 호출자 없는 Pandera 클래스를 보존하기로 했지만, 이 결정은
2026-07-29 L0 전체 마감에서 실제 생산자 계약과 어긋난다는 근거로 폐기했다.

`.dartlab.yml` 프로젝트 설정은 `loadProjectConfig` 호출자가 0 이라 문서화된 기능이 아예
동작하지 않는다. 배선하든 지우든 사용자에게 보이는 변화라 운영자 결정 사안이다.

### 정량 재측정

수정 뒤에도 Q2 헬퍼 16(기준 6), Q3 F 등급 163(기준 150)은 그대로다. 이번에 닫은 것은
정확성 결함이지 복잡도나 헬퍼 정리가 아니다.

**L0 판정: 미달.** 정확성 결함 열 건을 닫았으나 구조 기준(SSOT 중복, 호출자 0 코드)과
정량 기준 둘이 남아 있다.

## L1 gather, providers 판정 (2026-07-27)

전문 에이전트 셋이 providers 구조와 결함, gather 수집 정직성, providers 죽은 코드와 중복
파서를 나눠 훑었다. **셋 다 미달 판정**이다.

providers 쪽 근거는 DART OpenAPI 응답에 없는 필드를 읽고 있는 자리가 있다는 것이다.
내부자 거래 여섯 필드 중 넷이 틀렸고 그중 둘은 서로 뒤바뀌어 있어 거래 방향 자체가
뒤집힌다. `_safeInt` 가 모든 미스를 0 으로 바꾸므로 예외 없이 확신에 찬 숫자로 나간다.

gather 쪽 근거는 KIND 가 잠깐 끊기면 빈 상장목록이 24 시간짜리 파일 캐시에 굳는다는
것이다. 30 초짜리 끊김 하나가 KR 종목코드 해석을 하루 종일 죽이고, 네트워크가 돌아와도
회복되지 않으며, 사용자에게는 0 개 로드 완료라는 성공 문구가 나간다.

### 닫은 것

| 결함 | 증상 | 상태 |
|---|---|---|
| 서술 표 단위 해석 | '(단위: 억원, %)' 100 배 축소, '조원' 100 만 배 축소. 그 값에 confidence high | 수정 |
| KIND 장애 캐시 오염 | 빈 목록을 24 시간 캐시에 저장해 회복 차단 | 수정 |
| 아키텍처 회귀 낡음 | 죽은 seam 의 이름 존재로 계층 방향을 확인하고 있었다 | 수정 |

### 확인했으나 현재 오답은 아닌 것

`_common/tableParser.parseAmount` 가 선행 마이너스를 버려 '-1,234' 를 +1234 로 읽는다.
다만 그 동작은 계약금액 전용이라고 문서와 테스트에 명시돼 있고, 재무제표 경로인
`extractAccounts` 는 호출자가 0 이라 실제로 도달하지 않는다. 잠재 함정이지 현재 오답이
아니므로 문서화된 동작을 근거 없이 바꾸지 않았다. 같은 이름의 함수가 `dart/tableRows` 에
따로 있고 그쪽은 부호를 지킨다는 점이 함정을 키운다.

`_common/tableParser.detectUnit` 과 `panel/build/cell._detectUnit` 도 억원을 모르지만
둘 다 호출자 0 이다.

### 남은 것

내부자 거래와 대주주 필드 매핑, 분기 역누적의 위치 기반 shift, EDGAR 분기 키의 12 월
결산 가정, 세 parseAmount 와 여섯 단위표의 분열, gov 페이징 무언 절단, 시장 구분이 빠진
가격 캐시 키. 각각 회귀가 함께 가야 하는 수정이라 한 번에 묶지 않는다.

**L1 판정: 미달.**

### L1 후속: 내부자 거래 필드 실측 확정 (2026-07-27)

앞서 "회귀가 함께 가야 하는 수정" 으로 미뤄 둔 항목을 실제 DART 응답으로 확인해 닫았다.

`elestock.json` 에는 `ofcps` 도 `ctr_motive` 도 없다. 그 두 이름을 읽어 직위와 사유가
언제나 빈 문자열이었다. 대주주 쪽 `report_nm` 과 `change_on` 도 응답에 없다.

더 무거운 것은 소유주식수와 증감주식수를 서로 바꿔 읽고 있었다는 점이다. 삼성전자 정용준
부사장 행이 소유 2,000 주 증감 1,000 주인데 화면에는 증감 2,000 주로 나갔다. 거래 규모가
두 배로 부풀고 보유량은 절반이 된다.

거래 유형은 응답에 필드가 없어 증감 부호로 파생한다. 없는 필드를 읽어 빈 문자열을
내보내는 것보다 있는 자료로 답하는 쪽이 맞다.

회귀는 실제 응답 행을 그대로 쓴다. 소유수와 증감수가 같은 행으로 검사하면 바꿔 읽어도
통과하므로 다른 행을 골랐다.

## L1.5 scan, frame, synth, reference 판정 (2026-07-27)

전문 에이전트 둘이 scan 과 나머지 세 형제를 나눠 훑었다. **둘 다 미달 판정**이다.

scan 쪽 근거는 연결재무제표 우선 필터가 회사별이 아니라 유니버스 전체 결정으로 구현돼
있다는 것이다. 별도재무제표만 내는 회사가, 다른 회사가 연결을 낸다는 이유로 전종목 표에서
사라진다. 같은 블록이 11 곳에 복사돼 있어 결함도 11 개다.

synth 쪽 근거는 가치평가 원시값이 없는 계산을 매직 상수로 대체하면서 그 결과를 계산값과
구분할 수 없는 모양으로 돌려준다는 것이다.

### 닫은 것

| 결함 | 증상 | 상태 |
|---|---|---|
| 프리셋 2/8 매 호출 예외 | 목록에 제시하면서 부르면 죽었다. 없는 축 이름, 형제와 다른 컬럼명 | 수정 |
| 바텀업 베타 무작위 표본 | 전 종목 무작위 peer 에 같은 섹터 베타를 심고 `bottom_up` 라벨. seed 가 실행마다 달라 같은 회사가 매번 다른 베타 | 수정 |
| `frame/sector` 두 모듈 | 하위 호환 경로를 표방하나 import 자체가 ImportError | 삭제 |
| 가치평가 docstring 예제 | 존재하지 않는 `SECTOR_PARAMS` 를 안내 | 수정 |

미테스트였던 `frame/resolve` 에 회귀 16 건을 세웠다.

### 남은 것

연결 우선 필터의 회사별 전환(11 곳 공통 헬퍼 필요), 결손 입력을 적자와 급감으로 등급
매기는 자리, `screen` 멤버 수 절단, `asOf` 를 받아 놓고 아무도 지키지 않는 것, 시장 값이
인식 불가여도 KR 로 떨어지는 것, `impliedERP` 가 지수 수준과 무관한 값을 `gordon_simple`
이라 라벨하는 것, `damodaranL15` 의 `or 리터럴` 12 자리가 0 을 결측으로 취급하는 것.

각각 회귀가 함께 가야 하고 일부는 전종목 표의 유니버스를 바꾸므로 한 번에 묶지 않는다.

**L1.5 판정: 미달.**

## L2 analysis, credit, macro, quant, industry 판정 (2026-07-27)

전문 에이전트 둘이 나눠 훑었다. **둘 다 미달 판정**이다.

analysis 와 credit 쪽 근거는 이 계층이 "측정하지 못했다" 를 특정한 유리한 숫자로 바꿔
내보내는데, 그것이 중간값이 아니라 사용자가 행동하는 최종 판단(할인율, 신용등급, 적정가)
이라는 것이다.

macro, quant, industry 쪽 근거는 측정 계층 자체를 믿을 수 없다는 것이다. 종합순위가 부호
반대로 나가고, 백테스트 샤프가 자기가 물린다고 밝힌 비용을 하나도 반영하지 않으며, 과적합
확률이 상수 1.0 이다.

### 닫은 것

| 결함 | 증상 | 상태 |
|---|---|---|
| 종합순위 부호 반대 | `quant("순위")` 가 상위가 아니라 하위 50 종목을 냈다. 마진 -5%, 부채 400% 짜리가 1 위 | 수정 |
| 거시 정규분포 CDF | 지수항 계수 누락으로 최대 오차 0.037. 문서 주장(7.5e-8)보다 50 만 배 | 수정 |
| WACC 베타 역전 | 정교한 옵션을 켜면 섹터 베타 1.2 대신 대체값 1.0 이 들어가 할인율이 낮아짐 | 수정 |
| WACC 자본잠식 | 음수 자기자본이 가중치를 뒤집어 가장 위험한 회사가 최저 할인율 | 수정 |
| 은행 적정가 | 주식수를 주가로 만들어 상승여력이 주가와 무관한 상수 | 수정 |

베타와 자기자본 판정에는 출처 표시를 함께 실어 대체값과 계산값이 구분되게 했다.

### 남은 것

팩터 형성 시점의 look-ahead(수익률 구간이 정렬 정보보다 앞선다), 백테스트 샤프의 비용
미반영, 과적합 확률 상수 1.0, Sortino 하방편차 정의 오류, 스타일 규칙의 전구간 분위수,
CPCV 이음매 수익률, 실패 fold 를 샤프 0 으로 세는 것, Altman 자동 모드의 모델 혼용,
Beneish 의 결측 다수 기본값, Track B 유동성 가중 0, 감사의견을 키워드 부재로 추정하는 것.

팩터 형성 시점과 스타일 전구간 분위수 둘은 발표된 모든 수치의 의미를 바꾸므로 별도 계획이
필요하다.

**L2 판정: 미달.**

## L2.5 data 판정 (2026-07-27)

**미달.** 다만 구조가 아니라 폭이 좁은 갭이다. 이 계층은 아래층들과 다르게 정직 장치를
스스로 갖추고 있다. `contentHash` 가 실패하면 영수증이 `UNSEALED` 를 찍고 스냅샷 id 를
비우고 품질단언이 실패로 나가는 식이다. 그것이 이 계층의 기준선이라 나머지가 어긋난 것이
눈에 띈다.

강한 판정 근거는 하나다. 부분 결과를 안 받겠다고 고른 요청에서, 버린 행의 성적표와 영수증이
그대로 남아 같은 봉투 안의 세 증적이 서로 다른 말을 했다. 하필 부분 답을 거절하려고 고르는
자리다.

### 닫은 것

| 결함 | 증상 | 상태 |
|---|---|---|
| requireComplete 증적 불일치 | partitions 0 인데 succeededPartitions 1, 영수증 1 장 | 수정 |
| resolver 스키마 오류 비systemic | 시장 전체 실패가 partial 로 내려감. 형제 경로는 전부 systemic | 수정 |
| resolver 예외 문구가 code | code 공간 무한 + 로컬 경로가 공개 결과에 노출 | 수정 |
| 문서 예제 `credit.overview` | 실재하지 않는 asset. 복사하면 ASSET_NOT_FOUND | 수정 |

### 기각한 것

`failures = len(gaps)` 를 `len(dataGaps)` 로 바꾸라는 제안은 받지 않았다. requireComplete
판정이 catalog gap 을 못 보게 되어, 해석조차 안 된 asset 이 있는데도 부분 행을 돌려주게
된다. `failures` 는 "답이 완전한가" 를, `failedAssets` 는 "몇 asset 이 자료를 못 냈나" 를
재는 서로 다른 자다. 지금 갈라져 있는 것이 맞다.

### 남은 것

`executeDataQuery` 복잡도 104(다음이 68), 세 paging 레인의 `_failedResult` 중복 약 120 줄,
generation key 가 엔트리 모듈만 해싱해 헬퍼 수정이 digest 에 안 잡히는 것, `temporalTruth`
가 언제나 참인 단언인 것, `UniverseCoverage` 가 레인마다 entity 와 shard 로 뜻이 갈리는 것,
죽은 코드 3 개 약 60 줄, 그리고 lease 갱신 실패를 원인 없이 삼키는 자리.

**L2.5 판정: 미달.**

## L3 story, simulate 판정 (2026-07-27)

**미달.** 두 엔진의 이유가 다르다.

story 는 자기 입력이 부정하는 문장을 확신 있게 내보냈고, 그것을 걸러야 할 검증기가 자료
부재를 통과로 셌다. 스무 검사가 전부 예외로 죽어도 보고서에는 "20개 불변량 전부 통과" 가
찍혔다.

simulate 는 결함의 성격이 다르다. 40,073 줄 중 38,235 줄(95%)이 어떤 공개 진입점에서도
닿지 않는다. `dartlab.simulate` 와 `Company.simulate` 가 닿는 것은 6 모듈 1,838 줄뿐이고,
Skill OS spec 도 없다. 잘 만들어졌고 테스트도 두텁지만 아직 사용자가 부를 수 없는 코드다.
그 안의 결함(AdaHedge 가 없는 면을 만점으로 셈, 영수증이 자기 규칙에 적은 필드를 안 읽음,
가중치를 채점 대상 주간으로 적합)은 지금 사용자에게 닿지 않으므로 story 뒤로 미룬다.

훌륭한 것도 있다. `story/lensTensions.py` 와 `lensProducts.py` 는 주장마다 knowledge
boundary 를 검사하고 근거 참조 무결성을 확인하며, 못 하면 낮추지 않고 예외를 던진다.
`driverCalibration` 4,536 줄은 적합과 표본외를 끝까지 분리하고 조용한 대체가 한 곳도 없다.
이것이 나머지가 맞춰야 할 기준선이다.

### 닫은 것

| 결함 | 증상 | 상태 |
|---|---|---|
| 평탄 계열을 추세로 판정 | 부채비율 100% 가 4 기 그대로인데 "지속적으로 증가하는 추세" | 수정 |
| 같은 문장의 자기모순 | "(보합)" 이라 적고 곧바로 "4기 연속 개선 중" | 수정 |
| 순손실 회사의 현금흐름 오독 | 영업현금 흑자인데 "영업현금흐름이 적자다" | 수정 |
| 자료 부재를 통과로 셈 | 지표 0 개인 회사가 3-test 한 칸을 공짜로 가져감 | 수정 |
| 예외를 삼키고 전부 통과 선언 | 스무 검사가 다 죽어도 "20개 전부 통과" | 수정 |
| 이자보상 0.0 에서 재무위기 검사 꺼짐 | `dr and ic` 가 최악의 순간에만 침묵 | 수정 |
| 설명과 구현이 다른 검사 4 종 | 배당 안 읽고 배당 말하기, 한 기 보고 5년 말하기 등 | 수정 |
| 문서 예제의 없는 블록 키 | `b["margin"]`, `b["cashflow"]` 복사하면 KeyError | 수정 |
| dashboard 렌즈 미등록 | 등록 누락이 fallback 으로 렌즈 하나에 조용히 내려앉음 | 수정 |

### 남은 것

story: `_safeCall` 이 177 블록 전부의 실패를 `[]` 로 돌려주면서 `limits` 나 `lensGaps` 에
아무것도 남기지 않아 보고서가 완전해 보이는 것, `storyTree` 의 결측 spread 가 안정성 주장이
되는 것, `narrative` 의 0 나눗셈이 밸류에이션 할인으로 바뀌는 것, 신용 블록의 결측 부도확률이
"0.00%" 로 찍히는 것, 추세 서사 두 함수의 중복.

simulate: 위 세 결함 + hindcast 의 `fill_null(0.0)`, 표본 수를 안 보는 hStar, 완벽히 일관된
신호를 최악 점수로 주는 scorecard, 3 주짜리 면이 t=867 로 1 위에 서는 것, 기간 대신 목록
위치로 수익률을 짚는 것, 자유도 0 인 적합이 rSquared 1.0 을 서명된 영수증에 싣는 것.

**L3 판정: 미달.**

## L4 ai, mcp 판정 (2026-07-27)

**미달.** 이 계층은 설계가 좋다. 모델 자율 도구 호출 본체, 실제로 동작하는 근거 계약,
레지스트리 하나로 모인 도구 정의, MCP 와 AG-UI 두 서빙 표면까지 갖췄다. 미달 판정의 이유는
설계가 아니라 **강행규칙이 "룰과 코드 자체로 충족" 된다고 선언한 안전 성질이 실제로는 어느
생산 경로에서도 성립하지 않았다**는 것이다.

본체는 감싸는 함수를 부른 뒤 세 줄 뒤에서 감싼 값을 통째로 잘라 냈다. 남기는 키 목록에 본문
키가 하나도 없었기 때문이다. MCP 경로에는 감싸는 호출 자체가 없었다. 실제로 마커가 붙던
곳은 선택 경로인 워크벤치 하나뿐이었다.

이것이 다른 결함들과 성격이 다른 이유는, 검증하지 않았기 때문에 생긴 갭이 아니라 **검증했다고
문서에 적어 둔 자리에서 생긴 갭**이라는 점이다. 감싸는 함수만 따로 시험하는 테스트가 이미
있었고 통과하고 있었다. 감싸기는 정말로 동작했다. 그 뒤 잘라 내는 단계가 결과를 지웠을 뿐이다.
경계 검사는 경계에서 해야 한다.

### 닫은 것

| 결함 | 증상 | 상태 |
|---|---|---|
| 마커가 모델에 미도달 | 감싼 값을 직후 trim 이 삭제. 웹 검색 본문도 함께 소실 | 수정 |
| 외부 제목 미감쌈 | 검색 결과 제목에 적은 지시문이 맨몸으로 전달 | 수정 |
| MCP 경로 미감쌈 | 외부 클라이언트가 웹, 스킬 본문을 마커 없이 수신 | 수정 |
| 문자열 목록 미감쌈 | 절차, 기준처럼 지시문 모양 필드가 목록이면 통과 | 수정 |
| 스킬 마켓 임의 주소 | 모델이 고른 주소를 그대로 열람. file:// 도 열림 | 수정 |
| 스킬 마켓 internal 표시 | 남이 쓴 절차문이 내부 자료로 표시돼 감쌈 대상 제외 | 수정 |
| Read 자격증명 노출 | .env 로 서비스 자격증명 17 개가 한 번의 호출로 노출 | 수정 |
| 근거 위조 통과 | 실재 id 의 앞부분이면 글자 하나짜리 토큰도 진짜 인용 | 수정 |
| 완전 실패를 성공 보고 | 대표 진입점이 ok 를 리터럴로 고정 | 수정 |
| 일시 실패의 영구 차단 | 실패 캐시가 재시도를 가로채 streak 이 도달 불가 | 수정 |
| 미검증을 통과로 표기 | GATE 를 안 도는 경로가 verification.ok=True | 수정 |
| MCP 안내문 오안내 | 서버가 거절하는 옛 도구명 안내 + 본체가 안 쓰는 그래프 광고 | 수정 |
| `__all__` 오탈자 | `from dartlab.ai import *` 가 AttributeError | 수정 |

### 감시 도구도 함께 고쳤다

감싸기 감시가 발급 파일마다 동행을 요구해서, 이미 덮인 파일이 부채로 잡히고 진짜 구멍인
MCP 길목은 검사 대상이 아니었다. 나가는 문 세 곳이 감싸는지 직접 보도록 바꿨다. 길목이
하나라도 무너지면 발급 목록 전체가 다시 위반이 된다. 부채 원장은 1 에서 0 으로 줄었다.

### 남은 것

RunPython 의 AST 차단이 alias import, getattr, importlib, 문자열 결합 등 여덟 우회 중 일곱을
막지 못한다. 이것은 차단 목록을 허용 목록으로 뒤집는 결정이 필요해 운영자 판단 사안이다.
GroundingCheck 가 주장 속 숫자를 근거의 값과 대조하지 않는다(토큰 존재만 확인). DCF 도구가
섹터 인자 해석 실패를 할인율 10%, 성장률 3% 로 조용히 대체하고 그 라벨이 실재하는 섹터명과
겹친다. 죽은 코드 셋(`ai/agents/` 157 줄, `providers/routing.py` 110 줄, `tools/_autogen.py`
191 줄). `_isLLMProvider` 와 `_resolveProvider` 가 kernel 과 gateway 에 중복돼 이미 갈라졌다.

**L4 판정: 미달.**

## 전수 검토 종합 (2026-07-27)

일곱 계층 전부 검토했고 일곱 계층 전부 미달이다. **v1.0.0 선언 불가.**

계층을 관통하는 결함이 하나 있다. **모르는 것을 그럴듯한 값으로 바꿔 내보내는 것**이다.
모양은 계층마다 다르지만 뿌리는 같다. L0 은 결측을 0 으로 바꿨고, L1.5 는 표본 없는 베타를
섹터 기본값으로 냈고, L2 는 자본잠식 회사에 최저 할인율을 줬고, L2.5 는 버린 행의 성적표를
남겼고, L3 은 부도확률을 못 구하면 0.00% 를 찍었고, L4 는 검증하지 않은 답에 검증 통과를
적었다. 매번 대체값이 하필 가장 안심되는 쪽이었다.

기존 감시 도구는 이 부류를 거의 못 본다. 넓은 except 가 상수를 return 하는 모양만 잡는데,
실제 사례 대부분은 `or 0`, `.get(k, 0)`, `if x and y` 같은 평범한 표현이라 예외 처리와
무관하다. 계층별 보고가 공통으로 지적한 지점이고, 감시 규칙 확장이 다음 과제다.

## 1.0.0 게이트 실측 (2026-07-28, 운영자 지시로 게이트 착수)

운영자가 "v1.0.0 을 선언하고 배포하는 것이 핵심 목표" 라고 지시해 릴리즈 게이트를 열었다.
`release_gate` 의 Q1~Q6 를 실측하고 미달분을 닫는다.

| 게이트 | 기준 | 착수 시점 | 현재 | 판정 |
|---|---|---|---|---|
| Q2 헬퍼 파일 수 | 6 이하 | 13 | **0** | 충족 |
| Q2 중복 함수 정의 | 1 곳으로 | 88 | 76 | 진행 |
| Q3 복잡도 31+ (radon E+F) | 150 이하 | 219 | 208 | 미달 |
| Q5 미테스트 공개 함수 | 0 | 1,250 | 1,250 | 미달 |
| Q5 src 줄 수 | 10% 감축 | 471,306 | 473,639 | 역행 |
| Q6 외부 venv 종합 smoke | 통과 | **10/11 실패** | **11/11** | 충족 |

### Q6 가 잡아낸 것

이 게이트가 실제로 결함을 잡았다. 격리 venv 에 wheel 을 설치해 돌리니 공개 계약인
`Company.analysis("종합평가")` 가 ValueError 로 통째로 죽었다. look-ahead 검사가 회계 기간
표기를 시점으로 오독한 탓이다. `latestPeriod: "2026"` 을 2026-12-31 로 읽으니, 2026 년
7 월에 2026 년 반기까지 받은 지극히 정상적인 결과가 미래를 봤다고 걸렸다. 범위는 끝이 아니라
시작으로 재야 한다는 것이 결론이다.

### Q5 는 게이트끼리 충돌한다

"줄 수 10% 감축" 과 "복잡도 감축" 이 같은 방향이 아니다. 복잡도를 낮추는 정공법은 함수를
쪼개고 왜 그 자리에 seam 이 있는지 적는 것인데, 그러면 모듈 헤더와 설명 주석만큼 줄이 는다.
이번 구간에 2,333 줄이 늘었고 그 대부분이 새 모듈의 docstring 과 seam 설명이다. 줄이려면
설명을 지우거나 쪼갠 것을 되돌려야 한다. 둘 다 제품에 해롭다. 이 항목은 기준 자체를 다시
볼 사안으로 남긴다.

### Q5 미테스트 1,250 의 실체

숫자만 보면 커 보이지만 **공개 계약 표면은 전부 테스트가 있다**. 열 엔진의 축 호출과
`Company` 파사드의 panel, select, filings, analysis, credit, story, quant 가 모두 테스트에서
불린다. 1,250 은 내부 헬퍼와 사적 함수다. `Company.topics` 만 미참조인데 강행규칙상 계약이
아니다.

다만 커버리지 감시의 baseline 이 양방향으로 낡았다. 기록은 1,106 항목인데 그중 651 만 현재
결손과 맞고, 현재 결손 599 는 baseline 에 없다. CI 게이트가 변경 파일만 보므로 지금 막고
있지는 않지만, 전수 판정 도구로는 못 쓴다.

### 이 구간에 닫은 결함

| 결함 | 증상 | 상태 |
|---|---|---|
| 전종목 스캔 순서 비결정 | 같은 질의가 매번 다른 순서. content seal 이 봉인 구실 못 함 | 수정 |
| statements scope 무시 | `scope="separate"` 가 연결 재무제표 반환 (별도 133조 자리에 연결 201조) | 수정 |
| 앙상블 두 소스 즉사 | BacklogSignal NameError, forecastMetric AttributeError | 수정 |
| 종합평가 크래시 | 회계 기간을 시점으로 오독한 look-ahead 검사 | 수정 |
| 품질 게이트 무력화 | 금지된 `scripts/` 를 baseline 으로 참조 + non-blocking | 수정 |
| 재현 해시 위치 의존 | 익명 람다 기본값이라 빈 줄 하나에 executableHash 변동 | 수정 |
| 플러그인 탐색 11 벌 복사 | 재진입 시 무한 반복 가능한 순서 | 수정 |

### 복잡도 리팩터 (전부 동작 보존 실측 증명)

| 대상 | 전 | 후 | 증명 |
|---|---|---|---|
| `simulate/world.py` 네 함수 | 176/154/77/76 | 14/15/8/7 | 94 변이 차등 대조, 불일치 0 |
| `synth/strategyRules.py` | 166 | 10 | 무작위 2 만 건 차등, 불일치 0 |
| `analysis/forecast` 매출예측 | 174 | 22 | 54 케이스 21 필드, 동일 |
| `dataHub/execution.py` | 108 | 38 | 7 질의 전 필드, 동일 |
| `viz/builder.py` | 85 | 10 | 49 어댑터 전수 스텁, 불일치 0 |

**현재 판정: 1.0.0 선언 불가.** Q3 와 Q5 가 미달이다.

## 하단 우선 안정화 원장 (2026-07-30)

진행 방식은 레이어를 아래에서 위로 하나씩 닫는 것이다. 하위 레이어에서 실호출로 드러난
결함은 해당 owner를 재개방해 한 체크포인트로 닫고, 근거·회귀·성능·잔존물 0을 기록한 뒤
커밋·푸시한다. 완료되지 않은 레이어를 둔 채 상위 레이어로 이동하거나 공식 Guard를 반복
실행하지 않는다. 공식 Guard는 L1.5 형제 전체가 동결된 뒤 한 번 실행한다.

### L1 panel 재개방 체크포인트: 완료

L1.5 network 실호출에서 드러난 DART panel 대형 회사 빌드 결함을 L1 owner에서 닫았다.
회사 전체 materialization과 실패 삼킴을 제거하고, 최대 2개 회사 fan-out, 공시 묶음별
짧은 수명 spawn process, pipe와 process sentinel 동시 대기, 48MiB expanded budget,
receipt 단위 stage/upsert를 적용했다. stage는 PyArrow 단일 writer로 임시 파일에 기록한 뒤
fsync·footer 검증·atomic replace하고, 부모가 모든 row group과 identity를 bounded 완독한다.
최종 artifact는 정확한 `PANEL_SCHEMA`, 최대 4,096행 row group, receipt provenance를 강제하며
실패와 cleanup이 함께 깨지면 `BaseExceptionGroup`으로 둘 다 보존한다.

구조는 zip 경로·메모리 입력과 해제 크기 검증을 `documentSource`, process 수명주기를
`documentProcess`, stage·artifact 발행을 `artifactWriter`, 기준선 오케스트레이션을
`baseline`이 소유하게 분리했다. 공개 API와 레이어는 추가하지 않았다. builder는
927 LoC에서 780 LoC로 내려가 새 folder-size 부채가 0이다.

동결 후보 실측은 000880 67공시를 337.34초에 빌드했고 process-tree peak는 767.29MiB다.
산출물은 62,830,889 bytes, 51,024행, 68 row groups, 최대 4,096행, 42기간이다.
16-col schema와 순서, corp, rceptNo→period, 정렬, receipt/blockOrder 유일성, content와
provenance가 모두 통과했다. 같은 artifact의 network bounded reader는 3.91초,
peak 148.16MiB로 통과했다. source hash는 실행 전후 동일했고 PID·stage·temp 잔존은 0이다.

회귀는 panel unit 77 passed, 실제 디스크·stream 동등성 2 passed, 손실·ratio 소비 4 passed,
Pyright 0, Ruff, formatter, compileall, docstring strict, silent-fail, camelCase,
public API coverage, folder baseline을 통과했다. 기존 생성 데이터 `noteTaxonomyData.py`
under-split 1건은 baseline 안이며 이번 변경으로 늘지 않았다.

다음 작업은 L1.5 scan network 체크포인트다. L2 이상은 L1.5 전체 완료 전 착수하지 않는다.

### L1.5 scan network 체크포인트: 완료

공개 `scan("network")`가 전 회사 panel을 runtime에 다시 읽고 source 쌍을 전부 비교하던
구조를 닫았다. runtime은 `network/affiliateDocs.parquet`만 읽고, prebuild가 panel의
계열회사 표를 회사별 최신 revision으로 해석해 membership과 기업집단 label을 발행한다.
공유 affiliate 역색인과 union-find를 써서 source 전쌍 비교를 없앴고, full과 incremental,
changed-to-empty, removed source와 affiliate 제거를 같은 artifact 계약으로 묶었다. 기존
artifact가 없거나 schema가 구형이면 full bootstrap으로 승격하며, realData CI와 정규
prebuild 모두 같은 validator를 사용한다.

회사명은 identity 근거로 쓰지 않는다. `corpProfile` v2의 13자리 ASCII 법인등록번호와
정확히 일치할 때만 상장 affiliate를 확정하고, name-only와 미확인·충돌 법인번호는 진단에
남긴다. 이 과정에서 종목 110990 디아이티가 이름이 같은 별도 법인 때문에 노루·사조 계열로
오분류되던 실제 오류를 제거했다. 최종 artifact에서 110990은 자기 source 한 행만 남고
000320을 포함한 잘못된 source 연결은 0이다. profile 3,981행은 v2 100%, 유효 jurir
3,943, 중복 jurir 0이며 원격 `Update KindList` run 30512166076과 HuggingFace 발행이
성공했다. 원격 artifact를 다시 받아 exact schema, v2 단일 version, 같은 행수와 identity
수를 확인했다.

구형 panel은 `contentRaw` 전체가 하나의 거대한 Parquet dictionary인 파일이 있어
batch 크기만 줄여도 dictionary 전체를 반복 decode했다. 105560의 content column은
비압축 576,758,445 bytes, 000880은 676.4MiB였다. `parquetContent`가 작은 dictionary
index page만 해독하고 필요한 dictionary id만 zstd stream에서 보존한다. null, 손상
varint, 길이 bomb와 multi-page를 fail-loud로 구분하고, 합법적인 oversized multi-page는
DuckDB single-thread와 전역 lock으로 직렬 처리한다. 신규 panel writer는
`contentRaw` dictionary를 만들지 않고 최대 4,096행 row group을 유지한다. PLAIN 경로는
선택 row group만 읽고 32MiB 초과 read를 직렬화한다. 신규 writer 재현은 기존 선택
222행과 byte-exact, 0.2872초, read RSS +75.67MiB, retained +1.08MiB였다.

최종 실제 corpus 2,930 panel, 2,931 row group full build는 494.938초, peak RSS
210.07MiB에 완료됐다. 산출은 51,527 bytes, 5,956행, source 2,431사, affiliate
2,604사, group 120개, schema v2다. 직전 완주 후보 811.734초와 1,784.93MiB보다
시간은 약 39%, peak는 약 88% 줄었다. 중복 source-affiliate, null identity, group
충돌, temp 잔존은 모두 0이다. no-change incremental은 0.141초이고 전후 SHA256이
같아 byte와 logical 결과가 모두 결정적이다. 최종 exact-state 단독 공개 product smoke는
3.515초, RSS delta 346.4MiB, peak 413.4MiB로 예산을 통과했다.

회귀는 network·prebuild·offline·EDGAR edge·profile·calendar·panel writer를 합쳐
132 passed, 최종 decoder와 writer focused 41 passed이며 audit rule을 포함한 최종
exact-state 묶음은 145 passed다. 변경 파일 Pyright 0,
Ruff, compileall, public API coverage, memory budget, camelCase, silent-fail,
docstring 4/9-section strict, provider mirror와 변경 모듈 folder-size strict를
통과했다. 독립 전문 재검토의 최종 잔여는 P0 0, P1 0, P2 0이다.

L1.5 전체는 아직 완료가 아니다. 다음 체크포인트는 scan의 남은 US audit, EDGAR
prebuild, universe, dispatcher와 KR report 구조 부채를 같은 방식으로 닫는 것이다.
그 뒤 frame, synth, reference 순서로 진행한다. 공식 Guard는 L1.5 형제 전체 동결 뒤
한 번 실행하며 L2 이상은 그 전 착수하지 않는다.

### L1.5 US coverage audit harness 체크포인트: 완료

EDGAR coverage 감사가 source 불변과 loader/network 0만 확인해 상장 universe와 finance
source, 성공 결과가 모두 0이어도 `passedSafetyGate=true`를 내던 release blocker를 닫았다.
schema v2는 빈 audited/source/success 집합을 각각 fail-closed하고, full audit에는 unique
CIK source coverage 90%와 공식 strict/flow/revenue 성공률 하한 30%/40%/50%를 적용한다.
임의 measure와 제한 표본은 성공·source가 하나 이상이어야 하며 full 하한을 수치처럼
오용하지 않는다. 실패 원인은 machine-readable code로 남긴다.

감사 guard도 프로세스 전역 영구 변조에서 구간 context로 바꿨다. Python audit hook은 한
번만 설치하되 감사 구간 밖에서는 비활성이고, dataLoader 함수는 실행 성공·실패와 무관하게
원본 identity로 복구된다. 같은 프로세스에서 감사 두 번 실행과 감사 종료 뒤
`socket.connect` audit event를 재현해 잔존 차단이 0임을 확인했다. revenue-only의
`four standalone revenue quarters`도 일반 실패로 뭉개지지 않고
`FEATURE_NO_COHERENT_FOUR_QUARTER_WINDOW`로 분류한다.

최종 코드 상태의 실제 7,683 ticker/6,069 unique CIK 전수에서 revenue-only는 4,038
성공(52.5576%), 189.837초, p50 87.916ms, p95 224.096ms였다. flow-only는 3,256
성공(42.3793%), 347.917초, p50 125.802ms, p95 453.128ms였다. 두 실행 모두 unique
source 5,662/6,069(93.2938%), missing 407, loader 0, network 0, listing과 source-set
digest 불변으로 새 gate를 통과했다. revenue는 수정 전 실행과 성공 4,038 및 source-set
digest가 같아 결정성도 확인했고, 최종 분류에서 `FEATURE_OTHER_FAILURE`는 0이다.

full-state strict는 최종 코드 100 ticker 표본에서 28 성공, 33.325초, source 73/75,
loader/network 0, source 불변을 통과했다. 전수는 15분 운영 한도를 넘겨 중단했으며 원인은
상위 `analysis/financial/edgarPitState`가 한 회사 반례에서 Polars collect 7,197회와 stock
candidate 119회를 반복하는 것이다. L1.5 audit harness 결함으로 숨기거나 성공을 주장하지
않고 해당 owner 레이어의 성능 차단 항목으로 원장에 남긴다. 하위 순서를 깨고 지금 상위
compiler를 수정하지 않는다.

회귀는 audit unit 12 passed, Pyright 0, Ruff, formatter, diff check를 통과했다. 독립
EDGAR 감사에서 확인된 다음 P0는 같은 L1.5의 다음 체크포인트인 EDGAR prebuild가 소유한다:
finance의 ticker/CIK 혼합, identity/prior/price 실패 뒤 빈·부분 scan 전체 덮어쓰기, 비원자
발행이다. 그다음 universe와 dispatcher를 닫으며 L2 이상은 여전히 착수하지 않는다.

### L1.5 EDGAR prebuild 체크포인트: 완료

finance, valuation, report 6종의 생산과 배포를 하나의 `buildEdgarPrebuild` 진입점으로
고정했다. 상장 universe의 canonical CIK와 ticker만 사용하며 CIK fallback, OTC와
비상장 혼입을 금지했다. finance는 10-K, 20-F, 40-F와 각 정정본을 포함하고 필요한 열만
12개 bounded worker로 읽는다. valuation 가격, employee와 auditor 직전 발행본, listed
원천과 SIC 원천의 손상은 빈 값이나 부분 성공으로 바꾸지 않고 원인을 포함해 실패한다.
모든 parquet는 같은 volume의 임시 파일에 zstd로 쓰고 footer의 행수와 schema를 확인한
뒤 fsync와 atomic replace로 교체한다. write와 cleanup이 함께 실패하면 두 원인을 모두
보존한다.

employee와 auditor는 1,108개 listed panel을 두 번 읽지 않고 같은 bounded pass에서
만들었다. 32MiB 초과 content chunk는 직렬화하고 작은 panel만 최대 2개 겹치며, 큰
파일을 먼저 처리해 allocator 잔류와 동시 peak를 제한했다. 실제 전수 실행은
1,982.777초, process peak 925.1MiB였고 employee 25,478행, 3,246종목과 auditor
32,900행, 3,890종목을 만들었다. 두 artifact 모두 stockCode/year 중복 0, exact schema,
listed identity를 통과했다.

실제 8종 cohort는 finance 23,683행, valuation 4,963행, shareholderReturn 35,610행,
debtMaturity 18,828행, execComp 6,500행, capitalChanges 23,219행, employee
25,478행, auditor 32,900행이다. finance는 5,423 ticker, listed 6,069 CIK 대비
89.3557%이며 source coverage는 5,662/6,069, 93.2938%다. 숫자 ticker, CIK/ticker
불일치와 stockCode/fy 중복은 모두 0이다. valuation은 4,963 ticker, 81.7762%이며
가격 snapshot의 원래 builtAt을 보존한다. XBRL report 4종도 listed identity와
stockCode/year 중복 0을 확인했다.

validator가 8종의 exact schema, nonempty, listed identity, key uniqueness, finance
CIK/ticker pair와 75% coverage 하한을 fail-closed로 확인한다. 통과 결과는 8개
artifact의 path, rows, bytes, SHA-256을 담은 결정적 `prebuild-manifest.json`으로
원자 봉인한다. provider 배포자는 상위 scan을 import하지 않고 manifest digest를
재검증한다. scan parquet, manifest, finance-us.json, search-index-us.json은 원격
head를 parent commit으로 건 단일 CAS commit에 같이 발행되며 HF transient 호출만
공용 retry를 사용한다. 배포 실패와 누락은 0건 성공으로 바꾸지 않는다.

최종 집중 회귀는 110 passed다. 변경 Python은 Pyright 0, Ruff, formatter,
camelCase strict, YAML parse와 diff check를 통과했다. L0-L1.5 Guard의 cycleScan,
architecturePytest, folderMirror, gatherGate와 public API smoke도 통과했다. 전체
providerGate에 남은 실패는 이번 diff가 아닌 기존 `company.py`, `dataDispatcher.py`,
`scanAccount.py` 크기와 `scanAccount.py` docstring 기준선 부채다. 공식 preflight의
Bash 실행은 현재 Windows에 WSL 배포판이 없어 시작할 수 없었으며, L1.5 형제 전체 동결
뒤 공식 Guard를 한 번 실행한다는 순서는 유지한다.

다음 체크포인트는 L1.5 universe다. 이후 dispatcher, KR report structure, frame,
synth, reference 순서로 하나씩 닫는다. L2 이상은 L1.5 전체 완료 전 착수하지 않는다.

### L1.5 universe 공개 계약 체크포인트: 완료 (2026-07-31)

범위는 scan 공개 facade `scan/scanClass.py`의 유니버스 선택 계약과 그 실제 호출자
(dartlab.scan · Company.scan · engines.scan spec을 읽는 AI agent)다. engines.scan
spec은 `inputs`·`requiredEvidence`·`## universe default`에서 `universe` 인자를
발행한다: 미지정이면 KR 전종목, `universe="US"`/`market="US"`는 미국, 종목 한정은
`{"stockCodes":[...]}`. 그런데 `scanClass.__call__`의 시그니처에는 `universe`
파라미터가 아예 없었다. `market`만 검증하고 `universe`는 `**kwargs`로 축 함수에
그대로 전달됐다.

제품 결함은 실호출로 재현했다. 전 축 함수 중 `universe`를 받는 것은 0개이고
`**kwargs`도 0개라, spec대로 `scan("ratio","roe",universe="KR")`를 부르면 사용자와
agent는 내부 함수명이 노출된 raw `TypeError: scanAccount() got an unexpected
keyword argument 'universe'`를 봤다. profitability·governance·account·ratio 넷 모두
같은 방식으로 죽었다. 대조군 `market=`는 정상적으로 명시 ValueError를 냈다. 즉
계약이 반쪽만 구현돼, 발행된 spec을 그대로 따르는 경로가 내부 오류로 깨졌다.

근본 원인은 유니버스 요청을 (시장, 종목 필터)로 해소하는 단일 소유자가 없었고
`market` 처리만 facade에 인라인돼 있었다는 것이다. L1의 유니버스 SSOT
`providers/universe.py::listedEquityUniverse`는 dataHub만 소비하고 scan은 참조하지
않았다. 산업 분류는 별도 SSOT(`dartlab.listing` 업종, `screen`의 `by:"industry"`)가
소유하므로 scan facade가 industryHint를 재구현하면 산업 분류 SSOT를 중복하게 된다.
따라서 `universe`를 entity-set(시장·종목) 선택자로만 소유하도록 경계를 확정했다.

수정은 facade 한 곳에 담았다. `_normalizeMarket`, `_normalizeStockCodes`,
`_resolveRequestedUniverse`가 `universe`(문자열 시장 alias · `{"market"}` ·
`{"stockCodes"}`)와 `market`를 하나의 (시장, 종목 필터)로 해소한다. 시장이 축의
`universeMarkets`에 없으면 거부하고, `universe`와 `market`이 다른 시장을 지정하면
충돌로 거부하며, `industryHint`는 industry 엔진·`screen by:"industry"`로 라우팅하는
명시 ValueError로 돌린다. 미지원 키·타입·빈 종목목록도 조용히 흘리지 않고 그
자리에서 막는다. 종목 필터는 결과 표의 `종목코드`/`stockCode`/`ticker`를 KR zero-pad와
US 대문자 변이로 매칭한다. engines.scan spec의 `## universe default`와 산업 라우팅
문구를 구현과 정확히 일치시켰다. `tests/scan/test_universeContract.py`에 계약 회귀
26건(시장 alias·종목 정규화·충돌·미지원 거부·종목 필터·US dispatch 분기·TypeError
비누출)을 추가했다.

공개 행동·정확성·속도·메모리는 실데이터로 확정했다. 전종목 `scan("profitability")`는
2,811행을 1.8737초, tracemalloc peak 0.38MB, RSS 증가 199.0MB로 반환했고,
`universe={"stockCodes":["005930","000660"]}`는 정확히 2행(000660·005930)을 1.4931초에
반환했다. 필터 결과는 전종목의 부분집합과 일치했고 ROE 값(24.5·9.7)이 필터 전후
동일해 값 보존을 확인했다. 종목 필터는 축이 전종목을 적재한 뒤 좁히는 post-filter라
전종목 default 동작과 같은 적재 비용을 갖는다(push-down은 없음).

Guard와 회귀는 변경 파일 범위에서 전부 통과했다. 신규 계약 회귀
`26 passed`, facade `market=`와 enrichment 인접 회귀(test_r27·test_consistency 포함)
`56 passed`다. `scanClass.py` Ruff·formatter·compileall·Pyright `0 errors, 0 warnings`,
`silentSubstitute --strict` 신규 위반 0, notebookContract(spec 코드펜스 AST) 신규
위반 0이다. 어떤 축 함수도 `universe`를 받지 않아 facade 가로채기의 회귀 위험은 0으로
확인했다.

남은 부채는 다음 순서로 넘긴다. 종목 필터의 소스 push-down(전종목 적재 회피)과
scan 유니버스를 L1 `listedEquityUniverse` SSOT로 직접 정합시키는 것은 dispatcher와
KR report 체크포인트에서 이어서 본다. 흡수된 sub-spec 예제의 `account=`/`metric=`
kwarg 표기와 scan 축 수 문서 표기(22 vs 27)는 이번 universe 계약 밖의 별도 문서
정합 부채다. 공식 Guard는 L1.5 형제 전체 동결 뒤 한 번 실행하는 순서를 유지한다.
다음 체크포인트는 L1.5 dispatcher다.

### L1.5 dispatcher 시장 분기 체크포인트: 완료 (2026-07-31)

범위는 scan 공개 facade의 KR/US 시장 dispatch(`scan/router.py::_edgarDispatch`,
`scan/builders/edgar/scan.py::edgarScan`, `scan/builders/edgar/helpers.py`)와 그
실제 호출자(dartlab.scan market="US", Company.scan)다. `_EDGAR_UNIVERSE_AXES`(13)와
`edgarScan._DISPATCH`(XBRL 11 + account/ratio 별도)의 1:1 주장은 실호출로 검증한
결과 정확히 맞아 그 부분은 결함이 아니었다.

제품 결함은 US 시장 안 축 간 identity 분열이었다. 형제 US 축(profitability/growth/...)
은 `scanAccount` 경유로 `stockCode=대표 ticker`와 상장 universe(`cikToTicker.values()`)를
쓰는데, audit 축만 `scanEdgarRawTags`가 `edgarDir.glob("*.parquet")`로 finance
디렉터리를 전부 훑고 raw 10자리 CIK를 stockCode로 emit했다. 실데이터에서 전자는
5,662 상장 source, 후자는 17,367 전 parquet(비상장·미매핑 11,705 포함)로 대상이
달랐고, 종목 식별자가 CIK와 ticker로 갈려 audit 결과는 다른 US 축과 stockCode로
join되지 않았고 universe stockCodes(ticker) 필터에도 걸리지 않았다. 또 `edgarScan`은
`_DISPATCH`에 없는 축을 값처럼 보이는 `{"info": [...]}` 1행 DataFrame으로 돌려주며
docstring에 그것을 "silent fail 회피"라고 잘못 적어, 미구현을 성공한 결과처럼 위장했다.

근본 원인은 US 축의 상장 universe와 ticker 정체성 SSOT(`edgarCikToTicker`,
`edgarListedFinanceSources`)를 audit 경로가 우회한 것과, 미구현 dispatch를 예외가
아니라 데이터 모양으로 표현한 것이다. audit도 형제와 같은 identity SSOT를 쓰게 하고,
미구현 dispatch는 loud 예외로 돌리는 것으로 경계를 확정했다.

수정은 두 곳이다. `scanEdgarRawTags`가 전 parquet glob 대신 `edgarCikToTicker` +
`edgarListedFinanceSources`로 상장 source만 순회하고 `stockCode=대표 ticker`를
emit한다. `edgarScan`은 미구현 축에 대해 info DataFrame 대신
`ValueError(가용 축 목록 포함)`를 던지고 docstring의 Returns·Raises·Capabilities·
Guide·How를 실제 동작에 맞췄다. `tests/scan/test_dispatcherContract.py`에 회귀 3건
(미구현 축 loud 거부, 구현 축 정상 dispatch, 합성 parquet 기반 ticker identity +
상장 universe 필터)을 추가했다.

공개 행동·정확성·속도·메모리는 실데이터로 확정했다. audit 스캔 대상이 전 parquet
17,367에서 상장 source 5,662로 좁아졌고(비상장·미매핑 11,705 제외) 해소는 0.107초다.
이 5,662는 앞선 US coverage audit 체크포인트의 unique source 5,662와 정확히 일치해
audit 축이 EDGAR 상장 source SSOT에 정합됐음을 보인다. identity 표본은
CIK 0000001750 -> ticker "AIR", 0000001800 -> "ABT", 0000002098 -> "ACU"로
raw CIK가 아니라 형제 축과 같은 대표 ticker다. 합성 parquet 회귀에서 값 보존과
비상장 제외를 함께 확인했다.

Guard와 회귀는 변경 파일 범위에서 전부 통과했다. dispatcher 회귀와 기존 edgar scan
helper 회귀 `6 passed`, `helpers.py`·`scan.py` Ruff·formatter·compileall·Pyright
`0 errors, 0 warnings`, `silentSubstitute --strict` 신규 위반 0(scanEdgarRawTags의
per-file skip은 기존 baseline 내)이다.

남은 부채는 다음 순서로 넘긴다. audit 축의 반환 스키마(AuditFees 등)는 여전히 KR audit
(opinion/auditor)과 달라 cross-market union 스키마 통일은 별도 사안이다. US valuation
축도 grade 없이 KR valuation과 컬럼이 달라 같은 스키마 부채를 공유한다. 전 상장 audit
스캔의 전수 실측은 다른 US 전수 경로와 같은 heaviness라 상장 source 축소 실측으로
갈음했다. 다음 체크포인트는 L1.5 KR report 구조다.

### L1.5 KR report 축 판정 정직성 체크포인트: 완료 (2026-07-31)

범위는 report 기반 KR scan 6축(governance·workforce·capital·debt·audit·insider)과
그 판정 산출부(`scan/audit.py`, `scan/debt/risk.py`, `scan/debt/__init__.py`),
prebuild 소유자(`scan/builders/kr/report/build.py`)다. 빌더는 카탈로그 구동
apiType 24종 도출과 배치 merge가 이미 정갈해 결함이 아니었고, 결함은 등급 산출부에
있었다. 6축 전수를 실데이터로 호출해 governance 2,872행, workforce 2,781,
capital 2,942, debt 2,832, audit 2,932, insider 2,608을 먼저 확인했다.

제품 결함은 자료 부재가 실질 리스크 판정으로 둔갑하는 것이었고 두 축에서 재현했다.
audit은 감사의견이 결측인 23종목 전부에 위험등급 "관찰"을 줬다. 원인은
`_OPINION_RISK.get(opinion, 1) if opinion else 1`로, 의견 부재와 표준 범주 밖
문자열이 모두 위험점수 1을 받는 것이다. 실데이터에는 `(*2)`, `주1)`, `(주1)` 같은
각주 마커가 감사의견으로 들어온 3종목이 있어 이들도 같은 경로로 "관찰"이 됐다.
debt은 `classifyRisk`가 ICR 결측일 때 상향 신호가 하나도 없어도 "관찰"을 반환해,
아무 자료가 없는 종목이 리스크 판정을 받았다. 형제 축 insider는 같은 상황에서
최대주주지분 결측 242종목에 정직하게 "미확인"을 주고, cashflow·growth는 "자료부족"을
쓴다. 즉 정직 gap 라벨이 이미 scan의 확립된 관례이고 audit·debt만 이탈해 있었다.

근본 원인은 등급의 몸통이 되는 입력(감사의견·ICR)이 없을 때도 합성 점수를 만들어
4단계 판정 격자에 밀어 넣은 것이다. 판정 가능 여부를 먼저 가르고, 불가하면 형제 축과
같은 정직 gap 라벨을 내는 것으로 정책을 통일했다.

수정은 두 곳이다. audit은 `_OPINION_RISK.get(opinion)`이 None이면 종합 점수를
만들지 않고 "자료부족"을 낸다. debt `classifyRisk`는 ICR 결측일 때 관측된 단기
리파이낸싱 사실(단기비중 50% 이상 또는 단기채무 존재)로만 "주의"로 상향하고, 그 신호도
없으면 "자료부족"을 낸다. 두 docstring의 반환 계약도 실제 동작에 맞췄다.
`tests/scan/test_reportGradeHonesty.py`에 회귀 11건을 추가했고, audit 쪽은 등급 규칙을
테스트에 복제하지 않고 합성 source를 monkeypatch해 실제 `scanAudit`을 호출한다.

공개 행동·정확성 실측은 수정 전후 전종목 분포로 확정했다. audit은 "관찰" 955에서
930, "주의" 4에서 3으로 줄고 "자료부족" 26이 생겼다. 26은 의견 결측 23과 각주 마커 3의
합과 정확히 일치한다. debt은 "관찰" 369에서 359로 줄고 "자료부족" 10이 생겼다.
ICR 결측 63종목의 최종 내역은 부채 자료 자체가 없어 null인 44, 판정 불가 "자료부족" 10,
관측된 단기채무로 정당하게 상향된 "주의" 9다. 정상 등급 경로의 분포(안전 1,911·
고위험 62, debt 주의 1,504·안전 736·고위험 179)는 그대로다. 축 실행 시간은 debt
6.48초, audit 6.21초로 변화가 없고 새 적재나 캐시도 없다.

Guard와 회귀는 변경 파일 범위에서 전부 통과했다. 신규 회귀 `11 passed`, 변경 3개
소스의 Ruff·formatter·compileall·Pyright `0 errors, 0 warnings`,
`silentSubstitute --strict` 신규 위반 각각 0이다.

남은 부채는 다음 순서로 넘긴다. `_normalizeOpinion`이 표준 범주 밖 문자열을 원본 그대로
돌려주는 것은 문서화된 동작이라 유지했고(사용자가 원본을 보는 편이 정직하다), 각주 마커가
감사의견 컬럼에 들어오는 것 자체는 report 원천 파싱 소유자의 부채로 남긴다.
`report/fields.py` 1,369줄의 분할과 governance 등급 산출의 결측 정책은 이번 판정
정직성 범위 밖이다. 다음 체크포인트는 L1.5 frame이다.

### L1.5 frame 자연어 해소·인벤토리 체크포인트: 완료 (2026-07-31)

범위는 `frame/` 7개 모듈과 실제 호출자다. 자연어 종목 해소(`frame/resolve.py`)는
공개 `dartlab.company.resolveFromText`와 CLI·server가 공유하는 원소스이고,
보고서 인벤토리(`frame/inventory.py`)는 `simulate.profile`의 세 축(인벤토리 census,
사업구조, 노동·설비)이 소비한다. `narrative.py`는 전수 대조에서 결측을 대체하지 않고
문서와 동작이 일치해 결함이 없었다.

제품 결함은 자연어 해소에서 재현됐고 사용자에게 다른 회사를 답하는 종류였다.
US ticker 분기가 검증 없이 대문자 1~5자 토큰을 회사로 확정하고, 한국 회사명 해소보다
먼저 실행됐다. 실호출에서 `"ROE 계산법 알려줘"`, `"DCF 설명해줘"`, `"IFRS 기준이 뭐야"`가
각각 ROE·DCF·IFRS라는 종목 질의로 바뀌었고, `"AI 반도체 어때"`는 공개 표면에서
미국 회사 `C3.ai, Inc.`로 해소됐다. 더 나쁜 것은 `"SK 하이닉스 실적"`이 `SK`(034730),
`"LG 화학 주가"`가 `LG`(003550)로 잡힌 것이다. 사용자가 물은 회사와 다른 회사의 답이
조용히 나갔다.

근본 원인은 둘이다. 첫째, ticker 주장에 실재 확인이 없었다. 둘째, 상장명은 공백 없이
등재되는데(`SK하이닉스`) 사용자는 공백을 넣어 치므로 2단어 후보가 통째로 매칭에 실패하고,
뒤이어 1단어 첫 토큰(`SK`)이 다른 회사로 먼저 잡혔다.

수정은 두 곳이다. ticker 분기는 로컬 US 상장 snapshot에서 읽은 ticker 집합에 실재할
때만 회사로 확정한다(네트워크를 켜지 않고, snapshot이 없으면 주장을 포기한다).
후보 매칭은 공백 제거 변형을 함께 시도해 `"SK 하이닉스"`가 `SK하이닉스`로 해소된다.
인벤토리 쪽은 빈 경로가 성공 경로와 다른 summary shape(`cataloguedUnits`·
`rawOnlyUnits` 누락)를 내던 것을 맞췄고, `_loadBoard`가 `MemoryError`와 `OSError`를
삼켜 OOM을 "단위 0개"라는 사실 주장으로 바꾸던 것을 자료 부재(`FileNotFoundError`·
`ValueError`)만 None으로 남기고 자원 실패는 전파하도록 고쳤다. 호출자
`simulate.profile` 세 곳이 실패를 잡으려고 둔 예외 분기가 그동안 도달 불가였다.

공개 행동 실측은 수정 전후 같은 질의로 확정했다. `ROE`·`DCF`·`IFRS`·`PER`·`EBIT`는
모두 `None`으로 회사 확정을 포기하고 원문을 그대로 돌려준다. `"SK 하이닉스 실적"`은
`000660` + 남은 질문 `"실적"`, `"LG 화학 주가"`는 `051910` + `"주가"`로 해소된다.
공개 표면에서도 `SK하이닉스`가 나온다. 종목코드 경로(`005930`), 한글 상장명 경로,
실재 US ticker 경로(`AAPL`)는 그대로다. US 상장 snapshot은 7,683 ticker이며
`SK`·`LG`·`ROE`·`DCF`·`IFRS`·`PER`·`EBIT`는 실재하지 않고 `AI`·`AAPL`·`MSFT`는 실재한다.

Guard와 회귀는 변경 파일 범위에서 통과했다. frame 전체 회귀 `35 passed`(기존 25 +
신규 10), 변경 2개 소스 Ruff·formatter·`silentSubstitute --strict` 신규 위반 0이다.
`inventory.py` Pyright 5건은 이번 hunk(119·160·173행) 밖 237·238·355행의 기존
`c.dart.key` 부채로, 이번 변경이 늘리지 않았다.

남은 부채는 정직하게 남긴다. `"AI 반도체 어때"`는 `AI`가 실재하는 US 상장 ticker라
여전히 C3.ai로 해소된다. 검증을 통과한 실재 ticker이므로 날조가 아니지만 한국어 질의
맥락에서는 모호하며, 맥락 휴리스틱은 추측이 되므로 도입하지 않고 문서화된 잔여
모호성으로 남긴다. `_statementUnits`가 board 내용과 무관하게 재무 5표를 `hasTable=True`로
주장하는 것은 의심 항목으로 조사했으나 실데이터 두 회사(005930·000660)에서 반증하지
못해 수정하지 않고 미검증 부채로 남긴다. `resolve.py`의 `strict=True`가 부분 문자열
매칭을 여전히 허용하는 것, 모듈 docstring의 존재하지 않는 심볼 예제,
`frame/sector/`의 재수출 3중화, `select.py`의 float 반올림 임계는 이번 해소 계약 밖
부채다. 다음 체크포인트는 L1.5 synth다.

### L1.5 synth 추정 비발행 체크포인트: 완료 (2026-07-31)

범위는 `synth/` 의 추정·역산 계산과 실제 소비자다. `eventStudy` 는
`analysis/eventStudy/newsImpact` 와 `quant/signal/eventStudy` 가, `impliedERP` 는
`analysis/financial/_proformaCore` 가 WACC 입력으로 소비한다. 전수 대조에서
`distress/survival`, `dalio48Match`, `macroCompanyContext` 는 실패에 source 를 붙이거나
예외를 올려 결함이 아니었다.

제품 결함 두 건을 재현했다. 첫째, `eventStudy._marketModel` 이 추정 구간 20 관측 미만
또는 특이행렬에서 `(alpha=0.0, beta=1.0, sigma=0.01)` 을 돌려줬다. `calcCAR` 은 이를
추정 결과처럼 `alpha`·`beta`·`sigma` 로 보고하고, 고정 sigma 를 t 값의 분모로 써
`isSignificant` 와 "유의 abnormal drift" 라는 결론까지 만들었다. 10일 추정 구간으로
실호출하니 실제로 `sigma=0.01`, `tStat=-0.192`, 확신에 찬 판정 문장이 나왔고 `error`
키는 없었다. 같은 모듈이 구간 초과·표본 부족에는 `{"error": ...}` 를 쓰므로 자기 관례도
어긴 것이다. sigma 가 0.01 로 고정되면 11일 창에서 CAR 6.5% 이상이 전부 유의로 판정된다.

둘째, `impliedERP` 는 Gordon 역산 ERP 를 발행하면서 분모로 시가총액이 아니라 자본총계
합산(장부가)을 썼다. 즉 `earnings_yield` 가 E/P 가 아니라 aggregate ROE 였고, 지수
레벨은 받아 놓고 산술에 쓰지 않으면서 `method="gordon_simple"` 라벨을 붙였다. 로컬
캐시에 실제로 `impliedERP: 12.0`, `totalERP: 12.0` (클램프 상한) 이 남아 있었다. 성숙시장
4.6% 대비 한국 ERP 12% 는 WACC 를 크게 밀어올려 모든 DCF 결과를 왜곡하며, 90일 동안
`source="cache_quarterly"` 로 계속 서빙된다.

근본 원인은 같다. 추정하지 못한 것을 추정값 모양으로 내보냈다. 시장모형은 표본이 없으면
모수가 없고, Gordon 역산은 가격이 없으면 성립하지 않는다.

수정도 같은 규칙을 따랐다. `_marketModel` 은 추정 불가에서 None 을 돌려주고 `calcCAR` 은
모듈 관례대로 `{"error": ...}` 를 낸다. 호출자 `newsImpact` 는 이미 `if "error" in
carResult` 를 검사하고 있어 계약이 그대로 맞물린다. `impliedERP` 는 L0-03 비정규 모델
비발행 계약과 같은 규칙으로 역산을 발행하지 않는다. 잘못된 계산 경로와 그에만 쓰이던
private 헬퍼를 제거해 347줄에서 101줄로 줄였고, 호환 키는 남기되 `impliedERP=None`,
`method="none"`, `source="fallback_historical"`, `sampleCount=0` 으로 비발행을 키에
드러낸다. 편향된 로컬 캐시 artifact 도 지웠다. 이 정리로 옛 `scan.io.parquet` 동적
import 가 사라져 synth 의 L1.5 cross import 도 0 이 됐다.

공개 행동 실측으로 효과를 확정했다. 추정 불가 구간의 `calcCAR` 은 이제
`{"error": "market model not estimable (estimation obs=10, 최소 20 필요 또는 특이행렬)"}`
만 반환하고 sigma·tStat·isSignificant·interpretation 키가 아예 없다. 추정 가능한 91일
구간의 정상 경로는 `alpha=0.00333`, `beta=0.122`, `sigma=0.0199`, `tStat=-2.142` 로
실제 추정치를 그대로 낸다. `calcImpliedERP("KR")` 의 `totalERP` 는 캐시가 내던 12.0 에서
큐레이션 정적값 5.2 로 바뀌었고(`matureMarketERP` 4.6 + `countryRiskPremium` 0.6),
`impliedERP` 는 None 이다. WACC 에 실려 있던 6.8%p 의 상방 편향이 사라졌다.

Guard와 회귀는 통과했다. 신규 회귀 `7 passed`, synth 단위 전체 `48 passed`,
변경 2개 소스 Ruff·formatter·Pyright `0 errors, 0 warnings`,
`silentSubstitute --strict` 신규 위반 각각 0이다.

남은 부채는 다음 순서로 넘긴다. implied ERP 재활성화에는 유니버스 시가총액 SSOT
(가격 x 상장주식수) 가 필요하며 배당·자사주 yield 와 payout 을 갖춘 원식으로 복원해야
한다. `damodaranL15._assumptions` 의 beta 1.0 · 세후 부채비용 4.5% · 성장 3% · 마진 10%
같은 매직 상수는 산업 기본값 JSON 에 해당 필드가 없는 기본 경로에서 전부 발화하고
`_costOfCapitalTable` 에 status 열이 없어 계산값과 구분되지 않는다. 다만 이 함수는
production 호출자가 0 이라 이번 순서에서 다루지 않고 별도 항목으로 남긴다.
`riskPremiums.loadDamodaranERP` 의 `source` 가 항상 상수이고 문서가 약속한 parquet
경로가 미구현인 것, 지원 국가 수 표기(90+ vs 실제 14)도 같은 항목이다.
다음 체크포인트는 L1.5 reference 다.

### L1.5 reference 대조 불가 표면화·매핑 SSOT 체크포인트: 완료 (2026-07-31)

범위는 `reference/docs/bridge.py` 와 `reference/mappers/accountMapper.py`, 그리고
실제 소비자인 server analysis API(`/api/company/{code}/topics/verify` 경로)와 매핑
호출자다. `reference/mapping/*` 운영 CLI, `reference/render/*` 재수출, capability
builder 는 전수 대조에서 이번 계약 밖이거나 이미 정직해 결함이 아니었다.

제품 결함은 실패가 사실 주장으로 바뀌는 것이었다. `getFinanceAmounts` 는 IS·BS·CF 세 장을
모두 못 읽어도 빈 dict 를 돌려줬고, 소비자 API 는 그 결과로
`matchRate = matched / max(extracted, 1)` 을 계산해 `matchRate: 0.0` 을 응답했다.
클라이언트에게 이 값은 "공시 본문 금액이 재무제표와 하나도 맞지 않는다" 는 경보성 결론이며,
대조 자체가 불가능했던 상황과 구분되지 않는다. 하필 회계 신뢰성을 점검하려고 부르는
자리다. 같은 파일 주석에 이 함수가 예전에 통째로 무력했던 사고가 이미 기록돼 있었다.

두 번째는 매핑 SSOT 분기다. `accountMapper` 는 모듈 docstring 에서 "매칭 로직은
`core.accounts.AccountNormalizer` 한 곳이 소유하며 같은 사전 위 두 매칭 분산은 SSOT
위반" 이라고 선언해 놓고, `korToSnakeId` 가 그 normalizer 를 우회한 raw dict 조회였다.
`lookup` 이 흡수하는 공백·괄호·하이픈 변형과 synonym 을 `korToSnakeId` 는 `None` 으로
돌려줘 같은 한글명이 경로에 따라 다르게 해소됐다.

근본 원인은 각각 "실패와 0 을 같은 모양으로 반환한 것" 과 "선언한 단일 소유자를 우회한
두 번째 매칭 경로" 다.

수정은 두 곳이다. `getFinanceAmounts` 는 재무를 한 장도 읽지 못했거나 대조할 기간이
없으면 원인을 담은 `RuntimeError` 를 올린다. `RuntimeError` 는 server 의
`HANDLED_API_ERRORS` 에 이미 포함돼 404 안내로 나가므로, 클라이언트는 "안 맞음" 대신
"대조 불가" 를 받는다. `korToSnakeId` 는 `AccountNormalizer` 로 위임해 `lookup` 과 같은
SSOT 를 쓴다.

공개 행동 실측으로 확정했다. 재무 부재(FileNotFoundError) 주입에서 이제 빈 dict 대신
"재무제표를 읽지 못해 본문 금액을 대조할 수 없습니다" 가 올라오고, 기간 불일치도 별도
사유로 구분된다. 흡수 목록 밖 I/O 실패는 그대로 전파돼 소비자가 실패로 본다. 정상 경로는
그대로 계정 금액(10억)을 돌려주고 연간 표기의 Q4 해소도 유지된다. 매핑은
`"매출액"`·`"매출"`·`"영업이익"`·`"매출 액"` 네 표기에서 `korToSnakeId` 와
`lookup.snakeId` 가 모두 일치했고, 공백이 낀 `"매출 액"` 은 수정 전 `None` 이었다.

Guard와 회귀는 통과했다. 신규 bridge 회귀 `5 passed`, 매핑 호출자 회귀 `45 passed`,
변경 2개 소스 Ruff·formatter·Pyright `0 errors, 0 warnings`,
`bridge.py` `silentSubstitute --strict` 위반 0(기존 baseline 항목이 실제로 해소됐다).

남은 부채는 다음 순서로 넘긴다. `bridge.py` 모듈 docstring 의 snake_case 예제 심볼
(`extract_amounts_from_text` 등)은 실재 심볼과 달라 복사하면 ImportError 이고,
`_parseNumber` 가 float 반환 계약에서 파싱 실패에 `0` 을 돌려주는 것(현재 소비자가
`tv == 0` 을 건너뛰어 무해)도 문서·계약 정리 항목이다. capability builder 가 import 실패한
axis registry 를 진단 없이 빠뜨리는 것은 baseline 에 있는 기존 부채다.
이로써 L1.5 네 형제(scan·frame·synth·reference) 체크포인트를 모두 닫았다.

## L1.5 scan, frame, synth, reference 전체 마감 (2026-07-31)

**상태: 완료.** 위 체크포인트(scan 의미 계약·재무 one-pass·EDGAR 계정 batch·공통 I/O·
network·US coverage audit·EDGAR prebuild·universe·dispatcher·KR report 판정 정직성,
그리고 frame·synth·reference)의 증거를 합쳐 L1.5 를 하나의 레이어로 닫는다. 파일이나
axis 하나는 이 판정의 증거일 뿐 별도 완료 단위가 아니다.

1. **범위와 실제 호출자.** 네 형제의 전체 src 와 실제 호출자를 대조했다. scan 은 공개
   27 축 facade 와 KR/US dispatch, prebuild 소유자까지, frame 은 자연어 종목 해소와
   보고서 인벤토리 및 그 소비자 `simulate.profile`, synth 는 event study 와 위험
   프리미엄을 쓰는 `analysis.eventStudy`·`analysis.financial._proformaCore`,
   reference 는 문서-재무 대조 bridge 와 그 소비자 server analysis API, 매핑 SSOT 와
   그 호출자다.
2. **제품 결함 재현.** 계층을 관통하는 한 가지 결함이 반복됐다. 모르는 것을 그럴듯한
   값으로 바꿔 내보내는 것이다. audit 은 감사의견 결측 23 종목에 "관찰" 판정을 줬고,
   debt 은 ICR 결측에 신호가 없어도 "관찰" 을 줬다. frame 은 검증 없이 대문자 토큰을
   회사로 확정해 `"ROE 계산법"` 을 종목 질의로 바꾸고 `"SK 하이닉스"` 를 `SK` 로 잡았다.
   synth 는 추정 불가 구간에서 `sigma=0.01` 을 지어내 유의성 판정을 만들고, 장부가를
   분모로 쓴 implied ERP 12.0% 를 캐시에 남겨 WACC 로 흘려보냈다. reference 는 재무를
   한 장도 못 읽어도 빈 dict 를 돌려줘 API 가 `matchRate: 0.0` 이라는 경보성 결론을
   서빙했다. US audit 축은 형제 축과 다른 identity(CIK vs ticker)와 universe(전 17,367
   parquet vs 상장 5,662)를 썼고, scan facade 는 발행된 `universe` 계약을 미구현해
   내부 함수명이 드러난 raw TypeError 를 냈다.
3. **근본 원인과 SSOT.** 판정 가능 여부를 가르지 않고 합성 점수를 격자에 밀어 넣은 것,
   실재 확인 없이 식별자를 주장한 것, 실패와 0 을 같은 모양으로 반환한 것이 뿌리다.
   축별 판정은 형제 축의 정직 gap 라벨("자료부족"·"미확인")로, US 종목 정체성은 상장
   ticker SSOT 로, 유니버스 선택은 facade 의 entity-set 계약으로, 계정 매칭은
   `AccountNormalizer` 한 곳으로 소유를 고정했다.
4. **수정과 테스트.** 여섯 체크포인트에서 9 개 소스를 고쳤고 신규 회귀 60 건을 세웠다
   (universe 26 · dispatcher 3 · KR report 11 · frame 10 · synth 7 · reference 5).
   audit 회귀는 등급 규칙을 테스트에 복제하지 않고 합성 source 로 실제 `scanAudit` 을
   호출한다. implied ERP 는 L0-03 비정규 모델 비발행 계약과 같은 규칙으로 잘못된 계산
   경로와 전용 헬퍼를 제거해 347 줄에서 101 줄로 줄였다.
5. **공개 행동, 정확성, 속도, 메모리.** 실데이터 전종목 호출로 확정했다. report 6 축은
   governance 2,872 · workforce 2,781 · capital 2,942 · debt 2,832 · audit 2,932 ·
   insider 2,608 행을 낸다. audit 은 "관찰" 955 에서 930, debt 은 369 에서 359 로 줄고
   각각 "자료부족" 26 과 10 이 생겼으며, 26 은 의견 결측 23 과 각주 마커 3 의 합과 정확히
   일치한다. debt ICR 결측 63 의 최종 내역은 자료 전무 null 44 · 판정 불가 10 · 관측된
   단기채무로 정당하게 상향된 "주의" 9 다. profitability 전종목은 2,811 행 1.8737 초,
   RSS 증가 199.0MB 이고 `universe={"stockCodes": [...]}` 는 정확히 2 행을 값 보존한 채
   돌려준다. US audit 대상은 17,367 에서 상장 5,662 로 좁아져 앞선 US coverage
   체크포인트의 unique source 5,662 와 일치한다. frame 은 `"SK 하이닉스 실적"` 을
   `000660` + `"실적"`, `"LG 화학 주가"` 를 `051910` + `"주가"` 로 해소하고 재무 약어
   다섯은 모두 회사 확정을 포기한다. synth 는 추정 불가 구간에서 error 만 내고 추정
   가능 구간은 `sigma=0.0199` 같은 실제 추정치를 유지하며, KR ERP 는 12.0 에서 큐레이션
   5.2 로 내려와 WACC 의 6.8%p 상방 편향이 사라졌다. 축 실행 시간(debt 6.48 초,
   audit 6.21 초)과 메모리는 수정 전후 변화가 없다.
6. **Guard와 회귀.** 네 형제 단위 회귀 `574 passed`. L1.5 cross import 는 정적·동적 모두
   0 이고(`test_l15_no_cross_import` 2 passed), 남은 문자열 매칭은 docstring 참조와
   `importlib.resources` 데이터 파일 접근뿐이다. `l15DynamicImport` 부채 원장의 마지막
   항목이던 `impliedERP -> scan.io.parquet` 은 이번 비발행 정리로 사라져 원장을 0 으로
   갱신했다. source 동결 뒤 공식 Guard
   `strict --scope l0-l15 --providers dart,edgar` 는 1,786 파일에서 **AST 룰 위반 0,
   baseline 대비 신규 위반 0, stale 0** 이고 외부 게이트 cycleScan · architecturePytest ·
   folderMirror · gatherGate · publicApiSmoke 가 통과했다. **다만 전체 status 는 fail 이다.**
   원인은 providerGate 의 룰 3(LoC)·룰 6(docstring) 기존 부채 하나뿐이며, 이는
   `providers/` 소유(`company.py`·`dataDispatcher.py`·`scanAccount.py`)로 직전 EDGAR
   prebuild 체크포인트가 이미 같은 내용으로 기록했다. 이번 세션의 diff 는 `providers/`
   파일을 한 개도 건드리지 않았다(변경 20 파일 전수 확인).
7. **남은 부채와 판정.** L1.5 공개 데이터 흐름에서 재현된 P0/P1 결함과 침묵 실패는 0 이다.
   남는 것은 각 체크포인트에 기록한 후속 항목이다. `"AI 반도체"` 는 `AI` 가 실재 상장
   ticker 라 남는 문서화된 모호성이고, `_statementUnits` 의 재무 5 표 상존 주장은 실데이터
   두 회사에서 반증하지 못해 미검증으로 남긴다. implied ERP 재활성화에는 유니버스
   시가총액 SSOT 가 필요하고, `damodaranL15._assumptions` 의 매직 상수군은 production
   호출자 0 이라 별도 항목이다. `report/fields.py` 1,369 줄 분할, US/KR audit·valuation
   축의 반환 스키마 통일, `bridge.py` docstring 심볼 드리프트도 남는다. providerGate 의
   `providers/` 크기·docstring 부채는 소유 레이어인 L1 이 이미 기록한 항목이라 이 판정을
   막지 않는다. 따라서 **L1.5 scan/frame/synth/reference 를 완료 판정하고 L2
   analysis/macro/quant/industry/credit 로 이동한다.**

### L1 재개방 체크포인트: EDGAR scanAccount 분할 (2026-07-31)

범위는 `providers/edgar/finance/scanAccount.py` 1,272 LoC 단일 모듈과 실제 호출자
(`scan/router.py` 의 US account·ratio dispatch, `scan/builders/edgar/helpers.py` 의
batch 계정 수집)다. L1.5 마감 뒤 CI 를 끝까지 확인하는 과정에서 드러났고, 소유가
L1 providers 라 원장의 재개방 패턴(L1 panel 체크포인트와 같은 방식)으로 닫는다.

제품 결함은 구조 규칙 위반이고 게이트 두 곳이 동시에 막혀 있었다. folderSize 룰 3 의
임계는 800 LoC 인데 이 파일은 1,272 였고 baseline 에도 없었다. LoC 변천을 실측하니
`1537cea4f` 780 -> `bb7f06aa8` 1,272 로, 직전 세션의 EDGAR 계정 batch 작업이 임계를
넘기며 분할도 baseline 갱신도 하지 않은 회귀였다. 이 하나가 lint 게이트의 folderSize
와 architecture-l0-l15 의 providerGate 룰 3 을 함께 실패시켜, CI 가 오래 빨간 마지막
이유였다. baseline 등재로 통과시키는 길은 택하지 않았다. 레포 규약이 baseline 을
줄어드는 방향으로만 갱신하기 때문이고, 회귀를 부채로 세탁하는 것이기 때문이다.

근본 원인은 한 모듈이 SQL, 오류 계약, 이름 해소, 실행, 공개 호출 다섯 책임을 함께
들고 있었다는 것이다. 감사가 지시한 대로 책임별 소유자를 갈랐다.

수정은 코드를 바꾸지 않고 옮기는 분할이다. `scanAccount/` 패키지로 `sql`(274) ·
`types`(73) · `taxonomy`(154+) · `pipeline`(483) · `api`(365) 를 두고 `__init__` 은
공개 계약(`scanAccount`·`scanAccounts`·`scanRatio` + 오류 4종)만 재수출하는 thin
모듈로 뒀다. 모듈 경로 `dartlab.providers.edgar.finance.scanAccount` 는 그대로라
호출자와 monkeypatch 경로가 깨지지 않는다. 다만 내부 심볼을 패키지 루트에서 patch
하던 기존 테스트는 소유 모듈(`api`)을 가리키게 고쳤다. 재수출로 import 만 통과시키면
patch 가 실제로는 먹지 않아 거짓 통과가 되기 때문이다. 룰 7 이 요구하는 미러 5개를
baseline 갱신이 아니라 실제 테스트로 채웠다(신규 33 건). 분할로 경로가 바뀌며 baseline
키가 어긋난 `prioritized()` 는 경로만 옮기지 않고 4 섹션 docstring 을 실제로 채웠다.

공개 행동 동등성은 분할 전 실측을 baseline 으로 잡아 대조했다. 공개 3 함수의 시그니처가
문자열 단위로 같고, 오류 4 종의 MRO 가 같다. 옮긴 순수 함수도 같은 출력을 낸다:
`_buildEdgarTagKeys("sales")` 의 usGaap 109 개 · ifrsFull 6 개 · common 5 개가 분할 전과
일치하고 tagKeys digest 는 `a887d7d38f483b44` 다. 패키지 top-level 노출은 42 개에서
13 개(공개 7 + 서브모듈 5 + annotations)로 좁아졌는데, 줄어든 29 개는 전부 소유 모듈로
옮겨간 private 이다.

Guard와 회귀는 전부 통과했다. 신규 미러 `33 passed`, 기존 scanAccount 회귀와 scan
helper `20 passed`(분할 전과 같은 수), EDGAR·scan 집중 회귀 `858 passed`. 변경 패키지
Pyright `0 errors, 0 warnings`, Ruff·formatter 통과, folderSize 는 baseline 안 통과로
under_split 48 -> 47, stale_references 잔존 0, silentSubstitute 신규 0 이다.
**providerGate 는 11/11 로 처음 전부 통과했고, 공식 Guard
`strict --scope l0-l15 --providers dart,edgar` 가 `status: pass`(7/7 규칙, 외부 게이트
cycleScan·architecturePytest·folderMirror·gatherGate·providerGate·publicApiSmoke 6/6)
로 돌아섰다.** 이 세션에서 Guard 가 pass 로 찍힌 것은 처음이다.

남은 부채는 다음과 같다. folderSize 의 over_split 20 · under_split 47 은 baseline 안의
기존 부채로 이번 분할이 늘리지 않았다. Guard known debt 47 건(active 9 + 보호된 Company
facade 38)도 그대로다. `api.py` 365 LoC 와 `pipeline.py` 483 LoC 는 임계 800 아래라
추가 분할 대상이 아니다.

### cycle 부채 원장 재측정 (2026-07-31)

lint 게이트가 `providers <-> scan` 2-cycle 을 baseline 밖 신규로 차단했다. 전문 검토
둘을 서로 다른 렌즈(설계 실현성 / 적대적 반증)로 독립 수행하고 직접 재검증했다.
결론은 갈리지 않았다. **이것은 코드 회귀가 아니라 미완 커밋이다.**

근거는 계측기 대조다. `providers/` 에는 정적 `from dartlab.scan` 이 0 건이고 상향 간선
10 개가 전부 `importlib.import_module("literal")` 동적 호출이다. `d8909662d` 이전의
cycleScan 추출기는 `ast.Import` 와 `ast.ImportFrom` 두 종류만 처리했으므로 이 간선을
볼 수 없었다. 그 커밋이 추출기를 Guard indexer 로 교체하며 리터럴 동적 import 를
해석하기 시작했고, 같은 커밋에서 `cycleScan.json` 은 재측정하지 않았다. baseline 의
`measuredAt` 은 2026-07-26 으로 검출기 교체 이전이다. 옛 추출기를 현재 트리에 다시
돌리면 정확히 기존 10 항목이 나온다. 델타 전부가 계측기 변경이다. 같은 파일의 유일한
선례 `238d294ae` 도 패키지 탐색을 넓히면서 같은 커밋에서 원장을 5 에서 10 으로
재측정했다. "검출 해상도가 바뀌면 같은 커밋에서 원장을 재측정한다" 가 이 파일의 규약이다.

의존 역전(composition registry)은 기각했다. 첫째, 게이트를 고치지 못한다. 상향 간선은
`scanAggregator.py` 5 건이 아니라 4 개 파일 10 건이고, `dart/company.py`(2),
`edgar/company.py`(1), `dart/finance/scanAccount.py`(2) 가 남으면 간선이 그대로다.
게다가 `_SCAN_AXES` 는 `ast.Dict` 라 indexer 가 아예 보지 못해, 그 4 축을 걷어내도
게이트 결과는 변하지 않는다. 역으로 리터럴을 dict 뒤로 숨기면 통과하는데 그건 import
우회다. 둘째, 남은 3 파일은 `dartlabGuard.json` 의 `protectedCompanyFacadeDebt` 이고
그 `_note` 가 "사용자 호출 표면을 보존하려고 남긴 것이라 정리 대상이 아니고 신규
증가만 차단한다" 고 명시한다. scan 만 골라 역전시키는 것은 기록된 운영자 결정을 재논의
없이 뒤집는 일이다. 셋째, 대상 5 개 공개 Company 메서드는 경로 전체가 None 관용이라
seam 오배선이 전 종목 무데이터로 조용히 degrade 한다. 실제로 같은 파일에서 그 사고가
한 번 있었고 post-mortem 주석이 남아 있다. `productSmoke` 와 `publicApiCoverage` 에
governance/network/workforce/capital/debt 언급이 0 건이라 실데이터로 잡을 그물도 없다.

조치는 손수 편집이 아니라 `cycleScan.py --update-baseline` 재측정이다. 손수 한 줄을
끼워 넣으면 `longerCycleCount` 가 어떤 계측기도 낸 적 없는 값으로 남아 그것이 진짜
staleness 가 된다. 재측정 결과는 2-cycle 10 -> 11, longer 737 -> 1251,
`measuredAt` 2026-07-31 이다. `--strict-toplevel` 기준 top-level cycle 은 여전히 0 이라
런타임 import cycle 은 없다. per-file 상향 회귀는 `architecture.lazyUpperImport` 가
계속 막는다.

남은 부채. `Company` facade 가 L1 에 주차된 채 상위 11 개(analysis·ai·credit·frame·
industry·macro·quant·scan·simulate·story·synth)를 lazy 로 끄는 것이 병이고 scan 은
증상이다. 별도 프로젝트로 올린다. 그 앞 1 단계 후보는 `scan/io/` 1,974 LoC 가
`scan/io/parquet.py:133` 의 `SCAN_API_TYPES` 한 줄만 위를 보는 구조라, 그 선언을 io 로
내리면 `scan/io/` 가 providers 와 scan 이 아래로 읽는 artifact 계층이 되고 10 건 중
3 건이 계층 정정만으로 사라진다는 것이다. 이것만으로 cycle 은 끊기지 않으므로 해결책이
아니라 순서상 1 단계로 기록한다. `scanAggregator.py:238` 이 `scan.io.parquet.loadListing`
을 거쳐 다시 `providers.dart.company.Company.listing()` 으로 되돌아오는 4-hop 왕복도
같은 계층 호출로 바꿀 위생 항목이다. 규약 보완으로 "검출기 해상도 변경 시 같은 커밋에서
원장 재측정" 을 명문화할 자리도 남긴다.

## L2 진입 (2026-07-31)

L1.5 네 형제를 닫았으므로 하단 우선 순서에 따라 L2 로 올라간다. 첫 항목은 L1.5 US
coverage audit 체크포인트가 성능 차단으로 상위 owner 에 넘긴 `analysis/financial/edgarPitState`
다. 그때 "하위 순서를 깨고 지금 상위 compiler 를 수정하지 않는다" 로 미뤄둔 바로 그 항목이다.

### L2 체크포인트: EDGAR full-state 컴파일 성능 (2026-07-31)

범위는 `analysis/financial/edgarPitState.py` 와 실제 호출자다. 위로는
`analysis/financial/filingFeatures.py` 의 세 feature 어댑터와 그 진입점
`analysis/financial/dataAssets.edgarFinancialFeatures`, 옆으로는 `simulate/edgarPitState.py`
호환 shim 과 `simulate/filingStateAdapters.py` 가 붙어 있다. 공개 계약 표면은 컴파일러
네 개(`compileEdgarFinancialState`, `compileEdgarQuarterlyFinancialState`,
`compileEdgarQuarterlyFlowState`, `compileEdgarQuarterlyRevenueState`)다.

제품 결함은 게이트가 아니라 실호출로 재현했다. 상장 universe 앞 288 사에 full-state
strict 를 실제로 걸어 263.4 초, 회사당 평균 914.6ms 였다. 전수 외삽은 86 분으로 15 분
운영 한도의 5.7 배다. 최악 반례 MTB(CIK 0000036270)는 19,408ms 였고, 더 중요한 것은
가장 느린 15 사 중 14 사가 그 시간을 다 쓰고 결국 `EdgarStateError` 로 끝났다는 점이다.
MTB 를 cProfile 로 갈라 보니 2.149 초 중 `_stockCandidates` 가 1.533 초(71%)였고
`PyLazyFrame.collect` 6,769 회가 tottime 1.014 초(47%)였다. Polars `filter` 는 4,232 회,
`_pick` 은 2,790 회, stock 후보는 140 개였다.

근본 원인은 후보가 140 개인 것이 아니라 후보마다 Polars 에 다시 들어가는 것이다.
`_pick` 이 태그 하나당 `group.filter(pl.col("tag") == tag)` 를 불러 후보 수와 태그 수의
곱만큼 lazy plan 을 새로 만들었다. 대상 group 은 접수 하나의 대차 행이라 수십 줄이고,
따라서 비용은 데이터가 아니라 Polars 호출 고정비가 전부였다. 결정적인 것은 같은 파일의
흐름 경로가 이미 올바른 규약을 쓰고 있었다는 점이다. `_quarterEvidence` 는 `filter` 한 번
뒤 `iter_rows` 로 파이썬 dict 버킷을 만들고, 기존 회귀
`testQuarterEvidenceUsesOneIndexedPolarsFilterPass` 가 "기간과 태그마다 Polars plan 을
다시 만들지 않아야 한다" 를 못 박아 두었다. stock 경로만 그 불변식을 채택하지 않았다.
새 규칙을 세우는 것이 아니라 이미 있는 불변식을 미채택 경로로 넓히는 일이라 SSOT 가
하나로 닫힌다. 두 번째 원인은 그 위층에 있었다. 후보는 접수 단위인데 고유 회계 기간말은
140 개 중 37 개뿐이고, `flowCompiler` 는 `(pit, fiscalThrough)` 의 순수 함수라서 같은
기간말에 같은 결과와 같은 오류를 되풀이 계산하고 있었다.

수정은 두 자리다. `_indexStockRows` 가 stock 프레임을 한 번 순회해
`(fiscalEnd, accession, filedAt)` 별 태그 색인을 만들고, `_pick` 은 dict 조회로 바뀌었다.
단위 충돌과 값 충돌 검증은 그대로 두었다. 색인 한 칸은 `__filed` 가 같은 접수 하나라
기존의 `sort("__filed", descending=True).row(0)` 은 첫 행 선택과 같다.
`_compileStockWithFlow` 는 기간말별로 흐름 컴파일 결과를 성공이든 `EdgarStateError` 든
한 번만 계산해 재사용한다. 오류 우선순위는 후보 순서를 그대로 따르므로 `firstFlowError`
의미가 바뀌지 않는다. 회귀 3 건을 신설했다.
`testStockCandidateWalkDoesNotReenterPolarsPerCandidate` 는 후보 수가 늘어도 Polars 진입이
1 회인지 보고, `testFlowCompilerRunsOncePerFiscalEndNotPerAccession` 은 같은 기간말을
공유하는 접수 4 개에서 흐름 컴파일이 1 회인지 본다.
`testManyStockCandidatesStillSelectTheFilingThatHasFlow` 는 색인 경로도 흐름 있는 접수를
그대로 고르고 값을 바꾸지 않는지 본다. 앞의 두 가드는 수정 전 코드에 같은 fixture 로
걸어 실제로 깨지는 것을 확인했다. 후보 5 개와 41 개에서 filter 가 91 회와 739 회로
후보에 비례했고, 흐름 컴파일은 4 회였다. 통과만 하는 테스트를 가드로 세지 않는다.

공개 행동 동등성은 실데이터로 증명했다. 수정 전 모듈을 git 에서 꺼내 같은 회사 facts 에
돌리고 공개 컴파일러 네 개의 `stateHash` 와 오류 문자열을 전부 대조했다. 400 사 x 4
컴파일러 = 1,548 건 비교에서 불일치 0 건이고, stock 수정만 넣은 1 차와 두 수정을 합친
2 차 모두 0 건이다. 같은 표본의 소요는 1 차 609.0 초 -> 179.5 초, 2 차 447.7 초 ->
107.7 초로 4.16 배다. 그리고 L1.5 가 한도 초과로 중단했던 그 실행을 완주시켰다. 감사
하네스 `edgarCoverageAudit` full-state strict 전수는 7,683 ticker / 6,069 unique CIK 에서
**238.578 초**로 끝났다. 15 분 한도의 27% 다. 성공 2,420 건(31.4981%)으로 full audit
하한 30% 를 넘겼고, unique source 5,662/6,069(93.2938%) missing 407 로 하한 90% 를
넘겼다. p50 46.530ms, p95 715.439ms, max 1,832.702ms 다. loader 0, network 0, listing
digest 는 시작과 끝이 같고, `entityRefIdentityMatches` 는 true 다. `passedSafetyGate` 는
true, `coverageGate.failures` 는 빈 목록이다. source coverage 5,662/6,069 와 missing 407
은 L1.5 가 flow-only 와 revenue-only 에서 기록한 값과 정확히 같아, universe 와 원천이
그대로임을 교차 확인해 준다.

Guard 와 회귀는 통과했다. 대상 회귀 `54 passed`(계약 21 + simulate 9 + filingFeatures 13 +
attempts flow prototype 3 + filingStateAdapters 8), `tests/analysis` unit `649 passed`,
Guard `quick` `status: pass`(7 규칙, 외부 게이트 architecturePytest PASS, known debt 47 건
불변). folderSize 는 baseline 안 통과로 over_split 20 / under_split 47 그대로,
silentSubstitute 신규 0, Ruff 와 formatter 통과다.

남은 부채는 넷이다. 첫째, `edgarPitState.py` 가 1,458 -> 1,533 LoC 로 늘었다. libSize
baseline 등재분이라 게이트는 통과하지만 임계 800 을 넘는 부채는 그대로이고 증가분은
9 섹션 docstring 이다. scanAccount 와 같은 책임별 분할 후보로 남긴다. 둘째, 같은 파일
Pyright 4 건(840, 896, 903 의 `_q4From*` 에서 `fiscalStart` 가 `str | None` 로 좁혀지지
않는 것)은 이번에 만지지 않은 줄의 선재 부채다. 런타임은 호출 전에 `None` 을 걸러내고
`typecheck` 게이트는 `blocking=False` 라, 비차단 린터를 만족시키려고 assert 를 얹는 것은
게이트 수리이지 제품 진보가 아니라고 판단해 손대지 않았다. 셋째,
`tests/_attempts/dataWorkbenchEdgarScale/testAudit.py` 가 `dartlab.dataHub.ownerPaging` 을
import 하는데 그 모듈은 `dataHub/paging/owner` 로 재편돼 collection 단계에서 죽는다.
CI 는 `_attempts` 를 수집하지 않아 green 이지만 죽은 하네스다. 넷째, full-state 성공률
31.4981% 는 하한 30% 바로 위라 여유가 얇다. 최대 실패군은
`FEATURE_NO_COHERENT_FOUR_QUARTER_WINDOW` 2,024 건과 `PIT_NO_FILING_BEFORE_CUTOFF`
1,456 건인데 이는 성능이 아니라 커버리지 항목이라 이 체크포인트의 판정 밖이다.

푸시 전 `tests/run.py preflight`(fast blocking 14 게이트) 전수에서 `lint` 와
`test-coverage-gate` 두 건이 걸렸고 둘 다 닫았다. `lint` 는 `workspaceHygiene` 이
`blog/09-investment-stories` 아래 빈 미디어 staging 디렉터리 두 개를 잡은 것이다.
gitignore 대상이라 CI 는 보지 못하는 로컬 잔재였고, 안에 파일이 0 개인 것을 확인한 뒤
빈 디렉터리에만 동작하는 `rmdir` 로 지웠다. `test-coverage-gate` 는 이 파일의 중첩
클로저 `priorQuarter` 두 개를 테스트 없는 공개 함수로 잡은 것이다. 이 모듈의 형제
헬퍼가 전부 언더스코어 접두인데 이 둘만 빠져 있었으므로 `_priorQuarter` 로 고쳤다.
호출부는 같은 함수 안 두 곳뿐이고 모듈 밖 참조는 0 건이다.

그 과정에서 게이트 결함을 하나 실측했다. `testCoverageGate._extractPublicFunctions` 의
docstring 은 "top-level + class-level public def 목록" 이라고 명시하는데 구현은
`ast.walk` 라 중첩 함수까지 센다. src/dartlab 전역에서 두 방식의 차이는 63 개 파일
125 개이고, 표본은 `eagerSandbox.denyWriter`, `httpApi.authorize`,
`transports.lifespan`, `setup.do_GET`, 채널 어댑터의 `onMessage` 처럼 전부 밖에서
import 할 수 없는 내부 콜백이다. 구현을 docstring 계약에 맞추는 것이 옳지만, 차단
게이트의 검출 표면을 무관한 체크포인트 안에서 125 건 줄이는 것은 정당해도 세탁과 같은
모양이라 여기서 하지 않는다. 별건 항목으로 남긴다.

**판정: L2 EDGAR full-state 컴파일 성능 체크포인트 완료.** L1.5 가 상위로 넘긴 성능
차단이 풀렸고, 전수 감사가 처음으로 한도 안에서 완주해 fail-closed 게이트를 통과했다.
다음 체크포인트는 L2 의 "남은 것" 목록 맨 앞인 팩터 형성 시점 look-ahead 다. 수익률
구간이 정렬 정보보다 앞서는 문제라 발표된 모든 팩터 수치의 의미를 바꾸고, 같은 목록의
스타일 전구간 분위수와 함께 별도 설계가 필요하다고 이미 기록돼 있다.

### L2 체크포인트: 팩터 형성 시점 look-ahead (2026-08-01)

범위는 `quant/factor/build.py` 의 `buildFactors` 와 그 소비자다. 소비자는 같은 패키지의
`calc.decomposeFactor`(종목 FF5 loadings), `_calcTearsheet.calcFactorTearSheet` 와
`calcFactorTearSheetAll`, `calcMultiFactorRisk` 세 곳이고 story 6막-3 시장분석 섹션이
`factorTearSheetBlock` 으로 자동 호출한다. 시점 계약을 검사하는 테스트는 착수 시점에
0 건이었다. `tests/quant/test_grinoldAbsorption.py` 가 유일하게 이름이 걸리는 파일인데
실제로는 상관계수와 IR 같은 순수 수학 헬퍼만 본다.

제품 결함은 코드 직독과 실데이터 양쪽에서 확인했다. `buildFactors` 는
`_latestYear` 로 얻은 Y 년 재무로 `_buildUniverseMetrics(market, Y)` 를 부르고, 그
안에서 `_fetchYearEndMarketcaps(market, Y)` 가 Y 년 12 월 25 일부터 31 일 사이의 시총을
읽는다. 그 두 값으로 5분위를 가른 뒤 `_portfolioReturns` 가
`loadFiltered(start=f"{Y}-01-01", end=f"{Y}-12-31")` 로 Y 년 1 월부터의 수익률을
붙인다. 정렬 정보는 Y 년 12 월 말 시점이고 재무는 Y+1 년 3 월경에야 공시되는데, 그
정보로 가른 포트폴리오에 12 개월 앞선 수익률을 귀속시킨 것이다. KR 실데이터에서
`_latestYear` 는 2025 였고 현행 산출은 SMB 연환산 -63.82%(Sharpe -1.943),
HML +97.45%(2.827), RMW +34.54%(1.254), CMA -32.77%(-1.160) 였다. SMB 의 -63.82% 는
전형적인 인공물이다. 연말 시총으로 소형 분위를 가르면 그 해에 하락한 종목이 소형에
담기므로, 결과로 정렬해 놓고 그 결과를 프리미엄이라 부르게 된다.

근본 원인은 규약 부재가 아니라 미채택이다. 같은 패키지의 `_factorIC.calcFactorIC` 는
`fund_year = Y-1`, 수익률 `{Y}-04-01` 부터 `{Y}-12-31` 을 쓰고 "전년 12 월말 데이터는
당해년도 Q1 이후 공시되므로 실전 예측 가능" 이라는 주석까지 달아 두었다. 두 함수가 같은
패키지에서 정반대로 동작했고 `build` 쪽만 그 규약을 따르지 않았다. 직전 체크포인트의
edgarPitState 와 구조가 같다. 새 규칙을 세우는 것이 아니라 이미 문서화된 규약을 미채택
경로로 넓히는 일이라 SSOT 가 하나로 닫힌다.

수정은 세 자리다. 모듈 상수 `_RETURN_WINDOW_START = "04-01"` 과
`_RETURN_WINDOW_END = "12-31"` 로 형성 규약을 한 자리에 못 박고 근거를 주석으로 남겼다.
`_portfolioReturns` 의 가격 조회 구간을 연초가 아니라 그 상수로 바꿨다. `buildFactors` 는
`fundYear = Y-1` 로 5분위를 가르고 `retYear = Y` 로 수익률을 붙인다. 시총은
`_buildUniverseMetrics(market, fundYear)` 를 타고 자동으로 Y-1 년 말이 되므로 형성
시점에 이미 알려진 값이다. 결과 dict 에는 `fundYear`, `retYear`, `returnWindow` 를
추가해 소비자가 시점 계약을 눈으로 확인할 수 있게 했고 `notes` 에도 실었다. 소비자가
읽는 `year` 는 팩터 시계열이 덮는 연도라는 뜻이 유지되도록 `retYear` 를 넣었다.

회귀는 `tests/quant/factor/test_factorFormationTiming.py` 3 건을 신설했다. 첫째는
`buildFactors` 가 펀더멘털을 Y-1 로, 수익률을 Y 로 요청하는지 실제 배선에서 본다.
둘째는 `_portfolioReturns` 가 가격을 `2025-04-01` 부터 요청하고 `2025-01-01` 이
아닌지 본다. 셋째는 형성 규약이 형제 IC 경로와 어긋나지 않는지 본다. 세 가드를
수정 전 코드에 같은 fixture 로 걸어 실제로 깨지는 것을 확인했다. 수정 전은 펀더멘털을
2025 로 요청했고 `fundYear` 와 `returnWindow` 필드가 아예 없었다.

공개 행동 변화는 실데이터로 측정했다. 같은 KR universe 에서 수정 전후는 다음과 같다.

| 팩터 | 수정 전 연환산 | 수정 전 Sharpe | 수정 후 연환산 | 수정 후 Sharpe |
|---|---|---|---|---|
| SMB | -63.82% | -1.943 | -19.24% | -0.748 |
| HML | +97.45% | 2.827 | +16.78% | 0.902 |
| RMW | +34.54% | 1.254 | -7.76% | -0.487 |
| CMA | -32.77% | -1.160 | +14.92% | 0.571 |

RMW 와 CMA 는 부호가 뒤집히고 HML 은 80.7%p 내려간다. Sharpe 절대값은 1.2~2.8 대에서
0.5~0.9 대로 내려앉는다. 발표되던 FF5 프리미엄이 상당 부분 look-ahead 인공물이었다는
뜻이다. 수정 후 산출은 `fundYear=2024`, `retYear=2025`,
`returnWindow=2025-04-01~2025-12-31`, universe 1966, n_obs 138,
`sizeSource=KRX_MKTCAP`, `isRealFamaFrench=true` 다. n_obs 가 240 대에서 138 로 줄어든
것은 구간을 9 개월로 좁힌 결과라 의도한 변화다.

Guard 와 회귀는 통과했다. 신규 3 건 포함 `tests/quant` unit `235 passed`, 변경 모듈
Ruff 와 formatter 통과다.

남은 부채는 넷이다. 첫째, 시총이 형성 시점(4 월) 값이 아니라 Y-1 년 말 값이다. Fama-French
원전은 size 에 6 월말 ME 를 쓰므로, 형성일 시총으로 올리는 것이 더 정확하다. 형성 시점에
알려진 값이라 look-ahead 는 아니고 정밀도 항목이다. 둘째, 단년도 한 창만 만들기 때문에
다년 패널이 없고 n_obs 138 로 통계적 신뢰구간이 넓다. 셋째, `_FACTOR_CACHE` 키가
`(market, "latest")` 라 연도를 담지 않아 원천이 갱신돼도 같은 프로세스 안에서는 옛 결과가
남는다. 선재 항목이다. 넷째, 측정 중 `loadData(2024, govPrices)` 가 8,039MB 를 잡아
2,000MB 한도를 크게 넘긴 것을 관측했다. 소유가 L1 gather 라 이 체크포인트 밖이다.

**판정: L2 팩터 형성 시점 look-ahead 체크포인트 완료.** L2 "남은 것" 목록에서 이 항목과
"발표된 모든 수치의 의미를 바꾼다" 는 단서를 지운다. 남은 것은 백테스트 샤프의 비용
미반영, 과적합 확률 상수 1.0, Sortino 하방편차 정의, 스타일 규칙의 전구간 분위수,
CPCV 이음매 수익률, 실패 fold 를 샤프 0 으로 세는 것, Altman 자동 모드 모델 혼용,
Beneish 결측 다수 기본값, Track B 유동성 가중 0, 감사의견 키워드 부재 추정이다.
다음 체크포인트는 백테스트 샤프의 비용 미반영이다. 엔진이 스스로 물린다고 밝힌 비용을
성과에 반영하지 않는 문제라 같은 "측정 계층을 믿을 수 없다" 계열의 뿌리다.
