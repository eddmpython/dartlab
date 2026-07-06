# 00b — 로컬 런타임 브리지의 일반화 + 로컬 GPU (탐색 노트)

> 출처: 운영자가 "Colab 로컬 런타임 동기화처럼 로컬 GPU 도 쓸 수 있지 않나, 깊이 고민하자" 제기.
> 본 노트는 왓처 브리프(`00-design-brief.md`)의 **로컬 브리지 축이 왓처 전용이 아님**을 밝히고,
> GPU·컴퓨트 방향을 박제한다. 패널 결과 합성 시 통합한다. **브리지는 왓처보다 크다 → 별 프로젝트
> (`local-runtime-bridge`)로 졸업할 후보.**

## 핵심 realization — 하나의 브리지, 여러 능력

Colab "로컬 런타임 연결"(`jupyter_http_over_ws` + 토큰 → 호스트 프론트가 로컬 Jupyter+GPU 에서 실행)은
**우리의 퍼블릭(GitHub Pages PWA) ↔ 로컬 `dartlab` 서버(`:8400` FastAPI `/api`) 브리지와 같은 패턴**이다.

GPU 는 *별도 기능*이 아니라 **로컬 런타임이 노출하는 하나의 리소스**다. 따라서:

```
퍼블릭 프론트엔드  ──(보안 페어링된 브리지)──►  로컬 dartlab 런타임(:8400)
                                                   ├─ 능력: 왓처 설정(개인)
                                                   ├─ 능력: AI 추론(로컬 GPU·Ollama)   ← 이미 작동
                                                   ├─ 능력: GPU 횡단 scan(cuDF)        ← polars-gpu-backend
                                                   └─ 능력: 컴퓨트 오프로드(allowlist) ← Colab 패리티
```

→ 왓처 설정과 GPU 컴퓨트는 **형제 능력**이지 중첩이 아니다. 브리지(핸드셰이크·전송·보안)를 **SSOT 층**으로
설계하고, 능력들이 그 위에 꽂힌다.

## 이미 있는 것 (재사용)

- **로컬 서버**: `dartlab` CLI → `dartlab ai` 가 `127.0.0.1:8400` FastAPI+SPA. `ensurePort` 재사용. `/api/status?probe` 헬스.
- **로컬 GPU AI**: `ai/providers/ollama.py` — GPU VRAM 감지·`127.0.0.1:11434`·qwen3:14b. **로컬 GPU 추론 작동 중**, 퍼블릭 미노출.
- **GPU scan 계획**: `mainPlan/polars-gpu-backend/` — `DARTLAB_CROSS_SCAN_ENGINE=gpu` opt-in, `scan/io/cross.py` backend protocol. CPU 기본 불변. KILL: cudf 기본의존·`[gpu]` extras.
- **runtime 일반화**: `createPublicRuntime`/`createLocalRuntime` 코어 공유(data-workbench-ssot, _done). AI 는 `/api/agent/*` 경유.

## 방향들 (준비도 × 가치 × 위험 순)

1. **로컬 AI 추론 over 브리지 (Ollama)** — **준비됨**(provider·GPU감지·/api/agent 존재). 가치 高(무과금·프라이버시 추론).
   위험 中(핸드셰이크 필요). 퍼블릭 PWA 가 로컬 페어링되면 ask/compose 를 *내 GPU* 에서. → **첫 GPU 브리지 능력 후보**.
2. **Polars GPU 횡단 scan over 브리지** — `polars-gpu-backend` 재사용. 브리지는 트리거 경로일 뿐. 파워유저 opt-in, CPU 기본. 그 PRD 가드 준수.
3. **범용 컴퓨트 오프로드 (Colab 패리티 그 자체)** — 가장 강력·가장 위험. 임의 코드 실행 금지, **allowlist 된 dartlab capability 만**(EngineCall 패턴)으로 제약해야 안전. 가장 늦게·가장 게이트.
4. **(학습은 브리지에서 제외)** — finance_slm G1~G3 게이트 + 개발머신/CI 학습 금지. 제품은 얼린 체크포인트 추론만 → 1번(추론)으로 흡수.

## Make-or-break — 보안 페어링

Colab 은 토큰-in-URL + 사용자가 로컬 런타임 URL 직접 붙여넣기로 푼다. 우리도 **명시 페어링(토큰 핸드셰이크)**
필수 — *조용한 localhost 자동연결 금지*. 안 그러면 **임의 악성 웹페이지가 내 로컬 런타임을 호출**한다(DNS rebinding·
CORS·PNA 포함). 이 위협모델은 왓처 브리지와 공유(보안 패널리스트가 지금 검토 중). 컴퓨트는 *실행*이라 *설정 읽기*보다
판돈이 크다 → 페어링 강도·capability allowlist 가 핵심.

## 불가침 제약

- CPU 기본 경로 절대 안 깨짐. GPU 없는 사용자 무영향. `[gpu]` extras·cudf 기본의존 금지(polars-gpu KILL 계승).
- GPU 가치는 좁다(대형 횡단 scan·로컬 LLM 한정). P1 아님 — 파워유저 능력.
- 임의 코드 실행 금지 — capability allowlist 만.
- 학습은 브리지 밖. 게이트·개발머신 금지 불변.

## 통합 방침

- 지금 2번째 패널 동시 가동 안 함 — **왓처 패널의 브리지·보안 결론이 GPU 브리지의 직접 입력**이라 순차가 맞다.
- 왓처 패널 반환 후: 브리지를 *foundational 층*으로 격상할지 + GPU 능력을 별 프로젝트(`local-runtime-bridge`)로
  분리할지 판단 → 필요 시 GPU·컴퓨트 전용 패널 1회.
