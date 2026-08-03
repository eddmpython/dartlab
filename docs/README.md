# docs

DartLab 문서가 사는 곳이다. 현재 제품 계약의 영구 정본은 `handbook/` 하나다.

| 위치 | 역할 | 수명 |
|---|---|---|
| `docs/handbook/product/` | 지금 사용자가 할 수 있는 것과 제한 | 영구 |
| `docs/handbook/architecture/` | 깨지면 안 되는 구조와 불변식 | 영구 |
| `docs/handbook/reference/` | 정확한 API, 이벤트, 상태 표 | 영구 |
| `docs/handbook/operations/` | 빌드, 테스트, 배포, 복구 | 영구 |
임시 설계와 진행 기록은 이 문서 트리에 포함하지 않는다. 구현이 끝난 기능은 설계 문장을 복사하지 않고 코드와 실제 실행에서 현재 사실을 다시 확인해 handbook으로 승격한다. Git 이력이 설계 과정을 보존한다.
