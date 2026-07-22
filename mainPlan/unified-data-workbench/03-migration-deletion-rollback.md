# 03. 이관, 삭제, 롤백

## 1. 보호 원칙

현재 worktree에는 사용자 변경과 ignored Universe U5 source가 있다. 다음을 금지한다.

- `git reset --hard`
- `git checkout --`
- `git clean`
- 자동 stash
- tests/_attempts 일괄 삭제
- 사용자 변경 파일의 wholesale rewrite

새 파일 우선으로 작업하고, dirty 파일을 수정해야 하면 기존 diff를 읽은 뒤 최소 patch만 적용한다.

## 2. 단계별 이관

### M0. 계약과 guard

- data layer와 두 public axis를 문서와 architecture map에 등록
- lower owner가 data를 import하지 않는 guard
- data가 simulate, story, AI를 import하지 않는 guard
- PIT label-only 위조 kill test
- discovery network side effect 0 test

### M1. control plane 선별 승격

Universe U0부터 U3에서 canonical ID, temporal, visibility, provenance, catalog, admission, receipt를 data 내부 계약으로 승격한다. blog, media, simulator adapter, spatial은 제외한다.

파일을 기계적으로 통째로 복제하지 않는다. public Data Workbench 타입 이름과 현재 layer에 맞게 contract 단위로 이동하고 attempts test를 production test로 전환한다.

### M2. owner descriptor와 catalog

L1, L1.5, L2 owner별 metadata provider를 추가한다. 기존 registry와 DATA_RELEASES, extraction concepts를 projection하고 package 후보를 전수 분류한다.

기존 registry는 삭제하지 않는다. 현재 builder의 중앙 6엔진 tuple은 새 discovery SSOT로 교체한 뒤 compatibility derived view로만 남기거나 caller 0에서 제거한다.

### M3. query와 projection

- native partition
- common records tagged union
- factor observation long
- narrative statement
- graph statement와 edge
- resource locator

각 projection의 compatibility matrix와 preflight validation을 구현한다.

### M4. simulator 소비

1. 공개 `simulate`의 read-once 재무 입력을 `analysis.simulationInputs` data asset으로 전환한다.
2. data snapshot, contract hash, lineage, receipt를 `SimulationResult`까지 전달한다.
3. 사용처가 없는 `simulate/mirror.py`는 compatibility shim 없이 제거한다.
4. 순수 folding kernel은 `data.factorKernel`로 이관한다.
5. `table.py`, `tableUs.py`의 simulator 전용 대량 파생은 이번 L1, L1.5, L2 작업대 범위에 억지로 편입하지 않는다. 해당 source owner가 bounded asset을 선언할 때 query 경로로 단계 전환한다.

data는 simulator result나 admission registry를 import하지 않는다. simulator-owned expectation, assumption, admission ledger는 그대로 simulator가 소유한다.

### M5. 외부 공개

- root callable module
- `__all__`
- capability catalog
- EngineCall mapping
- CLI와 MCP는 기존 engine call을 통해 자동 도달
- wheel 설치 후 별도 process smoke
- typed JSON과 Arrow round-trip

### M6. 문서와 Skill OS

- `engines.data`를 운영 절차 안내에서 실제 data engine 계약으로 재정의
- 운영 workflow 내용은 별도 `operation.dataPipeline` 또는 linked section으로 분리
- `operation.architecture`, `operation.apiContract`, CLAUDE와 public README 동기화
- catalog, agent, mcp, web, pyodide, graph JSON 6종 수동 동기화와 byte 검증

## 3. 삭제 순서

삭제 후보:

1. simulate Mirror의 직접 engine materializer
2. reference Mirror의 11열 구 canonical 위치와 소유권 중복
3. simulator 전용 feeds, enginefeeds, factors 중 data asset registry와 완전히 중복되는 부분
4. table과 tableUs의 직접 source reader 중 data query로 parity가 증명된 함수
5. 중복 catalog projection과 stale 문서

삭제하지 않을 것:

- owner의 registry와 domain calculation
- simulator expectation, assumption, admission ledger
- UI transport workbench
- pipeline build orchestration
- ignored U5 source
- receipt replay에 필요한 legacy schema decoder

## 4. 삭제 gate

다음 다섯 조건을 모두 만족해야 한다.

1. src, tests, docs, Skill OS caller 0
2. KR, US 실데이터 parity
3. stable public API의 deprecation 기간 충족
4. 이전 provider로 즉시 복귀 가능한 rollback test
5. 기존 snapshot, receipt, CAS, ledger replay에 옛 경로 불필요

## 5. 롤백

단계별 commit을 분리한다.

- contract와 catalog commit
- query와 projection commit
- simulator adoption commit
- public surface와 docs commit
- cleanup commit

adoption 전에는 기존 Mirror와 direct reader를 유지한다. query failure 시 compatibility layer가 legacy provider로 되돌아가는 명시적 정책을 둘 수 있지만, fallback 결과를 data query 성공으로 위장하지 않는다. rollback 사용 여부를 receipt에 남긴다.
