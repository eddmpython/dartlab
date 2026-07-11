# 진행 원장 - pyproc Runtime SSOT

> 결정·근거·세션 재개(NEXT) 원장. 상세 설계는 01~04, 실측은 00.

## 2026-07-11 세션 1 (기획 착수)

### 한 일
- **실측 3종 완료** (00-verified-facts SSOT):
  1. COEP 헤더 실측(`curl -I`): jsdelivr 안전, files.pythonhosted.org CORP/CORS 없음(휠 설치 차단 위험), HF cors-only.
  2. pyproc 소스 판독: 격리 요구 기능별 매핑(Runtime/AsgiServer/Terminal 격리 불요, fork+JSPI 만 필요), 부팅 토폴로지(boot() 메인스레드 / worker.js 워커안전), 소비 정책(SHA 핀, float 금지).
  3. **Tier-1 엔드투엔드 실증**(node-pyodide, exit 0): pyproc AsgiServer HELPER 가 dartlab FastAPI 를 dispatch -> `/health` 200 `{"ok":true,"version":"0.10.9"}`, 13 라우트, `/openapi.json` 200.
- mainPlan 폴더 생성: README + 00-verified-facts.
- 앞서 정리: pyodide 0.27.2 -> 0.27.5 버전 통일(loader.js·pyodide README·블로그 08), 커밋+push(39a85e483).

### 확정된 결정
- **D-STAGE**: Tier-1(격리 불요, 전 브라우저) 먼저 -> Tier-2(Chromium fork) 점진. 근거 = 격리 요구가 기능별로 갈리고 Tier-1 이 회귀 0 으로 실증됨.
- **D-NO-DELETE**: 라이브 커널 즉시 삭제 금지. seam 뒤 폴백 강등 후 게이트 통과 시 삭제.
- **D-AUTOUPDATE-SHAPE**: 자동 반영 = float 아님(pyproc 정책). 게이트 통과 후 핀 범프.

### 열린 질문 (에이전트 토론 대기)
- 워커-부팅 해법: `globalThis.loadPyodide` 프리셋 vs pyproc 에 워커안전 boot upstream 요청 vs 메인스레드-부모 토폴로지 재구성.
- seam 인터페이스 정확한 시그니처 + 마이그레이션 순서(dispatch·checkpoint 교체 vs 폴백 병존).
- 자동업데이트 워크플로 구체(핀 위치·cadence·auto-merge 정책) + pyproc 게이트 정의.
- COEP 롤아웃 SW 변경 상세 + pythonhosted CORP 완화 + 실브라우저 테스트 매트릭스.
- 리스크 원장 + go/no-go + veto 조건 + kill-switch.

### 에이전트 토론 수렴 (3인 완료)
- **브라우저 아키텍트**: 2개 소스 정정 -> (1) `boot()` 금지, `new Runtime(py)` 로 우리 pyodide 채택(두 번째 인스턴스 방지 + 버전 불일치 회피). (2) CheckpointGraph(분기 DAG) vs ReactiveController(선형) 비교체, 체크포인트 seam 뒤 손수 유지. ASGI 만 superset 교체. seam 인터페이스·Tier-1 첫 PR·upstream 요청 4 확정.
- **릴리즈 인프라**: 정본 핀 = `landing/package.json` github SHA 의존(Vite 번들 same-origin, Tier-1+Tier-2 동시 충족). 주간 게이트 핀 범프 Action(resolve/gate-a/gate-b/land). COEP 는 Tier-2 라우트 한정 credentialless(휠 문제 소멸) + require-corp 폴백. pythonhosted GET 은 ACAO * 있음(재실측 정정).
- **적대 PM**: Tier-1 조건부 GO(벤더·핀·플래그 off·throwaway 선증명·kill-switch), 라이브 Pages 격리 HARD NO-GO(R1 휠 붕괴 실측 전). R1~R9 + veto 5조건.
- **수렴**: 커널 라이브 CDN import 기각(적대 R9 + 인프라 Tier-2) -> package.json github 의존으로 확정(아키텍트 CDN 제안 뒤집힘).

### 확정 결정 추가
- **D-CONSUME**: package.json github SHA 핀(Vite 번들), 커널 CDN import 0.
- **D-ADOPT**: `new Runtime(pyodide)` 채택, pyproc `boot()` 프로덕션 경로 금지.
- **D-CHECKPOINT**: CheckpointGraph 유지, ReactiveController 는 P4 실험(자료모델 상이).
- **D-COEP**: Tier-2 라우트 한정, credentialless 우선. 사이트 전역·라이브 노트북 격리 현재 NO-GO.

### 문서 완성 (2026-07-12)
- 00 실측·01 아키텍처·02 자동반영·03 리스크·04 PRD(5섹션)·README·06 원장 전부 작성.

### NEXT (세션 재개 지점)
1. **운영자 승인 게이트**: 04-prd 로 P0(throwaway parity 선증명) 착수 승인 요청 중.
2. 승인 시: P0 하네스(tests/_attempts/pyprocKernel) ASGI·체크포인트 골든 diff 실측 -> P1 seam PR(플래그 off, 커밋만, push 는 UI 게이트라 운영자 승인) -> P2 flip -> P3 자동반영(pyprocPinBump.yml).
3. P4(Tier-2 격리)는 0.27.5 스냅샷 spike + COEP 실측 후 별도 PRD.
