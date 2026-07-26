# ai/ — L4 chat-native agent

> dartlab 의 LLM 자율 tool-calling 본체. 사용자 자연어 질문을 받아 dartlab 의 엔진/도구를 자율 호출.
> CLAUDE.md "graph 회귀 금지" 강행규칙 — `agent.py` chat-native 본체 보존, 5 패스 노드 클래스 신설 금지.

---

## 공개 API

| 모듈 | 역할 |
|------|------|
| `ai/agent.py` | chat-native agent (본체) — LLM 자율 tool calling |
| `ai/tools/` | tool 카탈로그 (현재 32 수동 + `_autogen.py` 자동 변환 후속) |
| `ai/trace.py` | AuditCollector — 5 패스 dump JSON round-trip (T11-4) |
| `ai/workbench/` | sub-agent (옵션) — 5 패스 BRIEF/WORK/CRITIQUE/COMPOSE/GATE/HARVEST |
| `ai/providers/` | LLM provider (OAuth / API 키) wrapper |
| `ai/memory/` | 세션 메모리 + searchPastSessions |
| `ai/recipes/` | AI 추천 recipe 카탈로그 |
| `ai/settings/` | model resolver / config |

---

## 진입점

```python
import dartlab
result = dartlab.ask("삼성전자 재무건전성")
# → AI 가 Company / analysis / credit / scan 도구 자율 호출
# → 답변 + ref (원본 추적 가능)
```

---

## 룰 (CLAUDE.md 강행)

- **본체는 `agent.py`** — chat-native + LLM 자율 tool calling. 5 패스 노드 클래스 신설 금지.
- **외부 본문은 untrusted** — `wrapExternalInResult` 마커 강제 (T2-5 audit).
- **5 패스 노드 식별자 회귀 가드** — `tests/audit/checkAgentBoundary.py` 가 차단 (T11-5).
- **ref circularity 가드** — `tests/audit/refCircularityCheck.py` (T11-3).

---

## 운영 KPI 측정 시작 (cryptic-discovering-kettle.md 트랙 2)

마스터 플랜 박힌 측정 인프라 4 종 — 운영자가 환경변수 활성 후 1+ 일 누적 시 즉시 정량 측정 시작.

```bash
# 1. trace dump 활성 — 모든 runAgent 호출 자동 JSON dump (~/.dartlab/ai_trace/{sessionId}.json)
export DARTLAB_AI_TRACE_DUMP=1

# 2. Anthropic prompt cache 활성 (Claude provider 사용 시) — system + 마지막 tool spec ephemeral 마커
export DARTLAB_ANTHROPIC_CACHE=1

# 3. 1+ 일 운영 후 KPI digest 출력
uv run python -X utf8 tests/audit/aiMetricsDigest.py --last 1d

# 4. workbench 빈도 확인 (PR-W2 production 빈도 라인 갱신용)
uv run python -X utf8 tests/audit/workbenchUsageDigest.py --last 7d

# 5. recall A/B harness (PR-O6, scripted N=20 baseline)
uv run --no-sync python -X utf8 tests/_attempts/memoryRecallAb.py
```

KPI 7 종 목표 + scripted baseline 은 `C:\Users\MSI\.claude\plans\cryptic-discovering-kettle.md` 의 "KPI 측정 결과" 표 참조. 운영 trace 1+ 주 누적 후 본 baseline 과 비교 → token 35% 감소 / cache hit > 60% / recall +15% 도달 검증.

---

## 관련

- [src/dartlab/skills/specs/runtime/workbenchEvidenceFlow.md](../skills/specs/runtime/workbenchEvidenceFlow.md) — evidence flow 본문 SSOT
- [memory/feedback_no_graph_regression.md](../../../) — graph 강박 회귀 가드 룰
- [TODO.md](../../../TODO.md) T11 트랙
- [docs/diagrams/ARCHITECTURE.md](../../../docs/diagrams/ARCHITECTURE.md) — 워크벤치 sequence 도식
