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
- [x] **코드 실행 진행 이벤트** — EventKind.CODE_ROUND + CLI 스피너 "코드 실행 1/5..." (2026-03-30)
- [x] **반복 루프 감지** — SequenceMatcher 유사도 85% 이상이면 조기 종료 (2026-03-30)
- [ ] **코드 실행 결과 품질** — 실행 결과가 잘려도 LLM이 맥락을 이해하도록 결과 포맷 개선. 토론 중
- [x] SKILL.md 워크플로우 외부화 — templates/skills 전부 disconnected, 시스템 프롬프트 30줄로 대체 (2026-03-30)

### 금융 AI 오픈소스 조사 기반 (2026-03-30, FinGPT/FinRobot/FinRL/CrewAI)

> dartlab 원칙: CAPABILITIES-Driven — AI가 도구를 검색·선택·실행·해석. 엔진은 도구를 제공.

**바로 효과 큰 것:**
- [ ] **AI 평가 체계** — ask() 품질을 정량 측정할 방법이 없음. `project_ai_eval_plan.md` 과제와 직결
  - **프레임워크**: DeepEval (MIT, pytest 네이티브) 1순위. Promptfoo (YAML 선언형) 보조
  - **평가 3축**: (1) 수치 정확도 — 답변 내 수치를 엔진 직접 실행 결과와 비교 (2) 근거 앵커링 — 언급 수치가 실제 데이터 출처에 존재하는지 (3) 분석 논리성 — G-Eval(자연어 기준 LLM-as-judge)로 채점
  - **커스텀 메트릭**: DeepEval BaseMetric 상속 → NumericalAccuracy, SourceAnchoring, AnalyticalCoherence 3개
  - **기간 귀속 정확성** 필수 검증 — "2024년 영업이익"이 실제 2024년 수치인지 (금융 LLM 핵심 실패 패턴, FailSafeQA 벤치마크 참고)
  - **데이터셋**: Golden(input + company + expected_numbers + expected_topics) JSON, Git 관리. Synthesizer로 초기 부트스트래핑
  - **CI 통합**: `bash scripts/test-lock.sh tests/ -m "eval" -v` — 기존 테스트 인프라와 동일 패턴
  - **비용**: GPT-4o-mini judge 기준 테스트 100개 × 메트릭 3개 = ~$1-3. 로컬 Ollama judge도 가능 (한국어 채점 품질은 열위)
  - **Ragas 보류**: RAG retrieval 평가 특화인데 dartlab은 코드 실행 기반. 향후 공시 RAG 추가 시 재검토
- [ ] **공시 RAG** — 현재 `/api/company/{code}/search`는 substring 검색만 지원. "삼성전자가 AI 투자에 대해 뭐라고 했지?" 같은 의미 기반 자유형 질문 불가
  - **핵심 이점**: sections가 이미 topic × period로 구조화 → RAG에서 가장 비용 큰 "전처리/청킹" 단계 불필요. 임베딩만 추가하면 됨
  - **스택**: ChromaDB persistent (로컬, 외부 의존성 제로) + BGE-M3-Korean (한국어 최적화, 8192토큰, 로컬 무료)
  - **LlamaIndex/LangChain 불필요**: sections가 이미 구조화되어 Loader/Splitter 필요 없음. `chromadb` + `sentence-transformers` 두 패키지만 추가
  - **파이프라인**: sections unpivot(wide→long) → 메타데이터(stockCode, topic, period, blockType) 추출 → Chroma add → 쿼리 시 메타데이터 필터 + 의미 검색 동시 수행
  - **AI 도구 통합**: `searchSections(query, stockCode?, period?)` tool로 노출 → AI가 자유형 질문 시 자동 호출
  - **lazy 인덱싱**: 첫 자유형 질문 시 해당 종목만 임베딩 (dartlab lazy load 원칙). PersistentClient로 디스크 캐시
  - **메모리 주의**: BGE-M3-Korean 568M → ~1.5GB RAM. dartlab 800MB pressure 규칙과 충돌 가능 → 임베딩 후 모델 해제 또는 경량 모델(all-MiniLM-L6-v2, 22M)로 시작
  - **확장**: 금융 용어 정확도 필요 시 LangChain EnsembleRetriever(BM25+벡터 하이브리드) 추가. FinSage 논문에서 하이브리드가 벡터 단독 대비 일관 우수 확인

