# 결정 원장

## 전문 검토 합의

런타임 계약, 브라우저 통합, 유지보수와 릴리스 세 관점에서 독립 검토했다. 세 검토의 합의는 다음과 같다.

1. pyproc의 machine core는 실익이 있다. 직접 관리하던 실행, 파일, 출력, 패키지, history와 환경 진단을 공개 계약 하나로 모을 수 있다.
2. pyproc 0.0.10은 patch 번호지만 공개 표면이 크게 바뀌었다. root export와 machine 계약만 사용하고 `pyproc/runtime`이나 root `Runtime` value를 가정하면 안 된다.
3. 블로그의 1차 경험은 "노트북 생성"이 아니라 본문 안의 즉시 편집 셀이어야 한다. 전체 노트북은 긴 작업을 위한 보조 진입점이다.
4. 페이지 진입 시 자동 실행이나 데이터 prefetch는 비용과 놀람을 만든다. 사용자 의도 뒤에만 런타임을 준비한다.
5. durable history, process pool, virtual origin을 무조건 켜는 것은 이득이 아니다. 현재 worker loader와 브라우저 전역 계약에서 거짓 지원이나 메모리 회귀가 된다.

## 채택한 범위

- root `boot({ loadPyodide, indexURL })`가 Pyodide를 한 번만 만든다.
- 셀 실행과 파일 IO는 `machine.run`, `machine.runAsync`, `machine.fs`를 쓴다.
- 패키지, stdout, interrupt, OPFS mount, ASGI는 `machine.runtime` 공개 능력을 쓴다.
- checkpoint UI는 `machine.history` branching tree를 문자열 ID로 감싼다.
- `checkEnvironment()` 결과를 capability에 그대로 노출한다.
- core와 wheel 캐시는 pyproc 경유 OPFS 단일 소유로 통합한다.
- 블로그, 노트북, 플레이그라운드는 같은 execution store와 worker singleton을 사용한다.

## 보류한 범위

- durable history: deterministic worker boot가 소비자 `loadPyodide`를 보존한다는 근거가 생길 때까지 비활성.
- process pool: worker에서 자식 Pyodide loader가 안전하게 부팅된다는 브라우저 증거가 생길 때까지 비활성.
- virtual origin: DedicatedWorker에는 `navigator.serviceWorker` 계약이 없으므로 현재 페이지의 Service Worker bridge를 유지.
- 손수 ASGI: pyproc ASGI가 기본이지만 한 안정화 주기 동안 자동 폴백으로 유지.

## 실익 판정

실익은 기능 수가 아니라 소유권 감소와 회귀 방지에서 확인한다. 원래 오류였던 `polars` 누락을 의존성 로더 한 곳에서 막고, main thread와 worker의 중복 Pyodide를 없앴으며, 체크포인트를 자체 그래프 대신 machine history로 교체했다. 반대로 아직 제품 가치가 입증되지 않은 process와 durable 기능은 켜지 않았다.
