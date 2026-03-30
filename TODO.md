# TODO

## 테스트 인프라

- [x] fixture 기반 테스트 헬퍼 (`tests/fixtureHelper.py`) — 2026-03-30
- [x] heavy 테스트 fixture 전환 (bsIdentity, mappingBenchmark, regressionFinance) — 2026-03-30
- [x] 벤치마크 fixture 생성 스크립트 (`scripts/generateFixtures.py`) — 2026-03-30
- [ ] 나머지 integration 테스트 중 불필요한 Company 로드 개선

## AI 엔진

### 2026-03-30 완료 — 시스템 프롬프트 대폭 간소화
- [x] 시스템 프롬프트: 수천 토큰 교과서 → 30줄 사용설명서 (CAPABILITIES + 도구 우선순위)
- [x] 제거: Self-Verification, autoInjectArtifacts, navigate, _classify_question, Few-shot, 업종벤치마크, 7단계 프레임워크
- [x] ask() 시그니처: company 필수 → question만으로 동작 (company는 optional keyword)
- [x] 도구 우선순위 명시: 1차(review/scan/gather) → 2차(Company 직접)

### 남은 과제
- [ ] **코드 실행 진행 이벤트** — _streamWithCodeExecution 라운드마다 "코드 실행 1/5..." 이벤트 emit. EventKind 정의 + CLI/SSE 소비 코드 이미 있음, 발화만 연결
- [ ] **반복 루프 감지** — 코드 실행 루프에서 동일/유사 코드 반복 감지 (Jaccard). 현재 maxRounds=5 하드 리밋만
- [ ] **전달 품질** — 엔진 출력을 LLM이 읽기 좋게 (주입 아님, 독스트링 해상도). 토론 중
- [ ] SKILL.md 워크플로우 외부화 — 분석 축 늘어나면 검토

## DX 개선

- [ ] Fetcher 프로토콜 명시화 — provider 내부 Transform-Extract-Transform 3단계 표준화. EDINET 추가 시점에 도입
- [ ] 타입 스텁 자동 생성 — `generateSpec.py` 확장해서 `.pyi` 스텁 생성, IDE 자동완성 완벽 지원
- [ ] 필드 중복 감지 CI — DART/EDGAR 간 accountMappings 정합성 자동 검증
- [ ] 통합 반환 래퍼 — 모든 공개 API가 동일한 래퍼(결과+출처+경고) 반환. Polars DataFrame 설계와 충돌 가능, 신중하게
