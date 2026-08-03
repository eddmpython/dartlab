# 데이터 작업대

DartLab 데이터 흐름은 owner 엔진과 단일 소비 경로를 유지한다. 수집은 gather, 가공과 횡단은 scan, 외부 프로세스의 대규모 작업은 dataHub가 소유한다. 런타임은 이 정본을 직독하며 편의를 위한 별도 사본이나 독립 fetch 경로를 만들지 않는다.

UI 데이터는 `ui/packages/runtime/src/data/fetch`를 단일 호출 진입점으로 사용하고 `data/origins` 레지스트리에서 source identity와 정책을 찾는다. 로컬 전용 API는 local adapter 안에 격리하고 공개 표면과 공유 표면은 같은 바닥 계약을 소비한다.

브라우저 실행은 Pyodide 커널 하나를 계산 SSOT로 사용한다. 노트북 실행과 브라우저 API가 별도 Python 상태를 만들지 않는다. 서버용 비동기 API는 import 시 무거운 엔진을 적재하지 않는다.

다운로드 센터 노출 항목은 `src/dartlab/core/dataConfig.py`의 공개 카탈로그에서 도출한다. 목록을 UI에 별도로 복제하지 않는다.
