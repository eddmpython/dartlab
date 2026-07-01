---
id: operation.README
title: Operation 카테고리 hub
purpose: dartlab skills/specs/operation/ 카테고리 진입점.
kind: curated
category: operation
status: curated
requiredEvidence: []
expectedOutputs: []
runtimeCompatibility:
  pyodide:
    status: supported
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
whenToUse:
  - operation 카테고리 시작점
---

# Skill OS — `operation/` 카테고리 hub

> 운영 설계 SSOT. 사상 (philosophy) 부터 코드 품질 (code) · API 계약 (apiContract) · 테스트 (testing) 까지.
> 외부 기여자 / 신규 메인테이너가 dartlab 의 *왜 / 어떻게* 를 이해하기 위한 본진.

---

## 추천 진입 순서

| 순서 | spec | 무엇을 |
|------|------|--------|
| 1 | [philosophy.md](philosophy.md) | 사상 SSOT (정점) — alias 금지 / single SSOT / 4 계층 단방향 |
| 2 | [architecture.md](architecture.md) | L0~L4 계층 구조 + import 룰 + sub-namespace 책임 |
| 3 | [code.md](code.md) | 코드 품질 — camelCase / docstring 9 섹션 / SSOT 3 종 |
| 4 | [apiContract.md](apiContract.md) | 새 함수 추가 시 contract 룰 |
| 5 | [testing.md](testing.md) | 테스트 계층 + marker + 메모리 안전 |
| 6 | [coreloop.md](coreloop.md) | 자가개선 루프 운영 SSOT |
| 7 | [methodology.md](methodology.md) | 분석 방법론 (forensics / 6 막 인과 / scenario) |

---

## 분류 (29 spec)

| 분류 | spec |
|------|------|
| **사상 / 정점** | philosophy · coreloop · methodology · stability |
| **구조 / 계층** | architecture · code · apiContract · refactorChecklist |
| **테스트 / 검증** | testing · engineAudit · skillDevelopmentLoop |
| **운영 / CLI** | cliMaintenance · contributionWorkflow · issues · recipePromote |
| **데이터 / 매핑** | mappingRefresh · docsBuilderRefactor · dataDownloadCenter (공개 parquet 서빙·라이브 API) |
| **AI / Skill** | aiEngine · aiProductReplatform · extendSkills · intentBoosts · opsAsSkills · skillMarket · docstringStandard |
| **UI / 시각** | dashboardDesign · ui |
| **분석 시나리오** | sixActsAnalysis (회사 간 비교는 engines.panel `dartlab.compare`) |

---

## 다음 카테고리

- **start/** — 첫 진입 (외부 LLM / 신규 사용자)
- **runtime/** — 실행 환경 (mcp / pyodide)
- **engines/** — 15 분석 엔진
- **recipes/** — 분석 recipe lifecycle

---

## 관련

- [SCHEMA.md](../SCHEMA.md) — Skill OS schema
- [TODO.md](../../../../../TODO.md) T10-5 — 4 카테고리 hub 생성 트랙
- [CONTRIBUTING.md](../../../../../CONTRIBUTING.md) — 외부 기여자 PR 흐름