**단계적 도입:**
- [ ] **공시 영향도 자동 태깅 (RLSP 개념)** — FinGPT의 핵심 혁신. 뉴스/공시 발행 후 주가 변동을 보상 신호로 사용해서 긍정/부정/중립 자동 라벨링 (사람 라벨링 불필요). dartlab에서는 gather(주가) + docs(공시 시점)을 조합해서 "이 공시가 시장에 어떤 반응을 일으켰는지" 자동 태깅. insights/grading의 데이터 근거로 활용
- [ ] **리포트 차트 고도화** — FinRobot은 리포트에 차트 11종 자동 삽입 (밸류에이션 감도 히트맵, 피어 비교 레이더, 기술 지표). dartlab review()에 분석 결과 기반 차트 자동 삽입 강화
- [ ] **역할별 해석 프롬프트** — _buildSystemPrompt에 role 파라미터로 "재무분석가 관점" vs "리스크분석가 관점" 분기. 효과 실험 후 도입

**장기 검토:**
- [ ] **선언형 분석 워크플로우** — 분석 파이프라인을 설정 파일로 외부화. 현재 시스템 프롬프트 30줄로 충분하지만, 분석 축 확장 시 재검토

## Review 출력 개선

### 2026-03-30 완료 — 출력 구조 개편 5단계
- [x] Thread 중복 제거 — 섹션 내 story 반복 삭제, 상단 순환 서사에서 1회만 표시
- [x] Helper 용어 강화 — HHI, ROE, CCC, Z-Score 등 전문용어에 괄호 해설 추가
- [x] Executive Summary — 최상단 요약 카드 (한줄결론 + 등급 + 강점3 + 경고3)
- [x] Detail 모드 — `detail=False`로 섹션 요약만 표시, Section에 summary 필드
- [x] 프리셋 시스템 — `preset="audit"/"executive"/"credit"/"growth"/"valuation"`

### 남은 과제
- [x] **FlagBlock 분류 정확도** — `_flagsBlock`에 키워드 기반 긍정/경고 자동 분류 적용 (2026-03-30)
- [x] **섹션 summary 품질 검증** — 삼성전자(제조), KB금융(금융) 검증 완료. 15개 섹션 모두 고유 핵심 정보 추출 확인 (2026-03-30)
- [ ] **금융업 분석 오진** — Analysis 갭 섹션으로 이동 (아래 참조)

## Analysis 분석관점 갭 (2026-03-30 진단)

> 110+ calc 함수 vs CFA/Palepu-Healy/McKinsey 대조 결과

**즉시 (데이터 있고 비용 낮음):**
- [x] **금융업 오진** — grading.py leverage skip, stability.py 부채비율 금융업 기준, capital.py Altman Z/IC 금융업 제외 (2026-03-30)
- [x] **세그먼트 수익성** — calcSegmentComposition에 opMargin 필드 추가 (2026-03-30)
- [x] **세금 해석 flag** — 3기 연속 저세율, 유효세율 변동성, DTA 3기 연속 증가 flag 추가 (2026-03-30)

**중기 (새 calc 함수 필요):**
- [ ] **비경상 항목 분리** — IS 영업외수익/비용 세부 항목 추출, 핵심이익(Core Earnings) 산출. earningsQuality.py
- [ ] **관계사/특수관계자 거래** — report relatedPartyTransaction에서 관계사 매출의존도 추출. governance.py 확장
- [ ] **피어 직접 비교** — 시장 백분위만 있고 "A vs B" 직접 비교표 없음. scan 데이터 활용. peerBenchmark.py

**장기 (연구 필요):**
- [ ] **매크로-기업 민감도** — gather 매크로 50+지표와 기업 특성(수출비중/차입금비율) 연결. 섹터별 탄성치 필요

## DX 개선

- [ ] Fetcher 프로토콜 명시화 — provider 내부 Transform-Extract-Transform 3단계 표준화. EDINET 추가 시점에 도입
- [ ] 타입 스텁 자동 생성 — `generateSpec.py` 확장해서 `.pyi` 스텁 생성, IDE 자동완성 완벽 지원
- [ ] 필드 중복 감지 CI — DART/EDGAR 간 accountMappings 정합성 자동 검증
- [ ] 통합 반환 래퍼 — 모든 공개 API가 동일한 래퍼(결과+출처+경고) 반환. Polars DataFrame 설계와 충돌 가능, 신중하게
