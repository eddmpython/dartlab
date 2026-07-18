# mainPlan 포트폴리오 인덱스

> 프로젝트 PRD·상세·진행상태의 정본은 각 폴더 안 문서다. 본 파일은 카테고리별 지도일 뿐이다.
> 끝난 PRD 는 `_done/` 로 격리한다(삭제 아님, 규약 = [_done/README.md](_done/README.md)).
> 상태 범례: 🟢 활성 진행 · 🟡 부분완료·정체 · ⚪ 미착수 설계(운영자 go 대기) · 📎 참조·운영 문서

## ★ 완료의 정의 (mainPlan 세션 강행)

**mainPlan 을 수행하는 세션은 "완료 = `_done` 처리까지"다.** 코드가 green 이고 배포됐어도, 문서가 `mainPlan/` 루트에 그대로 있으면 그 작업은 미완이다. 완료를 선언하기 전에 4매듭을 전부 짓는다.

1. `git mv mainPlan/<plan> mainPlan/_done/<plan>` (rename, 내용 무손실. 파일명 프리픽스 금지).
2. [_done/README.md](_done/README.md) 보관 목록에 한 줄(완료일 + as-built. 현역 런북 섞였으면 명시).
3. 본 인덱스에서 해당 항목을 활성 카테고리에서 빼고 하단 "완료·격리"로 이동.
4. `project_*` 메모리 + `MEMORY.md` §6.2 포인터를 ✅ 완료 + `_done/` 경로로 갱신.

이유: 완료를 `_done` 으로 매듭짓지 않으면 다음 세션이 끝난 PRD 를 활성으로 착각해 재착수하고, 활성 목록이 부풀어 진짜 남은 일이 안 보인다. 규약 SSOT = memory `feedback_mainplan_operation`.

## 1. 분석 리포트 · 서사 엔진

회사 단위 전문 리포트와 서사 조립.

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [professional-report-engine](professional-report-engine/) | 🟢 | story 엔진을 프로 애널리스트 리포트 SSOT 로 갈아엎기. P2 완결(emitter·`Company.reportModel` 공개계약). **P3(랜딩 동일소비) 운영자 결정 5건 대기.** |
| [periodic-report-dossier](periodic-report-dossier/) | 🟡 | 정기보고서 팩트 도시(분산+스파인). Phase 1 MVP 커밋됨. 사업보고서 영역이 아래 report-full-harvest 와 겹침(정리 대상). |
| [report-full-harvest](report-full-harvest/) | ⚪ | 사업보고서 전 섹션 수확(패널 −3·적층 블록). 설계 완료·구현 0. 운영자 결정 3종 대기. |
| [financial-statement-lab](financial-statement-lab/) | ⚪ | 터미널 재무제표 분석 surface 업그레이드(iTooza V차트·Butler 흡수). 비전 PRD, 착수 = 운영자 go. |
| [expectation-grid](expectation-grid/) | ⚪ | 기대 격자(E-panel 파생 추정). 완전 설계, P1~P6 착수 승인 대기. |

## 2. 시뮬레이션 · 시나리오

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [scenario-simulator](scenario-simulator/) | 🟢 | `dartlab.simulate(...)` 드라이버 DAG(L2.5). 결정론 코어 졸업, Play UI·fan·계약 등록 미완(preview). 사상 바닥 = 15·16. |

## 3. 스캔 · 스크리너 · 추출

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [scan-screener-os](scan-screener-os/) | 🟢 | 스크리너 = 조건x종목 판정격자. 퍼블릭 `/scan` 재구축 **구현 완료(눈검수·push 승인 대기)**. 옛 scan-composable-query 승계. |
| [panel-extraction-workbench-ssot](panel-extraction-workbench-ssot/) | 🟢 | 추출 개념 카탈로그 + 2-tier 완전성 census. panel-note-extraction-ssot(흡수) 확장. P3 dossier 는 폐기. |
| [scan-note-cross-section](scan-note-cross-section/) | 🟡 | 노트 횡단 스크리닝(재고·리스·법인세). Phase 1 구현 커밋됨. Phase 2(multiAxis·퍼블릭 UI)는 별도 승인. |

## 4. 노트북 · 브라우저 런타임 · 유니버스

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [dartlab-universe](dartlab-universe/) | 🟢 | 전체 HF 데이터를 지식과 결속(K0 spine~K1d row window 구현). 공개 진입은 사용자 검수 대기. |
| [dartlab-story-curriculum](dartlab-story-curriculum/) | 🟢 | 교육 SSOT = 블로그 연재 `dartlab 이야기`. 노트북 허브는 실습장. 편성지도·체크리스트(비공개). |
| [web-notebook-runtime](web-notebook-runtime/) | 🟡 | 설치 없는 브라우저 노트북(Pyodide 워커·OPFS·체크포인트). 다수 제품 적용 완료, TODO SSOT 잔여(wheel OPFS 캐시 등). ⚠ 커널 공유런타임 이관은 `_done/pyproc-runtime-ssot`(완료)가 승계. |

