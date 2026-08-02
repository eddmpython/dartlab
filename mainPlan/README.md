# mainPlan 포트폴리오 인덱스

> 프로젝트 PRD·상세·진행상태의 정본은 각 폴더 안 문서다. 본 파일은 카테고리별 지도일 뿐이다.
> 끝난 PRD 는 `_done/` 로 격리한다(삭제 아님, 규약 = [_done/README.md](_done/README.md)).
> 운영자가 폐기를 확정한 중복·보류 PRD는 삭제하고 본 인덱스에서도 제거한다.
> 상태 범례: 🟢 활성 진행 · 🟡 부분완료·정체 · ⚪ 미착수 설계(운영자 go 대기) · 📎 참조·운영 문서

## ★ 완료의 정의 (mainPlan 세션 강행)

**mainPlan 을 수행하는 세션은 "완료 = `_done` 처리까지"다.** 코드가 green 이고 배포됐어도, 문서가 `mainPlan/` 루트에 그대로 있으면 그 작업은 미완이다. 완료를 선언하기 전에 4매듭을 전부 짓는다.

1. `git mv mainPlan/<plan> mainPlan/_done/<plan>` (rename, 내용 무손실. 파일명 프리픽스 금지).
2. [_done/README.md](_done/README.md) 보관 목록에 한 줄(완료일 + as-built. 현역 런북 섞였으면 명시).
3. 본 인덱스에서 해당 항목을 활성 카테고리에서 빼고 하단 "완료·격리"로 이동.
4. `project_*` 메모리 + `MEMORY.md` §6.2 포인터를 ✅ 완료 + `_done/` 경로로 갱신.

이유: 완료를 `_done` 으로 매듭짓지 않으면 다음 세션이 끝난 PRD 를 활성으로 착각해 재착수하고, 활성 목록이 부풀어 진짜 남은 일이 안 보인다. 규약 SSOT = memory `feedback_mainplan_operation`.

## 0. 제품 방향 · 북극성 운영

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [dartlab-north-star](dartlab-north-star/) | ⚪ | 북극성 `Weekly Verified Analysis Loops`와 outcome lifecycle, 실행 증거 registry, scorecard, 주간 제품 운영 주기를 세운다. 현재 값은 `미측정`, Phase 0 착수 대기. |

## 1. 분석 리포트 · 서사 엔진

회사 단위 전문 리포트와 서사 조립.

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [professional-report-engine](professional-report-engine/) | 🟢 | story 엔진을 프로 애널리스트 리포트 SSOT 로 갈아엎기. P2 완결(emitter·`Company.reportModel` 공개계약). **P3(랜딩 동일소비) 운영자 결정 5건 대기.** |
| [financial-statement-lab](financial-statement-lab/) | ⚪ | 터미널 재무제표 분석 surface 업그레이드(iTooza V차트·Butler 흡수). 비전 PRD, 착수 = 운영자 go. |
| [expectation-grid](expectation-grid/) | ⚪ | 기대 격자(E-panel 파생 추정). 완전 설계, P1~P6 착수 승인 대기. |

## 2. 시뮬레이션 · 시나리오

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [scenario-simulator](scenario-simulator/) | 🟢 | `dartlab.simulate(...)` 드라이버 DAG(L3). 결정론 코어 졸업, Play UI·fan·계약 등록 미완(preview). 사상 바닥 = 15·16. |

## 3. 스캔 · 스크리너 · 추출

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [scan-screener-os](scan-screener-os/) | 🟢 | 스크리너 = 조건x종목 판정격자. 퍼블릭 `/scan` 재구축 **구현 완료(눈검수·push 승인 대기)**. 옛 scan-composable-query 승계. |
| [panel-extraction-workbench-ssot](panel-extraction-workbench-ssot/) | 🟢 | 추출 개념 카탈로그 + 2-tier 완전성 census. panel-note-extraction-ssot(흡수) 확장. P3 dossier 는 폐기. |

