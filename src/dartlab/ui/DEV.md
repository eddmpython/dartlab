# dartlab AI — UI 개발 문서

## 구조: 2-탭 (AI Chat / Viewer)

`dartlab ai` 실행 시 상단 헤더에 두 개의 탭이 있다.

```
┌──────────┬──────────┐
│  AI Chat │  Viewer  │
└──────────┴──────────┘
```

### AI Chat 탭

대화 중심. AI가 sections/finance/report를 활용해서 분석하고 답변한다.

- 기본 채팅 구조 유지
- 질문 → AI가 Company 데이터를 활용해 답변
- 차트, 테이블 인라인 렌더링
- Company가 선택되면 맥락이 자동으로 깔림

### Viewer 탭

sections를 중심으로 한 데이터 탐색 집중 뷰. AI 없이 독립 사용 가능.

Viewer 내부 하위 뷰:

```
Viewer
├── 공시 뷰어       ← sections 기반, 핵심
├── 정보 검색       ← 종목/공시 검색
├── 데이터 검색     ← 재무 데이터 탐색
└── 대시보드        ← (향후)
```

## 공시 뷰어 — sections의 GUI

공시 뷰어 = sections DataFrame을 실제 공시 문서처럼 렌더링하는 것.

### 레이아웃

```
┌─ 좌측 목차 ──────┬─ 본문 ─────────────────────────────────┐
│ I. 회사의 개요    │                                         │
│   companyOverview │  ■ 1. 회사의 개요              heading  │
│   ✓ text (3)     │                                         │
│   ✓ table (1)    │  ● 2025Q4  ● 2024Q4  ○ 2023Q4  timeline│
│ II. 사업의 내용   │                                         │
│   businessOverview│  삼성전자는 1969년 설립된...    body     │
│   ✓ text (8)     │                                         │
│   ✓ table (5)    │  ██░░ 전년 대비 12% 변경       diff bar │
│ III. 재무에 관한  │  + "반도체 HBM 생산량 확대"             │
│   BS (finance)   │  - "메모리 수요 부진에 따른..."          │
│   IS (finance)   │                                         │
│   ...            │  ┌─ 테이블 ──────────────────┐          │
│                   │  │ 항목 │ 2025 │ 2024 │ ... │          │
│                   │  │ 매출 │ 300T │ 280T │ ... │          │
│                   │  └─────────────────────────┘          │
└───────────────────┴─────────────────────────────────────────┘
```

### 텍스트 렌더링 규칙

1. **heading**: 최신 기간 기준 1개만 표시. 시간에 따라 바뀌지 않음.
   - sections의 `textNodeType="heading"` 행에서 최신 기간 값 사용

2. **body**: 기본은 최신 기간 텍스트 표시
   - 그 아래에 타임라인 바: `● 2025Q4  ● 2024Q4  ○ 2024Q3  ○ 2023Q4`
   - 활성 기간(●)은 데이터 있는 기간, 비활성(○)은 null
   - 타임라인 클릭 → 해당 시점 텍스트로 교체

3. **diff 요약**: 현재 보고 있는 기간과 직전 기간 사이의 변화
   - 변경률 바 (시각적)
   - 추가/삭제된 핵심 문장 미리보기
   - `c.diff(topic, prevPeriod, currentPeriod)` 활용

### 테이블 렌더링 규칙

테이블은 텍스트보다 복잡하다. 단계적 접근:

**Phase 1: 원본 마크다운** (기본)
- 마크다운 테이블을 HTML 테이블로 렌더
- 타임라인으로 기간 전환 가능
- 수평화 없음, 무손실

**Phase 2: 수평화 토글** (tableParser 성공 시)
- "수평화 보기" 토글 활성화
- 항목 × 기간 매트릭스로 전환
- 실패 시 원본 유지 (fallback)

**Phase 3: AI 보정** (향후)
- raw_markdown 블록에 AI 파싱
- AI가 매핑 규칙만 생성, 숫자는 만들지 않음

### sections 기반 데이터 흐름

```
sections DataFrame
  ↓ chapter/topic 순서대로 순회
  ↓ blockType으로 text/table 분기
  ↓ text → heading 고정 + body 타임라인 + diff
  ↓ table → 원본 마크다운 (Phase 1) / 수평화 (Phase 2)
  ↓ finance topic → finance 엔진 직접 (sections 우회)
```

### 서버 API 매핑

| 뷰어 기능 | 서버 엔드포인트 |
|-----------|----------------|
| 좌측 목차 | `GET /api/company/{code}/toc` |
| topic 본문 (뷰어 전용) | `GET /api/company/{code}/viewer/{topic}` |
| topic 본문 (기간 최적화) | `GET /api/company/{code}/viewer/{topic}?period={p}` |
| diff 요약 | `GET /api/company/{code}/diff/{topic}/summary` |
| 기간 diff | `GET /api/company/{code}/diff/{topic}?from={p1}&to={p2}` |
| trace | `GET /api/company/{code}/trace/{topic}` |
| (레거시) sections 원본 | `GET /api/company/{code}/sections` |
| (레거시) show 블록 | `GET /api/company/{code}/show/{topic}` |

## Chat ↔ Viewer 연동

- Chat에서 "사업의 내용 보여줘" → Viewer 탭 자동 전환 + 해당 topic 스크롤
- Viewer에서 텍스트 선택 → "AI에게 물어보기" 버튼 → Chat 탭 전환 + 선택 텍스트 컨텍스트
- 두 탭은 같은 Company 인스턴스를 공유

## 구현 순서

1. 상단 탭 (AI Chat / Viewer) 레이아웃
2. Viewer 내 공시뷰어 — 좌측 목차 + 본문 (텍스트 heading/body)
3. 텍스트 타임라인 + diff 요약
4. 테이블 원본 마크다운 렌더링
5. Chat ↔ Viewer 연동
6. 정보 검색 / 데이터 검색 하위 뷰
7. 테이블 수평화 토글
8. 대시보드 (향후)

## 컴포넌트 구조 (2026-03-19 구현)

```
App.svelte               ← 2-탭 (Chat / Viewer) + 탭 전환 버튼
├── ChatArea.svelte       ← AI Chat 탭
├── DisclosureViewer.svelte ← Viewer 탭 메인 레이아웃
│   ├── ViewerNav.svelte    ← 좌측 목차 (toc API)
│   └── TopicRenderer.svelte ← topic 블록 렌더링
│       ├── DiffSummary.svelte  ← 변경 요약 카드
│       ├── TimelineBar.svelte  ← 기간 선택 바
│       └── TableRenderer.svelte ← 테이블 렌더러
└── stores/
    ├── workspace.svelte.js  ← activeView (chat/viewer) 전환
    └── viewer.svelte.js     ← viewer 전용 상태 (toc, topic, cache)
```

## 기존 자산 재사용

- `SectionsViewer.svelte` — 레거시 공시 뷰어 (right panel용, 점진 제거 대상)
- `ChatArea.svelte` — AI 대화
- `AutocompleteInput.svelte` — 종목 검색
- 서버 API: toc, viewer/{topic}, diff/{topic}/summary (전부 구현됨)
