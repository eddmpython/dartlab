# mainPlan

앞으로 지을 임시 설계와 작업 순서다. 영구 문서나 현재 제품 계약의 정본이 아니다. 현재 동작의 정본은 [`docs/handbook/`](../docs/handbook/README.md)이다.

한 initiative는 폴더 하나다. 구현이 끝나면 코드와 실제 실행에서 확인한 현재 계약을 handbook의 product, architecture, reference, operations에 승격하고 해당 initiative 폴더를 삭제한다. `_done`으로 옮기지 않는다. 영구 자산은 mainPlan을 인용하지 않는다.

상태 범례: 🟢 활성 구현 · 🟡 부분 구현 · ⚪ 미착수 임시 설계

## 0. 제품 방향 · 북극성 운영

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [dartlab-north-star](dartlab-north-star/) | 🟢 | 북극성 `Weekly Verified Analysis Loops`와 outcome lifecycle, 실행 증거 registry, scorecard, 주간 제품 운영 주기를 세운다. **축별 점수표는 루트 README `## 북극성`이 정본**(2026-08-02 원장 결정 4 번복). 현재 전역 값은 `미측정`, 측정 바닥(Phase 0) 구현 대기. |

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
| [cards-knowledge-network](cards-knowledge-network/) | 🟡 | 카드→터미널 진입 + 회사 간 카드망 + 카드 결론 지식화. 데이터 토대(cardType) 착수, UI 는 푸시 게이트. |

## 6. 터미널 · UI · 데이터 내보내기

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [edgar-terminal-reach](edgar-terminal-reach/) | 🟡 | US(EDGAR) 종목 터미널 도달 배선 재정렬. 가격·지수 구조 확정. |
| [tutorial-guide](tutorial-guide/) | ⚪ | 공유 투어 엔진(map·terminal). PRD 확정, 착수 = 운영자 go. |

## 7. AI 연결 · 1급 AI

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [local-agent-workbench](local-agent-workbench/) | 🟢 | 로컬 앱 chat을 ChatGPT 양식에서 에이전트 작업대 양식으로 재편. paseo 아이디어 흡수 원장(01)이 SSOT, 스택 교체 없음. 착수 1단계 = 서버 영속 타임라인(A1). |
| [ai-workbench-connector](ai-workbench-connector/) | ⚪ | 외부 AI가 호출하는 remote evidence workbench connector. local MCP tool identity는 현재 Agent Runtime 계약과 정합하되 remote auth/CF 경계는 별도. |
| [first-party-ai](first-party-ai/) | ⚪ | public deterministic/on-device compose 중심으로 재정합 필요. local advanced runtime과 direct edge model 전제는 현재 Agent Runtime 계약 위에서 재검한다. |

## 8. 인프라 · 기술 연구

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [innovation-stack-research](innovation-stack-research/) | 📎 | 외부 최신 기술 흡수 위치·기각 기준 리서치 노트. **구현 없음이 정상**(참조 문서). |

## 9. 외부 데이터 수집

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [brokerage-research-index](brokerage-research-index/) | ⚪ | 증권사 리서치 링크 인덱스(메타만·본문 링크아웃). PRD 확정, `tests/_attempts/brokerageIndex` 졸업게이트 미착수. |

## 정리 관찰 (후속 판단 필요)

- **미착수 설계 백로그**: `dartlab-north-star` · `ai-workbench-connector` · `first-party-ai` · `financial-statement-lab` · `tutorial-guide` · `brokerage-research-index`는 "착수 = 운영자 go"인 설계 항목이다.
