# docs/ 현황

## 구조
```
docs/
├── index.md                      # 메인 페이지 (리다이렉트용)
├── getting-started/
│   ├── installation.md           # 설치 가이드
│   └── quickstart.md             # 빠른 시작 (첫 화면)
├── user-guide/
│   └── bridge-matching.md        # Bridge Matching 상세
├── api/
│   ├── overview.md               # API 전체 개요 (property + Notes + get)
│   ├── finance-summary.md        # fsSummary 모듈 상세
│   ├── finance-statements.md     # statements 모듈 상세
│   └── finance-others.md         # 전체 모듈 상세 (36개 property)
└── tutorials/
    ├── index.md                  # 튜토리얼 인덱스
    ├── 01_quickstart.md          # 첫 분석 (property 접근, all, guide)
    ├── 02_financial.md           # 재무 심화 (배당, 직원, 최대주주, Notes)
    ├── 03_disclosure.md          # 공시 텍스트 (사업, MD&A, 개요)
    └── 04_advanced.md            # 고급 분석 (Notes, 유형자산, 거버넌스)
```

## 렌더링
- SvelteKit + mdsvex로 마크다운 렌더링
- shiki로 코드 하이라이팅 (github-dark 테마)
- landing/ 안에서 @docs alias로 참조
- /docs 접속 시 quickstart로 자동 리다이렉트

## 배포
- GitHub Actions (`docs.yml`)로 자동 배포
- SvelteKit 단일 빌드 (랜딩 + 문서 통합)
- URL: https://eddmpython.github.io/dartlab/docs/

## 진행 상태
- [x] 기본 구조
- [x] 시작하기 (설치, 빠른 시작) — property API 반영
- [x] Bridge Matching 가이드 — 4단계 매칭, 상수 포함
- [x] API Overview — Company 클래스, 40개 property, Notes, get()
- [x] finance.summary 상세 — AnalysisResult, BridgeResult, Segment
- [x] finance.statements 상세 — StatementsResult, fsSummary vs statements 비교
- [x] 전체 모듈 상세 — 36개 property, Result 타입, get() 추가 DataFrame
- [x] 튜토리얼 4개 — property 접근, Notes 통합, get() 패턴
- [x] v0.1.12 기준 문서 갱신 (2026-03-08)
