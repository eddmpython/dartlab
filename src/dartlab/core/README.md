# core/ — L0 primitive

> dartlab 의 최하위 계층 — 메모리·캐시·logger·DI·decimal·secrets·data audit 등 *상위 계층이 다 의존* 하는 헬퍼.
> 상위 import 금지 (L1 / L1.5 / L2 / L3 / L4 어떤 계층도 import 하지 않음).

---

## 공개 API

| 모듈 | 역할 |
|------|------|
| `core/logger.py` | 중앙 로거 + Rich handler + `logEvent` 구조화 이벤트 (T1-1) |
| `core/memory/` | RSS 관측 + provider 주입형 bounded LRU/IPC 정책 + 계산 memoization + OomTripwire |
| `core/cache.py` | gather 시계열용 TTL cache |
| `core/decimal.py` | 회계 정합 Decimal 헬퍼 (toDecimal / roundDecimal / isClose / safeDivide) (T7-4) |
| `core/dataAudit.py` | sync/prebuild data lineage 추적 (T7-2) |
| `core/secrets.py` | SecretStore Protocol + EnvSecretStore backend (T2-3) |
| `core/credentials.py` | CredentialProvider Protocol DIP |
| `core/plugins.py` | 외부 plugin entry_points 로더 + introspection (T5-1) |
| `core/offlineGuard.py` | prebuild 단계 외부 host 차단 (CLAUDE.md sync vs prebuild 분리) |
| `core/naming/aliases.json` | 매개변수 의미 일관성 표준 사전 (`code` / `ticker` 등) |
| `core/env.py` | `.env` 자동 로드 |
| `core/types.py` | 공통 type alias / TypedDict |
| `core/random.py` | 결정론적 random seed (T7-3 정합) |

---

## 룰

- **상위 import 금지** — providers / scan / analysis 등 어떤 계층도 import 안 함.
- **Polars 직접 의존 0** — core 는 *데이터 구조 모름*. 필요 시 helper 가 dict / list 받음.
- **외부 API 호출 0** — 모든 외부 의존성은 L1 provider / gather 가 owner.
- **메모리 안전** — `BoundedCache` 외 무제한 dict 금지.

---

## 관련

- [src/dartlab/skills/specs/operation/architecture.md](../skills/specs/operation/architecture.md) — 4 계층 단방향
- [pyproject.toml [tool.importlinter]](../../../pyproject.toml) — L0 contract
- [TODO.md](../../../TODO.md) — T1-1 / T3-4 / T7-2/3/4 / T2-3 / T5-1 트랙
