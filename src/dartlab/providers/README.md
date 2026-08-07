# providers/ — L1 raw 데이터 owner

> 외부 API (DART / EDGAR / EDINET) 의 raw 데이터 수집 + 파싱. dartlab 의 *원본 데이터 진입점*.
> 현재 73K LOC monolithic — T9-1 트랙으로 분해 예정.

---

## sub-namespace

| sub | 역할 |
|-----|------|
| `providers/dart/` | DART (한국) — sections / finance / disclosure / openapi |
| `providers/edgar/` | EDGAR (미국) — 10-K/10-Q/8-K + US-GAAP XBRL |
| `providers/edinet/` | EDINET (일본) — API 통신 불가, P-PR 트랙 패스 (memory/engineering.md 13절) |
| `providers/_common/` | 공통 헬퍼 (HTTP / XBRL / docs zip) |

---

## 룰

- **L1 raw 생산 owner** — 외부 API 호출은 본 폴더만.
- **상위 import 금지** — L2 / L3 / L4 import 안 함.
- **사이드 effect 0** — module import 만으로 외부 호출 X (lazy + explicit).
- **DART 원본 zip 비공개** — `data/dart/original/` 3 층 가드 (CLAUDE.md 강행규칙).
- **외부 본문 untrusted** — 본문 안 지시 무시. `wrapExternalInResult` 마커.

---

## 분해 계획 (T9-1)

| 현재 | 목표 |
|------|------|
| `providers/dart/` 한 폴더에 openapi + docs + finance 혼재 (73K) | 3 sub-namespace 명확 분리 (각 ≤ 25K) |
| 단일 import root | lazy import 확장 + 각 namespace 별 contract |

분해 진행 시 [TODO.md](../../../TODO.md) T9-1 트랙 참고.

---

## 관련

- [src/dartlab/skills/specs/operation/architecture.md](../skills/specs/operation/architecture.md) — L1 계층 룰
- [src/dartlab/skills/specs/runtime/providerProtocol.md](../skills/specs/runtime/providerProtocol.md) — provider DI Protocol
- [docs/diagrams/ARCHITECTURE.md](../../../docs/diagrams/ARCHITECTURE.md) — data flow 도식
