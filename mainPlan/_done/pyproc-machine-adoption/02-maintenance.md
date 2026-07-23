# 유지보수와 릴리스

## 버전 변경 규칙

세 런타임 버전은 `landing/runtime-manifest.json`과 `landing/package.json`의 exact pin으로 관리한다. `pyprocApplyPin.mjs`는 두 파일을 함께 바꾼다. pyproc은 1.0 전까지 patch도 breaking으로 취급한다. 버전 범위와 자동 병합은 금지한다.

버전을 바꾸면 다음 항목을 함께 확인한다.

1. root export에 `boot`, `checkEnvironment`, machine type 계약이 있는가.
2. `boot({ loadPyodide, indexURL })`가 worker에서 한 Pyodide만 만드는가.
3. `machine.runtime`의 packages, stdout, interrupt, mount, ASGI 계약이 유지되는가.
4. history tree의 parent와 branch 복원이 유지되는가.
5. exact DartLab wheel과 네 C 확장이 함께 import되는가.
6. runtime namespace가 새 버전 조합으로 바뀌는가.

## 자동 업데이트

6시간 주기 resolver는 npm 최신 버전을 찾는다. 새 후보는 다음을 모두 통과한다.

- Gate A: Node에서 root machine, transitive C 확장, FS, stdout, branching history, ASGI.
- Gate B: 실제 Chromium COI와 JSPI에서 root machine, exact DartLab, branching history, 2-lane process.
- landing: check, 전체 test, production build.

통과 뒤에도 자동 병합하지 않는다. 전용 PR 토큰이 있으면 리뷰 PR을 만들고, 없으면 후보 branch와 deduplicated issue를 만든다.

## 수동 브라우저 smoke

릴리스 전 일반 non-COI 주소에서 다음을 확인한다.

1. `dartlab 이야기` 글을 열고 편집 셀이 즉시 보이는가.
2. 실행 전 Python output과 runtime 다운로드가 없는가.
3. 첫 셀 `import dartlab`이 `polars` 오류 없이 실행되는가.
4. 셀을 수정하고 다시 실행하면 수정 결과가 나오는가.
5. 같은 SPA 세션에서 전체 화면이나 플레이그라운드가 공용 worker를 쓰는가.
6. `/pyapi`가 base path와 요청 tab을 보존하는가.

COI Gate B만으로는 일반 블로그의 `SharedArrayBuffer` 부재 회귀를 잡지 못한다. non-COI smoke는 별도 필수다.

## 장애와 롤백

- machine boot 실패: 사용자에게 원문 오류를 표시하고 재시도 시 죽은 worker를 교체한다.
- pyproc ASGI 설치 실패: 같은 worker의 손수 ASGI로 한 번 폴백한다.
- OPFS 또는 quota 실패: cache와 persistence만 내리고 메모리 세션을 유지한다.
- Web Lock 충돌: 두 번째 tab은 persistent writer가 되지 않고 conflict capability를 표시한다.
- 새 pyproc 후보 실패: exact pin과 lockfile을 직전 검증 버전으로 되돌린다.

손수 ASGI 제거 조건은 한 안정화 주기 동안 production 오류와 폴백 사용이 0이고, Gate A와 실제 `/pyapi` browser smoke가 계속 통과하는 것이다.

## upstream 승격 조건

다음 두 조건은 DartLab에서 우회 구현하지 않는다.

- deterministic boot가 worker 제공 `loadPyodide`를 보존하고 durable save, recover, open이 실제 worker에서 통과.
- process pool이 worker 또는 명시적 main-thread coordinator를 통해 자식 loader를 안전하게 만들고 두 브라우저 세대에서 통과.

조건이 충족되면 capability 문자열과 Skill OS부터 바꾸고 UI를 연다.
