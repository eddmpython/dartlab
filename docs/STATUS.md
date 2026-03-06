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
├── api/
│   └── finance-summary.md        # Finance Summary API 레퍼런스
└── stylesheets/
    └── theme.css                 # MkDocs Material 커스텀 테마
```

## MkDocs 설정
- `mkdocs.yml` (프로젝트 루트)
- 테마: Material for MkDocs (다크 모드 기본)
- 컬러: Amber (#f59e0b) + Blue (#3b82f6)

## 배포
- GitHub Actions (`docs.yml`)로 자동 배포
- SvelteKit 랜딩(/) + MkDocs 문서(/docs/) 통합
- URL: https://eddmpython.github.io/dartlab/docs/

## 진행 상태
- [x] 기본 구조 생성
- [x] 시작하기 (설치, 빠른 시작)
- [x] Bridge Matching 가이드
- [x] Finance Summary API 레퍼런스
- [ ] 텍스트 분석 가이드 (Layer 2 개발 후)
- [ ] 교차 검증 가이드 (Layer 3 개발 후)
- [ ] 튜토리얼 노트북