## 4. 노트북 · 브라우저 런타임 · 유니버스

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [dartlab-universe](dartlab-universe/) | ⚪ | HF 전체·실존 엔진 전체·블로그·미디어를 하나의 근거 추적 지식 공간으로 묶는 전용 데이터 엔진. 기존 시스템 무변경·data-engine-first PRD, 공개 연결은 운영자 검수 후 별도 승인. |
| [dartlab-story-curriculum](dartlab-story-curriculum/) | 🟢 | 교육 SSOT = 블로그 연재 `dartlab 이야기`. 노트북 허브는 실습장. 편성지도·체크리스트(비공개). |

## 5. 콘텐츠 · 지식망

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [content-asset-ssot](content-asset-ssot/) | 📎 | 콘텐츠 자산 SSOT 3층(저작·`media/catalog.json`·HF 객체). **적용 완료·현재 운영 계약 문서**(cards-knowledge-network 가 의존). |
| [cards-knowledge-network](cards-knowledge-network/) | 🟡 | 카드→터미널 진입 + 회사 간 카드망 + 카드 결론 지식화. 데이터 토대(cardType) 착수, UI 는 푸시 게이트. |

## 6. 터미널 · UI · 데이터 내보내기

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [edgar-terminal-reach](edgar-terminal-reach/) | 🟡 | US(EDGAR) 종목 터미널 도달 배선 재정렬. 옛 `_done/edgar-parity-wiring` 대체 PRD. 가격·지수 구조 확정. |
| [tutorial-guide](tutorial-guide/) | ⚪ | 공유 투어 엔진(map·terminal). PRD 확정, 착수 = 운영자 go. |

## 7. AI 연결 · 1급 AI

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [agent-runtime-engine](agent-runtime-engine/) | ⚪ | 설치된 Codex·Claude Code·ACP agent를 사용하는 local Bring Your Agent runtime. 직접 모델 OAuth/API와 provider hardcoding을 제거하는 상세 설계, 구현 0. |
| [ai-workbench-connector](ai-workbench-connector/) | ⚪ | 외부 AI 가 호출하는 remote evidence workbench connector. local MCP tool identity는 agent-runtime-engine과 정합하되 remote auth/CF 경계는 별도. |
| [first-party-ai](first-party-ai/) | ⚪ | public deterministic/on-device compose 중심으로 재정합 필요. local advanced provider와 direct edge model 전제는 agent-runtime-engine 결정 뒤 재검. |

## 8. 인프라 · 기술 연구

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [innovation-stack-research](innovation-stack-research/) | 📎 | 외부 최신 기술 흡수 위치·기각 기준 리서치 노트. **구현 없음이 정상**(참조 문서). |

## 9. 외부 데이터 수집

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [brokerage-research-index](brokerage-research-index/) | ⚪ | 증권사 리서치 링크 인덱스(메타만·본문 링크아웃). PRD 확정, `tests/_attempts/brokerageIndex` 졸업게이트 미착수. |

## 완료·격리 (→ `_done/`)

끝난 PRD 는 [_done/](_done/) 로 격리하고 [_done/README.md](_done/README.md) 보관 목록이 정본이다.
최근 격리(2026-07-18): `dartlab-lens-product-architecture`(다섯 공개 렌즈 제품화) · `pyproc-runtime-ssot`(라이브 배포) · `macro-simulation-engine`(완결) · `terminal-data-download`(이미 ship).
2026-07-21: `landing-mobile-optimization`(🔀 후속 UI 작업에 흡수·라이브).

## 정리 관찰 (후속 판단 필요)

- **미착수 설계 백로그**: `dartlab-north-star` · `agent-runtime-engine` · `ai-workbench-connector` · `first-party-ai` · `financial-statement-lab` · `tutorial-guide` · `brokerage-research-index`는 "착수 = 운영자 go"인 설계 항목이다. 활성 구현과 구분한다.
