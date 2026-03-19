# DartLab 에이전트 규칙

> `CLAUDE.md`와 공통 규칙은 동일하게 유지한다. 한쪽을 수정하면 다른 쪽도 즉시 반영.

## 언어

- 사용자와의 대화는 **한국어**로 답변

## 핵심 원칙

### sections = 레포 근간
- sections(topic × period 수평화)가 회사의 전체 지도
- finance → sections의 해당 topic을 **대체** (숫자 authoritative)
- report → sections에 **채운다** (DART only)
- EDGAR → report 없이 sections + finance 대체만으로 완성

### Company 공통 인터페이스
- show(topic) / index / trace(topic) / diff() — 핵심 4개
- docs / finance / profile — namespace 3개
- BS/IS/CF/CIS, ratios, ratioSeries, timeseries — finance 바로가기
- sections, topics, filings(), insights, market, currency — 메타

### 코드 품질
- bare except 금지 → 구체적 예외 타입 명시
- 사용자 입력 검증은 early return
- 에러를 삼키지 않는다

## 데이터 소스

- DART 전자공시 (한국)
- SEC EDGAR (미국)
- 릴리즈 config: `src/dartlab/core/dataConfig.py` → `DATA_RELEASES`

## 장기 성장 전략 (5축)

### 축 1: MCP 서버 — AI 도구화 (최우선 레버리지)
- Claude Desktop/ChatGPT/Cursor에서 dartlab을 도구로 사용
- sections/show/diff/search/finance를 MCP tool로 노출
- 킬러: "삼성전자 리스크 섹션 올해 뭐 바뀌었어?" → diff 결과 즉시 반환

### 축 2: dartlab AI 2-탭 (AI Chat / Viewer) — 체감 포인트 (핵심 집중과제)
- **상단 2-탭**: AI Chat (대화 집중) / Viewer (데이터 탐색 집중)
- **공시 뷰어** (Viewer 핵심): sections 교차나열, heading 최신 1개 고정, body 타임라인+diff
  - 텍스트: heading 고정 → 타임라인 바 → 최신 본문 → diff 요약
  - 테이블: Phase 1 원본 마크다운 → Phase 2 수평화 토글 → Phase 3 AI 보정
- **Viewer 하위 뷰**: 공시뷰어 / 정보검색 / 데이터검색 / (향후 대시보드)
- **Chat ↔ Viewer 연동**: 대화에서 "보여줘" → Viewer 전환, Viewer에서 선택 → Chat 질문
- 상세 설계: `src/dartlab/ui/DEV.md`

### 축 3: EDGAR 커버리지 확대
- S&P 500 전종목 → "any US company, 5 lines of code"
- heading/body 분리 품질 개선

### 축 4: diff + 알림 — 변화 감지 자동화
- sections 기반 기간간 서술형 텍스트 변화 자동 감지
- 주간 뉴스레터/텔레그램 봇
- Bloomberg에 없는 것: 서술형 공시의 변화 감지

### 축 5: 유입 + 바이럴
- 블로그 SEO + llms.txt → AI 검색 유입
- Jupyter/Colab 노트북 → "5줄로 분석"
- GitHub 스타 + 커뮤니티

## 실행 우선순위

| 순서 | 축 | 첫 마일스톤 |
|------|-----|------------|
| 1 | 축 2 AI 2-탭 | 상단 탭 + 공시뷰어 heading/body + 타임라인 + diff |
| 2 | 축 1 MCP | 첫 5개 tool 동작 |
| 3 | 축 4 diff | 주간 변화 리포트 생성 |
| 4 | 축 5 바이럴 | Colab 노트북 3개 배포 |
| 5 | 축 3 EDGAR | S&P 500 커버리지 |

## 비전

> Bloomberg는 사람이 읽는 터미널. dartlab은 **AI가 읽는 터미널**이 된다.
> sections 수평화가 엔진, MCP가 진입점, 뷰어가 체감 포인트.

## 개발 규칙 참조

상세 개발 규칙은 `CLAUDE.md`를 따른다:
- 프로젝트 구조, 실험 규칙, 블로그 규칙, 기술 스택
- Git 커밋/푸시 규칙 (AI 흔적 금지)
- 자동 생성 문서 체계 (registry 기반)
- 가상환경, 인코딩, 안정성 tier
