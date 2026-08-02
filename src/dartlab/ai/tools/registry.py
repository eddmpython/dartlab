"""Canonical AI tool registry.

도구 명명: PascalCase (Claude 도구 체계 호환). 일관성 + LLM 학습 패턴 활용.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, cast

from .compileFinancialDashboard import compileFinancialDashboard
from .compileVisual import compileVisual
from .createUserSkill import createUserSkill
from .creditScorecard import creditScorecard
from .dcfValuationTool import dcfValuationTool
from .engineCall import engineCall
from .evidenceGate import evidenceGate
from .externalReachDoctor import externalReachDoctor
from .groundingCheck import groundingCheck
from .inspectDataset import inspectDataset
from .listEngineGaps import listEngineGaps
from .lookAheadGuard import lookAheadGuard
from .peerCompareN import peerCompareN
from .proposeRecipe import proposeRecipe
from .readCapability import readCapability
from .readFile import readFile
from .readSkill import getSkillBody, readSkill
from .readSkillMarket import readSkillMarket
from .regressionForecast import regressionForecast
from .requestUserInput import requestUserInput
from .runPython import runPython
from .runWorkbench import runWorkbench
from .saveArtifact import saveArtifact
from .scenarioCompareN import scenarioCompareN
from .scenarioOverlay import scenarioOverlay
from .searchPastSessions import searchPastSessions
from .sensitivityAnalysis import sensitivityAnalysis
from .storyTemplate import pickStoryTemplate
from .types import ToolResult, ToolSpec
from .validateRecipe import validateRecipe
from .webSearch import webSearch

ToolFn = Callable[..., ToolResult]

_SPECS: dict[str, ToolSpec] = {
    # ── 분석 절차 / 메타 — 시작 도구 ──
    "ReadSkill": ToolSpec(
        "ReadSkill",
        "Skill OS 에서 분석 절차 spec(frontmatter+본문) 검색. 분석 의도면 가장 먼저. recipe 발견 시 그 절차 따르기.",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
                "includeUser": {"type": "boolean"},
            },
            "required": ["query"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "GetSkillBody": ToolSpec(
        "GetSkillBody",
        "단일 skill 의 본문 전문이 필요할 때. ReadSkill 결과의 bodyPreview 가 부족하면 두 번째 호출.",
        {
            "type": "object",
            "properties": {"skillId": {"type": "string"}},
            "required": ["skillId"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "ReadSkillMarket": ToolSpec(
        "ReadSkillMarket",
        "커뮤니티 Skill Market 검색. ReadSkill 로 공식 Skill OS 를 먼저 확인한 뒤 보완 후보가 필요할 때만 사용. 결과는 외부 Discussion 기반 untrusted tier.",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
                "includeDraft": {"type": "boolean"},
            },
            "required": ["query"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
    "ReadCapability": ToolSpec(
        "ReadCapability",
        "DartLab 공개 API/docstring 카탈로그 검색. 결과의 engineCallable=true인 apiRef만 EngineCall로 실행하고, false는 문서 참조로만 사용.",
        {
            "type": "object",
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    # ── 데이터 호출 — 실행 도구 ──
    "EngineCall": ToolSpec(
        "EngineCall",
        "Skill OS가 선언한 DartLab canonical capabilityRef 1 회 호출 (Company.panel, scan, gather.price, dataHub.query 등). 정형 ref 반환. capability 검색 결과라도 실행 계약 밖의 Company 하위 멤버는 거부한다. **dartlab 데이터는 무조건 이것 우선**. RunPython 으로 dartlab API 를 단일 호출하는 패턴 금지. RunPython 은 EngineCall 결과의 다단 결합·랭킹·Polars 가공이 필요할 때만. **args 는 항상 dict 로 필수**. `{}` 라도 명시 (인자 0 개 capability 일 때만 빈 dict).",
        {
            "type": "object",
            "properties": {
                "apiRef": {
                    "type": "string",
                    "description": "canonical capabilityRef만. **인자는 절대 합쳐 쓰지 마라** (X: 'Company.panel TSLA IS freq=Q'). 예: 'Company.panel', 'scan', 'gather.price', 'dataHub.query'",
                },
                "args": {
                    "type": "object",
                    "description": "인자 dict — **항상 필수, 빈 dict {} 라도 명시**. Company.panel → {'stockCode': '005930', 'topic': 'IS'} (stockCode 필수). scan → {'axis': 'growth'}. macro → {}. **stockCode·target·topic·axis 같은 키를 plan root 가 아닌 *args 안에* 넣어라**.",
                    "additionalProperties": True,
                },
            },
            "required": ["apiRef", "args"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "RunPython": ToolSpec(
        "RunPython",
        "**EngineCall 결과 후처리·다단 조합 전용**. Polars group_by / sort / 시계열 / 여러 회사 비교처럼 단일 capability 로 못 푸는 가공일 때만. **dartlab API 를 여기서 1 회 호출하는 패턴 절대 금지** — `dartlab.scan(...)` / `Company('xxx').panel(...)` 같은 단일 호출은 EngineCall 의 일이다. 결과는 emit_result(table=..., values=..., date=...) keyword 형식 (dict 한 개 positional 도 자동 unpack). 사용 가능 변수: dartlab, pl(polars), normalizeColumn, columnsFor, availableTopics.",
        {
            "type": "object",
            "properties": {"code": {"type": "string"}, "runId": {"type": "string"}},
            "required": ["code"],
        },
        # 임의 코드 실행 — read-only 라 단정 못 함 (사용자 코드가 SaveArtifact 같은 도구 우회 가능).
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
    "InspectDataset": ToolSpec(
        "InspectDataset",
        "dataset schema·행 수·최신 관측·샘플 빠르게 확인. RunPython 코드 짜기 전 컬럼 추측 실패 방지용.",
        {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "예: 'Company.panel:005930:BS', 'scan:profitability', 'macro', 'gather:price:005930'",
                },
                "sampleRows": {"type": "integer"},
            },
            "required": ["target"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    # ── 파일·외부 ──
    "Read": ToolSpec(
        "Read",
        "안전 경로 (repo, 사용자 artifacts) 안의 텍스트 파일을 읽어 docRef 발급. 사용자 보고서·블로그 본문·skill body 직접 인용 시.",
        {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "절대 경로 또는 repo 기준 상대 경로"},
                "startLine": {"type": "integer"},
                "endLine": {"type": "integer"},
            },
            "required": ["target"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "WebSearch": ToolSpec(
        "WebSearch",
        "외부 최신 정보 (오늘 종가, 신규 공시, 컨센서스). dartlab 내부 데이터엔 EngineCall/RunPython.",
        {
            "type": "object",
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        },
        # 외부 검색 — 결과가 외부 환경 (web) 의존, idempotent 아님, openWorld True.
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
    "ExternalReachDoctor": ToolSpec(
        "ExternalReachDoctor",
        "외부 조사 backend 상태 진단. WebSearch 실패/차단/0건 후 재시도 전에 현재 살아있는 WebSearch/Jina/GitHub/optional Exa 경로를 확인한다. 설치·로그인·쿠키 저장은 하지 않는 read-only doctor.",
        {
            "type": "object",
            "properties": {
                "timeoutSec": {"type": "integer", "description": "backend별 timeout 초. 1..30으로 clamp."},
                "skipNetwork": {
                    "type": "boolean",
                    "description": "True면 HTTP probe를 건너뛰고 로컬 command status만 확인.",
                },
            },
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
    # ── 산출 ──
    "SaveArtifact": ToolSpec(
        "SaveArtifact",
        "큰 표 (>50 rows)·차트·긴 텍스트를 사용자 홈 안전 경로에 저장 → artifactRef. 짧은 답변 본문엔 쓰지 말 것.",
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "content": {"type": "string"},
                "kind": {"type": "string"},
            },
            "required": ["name", "content"],
        },
        # 디스크 쓰기 — 사용자 홈 ~/.dartlab/artifacts/ 에 새 파일 생성. 같은 이름 두 번 호출 시
        # 덮어쓰기 가능 (idempotent 아님). destructive 는 아니지만 read-only 도 아님.
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
    "CreateUserSkill": ToolSpec(
        "CreateUserSkill",
        "사용자 요청으로 프로젝트 로컬 user skill 초안을 `.dartlab/skills` 아래에 작성. 공식 `src/dartlab/skills/specs` 는 절대 변경하지 않음. 엔진 capability 가 있으면 EngineCall 우선, RunPython 은 fallback 절차가 명시될 때만.",
        {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "id": {
                    "type": "string",
                    "description": "선택. user.<slug> 로 정규화됨. 예: 'l15-event-watch' → user.l15-event-watch",
                },
                "purpose": {"type": "string"},
                "whenToUse": {"type": "array", "items": {"type": "string"}},
                "body": {"type": "string"},
                "capabilityRefs": {"type": "array", "items": {"type": "string"}},
                "toolRefs": {"type": "array", "items": {"type": "string"}},
                "linkedSkills": {"type": "array", "items": {"type": "string"}},
                "requiredEvidence": {"type": "array", "items": {"type": "string"}},
                "expectedOutputs": {"type": "array", "items": {"type": "string"}},
                "visualRefs": {"type": "array", "items": {"type": "string"}},
                "visualGuidance": {"type": "array", "items": {"type": "string"}},
                "incubating": {"type": "boolean"},
                "overwrite": {"type": "boolean"},
            },
            "required": ["title", "purpose"],
        },
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
    "CompileVisual": ToolSpec(
        "CompileVisual",
        "분석 결과를 차트/표 spec 으로 변환 → visualRef → 메시지 흐름에 인라인 차트 렌더. 시계열·비교·분포는 텍스트보다 이게 명확.",
        {
            "type": "object",
            "properties": {
                "chartType": {
                    "type": "string",
                    "enum": [
                        "line",
                        "bar",
                        "table",
                        "radar",
                        "waterfall",
                        "heatmap",
                        "histogram",
                        "combo",
                        "sparkline",
                        "pie",
                        "price-chart",
                    ],
                },
                "data": {
                    "type": "array",
                    "description": "행 list (예: [{date:'2024-Q1', value:100}, ...])",
                    "items": {"type": "object", "additionalProperties": True},
                },
                "title": {"type": "string"},
                "xAxis": {"type": "string"},
                "yAxis": {"type": "string"},
                "subtitle": {"type": "string"},
                "source": {"type": "string"},
            },
            "required": ["chartType", "data"],
        },
        # 메모리 spec 생성 — 디스크 쓰기 없음. 같은 입력은 같은 spec.
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    # ── 분석 추론 surfacing (workbench 내부 → registry SSOT) ──
    "LookAheadGuard": ToolSpec(
        "LookAheadGuard",
        "Company.panel 의 asOf 강제 호출 — back-test/decision reflection 시 미래 데이터 누설 차단. asOf 누락 거부.",
        {
            "type": "object",
            "properties": {
                "stockCode": {"type": "string"},
                "asOf": {"type": "string"},
                "topic": {"type": "string"},
                "market": {"type": "string", "enum": ["KR", "US"]},
                "block": {"type": "integer"},
                "period": {},
                "freq": {"type": "string"},
                "scope": {"type": "string"},
            },
            "required": ["stockCode", "asOf"],
        },
        # 분석 read — 같은 입력 같은 결과 (provider cache).
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "PeerCompareN": ToolSpec(
        "PeerCompareN",
        "N (2~12) 종목 wide-format 비교 + peer-internal percentile rank (각 metric 별 0.0~1.0, 1.0=best). 2~3 종목 비교도 본 도구 1 회. '5 개 회사 비교', '삼성 vs SK vs LG vs ...', 'A vs B' 류 질문에 1 회 호출.",
        {
            "type": "object",
            "properties": {
                "stockCodes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2~12 개 종목 코드. 초과 시 앞 12 개만.",
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "비교 metric list. 기본 8 종 (revenue/operatingProfit/netIncome/totalAssets/totalEquity/totalLiabilities/debtRatio/roe).",
                },
            },
            "required": ["stockCodes"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "CompileFinancialDashboard": ToolSpec(
        "CompileFinancialDashboard",
        "단일 종목 한 화면 dashboard — growth/value/credit 3 template 자동 spec 생성. Company.panel + _companyMetrics 재사용 + visualRef spec 박음. '대시보드', '한 화면 요약', '성장성 차트' 류 질문에 본 도구 1 회 호출.",
        {
            "type": "object",
            "properties": {
                "stockCode": {"type": "string"},
                "template": {
                    "type": "string",
                    "enum": ["growth", "value", "credit"],
                    "description": "기본 'growth'. growth=매출/영업이익/순이익, value=ROE/equity, credit=부채/안정성.",
                },
                "periods": {"type": "integer", "description": "시계열 기간 (정보성). 기본 8."},
            },
            "required": ["stockCode"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "CreditScorecard": ToolSpec(
        "CreditScorecard",
        "단일 종목 dCR 신용등급 + 1Y PD + 7 축 분석. includeFactors=True 시 Altman 적용성 점수와 Beneish 비발행 상태를 동행한다. 역사적 basePeriod에는 최신 횡단 factor를 섞지 않는다.",
        {
            "type": "object",
            "properties": {
                "stockCode": {"type": "string"},
                "basePeriod": {
                    "type": "string",
                    "description": "평가 기준 분기 ('2024Q4'/'2023'). 미지정 시 최신.",
                },
                "includeFactors": {
                    "type": "boolean",
                    "description": "Altman 적용성 원장 + Beneish available 상태 동행 (기본 False).",
                },
            },
            "required": ["stockCode"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "RegressionForecast": ToolSpec(
        "RegressionForecast",
        "단일 종목 매출 성장률 회귀 예측 (cross-section/panel 사전 적합 모델 cache load). '매출 성장 예측', '내년 매출 전망', 'regression forecast' 류 질문에 본 도구 1 회 호출. cache miss 시 model_unavailable — 사전 학습 필요.",
        {
            "type": "object",
            "properties": {
                "stockCode": {"type": "string"},
                "year": {"type": "integer", "description": "회계연도. None 시 직전 연도 자동."},
                "modelKind": {
                    "type": "string",
                    "enum": ["panel", "cross"],
                    "description": "panel=다년 안정, cross=단일 연도 횡단면. 기본 panel.",
                },
            },
            "required": ["stockCode"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "SensitivityAnalysis": ToolSpec(
        "SensitivityAnalysis",
        "단일 종목 DCF parameter grid (WACC × terminalGrowth NxM) 민감도 매트릭스 — heatmap-friendly. 'WACC 민감도', '할인율 변화', '성장률 민감도', '민감도 매트릭스' 류 질문에 본 도구 1 회 호출.",
        {
            "type": "object",
            "properties": {
                "stockCode": {"type": "string"},
                "waccRange": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "[min, max, steps] 예: [8.0, 12.0, 5]. 기본 [8.0, 12.0, 5].",
                },
                "growthRange": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "[min, max, steps] 예: [1.0, 5.0, 5]. 기본 [1.0, 5.0, 5].",
                },
                "projectionYears": {"type": "integer", "description": "초기 고성장 구간 (년). 기본 5."},
            },
            "required": ["stockCode"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "DCFValuation": ToolSpec(
        "DCFValuation",
        "단일 종목 Damodaran 2-stage DCF 내재가치 밴드 (bear/base/bull) 자동 계산. discountRate ± 100bps + terminalGrowth ± 50bps 표준 변형. '삼성전자 적정가격', 'AAPL 공정가치', 'DCF 평가' 류 질문에 본 도구 1 회 호출 — RunPython ad-hoc 회피 (token 30% 절감).",
        {
            "type": "object",
            "properties": {
                "stockCode": {"type": "string", "description": "6 자리 KR 또는 US ticker."},
                "wacc": {
                    "type": "number",
                    "description": "할인율 (%). 미지정 시 sectorParams.discountRate.",
                },
                "terminalGrowthRate": {
                    "type": "number",
                    "description": "영구성장률 (%). 미지정 시 min(sectorGrowth, 3.0).",
                },
                "projectionYears": {"type": "integer", "description": "초기 고성장 구간 (년). 기본 5."},
                "scenarios": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["bear", "base", "bull"]},
                    "description": "기본 3 종 전체. 일부만 필요 시 명시.",
                },
            },
            "required": ["stockCode"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "ScenarioCompareN": ToolSpec(
        "ScenarioCompareN",
        "macro 시나리오 N (2~5) 개 baseline 대비 동시 비교 — score_delta + cycle_phase + crisis_zone 매트릭스. '여러 시나리오 비교', '스트레스 테스트', '최악 케이스' 류 질문에 본 도구 1 회 호출.",
        {
            "type": "object",
            "properties": {
                "scenarioNames": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2~5 시나리오 이름 (예: ['2008 금융위기', '금리 충격']).",
                },
                "severity": {
                    "type": "string",
                    "enum": ["mild", "moderate", "severe", "extreme", ""],
                    "description": "모든 시나리오 공통 심각도.",
                },
                "market": {"type": "string", "enum": ["KR", "US", ""]},
            },
            "required": ["scenarioNames"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
    "ScenarioOverlay": ToolSpec(
        "ScenarioOverlay",
        "macro 시나리오 preset (146 종 — 1997 IMF / 2008 GFC / Fed DFAST 등) 의 macro overrides 와 업종 탄성치 결합 → 종목별 매출/마진/NIM 임팩트 거친 추정. '금리 +50bp 면?' 류 질문에 답변 본문 옵션 1 회 호출.",
        {
            "type": "object",
            "properties": {
                "scenarioName": {
                    "type": "string",
                    "description": "preset 이름 (예: 'asia_crisis', 'semiconductor_downturn')",
                },
                "stockCode": {"type": "string"},
                "severity": {"type": "string", "enum": ["mild", "moderate", "severe", "extreme", ""]},
                "market": {"type": "string", "enum": ["KR", "US", ""]},
            },
            "required": ["scenarioName"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "PickStoryTemplate": ToolSpec(
        "PickStoryTemplate",
        "기업유형 (growth/value/credit_risk 등 9 enum) 자동 분류 + 추천 story 섹션 묶음. '이 회사 어떻게 봐?' 종합 분석 의도면 답변 흐름 잡기 전에 호출.",
        {
            "type": "object",
            "properties": {
                "stockCode": {"type": "string"},
                "question": {"type": "string"},
            },
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "EvidenceGate": ToolSpec(
        "EvidenceGate",
        "Skill OS spec 의 requiredEvidence ↔ 누적 refs 비교. 답변 합성 직전 호출 — missing ref kind 있으면 답변에 ⚠ + 한계 문장 추가 권장.",
        {
            "type": "object",
            "properties": {
                "skillId": {"type": "string"},
                "refs": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "지금까지 모은 refs (각 항목 dict, 최소 'kind' 키 포함). 빈 list 도 허용 — 검증만 수행.",
                },
            },
            "required": ["skillId"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "GroundingCheck": ToolSpec(
        "GroundingCheck",
        "답변 본문의 material claim (수치/날짜/랭킹) 분류 + ref token 매칭 검증. fake ref token 감지. workbench GATE 휴리스틱 표면화.",
        {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "refs": {
                    "type": "array",
                    "items": {"type": "object", "additionalProperties": True},
                    "description": "지금까지 모은 refs. 빈 list 도 허용.",
                },
            },
            "required": ["answer"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "SearchPastSessions": ToolSpec(
        "SearchPastSessions",
        "과거 세션 transcript (~/.claude/projects/.../*.jsonl) BM25 검색. '이 회사 분석한 적 있나' · '이 매핑 결정 어디서 했지' 류 cross-session recall. rebuild=True 면 호출 전 전체 재인덱싱.",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "자유형 검색어. 공백 분리 토큰 AND 매칭."},
                "limit": {"type": "integer", "description": "반환 hit 수 (1-50, 기본 10)"},
                "role": {"type": "string", "enum": ["user", "assistant"], "description": "역할 필터. 생략 시 둘 다."},
                "rebuild": {
                    "type": "boolean",
                    "description": "True 면 호출 전 ~/.claude/projects/ 전체 재인덱싱 (느림). 기본 False — 기존 인덱스만.",
                },
            },
            "required": ["query"],
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "RequestUserInput": ToolSpec(
        "RequestUserInput",
        "ambiguity 만났을 때 사용자에게 schema 있는 structured 입력 요청 (MCP elicit_form). MCP 컨텍스트 전용 — non-MCP 시 자연어 fallback 권장.",
        {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "type": {"type": "string"},
                            "enum": {"type": "array", "items": {"type": "string"}},
                            "required": {"type": "boolean"},
                        },
                        "required": ["name"],
                    },
                },
            },
            "required": ["message"],
        },
        # 사용자에게 묻기 — read tool 분류 (외부 의존성 있음 — 사용자 응답이 외부 입력).
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
    # ── recipe lifecycle (chat-native, graph node X) ──
    "ListEngineGaps": ToolSpec(
        "ListEngineGaps",
        "recipe 카탈로그에서 다리 ≤ minBridges 인 엔진 페어 + 샘플 질문 반환. ProposeRecipe 의 입력 가이드.",
        {
            "type": "object",
            "properties": {
                "engines": {"type": "array", "items": {"type": "string"}},
                "minBridges": {"type": "integer", "default": 1},
                "limit": {"type": "integer", "default": 30},
            },
        },
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    "ProposeRecipe": ToolSpec(
        "ProposeRecipe",
        "recipes.<category>.<slug> markdown spec 1 건 신규 작성 (status=drafted). gap.primary ≥ 2 + falsifier.description 강제. 승격은 운영자 CLI 단독.",
        {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "purpose": {"type": "string"},
                "gap": {"type": "object"},
                "falsifier": {"type": "object"},
                "expectedNovelty": {"type": "array", "items": {"type": "string"}},
                "testUniverse": {"type": "object"},
                "linkedSkills": {"type": "array", "items": {"type": "string"}},
                "requiredEvidence": {"type": "array", "items": {"type": "string"}},
                "body": {"type": "string"},
            },
            "required": ["id", "title", "gap", "falsifier"],
        },
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
    "ValidateRecipe": ToolSpec(
        "ValidateRecipe",
        "recipe 1 건을 testUniverse target 들에 직렬 실행 (≤5 종목, Polars 메모리 가드) + 6 신호 scorecard. status 자동 변경 X — 승격은 운영자 CLI.",
        {
            "type": "object",
            "properties": {
                "skillId": {"type": "string"},
                "targets": {"type": "array", "items": {"type": "string"}},
                "asOf": {"type": "string"},
                "maxTargets": {"type": "integer", "default": 5},
                "capture": {"type": "boolean", "default": True},
            },
            "required": ["skillId"],
        },
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
    # ── elevate (옵션 sub-agent) ──
    "RunWorkbench": ToolSpec(
        "RunWorkbench",
        "깊은 분석을 5 패스 (BRIEF/WORK/CRITIQUE/COMPOSE/GATE/HARVEST) 작업대로 elevate. 회사 종합 분석·skill 절차 의존·ref 검증 강제 필요할 때만.",
        {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "stockCode": {"type": "string"},
                "market": {"type": "string", "enum": ["KR", "US"]},
            },
            "required": ["question"],
        },
        # 5 패스 elevate — 내부에서 RunPython / SaveArtifact 호출 가능. read-only 단정 X.
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
}

_TOOLS: dict[str, ToolFn] = {
    "ReadSkill": readSkill,
    "GetSkillBody": getSkillBody,
    "ReadSkillMarket": readSkillMarket,
    "ReadCapability": readCapability,
    "EngineCall": engineCall,
    "EvidenceGate": evidenceGate,
    "PickStoryTemplate": pickStoryTemplate,
    "PeerCompareN": peerCompareN,
    "CompileFinancialDashboard": compileFinancialDashboard,
    "CreditScorecard": creditScorecard,
    "RegressionForecast": regressionForecast,
    "SensitivityAnalysis": sensitivityAnalysis,
    "DCFValuation": dcfValuationTool,
    "ScenarioCompareN": scenarioCompareN,
    "ScenarioOverlay": scenarioOverlay,
    "RunPython": runPython,
    "InspectDataset": inspectDataset,
    "Read": readFile,
    "WebSearch": webSearch,
    "ExternalReachDoctor": externalReachDoctor,
    "SaveArtifact": saveArtifact,
    "CreateUserSkill": createUserSkill,
    "CompileVisual": compileVisual,
    "LookAheadGuard": lookAheadGuard,
    "GroundingCheck": groundingCheck,
    "RequestUserInput": requestUserInput,
    "ListEngineGaps": listEngineGaps,
    "ProposeRecipe": proposeRecipe,
    "ValidateRecipe": validateRecipe,
    "RunWorkbench": runWorkbench,
    "SearchPastSessions": searchPastSessions,
}

CANONICAL_TOOL_NAMES = tuple(_SPECS.keys())

# chat-native LLM 노출 default. ReadSkill 부터 시작 권장 (system prompt 가 순서 안내).
# GetSkillBody 는 ReadSkill 후보 압축한 뒤 단일 skill 본문 fetch — 두 단계 호출 루틴.
CANONICAL_V2: tuple[str, ...] = (
    "ReadSkill",
    "GetSkillBody",
    "ReadSkillMarket",
    "ReadCapability",
    "EngineCall",
    "RunPython",
    "Read",
    "WebSearch",
    "ExternalReachDoctor",
    "SaveArtifact",
    "CreateUserSkill",
    "CompileVisual",
    "PeerCompareN",
    "DCFValuation",
    "CompileFinancialDashboard",
    "RegressionForecast",
    "SensitivityAnalysis",
    "CreditScorecard",
    "ScenarioCompareN",
    "ScenarioOverlay",
    "SearchPastSessions",
)

# snake_case ↔ PascalCase 호환 — 옛 호출자 / 옛 model 가 snake 로 부르면 자동 매핑.
_LEGACY_NAME_MAP = {
    "read_skill": "ReadSkill",
    "get_skill_body": "GetSkillBody",
    "read_skill_market": "ReadSkillMarket",
    "read_capability": "ReadCapability",
    "engine_call": "EngineCall",
    "evidence_gate": "EvidenceGate",
    "pick_story_template": "PickStoryTemplate",
    "peer_compare_n": "PeerCompareN",
    "dcf_valuation": "DCFValuation",
    "credit_scorecard": "CreditScorecard",
    "sensitivity_analysis": "SensitivityAnalysis",
    "compile_financial_dashboard": "CompileFinancialDashboard",
    "regression_forecast": "RegressionForecast",
    "scenario_compare_n": "ScenarioCompareN",
    "scenario_overlay": "ScenarioOverlay",
    "run_python": "RunPython",
    "inspect_dataset": "InspectDataset",
    "read": "Read",
    "web_search": "WebSearch",
    "external_reach_doctor": "ExternalReachDoctor",
    "save_artifact": "SaveArtifact",
    "create_user_skill": "CreateUserSkill",
    "compile_visual": "CompileVisual",
    "lookahead_guard": "LookAheadGuard",
    "grounding_check": "GroundingCheck",
    "request_user_input": "RequestUserInput",
    "run_workbench": "RunWorkbench",
    "list_engine_gaps": "ListEngineGaps",
    "propose_recipe": "ProposeRecipe",
    "validate_recipe": "ValidateRecipe",
}


def toolSpecs(provider: Any = None) -> list[dict[str, Any]]:
    """설치형 에이전트와 MCP가 공유하는 provider 중립 JSON Schema 목록."""
    if provider is not None:
        raise ValueError("provider별 schema 변환은 제거되었습니다. generic MCP schema를 사용하세요")
    return [spec.toDict() for spec in _SPECS.values()]


def listToolNames() -> tuple[str, ...]:
    """현재 등록된 모든 tool name (canonical + plugin) tuple."""
    return tuple(_SPECS.keys())


def isToolReadOnly(name: str) -> bool:
    """도구가 read-only 인지 (ToolSpec.readOnlyHint True). agent 의 병렬 fan-out 분기 판단.

    snake/PascalCase 양쪽 인식. 미등록 도구는 보수적 False (병렬 X).
    readOnlyHint=None (미선언) 도 보수적 False — 명시 True 인 경우만 병렬 그룹.
    """
    canonical = _LEGACY_NAME_MAP.get(name, name)
    spec = _SPECS.get(canonical)
    if spec is None:
        return False
    return spec.readOnlyHint is True


def registerTool(
    name: str,
    func: Callable[..., Any],
    *,
    description: str | None = None,
    inputSchema: dict[str, Any] | None = None,
) -> None:
    """plugin tool 등록 — name + 함수 + schema (canonical 이름 덮어쓰기 차단)."""
    # Legacy snake 이름 (read_skill 등) 도 canonical PascalCase 로 정규화해 보호 — plugin
    # 이 옛 이름으로 우회 등록하면 canonical 도구가 silently 덮어씌워지는 회귀 가능.
    canonical = _LEGACY_NAME_MAP.get(name, name)
    if canonical in CANONICAL_TOOL_NAMES:
        raise ValueError(f"canonical tool은 plugin으로 덮어쓸 수 없습니다: {name} (-> {canonical})")
    _SPECS[name] = ToolSpec(
        name,
        description or inspect.getdoc(func) or f"{name} plugin tool",
        inputSchema or _schemaFromSignature(func),
    )

    def _wrapped(**kwargs: Any) -> ToolResult:
        try:
            result = func(**kwargs)
        except Exception as exc:  # pragma: no cover - defensive plugin boundary
            return ToolResult(False, f"{name} plugin tool 실패: {exc}", error=type(exc).__name__)
        if isinstance(result, ToolResult):
            return result
        return ToolResult(True, f"{name} plugin tool 실행 완료", data={"result": result})

    _TOOLS[name] = _wrapped


def unregisterTool(name: str) -> None:
    """plugin tool 등록 해제 (canonical 이름은 보호 — ValueError)."""
    canonical = _LEGACY_NAME_MAP.get(name, name)
    if canonical in CANONICAL_TOOL_NAMES:
        raise ValueError(f"canonical tool은 해제할 수 없습니다: {name} (-> {canonical})")
    _SPECS.pop(name, None)
    _TOOLS.pop(name, None)


def executeTool(name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    """tool name + args → 등록된 함수 호출 → ToolResult.toDict() 반환."""
    canonical = _LEGACY_NAME_MAP.get(name, name)
    if canonical not in _TOOLS:
        return ToolResult(False, f"Unknown tool: {name}", error="unknown_tool").toDict()
    payload = dict(args or {})
    filtered = _filterKwargs(_TOOLS[canonical], payload)
    result = _TOOLS[canonical](**filtered)
    return result.toDict()


def _filterKwargs(func: Callable[..., Any], payload: dict[str, Any]) -> dict[str, Any]:
    try:
        sig = inspect.signature(func)
    except (TypeError, ValueError):
        return payload
    accepts_var_kw = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    if accepts_var_kw:
        return payload
    known = {p.name for p in sig.parameters.values() if p.kind is not inspect.Parameter.VAR_POSITIONAL}
    return {k: v for k, v in payload.items() if k in known}


def _schemaFromSignature(func: Callable[..., Any]) -> dict[str, Any]:
    properties: dict[str, dict[str, Any]] = {}
    required: list[str] = []
    for param in inspect.signature(func).parameters.values():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        properties[param.name] = {"type": _jsonType(param.annotation)}
        if param.default is inspect.Parameter.empty:
            required.append(param.name)
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def _jsonType(annotation: Any) -> str:
    if annotation in (int, "int"):
        return "integer"
    if annotation in (float, "float"):
        return "number"
    if annotation in (bool, "bool"):
        return "boolean"
    if annotation in (list, "list"):
        return "array"
    if annotation in (dict, "dict"):
        return "object"
    return "string"
