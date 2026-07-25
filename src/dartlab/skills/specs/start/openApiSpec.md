---
id: start.openApiSpec
title: OpenAPI Spec — public REST 진입점
kind: curated
scope: builtin
status: drafted
category: start
purpose: dartlab public REST API 의 OpenAPI 3.0 YAML 사양 — 외부 통합 진입점 표준. engines/recipes 호출 REST 추상화.
whenToUse:
  - OpenAPI
  - public REST
  - 외부 통합
  - API spec
  - YAML schema
inputs:
  - REST endpoint (HTTP)
outputs:
  - JSON response
  - error code
toolRefs: []
knowledgeRefs:
  - start.dartlabSkillOs
  - runtime.channel
sourceRefs:
  - dartlab://skills/start.openApiSpec
requiredEvidence:
  - skillRef
  - executionRef
runtimeCompatibility:
  server:
    status: limited
  localPython:
    status: limited
  mcp:
    status: limited
  webAi:
    status: limited
  pyodide:
    status: limited
linkedSkills:
  - start.dartlabSkillOs
  - runtime.channel
---

## endpoint 카탈로그

| 경로 | method | 매핑 |
|---|---|---|
| `/v1/company/{code}/show/{topic}` | GET | Company.panel (호환 URL) |
| `/v1/company/{code}/analysis/{axis}` | GET | Company.analysis |
| `/v1/scan/{axis}` | GET | scan |
| `/v1/macro/{axis}` | GET | dartlab.macro |
| `/v1/quant/{axis}` | GET | dartlab.quant |
| `/v1/search` | GET | dartlab.search |
| `/v1/recipe/{id}/execute` | POST | recipe execute |
| `/v1/skills` | GET | listSkills |
| `/v1/skill/{id}` | GET | getSkill |

## OpenAPI 3.0 YAML (snippet)

```yaml
openapi: 3.0.0
info:
  title: dartlab API
  version: 0.10.3
paths:
  /v1/company/{code}/show/{topic}:
    get:
      parameters:
        - name: code
          in: path
          required: true
          schema: {type: string, pattern: "^[0-9]{6}$"}
        - name: topic
          in: path
          required: true
          schema: {type: string, enum: [BS, IS, CF, CIS, SCE]}
      responses:
        200:
          description: success
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/CompanyShowResult"
```

## 강행 룰

1. 모든 endpoint OpenAPI YAML 작성 (자동 생성 X — 사람 작성).
2. error code 표준 (400/401/404/429/500).
3. rate limit (per-API-key, per-IP).
4. response 단위 dateRef + evidence ref 동행.

## 기본 검증

- YAML 정합 (swagger-cli validate).
- 모든 endpoint test 통과 (smoke).
- rate limit metric.
