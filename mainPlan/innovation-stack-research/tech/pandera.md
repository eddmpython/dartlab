# Pandera 조사 원장

- **무엇**: DataFrame 스키마 검사기. pydantic 이 dict/JSON 을 검증하듯 Pandera 는 polars/pandas 표의 컬럼 이름·존재·타입·값 제약을 선언적으로 검증하고, 어긋나면 SchemaError 를 낸다.
- **우리 현재 사용**: 예, 단 dev 전용. pin `pandera[polars]>=0.29.0,<0.32`. 위치는 pyproject `[dependency-groups] dev` (line 398), main `dependencies` 아님. 즉 `pip install dartlab` 사용자는 pandera 를 받지 않는다.
- **주 사용처**: `src/dartlab/core/schemas.py` (스키마 SSOT). 실제 배선은 `src/dartlab/gather/dart/dartHelpers.py::_maybeValidateFinance` (env 게이트, production 기본 OFF, 실패 시 warning 만 raise 안 함) + `tests/_schemas/test_finance_schema.py` (fixture 10 종 회귀).
- **마지막 조사일**: 2026-07-06
- **현재 결정**: 채택 (개념, CI/dev 데이터 계약 게이트 한정). 의존성 승격 금지(dev-only 유지, 사용자 부담 0). 실배선은 finance·report 2 개뿐이고 나머지 49 개는 미배선 장식. not-null 강화는 실데이터 오탐으로 기각, dtype 강화는 무의미(전부 String), enum 강화만 실질 증분(옵션). 49 개 삭제는 불필요(청소 반사, 값어치 대비 안 맞음).

---

## 핵심 사실 (실측, 2026-07-06)

이번 조사는 웹이 아니라 우리 코드 실측 + fixture 실험으로 판정했다.

**배선 현황**

- `core/schemas.py` 에 스키마 51 개 정의(~850 줄). 주석에 `T6-4 sprint 추가 (30 schema 목표 도달)` = 숫자 맞추려 찍어낸 흔적.
- `core.schemas` import 는 repo 전체에서 딱 2 곳: `dartHelpers.py`(FinanceSchema), `test_finance_schema.py`(FinanceSchema, ReportSchema). `__all__` 51 개를 일괄 참조하는 곳 없음.
- 결론: 51 개 중 실사용 2 개, 나머지 49 개는 어디서도 호출/테스트 안 되는 미사용 정의.
- 유일한 production 경로(`_maybeValidateFinance`)도 env 기본 OFF + 실패 시 warning 만. 사용자 wheel 에 pandera 가 없어서 `try/except ImportError` 로 감싼 구조.

**강한 제약이 실데이터에 되나 (fixture 10 종 실험)**

- 구조: finance fixture 10 종이 (컬럼,타입) 시그니처 2 개로 수렴. 계약 걸 만함.
- 모든 컬럼이 String 타입(금액 `thstrm_amount` 포함). dtype 제약은 "string 이다" 이상 걸 게 없음.
- enum 후보가 실데이터에서 딱 떨어짐: `sj_div in {BS,CF,CIS,IS,SCE}`, `fs_div in {CFS,OFS}`, `reprt_code in {11011~11014}`. 현 스키마는 이걸 안 걸고 있음.
- not-null 강화 실패: `rcept_no` not-null 은 10 종 중 3 종만 통과. 나머지 7 종은 정상 데이터인데 rcept_no 에 null row 가 섞임. 즉 not-null 로 조이면 정상 데이터 70% 를 오탐. 현 스키마가 nullable=True 로 둔 건 게으름이 아니라 실데이터 성질.
- drift 3 종(컬럼 삭제·null 오염·enum 위반) 주입: 전부 잡음.

**효과 크기**

- 효과 = DART/EDGAR 가 응답 스키마를 조용히 바꿨을 때, 망가진 데이터가 panel → scan → analysis → 사용자/HF 로 퍼지기 전에 gather 끝점에서 CI 가 즉시 터뜨려 잡는 트립와이어.
- 저빈도(스키마 변경은 드묾) 고파급(터지면 silent bad data 라 blast radius 큼) 보험.
- 컬럼 존재 검사는 이미 있어서 흔한 drift(rename/drop)는 지금도 잡힘. enum 은 미묘한 drift(코드값 변경)까지 덤으로 잡는 증분.

