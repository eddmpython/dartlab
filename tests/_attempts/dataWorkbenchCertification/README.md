# Data Workbench 전수 인증 Attempt

목표: queryable asset 전체가 소유자 이름에 의존하지 않고 descriptor 계약만으로 선택자를 만들며, 한 번의 혼합 query에서 빠짐없이 실행 단위로 컴파일되는지 검증한다.

## 확인할 가설

1. subject와 measure 선택은 owner 이름이 아니라 `selectorKind`와 `selectorRequired`로 결정할 수 있다.
2. 필수 선택자가 없으면 owner 실행 뒤 예외가 아니라 실행 전 `MISSING_SELECTOR` gap으로 판정할 수 있다.
3. 선택자가 선택 사항인 macro와 gather asset도 전달된 subject를 잃지 않는다.
4. locator 전용 resource query는 subject 없이도 안전하게 실행할 수 있다.
5. 현재 queryable asset 170개를 하나의 descriptor 기반 계획으로 모두 컴파일할 수 있다.

## 승격 기준

- 선택자 규칙에 owner별 분기문이 없다.
- 필수 subject와 measure 누락이 결정적인 gap이 된다.
- subject, measure, selector 없음의 세 경로를 모두 검증한다.
- 같은 입력에서 계획 순서와 gap이 결정적이다.
- production 전수 라우팅 테스트가 queryable catalog 전부를 실제로 포함한다.
