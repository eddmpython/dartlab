# DartLab 장기 TODO

> 지금 당장은 아니지만, 조건이 맞으면 꺼내 쓸 항목들.
> 각 항목에 **트리거 조건**을 명시해서 "언제 하면 되는지"를 판단할 수 있게 한다.

---

## Sections / Diff

### Needleman-Wunsch 단락 정렬 도입
- **실험**: `experiments/080_sectionsRefinement/005_needlemanWunschDiff.py`
- **요약**: NW가 difflib 대비 평균 +3.0 유사도, 76.8% 승률. consolidatedNotes에서 최대 +54.8.
- **트레이드오프**: 속도 20~450x 열세 (O(n²) 유사도 매트릭스)
- **트리거**: 기간간 텍스트 변화 추적이 사용자 기능으로 올라올 때
- **적용 방향**:
  - `common/docs/diff.py`에 전면 교체가 아닌, difflib 매칭 품질 낮을 때 fallback
  - 50~500단락 범위만. 1000+ 단락은 banded NW 또는 `rapidfuzz.process.cdist` 배치 최적화 필요
  - fsSummary 같은 대규모 텍스트에서는 difflib이 우위 — 무조건 적용 금지

---

## Finance

(항목 추가 시 여기에)

---

## UI / Server

### ChatGPT OAuth 구독 모델 활용
- **현재**: `oauthToken.py` + `providers/oauthCodex.py`에 ChatGPT OAuth PKCE 구현 완료
- **가능성**: ChatGPT Plus/Pro 구독자가 API 키 없이 GPT-5.4/o3/o4-mini 사용 가능
- **트리거**: UI에서 "ChatGPT로 로그인" 버튼 추가 수요가 생길 때

---

## AI

### ✅ AI 코어 통합 — 단일 소스 오케스트레이터 (완료)
- **구현**: `engines/ai/core.py` — `analyze()` 동기 제너레이터, `AnalysisEvent` 이벤트 스트림
- **소비자**: `dartlab.ask()` / `dartlab.chat()` (코드), `server/streaming.py` (UI), CLI
- **진입점**: `dartlab.ask("005930", "재무 건전성")` — Company 내부 생성, 서버 불필요
- **server 통합**: context tier 로직 공유 (`_resolve_context_tier`), 나머지는 점진 통합

### server/streaming.py 전면 core 위임
- **현재**: context tier 로직만 core에서 재사용. SSE 레이아웃/async agent/guided JSON은 server 고유
- **목표**: 분석 경로의 context build + prompt assembly를 core.analyze()로 전면 위임
- **필요 작업**:
  - core에 `system_prompt` 이벤트, `yearRange` 메타 추가
  - server의 `_skeleton`/`_full` 분기별 SSE 레이아웃을 core 이벤트로 매핑
  - async queue agent streaming을 core 이벤트 소비로 교체
- **트리거**: server에 새 분석 기능 추가할 때 중복이 불편해질 때
- **예상 효과**: streaming.py 670줄 → ~200줄


