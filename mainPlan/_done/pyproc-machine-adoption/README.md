# pyproc machine 채택 완료

상태: 완료, 2026-07-23

DartLab 웹 Python 표면을 pyproc 0.0.10의 root machine 계약으로 통합했다. 블로그 셀, 브라우저 노트북, 플레이그라운드는 한 worker와 한 machine을 공유한다. 블로그는 처음부터 편집 가능한 셀을 보여 주고, 사용자가 실행하거나 명시적으로 hover하기 전에는 Python과 데이터를 받지 않는다.

핵심 결론은 "전부 쓴다"가 아니라 "검증된 공용 기반은 전부 쓰고, 검증되지 않은 고급 기능은 capability로 막는다"다. 이 선택으로 기본 실행, 파일, 출력, 패키지, 캐시, 환경 진단, branching history, ASGI는 pyproc에 맡겼다. durable history와 worker process pool은 upstream loader 계약이 검증될 때까지 제품 기능으로 노출하지 않는다.

## 문서 지도

1. [00-decisions.md](00-decisions.md): 전문 검토 합의와 제품 결정
2. [01-architecture.md](01-architecture.md): 현재 구조와 소유권
3. [02-maintenance.md](02-maintenance.md): 버전, 캐시, 업그레이드, 롤백
4. [03-verification.md](03-verification.md): 실행 증거와 회귀 게이트
5. [04-progress-ledger.md](04-progress-ledger.md): 완료 원장과 후속 조건

Skill OS 정본은 `runtime.pyodideBrowser`와 `runtime.notebooks`다.
