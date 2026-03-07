# docs/ 현황

## 구조
```
docs/
├── index.md                      # 메인 페이지
├── getting-started/
│   ├── installation.md           # 설치 가이드
│   └── quickstart.md             # 빠른 시작
├── user-guide/
│   └── bridge-matching.md        # Bridge Matching 상세
└── api/
    ├── overview.md               # API 전체 개요 + Company 클래스
    ├── finance-summary.md        # summary 모듈 상세
    ├── finance-statements.md     # statements 모듈 상세
    └── finance-others.md         # 나머지 12개 모듈
```

## 렌더링
- SvelteKit + mdsvex로 마크다운 렌더링 (MkDocs 제거)
- shiki로 코드 하이라이팅 (github-dark 테마)
- landing/ 안에서 @docs alias로 참조

## 배포
- GitHub Actions (`docs.yml`)로 자동 배포
- SvelteKit 단일 빌드 (랜딩 + 문서 통합)
- URL: https://eddmpython.github.io/dartlab/docs/

## 진행 상태
- [x] 기본 구조
- [x] 시작하기 (설치, 빠른 시작) - 실제 API 반영
- [x] Bridge Matching 가이드 - 4단계 매칭, 상수 포함
- [x] API Overview - Company 클래스, 14개 모듈 전체 목록
- [x] finance.summary 상세 - AnalysisResult, BridgeResult, Segment
- [x] finance.statements 상세 - StatementsResult
- [x] 기타 12개 모듈 API - 시그니처, Result 타입, 예제
- [ ] 텍스트 분석 가이드 (Layer 2 개발 후)
- [ ] 교차 검증 가이드 (Layer 3 개발 후)
- [ ] 튜토리얼 노트북
