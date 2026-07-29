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

각 계층은 다음 일곱 칸을 순서대로 닫는다.

1. 현재 범위와 실제 호출자
2. 제품 행동에서 재현된 결함
3. 결함의 근본 원인과 단일 SSOT
4. 테스트와 함께 적용한 수정
5. 실제 공개 행동, 정확성, 속도, 메모리 실측
6. Guard Index와 회귀 결과
7. 남은 부채와 완료 또는 미달 판정

발견만 했거나 게이트만 통과한 상태는 완료가 아니다. 일곱 칸의 증거를 이 원장에 기록한
뒤에만 다음 계층으로 이동한다. 세션 종료 시 현재 계층, 마지막 완료 항목, 진행 중인 단일
항목, 다음 첫 행동을 아래 세션 인계 칸에 갱신한다.

### 세션 인계

- 현재 계층: L0 core
- 마지막 완료 항목: L0-07 동적 상향 import 감시와 composition 경계
- 진행 중인 단일 항목: L0-08 `core/_entries` residency와 registry 호출자 경계
- 다음 첫 행동: `core/_entries`의 모든 생성자와 소비자를 정적·제품 호출로 대조하고,
  L0 metadata primitive와 L4 Company/API entry를 분리할 수 있는 최소 소유 경계를 재현한다.
- 금지: L0 완료 판정 전 L1 이상 감사나 수정 착수

## L0 순차 안정화 원장 (2026-07-29)

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
| L0 core | 순차 안정화 진행 중. 미달 |
| L1 gather, providers | L0 완료 전 재검토 대기 (과거 판정 미달) |
| L1.5 scan, frame, synth, reference | L0 완료 전 재검토 대기 (과거 판정 미달) |
| L2 analysis, macro, quant, industry, credit | L0 완료 전 재검토 대기 (과거 판정 미달) |
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

`core/schemas.py` 의 Pandera 클래스 47 개(약 700 줄)가 호출자 0 이지만, 삭제하지 않기로
한 기존 결정이 `mainPlan/innovation-stack-research/tech/pandera.md` 에 있다.

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

