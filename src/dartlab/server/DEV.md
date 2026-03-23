# Server — FastAPI 웹 서버

## 구조

```
server/
├── __init__.py       # FastAPI 앱 설정 (CORS, GZip, 라우터 등록)
├── runtime.py        # uvicorn 실행 (ensure_port, run_server)
├── web.py            # SPA 정적 파일 등록 (ui/build/)
├── api/              # API 라우터 (thin adapter — 로직은 엔진에 위임)
│   ├── ask.py        # /api/ask (LLM 질의 + SSE 스트리밍)
│   ├── company.py    # /api/search, /api/company/{code}/*
│   ├── analysis.py   # /api/company/{code}/diff, diff/matrix
│   ├── ai.py         # /api/ai/* + /api/status + /api/suggest + OpenDART key 관리
│   ├── macro.py      # /api/macro/* (FRED 거시경제)
│   ├── room.py       # /api/room/* (협업 세션)
│   ├── data.py       # /api/data/* (데이터 관리)
│   └── common.py     # 공통 헬퍼 (company_dep 등)
├── cache.py          # CompanyCache (LRU, 적응형 TTL, 메모리 압박 감지)
├── streaming.py      # SSE 변환 (core.analyze() 이벤트 → SSE)
├── models.py         # Pydantic 스키마 (AskRequest, HistoryMessage 등)
├── resolve.py        # 종목 이름 → 코드 (strict → fuzzy fallback)
├── chat.py           # 대화 히스토리 + 동적 프롬프트
├── dialogue.py       # 대화 흐름 관리
├── security.py       # 터널 보안 (TokenManager, TunnelKillSwitch)
├── room.py           # 협업 세션 관리
├── embed.py          # embed widget SSE 라우터
└── services/         # 서비스 레이어
    ├── ai_analysis.py   # 질문 분류 → 모듈 선택 → 병렬 계산
    ├── ai_profile.py    # provider 설정 + preload
    ├── channel_runtime.py # Telegram/Slack/Discord runtime start/stop
    └── company_api.py   # Company 조회/변환/직렬화
```

## 핵심 원칙

1. **One-Source Consumption**: 모든 클라이언트(SPA, CLI, embed, adapter)는 `/api/*` 경유
2. **라우터 = thin adapter**: 실제 로직은 dartlab 엔진에 위임, 라우터는 변환/검증만
3. **SSE 스트리밍**: `stream_ask()`가 `core.analyze()` 이벤트를 SSE로 변환
4. **메모리 안전**: CompanyCache 최대 5종목, 1500MB threshold 시 적응형 TTL 축소
5. **설정 단일화**: provider secret, OpenDART key, 외부 채널 상태를 `/api/status`에서 함께 노출하고, UI는 같은 상태 모델을 기준으로 렌더링

## CompanyCache 설계

```
LRU 캐시 (최대 5종목)
├── 적응형 TTL: 메모리 압박 시 TTL 축소
├── 메모리 모니터링: 1500MB 초과 시 가장 오래된 항목 제거
└── thread-safe: asyncio.Lock 기반
```

- Company 1개 ≈ 200~500MB → 5개 동시 = 최대 2.5GB
- 메모리 압박 감지 시 자동으로 오래된 캐시 제거

## SSE 이벤트 타입

| 이벤트 | 설명 |
|--------|------|
| `meta` | 질문 분류, 선택 모듈, 사용자용 evidence label |
| `snapshot` | 기업 요약 데이터 |
| `context` | 분석 컨텍스트 |
| `system_prompt` | LLM 시스템 프롬프트 |
| `tool_call` | LLM 도구 호출 |
| `chunk` | LLM 응답 스트리밍 |
| `ui_action` | UI 렌더링 지시 |
| `done` | 완료 |
| `error` | 에러 |

### Meta / Done payload 원칙

- server는 `core.analyze()`의 raw module 정보와 사용자용 evidence label을 둘 다 흘려보낸다.
- raw 식별자:
  - `includedModules`
- 사용자용 식별자:
  - `includedEvidence` = `[{name, label}]`
  - `includedModuleLabels`
- UI는 기본적으로 사용자용 식별자를 렌더링하고, raw module 이름은 디버그/내부 검증에만 쓴다.