## 5. 콘텐츠 · 지식망

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [content-asset-ssot](content-asset-ssot/) | 📎 | 콘텐츠 자산 SSOT 3층(저작·`media/catalog.json`·HF 객체). **적용 완료·현재 운영 계약 문서**(cards-knowledge-network 가 의존). |
| [cards-knowledge-network](cards-knowledge-network/) | 🟡 | 카드→터미널 진입 + 회사 간 카드망 + 카드 결론 지식화. 데이터 토대(cardType) 착수, UI 는 푸시 게이트. |

## 6. 터미널 · UI · 데이터 내보내기

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [edgar-terminal-reach](edgar-terminal-reach/) | 🟡 | US(EDGAR) 종목 터미널 도달 배선 재정렬. 옛 `_done/edgar-parity-wiring` 대체 PRD. 가격·지수 구조 확정. |
| [table-export](table-export/) | ⚪ | zero-dep .xlsx 내보내기(뷰어 격자=미리보기). 기본 내보내기는 `_done/terminal-data-download`(ship)가 소유, 잔여 고도화 백로그. |
| [terminal-improvement](terminal-improvement/) | ⚪ | 기존 터미널 surface 확장(워치리스트 1개만 신설). 비전 PRD, 구현 0. |
| [landing-mobile-optimization](landing-mobile-optimization/) | ⚪ | 랜딩 모바일 최적화(리포트·카드 디자인). 기획 박제 완료, 운영자 승인 후 구현. |
| [tutorial-guide](tutorial-guide/) | ⚪ | 공유 투어 엔진(map·terminal). PRD 확정, 착수 = 운영자 go. |

## 7. AI 연결 · 1급 AI

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [ai-workbench-connector](ai-workbench-connector/) | ⚪ | 외부 AI 가 호출하는 evidence workbench connector(MCP-first·CF Worker). 구현 착수 PRD, 코드 0. |
| [first-party-ai](first-party-ai/) | ⚪ | dartlab 자신이 글쓰고 분석하는 1급 AI 레인. 비전 PRD, 구현 0. |

## 8. 인프라 · 기술 연구

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [polars-gpu-backend](polars-gpu-backend/) | ⚪ | 선택적 GPU cross-scan backend. 비전 PRD, NEXT = 운영자 go 시 `_attempts` 벤치. |
| [innovation-stack-research](innovation-stack-research/) | 📎 | 외부 최신 기술 흡수 위치·기각 기준 리서치 노트. **구현 없음이 정상**(참조 문서). |

## 9. 외부 데이터 수집

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [brokerage-research-index](brokerage-research-index/) | ⚪ | 증권사 리서치 링크 인덱스(메타만·본문 링크아웃). PRD 확정, `tests/_attempts/brokerageIndex` 졸업게이트 미착수. |

## 10. 제품 아키텍처 (메타)

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [dartlab-lens-product-architecture](dartlab-lens-product-architecture/) | ⚪ | 저장소 전체 제품 구조 + 공개 5 분석 렌즈 + 루트 README 제품화. 설계 확정(2026-07-18), 구현 미착수. |

---

## 완료·격리 (→ `_done/`)

끝난 PRD 는 [_done/](_done/) 로 격리하고 [_done/README.md](_done/README.md) 보관 목록이 정본이다.
최근 격리(2026-07-18): `pyproc-runtime-ssot`(라이브 배포) · `macro-simulation-engine`(완결) · `terminal-data-download`(이미 ship).

## 정리 관찰 (후속 판단 필요)

- **사업보고서 영역 3중 중복**: `professional-report-engine`(리포트 서사) · `report-full-harvest`(섹션 수확) · `periodic-report-dossier`(팩트 도시)가 같은 사업보고서 데이터를 다르게 조립한다. 한 SSOT 로 수렴할지 운영자 판단.
- **미착수 설계 백로그(⚪ 8건)**: `ai-workbench-connector` · `first-party-ai` · `financial-statement-lab` · `polars-gpu-backend` · `terminal-improvement` · `tutorial-guide` · `report-full-harvest` · `brokerage-research-index` 는 전부 "착수 = 운영자 go"에서 3~4주+ 정체 중이다. 착수하거나 폐기 판정하기 전까지 활성 작업 목록과 구분한다.
