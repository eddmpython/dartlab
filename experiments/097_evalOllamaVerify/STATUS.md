# 097 Eval Ollama 검증

## 목표
55개 personaCases + sections topic별 직접 검증으로 AI 품질 약점을 찾고 개선한다.

## 실험 목록
| # | 파일 | 내용 | 상태 |
|---|------|------|------|
| 001 | criticalHighBatch.py | critical+high 35건 자동 배치 | ✅ 완료 |
| 002 | mediumBatch.py | medium 20건 자동 배치 | ✅ 완료 |
| 003 | sectionsDeepVerify.py | sections topic별 직접 질문→답변 검증 | ✅ 완료 |

## 001+002 자동 배치 (55건)

| 지표 | 값 |
|------|-----|
| 평균 overall | 8.95 |
| route 정확도 | 98% (54/55) |
| PASS율 | 54/55 (98%) |
| 모듈 활용률 | 55% |
| ERROR | 1건 → **수정 완료** (report year 파싱 버그) |

## 003 직접 검증 (15건) — 핵심 발견

### 판정 요약
| 판정 | 건수 | 비율 |
|------|------|------|
| ✅ 양호 | 8 | 53% |
| ⚠️ 수치 의심/부분 | 4 | 27% |
| ❌ 심각한 문제 | 3 | 20% |

### ❌ AI가 dartlab을 제대로 못 쓰는 경우 (즉시 수정 대상)

| topic | 증상 | 원인 |
|-------|------|------|
| fsSummary | "재무데이터 없음" 응답 | finance 데이터가 context에 미주입 |
| mdnaOverview | 빈 답변 | sections 경영진단의견이 context에 전달 안 됨 |
| executivePay | "데이터 미포함" 응답 | report API 데이터가 context에 미포함 |

### ⚠️ hallucination 의심

| topic | 증상 |
|-------|------|
| rawMaterial | 국내35%/해외65% 수치 출처 불명 |
| productService | TV 308.6조 수치 의심 |
| liquidityAndCapitalResources | 같은 질문인데 다른 세션에서 부채비율 45.2% vs 65.3% |

### ✅ 정상 동작 확인

companyOverview, dividend, businessOverview, riskDerivative, consolidatedNotes, majorHolder (6건 정확한 수치 + sections 활용)

## 수정 완료

1. ✅ `report/extract.py` year 파싱 버그 — str→i32 변환 시 비숫자("제54기", "-") 처리
2. ✅ `runtime/core.py` tool calling 차단 해제 — `use_guided`가 `tool_capable`을 막던 버그
   - 변경 전: `tool_capable = not use_guided and ...` → ollama에서 94개 도구 전혀 호출 불가
   - 변경 후: `tool_capable` 독립 판정, `use_guided`는 tool 불가능 시 fallback으로만 사용
3. ✅ `runtime/standalone.py` tool calling 활성화 — `use_tools=False` → `True`
4. ✅ `runtime/agent.py` tool 결과 후 답변 직접 반환 — `stream()` 재생성 대신 `response.answer` 직접 yield

### 수정 후 재검증 (3건)

| topic | 이전 | 수정 후 | tool 호출 |
|-------|------|---------|----------|
| fsSummary | "재무데이터 없음" | 4118자 BS 데이터 포함 답변 | `get_data` × 2 |
| mdnaOverview | 빈 답변 | 348자 답변 (topic 접근은 부정확) | `show_topic` × 2 |
| executivePay | "데이터 미포함" | 1766자 임원 구성 분석 | `get_report_data` × 1 |

## 남은 품질 문제

### LLM tool 선택/파라미터 정확도
- fsSummary: 최근 3년이 아닌 과거 데이터(2014-2018) 접근 — tool 파라미터 문제
- mdnaOverview: 경영진 분석이 아닌 "주요 제품 및 서비스" topic 접근 — topic 선택 오류
- executivePay: 보수 총액/개인별 보수가 아닌 임원 목록만 반환 — apiType 지정 부정확
- qwen3 thinking 토큰(`<think>`) 답변에 노출 — 필터링 필요

### 중기 (hallucination 방지)
1. context에 정확한 테이블이 없으면 "데이터 부족" 명시 — 추정값 생성 방지
2. 답변 내 수치 vs 실제 finance/report 데이터 교차검증 post-check

### 장기 (추가 기능)
3. sections topic별 context 주입 커버리지 맵 자동 생성
4. "근거 인용" 강화 — 어떤 section/period에서 왔는지 출처 명시
5. EDGAR finance 데이터 연결 (AAPL 등 미국 기업)
6. `<think>` 태그 필터링 (qwen3 등 thinking 모델 대응)
