# 현재 계약 소유자

| 계약 | 코드 정본 | 설명 정본 | 실행 가드 |
|---|---|---|---|
| 공개 Python 엔진 | `src/dartlab/__init__.py` | Skill OS `operation.apiContract` | `tests/audit/notebookContract.py` |
| 데이터 작업대 | `src/dartlab/dataHub/`, `ui/packages/runtime/src/data/` | Skill OS `operation.architecture`, `operation.ui` | architecture와 UI data wiring audit |
| 다운로드 카탈로그 | `src/dartlab/core/dataConfig.py` | Skill OS `operation.dataDownloadCenter` | `tests/core/test_download_catalog.py` |
| 시뮬레이션 | `src/dartlab/simulate/`, `src/dartlab/macro/simulate/` | Skill OS `engines.simulate` | simulate focused tests와 architecture audit |
| 리포트 | `src/dartlab/story/` | Skill OS `engines.story` | story와 report model tests |
| 검색 | `src/dartlab/search/` | Skill OS `engines.search` | search contract tests |
| 알림 파이프라인 | `.github/`, `src/dartlab/scan/`, push hub | Skill OS `operation.notifyPipeline` | workflow와 watcher tests |
| Agent Runtime | `src/dartlab/ai/runtime/` | handbook Agent Runtime 문서 | AI runtime, gateway, schema drift tests |
| 제품 outcome | `src/dartlab/ai/runtime/evidenceStore.py` | handbook 북극성 문서 | outcome API와 evidence verification tests |

수량과 열거값은 코드 또는 생성 계약이 정본이다. 이 표는 소유 위치를 설명하며 수기 복제본을 만들지 않는다.
