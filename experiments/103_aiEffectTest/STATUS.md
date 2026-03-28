# 103_aiEffectTest — AI 재설계 효과 테스트

## 실험 목록

| ID | 실험명 | 상태 | 핵심 결과 |
|----|--------|------|----------|
| 001 | compact map + 도구 체제 검증 | 완료 | 4/4 통과 (OAuth-Codex), 1차 Ollama는 1/4 |
| 002 | _generatedCatalog Super Tool 최적화 | 완료 | 4/4 통과 + 토큰 75% 절감, 연쇄 패턴 개선 |

## 001 최종 결과

### 2차 검증 (OAuth-Codex) — 4/4 PASS

| 시나리오 | 도구 호출 | 시간 | 응답 |
|---------|----------|------|------|
| 1. 단일기업 수익성 | finance(data/ratios/decompose) + explore(search) | 40s | 2479자 |
| 2. 기업비교 매출 | market(scanAccount x2 + scanRatio) | 36s | 2017자 |
| 3. 전종목 ROE | market(scanRatio + benchmark) | 25s | 1903자 |
| 4. 공시변화 | analyze(watch) + explore(diff x2 + search + show) | 36s | 2352자 |

### 수정 사항 (테스트 중 발견)
1. `_analyze_inner()`에 `companies` 파라미터 전달 누락 수정
2. 시스템 프롬프트 "도구 사용 강제" 규칙 추가
3. `isDartFilingQuestion()` 공시 변화 질문 오탐 방지
4. provider 미명시 시 Ollama fallback 문제 발견

### 핵심 결론
- compact map + 도구 체제 정상 동작
- provider 품질이 핵심 변수 (ChatGPT >> Ollama)
- 기업 비교에서 scanAccount/scanRatio 사용 성공 (Company N개 로드 불필요)

## 002 최종 결과

### 토큰 효율 (PASS)
| 항목 | 개선 전 | 개선 후 | 절감 |
|------|--------|--------|------|
| 카탈로그 | 20,872자 (~5,218 토큰) | 5,145자 (~1,286 토큰) | 75% |
| 전체 프롬프트 대비 | ~58% | 34.2% | -24pp |

### 도구 품질 (4/4 PASS)
| 시나리오 | 도구 호출 | 시간 | 응답 |
|---------|----------|------|------|
| 1. 단일기업 수익성 | finance 5 + explore 4 = 9건 | 63.6s | 4369자 |
| 2. 기업비교 매출 | market 5 + finance 1 = 6건 | 48.9s | 2139자 |
| 3. 전종목 ROE | market 3건 | 208.8s | 1509자 |
| 4. 공시변화 | analyze 1 + explore 5 = 6건 | 54.9s | 3796자 |

### 파라미터 정확도
- 24건 중 1건 오류 (4.2%) — LLM self-correct로 실질 100%

### 001 대비 개선
- 카탈로그 크기 -75%, 평균 도구 호출 +60% (더 풍부한 분석)
- 연쇄 패턴 가이드 효과: finance->explore, changes->diff 자동 전환 관측
