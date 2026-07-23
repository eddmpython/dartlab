# 진행 원장

## 완료

- [x] pyproc 0.0.10 공개 계약 감사
- [x] root `boot`와 `PyprocMachine`으로 이관
- [x] main-thread 중복 Pyodide 제거
- [x] DartLab transitive C 확장 명시 로드
- [x] exact runtime manifest와 cache namespace
- [x] OPFS core와 wheel cache, 2세대 GC, quota fallback
- [x] notebook workspace mount와 Web Lock writer
- [x] machine history branching adapter
- [x] 부팅 `cp0` 즉시 해제
- [x] capability 진단과 고급 기능 비활성 표기
- [x] base-aware, request-client-aware Service Worker bridge
- [x] 블로그 즉시 편집 셀과 사용자 의도 실행
- [x] 블로그 전체 화면 투영의 sequential, 무자동실행 정책
- [x] 옛 글 노트북 실행 정책과 중복 정의 오류 출력 정규화
- [x] 인라인 블로그 전역과 전체 화면 노트북 machine 격리
- [x] 플레이그라운드 공용 worker 통합
- [x] Gate A, Gate B, landing check, test, build
- [x] 일반 non-COI 제품 smoke
- [x] 자동 업데이트를 리뷰 후보 방식으로 변경
- [x] Skill OS와 완료 문서 갱신

## 제거

- [x] 자체 `CheckpointGraph`
- [x] `pyproc/runtime` ambient declaration
- [x] 플레이그라운드의 별도 `$pyodide/loader.js`
- [x] Service Worker의 중복 runtime wheel cache
- [x] 블로그 진입 시 무조건 runtime과 data prewarm

## 후속 조건부 작업

아래는 미완료가 아니라 upstream capability가 열릴 때 다시 평가할 항목이다.

- [ ] worker deterministic loader 검증 뒤 durable history 실험
- [ ] worker process loader 또는 main-thread coordinator 검증 뒤 process UI 실험
- [ ] 한 안정화 주기 무폴백 뒤 손수 ASGI 제거
- [ ] pyproc 1.0 이후 version policy 재평가

각 항목은 별도 PRD와 성능, 메모리, 브라우저 compatibility 증거 없이는 활성화하지 않는다.