---

## 조사 이력

### 2026-07-06 (pandera[polars] 0.29~0.31 라인, 우리 pin `<0.32`)

**카테고리별 관찰**

1. 개념 / 도구 적합성
   - DART/EDGAR raw 의 silent schema drift 를 gather 끝점에서 잡는다는 목적은 재무 라이브러리에 타당. Pandera 는 선언적 계약 + hypothesis 전략 생성까지 되어 도구 자체는 합당.
   - 판단: 개념 채택 유지.

2. 의존성 부담
   - dev-only 라 사용자 `pip install dartlab` 무영향. 사용자 런타임 강제하려면 하드 의존성 승격 필요한데, 그건 "single base install, extras 금지"([[feedback_no_patterns]]) 위반.
   - 판단: dev-only 유지, 하드 승격 금지. 맞는 자리는 CI/빌드 시점 데이터 계약 게이트(우리가 gather 해 HF 에 올리는 데이터 보호).

3. 배선 완성도
   - 51 정의 중 2 배선. 49 는 장식. 유일한 production 경로도 OFF + warning-only.
   - 판단: 실 gather 끝점(finance·report, 필요시 filings)만 진짜 배선. CI 는 warning 아니라 fail 로 조이는 게 값어치. production OFF 는 사용자 wheel 에 pandera 없으니 유지.

4. 제약 강도 (실측 기반)
   - enum 강화 = 됨(실데이터 통과 + drift 잡음). 실질 증분.
   - not-null 강화 = 안 됨(실데이터 오탐 7/10). 기각.
   - dtype 강화 = 무의미(전부 String).

5. 미사용 49 개 처리
   - 삭제 검토했으나 취소. 이유: 가만히 있는 정의라 런타임 비용 0, 삭제는 850 줄 들어내는 작업+리스크인데 기능 증가 0, 엔진 출력 컬럼 계약이라는 설계 의도 보존 가치. 유일한 삭제 근거(미래 독자 오해)는 module 상단 한 줄 주석으로 더 싸게 해결.
   - 판단: 삭제 불필요. 대신 `core/schemas.py` 상단에 "실배선 = FinanceSchema, ReportSchema 둘뿐, 나머지는 미배선 aspirational, 검증 의존/집계 금지" 한 줄 표시 권장(미착수).

6. 버전 / pin
   - pin `<0.32` 이유: 0.32.0 polars 백엔드가 `pa.Field(isin=...)` 빌트인 체크 미등록 → class 정의 시점 `KeyError 'isin'`. 업스트림 수정 시 상한 해제.
   - 판단: pin 유지. isin(enum) 을 실제로 쓰려면 이 상한이 오히려 필수.

**본 자료 (sources)**

- 코드: `src/dartlab/core/schemas.py`, `src/dartlab/gather/dart/dartHelpers.py`, `tests/_schemas/test_finance_schema.py`, `pyproject.toml` (line 51 main deps vs line 382~398 dev group).
- 실험: finance fixture 10 종(`tests/fixtures/*.finance.parquet`) 에 강한 제약(not-null·enum) 주입 + drift 3 종 탐지 테스트. 결과는 위 "핵심 사실" 참조.
- 외부 공식(pin 근거 재확인용): pandera polars 백엔드 isin 이슈. 상세는 pyproject 주석이 SSOT.

**결정 및 근거 (2026-07-06)**

- 채택 유지(개념, CI/dev 게이트). 변경 없음.
- 안 할 것: 의존성 하드 승격, not-null 강화, dtype 강화, 49 개 삭제. 모두 값어치 대비 안 맞거나 실측으로 기각됨.
- 옵션(미착수, 착수 시 소): enum 제약 추가(sj_div·fs_div·reprt_code), CI fail 로 조이기, schemas.py 상단 정직 주석 한 줄.
- 다음에 "pandera 뭐지"로 재조사 금지. 결론 바뀔 새 근거 = pandera[polars] 메이저 변화 또는 엔진 출력 검증을 실제로 배선하기로 결정할 때뿐.
